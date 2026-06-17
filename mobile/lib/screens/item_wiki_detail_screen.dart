import 'package:flutter/material.dart';

import '../data/inventory_controller.dart';
import '../models/inventory_item.dart';
import '../models/item_status.dart';
import '../models/item_wiki.dart';
import '../theme/app_theme.dart';
import '../utils/date_formatters.dart';
import '../utils/web_route_state.dart';
import '../widgets/app_cards.dart';
import '../widgets/icon_mapper.dart';
import 'item_detail_screen.dart';
import 'item_wiki_edit_screen.dart';

class ItemWikiDetailScreen extends StatefulWidget {
  const ItemWikiDetailScreen({
    super.key,
    required this.controller,
    required this.wikiId,
  });

  final InventoryController controller;
  final String wikiId;

  @override
  State<ItemWikiDetailScreen> createState() => _ItemWikiDetailScreenState();
}

class _ItemWikiDetailScreenState extends State<ItemWikiDetailScreen> {
  late Future<_WikiDetailData> _future;
  final Set<String> _selectedItemIds = <String>{};
  bool _selectionMode = false;
  bool _working = false;

  @override
  void initState() {
    super.initState();
    widget.controller.addListener(_handleControllerChanged);
    _future = _load();
  }

  @override
  void didUpdateWidget(covariant ItemWikiDetailScreen oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.controller != widget.controller) {
      oldWidget.controller.removeListener(_handleControllerChanged);
      widget.controller.addListener(_handleControllerChanged);
      _future = _load();
    }
  }

  @override
  void dispose() {
    widget.controller.removeListener(_handleControllerChanged);
    super.dispose();
  }

  Future<_WikiDetailData> _load() async {
    final wiki = await widget.controller.repository.getWiki(widget.wikiId);
    final items =
        await widget.controller.repository.getInventoryByWikiId(widget.wikiId);
    return _WikiDetailData(wiki: wiki, items: items);
  }

  void _handleControllerChanged() {
    _reloadDetail();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        leading: _selectionMode
            ? IconButton(
                tooltip: '退出批量选择',
                onPressed: _working ? null : _exitSelectionMode,
                icon: const Icon(Icons.close),
              )
            : null,
        title: Text(
          _selectionMode ? '已选择 ${_selectedItemIds.length} 项' : '物品资料',
        ),
        actions: _selectionMode
            ? null
            : [
                FutureBuilder<_WikiDetailData>(
                  future: _future,
                  builder: (context, snapshot) {
                    final wiki = snapshot.data?.wiki;
                    if (wiki == null) {
                      return const SizedBox.shrink();
                    }
                    return Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        IconButton(
                          tooltip: '编辑物品资料',
                          onPressed: () => _editWiki(wiki),
                          icon: const Icon(Icons.edit_outlined),
                        ),
                        IconButton(
                          tooltip: '删除物品资料',
                          onPressed: () => _deleteWiki(wiki),
                          icon: const Icon(Icons.delete_outline),
                        ),
                      ],
                    );
                  },
                ),
              ],
      ),
      body: FutureBuilder<_WikiDetailData>(
        future: _future,
        builder: (context, snapshot) {
          if (snapshot.connectionState != ConnectionState.done) {
            return const Center(child: CircularProgressIndicator());
          }
          final data = snapshot.data!;
          final wiki = data.wiki;
          if (wiki == null) {
            return const Center(child: Text('物品资料不存在'));
          }
          final selectedItems = _selectedItems(data.items);
          final activeSelectedCount = selectedItems
              .where((item) => item.status == ItemStatus.active)
              .length;
          final allSelected = data.items.isNotEmpty &&
              data.items.every((item) => _selectedItemIds.contains(item.id));
          return RefreshIndicator(
            onRefresh: () async {
              if (!mounted) {
                return;
              }
              final future = _load();
              setState(() {
                _future = future;
                _selectedItemIds.clear();
                _selectionMode = false;
              });
              await future;
            },
            child: ListView(
              padding: AppSpacing.detailListPadding,
              children: [
                ContentWidth(
                  child: _WikiHeader(wiki: wiki),
                ),
                const SizedBox(height: AppSpacing.fieldGap),
                ContentWidth(
                  child: _WikiFacts(wiki: wiki),
                ),
                const SizedBox(height: AppSpacing.sectionGap),
                ContentWidth(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Expanded(
                            child: Text(
                              '库存批次',
                              style: Theme.of(context)
                                  .textTheme
                                  .titleLarge
                                  ?.copyWith(
                                    fontWeight: FontWeight.w800,
                                  ),
                            ),
                          ),
                          if (data.items.isNotEmpty)
                            _selectionMode
                                ? TextButton.icon(
                                    onPressed: _working
                                        ? null
                                        : () => _toggleSelectAll(
                                              data.items,
                                              allSelected: allSelected,
                                            ),
                                    icon: Icon(
                                      allSelected
                                          ? Icons.check_box_outline_blank
                                          : Icons.select_all_outlined,
                                    ),
                                    label: Text(
                                      allSelected ? '取消全选' : '全选',
                                    ),
                                  )
                                : OutlinedButton.icon(
                                    onPressed: _working
                                        ? null
                                        : () => _enterSelectionMode(),
                                    icon: const Icon(Icons.checklist_outlined),
                                    label: const Text('批量'),
                                  ),
                        ],
                      ),
                      if (_selectionMode) ...[
                        const SizedBox(height: AppSpacing.cardGap),
                        _BatchActionBar(
                          selectedCount: selectedItems.length,
                          activeSelectedCount: activeSelectedCount,
                          working: _working,
                          onConsume: () => _consumeSelectedItems(data.items),
                          onChangeCategory: () =>
                              _changeSelectedCategory(data.items),
                          onChangeLocation: () =>
                              _changeSelectedStorageLocation(data.items),
                          onDelete: () => _deleteSelectedItems(data.items),
                        ),
                      ],
                      const SizedBox(height: AppSpacing.cardGap),
                      if (data.items.isEmpty)
                        const EmptyState(
                          icon: Icons.inventory_2_outlined,
                          title: '暂无库存',
                          message: '这个物品资料下还没有'
                              '具体库存记录。',
                        )
                      else
                        ...data.items.map(
                          (item) => Padding(
                            padding: const EdgeInsets.only(bottom: 10),
                            child: _BatchTile(
                              item: item,
                              selectionMode: _selectionMode,
                              selected: _selectedItemIds.contains(item.id),
                              onSelectionChanged: () =>
                                  _toggleItemSelection(item),
                              onLongPress: () => _enterSelectionMode(item.id),
                              onTap: () => _openItemDetail(item),
                            ),
                          ),
                        ),
                    ],
                  ),
                ),
              ],
            ),
          );
        },
      ),
    );
  }

  List<InventoryItem> _selectedItems(List<InventoryItem> items) {
    return items.where((item) => _selectedItemIds.contains(item.id)).toList();
  }

  void _enterSelectionMode([String? itemId]) {
    setState(() {
      _selectionMode = true;
      if (itemId != null) {
        _selectedItemIds.add(itemId);
      }
    });
  }

  void _exitSelectionMode() {
    setState(() {
      _selectionMode = false;
      _selectedItemIds.clear();
    });
  }

  void _toggleItemSelection(InventoryItem item) {
    setState(() {
      _selectionMode = true;
      if (_selectedItemIds.contains(item.id)) {
        _selectedItemIds.remove(item.id);
      } else {
        _selectedItemIds.add(item.id);
      }
    });
  }

  void _toggleSelectAll(
    List<InventoryItem> items, {
    required bool allSelected,
  }) {
    setState(() {
      if (allSelected) {
        _selectedItemIds.clear();
      } else {
        _selectedItemIds
          ..clear()
          ..addAll(items.map((item) => item.id));
      }
    });
  }

  Future<void> _openItemDetail(InventoryItem item) async {
    final route = '/items/item/${item.id}';
    setWebRouteState(route);
    final detail = Navigator.of(context).push(
      MaterialPageRoute(
        settings: RouteSettings(name: route),
        builder: (_) => ItemDetailScreen(
          controller: widget.controller,
          itemId: item.id,
        ),
      ),
    );
    setWebRouteState(route, replace: true);
    await detail;
    setWebRouteState('/items/wiki/${widget.wikiId}', replace: true);
    if (mounted) {
      setState(() {
        _future = _load();
      });
    }
  }

  Future<void> _consumeSelectedItems(List<InventoryItem> items) async {
    final ids = _selectedItems(items)
        .where((item) => item.status == ItemStatus.active)
        .map((item) => item.id)
        .toList();
    if (ids.isEmpty) {
      _showMessage('请选择使用中的库存批次');
      return;
    }
    final confirmed = await showAppConfirmDialog(
      context,
      title: '批量标记消耗',
      message: '确定将选中的 ${ids.length} 个批次各消耗 1 件吗？',
      confirmLabel: '标记消耗',
    );
    if (!confirmed) {
      return;
    }
    await _runBatchAction(
      itemIds: ids,
      message: '已标记 ${ids.length} 个批次各消耗 1 件',
      action: (ids) => widget.controller.markItemsAsConsumed(ids),
    );
  }

  Future<void> _deleteSelectedItems(List<InventoryItem> items) async {
    final ids = _selectedItems(items).map((item) => item.id).toList();
    if (ids.isEmpty) {
      _showMessage('请选择要删除的库存批次');
      return;
    }
    final confirmed = await showAppConfirmDialog(
      context,
      title: '批量删除库存',
      message: '确定删除选中的 ${ids.length} 条库存记录吗？',
      confirmLabel: '删除',
      isDestructive: true,
    );
    if (!confirmed) {
      return;
    }
    await _runBatchAction(
      itemIds: ids,
      message: '已删除 ${ids.length} 条库存记录',
      action: (ids) => widget.controller.deleteItems(ids),
    );
  }

  Future<void> _changeSelectedStorageLocation(List<InventoryItem> items) async {
    final ids = _selectedItems(items).map((item) => item.id).toList();
    if (ids.isEmpty) {
      _showMessage('请选择要修改位置的库存批次');
      return;
    }
    final selected = await showModalBottomSheet<String>(
      context: context,
      showDragHandle: true,
      builder: (context) => SafeArea(
        child: ListView(
          shrinkWrap: true,
          children: [
            const ListTile(
              title: Text('选择存放位置'),
            ),
            for (final location in _storageLocationOptions)
              ListTile(
                leading: const Icon(Icons.place_outlined),
                title: Text(location),
                onTap: () => Navigator.of(context).pop(location),
              ),
            ListTile(
              leading: const Icon(Icons.clear_outlined),
              title: const Text('清空位置'),
              onTap: () => Navigator.of(context).pop(''),
            ),
          ],
        ),
      ),
    );
    if (selected == null) {
      return;
    }
    await _runBatchAction(
      itemIds: ids,
      message: '已修改 ${ids.length} 条库存的位置',
      action: (ids) => widget.controller.updateItemsStorageLocation(
        ids,
        selected.isEmpty ? null : selected,
      ),
    );
  }

  Future<void> _changeSelectedCategory(List<InventoryItem> items) async {
    final ids = _selectedItems(items).map((item) => item.id).toList();
    if (ids.isEmpty) {
      _showMessage('请选择要调整分类的库存批次');
      return;
    }
    final categories = widget.controller.categories;
    if (categories.isEmpty) {
      _showMessage('暂无可用分类');
      return;
    }
    final selected = await showModalBottomSheet<String>(
      context: context,
      showDragHandle: true,
      builder: (context) => SafeArea(
        child: ListView(
          shrinkWrap: true,
          children: [
            const ListTile(
              title: Text('选择物品资料分类'),
            ),
            for (final category in categories)
              ListTile(
                leading: Icon(iconForName(category.icon)),
                title: Text(category.name),
                onTap: () => Navigator.of(context).pop(category.id),
              ),
            ListTile(
              leading: const Icon(Icons.clear_outlined),
              title: const Text('清空分类'),
              onTap: () => Navigator.of(context).pop(''),
            ),
          ],
        ),
      ),
    );
    if (selected == null) {
      return;
    }
    await _runBatchAction(
      itemIds: ids,
      message: '已修改物品资料分类',
      action: (ids) => widget.controller.updateItemsCategory(
        ids,
        selected.isEmpty ? null : selected,
      ),
    );
  }

  Future<void> _runBatchAction({
    required List<String> itemIds,
    required String message,
    required Future<void> Function(List<String> itemIds) action,
  }) async {
    if (!mounted || itemIds.isEmpty || _working) {
      return;
    }
    setState(() => _working = true);
    try {
      await action(itemIds);
      if (!mounted) {
        return;
      }
      _showMessage(message);
      setState(() {
        _selectedItemIds.clear();
        _selectionMode = false;
        _future = _load();
        _working = false;
      });
    } catch (error, stackTrace) {
      if (!mounted) {
        return;
      }
      setState(() => _working = false);
      showAppErrorSnackBar(
        context,
        message: '批量操作失败',
        error: error,
        stackTrace: stackTrace,
      );
    }
  }

  void _showMessage(String message) {
    if (!mounted) {
      return;
    }
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message)),
    );
  }

  Future<void> _editWiki(ItemWiki wiki) async {
    final changed = await Navigator.of(context).push<bool>(
      MaterialPageRoute(
        builder: (_) => ItemWikiEditScreen(
          controller: widget.controller,
          wiki: wiki,
        ),
      ),
    );
    if (changed == true && mounted) {
      await widget.controller.refresh();
      if (!mounted) {
        return;
      }
      _reloadDetail();
      Future<void>.delayed(
        const Duration(milliseconds: 300),
        _reloadDetail,
      );
      Future<void>.delayed(const Duration(seconds: 1), _reloadDetail);
    }
  }

  void _reloadDetail() {
    if (!mounted) {
      return;
    }
    setState(() {
      _future = _load();
    });
  }

  Future<void> _deleteWiki(ItemWiki wiki) async {
    final inventoryCount =
        await widget.controller.repository.getWikiInventoryCount(wiki.id);
    if (!mounted) {
      return;
    }
    if (inventoryCount > 0) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            '“${wiki.name}”下还有 '
            '$inventoryCount 条库存记录，不能删除',
          ),
        ),
      );
      return;
    }

    final confirmed = await showAppConfirmDialog(
      context,
      title: '删除物品资料',
      message: '确定删除“${wiki.name}”这个物品资料吗？',
      confirmLabel: '删除',
      isDestructive: true,
    );
    if (!confirmed) {
      return;
    }
    await widget.controller.deleteWiki(wiki.id);
    if (mounted) {
      Navigator.of(context).pop();
    }
  }
}

class _WikiHeader extends StatelessWidget {
  const _WikiHeader({required this.wiki});

  final ItemWiki wiki;

  @override
  Widget build(BuildContext context) {
    return SectionCard(
      padding: const EdgeInsets.all(18),
      child: Row(
        children: [
          Container(
            width: 58,
            height: 58,
            decoration: BoxDecoration(
              color: AppColors.primaryContainer,
              borderRadius: BorderRadius.circular(18),
            ),
            child: Icon(
              iconForName(wiki.icon),
              color: AppColors.primary,
              size: 30,
            ),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  wiki.name,
                  style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                        fontWeight: FontWeight.w900,
                      ),
                ),
                const SizedBox(height: 6),
                Text(
                  wiki.description ?? '暂无描述',
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                        color: AppColors.textSecondary,
                      ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _WikiFacts extends StatelessWidget {
  const _WikiFacts({required this.wiki});

  final ItemWiki wiki;

  @override
  Widget build(BuildContext context) {
    return SectionCard(
      child: Column(
        children: [
          _FactRow(label: '分类', value: wiki.categoryName ?? '其他'),
          _FactRow(label: '默认单位', value: wiki.defaultUnit ?? '未设置'),
          _FactRow(
            label: '建议保质期',
            value: wiki.suggestedExpiryDays == null
                ? '未设置'
                : '${wiki.suggestedExpiryDays} 天',
          ),
          _FactRow(
            label: '默认提醒',
            value: '提前 ${wiki.defaultReminderDays} 天',
          ),
          _FactRow(label: '存放位置', value: wiki.storageLocation ?? '未设置'),
          _FactRow(label: '库存批次', value: '${wiki.inventoryCount}'),
        ],
      ),
    );
  }
}

class _FactRow extends StatelessWidget {
  const _FactRow({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Row(
        children: [
          SizedBox(
            width: 92,
            child: Text(
              label,
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: AppColors.textSecondary,
                  ),
            ),
          ),
          Expanded(
            child: Text(
              value,
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: AppColors.textPrimary,
                    fontWeight: FontWeight.w700,
                  ),
            ),
          ),
        ],
      ),
    );
  }
}

class _BatchTile extends StatelessWidget {
  const _BatchTile({
    required this.item,
    required this.selectionMode,
    required this.selected,
    required this.onTap,
    required this.onSelectionChanged,
    required this.onLongPress,
  });

  final InventoryItem item;
  final bool selectionMode;
  final bool selected;
  final VoidCallback onTap;
  final VoidCallback onSelectionChanged;
  final VoidCallback onLongPress;

  @override
  Widget build(BuildContext context) {
    final days = item.daysUntilExpiry;
    final statusColor = item.status.dbValue == 'consumed'
        ? AppColors.textHint
        : item.isExpired
            ? AppColors.error
            : days != null && days <= 7
                ? AppColors.warning
                : AppColors.success;
    final background = item.status.dbValue == 'consumed'
        ? AppColors.surfaceVariant
        : item.isExpired
            ? AppColors.errorContainer
            : days != null && days <= 7
                ? AppColors.warningContainer
                : AppColors.successContainer;

    return SectionCard(
      onTap: selectionMode ? onSelectionChanged : onTap,
      onLongPress: onLongPress,
      color:
          selected ? AppColors.primaryContainer.withValues(alpha: 0.45) : null,
      borderColor: selected ? AppColors.primary : null,
      child: Row(
        children: [
          if (selectionMode) ...[
            SizedBox(
              width: 42,
              child: Checkbox(
                value: selected,
                onChanged: (_) => onSelectionChanged(),
              ),
            ),
            const SizedBox(width: 4),
          ],
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  '${item.quantity}${item.unit ?? ''}',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.w900,
                      ),
                ),
                const SizedBox(height: 4),
                Text(
                  '购买 ${formatDate(item.purchaseDate)} · '
                  '过期 ${formatDate(item.expiryDate)}',
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                        color: AppColors.textSecondary,
                      ),
                ),
                if (item.storageLocation != null || item.tags.isNotEmpty) ...[
                  const SizedBox(height: 4),
                  Text(
                    [
                      if (item.storageLocation != null)
                        '位置 ${item.storageLocation}',
                      if (item.tags.isNotEmpty) item.tags.take(2).join('、'),
                    ].join(' · '),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: Theme.of(context).textTheme.labelMedium?.copyWith(
                          color: AppColors.textHint,
                        ),
                  ),
                ],
              ],
            ),
          ),
          const SizedBox(width: 12),
          StatusPill(
            label: item.status.label,
            color: statusColor,
            backgroundColor: background,
          ),
        ],
      ),
    );
  }
}

class _BatchActionBar extends StatelessWidget {
  const _BatchActionBar({
    required this.selectedCount,
    required this.activeSelectedCount,
    required this.working,
    required this.onConsume,
    required this.onChangeCategory,
    required this.onChangeLocation,
    required this.onDelete,
  });

  final int selectedCount;
  final int activeSelectedCount;
  final bool working;
  final VoidCallback onConsume;
  final VoidCallback onChangeCategory;
  final VoidCallback onChangeLocation;
  final VoidCallback onDelete;

  @override
  Widget build(BuildContext context) {
    final error = Theme.of(context).colorScheme.error;
    return Wrap(
      spacing: 8,
      runSpacing: 8,
      crossAxisAlignment: WrapCrossAlignment.center,
      children: [
        StatusPill(
          label: '$selectedCount 项',
          color: AppColors.primary,
          backgroundColor: AppColors.primaryContainer,
        ),
        OutlinedButton.icon(
          onPressed: working || activeSelectedCount == 0 ? null : onConsume,
          icon: const Icon(Icons.check_circle_outline),
          label: const Text('消耗'),
        ),
        OutlinedButton.icon(
          onPressed: working || selectedCount == 0 ? null : onChangeCategory,
          icon: const Icon(Icons.category_outlined),
          label: const Text('改分类'),
        ),
        OutlinedButton.icon(
          onPressed: working || selectedCount == 0 ? null : onChangeLocation,
          icon: const Icon(Icons.place_outlined),
          label: const Text('改位置'),
        ),
        OutlinedButton.icon(
          onPressed: working || selectedCount == 0 ? null : onDelete,
          icon: Icon(Icons.delete_outline, color: error),
          label: Text('删除', style: TextStyle(color: error)),
        ),
      ],
    );
  }
}

class _WikiDetailData {
  const _WikiDetailData({
    required this.wiki,
    required this.items,
  });

  final ItemWiki? wiki;
  final List<InventoryItem> items;
}

const _storageLocationOptions = [
  '冷藏',
  '冷冻',
  '常温',
  '药箱',
  '浴室',
  '其他',
];
