import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../data/inventory_controller.dart';
import '../models/inventory_item.dart';
import '../models/item_status.dart';
import '../models/item_wiki_category.dart';
import '../models/registered_item.dart';
import '../models/shopping_list_item.dart';
import '../theme/app_theme.dart';
import '../utils/date_formatters.dart';
import '../utils/web_route_state.dart';
import '../widgets/app_cards.dart';
import '../widgets/icon_mapper.dart';
import 'item_detail_screen.dart';
import 'item_wiki_detail_screen.dart';

enum ItemsScreenTarget { catalog, history, shopping }

enum ItemsScreenFocus { expired, dueToday, reminderDue, expiring, cleanup }

class ItemsScreenRequest {
  const ItemsScreenRequest({
    this.target = ItemsScreenTarget.catalog,
    this.focus,
    this.keyword,
    this.categoryId,
  });

  final ItemsScreenTarget target;
  final ItemsScreenFocus? focus;
  final String? keyword;
  final String? categoryId;
}

class ItemsScreen extends StatefulWidget {
  const ItemsScreen({super.key, required this.controller});

  final InventoryController controller;

  @override
  State<ItemsScreen> createState() => ItemsScreenState();
}

class ItemsScreenState extends State<ItemsScreen> {
  final _searchController = TextEditingController();
  final _listController = ScrollController();
  String? _categoryId;
  ItemsScreenFocus? _focus;
  int _viewIndex = 0;

  @override
  void dispose() {
    _searchController.dispose();
    _listController.dispose();
    super.dispose();
  }

  String get _viewTitle {
    final focusedTitle = _focusTitle;
    if (focusedTitle != null) {
      return focusedTitle;
    }
    return switch (_viewIndex) {
      0 => '物品目录',
      1 => '历史记录',
      _ => '采购清单',
    };
  }

  String get _viewSubtitle {
    final focusedSubtitle = _focusSubtitle;
    if (focusedSubtitle != null) {
      return focusedSubtitle;
    }
    return switch (_viewIndex) {
      0 => '按物品资料查看所有库存批次',
      1 => '查看已消耗和已过期的库存批次',
      _ => '低库存、已用完和常买物品会自动建议',
    };
  }

  String? get _focusTitle {
    return switch (_focus) {
      ItemsScreenFocus.expired => '已过期',
      ItemsScreenFocus.dueToday => '今日到期',
      ItemsScreenFocus.reminderDue => '提醒到期',
      ItemsScreenFocus.expiring => '即将过期',
      ItemsScreenFocus.cleanup => '清理建议',
      null => null,
    };
  }

  String? get _focusSubtitle {
    return switch (_focus) {
      ItemsScreenFocus.expired => '优先处理已经超过保质期的库存批次',
      ItemsScreenFocus.dueToday => '今天到期的库存批次',
      ItemsScreenFocus.reminderDue => '提醒规则已经命中的库存批次',
      ItemsScreenFocus.expiring => '7 天内建议优先消耗的库存批次',
      ItemsScreenFocus.cleanup => '临期和历史批次，适合做清理决策',
      null => null,
    };
  }

  void applyRequest(ItemsScreenRequest request) {
    setState(() {
      _viewIndex = switch (request.target) {
        ItemsScreenTarget.catalog => 0,
        ItemsScreenTarget.history => 1,
        ItemsScreenTarget.shopping => 2,
      };
      _focus = request.focus;
      _categoryId = request.categoryId;
      if (request.keyword != null) {
        _searchController.text = request.keyword!;
      } else if (request.focus != null) {
        _searchController.clear();
      }
    });
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted || !_listController.hasClients) {
        return;
      }
      _listController.animateTo(
        0,
        duration: const Duration(milliseconds: 220),
        curve: Curves.easeOutCubic,
      );
    });
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: widget.controller,
      builder: (context, _) {
        final items = _filteredItems();
        final focusedItems = _focusedInventoryItems();
        final historyItems = _filteredHistoryItems();
        return RefreshIndicator(
          onRefresh: widget.controller.refresh,
          child: ListView(
            controller: _listController,
            padding: AppSpacing.pageListPadding,
            children: [
              PageHeader(
                title: _viewTitle,
                subtitle: _viewSubtitle,
                action: _viewIndex == 2
                    ? FilledButton.icon(
                        onPressed: _showShoppingItemSheet,
                        icon: const Icon(Icons.add),
                        label: const Text('添加'),
                      )
                    : null,
              ),
              PageSection(
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
                          ButtonSegment(
                            value: 2,
                            label: Text('采购'),
                            icon: Icon(Icons.shopping_cart_outlined),
                          ),
                        ],
                        selected: {_viewIndex},
                        onSelectionChanged: (selection) {
                          setState(() {
                            _viewIndex = selection.first;
                            _focus = null;
                          });
                          _syncItemsRoute();
                        },
                      ),
                    ),
                    const SizedBox(height: AppSpacing.cardGap),
                    if (_viewIndex != 2 && _focus == null) ...[
                      TextField(
                        controller: _searchController,
                        textInputAction: TextInputAction.search,
                        decoration: const InputDecoration(
                          prefixIcon: Icon(Icons.search),
                          labelText: '搜索物品',
                        ),
                        onChanged: (_) => setState(() {}),
                      ),
                      const SizedBox(height: AppSpacing.cardGap),
                    ],
                    if (_viewIndex == 0 && _focus == null)
                      SingleChildScrollView(
                        scrollDirection: Axis.horizontal,
                        child: Row(
                          children: [
                            Padding(
                              padding: const EdgeInsets.only(right: 8),
                              child: ChoiceChip(
                                label: const Text('全部'),
                                selected: _categoryId == null,
                                onSelected: (_) {
                                  setState(() {
                                    _categoryId = null;
                                    _focus = null;
                                  });
                                  _syncItemsRoute();
                                },
                              ),
                            ),
                            ...widget.controller.categories.map(
                              (category) => Padding(
                                padding: const EdgeInsets.only(right: 8),
                                child: ChoiceChip(
                                  label: Text(category.name),
                                  selected: _categoryId == category.id,
                                  avatar: Icon(
                                    iconForName(category.icon),
                                    size: 18,
                                  ),
                                  onSelected: (_) {
                                    setState(() {
                                      _categoryId = category.id;
                                      _focus = null;
                                    });
                                    _syncItemsRoute();
                                  },
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),
                    const SizedBox(height: AppSpacing.sectionGap),
                    if (_viewIndex == 0 &&
                        _focus == null &&
                        widget.controller.expiringItems.isNotEmpty) ...[
                      _FreshnessStrip(
                        items: widget.controller.expiringItems,
                        onItemTap: _openInventoryItem,
                      ),
                      const SizedBox(height: AppSpacing.sectionGap),
                    ],
                    if (_viewIndex == 0 && _focus != null)
                      _FocusedInventoryList(
                        title: _focusTitle!,
                        items: focusedItems,
                        onClear: () {
                          setState(() => _focus = null);
                          _syncItemsRoute();
                        },
                        onTap: _openInventoryItem,
                        onAddShopping: _addInventoryToShopping,
                      )
                    else if (_viewIndex == 2)
                      _ShoppingListView(
                        suggestions: widget.controller.shoppingSuggestions,
                        items: widget.controller.shoppingListItems,
                        onAddSuggestion: _addShoppingSuggestion,
                        onToggle: _toggleShoppingItem,
                        onQuantityChanged: _changeShoppingQuantity,
                        onEdit: _showShoppingItemSheet,
                        onDelete: _deleteShoppingItem,
                        onConvertChecked: _convertCheckedShoppingItems,
                      )
                    else if (_viewIndex == 0 && items.isEmpty)
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
                            onAddShopping: () => _addRegisteredToShopping(item),
                            onTap: () async {
                              setWebRouteState('/items/wiki/${item.wikiId}');
                              await Navigator.of(context).push(
                                MaterialPageRoute(
                                  settings: RouteSettings(
                                    name: '/items/wiki/${item.wikiId}',
                                  ),
                                  builder: (_) => ItemWikiDetailScreen(
                                    controller: widget.controller,
                                    wikiId: item.wikiId,
                                  ),
                                ),
                              );
                              _syncItemsRoute(replace: true);
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
                            onAddShopping: () => _addInventoryToShopping(item),
                            onTap: () => _openInventoryItem(item),
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
    );
  }

  List<InventoryItem> _focusedInventoryItems() {
    final items = switch (_focus) {
      ItemsScreenFocus.expired => widget.controller.todayActionItems.where(
          (item) {
            final days = item.daysUntilExpiry;
            return days != null && days < 0;
          },
        ),
      ItemsScreenFocus.dueToday => widget.controller.todayActionItems.where(
          (item) => item.daysUntilExpiry == 0,
        ),
      ItemsScreenFocus.reminderDue => widget.controller.todayActionItems.where(
          (item) => item.shouldRemind,
        ),
      ItemsScreenFocus.expiring => widget.controller.expiringItems,
      ItemsScreenFocus.cleanup => [
          ...widget.controller.expiringItems,
          ...widget.controller.todayActionItems,
        ],
      null => const Iterable<InventoryItem>.empty(),
    };
    final unique = <String, InventoryItem>{};
    for (final item in items) {
      unique[item.id] = item;
    }
    return unique.values.toList();
  }

  Future<void> _openInventoryItem(InventoryItem item) async {
    setWebRouteState('/items/item/${item.id}');
    await Navigator.of(context).push(
      MaterialPageRoute(
        settings: RouteSettings(name: '/items/item/${item.id}'),
        builder: (_) => ItemDetailScreen(
          controller: widget.controller,
          itemId: item.id,
        ),
      ),
    );
    _syncItemsRoute(replace: true);
    if (mounted) {
      await widget.controller.refresh();
    }
  }

  void _syncItemsRoute({bool replace = false}) {
    setWebRouteState(_routeForCurrentState(), replace: replace);
  }

  String _routeForCurrentState() {
    final query = <String, String>{};
    final view = switch (_viewIndex) {
      1 => 'history',
      2 => 'shopping',
      _ => null,
    };
    final focus = switch (_focus) {
      ItemsScreenFocus.expired => 'expired',
      ItemsScreenFocus.dueToday => 'dueToday',
      ItemsScreenFocus.reminderDue => 'reminderDue',
      ItemsScreenFocus.expiring => 'expiring',
      ItemsScreenFocus.cleanup => 'cleanup',
      null => null,
    };
    if (view != null) {
      query['view'] = view;
    }
    if (focus != null) {
      query['focus'] = focus;
    }
    if (_categoryId != null && _categoryId!.isNotEmpty) {
      query['category'] = _categoryId!;
    }
    final keyword = _searchController.text.trim();
    if (keyword.isNotEmpty) {
      query['q'] = keyword;
    }
    return Uri(
      path: '/items',
      queryParameters: query.isEmpty ? null : query,
    ).toString();
  }

  List<RegisteredItem> _filteredItems() {
    final keyword = _searchController.text.trim().toLowerCase();
    return widget.controller.registeredItems.where((item) {
      final matchesCategory =
          _categoryId == null || item.categoryId == _categoryId;
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

  Future<void> _addShoppingSuggestion(ShoppingSuggestion suggestion) async {
    await widget.controller.addShoppingSuggestion(suggestion);
    if (!mounted) {
      return;
    }
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text('已加入采购清单：${suggestion.name}')),
    );
  }

  Future<void> _addRegisteredToShopping(RegisteredItem item) async {
    await widget.controller.addRegisteredItemToShoppingList(item);
    if (!mounted) {
      return;
    }
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text('已加入采购清单：${item.name}')),
    );
  }

  Future<void> _addInventoryToShopping(InventoryItem item) async {
    await widget.controller.addInventoryItemToShoppingList(item);
    if (!mounted) {
      return;
    }
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text('已加入采购清单：${item.name}')),
    );
  }

  Future<void> _toggleShoppingItem(
    ShoppingListItem item,
    bool isChecked,
  ) {
    return widget.controller.setShoppingListItemChecked(
      item.id,
      isChecked: isChecked,
    );
  }

  Future<void> _changeShoppingQuantity(
    ShoppingListItem item,
    int delta,
  ) async {
    final nextQuantity = item.quantity + delta;
    if (nextQuantity <= 0) {
      await _deleteShoppingItem(item);
      return;
    }
    await widget.controller.updateShoppingListItem(
      itemId: item.id,
      draft: ShoppingListDraft(
        name: item.name,
        categoryId: item.categoryId,
        sourceWikiId: item.sourceWikiId,
        sourceItemId: item.sourceItemId,
        quantity: nextQuantity,
        unit: item.unit,
        note: item.note,
        source: item.source,
      ),
    );
  }

  Future<void> _deleteShoppingItem(ShoppingListItem item) async {
    final confirmed = await showAppConfirmDialog(
      context,
      title: '删除采购项',
      message: '确定从采购清单删除“${item.name}”吗？',
      confirmLabel: '删除',
      isDestructive: true,
    );
    if (!confirmed) {
      return;
    }
    await widget.controller.deleteShoppingListItem(item.id);
  }

  Future<void> _convertCheckedShoppingItems() async {
    final checkedCount = widget.controller.shoppingListItems
        .where((item) => item.isChecked && item.convertedAt == null)
        .length;
    final confirmed = await showAppConfirmDialog(
      context,
      title: '采购项入库',
      message: '确定将 $checkedCount 个已买到采购项转为库存记录吗？',
      confirmLabel: '确认入库',
    );
    if (!confirmed) {
      return;
    }
    final converted =
        await widget.controller.convertCheckedShoppingItemsToInventory();
    if (!mounted) {
      return;
    }
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(
          converted == 0 ? '没有已勾选的采购项' : '已入库 $converted 项',
        ),
      ),
    );
  }

  Future<void> _showShoppingItemSheet([ShoppingListItem? item]) async {
    final draft = await showModalBottomSheet<ShoppingListDraft>(
      context: context,
      isScrollControlled: true,
      showDragHandle: true,
      builder: (context) => _ShoppingItemSheet(
        categories: widget.controller.categories,
        item: item,
      ),
    );
    if (draft == null) {
      return;
    }
    if (item == null) {
      await widget.controller.addShoppingListItem(draft);
    } else {
      await widget.controller.updateShoppingListItem(
        itemId: item.id,
        draft: draft,
      );
    }
  }
}

class _ShoppingListView extends StatelessWidget {
  const _ShoppingListView({
    required this.suggestions,
    required this.items,
    required this.onAddSuggestion,
    required this.onToggle,
    required this.onQuantityChanged,
    required this.onEdit,
    required this.onDelete,
    required this.onConvertChecked,
  });

  final List<ShoppingSuggestion> suggestions;
  final List<ShoppingListItem> items;
  final ValueChanged<ShoppingSuggestion> onAddSuggestion;
  final Future<void> Function(ShoppingListItem item, bool isChecked) onToggle;
  final Future<void> Function(ShoppingListItem item, int delta)
      onQuantityChanged;
  final ValueChanged<ShoppingListItem> onEdit;
  final ValueChanged<ShoppingListItem> onDelete;
  final VoidCallback onConvertChecked;

  @override
  Widget build(BuildContext context) {
    final pending = items.where((item) => !item.isChecked).toList();
    final checked = items.where((item) => item.isChecked).toList();
    if (suggestions.isEmpty && items.isEmpty) {
      return const EmptyState(
        icon: Icons.shopping_cart_outlined,
        title: '采购清单是空的',
        message: '低库存、已用完和常买物品会在这里形成建议。',
      );
    }
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (suggestions.isNotEmpty) ...[
          _SuggestionRail(
            suggestions: suggestions,
            onAddSuggestion: onAddSuggestion,
          ),
          const SizedBox(height: 16),
        ],
        _ShoppingSection(
          title: '待采购',
          items: pending,
          emptyMessage: '暂时没有待采购物品。',
          onToggle: onToggle,
          onQuantityChanged: onQuantityChanged,
          onEdit: onEdit,
          onDelete: onDelete,
        ),
        const SizedBox(height: 12),
        _ShoppingSection(
          title: '已买到',
          items: checked,
          emptyMessage: '勾选已买到的物品后，可一键入库。',
          onToggle: onToggle,
          onQuantityChanged: onQuantityChanged,
          onEdit: onEdit,
          onDelete: onDelete,
          trailing: checked.isEmpty
              ? null
              : FilledButton.icon(
                  onPressed: onConvertChecked,
                  icon: const Icon(Icons.move_to_inbox_outlined),
                  label: const Text('入库'),
                ),
        ),
      ],
    );
  }
}

class _FocusedInventoryList extends StatelessWidget {
  const _FocusedInventoryList({
    required this.title,
    required this.items,
    required this.onClear,
    required this.onTap,
    required this.onAddShopping,
  });

  final String title;
  final List<InventoryItem> items;
  final VoidCallback onClear;
  final ValueChanged<InventoryItem> onTap;
  final ValueChanged<InventoryItem> onAddShopping;

  @override
  Widget build(BuildContext context) {
    return SectionCard(
      color: AppColors.surfaceWarm,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Text(
                  title,
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        color: AppColors.textPrimary,
                        fontWeight: FontWeight.w900,
                      ),
                ),
              ),
              TextButton.icon(
                onPressed: onClear,
                icon: const Icon(Icons.close),
                label: const Text('返回目录'),
              ),
            ],
          ),
          const SizedBox(height: AppSpacing.cardGap),
          if (items.isEmpty)
            const EmptyState(
              icon: Icons.task_alt_outlined,
              title: '没有待处理库存',
              message: '当前筛选条件下没有需要处理的批次。',
            )
          else
            ...items.map(
              (item) => Padding(
                padding: const EdgeInsets.only(bottom: 10),
                child: _FocusedInventoryTile(
                  item: item,
                  onTap: () => onTap(item),
                  onAddShopping: () => onAddShopping(item),
                ),
              ),
            ),
        ],
      ),
    );
  }
}

class _FocusedInventoryTile extends StatelessWidget {
  const _FocusedInventoryTile({
    required this.item,
    required this.onTap,
    required this.onAddShopping,
  });

  final InventoryItem item;
  final VoidCallback onTap;
  final VoidCallback onAddShopping;

  @override
  Widget build(BuildContext context) {
    final status = _FreshnessStatus.fromDate(item.expiryDate);
    return SectionCard(
      onTap: onTap,
      padding: const EdgeInsets.all(14),
      child: Row(
        children: [
          Container(
            width: 46,
            height: 46,
            decoration: BoxDecoration(
              color: status.backgroundColor,
              borderRadius: BorderRadius.circular(AppRadii.large),
            ),
            child: Icon(iconForName(item.wikiIcon), color: status.color),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  item.name,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: Theme.of(context).textTheme.titleSmall?.copyWith(
                        color: AppColors.textPrimary,
                        fontWeight: FontWeight.w900,
                      ),
                ),
                const SizedBox(height: 4),
                Text(
                  [
                    '${item.quantity}${item.unit ?? ''}',
                    item.categoryName ?? '未分类',
                    if (item.storageLocation != null) item.storageLocation!,
                  ].join(' · '),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: AppColors.textSecondary,
                      ),
                ),
              ],
            ),
          ),
          const SizedBox(width: 8),
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              ConstrainedBox(
                constraints: const BoxConstraints(maxWidth: 112),
                child: StatusPill(
                  label: status.label,
                  color: status.color,
                  backgroundColor: status.backgroundColor,
                ),
              ),
              IconButton(
                tooltip: '加入采购清单',
                onPressed: onAddShopping,
                icon: const Icon(Icons.add_shopping_cart_outlined),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _SuggestionRail extends StatelessWidget {
  const _SuggestionRail({
    required this.suggestions,
    required this.onAddSuggestion,
  });

  final List<ShoppingSuggestion> suggestions;
  final ValueChanged<ShoppingSuggestion> onAddSuggestion;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Text(
              '补货建议',
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.w900,
                  ),
            ),
            const SizedBox(width: 8),
            StatusPill(
              label: '${suggestions.length}',
              color: AppColors.primary,
              backgroundColor: AppColors.primaryContainer,
            ),
          ],
        ),
        const SizedBox(height: 10),
        SizedBox(
          height: 138,
          child: ListView.separated(
            scrollDirection: Axis.horizontal,
            itemCount: suggestions.length,
            separatorBuilder: (context, index) => const SizedBox(width: 10),
            itemBuilder: (context, index) {
              final suggestion = suggestions[index];
              return SizedBox(
                width: 196,
                child: SectionCard(
                  padding: const EdgeInsets.all(14),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Container(
                            width: 38,
                            height: 38,
                            decoration: BoxDecoration(
                              color: AppColors.primaryContainer,
                              borderRadius: BorderRadius.circular(14),
                            ),
                            child: Icon(
                              iconForName(suggestion.categoryIcon),
                              color: AppColors.primary,
                            ),
                          ),
                          const SizedBox(width: 10),
                          Expanded(
                            child: Text(
                              suggestion.name,
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                              style: Theme.of(context)
                                  .textTheme
                                  .titleSmall
                                  ?.copyWith(fontWeight: FontWeight.w900),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 6),
                      Text(
                        suggestion.reason,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(
                              color: AppColors.textSecondary,
                            ),
                      ),
                      const Spacer(),
                      SizedBox(
                        width: double.infinity,
                        child: OutlinedButton.icon(
                          onPressed: () => onAddSuggestion(suggestion),
                          icon: const Icon(Icons.add_shopping_cart_outlined),
                          label: const Text('加入清单'),
                        ),
                      ),
                    ],
                  ),
                ),
              );
            },
          ),
        ),
      ],
    );
  }
}

class _ShoppingSection extends StatelessWidget {
  const _ShoppingSection({
    required this.title,
    required this.items,
    required this.emptyMessage,
    required this.onToggle,
    required this.onQuantityChanged,
    required this.onEdit,
    required this.onDelete,
    this.trailing,
  });

  final String title;
  final List<ShoppingListItem> items;
  final String emptyMessage;
  final Future<void> Function(ShoppingListItem item, bool isChecked) onToggle;
  final Future<void> Function(ShoppingListItem item, int delta)
      onQuantityChanged;
  final ValueChanged<ShoppingListItem> onEdit;
  final ValueChanged<ShoppingListItem> onDelete;
  final Widget? trailing;

  @override
  Widget build(BuildContext context) {
    final groups = _groupShoppingItems(items);
    return SectionCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Text(
                title,
                style: Theme.of(context).textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.w900,
                    ),
              ),
              const SizedBox(width: 8),
              StatusPill(
                label: '${items.length}',
                color: AppColors.secondary,
                backgroundColor: AppColors.secondaryContainer,
              ),
              const Spacer(),
              if (trailing != null) trailing!,
            ],
          ),
          if (items.isEmpty) ...[
            const SizedBox(height: 12),
            Text(
              emptyMessage,
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: AppColors.textSecondary,
                  ),
            ),
          ] else
            for (final entry in groups.entries) ...[
              const SizedBox(height: AppSpacing.fieldGap),
              _ShoppingGroupHeader(
                name: entry.key,
                count: entry.value.length,
              ),
              const SizedBox(height: 4),
              for (final item in entry.value)
                _ShoppingItemRow(
                  item: item,
                  onToggle: onToggle,
                  onQuantityChanged: onQuantityChanged,
                  onEdit: onEdit,
                  onDelete: onDelete,
                ),
            ],
        ],
      ),
    );
  }
}

class _ShoppingGroupHeader extends StatelessWidget {
  const _ShoppingGroupHeader({required this.name, required this.count});

  final String name;
  final int count;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Container(
          width: 8,
          height: 8,
          decoration: const BoxDecoration(
            color: AppColors.primary,
            shape: BoxShape.circle,
          ),
        ),
        const SizedBox(width: 8),
        Text(
          name,
          style: Theme.of(context).textTheme.labelLarge?.copyWith(
                color: AppColors.textSecondary,
                fontWeight: FontWeight.w800,
              ),
        ),
        const SizedBox(width: 6),
        Text(
          '$count',
          style: Theme.of(context).textTheme.labelMedium?.copyWith(
                color: AppColors.textHint,
              ),
        ),
      ],
    );
  }
}

class _ShoppingItemRow extends StatelessWidget {
  const _ShoppingItemRow({
    required this.item,
    required this.onToggle,
    required this.onQuantityChanged,
    required this.onEdit,
    required this.onDelete,
  });

  final ShoppingListItem item;
  final Future<void> Function(ShoppingListItem item, bool isChecked) onToggle;
  final Future<void> Function(ShoppingListItem item, int delta)
      onQuantityChanged;
  final ValueChanged<ShoppingListItem> onEdit;
  final ValueChanged<ShoppingListItem> onDelete;

  @override
  Widget build(BuildContext context) {
    void toggle() {
      onToggle(item, !item.isChecked);
    }

    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Row(
        children: [
          SizedBox(
            width: 44,
            height: 44,
            child: Checkbox(
              value: item.isChecked,
              materialTapTargetSize: MaterialTapTargetSize.padded,
              onChanged: (value) => onToggle(item, value ?? false),
            ),
          ),
          const SizedBox(width: 4),
          Expanded(
            child: GestureDetector(
              behavior: HitTestBehavior.opaque,
              onTap: toggle,
              child: Padding(
                padding: const EdgeInsets.symmetric(vertical: 4),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      item.name,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: Theme.of(context).textTheme.titleSmall?.copyWith(
                            fontWeight: FontWeight.w800,
                            decoration: item.isChecked
                                ? TextDecoration.lineThrough
                                : null,
                          ),
                    ),
                    const SizedBox(height: 3),
                    Text(
                      [
                        item.quantityLabel,
                        if (item.note != null) '备注：${item.note}',
                      ].join(' · '),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                            color: AppColors.textSecondary,
                          ),
                    ),
                  ],
                ),
              ),
            ),
          ),
          const SizedBox(width: 8),
          _QuantityStepper(
            quantity: item.quantity,
            onDecrease: () => onQuantityChanged(item, -1),
            onIncrease: () => onQuantityChanged(item, 1),
          ),
          PopupMenuButton<String>(
            tooltip: '更多操作',
            onSelected: (value) {
              if (value == 'edit') {
                onEdit(item);
              }
              if (value == 'delete') {
                onDelete(item);
              }
            },
            itemBuilder: (context) => const [
              PopupMenuItem(
                value: 'edit',
                child: Text('编辑'),
              ),
              PopupMenuItem(
                value: 'delete',
                child: Text('删除'),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _QuantityStepper extends StatelessWidget {
  const _QuantityStepper({
    required this.quantity,
    required this.onDecrease,
    required this.onIncrease,
  });

  final int quantity;
  final VoidCallback onDecrease;
  final VoidCallback onIncrease;

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 44,
      decoration: BoxDecoration(
        border: Border.all(color: AppColors.divider),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          SizedBox(
            width: 40,
            height: 44,
            child: IconButton(
              padding: EdgeInsets.zero,
              constraints: const BoxConstraints.tightFor(
                width: 40,
                height: 44,
              ),
              onPressed: onDecrease,
              icon: const Icon(Icons.remove, size: 18),
            ),
          ),
          SizedBox(
            width: 32,
            child: Text(
              '$quantity',
              textAlign: TextAlign.center,
              style: Theme.of(context).textTheme.labelLarge?.copyWith(
                    fontWeight: FontWeight.w900,
                  ),
            ),
          ),
          SizedBox(
            width: 40,
            height: 44,
            child: IconButton(
              padding: EdgeInsets.zero,
              constraints: const BoxConstraints.tightFor(
                width: 40,
                height: 44,
              ),
              onPressed: onIncrease,
              icon: const Icon(Icons.add, size: 18),
            ),
          ),
        ],
      ),
    );
  }
}

class _ShoppingItemSheet extends StatefulWidget {
  const _ShoppingItemSheet({
    required this.categories,
    this.item,
  });

  final List<ItemWikiCategory> categories;
  final ShoppingListItem? item;

  @override
  State<_ShoppingItemSheet> createState() => _ShoppingItemSheetState();
}

class _ShoppingItemSheetState extends State<_ShoppingItemSheet> {
  final _formKey = GlobalKey<FormState>();
  late final TextEditingController _nameController;
  late final TextEditingController _quantityController;
  late final TextEditingController _unitController;
  late final TextEditingController _noteController;
  String? _categoryId;

  @override
  void initState() {
    super.initState();
    final item = widget.item;
    _nameController = TextEditingController(text: item?.name ?? '');
    _quantityController = TextEditingController(
      text: '${item?.quantity ?? 1}',
    );
    _unitController = TextEditingController(text: item?.unit ?? '');
    _noteController = TextEditingController(text: item?.note ?? '');
    _categoryId = item?.categoryId;
  }

  @override
  void dispose() {
    _nameController.dispose();
    _quantityController.dispose();
    _unitController.dispose();
    _noteController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final bottom = MediaQuery.viewInsetsOf(context).bottom;
    return SafeArea(
      child: Padding(
        padding: EdgeInsets.fromLTRB(20, 0, 20, 20 + bottom),
        child: Form(
          key: _formKey,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Row(
                children: [
                  Expanded(
                    child: Text(
                      widget.item == null ? '添加采购项' : '编辑采购项',
                      style: Theme.of(context).textTheme.titleLarge?.copyWith(
                            fontWeight: FontWeight.w900,
                          ),
                    ),
                  ),
                  IconButton(
                    tooltip: '关闭',
                    onPressed: () => Navigator.of(context).pop(),
                    icon: const Icon(Icons.close),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              TextFormField(
                controller: _nameController,
                textInputAction: TextInputAction.next,
                decoration: const InputDecoration(
                  labelText: '物品名称',
                  prefixIcon: Icon(Icons.shopping_bag_outlined),
                ),
                validator: (value) {
                  if (value == null || value.trim().isEmpty) {
                    return '请输入物品名称';
                  }
                  return null;
                },
              ),
              const SizedBox(height: 12),
              DropdownButtonFormField<String?>(
                initialValue: _categoryId,
                decoration: const InputDecoration(
                  labelText: '分类',
                  prefixIcon: Icon(Icons.category_outlined),
                ),
                items: [
                  const DropdownMenuItem<String?>(
                    child: Text('未分类'),
                  ),
                  for (final category in widget.categories)
                    DropdownMenuItem<String?>(
                      value: category.id,
                      child: Text(category.name),
                    ),
                ],
                onChanged: (value) => setState(() => _categoryId = value),
              ),
              const SizedBox(height: 12),
              Row(
                children: [
                  Expanded(
                    child: TextFormField(
                      controller: _quantityController,
                      keyboardType: TextInputType.number,
                      decoration: const InputDecoration(
                        labelText: '数量',
                        prefixIcon: Icon(Icons.numbers_outlined),
                      ),
                      validator: (value) {
                        final parsed = int.tryParse(value ?? '');
                        if (parsed == null || parsed <= 0) {
                          return '请输入大于 0 的整数';
                        }
                        return null;
                      },
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: TextFormField(
                      controller: _unitController,
                      decoration: const InputDecoration(
                        labelText: '单位',
                        prefixIcon: Icon(Icons.straighten_outlined),
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              TextFormField(
                controller: _noteController,
                minLines: 2,
                maxLines: 3,
                decoration: const InputDecoration(
                  labelText: '备注',
                  alignLabelWithHint: true,
                  prefixIcon: Icon(Icons.notes_outlined),
                ),
              ),
              const SizedBox(height: 16),
              SizedBox(
                width: double.infinity,
                child: FilledButton.icon(
                  onPressed: _submit,
                  icon: const Icon(Icons.check),
                  label: const Text('保存'),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  void _submit() {
    if (!_formKey.currentState!.validate()) {
      return;
    }
    Navigator.of(context).pop(
      ShoppingListDraft(
        name: _nameController.text,
        categoryId: _categoryId,
        sourceWikiId: widget.item?.sourceWikiId,
        sourceItemId: widget.item?.sourceItemId,
        quantity: int.parse(_quantityController.text),
        unit: _unitController.text,
        note: _noteController.text,
        source: widget.item?.source ?? 'manual',
      ),
    );
  }
}

Map<String, List<ShoppingListItem>> _groupShoppingItems(
  List<ShoppingListItem> items,
) {
  final groups = <String, List<ShoppingListItem>>{};
  for (final item in items) {
    final name = item.categoryName ?? '未分类';
    groups.putIfAbsent(name, () => []).add(item);
  }
  return groups;
}

class _RegisteredItemTile extends StatelessWidget {
  const _RegisteredItemTile({
    required this.item,
    required this.onTap,
    required this.onAddShopping,
  });

  final RegisteredItem item;
  final VoidCallback onTap;
  final VoidCallback onAddShopping;

  @override
  Widget build(BuildContext context) {
    final freshness = _FreshnessStatus.fromDate(item.nextExpiryDate);
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
                const SizedBox(height: 8),
                Wrap(
                  spacing: 8,
                  runSpacing: 6,
                  children: [
                    StatusPill(
                      label: item.storageLocation ?? '未设置位置',
                      color: AppColors.primaryDark,
                      backgroundColor: AppColors.primaryContainer,
                    ),
                    StatusPill(
                      label: freshness.label,
                      color: freshness.color,
                      backgroundColor: freshness.backgroundColor,
                    ),
                  ],
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
              IconButton(
                tooltip: '加入采购清单',
                onPressed: onAddShopping,
                icon: const Icon(Icons.add_shopping_cart_outlined),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _FreshnessStrip extends StatelessWidget {
  const _FreshnessStrip({required this.items, required this.onItemTap});

  final List<InventoryItem> items;
  final ValueChanged<InventoryItem> onItemTap;

  @override
  Widget build(BuildContext context) {
    return SectionCard(
      color: AppColors.surfaceWarm,
      padding: const EdgeInsets.all(14),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Text(
                  '即将过期',
                  style: Theme.of(context).textTheme.titleSmall?.copyWith(
                        color: AppColors.textPrimary,
                        fontWeight: FontWeight.w900,
                      ),
                ),
              ),
              StatusPill(
                label: '${items.length} 项',
                color: AppColors.warning,
                backgroundColor: AppColors.warningContainer,
              ),
            ],
          ),
          const SizedBox(height: 12),
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            child: Row(
              children: items.take(6).map((item) {
                final status = _FreshnessStatus.fromDate(item.expiryDate);
                return Padding(
                  padding: const EdgeInsets.only(right: 10),
                  child: SizedBox(
                    width: 164,
                    child: SectionCard(
                      onTap: () => onItemTap(item),
                      color: status.backgroundColor.withValues(alpha: 0.55),
                      padding: const EdgeInsets.all(12),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: [
                              Container(
                                width: 34,
                                height: 34,
                                decoration: BoxDecoration(
                                  color: AppColors.surface,
                                  borderRadius:
                                      BorderRadius.circular(AppRadii.medium),
                                ),
                                child: Icon(
                                  iconForName(item.wikiIcon),
                                  color: status.color,
                                  size: 20,
                                ),
                              ),
                              const Spacer(),
                              Text(
                                '${item.quantity}${item.unit ?? ''}',
                                style: Theme.of(context)
                                    .textTheme
                                    .labelLarge
                                    ?.copyWith(
                                      color: status.color,
                                      fontWeight: FontWeight.w900,
                                    ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 10),
                          Text(
                            item.name,
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                            style: Theme.of(context)
                                .textTheme
                                .titleSmall
                                ?.copyWith(
                                  color: AppColors.textPrimary,
                                  fontWeight: FontWeight.w900,
                                ),
                          ),
                          const SizedBox(height: 3),
                          Text(
                            status.label,
                            style:
                                Theme.of(context).textTheme.bodySmall?.copyWith(
                                      color: AppColors.textSecondary,
                                    ),
                          ),
                        ],
                      ),
                    ),
                  ),
                );
              }).toList(),
            ),
          ),
        ],
      ),
    );
  }
}

class _FreshnessStatus {
  const _FreshnessStatus({
    required this.label,
    required this.color,
    required this.backgroundColor,
  });

  final String label;
  final Color color;
  final Color backgroundColor;

  factory _FreshnessStatus.fromDate(DateTime? expiryDate) {
    if (expiryDate == null) {
      return const _FreshnessStatus(
        label: '无到期日',
        color: AppColors.textHint,
        backgroundColor: AppColors.surfaceVariant,
      );
    }
    final today = DateTime.now();
    final dateOnly = DateTime(today.year, today.month, today.day);
    final days = expiryDate.difference(dateOnly).inDays;
    if (days < 0) {
      return _FreshnessStatus(
        label: '已过期 ${days.abs()} 天',
        color: AppColors.error,
        backgroundColor: AppColors.errorContainer,
      );
    }
    if (days == 0) {
      return const _FreshnessStatus(
        label: '今天到期',
        color: AppColors.warning,
        backgroundColor: AppColors.warningContainer,
      );
    }
    if (days <= 7) {
      return _FreshnessStatus(
        label: '$days 天后到期',
        color: AppColors.warning,
        backgroundColor: AppColors.warningContainer,
      );
    }
    return _FreshnessStatus(
      label: DateFormat('MM-dd 到期').format(expiryDate),
      color: AppColors.primaryDark,
      backgroundColor: AppColors.primaryContainer,
    );
  }
}

class _HistoryItemTile extends StatelessWidget {
  const _HistoryItemTile({
    required this.item,
    required this.onTap,
    required this.onAddShopping,
  });

  final InventoryItem item;
  final VoidCallback onTap;
  final VoidCallback onAddShopping;

  @override
  Widget build(BuildContext context) {
    final isConsumed = item.status == ItemStatus.consumed;
    final statusLabel = isConsumed
        ? '已消耗'
        : item.isExpired
            ? '已过期'
            : item.status.label;
    final statusColor = isConsumed ? AppColors.success : AppColors.error;
    final statusBackground =
        isConsumed ? AppColors.successContainer : AppColors.errorContainer;

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
              isConsumed
                  ? Icons.check_circle_outline
                  : Icons.warning_amber_outlined,
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
                  '${item.quantity}${item.unit ?? ''} · '
                  '过期 ${formatDate(item.expiryDate)}',
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
              StatusPill(
                label: statusLabel,
                color: statusColor,
                backgroundColor: statusBackground,
              ),
              IconButton(
                tooltip: '加入采购清单',
                onPressed: onAddShopping,
                icon: const Icon(Icons.add_shopping_cart_outlined),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
