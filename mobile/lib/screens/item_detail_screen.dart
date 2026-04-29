import 'package:flutter/material.dart';

import '../data/inventory_controller.dart';
import '../models/inventory_item.dart';
import '../models/item_status.dart';
import '../theme/app_theme.dart';
import '../utils/date_formatters.dart';
import '../widgets/app_cards.dart';
import '../widgets/icon_mapper.dart';
import 'item_edit_screen.dart';

class ItemDetailScreen extends StatefulWidget {
  const ItemDetailScreen({
    super.key,
    required this.controller,
    required this.itemId,
  });

  final InventoryController controller;
  final String itemId;

  @override
  State<ItemDetailScreen> createState() => _ItemDetailScreenState();
}

class _ItemDetailScreenState extends State<ItemDetailScreen> {
  late Future<InventoryItem?> _future;
  bool _working = false;

  @override
  void initState() {
    super.initState();
    _future = _load();
  }

  Future<InventoryItem?> _load() {
    return widget.controller.repository.getItem(widget.itemId);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('库存详情'),
        actions: [
          FutureBuilder<InventoryItem?>(
            future: _future,
            builder: (context, snapshot) {
              final item = snapshot.data;
              if (item == null) {
                return const SizedBox.shrink();
              }
              return Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  IconButton(
                    tooltip: '编辑库存',
                    onPressed: _working ? null : () => _editItem(item),
                    icon: const Icon(Icons.edit_outlined),
                  ),
                  IconButton(
                    tooltip: '删除库存',
                    onPressed: _working ? null : () => _deleteItem(item),
                    icon: const Icon(Icons.delete_outline),
                  ),
                ],
              );
            },
          ),
        ],
      ),
      body: FutureBuilder<InventoryItem?>(
        future: _future,
        builder: (context, snapshot) {
          if (snapshot.connectionState != ConnectionState.done) {
            return const Center(child: CircularProgressIndicator());
          }
          final item = snapshot.data;
          if (item == null) {
            return const Center(child: Text('库存记录不存在'));
          }
          return ListView(
            padding: const EdgeInsets.fromLTRB(20, 8, 20, 24),
            children: [
              ContentWidth(child: _Header(item: item)),
              const SizedBox(height: 14),
              ContentWidth(child: _Facts(item: item)),
              const SizedBox(height: 18),
              if (item.status == ItemStatus.active) ...[
                ContentWidth(
                  child: Row(
                    children: [
                      Expanded(
                        child: OutlinedButton.icon(
                          onPressed:
                              _working ? null : () => _changeQuantity(-1),
                          icon: const Icon(Icons.remove),
                          label: const Text('减少'),
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: OutlinedButton.icon(
                          onPressed: _working ? null : () => _changeQuantity(1),
                          icon: const Icon(Icons.add),
                          label: const Text('增加'),
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 12),
                ContentWidth(
                  child: SizedBox(
                    width: double.infinity,
                    child: FilledButton.icon(
                      onPressed: _working ? null : _markConsumed,
                      icon: const Icon(Icons.check_circle_outline),
                      label: const Text('标记已消耗'),
                    ),
                  ),
                ),
              ] else
                ContentWidth(
                  child: SizedBox(
                    width: double.infinity,
                    child: FilledButton.tonalIcon(
                      onPressed: _working ? null : _restoreItem,
                      icon: const Icon(Icons.restore_outlined),
                      label: const Text('恢复为使用中'),
                    ),
                  ),
                ),
            ],
          );
        },
      ),
    );
  }

  Future<void> _changeQuantity(int delta) async {
    setState(() => _working = true);
    await widget.controller.updateItemQuantity(widget.itemId, delta);
    if (mounted) {
      setState(() {
        _future = _load();
        _working = false;
      });
    }
  }

  Future<void> _markConsumed() async {
    setState(() => _working = true);
    await widget.controller.markAsConsumed(widget.itemId);
    if (mounted) {
      Navigator.of(context).pop();
    }
  }

  Future<void> _editItem(InventoryItem item) async {
    final changed = await Navigator.of(context).push<bool>(
      MaterialPageRoute(
        builder: (_) => ItemEditScreen(
          controller: widget.controller,
          item: item,
        ),
      ),
    );
    if (changed == true && mounted) {
      setState(() => _future = _load());
    }
  }

  Future<void> _deleteItem(InventoryItem item) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('删除库存记录'),
        content: Text('确定删除“${item.name}”这条库存记录吗？'),
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
    setState(() => _working = true);
    await widget.controller.deleteItem(item.id);
    if (mounted) {
      Navigator.of(context).pop();
    }
  }

  Future<void> _restoreItem() async {
    setState(() => _working = true);
    await widget.controller.restoreItem(widget.itemId);
    if (mounted) {
      setState(() {
        _future = _load();
        _working = false;
      });
    }
  }
}

class _Header extends StatelessWidget {
  const _Header({required this.item});

  final InventoryItem item;

  @override
  Widget build(BuildContext context) {
    final days = item.daysUntilExpiry;
    final label = days == null
        ? '无到期日'
        : days < 0
            ? '已过期 ${days.abs()} 天'
            : days == 0
                ? '今天到期'
                : '$days 天后到期';

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
            child: Icon(iconForName(item.wikiIcon),
                color: AppColors.primary, size: 30),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  item.name,
                  style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                        fontWeight: FontWeight.w900,
                      ),
                ),
                const SizedBox(height: 6),
                Wrap(
                  spacing: 8,
                  runSpacing: 8,
                  children: [
                    StatusPill(
                      label: item.status.label,
                      color: AppColors.primary,
                      backgroundColor: AppColors.primaryContainer,
                    ),
                    StatusPill(
                      label: label,
                      color:
                          item.isExpired ? AppColors.error : AppColors.warning,
                      backgroundColor: item.isExpired
                          ? AppColors.errorContainer
                          : AppColors.warningContainer,
                      icon: Icons.schedule_outlined,
                    ),
                  ],
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _Facts extends StatelessWidget {
  const _Facts({required this.item});

  final InventoryItem item;

  @override
  Widget build(BuildContext context) {
    return SectionCard(
      child: Column(
        children: [
          _FactRow(label: '数量', value: '${item.quantity}${item.unit ?? ''}'),
          _FactRow(label: '分类', value: item.categoryName ?? '其他'),
          _FactRow(label: '购买日期', value: formatDate(item.purchaseDate)),
          _FactRow(label: '过期日期', value: formatDate(item.expiryDate)),
          _FactRow(label: '提醒日期', value: formatDate(item.reminderDate)),
          _FactRow(label: '提醒开关', value: item.isReminderEnabled ? '开启' : '关闭'),
          if (item.description != null && item.description!.isNotEmpty)
            _FactRow(label: '描述', value: item.description!),
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
        crossAxisAlignment: CrossAxisAlignment.start,
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
