import '../models/inventory_item.dart';

bool hasUserVisibleImportTrace(InventoryItem item) {
  return importSourceLabel(item.sourceApp) != null ||
      _hasText(item.sourceOrderId) ||
      item.recognitionConfidence != null;
}

String? importSourceLabel(String? sourceApp) {
  final value = sourceApp?.trim();
  if (value == null || value.isEmpty) {
    return null;
  }
  return switch (value.toLowerCase()) {
    'legacy' => '旧版库存',
    'shopping-list' => '采购清单',
    _ => value,
  };
}

bool _hasText(String? value) => value != null && value.trim().isNotEmpty;
