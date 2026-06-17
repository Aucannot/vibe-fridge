import 'package:file_selector/file_selector.dart' as file_selector;
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:image_picker/image_picker.dart';

import '../data/inventory_controller.dart';
import '../data/local_image_store.dart';
import '../models/inventory_item.dart';
import '../models/item_status.dart';
import '../theme/app_theme.dart';
import '../utils/date_formatters.dart';
import '../widgets/app_cards.dart';
import '../widgets/image_attachment_card.dart';
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
  final _imagePicker = ImagePicker();
  bool _working = false;
  bool _pickingAttachment = false;

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
            padding: AppSpacing.detailListPadding,
            children: [
              ContentWidth(child: _Header(item: item)),
              const SizedBox(height: AppSpacing.fieldGap),
              ContentWidth(
                child: _QuantityReminderGrid(
                  item: item,
                  working: _working,
                  onDecrease: () => _changeQuantity(-1),
                  onIncrease: () => _changeQuantity(1),
                ),
              ),
              const SizedBox(height: AppSpacing.fieldGap),
              ContentWidth(child: _FreshnessTimeline(item: item)),
              const SizedBox(height: AppSpacing.fieldGap),
              ContentWidth(child: _StorageAdvice(item: item)),
              const SizedBox(height: AppSpacing.fieldGap),
              ContentWidth(child: _Facts(item: item)),
              if (item.tags.isNotEmpty) ...[
                const SizedBox(height: AppSpacing.fieldGap),
                ContentWidth(child: _Tags(item: item)),
              ],
              const SizedBox(height: AppSpacing.fieldGap),
              ContentWidth(
                child: ImageAttachmentCard(
                  imagePath: item.imagePath,
                  isBusy: _pickingAttachment,
                  onPick: () => _pickInventoryAttachment(item),
                  onClear: () => _clearImageAttachment(item),
                ),
              ),
              if (_hasImportTrace(item)) ...[
                const SizedBox(height: AppSpacing.fieldGap),
                ContentWidth(child: _ImportTrace(item: item)),
              ],
              const SizedBox(height: AppSpacing.sectionGap),
              if (item.status == ItemStatus.active) ...[
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
    final confirmed = await showAppConfirmDialog(
      context,
      title: '标记已消耗',
      message: '确定将这条库存记录标记为已消耗吗？',
      confirmLabel: '标记已消耗',
    );
    if (!confirmed) {
      return;
    }
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
      setState(() {
        _future = _load();
      });
    }
  }

  Future<void> _deleteItem(InventoryItem item) async {
    final confirmed = await showAppConfirmDialog(
      context,
      title: '删除库存记录',
      message: '确定删除“${item.name}”这条库存记录吗？',
      confirmLabel: '删除',
      isDestructive: true,
    );
    if (!confirmed) {
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

  Future<void> _pickInventoryAttachment(InventoryItem item) async {
    final source = await _showImageSourceSheet(
      hasImage: item.imagePath != null && item.imagePath!.isNotEmpty,
    );
    if (source == null || !mounted) {
      return;
    }
    setState(() => _pickingAttachment = true);
    try {
      final image = await _pickImage(source);
      if (image == null) {
        return;
      }
      final path = await LocalImageStore.saveImage(
        bytes: image.bytes,
        folderName: 'inventory',
        originalName: image.name,
        mimeType: image.mimeType,
      );
      await _updateItemImage(item, path);
      if (!mounted) {
        return;
      }
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('物品照片已保存')),
      );
    } catch (error, stackTrace) {
      if (!mounted) {
        return;
      }
      showAppErrorSnackBar(
        context,
        message: '物品照片保存失败',
        error: error,
        stackTrace: stackTrace,
      );
    } finally {
      if (mounted) {
        setState(() => _pickingAttachment = false);
      }
    }
  }

  Future<void> _clearImageAttachment(InventoryItem item) async {
    setState(() => _pickingAttachment = true);
    try {
      await _updateItemImage(item, null);
      if (!mounted) {
        return;
      }
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('已移除物品照片')),
      );
    } finally {
      if (mounted) {
        setState(() => _pickingAttachment = false);
      }
    }
  }

  Future<void> _updateItemImage(
    InventoryItem item,
    String? imagePath,
  ) async {
    await widget.controller.updateItem(
      itemId: item.id,
      quantity: item.quantity,
      unit: item.unit,
      description: item.description,
      purchaseDate: item.purchaseDate,
      expiryDate: item.expiryDate,
      imagePath: imagePath,
      storageLocation: item.storageLocation,
      tags: item.tags,
      isReminderEnabled: item.isReminderEnabled,
      reminderDaysBefore: item.reminderDaysBefore,
    );
    if (mounted) {
      setState(() {
        _future = _load();
      });
    }
  }

  Future<_ImageSourceChoice?> _showImageSourceSheet({
    required bool hasImage,
  }) {
    return showModalBottomSheet<_ImageSourceChoice>(
      context: context,
      showDragHandle: true,
      builder: (context) {
        return SafeArea(
          child: Padding(
            padding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                ListTile(
                  title: Text(
                    hasImage ? '更换物品照片' : '添加物品照片',
                    style: Theme.of(context).textTheme.titleMedium?.copyWith(
                          fontWeight: FontWeight.w900,
                        ),
                  ),
                ),
                ListTile(
                  leading: const Icon(Icons.photo_camera_outlined),
                  title: const Text('拍照记录'),
                  onTap: () =>
                      Navigator.of(context).pop(_ImageSourceChoice.camera),
                ),
                ListTile(
                  leading: const Icon(Icons.photo_library_outlined),
                  title: const Text('从相册选择'),
                  onTap: () =>
                      Navigator.of(context).pop(_ImageSourceChoice.gallery),
                ),
                ListTile(
                  leading: const Icon(Icons.folder_open_outlined),
                  title: const Text('从文件选择'),
                  onTap: () =>
                      Navigator.of(context).pop(_ImageSourceChoice.file),
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  Future<_PickedImage?> _pickImage(_ImageSourceChoice source) async {
    switch (source) {
      case _ImageSourceChoice.camera:
        try {
          final file = await _imagePicker.pickImage(
            source: ImageSource.camera,
            requestFullMetadata: false,
          );
          if (file == null) {
            return null;
          }
          return _PickedImage.fromImagePicker(file);
        } on UnsupportedError {
          _showCameraUnavailable();
          return null;
        } on PlatformException catch (error) {
          if (_isDesktopPlatform) {
            _showCameraUnavailable();
            return null;
          }
          throw Exception(error.message ?? error.code);
        }
      case _ImageSourceChoice.gallery:
        final file = await _imagePicker.pickImage(
          source: ImageSource.gallery,
          requestFullMetadata: false,
        );
        if (file == null) {
          return null;
        }
        return _PickedImage.fromImagePicker(file);
      case _ImageSourceChoice.file:
        final file = await file_selector.openFile(
          acceptedTypeGroups: const [
            file_selector.XTypeGroup(
              label: '物品照片',
              extensions: ['png', 'jpg', 'jpeg', 'webp', 'heic', 'heif'],
            ),
          ],
        );
        if (file == null) {
          return null;
        }
        return _PickedImage.fromFileSelector(file);
    }
  }

  void _showCameraUnavailable() {
    if (!mounted) {
      return;
    }
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('当前平台暂不支持直接拍照，请改用相册或文件'),
      ),
    );
  }
}

bool _hasImportTrace(InventoryItem item) {
  return item.sourceApp != null ||
      item.sourceOrderId != null ||
      item.importBatchId != null ||
      item.recognitionConfidence != null;
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

class _QuantityReminderGrid extends StatelessWidget {
  const _QuantityReminderGrid({
    required this.item,
    required this.working,
    required this.onDecrease,
    required this.onIncrease,
  });

  final InventoryItem item;
  final bool working;
  final VoidCallback onDecrease;
  final VoidCallback onIncrease;

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final wide = constraints.maxWidth >= AppBreakpoints.wideGrid;
        final cards = [
          _QuantityCard(
            item: item,
            working: working,
            onDecrease: onDecrease,
            onIncrease: onIncrease,
          ),
          _ReminderCard(item: item),
        ];
        if (wide) {
          return Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(child: cards[0]),
              const SizedBox(width: AppSpacing.cardGap),
              Expanded(child: cards[1]),
            ],
          );
        }
        return Column(
          children: [
            cards[0],
            const SizedBox(height: AppSpacing.cardGap),
            cards[1],
          ],
        );
      },
    );
  }
}

class _QuantityCard extends StatelessWidget {
  const _QuantityCard({
    required this.item,
    required this.working,
    required this.onDecrease,
    required this.onIncrease,
  });

  final InventoryItem item;
  final bool working;
  final VoidCallback onDecrease;
  final VoidCallback onIncrease;

  @override
  Widget build(BuildContext context) {
    final canAdjust = item.status == ItemStatus.active && !working;
    return SectionCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            '数量操作',
            style: Theme.of(context).textTheme.titleMedium?.copyWith(
                  color: AppColors.textPrimary,
                  fontWeight: FontWeight.w900,
                ),
          ),
          const SizedBox(height: 16),
          Row(
            children: [
              OutlinedButton(
                onPressed: canAdjust ? onDecrease : null,
                child: const Icon(Icons.remove),
              ),
              Expanded(
                child: Center(
                  child: Text(
                    '${item.quantity} ${item.unit ?? ''}'.trim(),
                    style: Theme.of(context).textTheme.displaySmall?.copyWith(
                          color: AppColors.textPrimary,
                          fontWeight: FontWeight.w900,
                        ),
                  ),
                ),
              ),
              FilledButton(
                onPressed: canAdjust ? onIncrease : null,
                child: const Icon(Icons.add),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _ReminderCard extends StatelessWidget {
  const _ReminderCard({required this.item});

  final InventoryItem item;

  @override
  Widget build(BuildContext context) {
    return SectionCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            '提醒',
            style: Theme.of(context).textTheme.titleMedium?.copyWith(
                  color: AppColors.textPrimary,
                  fontWeight: FontWeight.w900,
                ),
          ),
          const SizedBox(height: 12),
          InfoRow(
            label: '提醒日期',
            value: formatDate(item.reminderDate),
            icon: Icons.notifications_active_outlined,
          ),
          InfoRow(
            label: '提前天数',
            value: '${item.reminderDaysBefore} 天',
            icon: Icons.hourglass_bottom_outlined,
          ),
          const SizedBox(height: 8),
          StatusPill(
            label: item.isReminderEnabled ? '已启用' : '已关闭',
            color: item.isReminderEnabled
                ? AppColors.primaryDark
                : AppColors.textHint,
            backgroundColor: item.isReminderEnabled
                ? AppColors.primaryContainer
                : AppColors.surfaceVariant,
          ),
        ],
      ),
    );
  }
}

class _FreshnessTimeline extends StatelessWidget {
  const _FreshnessTimeline({required this.item});

  final InventoryItem item;

  @override
  Widget build(BuildContext context) {
    final purchase = item.purchaseDate;
    final expiry = item.expiryDate;
    final now = DateTime.now();
    final value =
        purchase == null || expiry == null || !expiry.isAfter(purchase)
            ? 0.5
            : now.difference(purchase).inDays /
                expiry.difference(purchase).inDays.clamp(1, 9999);
    return SectionCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            '新鲜度时间线',
            style: Theme.of(context).textTheme.titleMedium?.copyWith(
                  color: AppColors.textPrimary,
                  fontWeight: FontWeight.w900,
                ),
          ),
          const SizedBox(height: 14),
          MiniProgressBar(
            value: value.clamp(0.0, 1.0),
            color: item.isExpired ? AppColors.error : AppColors.primaryDark,
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              Expanded(
                child: _TimelinePoint(
                  label: '购买',
                  value: formatDate(item.purchaseDate),
                ),
              ),
              Expanded(
                child: _TimelinePoint(
                  label: '建议食用',
                  value: item.reminderDate == null
                      ? '按需处理'
                      : formatDate(item.reminderDate),
                  alignEnd: false,
                ),
              ),
              Expanded(
                child: _TimelinePoint(
                  label: '到期',
                  value: formatDate(item.expiryDate),
                  alignEnd: true,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _TimelinePoint extends StatelessWidget {
  const _TimelinePoint({
    required this.label,
    required this.value,
    this.alignEnd = false,
  });

  final String label;
  final String value;
  final bool alignEnd;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment:
          alignEnd ? CrossAxisAlignment.end : CrossAxisAlignment.start,
      children: [
        Text(
          label,
          style: Theme.of(context).textTheme.labelMedium?.copyWith(
                color: AppColors.textHint,
                fontWeight: FontWeight.w700,
              ),
        ),
        const SizedBox(height: 3),
        Text(
          value,
          style: Theme.of(context).textTheme.bodySmall?.copyWith(
                color: AppColors.textPrimary,
                fontWeight: FontWeight.w800,
              ),
        ),
      ],
    );
  }
}

class _StorageAdvice extends StatelessWidget {
  const _StorageAdvice({required this.item});

  final InventoryItem item;

  @override
  Widget build(BuildContext context) {
    final location = item.storageLocation ?? '未设置';
    final advice = switch (location) {
      '冷藏' => '保持密封，放在视线高度，优先处理临期批次。',
      '冷冻' => '标记分装日期，解冻后尽快食用。',
      '常温' => '避光干燥存放，打开后记得调整提醒。',
      '药箱' => '远离潮湿和儿童可触达区域。',
      '浴室' => '注意防潮，定期检查包装状态。',
      _ => '建议补充存放位置，方便提醒和批量整理。',
    };
    return SectionCard(
      color: AppColors.surfaceWarm,
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 44,
            height: 44,
            decoration: BoxDecoration(
              color: AppColors.secondaryContainer,
              borderRadius: BorderRadius.circular(AppRadii.large),
            ),
            child: const Icon(
              Icons.tips_and_updates_outlined,
              color: AppColors.secondary,
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  '存储建议 · $location',
                  style: Theme.of(context).textTheme.titleSmall?.copyWith(
                        color: AppColors.textPrimary,
                        fontWeight: FontWeight.w900,
                      ),
                ),
                const SizedBox(height: 5),
                Text(
                  advice,
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

class _Facts extends StatelessWidget {
  const _Facts({required this.item});

  final InventoryItem item;

  @override
  Widget build(BuildContext context) {
    return SectionCard(
      child: Column(
        children: [
          _FactRow(label: '数量', value: '${item.quantity}${item.unit ?? ''}'),
          _FactRow(label: '分类', value: item.categoryName ?? '未分类'),
          _FactRow(label: '购买日期', value: formatDate(item.purchaseDate)),
          _FactRow(label: '过期日期', value: formatDate(item.expiryDate)),
          _FactRow(label: '提醒日期', value: formatDate(item.reminderDate)),
          _FactRow(
            label: '提醒开关',
            value: item.isReminderEnabled ? '开启' : '关闭',
          ),
          if (item.isReminderEnabled)
            _FactRow(label: '提前天数', value: '${item.reminderDaysBefore} 天'),
          if (item.storageLocation != null)
            _FactRow(label: '存放位置', value: item.storageLocation!),
          if (item.description != null && item.description!.isNotEmpty)
            _FactRow(label: '描述', value: item.description!),
        ],
      ),
    );
  }
}

class _Tags extends StatelessWidget {
  const _Tags({required this.item});

  final InventoryItem item;

  @override
  Widget build(BuildContext context) {
    return SectionCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            '标签',
            style: Theme.of(context).textTheme.titleMedium?.copyWith(
                  color: AppColors.textPrimary,
                  fontWeight: FontWeight.w900,
                ),
          ),
          const SizedBox(height: 10),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              for (final tag in item.tags)
                StatusPill(
                  label: tag,
                  color: AppColors.secondary,
                  backgroundColor: AppColors.secondaryContainer,
                ),
            ],
          ),
        ],
      ),
    );
  }
}

enum _ImageSourceChoice { camera, gallery, file }

class _PickedImage {
  const _PickedImage({
    required this.bytes,
    required this.name,
    required this.mimeType,
  });

  final Uint8List bytes;
  final String name;
  final String mimeType;

  static Future<_PickedImage> fromImagePicker(XFile file) async {
    return _PickedImage(
      bytes: await file.readAsBytes(),
      name: file.name.isEmpty ? 'image' : file.name,
      mimeType: _mimeTypeForImage(
        mimeType: file.mimeType,
        name: file.name,
        path: file.path,
      ),
    );
  }

  static Future<_PickedImage> fromFileSelector(file_selector.XFile file) async {
    return _PickedImage(
      bytes: await file.readAsBytes(),
      name: file.name.isEmpty ? 'image' : file.name,
      mimeType: _mimeTypeForImage(
        mimeType: file.mimeType,
        name: file.name,
        path: file.path,
      ),
    );
  }
}

bool get _isDesktopPlatform {
  return defaultTargetPlatform == TargetPlatform.linux ||
      defaultTargetPlatform == TargetPlatform.macOS ||
      defaultTargetPlatform == TargetPlatform.windows;
}

String _mimeTypeForImage({
  String? mimeType,
  String? name,
  String? path,
}) {
  if (mimeType != null && mimeType.isNotEmpty) {
    return mimeType;
  }
  final candidate =
      (name != null && name.isNotEmpty ? name : path ?? '').toLowerCase();
  if (candidate.endsWith('.png')) {
    return 'image/png';
  }
  if (candidate.endsWith('.webp')) {
    return 'image/webp';
  }
  if (candidate.endsWith('.heic')) {
    return 'image/heic';
  }
  if (candidate.endsWith('.heif')) {
    return 'image/heif';
  }
  return 'image/jpeg';
}

class _ImportTrace extends StatelessWidget {
  const _ImportTrace({required this.item});

  final InventoryItem item;

  @override
  Widget build(BuildContext context) {
    return SectionCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            '导入来源',
            style: Theme.of(context).textTheme.titleMedium?.copyWith(
                  color: AppColors.textPrimary,
                  fontWeight: FontWeight.w900,
                ),
          ),
          const SizedBox(height: 10),
          if (item.sourceApp != null)
            _TraceRow(label: '来源', value: item.sourceApp!),
          if (item.sourceOrderId != null)
            _TraceRow(label: '订单号', value: item.sourceOrderId!),
          if (item.importBatchId != null)
            _TraceRow(label: '导入批次', value: item.importBatchId!),
          if (item.recognitionConfidence != null)
            _TraceRow(
              label: '识别置信度',
              value: '${(item.recognitionConfidence! * 100).round()}%',
            ),
        ],
      ),
    );
  }
}

class _TraceRow extends StatelessWidget {
  const _TraceRow({required this.label, required this.value});

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
            child: SelectableText(
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
