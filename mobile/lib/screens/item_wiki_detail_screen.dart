import 'package:flutter/material.dart';

import '../data/inventory_controller.dart';
import '../models/inventory_item.dart';
import '../models/item_wiki.dart';
import '../theme/app_theme.dart';
import '../utils/date_formatters.dart';
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

  @override
  void initState() {
    super.initState();
    _future = _load();
  }

  Future<_WikiDetailData> _load() async {
    final wiki = await widget.controller.repository.getWiki(widget.wikiId);
    final items = await widget.controller.repository.getInventoryByWikiId(widget.wikiId);
    return _WikiDetailData(wiki: wiki, items: items);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('物品 Wiki'),
        actions: [
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
                    tooltip: '编辑 Wiki',
                    onPressed: () => _editWiki(wiki),
                    icon: const Icon(Icons.edit_outlined),
                  ),
                  IconButton(
                    tooltip: '删除 Wiki',
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
            return const Center(child: Text('Wiki 不存在'));
          }
          return RefreshIndicator(
            onRefresh: () async {
              setState(() => _future = _load());
              await _future;
            },
            child: ListView(
              padding: const EdgeInsets.fromLTRB(20, 8, 20, 24),
              children: [
                ContentWidth(
                  child: _WikiHeader(wiki: wiki),
                ),
                const SizedBox(height: 14),
                ContentWidth(
                  child: _WikiFacts(wiki: wiki),
                ),
                const SizedBox(height: 20),
                ContentWidth(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        '库存批次',
                        style: Theme.of(context).textTheme.titleLarge?.copyWith(
                              fontWeight: FontWeight.w800,
                            ),
                      ),
                      const SizedBox(height: 12),
                      if (data.items.isEmpty)
                        const EmptyState(
                          icon: Icons.inventory_2_outlined,
                          title: '暂无库存',
                          message: '这个 Wiki 条目下还没有具体库存记录。',
                        )
                      else
                        ...data.items.map(
                          (item) => Padding(
                            padding: const EdgeInsets.only(bottom: 10),
                            child: _BatchTile(
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
                                  setState(() => _future = _load());
                                }
                              },
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
      setState(() => _future = _load());
    }
  }

  Future<void> _deleteWiki(ItemWiki wiki) async {
    final inventoryCount = await widget.controller.repository.getWikiInventoryCount(wiki.id);
    if (!mounted) {
      return;
    }
    if (inventoryCount > 0) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('“${wiki.name}”下还有 $inventoryCount 条库存记录，不能删除')),
      );
      return;
    }

    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('删除 Wiki'),
        content: Text('确定删除“${wiki.name}”这个 Wiki 条目吗？'),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: const Text('取消'),
          ),
          FilledButton(
            onPressed: () => Navigator.of(context).pop(true),
            child: const Text('删除'),
          ),
        ],
      ),
    );
    if (confirmed != true) {
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
            value: wiki.suggestedExpiryDays == null ? '未设置' : '${wiki.suggestedExpiryDays} 天',
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
    required this.onTap,
  });

  final InventoryItem item;
  final VoidCallback onTap;

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
      onTap: onTap,
      child: Row(
        children: [
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
                  '购买 ${formatDate(item.purchaseDate)} · 过期 ${formatDate(item.expiryDate)}',
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                        color: AppColors.textSecondary,
                      ),
                ),
              ],
            ),
          ),
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

class _WikiDetailData {
  const _WikiDetailData({
    required this.wiki,
    required this.items,
  });

  final ItemWiki? wiki;
  final List<InventoryItem> items;
}
