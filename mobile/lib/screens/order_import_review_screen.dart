import 'package:flutter/material.dart';

import '../data/inventory_controller.dart';
import '../models/order_recognition.dart';
import '../theme/app_theme.dart';
import '../widgets/app_cards.dart';

class OrderImportReviewScreen extends StatefulWidget {
  const OrderImportReviewScreen({
    super.key,
    required this.controller,
    required this.result,
    this.imagePath,
  });

  final InventoryController controller;
  final OrderRecognitionResult result;
  final String? imagePath;

  @override
  State<OrderImportReviewScreen> createState() =>
      _OrderImportReviewScreenState();
}

class _OrderImportReviewScreenState extends State<OrderImportReviewScreen> {
  late final Set<int> _selectedIndexes;
  bool _importing = false;

  @override
  void initState() {
    super.initState();
    _selectedIndexes = {
      for (var index = 0; index < widget.result.items.length; index += 1) index,
    };
  }

  @override
  Widget build(BuildContext context) {
    final selectedCount = _selectedIndexes.length;
    return Scaffold(
      appBar: AppBar(
        title: const Text('确认入库'),
        actions: [
          TextButton(
            onPressed: _importing ? null : _toggleAll,
            child: Text(
                selectedCount == widget.result.items.length ? '全不选' : '全选'),
          ),
        ],
      ),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(20, 12, 20, 24),
        children: [
          SectionCard(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  widget.result.merchant ?? widget.result.sourceApp ?? '订单截图',
                  style: Theme.of(context).textTheme.titleLarge?.copyWith(
                        color: AppColors.textPrimary,
                        fontWeight: FontWeight.w900,
                      ),
                ),
                const SizedBox(height: 10),
                Wrap(
                  spacing: 8,
                  runSpacing: 8,
                  children: [
                    if (widget.result.sourceApp != null)
                      StatusPill(
                        label: widget.result.sourceApp!,
                        color: AppColors.secondary,
                        backgroundColor:
                            AppColors.secondary.withValues(alpha: 0.12),
                        icon: Icons.apps_outlined,
                      ),
                    if (widget.result.orderId != null)
                      StatusPill(
                        label: '订单 ${widget.result.orderId!}',
                        color: AppColors.primary,
                        backgroundColor:
                            AppColors.primary.withValues(alpha: 0.12),
                        icon: Icons.receipt_long_outlined,
                      ),
                    if (widget.result.purchaseDate != null)
                      StatusPill(
                        label: _dateText(widget.result.purchaseDate!),
                        color: AppColors.success,
                        backgroundColor:
                            AppColors.success.withValues(alpha: 0.12),
                        icon: Icons.event_available_outlined,
                      ),
                  ],
                ),
              ],
            ),
          ),
          const SizedBox(height: 14),
          for (var index = 0;
              index < widget.result.items.length;
              index += 1) ...[
            _RecognizedItemTile(
              item: widget.result.items[index],
              selected: _selectedIndexes.contains(index),
              onChanged: _importing
                  ? null
                  : (selected) {
                      setState(() {
                        if (selected) {
                          _selectedIndexes.add(index);
                        } else {
                          _selectedIndexes.remove(index);
                        }
                      });
                    },
            ),
            const SizedBox(height: 10),
          ],
        ],
      ),
      bottomNavigationBar: SafeArea(
        child: Padding(
          padding: const EdgeInsets.fromLTRB(20, 10, 20, 16),
          child: FilledButton.icon(
            onPressed:
                _importing || selectedCount == 0 ? null : _importSelectedItems,
            icon: _importing
                ? const SizedBox(
                    width: 18,
                    height: 18,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : const Icon(Icons.playlist_add_check_outlined),
            label: Text(_importing ? '入库中' : '添加 $selectedCount 个物品'),
          ),
        ),
      ),
    );
  }

  void _toggleAll() {
    setState(() {
      if (_selectedIndexes.length == widget.result.items.length) {
        _selectedIndexes.clear();
      } else {
        _selectedIndexes
          ..clear()
          ..addAll(
            List.generate(widget.result.items.length, (index) => index),
          );
      }
    });
  }

  Future<void> _importSelectedItems() async {
    setState(() => _importing = true);
    try {
      final selectedItems = widget.result.items
          .asMap()
          .entries
          .where((entry) => _selectedIndexes.contains(entry.key))
          .map((entry) => entry.value)
          .toList();
      final count = await widget.controller.createItemsFromOrder(
        result: widget.result,
        items: selectedItems,
        imagePath: widget.imagePath,
      );
      if (!mounted) {
        return;
      }
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('已添加 $count 个物品')),
      );
      Navigator.of(context).pop(true);
    } catch (error) {
      if (!mounted) {
        return;
      }
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('入库失败：$error')),
      );
    } finally {
      if (mounted) {
        setState(() => _importing = false);
      }
    }
  }
}

class _RecognizedItemTile extends StatelessWidget {
  const _RecognizedItemTile({
    required this.item,
    required this.selected,
    required this.onChanged,
  });

  final OrderRecognitionItem item;
  final bool selected;
  final ValueChanged<bool>? onChanged;

  @override
  Widget build(BuildContext context) {
    return SectionCard(
      padding: EdgeInsets.zero,
      child: CheckboxListTile(
        value: selected,
        onChanged:
            onChanged == null ? null : (value) => onChanged!(value ?? false),
        controlAffinity: ListTileControlAffinity.leading,
        title: Text(
          item.name,
          style: Theme.of(context).textTheme.titleMedium?.copyWith(
                color: AppColors.textPrimary,
                fontWeight: FontWeight.w900,
              ),
        ),
        subtitle: Padding(
          padding: const EdgeInsets.only(top: 8),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: [
                  StatusPill(
                    label: '${item.quantity}${item.unit ?? ''}',
                    color: AppColors.textPrimary,
                    backgroundColor: AppColors.surfaceVariant,
                    icon: Icons.inventory_2_outlined,
                  ),
                  if (item.categoryName != null)
                    StatusPill(
                      label: item.categoryName!,
                      color: AppColors.secondary,
                      backgroundColor:
                          AppColors.secondary.withValues(alpha: 0.12),
                      icon: Icons.category_outlined,
                    ),
                  if (item.expiryDate != null)
                    StatusPill(
                      label: '到期 ${_dateText(item.expiryDate!)}',
                      color: AppColors.warning,
                      backgroundColor:
                          AppColors.warning.withValues(alpha: 0.12),
                      icon: Icons.event_busy_outlined,
                    ),
                  if (item.expiryDate == null &&
                      item.predictedExpiryDate != null)
                    StatusPill(
                      label: '预测 ${_dateText(item.predictedExpiryDate!)}',
                      color: AppColors.warning,
                      backgroundColor:
                          AppColors.warning.withValues(alpha: 0.12),
                      icon: Icons.auto_awesome_outlined,
                    ),
                  if (item.confidence != null)
                    StatusPill(
                      label: '${(item.confidence! * 100).round()}%',
                      color: AppColors.success,
                      backgroundColor:
                          AppColors.success.withValues(alpha: 0.12),
                      icon: Icons.verified_outlined,
                    ),
                ],
              ),
              if (item.notes != null) ...[
                const SizedBox(height: 8),
                Text(
                  item.notes!,
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: AppColors.textSecondary,
                      ),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}

String _dateText(DateTime date) {
  return '${date.year.toString().padLeft(4, '0')}-'
      '${date.month.toString().padLeft(2, '0')}-'
      '${date.day.toString().padLeft(2, '0')}';
}
