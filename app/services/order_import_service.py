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
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

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
        self.import_payload["items"][index]["selected"] = bool(selected)

    def update_item(self, index: int, updates: Dict[str, Any]) -> None:
        self.import_payload["items"][index].update(copy.deepcopy(updates))

    def build_commit_payload(self) -> Dict[str, Any]:
        return copy.deepcopy(self.import_payload)


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
        default_purchase_date = self._format_date_string(
            self._parse_date_value(payload.get("purchase_date"))
        )

        created_count = 0
        skipped_count = 0
        failed_rows: List[Dict[str, Any]] = []

        for index, item_data in enumerate(items, start=1):
            if not item_data.get("selected", True):
                skipped_count += 1
                continue

            normalized_item = self.normalize_review_item(
                item_data,
                default_purchase_date=default_purchase_date,
            )
            if not normalized_item["can_import"]:
                failed_rows.append(
                    {
                        "row": index,
                        "name": normalized_item["name"] or "未命名条目",
                        "reason": "物品名称不能为空",
                    }
                )
                continue

            created_item = item_service.create_item(
                name=normalized_item["name"],
                category=normalized_item["category"],
                quantity=normalized_item["quantity"],
                expiry_date=self._parse_date_value(normalized_item["expiry_date"]),
                purchase_date=self._parse_date_value(normalized_item["purchase_date"]),
                unit=normalized_item["unit"],
                source_app=source_app,
                source_order_id=source_order_id,
                image_path=image_path,
            )
            if created_item is None:
                failed_rows.append(
                    {
                        "row": index,
                        "name": normalized_item["name"],
                        "reason": "创建库存记录失败",
                    }
                )
                continue

            created_count += 1

        return {
            "created_count": created_count,
            "skipped_count": skipped_count,
            "failed_rows": failed_rows,
        }

    def _resolve_vision_model(self) -> str:
        stored_model = db_service.get_setting("silicon_flow_vision_model")
        if stored_model:
            return stored_model
        return os.getenv("SILICON_FLOW_VISION_MODEL", DEFAULT_MODEL)

    def _resolve_api_key(self) -> Optional[str]:
        stored_key = db_service.get_setting("silicon_flow_api_key")
        if stored_key:
            return stored_key
        return os.getenv("SILICON_FLOW_API_KEY")

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
            '"items": [{"name": "...", "quantity": 1, "unit": "...", "category": "...", '
            '"purchase_date": "YYYY-MM-DD 或 null", "expiry_date": "YYYY-MM-DD 或 null", '
            '"confidence": 0.0, "warnings": ["..."]}]}.'
            "如果截图中没有明确值，请填 null 或空数组。"
            f'category 仅可使用 {", ".join(CANONICAL_CATEGORIES)} 中的一个。'
            "quantity 必须是整数。"
        )

    def _normalize_import_payload(
        self, response_payload: Dict[str, Any], image_path: str
    ) -> Dict[str, Any]:
        purchase_date = self._format_date_string(
            self._parse_date_value(response_payload.get("purchase_date"))
        )
        source_app = response_payload.get("source_app") or DEFAULT_SOURCE_APP
        source_order_id = response_payload.get("source_order_id") or None

        normalized_items = [
            self.normalize_review_item(item, default_purchase_date=purchase_date)
            for item in (response_payload.get("items") or [])
        ]

        return {
            "source_app": source_app,
            "source_order_id": source_order_id,
            "purchase_date": purchase_date,
            "image_path": image_path,
            "items": normalized_items,
        }

    def normalize_review_item(
        self, item_payload: Dict[str, Any], default_purchase_date: Optional[str]
    ) -> Dict[str, Any]:
        item_payload = item_payload if isinstance(item_payload, dict) else {}
        raw_name = (item_payload.get("name") or "").strip()
        wiki_item = wiki_service.get_wiki_by_name(raw_name) if raw_name else None

        warnings = self._normalize_warnings(item_payload.get("warnings"))
        quantity, quantity_warning = self._normalize_quantity(item_payload.get("quantity"))
        if quantity_warning:
            warnings.append(quantity_warning)

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

        purchase_date = self._parse_date_value(
            item_payload.get("purchase_date") or default_purchase_date
        )
        purchase_date_str = self._format_date_string(purchase_date)

        expiry_date = self._parse_date_value(item_payload.get("expiry_date"))
        if expiry_date is None and wiki_item and purchase_date and wiki_item.get(
            "suggested_expiry_days"
        ):
            expiry_date = purchase_date + timedelta(
                days=int(wiki_item["suggested_expiry_days"])
            )
            warnings.append(
                f"根据 Wiki 建议保质期推导过期日期：{self._format_date_string(expiry_date)}"
            )
        expiry_date_str = self._format_date_string(expiry_date)

        confidence = self._normalize_confidence(item_payload.get("confidence"))
        can_import = bool(raw_name)
        if not can_import:
            warnings.append("未识别到物品名称，当前条目不可导入")

        normalized_item = {
            "name": raw_name,
            "quantity": quantity,
            "unit": unit,
            "category": category,
            "purchase_date": purchase_date_str,
            "expiry_date": expiry_date_str,
            "confidence": confidence,
            "warnings": warnings,
            "selected": bool(item_payload.get("selected", True)) and can_import,
            "can_import": can_import,
        }
        return normalized_item

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

    def _format_date_string(self, value: Optional[date]) -> Optional[str]:
        if value is None:
            return None
        return value.strftime("%Y-%m-%d")


order_import_service = OrderImportService()
