# -*- coding: utf-8 -*-
"""Order import draft state tests."""

from app.services.order_import_service import OrderImportDraft


def test_draft_transitions_from_pick_to_review():
    draft = OrderImportDraft()

    draft.select_image("/tmp/order.png")
    draft.start_parsing()
    draft.load_review_payload(
        {
            "source_app": "盒马",
            "source_order_id": "HM-2026",
            "purchase_date": "2026-04-01",
            "image_path": "/tmp/order.png",
            "items": [
                {
                    "name": "牛奶",
                    "quantity": 2,
                    "unit": "盒",
                    "selected": True,
                }
            ],
        }
    )

    assert draft.image_path == "/tmp/order.png"
    assert draft.view_state == "review"
    assert draft.import_payload["source_app"] == "盒马"


def test_draft_can_ignore_and_edit_rows_without_mutating_snapshot():
    draft = OrderImportDraft()
    draft.load_review_payload(
        {
            "source_app": "盒马",
            "source_order_id": "HM-2026",
            "purchase_date": "2026-04-01",
            "image_path": "/tmp/order.png",
            "items": [
                {
                    "name": "牛奶",
                    "quantity": 2,
                    "unit": "盒",
                    "category": "食品",
                    "selected": True,
                }
            ],
        }
    )

    draft.set_item_selected(0, False)
    draft.update_item(0, {"name": "低温鲜奶", "quantity": 4})

    payload = draft.build_commit_payload()
    payload["items"][0]["name"] = "外部修改"

    assert draft.import_payload["items"][0]["selected"] is False
    assert draft.import_payload["items"][0]["name"] == "低温鲜奶"
    assert draft.import_payload["items"][0]["quantity"] == 4


def test_draft_reset_clears_selected_image_and_payload():
    draft = OrderImportDraft()
    draft.select_image("/tmp/order.png")
    draft.load_review_payload(
        {
            "source_app": "盒马",
            "source_order_id": "HM-2026",
            "purchase_date": "2026-04-01",
            "image_path": "/tmp/order.png",
            "items": [{"name": "牛奶", "selected": True}],
        }
    )

    draft.reset()

    assert draft.view_state == "pick"
    assert draft.image_path == ""
    assert draft.import_payload["items"] == []
