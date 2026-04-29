enum ItemStatus {
  active('active', '使用中'),
  expired('expired', '已过期'),
  consumed('consumed', '已消耗'),
  wasted('wasted', '已丢弃');

  const ItemStatus(this.dbValue, this.label);

  final String dbValue;
  final String label;

  static ItemStatus fromDbValue(String? value) {
    return ItemStatus.values.firstWhere(
      (status) => status.dbValue == value,
      orElse: () => ItemStatus.active,
    );
  }
}
