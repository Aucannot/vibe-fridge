import 'dart:async';

import 'package:flutter/material.dart';

import '../data/inventory_controller.dart';
import '../models/order_recognition.dart';
import '../theme/app_theme.dart';
import '../widgets/app_cards.dart';

const double _lowConfidenceThreshold = 0.7;

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
  late final List<_EditableOrderItem> _drafts;
  late final Set<int> _selectedIndexes;
  final Map<int, OrderImportDuplicate> _duplicatesByIndex = {};
  Timer? _duplicateDebounce;
  bool _checkingDuplicates = false;
  bool _importing = false;
  OrderImportSummary? _lastSummary;

  @override
  void initState() {
    super.initState();
    _drafts = widget.result.items.map(_EditableOrderItem.fromItem).toList();
    _selectedIndexes = {
      for (var index = 0; index < _drafts.length; index += 1) index,
    };
    WidgetsBinding.instance.addPostFrameCallback((_) => _refreshDuplicates());
  }

  @override
  void dispose() {
    _duplicateDebounce?.cancel();
    for (final draft in _drafts) {
      draft.dispose();
    }
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final selectedCount = _selectedIndexes.length;
    final readyCount = _readySelectedCount;
    final duplicateCount = _selectedIndexes
        .where((index) => _duplicatesByIndex.containsKey(index))
        .length;
    final reviewCount = _selectedIndexes
        .where((index) => _drafts[index].needsManualReview)
        .length;

    return Scaffold(
      appBar: AppBar(
        title: const Text('确认入库'),
        actions: [
          TextButton(
            onPressed: _importing ? null : _toggleAll,
            child: Text(selectedCount == _drafts.length ? '全不选' : '全选'),
          ),
        ],
      ),
      body: ListView(
        padding: AppSpacing.reviewListPadding,
        children: [
          _ReceiptPreviewCard(
            result: widget.result,
            imagePath: widget.imagePath,
          ),
          const SizedBox(height: AppSpacing.fieldGap),
          _OrderImportOverview(
            result: widget.result,
            totalCount: _drafts.length,
            selectedCount: selectedCount,
            readyCount: readyCount,
            duplicateCount: duplicateCount,
            reviewCount: reviewCount,
          ),
          if (_checkingDuplicates) ...[
            const SizedBox(height: AppSpacing.compactPadding),
            const LinearProgressIndicator(minHeight: 3),
          ],
          if (_lastSummary != null) ...[
            const SizedBox(height: AppSpacing.fieldGap),
            _ImportSummaryCard(summary: _lastSummary!),
          ],
          const SizedBox(height: AppSpacing.fieldGap),
          for (var index = 0; index < _drafts.length; index += 1) ...[
            _EditableRecognizedItemTile(
              index: index,
              draft: _drafts[index],
              selected: _selectedIndexes.contains(index),
              duplicate: _duplicatesByIndex[index],
              categoryNames:
                  widget.controller.categories.map((row) => row.name).toList(),
              onSelectedChanged: _importing
                  ? null
                  : (selected) => _setSelected(index, selected),
              onChanged: () => _onDraftChanged(index),
              onConfirm: () => _confirmDraft(index),
              onPickPurchaseDate: () => _pickDate(
                initialDate: _drafts[index].purchaseDate,
                onPicked: (date) {
                  _drafts[index].purchaseDate = date;
                  _onDraftChanged(index);
                },
              ),
              onClearPurchaseDate: () {
                _drafts[index].purchaseDate = null;
                _onDraftChanged(index);
              },
              onPickPredictedExpiryDate: () => _pickDate(
                initialDate: _drafts[index].predictedExpiryDate,
                onPicked: (date) {
                  _drafts[index].predictedExpiryDate = date;
                  _onDraftChanged(index, affectsDuplicate: false);
                },
              ),
              onClearPredictedExpiryDate: () {
                _drafts[index].predictedExpiryDate = null;
                _onDraftChanged(index, affectsDuplicate: false);
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
            label: Text(_importing ? '入库中' : '添加 $readyCount 个物品'),
          ),
        ),
      ),
    );
  }

  int get _readySelectedCount {
    var count = 0;
    for (final index in _selectedIndexes) {
      if (_duplicatesByIndex.containsKey(index)) {
        continue;
      }
      if (_drafts[index].blocksImport) {
        continue;
      }
      count += 1;
    }
    return count;
  }

  void _toggleAll() {
    setState(() {
      _lastSummary = null;
      if (_selectedIndexes.length == _drafts.length) {
        _selectedIndexes.clear();
      } else {
        _selectedIndexes
          ..clear()
          ..addAll(List.generate(_drafts.length, (index) => index));
      }
    });
  }

  void _setSelected(int index, bool selected) {
    setState(() {
      _lastSummary = null;
      if (selected) {
        _selectedIndexes.add(index);
      } else {
        _selectedIndexes.remove(index);
      }
    });
  }

  void _confirmDraft(int index) {
    setState(() {
      _lastSummary = null;
      _drafts[index].confirmed = true;
    });
  }

  void _onDraftChanged(int index, {bool affectsDuplicate = true}) {
    setState(() => _lastSummary = null);
    if (affectsDuplicate) {
      _scheduleDuplicateRefresh();
    }
  }

  void _scheduleDuplicateRefresh() {
    _duplicateDebounce?.cancel();
    _duplicateDebounce = Timer(
      const Duration(milliseconds: 300),
      _refreshDuplicates,
    );
  }

  Future<void> _refreshDuplicates() async {
    if (!mounted) {
      return;
    }
    setState(() => _checkingDuplicates = true);
    try {
      final duplicates = await widget.controller.findOrderImportDuplicates(
        result: widget.result,
        items: _drafts.map((draft) => draft.toRecognitionItem()).toList(),
      );
      if (!mounted) {
        return;
      }
      setState(() {
        _duplicatesByIndex
          ..clear()
          ..addEntries(
            duplicates.map((duplicate) {
              return MapEntry(duplicate.index, duplicate);
            }),
          );
      });
    } finally {
      if (mounted) {
        setState(() => _checkingDuplicates = false);
      }
    }
  }

  Future<void> _pickDate({
    required DateTime? initialDate,
    required ValueChanged<DateTime> onPicked,
  }) async {
    final now = DateTime.now();
    final picked = await showDatePicker(
      context: context,
      initialDate: initialDate ?? now,
      firstDate: DateTime(2020),
      lastDate: DateTime(2100),
    );
    if (picked != null) {
      onPicked(picked);
    }
  }

  Future<void> _importSelectedItems() async {
    setState(() => _importing = true);
    try {
      await _refreshDuplicates();
      if (!mounted) {
        return;
      }

      final sortedIndexes = _selectedIndexes.toList()..sort();
      final items = <OrderRecognitionItem>[];
      var duplicateSkipped = 0;
      var needsManualReview = 0;
      for (final index in sortedIndexes) {
        final draft = _drafts[index];
        if (_duplicatesByIndex.containsKey(index)) {
          duplicateSkipped += 1;
          continue;
        }
        if (draft.blocksImport) {
          needsManualReview += 1;
          continue;
        }
        items.add(draft.toRecognitionItem());
      }

      if (items.isNotEmpty) {
        final confirmed = await showAppConfirmDialog(
          context,
          title: '确认批量入库',
          message: '将新增 ${items.length} 条库存记录。'
              '重复跳过 $duplicateSkipped 条，'
              '仍需确认 $needsManualReview 条。',
          confirmLabel: '确认入库',
        );
        if (!confirmed) {
          return;
        }
      }

      final summary = items.isEmpty
          ? OrderImportSummary(
              addedCount: 0,
              uncheckedCount: _drafts.length - sortedIndexes.length,
              duplicateCount: duplicateSkipped,
              needsManualReviewCount: needsManualReview,
            )
          : await widget.controller.createItemsFromOrder(
              result: widget.result,
              items: items,
              imagePath: widget.imagePath,
              uncheckedCount: _drafts.length - sortedIndexes.length,
              duplicateSkippedBeforeImport: duplicateSkipped,
              needsManualReviewCount: needsManualReview,
            );

      if (!mounted) {
        return;
      }
      setState(() => _lastSummary = summary);
      await _showImportSummary(summary);
      if (mounted && summary.addedCount > 0) {
        Navigator.of(context).pop(true);
      }
    } catch (error, stackTrace) {
      if (!mounted) {
        return;
      }
      showAppErrorSnackBar(
        context,
        message: '入库失败',
        error: error,
        stackTrace: stackTrace,
      );
    } finally {
      if (mounted) {
        setState(() => _importing = false);
      }
    }
  }

  Future<void> _showImportSummary(OrderImportSummary summary) {
    return showDialog<void>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(summary.addedCount > 0 ? '导入完成' : '没有新增物品'),
        content: _ImportSummaryLines(summary: summary),
        actions: [
          FilledButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text('知道了'),
          ),
        ],
      ),
    );
  }
}

class _ReceiptPreviewCard extends StatelessWidget {
  const _ReceiptPreviewCard({
    required this.result,
    required this.imagePath,
  });

  final OrderRecognitionResult result;
  final String? imagePath;

  @override
  Widget build(BuildContext context) {
    final rawText = result.rawText?.trim();
    return SectionCard(
      color: AppColors.surfaceWarm,
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 72,
            height: 96,
            decoration: BoxDecoration(
              color: AppColors.warningContainer.withValues(alpha: 0.62),
              borderRadius: BorderRadius.circular(AppRadii.card),
              border: Border.all(color: AppColors.divider),
            ),
            child: Icon(
              imagePath == null
                  ? Icons.receipt_long_outlined
                  : Icons.image_outlined,
              color: AppColors.warning,
              size: 30,
            ),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  '识别来源预览',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        color: AppColors.textPrimary,
                        fontWeight: FontWeight.w900,
                      ),
                ),
                const SizedBox(height: 6),
                Text(
                  result.merchant ??
                      result.sourceApp ??
                      (imagePath == null ? '手动粘贴文本' : '订单截图'),
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                        color: AppColors.textSecondary,
                        fontWeight: FontWeight.w700,
                      ),
                ),
                if (result.orderId != null) ...[
                  const SizedBox(height: 4),
                  Text(
                    '订单 ${result.orderId}',
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          color: AppColors.textHint,
                        ),
                  ),
                ],
                if (rawText != null && rawText.isNotEmpty) ...[
                  const SizedBox(height: 8),
                  Text(
                    rawText,
                    maxLines: 3,
                    overflow: TextOverflow.ellipsis,
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          color: AppColors.textSecondary,
                        ),
                  ),
                ],
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _OrderImportOverview extends StatelessWidget {
  const _OrderImportOverview({
    required this.result,
    required this.totalCount,
    required this.selectedCount,
    required this.readyCount,
    required this.duplicateCount,
    required this.reviewCount,
  });

  final OrderRecognitionResult result;
  final int totalCount;
  final int selectedCount;
  final int readyCount;
  final int duplicateCount;
  final int reviewCount;

  @override
  Widget build(BuildContext context) {
    return SectionCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            result.merchant ?? result.sourceApp ?? '订单截图',
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
              StatusPill(
                label: '$selectedCount/$totalCount 已选',
                color: AppColors.primary,
                backgroundColor: AppColors.primaryContainer,
                icon: Icons.checklist_outlined,
              ),
              StatusPill(
                label: '$readyCount 可入库',
                color: AppColors.success,
                backgroundColor: AppColors.successContainer,
                icon: Icons.playlist_add_check_outlined,
              ),
              if (duplicateCount > 0)
                StatusPill(
                  label: '$duplicateCount 疑似重复',
                  color: AppColors.error,
                  backgroundColor: AppColors.errorContainer,
                  icon: Icons.content_copy_outlined,
                ),
              if (reviewCount > 0)
                StatusPill(
                  label: '$reviewCount 需要确认',
                  color: AppColors.warning,
                  backgroundColor: AppColors.warningContainer,
                  icon: Icons.priority_high_outlined,
                ),
              if (result.sourceApp != null)
                StatusPill(
                  label: result.sourceApp!,
                  color: AppColors.secondary,
                  backgroundColor: AppColors.secondaryContainer,
                  icon: Icons.apps_outlined,
                ),
              if (result.orderId != null)
                StatusPill(
                  label: '订单 ${result.orderId!}',
                  color: AppColors.textSecondary,
                  backgroundColor: AppColors.surfaceVariant,
                  icon: Icons.receipt_long_outlined,
                ),
              if (result.purchaseDate != null)
                StatusPill(
                  label: _dateText(result.purchaseDate!),
                  color: AppColors.textSecondary,
                  backgroundColor: AppColors.surfaceVariant,
                  icon: Icons.event_available_outlined,
                ),
            ],
          ),
        ],
      ),
    );
  }
}

class _EditableRecognizedItemTile extends StatelessWidget {
  const _EditableRecognizedItemTile({
    required this.index,
    required this.draft,
    required this.selected,
    required this.duplicate,
    required this.categoryNames,
    required this.onSelectedChanged,
    required this.onChanged,
    required this.onConfirm,
    required this.onPickPurchaseDate,
    required this.onClearPurchaseDate,
    required this.onPickPredictedExpiryDate,
    required this.onClearPredictedExpiryDate,
  });

  final int index;
  final _EditableOrderItem draft;
  final bool selected;
  final OrderImportDuplicate? duplicate;
  final List<String> categoryNames;
  final ValueChanged<bool>? onSelectedChanged;
  final VoidCallback onChanged;
  final VoidCallback onConfirm;
  final VoidCallback onPickPurchaseDate;
  final VoidCallback onClearPurchaseDate;
  final VoidCallback onPickPredictedExpiryDate;
  final VoidCallback onClearPredictedExpiryDate;

  @override
  Widget build(BuildContext context) {
    final hasDuplicate = duplicate != null;
    final needsReview = draft.needsManualReview;
    final invalid = !draft.hasValidName || !draft.hasValidQuantity;
    final borderColor = hasDuplicate || invalid
        ? AppColors.error
        : needsReview
            ? AppColors.warning
            : AppColors.divider;
    final backgroundColor = hasDuplicate || invalid
        ? AppColors.errorContainer.withValues(alpha: 0.45)
        : needsReview
            ? AppColors.warningContainer.withValues(alpha: 0.55)
            : null;

    return SectionCard(
      color: backgroundColor,
      borderColor: borderColor,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Checkbox(
                value: selected,
                onChanged: onSelectedChanged == null
                    ? null
                    : (value) => onSelectedChanged!(value ?? false),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      draft.displayName,
                      style: Theme.of(context).textTheme.titleMedium?.copyWith(
                            color: AppColors.textPrimary,
                            fontWeight: FontWeight.w900,
                          ),
                    ),
                    const SizedBox(height: 8),
                    Wrap(
                      spacing: 8,
                      runSpacing: 8,
                      children: [
                        StatusPill(
                          label: '#${index + 1}',
                          color: AppColors.textSecondary,
                          backgroundColor: AppColors.surfaceVariant,
                        ),
                        StatusPill(
                          label: '${draft.quantityText}${draft.unitText}',
                          color: AppColors.textPrimary,
                          backgroundColor: AppColors.surfaceVariant,
                          icon: Icons.inventory_2_outlined,
                        ),
                        if (draft.categoryName != null)
                          StatusPill(
                            label: draft.categoryName!,
                            color: AppColors.secondary,
                            backgroundColor: AppColors.secondaryContainer,
                            icon: Icons.category_outlined,
                          ),
                        _ConfidencePill(confidence: draft.confidence),
                        if (needsReview)
                          const StatusPill(
                            label: '需要确认',
                            color: AppColors.warning,
                            backgroundColor: AppColors.warningContainer,
                            icon: Icons.priority_high_outlined,
                          ),
                        if (hasDuplicate)
                          StatusPill(
                            label: '疑似重复 ${duplicate!.existingCount}',
                            color: AppColors.error,
                            backgroundColor: AppColors.errorContainer,
                            icon: Icons.content_copy_outlined,
                          ),
                        if (invalid)
                          const StatusPill(
                            label: '信息不完整',
                            color: AppColors.error,
                            backgroundColor: AppColors.errorContainer,
                            icon: Icons.error_outline,
                          ),
                      ],
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: AppSpacing.fieldGap),
          TextField(
            controller: draft.nameController,
            textInputAction: TextInputAction.next,
            onChanged: (_) => onChanged(),
            decoration: InputDecoration(
              labelText: '名称',
              prefixIcon: const Icon(Icons.inventory_2_outlined),
              errorText: selected && !draft.hasValidName ? '请输入名称' : null,
            ),
          ),
          const SizedBox(height: 12),
          _ResponsiveFieldPair(
            first: TextField(
              controller: draft.quantityController,
              keyboardType: TextInputType.number,
              textInputAction: TextInputAction.next,
              onChanged: (_) => onChanged(),
              decoration: InputDecoration(
                labelText: '数量',
                prefixIcon: const Icon(Icons.numbers_outlined),
                errorText:
                    selected && !draft.hasValidQuantity ? '请输入大于 0 的整数' : null,
              ),
            ),
            second: TextField(
              controller: draft.unitController,
              textInputAction: TextInputAction.next,
              onChanged: (_) => onChanged(),
              decoration: const InputDecoration(
                labelText: '单位',
                prefixIcon: Icon(Icons.straighten_outlined),
              ),
            ),
          ),
          const SizedBox(height: 12),
          _CategoryField(
            value: draft.categoryName,
            categoryNames: categoryNames,
            onChanged: (value) {
              draft.categoryName = value?.isEmpty == true ? null : value;
              onChanged();
            },
          ),
          const SizedBox(height: 12),
          _ResponsiveFieldPair(
            first: _EditableDateField(
              label: '购买日期',
              value: draft.purchaseDate,
              onTap: onPickPurchaseDate,
              onClear: onClearPurchaseDate,
            ),
            second: _EditableDateField(
              label: '预测过期日',
              value: draft.predictedExpiryDate ?? draft.exactExpiryDate,
              onTap: onPickPredictedExpiryDate,
              onClear: onClearPredictedExpiryDate,
            ),
          ),
          const SizedBox(height: 12),
          _ConfidenceSlider(
            confidence: draft.confidence,
            onChanged: (value) {
              draft.confidence = value;
              draft.confirmed = value >= _lowConfidenceThreshold;
              onChanged();
            },
          ),
          if (draft.notes != null) ...[
            const SizedBox(height: 8),
            Text(
              draft.notes!,
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: AppColors.textSecondary,
                  ),
            ),
          ],
          if (needsReview) ...[
            const SizedBox(height: 12),
            SizedBox(
              width: double.infinity,
              child: OutlinedButton.icon(
                onPressed: onConfirm,
                icon: const Icon(Icons.check_circle_outline),
                label: const Text('标记已确认'),
              ),
            ),
          ],
        ],
      ),
    );
  }
}

class _CategoryField extends StatelessWidget {
  const _CategoryField({
    required this.value,
    required this.categoryNames,
    required this.onChanged,
  });

  final String? value;
  final List<String> categoryNames;
  final ValueChanged<String?> onChanged;

  @override
  Widget build(BuildContext context) {
    final options = <String>{'', ...categoryNames};
    final current = value == null || value!.isEmpty ? '' : value!;
    options.add(current);
    return InputDecorator(
      decoration: const InputDecoration(
        labelText: '分类',
        prefixIcon: Icon(Icons.category_outlined),
      ),
      child: DropdownButtonHideUnderline(
        child: DropdownButton<String>(
          value: current,
          isExpanded: true,
          items: options
              .map(
                (option) => DropdownMenuItem(
                  value: option,
                  child: Text(option.isEmpty ? '未分类' : option),
                ),
              )
              .toList(),
          onChanged: onChanged,
        ),
      ),
    );
  }
}

class _ResponsiveFieldPair extends StatelessWidget {
  const _ResponsiveFieldPair({
    required this.first,
    required this.second,
  });

  final Widget first;
  final Widget second;

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        if (constraints.maxWidth < 560) {
          return Column(
            children: [
              first,
              const SizedBox(height: 12),
              second,
            ],
          );
        }
        return Row(
          children: [
            Expanded(child: first),
            const SizedBox(width: 12),
            Expanded(child: second),
          ],
        );
      },
    );
  }
}

class _EditableDateField extends StatelessWidget {
  const _EditableDateField({
    required this.label,
    required this.value,
    required this.onTap,
    required this.onClear,
  });

  final String label;
  final DateTime? value;
  final VoidCallback onTap;
  final VoidCallback onClear;

  @override
  Widget build(BuildContext context) {
    return InputDecorator(
      decoration: InputDecoration(
        labelText: label,
        prefixIcon: const Icon(Icons.calendar_today_outlined),
      ),
      child: Row(
        children: [
          Expanded(
            child: InkWell(
              onTap: onTap,
              child: Padding(
                padding: const EdgeInsets.symmetric(vertical: 2),
                child: Text(
                  value == null ? '未设置' : _dateText(value!),
                  style: TextStyle(
                    color: value == null
                        ? AppColors.textHint
                        : AppColors.textPrimary,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),
            ),
          ),
          if (value != null)
            IconButton(
              tooltip: '清除',
              onPressed: onClear,
              icon: const Icon(Icons.close, size: 18),
            ),
        ],
      ),
    );
  }
}

class _ConfidenceSlider extends StatelessWidget {
  const _ConfidenceSlider({
    required this.confidence,
    required this.onChanged,
  });

  final double? confidence;
  final ValueChanged<double> onChanged;

  @override
  Widget build(BuildContext context) {
    final value = confidence ?? 0;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            const Icon(Icons.verified_outlined, color: AppColors.textHint),
            const SizedBox(width: 12),
            Expanded(
              child: Text(
                '置信度',
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                      color: AppColors.textSecondary,
                      fontWeight: FontWeight.w700,
                    ),
              ),
            ),
            Text(
              '${(value * 100).round()}%',
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: value < _lowConfidenceThreshold
                        ? AppColors.warning
                        : AppColors.success,
                    fontWeight: FontWeight.w900,
                  ),
            ),
          ],
        ),
        Slider(
          value: value,
          min: 0,
          max: 1,
          divisions: 100,
          label: '${(value * 100).round()}%',
          onChanged: onChanged,
        ),
      ],
    );
  }
}

class _ConfidencePill extends StatelessWidget {
  const _ConfidencePill({required this.confidence});

  final double? confidence;

  @override
  Widget build(BuildContext context) {
    final value = confidence;
    if (value == null) {
      return const StatusPill(
        label: '无置信度',
        color: AppColors.warning,
        backgroundColor: AppColors.warningContainer,
        icon: Icons.help_outline,
      );
    }
    final low = value < _lowConfidenceThreshold;
    return StatusPill(
      label: '${(value * 100).round()}%',
      color: low ? AppColors.warning : AppColors.success,
      backgroundColor:
          low ? AppColors.warningContainer : AppColors.successContainer,
      icon: low ? Icons.priority_high_outlined : Icons.verified_outlined,
    );
  }
}

class _ImportSummaryCard extends StatelessWidget {
  const _ImportSummaryCard({required this.summary});

  final OrderImportSummary summary;

  @override
  Widget build(BuildContext context) {
    return SectionCard(
      color: AppColors.primaryContainer,
      borderColor: AppColors.primary.withValues(alpha: 0.25),
      child: _ImportSummaryLines(summary: summary),
    );
  }
}

class _ImportSummaryLines extends StatelessWidget {
  const _ImportSummaryLines({required this.summary});

  final OrderImportSummary summary;

  @override
  Widget build(BuildContext context) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        _SummaryLine(
          icon: Icons.add_circle_outline,
          label: '新增',
          value: '${summary.addedCount}',
          color: AppColors.success,
        ),
        _SummaryLine(
          icon: Icons.skip_next_outlined,
          label: '跳过',
          value: '${summary.skippedCount}',
          color: AppColors.textSecondary,
        ),
        _SummaryLine(
          icon: Icons.priority_high_outlined,
          label: '需要手动处理',
          value: '${summary.needsManualReviewCount}',
          color: AppColors.warning,
        ),
      ],
    );
  }
}

class _SummaryLine extends StatelessWidget {
  const _SummaryLine({
    required this.icon,
    required this.label,
    required this.value,
    required this.color,
  });

  final IconData icon;
  final String label;
  final String value;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        children: [
          Icon(icon, color: color),
          const SizedBox(width: 10),
          Expanded(
            child: Text(
              label,
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: AppColors.textSecondary,
                    fontWeight: FontWeight.w700,
                  ),
            ),
          ),
          Text(
            value,
            style: Theme.of(context).textTheme.titleMedium?.copyWith(
                  color: color,
                  fontWeight: FontWeight.w900,
                ),
          ),
        ],
      ),
    );
  }
}

class _EditableOrderItem {
  _EditableOrderItem({
    required String name,
    required int quantity,
    required String? unit,
    required this.categoryName,
    required this.purchaseDate,
    required this.exactExpiryDate,
    required this.predictedExpiryDate,
    required this.notes,
    required this.confidence,
  })  : nameController = TextEditingController(text: name),
        quantityController = TextEditingController(text: '$quantity'),
        unitController = TextEditingController(text: unit ?? '');

  factory _EditableOrderItem.fromItem(OrderRecognitionItem item) {
    final draft = _EditableOrderItem(
      name: item.name,
      quantity: item.quantity,
      unit: item.unit,
      categoryName: item.categoryName,
      purchaseDate: item.purchaseDate,
      exactExpiryDate: item.expiryDate,
      predictedExpiryDate: item.predictedExpiryDate,
      notes: item.notes,
      confidence: item.confidence,
    );
    draft.confirmed = !draft.lowConfidence;
    return draft;
  }

  final TextEditingController nameController;
  final TextEditingController quantityController;
  final TextEditingController unitController;
  String? categoryName;
  DateTime? purchaseDate;
  DateTime? exactExpiryDate;
  DateTime? predictedExpiryDate;
  String? notes;
  double? confidence;
  bool confirmed = false;

  String get displayName {
    final name = nameController.text.trim();
    return name.isEmpty ? '未命名物品' : name;
  }

  bool get hasValidName => nameController.text.trim().isNotEmpty;

  bool get hasValidQuantity {
    final quantity = int.tryParse(quantityController.text.trim());
    return quantity != null && quantity > 0;
  }

  bool get lowConfidence {
    final value = confidence;
    return value == null || value < _lowConfidenceThreshold;
  }

  bool get needsManualReview => lowConfidence && !confirmed;

  bool get blocksImport =>
      needsManualReview || !hasValidName || !hasValidQuantity;

  String get quantityText {
    final quantity = int.tryParse(quantityController.text.trim());
    return '${quantity == null || quantity < 1 ? 1 : quantity}';
  }

  String get unitText {
    final unit = unitController.text.trim();
    return unit.isEmpty ? '' : unit;
  }

  OrderRecognitionItem toRecognitionItem() {
    final quantity = int.tryParse(quantityController.text.trim());
    final unit = unitController.text.trim();
    return OrderRecognitionItem(
      name: nameController.text.trim(),
      quantity: quantity == null || quantity < 1 ? 1 : quantity,
      unit: unit.isEmpty ? null : unit,
      categoryName: categoryName,
      purchaseDate: purchaseDate,
      expiryDate: exactExpiryDate,
      predictedExpiryDate: predictedExpiryDate,
      notes: notes,
      confidence: confidence?.clamp(0, 1).toDouble(),
    );
  }

  void dispose() {
    nameController.dispose();
    quantityController.dispose();
    unitController.dispose();
  }
}

String _dateText(DateTime date) {
  return '${date.year.toString().padLeft(4, '0')}-'
      '${date.month.toString().padLeft(2, '0')}-'
      '${date.day.toString().padLeft(2, '0')}';
}
