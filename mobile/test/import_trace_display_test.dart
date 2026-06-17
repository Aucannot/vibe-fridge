import 'package:flutter_test/flutter_test.dart';
import 'package:vibe_fridge/models/inventory_item.dart';
import 'package:vibe_fridge/models/item_status.dart';
import 'package:vibe_fridge/utils/import_trace_display.dart';

void main() {
  test('maps internal import source names to user-facing labels', () {
    expect(importSourceLabel('legacy'), '旧版库存');
    expect(importSourceLabel(' LEGACY '), '旧版库存');
    expect(importSourceLabel('shopping-list'), '采购清单');
    expect(importSourceLabel('盒马'), '盒马');
    expect(importSourceLabel('  '), isNull);
  });

  test('does not expose import batch ids as visible import trace', () {
    expect(
      hasUserVisibleImportTrace(
        _item(importBatchId: 'legacy-batch'),
      ),
      isFalse,
    );
    expect(
      hasUserVisibleImportTrace(
        _item(sourceApp: 'legacy', importBatchId: 'legacy-batch'),
      ),
      isTrue,
    );
  });
}

InventoryItem _item({
  String? sourceApp,
  String? sourceOrderId,
  String? importBatchId,
  double? recognitionConfidence,
}) {
  final now = DateTime(2026, 6, 18);
  return InventoryItem(
    id: 'item-test',
    wikiId: 'wiki-test',
    name: '测试物品',
    quantity: 1,
    reminderDaysBefore: 3,
    status: ItemStatus.active,
    isReminderEnabled: true,
    sourceApp: sourceApp,
    sourceOrderId: sourceOrderId,
    importBatchId: importBatchId,
    recognitionConfidence: recognitionConfidence,
    createdAt: now,
    updatedAt: now,
  );
}
