import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../data/inventory_controller.dart';
import '../models/inventory_item.dart';
import '../models/item_status.dart';
import '../models/registered_item.dart';
import '../theme/app_theme.dart';
import '../utils/date_formatters.dart';
import '../widgets/app_cards.dart';
import '../widgets/icon_mapper.dart';
import 'item_detail_screen.dart';
import 'item_wiki_detail_screen.dart';

class ItemsScreen extends StatefulWidget {
  const ItemsScreen({super.key, required this.controller});

  final InventoryController controller;

  @override
  State<ItemsScreen> createState() => _ItemsScreenState();
}

class _ItemsScreenState extends State<ItemsScreen> {
  final _searchController = TextEditingController();
  String? _categoryId;
  int _viewIndex = 0;

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final items = _filteredItems();
    final historyItems = _filteredHistoryItems();
    return RefreshIndicator(
      onRefresh: widget.controller.refresh,
      child: ListView(
        padding: const EdgeInsets.only(bottom: 24),
        children: [
          PageHeader(
            title: _viewIndex == 0 ? '物品目录' : '历史记录',
            subtitle: _viewIndex == 0 ? '按 Wiki 条目查看所有库存批次' : '查看已消耗和已过期的库存批次',
          ),
          ContentWidth(
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 20),
              child: Column(
                children: [
                  SizedBox(
                    width: double.infinity,
                    child: SegmentedButton<int>(
                      segments: const [
                        ButtonSegment(
                          value: 0,
                          label: Text('目录'),
                          icon: Icon(Icons.menu_book_outlined),
                        ),
                        ButtonSegment(
                          value: 1,
                          label: Text('历史'),
                          icon: Icon(Icons.history_outlined),
                        ),
                      ],
                      selected: {_viewIndex},
                      onSelectionChanged: (selection) {
                        setState(() => _viewIndex = selection.first);
                      },
                    ),
                  ),
                  const SizedBox(height: 12),
                  TextField(
                    controller: _searchController,
                    textInputAction: TextInputAction.search,
                    decoration: const InputDecoration(
                      prefixIcon: Icon(Icons.search),
                      labelText: '搜索物品',
                    ),
                    onChanged: (_) => setState(() {}),
                  ),
                  const SizedBox(height: 12),
                  if (_viewIndex == 0)
                    SingleChildScrollView(
                      scrollDirection: Axis.horizontal,
                      child: Row(
                        children: [
                          Padding(
                            padding: const EdgeInsets.only(right: 8),
                            child: ChoiceChip(
                              label: const Text('全部'),
                              selected: _categoryId == null,
                              onSelected: (_) => setState(() => _categoryId = null),
                            ),
                          ),
                          ...widget.controller.categories.map(
                            (category) => Padding(
                              padding: const EdgeInsets.only(right: 8),
                              child: ChoiceChip(
                                label: Text(category.name),
                                selected: _categoryId == category.id,
                                avatar: Icon(iconForName(category.icon), size: 18),
                                onSelected: (_) {
                                  setState(() => _categoryId = category.id);
                                },
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                  const SizedBox(height: 18),
                  if (_viewIndex == 0 && items.isEmpty)
                    const EmptyState(
                      icon: Icons.inventory_2_outlined,
                      title: '没有匹配物品',
                      message: '换一个分类或关键词再试。',
                    )
                  else if (_viewIndex == 0)
                    ...items.map(
                      (item) => Padding(
                        padding: const EdgeInsets.only(bottom: 10),
                        child: _RegisteredItemTile(
                          item: item,
                          onTap: () async {
                            await Navigator.of(context).push(
                              MaterialPageRoute(
                                builder: (_) => ItemWikiDetailScreen(
                                  controller: widget.controller,
                                  wikiId: item.wikiId,
                                ),
                              ),
                            );
                            if (mounted) {
                              await widget.controller.refresh();
                            }
                          },
                        ),
                      ),
                    )
                  else if (historyItems.isEmpty)
                    const EmptyState(
                      icon: Icons.history_outlined,
                      title: '暂无历史记录',
                      message: '已消耗和已过期物品会出现在这里。',
                    )
                  else
                    ...historyItems.map(
                      (item) => Padding(
                        padding: const EdgeInsets.only(bottom: 10),
                        child: _HistoryItemTile(
                          item: item,
                          onTap: () async {
                            await Navigator.of(context).push(
                              MaterialPageRoute(
                                builder: (_) => ItemDetailScreen(
                                  controller: widget.controller,
                                  itemId: item.id,
                                ),
                              ),
                            );
                            if (mounted) {
                              await widget.controller.refresh();
                            }
                          },
                        ),
                      ),
                    ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  List<RegisteredItem> _filteredItems() {
    final keyword = _searchController.text.trim().toLowerCase();
    return widget.controller.registeredItems.where((item) {
      final matchesCategory = _categoryId == null || item.categoryId == _categoryId;
      final matchesKeyword = keyword.isEmpty ||
          item.name.toLowerCase().contains(keyword) ||
          (item.description ?? '').toLowerCase().contains(keyword);
      return matchesCategory && matchesKeyword;
    }).toList();
  }

  List<InventoryItem> _filteredHistoryItems() {
    final keyword = _searchController.text.trim().toLowerCase();
    return widget.controller.historyItems.where((item) {
      if (keyword.isEmpty) {
        return true;
      }
      return item.name.toLowerCase().contains(keyword) ||
          (item.description ?? '').toLowerCase().contains(keyword);
    }).toList();
  }
}

class _RegisteredItemTile extends StatelessWidget {
  const _RegisteredItemTile({
    required this.item,
    required this.onTap,
  });

  final RegisteredItem item;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return SectionCard(
      onTap: onTap,
      child: Row(
        children: [
          Container(
            width: 50,
            height: 50,
            decoration: BoxDecoration(
              color: AppColors.primaryContainer,
              borderRadius: BorderRadius.circular(16),
            ),
            child: Icon(iconForName(item.icon), color: AppColors.primary),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  item.name,
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.w800,
                      ),
                ),
                const SizedBox(height: 4),
                Text(
                  [
                    item.categoryName ?? '其他',
                    if (item.storageLocation != null) item.storageLocation!,
                    if (item.defaultUnit != null) '单位 ${item.defaultUnit}',
                  ].join(' · '),
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                        color: AppColors.textSecondary,
                      ),
                ),
              ],
            ),
          ),
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text(
                '${item.totalQuantity}',
                style: Theme.of(context).textTheme.titleLarge?.copyWith(
                      fontWeight: FontWeight.w900,
                      color: AppColors.textPrimary,
                    ),
              ),
              Text(
                item.nextExpiryDate == null
                    ? '${item.activeBatchCount} 批次'
                    : DateFormat('MM-dd').format(item.nextExpiryDate!),
                style: Theme.of(context).textTheme.labelMedium?.copyWith(
                      color: AppColors.textHint,
                    ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _HistoryItemTile extends StatelessWidget {
  const _HistoryItemTile({
    required this.item,
    required this.onTap,
  });

  final InventoryItem item;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final isConsumed = item.status == ItemStatus.consumed;
    final statusLabel = isConsumed
        ? '已消耗'
        : item.isExpired
            ? '已过期'
            : item.status.label;
    final statusColor = isConsumed ? AppColors.success : AppColors.error;
    final statusBackground = isConsumed ? AppColors.successContainer : AppColors.errorContainer;

    return SectionCard(
      onTap: onTap,
      child: Row(
        children: [
          Container(
            width: 50,
            height: 50,
            decoration: BoxDecoration(
              color: statusBackground,
              borderRadius: BorderRadius.circular(16),
            ),
            child: Icon(
              isConsumed ? Icons.check_circle_outline : Icons.warning_amber_outlined,
              color: statusColor,
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  item.name,
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.w800,
                      ),
                ),
                const SizedBox(height: 4),
                Text(
                  '${item.quantity}${item.unit ?? ''} · 过期 ${formatDate(item.expiryDate)}',
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                        color: AppColors.textSecondary,
                      ),
                ),
              ],
            ),
          ),
          StatusPill(
            label: statusLabel,
            color: statusColor,
            backgroundColor: statusBackground,
          ),
        ],
      ),
    );
  }
}
