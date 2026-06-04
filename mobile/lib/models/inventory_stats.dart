class CategoryCount {
  const CategoryCount({
    required this.categoryName,
    required this.count,
  });

  final String categoryName;
  final int count;
}

class InventoryStats {
  const InventoryStats({
    required this.activeBatchCount,
    required this.totalQuantity,
    required this.expiringSoonCount,
    required this.expiredCount,
    required this.registeredWikiCount,
    required this.needingReminderCount,
    required this.categoryCounts,
  });

  final int activeBatchCount;
  final int totalQuantity;
  final int expiringSoonCount;
  final int expiredCount;
  final int registeredWikiCount;
  final int needingReminderCount;
  final List<CategoryCount> categoryCounts;

  static const empty = InventoryStats(
    activeBatchCount: 0,
    totalQuantity: 0,
    expiringSoonCount: 0,
    expiredCount: 0,
    registeredWikiCount: 0,
    needingReminderCount: 0,
    categoryCounts: [],
  );
}
