import 'package:file_selector/file_selector.dart' as file_selector;
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:image_picker/image_picker.dart';
import 'package:intl/intl.dart';

import '../data/inventory_controller.dart';
import '../data/local_image_store.dart';
import '../models/inventory_item.dart';
import '../theme/app_theme.dart';
import '../widgets/app_cards.dart';
import '../widgets/image_attachment_card.dart';
import '../widgets/tag_selector_card.dart';

class ItemEditScreen extends StatefulWidget {
  const ItemEditScreen({
    super.key,
    required this.controller,
    required this.item,
  });

  final InventoryController controller;
  final InventoryItem item;

  @override
  State<ItemEditScreen> createState() => _ItemEditScreenState();
}

class _ItemEditScreenState extends State<ItemEditScreen> {
  final _formKey = GlobalKey<FormState>();
  late final TextEditingController _quantityController;
  late final TextEditingController _unitController;
  late final TextEditingController _descriptionController;
  late final TextEditingController _reminderDaysController;
  final _imagePicker = ImagePicker();
  late DateTime? _purchaseDate;
  late DateTime? _expiryDate;
  late String? _storageLocation;
  late String? _imagePath;
  late Set<String> _selectedTags;
  late bool _isReminderEnabled;
  bool _saving = false;
  bool _pickingAttachment = false;

  @override
  void initState() {
    super.initState();
    final item = widget.item;
    _quantityController = TextEditingController(text: '${item.quantity}');
    _unitController = TextEditingController(text: item.unit ?? '');
    _descriptionController =
        TextEditingController(text: item.description ?? '');
    _reminderDaysController =
        TextEditingController(text: '${item.reminderDaysBefore}');
    _purchaseDate = item.purchaseDate;
    _expiryDate = item.expiryDate;
    _storageLocation = item.storageLocation;
    _imagePath = item.imagePath;
    _selectedTags = item.tags.toSet();
    _isReminderEnabled = item.isReminderEnabled;
  }

  @override
  void dispose() {
    _quantityController.dispose();
    _unitController.dispose();
    _descriptionController.dispose();
    _reminderDaysController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('编辑库存')),
      body: ListView(
        padding: AppSpacing.detailListPadding,
        children: [
          ContentWidth(
            child: Form(
              key: _formKey,
              child: Column(
                children: [
                  SectionCard(
                    child: Column(
                      children: [
                        TextFormField(
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
                        const SizedBox(height: AppSpacing.cardGap),
                        TextFormField(
                          controller: _unitController,
                          decoration: const InputDecoration(
                            labelText: '单位',
                            prefixIcon: Icon(Icons.straighten_outlined),
                          ),
                        ),
                        const SizedBox(height: AppSpacing.cardGap),
                        DropdownButtonFormField<String?>(
                          initialValue: _storageLocation,
                          decoration: const InputDecoration(
                            labelText: '存放位置',
                            prefixIcon: Icon(Icons.place_outlined),
                          ),
                          items: [
                            const DropdownMenuItem<String?>(
                              child: Text('未设置'),
                            ),
                            for (final location in _storageLocationOptions)
                              DropdownMenuItem<String?>(
                                value: location,
                                child: Text(location),
                              ),
                          ],
                          onChanged: (value) =>
                              setState(() => _storageLocation = value),
                        ),
                        const SizedBox(height: 12),
                        TextFormField(
                          controller: _descriptionController,
                          minLines: 2,
                          maxLines: 4,
                          decoration: const InputDecoration(
                            labelText: '描述',
                            alignLabelWithHint: true,
                            prefixIcon: Icon(Icons.notes_outlined),
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: AppSpacing.fieldGap),
                  ImageAttachmentCard(
                    imagePath: _imagePath,
                    isBusy: _pickingAttachment,
                    onPick: _pickInventoryAttachment,
                    onClear: () => setState(() => _imagePath = null),
                  ),
                  const SizedBox(height: AppSpacing.fieldGap),
                  TagSelectorCard(
                    selectedTags: _selectedTags,
                    onChanged: (tags) => setState(() => _selectedTags = tags),
                  ),
                  const SizedBox(height: AppSpacing.fieldGap),
                  SectionCard(
                    child: Column(
                      children: [
                        _DateField(
                          label: '购买日期',
                          value: _purchaseDate,
                          onTap: () => _pickDate(
                            initialDate: _purchaseDate ?? DateTime.now(),
                            onPicked: (date) =>
                                setState(() => _purchaseDate = date),
                          ),
                          onClear: () => setState(() => _purchaseDate = null),
                        ),
                        const SizedBox(height: AppSpacing.cardGap),
                        _DateField(
                          label: '过期日期',
                          value: _expiryDate,
                          onTap: () => _pickDate(
                            initialDate: _expiryDate ??
                                DateTime.now().add(const Duration(days: 7)),
                            onPicked: (date) =>
                                setState(() => _expiryDate = date),
                          ),
                          onClear: () => setState(() => _expiryDate = null),
                        ),
                        const SizedBox(height: 8),
                        SwitchListTile(
                          contentPadding: EdgeInsets.zero,
                          value: _isReminderEnabled,
                          title: const Text('启用过期提醒'),
                          subtitle: Text(
                            _expiryDate == null
                                ? '设置过期日期后可计算提醒日'
                                : '按设置的提前天数生成提醒日',
                          ),
                          onChanged: (value) {
                            setState(() => _isReminderEnabled = value);
                          },
                        ),
                        if (_isReminderEnabled) ...[
                          const SizedBox(height: 8),
                          TextFormField(
                            controller: _reminderDaysController,
                            keyboardType: TextInputType.number,
                            decoration: const InputDecoration(
                              labelText: '提前天数',
                              prefixIcon: Icon(Icons.alarm_outlined),
                              suffixText: '天',
                            ),
                            validator: (value) {
                              if (!_isReminderEnabled) {
                                return null;
                              }
                              final parsed = int.tryParse(value ?? '');
                              if (parsed == null || parsed < 0) {
                                return '请输入 0 或更大的整数';
                              }
                              return null;
                            },
                          ),
                        ],
                      ],
                    ),
                  ),
                  const SizedBox(height: AppSpacing.sectionGap),
                  SizedBox(
                    width: double.infinity,
                    child: FilledButton.icon(
                      onPressed: _saving ? null : _save,
                      icon: _saving
                          ? const SizedBox(
                              width: 18,
                              height: 18,
                              child: CircularProgressIndicator(strokeWidth: 2),
                            )
                          : const Icon(Icons.save_outlined),
                      label: Text(_saving ? '保存中' : '保存修改'),
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

  Future<void> _pickDate({
    required DateTime initialDate,
    required ValueChanged<DateTime> onPicked,
  }) async {
    final picked = await showDatePicker(
      context: context,
      initialDate: initialDate,
      firstDate: DateTime(2020),
      lastDate: DateTime(2100),
    );
    if (picked != null) {
      onPicked(picked);
    }
  }

  Future<void> _pickInventoryAttachment() async {
    final source = await _showImageSourceSheet();
    if (source == null) {
      return;
    }
    if (!mounted) {
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
      if (mounted) {
        setState(() => _imagePath = path);
      }
    } catch (error, stackTrace) {
      if (!mounted) {
        return;
      }
      showAppErrorSnackBar(
        context,
        message: '图片附件保存失败',
        error: error,
        stackTrace: stackTrace,
      );
    } finally {
      if (mounted) {
        setState(() => _pickingAttachment = false);
      }
    }
  }

  Future<_ImageSourceChoice?> _showImageSourceSheet() {
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
                    '更换物品照片',
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
      case _ImageSourceChoice.gallery:
        final file = await _imagePicker.pickImage(
          source: ImageSource.gallery,
          requestFullMetadata: false,
        );
        if (file == null) {
          return null;
        }
        return _PickedImage.fromImagePicker(file);
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
      case _ImageSourceChoice.file:
        final file = await file_selector.openFile(
          acceptedTypeGroups: const [
            file_selector.XTypeGroup(
              label: '库存图片',
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
        content: Text(
          '当前平台暂不支持直接拍照，请改用相册或文件',
        ),
      ),
    );
  }

  Future<void> _save() async {
    if (!_formKey.currentState!.validate()) {
      return;
    }

    setState(() => _saving = true);
    try {
      await widget.controller.updateItem(
        itemId: widget.item.id,
        quantity: int.parse(_quantityController.text),
        unit: _unitController.text,
        description: _descriptionController.text,
        purchaseDate: _purchaseDate,
        expiryDate: _expiryDate,
        storageLocation: _storageLocation,
        imagePath: _imagePath,
        tags: _selectedTags.toList(),
        isReminderEnabled: _isReminderEnabled,
        reminderDaysBefore: int.tryParse(_reminderDaysController.text) ?? 3,
      );
      if (mounted) {
        Navigator.of(context).pop(true);
      }
    } finally {
      if (mounted) {
        setState(() => _saving = false);
      }
    }
  }
}

class _DateField extends StatelessWidget {
  const _DateField({
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
    final text =
        value == null ? '未设置' : DateFormat('yyyy-MM-dd').format(value!);
    return InkWell(
      borderRadius: BorderRadius.circular(14),
      onTap: onTap,
      child: InputDecorator(
        decoration: InputDecoration(
          labelText: label,
          prefixIcon: const Icon(Icons.calendar_today_outlined),
          suffixIcon: value == null
              ? null
              : IconButton(
                  tooltip: '清除日期',
                  onPressed: onClear,
                  icon: const Icon(Icons.close),
                ),
        ),
        child: Text(
          text,
          style: TextStyle(
            color: value == null ? AppColors.textHint : AppColors.textPrimary,
            fontWeight: FontWeight.w600,
          ),
        ),
      ),
    );
  }
}

const _storageLocationOptions = [
  '冷藏',
  '冷冻',
  '常温',
  '药箱',
  '浴室',
  '其他',
];

enum _ImageSourceChoice { gallery, file, camera }

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
