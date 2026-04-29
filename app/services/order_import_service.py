# -*- coding: utf-8 -*-
"""
订单截图批量导入服务
"""

import base64
import copy
import json
import mimetypes
import os
import re
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests
from dateutil import parser as date_parser

from app.services.database import db_service
from app.services.item_service import item_service
from app.services.wiki_service import wiki_service
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


DEFAULT_SOURCE_APP = "订单截图"
DEFAULT_CATEGORY = "食品"
DEFAULT_UNIT = "件"
DEFAULT_MODEL = "Qwen/Qwen2-VL-72B-Instruct"
SUPPORTED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}
CANONICAL_CATEGORIES = ("食品", "日用品", "药品", "化妆品", "其他")
FUZZY_EXPIRY_RULES = (
    (("三明治", "便当", "寿司", "饭团", "沙拉", "熟食", "鲜切"), 1, "即食/鲜食类"),
    (("香蕉", "甜蕉", "草莓", "蓝莓", "叶菜", "生菜", "青菜"), 3, "短保生鲜"),
    (("面包", "吐司", "蛋糕", "烘焙"), 3, "烘焙短保"),
    (("牛奶", "鲜奶", "酸奶", "奶酪", "乳"), 7, "乳制品"),
    (("鸡蛋", "溏心蛋", "蛋"), 14, "蛋类"),
    (("姜", "蒜", "土豆", "洋葱", "胡萝卜"), 30, "耐储蔬菜"),
)
FUZZY_CATEGORY_EXPIRY_DAYS = {
    "食品": (7, "食品默认短保"),
}
WIKI_NAME_ALIASES = {
    "香蕉": ("甜蕉", "蕉"),
    "苹果": ("红富士", "富士苹果", "青苹果"),
    "牛奶": ("鲜奶", "纯牛奶"),
    "酸奶": ("酸乳", "发酵乳"),
    "面包": ("吐司", "切片"),
    "鸡蛋": ("蛋", "溏心蛋"),
}
SILICONFLOW_MODEL_SETTING = "siliconflow_vision_model"
LEGACY_SILICONFLOW_MODEL_SETTING = "silicon_flow_vision_model"
SILICONFLOW_API_KEY_SETTING = "siliconflow_api_key"
LEGACY_SILICONFLOW_API_KEY_SETTING = "silicon_flow_api_key"
SILICONFLOW_MODEL_ENV = "SILICONFLOW_VISION_MODEL"
LEGACY_SILICONFLOW_MODEL_ENV = "SILICON_FLOW_VISION_MODEL"
SILICONFLOW_API_KEY_ENV = "SILICONFLOW_API_KEY"
LEGACY_SILICONFLOW_API_KEY_ENV = "SILICON_FLOW_API_KEY"


@dataclass
class OrderImportDraft:
    """Pure-Python state used by the screen and tests."""

    view_state: str = "pick"
    image_path: str = ""
    import_payload: Dict[str, Any] = field(
        default_factory=lambda: {
            "source_app": DEFAULT_SOURCE_APP,
            "source_order_id": None,
            "purchase_date": None,
            "order_time": None,
            "order_time_source": None,
            "image_path": "",
            "items": [],
        }
    )

    def reset(self) -> None:
        self.view_state = "pick"
        self.image_path = ""
        self.import_payload = {
            "source_app": DEFAULT_SOURCE_APP,
            "source_order_id": None,
            "purchase_date": None,
            "order_time": None,
            "order_time_source": None,
            "image_path": "",
            "items": [],
        }

    def select_image(self, image_path: str) -> None:
        self.image_path = os.path.abspath(image_path) if image_path else ""

    def start_parsing(self) -> None:
        self.view_state = "parsing"

    def load_review_payload(self, payload: Dict[str, Any]) -> None:
        self.import_payload = copy.deepcopy(payload)
        self.image_path = self.import_payload.get("image_path") or self.image_path
        self.view_state = "review"

    def set_item_selected(self, index: int, selected: bool) -> None:
        item = self.import_payload["items"][index]
        if item.get("imported") or not item.get("can_import", True):
            item["selected"] = False
            return
        item["selected"] = bool(selected)

    def update_item(self, index: int, updates: Dict[str, Any]) -> None:
        self.import_payload["items"][index].update(copy.deepcopy(updates))

    def selected_importable_count(self) -> int:
        return sum(
            1
            for item in self.import_payload.get("items", [])
            if self._is_item_ready_to_import(item)
        )

    def mark_created_rows(self, created_rows: List[Dict[str, Any]]) -> None:
        for row in created_rows or []:
            try:
                index = int(row.get("row", 0)) - 1
            except (TypeError, ValueError):
                continue
            if 0 <= index < len(self.import_payload.get("items", [])):
                item = self.import_payload["items"][index]
                item["imported"] = True
                item["selected"] = False

    def build_commit_payload(self) -> Dict[str, Any]:
        payload = copy.deepcopy(self.import_payload)
        payload["items"] = [
            {**item, "_row_number": index}
            for index, item in enumerate(payload.get("items", []), start=1)
            if not item.get("imported")
        ]
        return payload

    def _is_item_ready_to_import(self, item: Dict[str, Any]) -> bool:
        return (
            bool(item.get("selected"))
            and bool(item.get("can_import", True))
            and not bool(item.get("imported"))
        )


class OrderImportService:
    """订单截图导入服务"""

    api_url = "https://api.siliconflow.cn/v1/chat/completions"

    def parse_order_screenshot(self, image_path: str) -> Dict[str, Any]:
        """解析订单截图并返回可供确认的导入载荷。"""
        image_path = self._validate_image_path(image_path)
        api_key = self._resolve_api_key()
        if not api_key or api_key == "your_api_key_here":
            raise RuntimeError("未配置 API Key，无法解析订单截图。请在设置页填写，或在桌面端使用 .env 作为回退。")

        response_payload = self._call_vision_model(image_path=image_path, api_key=api_key)
        return self._normalize_import_payload(response_payload, image_path=image_path)

    def commit_import(self, import_payload: Dict[str, Any]) -> Dict[str, Any]:
        """将确认后的载荷批量写入库存。"""
        payload = copy.deepcopy(import_payload or {})
        items = payload.get("items") or []
        source_app = payload.get("source_app") or DEFAULT_SOURCE_APP
        source_order_id = payload.get("source_order_id") or None
        image_path = payload.get("image_path") or None
        payload_purchase_date = self._parse_date_value(payload.get("purchase_date"))
        source_order_time = self._parse_datetime_value(
            payload.get("order_time"),
            default_date=payload_purchase_date,
        )
        source_order_time_source = (
            payload.get("order_time_source") or None
        ) if source_order_time else None
        default_purchase_date = self._format_date_string(
            payload_purchase_date or (source_order_time.date() if source_order_time else None)
        )

        created_count = 0
        skipped_count = 0
        failed_rows: List[Dict[str, Any]] = []
        created_rows: List[Dict[str, Any]] = []

        for index, item_data in enumerate(items, start=1):
            row_number = self._resolve_row_number(item_data, index)
            if item_data.get("imported") or not item_data.get("selected", True):
                skipped_count += 1
                continue

            normalized_item = self.normalize_review_item(
                item_data,
                default_purchase_date=default_purchase_date,
            )
            if not normalized_item["can_import"]:
                failed_rows.append(
                    {
                        "row": row_number,
                        "name": normalized_item["name"] or "未命名条目",
                        "reason": "物品名称不能为空",
                    }
                )
                continue

            inventory_name = normalized_item.get("wiki_name") or normalized_item["name"]
            created_item = item_service.create_item(
                name=inventory_name,
                category=normalized_item["category"],
                quantity=normalized_item["quantity"],
                expiry_date=self._parse_date_value(normalized_item["expiry_date"]),
                purchase_date=self._parse_date_value(normalized_item["purchase_date"]),
                unit=normalized_item["unit"],
                source_app=source_app,
                source_order_id=source_order_id,
                source_order_time=source_order_time,
                source_order_time_source=source_order_time_source,
                image_path=image_path,
                predicted_expiry_date=self._parse_date_value(normalized_item["expiry_date"]),
                prediction_confidence=normalized_item["confidence"],
            )
            if created_item is None:
                failed_rows.append(
                    {
                        "row": row_number,
                        "name": inventory_name,
                        "reason": "创建库存记录失败",
                    }
                )
                continue

            created_count += 1
            created_rows.append(
                {
                    "row": row_number,
                    "name": inventory_name,
                    "item_id": created_item.id,
                }
            )

        return {
            "created_count": created_count,
            "skipped_count": skipped_count,
            "failed_rows": failed_rows,
            "created_rows": created_rows,
        }

    def _resolve_row_number(self, item_data: Dict[str, Any], fallback: int) -> int:
        try:
            return int(item_data.get("_row_number") or fallback)
        except (TypeError, ValueError):
            return fallback

    def _resolve_vision_model(self) -> str:
        stored_model = db_service.get_setting(SILICONFLOW_MODEL_SETTING)
        if not stored_model:
            stored_model = db_service.get_setting(LEGACY_SILICONFLOW_MODEL_SETTING)
        if stored_model:
            return stored_model
        return (
            os.getenv(SILICONFLOW_MODEL_ENV)
            or os.getenv(LEGACY_SILICONFLOW_MODEL_ENV)
            or DEFAULT_MODEL
        )

    def _resolve_api_key(self) -> Optional[str]:
        stored_key = db_service.get_setting(SILICONFLOW_API_KEY_SETTING)
        if not stored_key:
            stored_key = db_service.get_setting(LEGACY_SILICONFLOW_API_KEY_SETTING)
        if stored_key:
            return stored_key
        return os.getenv(SILICONFLOW_API_KEY_ENV) or os.getenv(
            LEGACY_SILICONFLOW_API_KEY_ENV
        )

    def _call_vision_model(self, image_path: str, api_key: str) -> Dict[str, Any]:
        mime_type = mimetypes.guess_type(image_path)[0] or "image/png"
        encoded_image = base64.b64encode(Path(image_path).read_bytes()).decode("utf-8")
        user_prompt = self._build_user_prompt()
        payload = {
            "model": self._resolve_vision_model(),
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "你是一个订单截图解析助手。你必须只输出一个 JSON 对象，"
                        "不要输出 Markdown、解释、代码块或额外文本。"
                    ),
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{encoded_image}",
                                "detail": "high",
                            },
                        },
                        {
                            "type": "text",
                            "text": user_prompt,
                        },
                    ],
                },
            ],
            "max_tokens": 1800,
            "temperature": 0.1,
            "top_p": 0.1,
            "stream": False,
        }
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        try:
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=90,
            )
            response.raise_for_status()
            response_json = response.json()
        except requests.RequestException as exc:
            raise RuntimeError(f"调用硅基流动接口失败: {exc}") from exc
        except ValueError as exc:
            raise RuntimeError("硅基流动返回了无法解析的响应") from exc

        content = self._extract_message_content(response_json)
        parsed_payload = self._extract_json_payload(content)
        if not isinstance(parsed_payload, dict):
            raise RuntimeError("订单识别结果不是有效的 JSON 对象")
        return parsed_payload

    def _build_user_prompt(self) -> str:
        return (
            "请读取这张中文订单截图，提取订单来源、订单号、下单日期和商品列表。"
            "必须只返回一个 JSON 对象，结构严格如下："
            '{"source_app": "...", "source_order_id": "...", "purchase_date": "YYYY-MM-DD 或 null", '
            '"order_time": "YYYY-MM-DD HH:MM 或 HH:MM 或 null", '
            '"items": [{"name": "...", "quantity": 1, "unit": "...", "category": "...", '
            '"purchase_date": "YYYY-MM-DD 或 null", "expiry_date": "YYYY-MM-DD 或 null", '
            '"confidence": 0.85, "warnings": ["..."]}]}.'
            "如果截图中没有明确值，请填 null 或空数组。"
            "order_time 只能来自订单正文中的下单、支付、结算、送达或完成时间。"
            "不要把手机状态栏时间、截图时间或系统时间当作下单时间。"
            "如果订单正文没有明确下单时间，请填 null。"
            "如果订单正文只有时间没有日期，可只填 HH:MM。"
            f'category 仅可使用 {", ".join(CANONICAL_CATEGORIES)} 中的一个。'
            "quantity 必须是整数。"
            "confidence 必须是 0 到 1 之间的识别置信度；只有完全无法判断时才填 0。"
            "如果商品名称在截图中被省略号截断，请保留可见名称并在 warnings 中说明。"
        )

    def _normalize_import_payload(
        self, response_payload: Dict[str, Any], image_path: str
    ) -> Dict[str, Any]:
        image_mtime = self._image_mtime_datetime(image_path)
        parsed_purchase_date = self._parse_date_value(response_payload.get("purchase_date"))
        source_app = response_payload.get("source_app") or DEFAULT_SOURCE_APP
        source_order_id = response_payload.get("source_order_id") or None
        raw_order_time = response_payload.get("order_time")
        order_time = self._parse_datetime_value(
            raw_order_time,
            default_date=parsed_purchase_date or (image_mtime.date() if image_mtime else None),
        )
        order_time_source = "model" if order_time else None
        if (
            order_time is not None
            and parsed_purchase_date is None
            and source_order_id is None
            and image_mtime is not None
            and self._same_minute(order_time, image_mtime)
        ):
            order_time_source = "image_file_mtime"
        elif (
            order_time is not None
            and parsed_purchase_date is None
            and image_mtime is not None
            and not self._has_explicit_date_component(raw_order_time)
        ):
            order_time_source = "model_time_image_date"
        if order_time is None and parsed_purchase_date is None and image_mtime is not None:
            order_time = image_mtime
            order_time_source = "image_file_mtime"

        purchase_date_value = parsed_purchase_date or (
            order_time.date() if order_time else None
        )
        purchase_date = self._format_date_string(purchase_date_value)

        normalized_items = [
            self.normalize_review_item(item, default_purchase_date=purchase_date)
            for item in (response_payload.get("items") or [])
        ]

        return {
            "source_app": source_app,
            "source_order_id": source_order_id,
            "purchase_date": purchase_date,
            "order_time": self._format_datetime_string(order_time),
            "order_time_source": order_time_source,
            "image_path": image_path,
            "items": normalized_items,
        }

    def normalize_review_item(
        self, item_payload: Dict[str, Any], default_purchase_date: Optional[str]
    ) -> Dict[str, Any]:
        item_payload = item_payload if isinstance(item_payload, dict) else {}
        raw_name = (item_payload.get("name") or "").strip()
        wiki_item, wiki_match = self._resolve_wiki_match(item_payload, raw_name)

        warnings = self._normalize_warnings(item_payload.get("warnings"))
        quantity, quantity_warning = self._normalize_quantity(item_payload.get("quantity"))
        if quantity_warning:
            warnings.append(quantity_warning)
        if wiki_item and wiki_match.get("type") != "exact":
            warnings.append(self._format_wiki_match_warning(raw_name, wiki_item, wiki_match))

        unit = (item_payload.get("unit") or "").strip()
        if not unit and wiki_item and wiki_item.get("default_unit"):
            unit = wiki_item["default_unit"]
            warnings.append(f"使用 Wiki 默认单位：{unit}")
        if not unit:
            unit = DEFAULT_UNIT
            warnings.append(f"未识别到单位，已使用默认单位：{DEFAULT_UNIT}")

        category = self._canonicalize_category(item_payload.get("category"))
        if category != (item_payload.get("category") or "").strip():
            warnings.append(f"类别已标准化为：{category}")
        wiki_category = (
            self._canonicalize_category(wiki_item.get("category_name"))
            if wiki_item and wiki_item.get("category_name")
            else None
        )
        if wiki_category and category != wiki_category:
            category = wiki_category
            warnings.append(
                f"已按物品 Wiki「{wiki_item['name']}」的分类调整为：{category}"
            )

        purchase_date_value = item_payload.get("purchase_date")
        if item_payload.get("purchase_date_source") == "default":
            purchase_date_value = None
        purchase_date = self._parse_date_value(purchase_date_value or default_purchase_date)
        purchase_date_str = self._format_date_string(purchase_date)
        purchase_date_source = (
            "item"
            if purchase_date_value
            else ("default" if default_purchase_date and purchase_date else None)
        )

        expiry_source = item_payload.get("expiry_date_source")
        expiry_date_value = item_payload.get("expiry_date")
        if expiry_source in {"wiki_estimate", "fuzzy_estimate"}:
            expiry_date_value = None
        expiry_date = self._parse_date_value(expiry_date_value)
        expiry_date_source = "item" if expiry_date_value and expiry_date else None
        if expiry_date is None and wiki_item and purchase_date and wiki_item.get(
            "suggested_expiry_days"
        ):
            expiry_date = purchase_date + timedelta(
                days=int(wiki_item["suggested_expiry_days"])
            )
            expiry_date_source = "wiki_estimate"
            warnings.append(
                f"根据 Wiki 建议保质期推导过期日期：{self._format_date_string(expiry_date)}"
            )
        if expiry_date is None and purchase_date:
            estimated = self._estimate_fuzzy_expiry_date(
                raw_name,
                category,
                purchase_date,
            )
            if estimated:
                expiry_date, estimate_reason, estimate_days = estimated
                expiry_date_source = "fuzzy_estimate"
                warnings.append(
                    "根据下单时间和"
                    f"{estimate_reason}（约 {estimate_days} 天）模糊估计过期日期："
                    f"{self._format_date_string(expiry_date)}"
                )
        expiry_date_str = self._format_date_string(expiry_date)

        confidence = self._normalize_confidence(item_payload.get("confidence"))
        can_import = bool(raw_name)
        imported = bool(item_payload.get("imported", False))
        if not can_import:
            warnings.append("未识别到物品名称，当前条目不可导入")

        normalized_item = {
            "name": raw_name,
            "quantity": quantity,
            "unit": unit,
            "category": category,
            "purchase_date": purchase_date_str,
            "purchase_date_source": purchase_date_source,
            "expiry_date": expiry_date_str,
            "expiry_date_source": expiry_date_source,
            "confidence": confidence,
            "warnings": warnings,
            "selected": bool(item_payload.get("selected", True)) and can_import and not imported,
            "can_import": can_import,
            "imported": imported,
            "wiki_id": wiki_item.get("id") if wiki_item else None,
            "wiki_name": wiki_item.get("name") if wiki_item else None,
            "wiki_match_type": wiki_match.get("type") if wiki_item else None,
            "wiki_match_score": wiki_match.get("score") if wiki_item else None,
        }
        return normalized_item

    def _resolve_wiki_match(
        self, item_payload: Dict[str, Any], raw_name: str
    ) -> Tuple[Optional[Dict[str, Any]], Dict[str, Any]]:
        explicit_wiki_name = (item_payload.get("wiki_name") or "").strip()
        if explicit_wiki_name:
            wiki_item = wiki_service.get_wiki_by_name(explicit_wiki_name)
            if wiki_item:
                return wiki_item, {"type": "manual", "score": 1.0}

        if raw_name:
            exact_match = wiki_service.get_wiki_by_name(raw_name)
            if exact_match:
                return exact_match, {"type": "exact", "score": 1.0}

        return self._find_best_wiki_match(
            raw_name,
            self._canonicalize_category(item_payload.get("category")),
        )

    def _find_best_wiki_match(
        self, raw_name: str, category: str
    ) -> Tuple[Optional[Dict[str, Any]], Dict[str, Any]]:
        normalized_raw = self._normalize_wiki_match_text(raw_name)
        if not normalized_raw:
            return None, {}

        best_wiki = None
        best_match: Dict[str, Any] = {}
        for wiki_item in wiki_service.get_all_wikis(
            limit=500,
            include_inventory_count=False,
        ):
            score, match_type = self._score_wiki_match(
                normalized_raw,
                wiki_item,
                category,
            )
            if score > (best_match.get("score") or 0):
                best_wiki = wiki_item
                best_match = {"type": match_type, "score": score}

        if best_wiki and best_match.get("score", 0) >= 0.78:
            return best_wiki, best_match
        return None, {}

    def _score_wiki_match(
        self,
        normalized_raw: str,
        wiki_item: Dict[str, Any],
        category: str,
    ) -> Tuple[float, Optional[str]]:
        wiki_name = wiki_item.get("name") or ""
        normalized_wiki = self._normalize_wiki_match_text(wiki_name)
        if not normalized_wiki:
            return 0.0, None

        score = 0.0
        match_type = None
        if normalized_raw == normalized_wiki:
            score = 1.0
            match_type = "exact"
        elif normalized_wiki in normalized_raw and len(normalized_wiki) >= 2:
            score = 0.9 + min(len(normalized_wiki), 8) / 100
            match_type = "contains"
        else:
            for alias in WIKI_NAME_ALIASES.get(wiki_name, ()):
                normalized_alias = self._normalize_wiki_match_text(alias)
                if normalized_alias and normalized_alias in normalized_raw:
                    score = 0.84 + min(len(normalized_alias), 8) / 100
                    match_type = "alias"
                    break
            if score == 0.0 and len(normalized_wiki) >= 3:
                ratio = SequenceMatcher(None, normalized_raw, normalized_wiki).ratio()
                if ratio >= 0.62:
                    score = ratio
                    match_type = "similar"

        if score == 0.0:
            return 0.0, None

        raw_wiki_category = wiki_item.get("category_name")
        wiki_category = (
            self._canonicalize_category(raw_wiki_category)
            if raw_wiki_category
            else None
        )
        if wiki_category == category:
            score += 0.04
        elif category and wiki_category and wiki_category != category:
            score -= 0.25

        return max(0.0, min(score, 1.0)), match_type

    def _normalize_wiki_match_text(self, value: Any) -> str:
        text = str(value or "").lower()
        text = re.sub(
            r"\d+(\.\d+)?\s*"
            r"(g|kg|ml|l|克|千克|斤|毫升|升|个|只|枚|盒|袋|瓶|份|支|把|片|包)",
            "",
            text,
        )
        text = re.sub(r"[^\w\u4e00-\u9fff]+", "", text)
        return text.strip()

    def _format_wiki_match_warning(
        self,
        raw_name: str,
        wiki_item: Dict[str, Any],
        wiki_match: Dict[str, Any],
    ) -> str:
        if wiki_match.get("type") == "manual":
            return f"已按手动指定归属到物品 Wiki「{wiki_item['name']}」"
        return f"已将订单商品「{raw_name}」归并到物品 Wiki「{wiki_item['name']}」"

    def _estimate_fuzzy_expiry_date(
        self,
        name: str,
        category: str,
        purchase_date: date,
    ) -> Optional[tuple[date, str, int]]:
        if category != "食品":
            return None

        normalized_name = name or ""
        for keywords, days, reason in FUZZY_EXPIRY_RULES:
            if any(keyword in normalized_name for keyword in keywords):
                return purchase_date + timedelta(days=days), reason, days

        category_rule = FUZZY_CATEGORY_EXPIRY_DAYS.get(category)
        if not category_rule:
            return None
        days, reason = category_rule
        return purchase_date + timedelta(days=days), reason, days

    def _normalize_quantity(self, quantity_value: Any) -> tuple[int, Optional[str]]:
        if quantity_value in (None, ""):
            return 1, "未识别到数量，已使用默认值 1"

        try:
            quantity = int(float(str(quantity_value).strip()))
        except (TypeError, ValueError):
            return 1, f"数量 '{quantity_value}' 无法识别，已使用默认值 1"

        if quantity <= 0:
            return 1, "数量小于等于 0，已使用默认值 1"
        return quantity, None

    def _normalize_confidence(self, confidence_value: Any) -> float:
        try:
            confidence = float(confidence_value)
        except (TypeError, ValueError):
            return 0.0
        return max(0.0, min(1.0, confidence))

    def _canonicalize_category(self, category_value: Any) -> str:
        raw_category = (str(category_value).strip() if category_value is not None else "")
        if raw_category in CANONICAL_CATEGORIES:
            return raw_category

        alias_map = {
            "生鲜": "食品",
            "食品饮料": "食品",
            "饮料": "食品",
            "零食": "食品",
            "家居": "日用品",
            "清洁": "日用品",
            "洗护": "日用品",
            "美妆": "化妆品",
            "护肤": "化妆品",
            "保健": "药品",
            "医药": "药品",
        }
        return alias_map.get(raw_category, DEFAULT_CATEGORY)

    def _normalize_warnings(self, warning_values: Any) -> List[str]:
        if not warning_values:
            return []
        if isinstance(warning_values, str):
            warning_values = [warning_values]
        return [str(value).strip() for value in warning_values if str(value).strip()]

    def _extract_message_content(self, response_json: Dict[str, Any]) -> str:
        choices = response_json.get("choices") or []
        if not choices:
            raise RuntimeError("硅基流动返回为空")

        message = choices[0].get("message") or {}
        content = message.get("content")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            text_parts = [
                part.get("text", "")
                for part in content
                if isinstance(part, dict) and part.get("type") == "text"
            ]
            return "".join(text_parts).strip()
        raise RuntimeError("硅基流动返回内容格式不支持")

    def _extract_json_payload(self, message_content: str) -> Dict[str, Any]:
        content = (message_content or "").strip()
        if not content:
            raise RuntimeError("订单识别结果为空")

        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass

        match = re.search(r"\{.*\}", content, re.DOTALL)
        if not match:
            raise RuntimeError("无法从模型回复中提取 JSON")

        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError as exc:
            raise RuntimeError("模型回复中的 JSON 无法解析") from exc

    def _validate_image_path(self, image_path: str) -> str:
        if not image_path:
            raise ValueError("请先选择订单截图")

        path = Path(image_path).expanduser().resolve()
        if not path.exists() or not path.is_file():
            raise ValueError("所选订单截图不存在")

        if path.suffix.lower() not in SUPPORTED_IMAGE_EXTENSIONS:
            raise ValueError("仅支持 png、jpg、jpeg、webp、bmp 格式的图片")

        return str(path)

    def _parse_date_value(self, value: Any) -> Optional[date]:
        if value in (None, ""):
            return None
        if isinstance(value, date):
            return value

        text = str(value).strip()
        if not text or text.lower() == "null":
            return None

        text = (
            text.replace("年", "-")
            .replace("月", "-")
            .replace("日", "")
            .replace("/", "-")
            .replace(".", "-")
        )
        try:
            return date_parser.parse(text, fuzzy=True, dayfirst=False).date()
        except (ValueError, TypeError, OverflowError):
            return None

    def _parse_datetime_value(
        self,
        value: Any,
        default_date: Optional[date] = None,
    ) -> Optional[datetime]:
        if value in (None, ""):
            return None
        if isinstance(value, datetime):
            return value.replace(second=0, microsecond=0)
        if isinstance(value, date):
            return datetime.combine(value, datetime.min.time())

        text = str(value).strip()
        if not text or text.lower() == "null":
            return None

        text = (
            text.replace("年", "-")
            .replace("月", "-")
            .replace("日", "")
            .replace("时", ":")
            .replace("点", ":")
            .replace("分", "")
            .replace("/", "-")
            .replace(".", "-")
        )
        parse_default = None
        if default_date:
            parse_default = datetime.combine(default_date, datetime.min.time())
        try:
            parsed = date_parser.parse(
                text,
                fuzzy=True,
                dayfirst=False,
                default=parse_default,
            )
        except (ValueError, TypeError, OverflowError):
            return None
        return parsed.replace(second=0, microsecond=0)

    def _has_explicit_date_component(self, value: Any) -> bool:
        if isinstance(value, datetime):
            return True
        if isinstance(value, date):
            return True
        text = str(value or "")
        if re.search(r"\d{4}\s*[-/年.]\s*\d{1,2}", text):
            return True
        return bool(re.search(r"\d{1,2}\s*[-/月.]\s*\d{1,2}\s*(日)?", text))

    def _same_minute(self, first: datetime, second: datetime) -> bool:
        return first.replace(second=0, microsecond=0) == second.replace(
            second=0,
            microsecond=0,
        )

    def _image_mtime_datetime(self, image_path: Optional[str]) -> Optional[datetime]:
        if not image_path:
            return None
        android_datetime = self._android_media_datetime(image_path)
        if android_datetime:
            return android_datetime
        try:
            return datetime.fromtimestamp(Path(image_path).stat().st_mtime).replace(
                second=0,
                microsecond=0,
            )
        except (OSError, TypeError, ValueError):
            return None

    def _android_media_datetime(self, image_path: str) -> Optional[datetime]:
        """Best-effort Android screenshot timestamp lookup via ContentResolver."""
        try:
            from jnius import autoclass

            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            Uri = autoclass("android.net.Uri")
            MediaStoreImages = autoclass("android.provider.MediaStore$Images$Media")

            activity = PythonActivity.mActivity
            resolver = activity.getContentResolver()
            uri = Uri.parse(image_path)
            projection = [
                MediaStoreImages.DATE_TAKEN,
                MediaStoreImages.DATE_ADDED,
                MediaStoreImages.DATE_MODIFIED,
            ]
            cursor = resolver.query(uri, projection, None, None, None)
            if cursor is None:
                return None
            try:
                if not cursor.moveToFirst():
                    return None
                for column_name in projection:
                    column_index = cursor.getColumnIndex(column_name)
                    if column_index < 0:
                        continue
                    parsed = self._datetime_from_media_timestamp(
                        cursor.getLong(column_index)
                    )
                    if parsed:
                        return parsed
            finally:
                cursor.close()
        except Exception:
            return None
        return None

    def _datetime_from_media_timestamp(self, timestamp_value: Any) -> Optional[datetime]:
        try:
            timestamp = int(timestamp_value)
        except (TypeError, ValueError, OverflowError):
            return None
        if timestamp <= 0:
            return None
        if timestamp > 10_000_000_000:
            timestamp = timestamp / 1000
        try:
            return datetime.fromtimestamp(timestamp).replace(second=0, microsecond=0)
        except (OSError, ValueError, OverflowError):
            return None

    def _format_date_string(self, value: Optional[date]) -> Optional[str]:
        if value is None:
            return None
        return value.strftime("%Y-%m-%d")

    def _format_datetime_string(self, value: Optional[datetime]) -> Optional[str]:
        if value is None:
            return None
        return value.strftime("%Y-%m-%d %H:%M")


order_import_service = OrderImportService()
