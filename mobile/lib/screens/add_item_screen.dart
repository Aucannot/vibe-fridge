import 'dart:async';
import 'dart:io' show Platform;

import 'package:file_selector/file_selector.dart' as file_selector;
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:image_picker/image_picker.dart';
import 'package:intl/intl.dart';

import '../data/inventory_controller.dart';
import '../data/local_image_store.dart';
import '../data/order_text_import_parser.dart';
import '../data/vlm_order_service.dart';
import '../data/vlm_settings_store.dart';
import '../theme/app_theme.dart';
import '../widgets/app_cards.dart';
import '../widgets/image_attachment_card.dart';
import '../widgets/tag_selector_card.dart';
import 'order_import_review_screen.dart';

class AddItemScreen extends StatefulWidget {
  const AddItemScreen({
    super.key,
    required this.controller,
    required this.onItemSaved,
  });

  final InventoryController controller;
  final VoidCallback onItemSaved;

  @override
  State<AddItemScreen> createState() => _AddItemScreenState();
}

class _AddItemScreenState extends State<AddItemScreen> {
  final _formKey = GlobalKey<FormState>();
  final _nameController = TextEditingController();
  final _quantityController = TextEditingController(text: '1');
  final _unitController = TextEditingController();
  final _descriptionController = TextEditingController();
  final _settingsStore = VlmSettingsStore();
  final _orderService = VlmOrderService();
  final _imagePicker = ImagePicker();
  DateTime? _purchaseDate = DateTime.now();
  DateTime? _expiryDate;
  String? _categoryId;
  String? _storageLocation;
  String? _imagePath;
  Set<String> _selectedTags = {};
  bool _saving = false;
  bool _recognizing = false;
  bool _parsingText = false;
  bool _pickingAttachment = false;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      unawaited(_recoverLostImagePickerData());
    });
  }

  @override
  void dispose() {
    _nameController.dispose();
    _quantityController.dispose();
    _unitController.dispose();
    _descriptionController.dispose();
    _orderService.close();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final categories = widget.controller.categories;
    final selectedCategoryId =
        _categoryId ?? (categories.isEmpty ? null : categories.first.id);

    return ListView(
      padding: AppSpacing.pageListPadding,
      children: [
        const PageHeader(
          title: '添加物品',
          subtitle: '创建库存记录时会自动创建或关联物品资料',
        ),
        PageSection(
          child: Form(
            key: _formKey,
            child: Column(
              children: [
                _CaptureEntryCards(
                  recognizing: _recognizing,
                  parsingText: _parsingText,
                  pickingAttachment: _pickingAttachment,
                  onPickAttachment: _pickInventoryAttachment,
                  onRecognizeOrder: _recognizeOrder,
                  onPasteOrderText: _pasteOrderText,
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
                      TextFormField(
                        controller: _nameController,
                        textInputAction: TextInputAction.next,
                        decoration: const InputDecoration(
                          labelText: '物品名称',
                          prefixIcon: Icon(Icons.inventory_2_outlined),
                        ),
                        validator: (value) {
                          if (value == null || value.trim().isEmpty) {
                            return '请输入物品名称';
                          }
                          return null;
                        },
                      ),
                      const SizedBox(height: 12),
                      DropdownButtonFormField<String>(
                        initialValue: selectedCategoryId,
                        decoration: const InputDecoration(
                          labelText: '分类',
                          prefixIcon: Icon(Icons.category_outlined),
                        ),
                        items: categories
                            .map(
                              (category) => DropdownMenuItem(
                                value: category.id,
                                child: Text(category.name),
                              ),
                            )
                            .toList(),
                        onChanged: (value) =>
                            setState(() => _categoryId = value),
                      ),
                      const SizedBox(height: 12),
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
                SectionCard(
                  child: Column(
                    children: [
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
                      _DateField(
                        label: '购买日期',
                        value: _purchaseDate,
                        onTap: () => _pickDate(
                          initialDate: _purchaseDate ?? DateTime.now(),
                          onPicked: (date) =>
                              setState(() => _purchaseDate = date),
                        ),
                      ),
                      const SizedBox(height: 12),
                      _DateField(
                        label: '过期日期',
                        value: _expiryDate,
                        onTap: () => _pickDate(
                          initialDate: _expiryDate ??
                              DateTime.now().add(const Duration(days: 7)),
                          onPicked: (date) =>
                              setState(() => _expiryDate = date),
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: AppSpacing.sectionGap),
                SizedBox(
                  width: double.infinity,
                  child: FilledButton.icon(
                    onPressed: _saving ? null : () => _save(selectedCategoryId),
                    icon: _saving
                        ? const SizedBox(
                            width: 18,
                            height: 18,
                            child: CircularProgressIndicator(strokeWidth: 2),
                          )
                        : const Icon(Icons.check),
                    label: Text(_saving ? '保存中' : '保存物品'),
                  ),
                ),
              ],
            ),
          ),
        ),
      ],
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

  Future<void> _save(String? categoryId) async {
    if (!_formKey.currentState!.validate()) {
      return;
    }

    setState(() => _saving = true);
    try {
      await widget.controller.createItem(
        name: _nameController.text,
        categoryId: categoryId,
        description: _descriptionController.text.trim().isEmpty
            ? null
            : _descriptionController.text.trim(),
        quantity: int.parse(_quantityController.text),
        unit: _unitController.text.trim().isEmpty
            ? null
            : _unitController.text.trim(),
        purchaseDate: _purchaseDate,
        expiryDate: _expiryDate,
        imagePath: _imagePath,
        storageLocation: _storageLocation,
        tags: _selectedTags.toList(),
      );
      _nameController.clear();
      _quantityController.text = '1';
      _unitController.clear();
      _descriptionController.clear();
      setState(() {
        _purchaseDate = DateTime.now();
        _expiryDate = null;
        _storageLocation = null;
        _imagePath = null;
        _selectedTags = {};
      });
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('物品已保存')),
        );
        widget.onItemSaved();
      }
    } finally {
      if (mounted) {
        setState(() => _saving = false);
      }
    }
  }

  Future<void> _recognizeOrder() async {
    final source = await _showImageSourceSheet(title: '导入订单图片');
    if (source == null) {
      return;
    }
    if (!mounted) {
      return;
    }

    setState(() => _recognizing = true);
    try {
      final image = await _pickImage(source);
      if (image == null) {
        return;
      }
      final settings = await _loadConfiguredOrderSettings();
      if (settings == null || !mounted) {
        return;
      }
      final imagePath = await _saveSelectedImage(image, 'order_imports');
      await _recognizeSelectedOrderImage(
        image,
        settings: settings,
        imagePath: imagePath,
      );
    } catch (error, stackTrace) {
      if (!mounted) {
        return;
      }
      showAppErrorSnackBar(
        context,
        message: '订单识别失败',
        error: error,
        stackTrace: stackTrace,
      );
    } finally {
      if (mounted) {
        setState(() => _recognizing = false);
      }
    }
  }

  Future<_OrderImageSource?> _showImageSourceSheet({
    required String title,
    String cameraLabel = '拍照识别',
    bool cameraFirst = false,
  }) {
    return showModalBottomSheet<_OrderImageSource>(
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
                    title,
                    style: Theme.of(context).textTheme.titleMedium?.copyWith(
                          fontWeight: FontWeight.w900,
                        ),
                  ),
                ),
                if (cameraFirst)
                  ListTile(
                    leading: const Icon(Icons.photo_camera_outlined),
                    title: Text(cameraLabel),
                    onTap: () =>
                        Navigator.of(context).pop(_OrderImageSource.camera),
                  ),
                ListTile(
                  leading: const Icon(Icons.photo_library_outlined),
                  title: const Text('从相册选择'),
                  onTap: () =>
                      Navigator.of(context).pop(_OrderImageSource.gallery),
                ),
                ListTile(
                  leading: const Icon(Icons.folder_open_outlined),
                  title: const Text('从文件选择'),
                  onTap: () =>
                      Navigator.of(context).pop(_OrderImageSource.file),
                ),
                if (!cameraFirst)
                  ListTile(
                    leading: const Icon(Icons.photo_camera_outlined),
                    title: Text(cameraLabel),
                    onTap: () =>
                        Navigator.of(context).pop(_OrderImageSource.camera),
                  ),
              ],
            ),
          ),
        );
      },
    );
  }

  Future<_SelectedOrderImage?> _pickImage(_OrderImageSource source) async {
    switch (source) {
      case _OrderImageSource.gallery:
        final file = await _imagePicker.pickImage(
          source: ImageSource.gallery,
          requestFullMetadata: false,
        );
        if (file == null) {
          return null;
        }
        return _SelectedOrderImage.fromImagePicker(file);
      case _OrderImageSource.camera:
        try {
          final file = await _imagePicker.pickImage(
            source: ImageSource.camera,
            requestFullMetadata: false,
          );
          if (file == null) {
            return null;
          }
          return _SelectedOrderImage.fromImagePicker(file);
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
      case _OrderImageSource.file:
        final file = await file_selector.openFile(
          acceptedTypeGroups: const [
            file_selector.XTypeGroup(
              label: '订单截图',
              extensions: ['png', 'jpg', 'jpeg', 'webp', 'heic', 'heif'],
            ),
          ],
        );
        if (file == null) {
          return null;
        }
        return _SelectedOrderImage.fromFileSelector(file);
    }
  }

  Future<void> _recoverLostImagePickerData() async {
    if (kIsWeb || !Platform.isAndroid) {
      return;
    }
    final response = await _imagePicker.retrieveLostData();
    if (!mounted || response.isEmpty) {
      return;
    }
    if (response.exception != null) {
      showAppErrorSnackBar(
        context,
        message: '图片恢复失败',
        error: response.exception,
      );
      return;
    }
    final files = response.files;
    if (files == null || files.isEmpty) {
      return;
    }
    final file = files.first;
    setState(() => _recognizing = true);
    try {
      final image = await _SelectedOrderImage.fromImagePicker(file);
      final settings = await _loadConfiguredOrderSettings();
      if (settings == null || !mounted) {
        return;
      }
      final imagePath = await _saveSelectedImage(image, 'order_imports');
      await _recognizeSelectedOrderImage(
        image,
        settings: settings,
        imagePath: imagePath,
      );
    } finally {
      if (mounted) {
        setState(() => _recognizing = false);
      }
    }
  }

  Future<VlmSettings?> _loadConfiguredOrderSettings() async {
    final settings = await _settingsStore.load();
    if (settings.isConfigured) {
      return settings;
    }
    if (!mounted) {
      return null;
    }
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('请先在设置里配置订单识别服务和 API 密钥'),
      ),
    );
    return null;
  }

  Future<void> _recognizeSelectedOrderImage(
    _SelectedOrderImage image, {
    required VlmSettings settings,
    String? imagePath,
  }) async {
    final effectiveImagePath = imagePath ?? image.path;
    final result = await _orderService.recognizeOrderImage(
      imageBytes: image.bytes,
      mimeType: image.mimeType,
      settings: settings,
      categoryNames: widget.controller.categories
          .map((category) => category.name)
          .toList(),
    );
    if (!mounted) {
      return;
    }
    final imported = await Navigator.of(context).push<bool>(
      MaterialPageRoute(
        builder: (_) => OrderImportReviewScreen(
          controller: widget.controller,
          result: result,
          imagePath: effectiveImagePath,
        ),
      ),
    );
    if (imported == true && mounted) {
      widget.onItemSaved();
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

  Future<void> _pickInventoryAttachment() async {
    final source = await _showImageSourceSheet(
      title: '添加物品照片',
      cameraLabel: '拍照记录',
      cameraFirst: true,
    );
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
      final path = await _saveSelectedImage(image, 'inventory');
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

  Future<void> _pasteOrderText() async {
    final text = await _showOrderTextDialog();
    if (text == null) {
      return;
    }

    setState(() => _parsingText = true);
    try {
      final result = parseOrderTextImport(text);
      if (!mounted) {
        return;
      }
      final imported = await Navigator.of(context).push<bool>(
        MaterialPageRoute(
          builder: (_) => OrderImportReviewScreen(
            controller: widget.controller,
            result: result,
          ),
        ),
      );
      if (imported == true && mounted) {
        widget.onItemSaved();
      }
    } catch (error, stackTrace) {
      if (!mounted) {
        return;
      }
      showAppErrorSnackBar(
        context,
        message: '文本解析失败',
        error: error,
        stackTrace: stackTrace,
      );
    } finally {
      if (mounted) {
        setState(() => _parsingText = false);
      }
    }
  }

  Future<String?> _showOrderTextDialog() async {
    final controller = TextEditingController();
    String? errorText;
    try {
      final result = await showDialog<String>(
        context: context,
        builder: (context) => StatefulBuilder(
          builder: (context, setDialogState) {
            return AlertDialog(
              title: const Text('粘贴订单文本'),
              content: SizedBox(
                width: 560,
                child: TextField(
                  controller: controller,
                  minLines: 8,
                  maxLines: 12,
                  autofocus: true,
                  decoration: InputDecoration(
                    labelText: '订单文本',
                    alignLabelWithHint: true,
                    prefixIcon: const Icon(Icons.receipt_long_outlined),
                    errorText: errorText,
                  ),
                ),
              ),
              actions: [
                TextButton(
                  onPressed: () => Navigator.of(context).pop(),
                  child: const Text('取消'),
                ),
                FilledButton(
                  onPressed: () {
                    final value = controller.text.trim();
                    if (value.isEmpty) {
                      setDialogState(() => errorText = '请先粘贴订单文本');
                      return;
                    }
                    Navigator.of(context).pop(value);
                  },
                  child: const Text('预览'),
                ),
              ],
            );
          },
        ),
      );
      return result;
    } finally {
      controller.dispose();
    }
  }
}

class _CaptureEntryCards extends StatelessWidget {
  const _CaptureEntryCards({
    required this.recognizing,
    required this.parsingText,
    required this.pickingAttachment,
    required this.onPickAttachment,
    required this.onRecognizeOrder,
    required this.onPasteOrderText,
  });

  final bool recognizing;
  final bool parsingText;
  final bool pickingAttachment;
  final VoidCallback onPickAttachment;
  final VoidCallback onRecognizeOrder;
  final VoidCallback onPasteOrderText;

  @override
  Widget build(BuildContext context) {
    final cards = [
      _CaptureCard(
        icon: Icons.photo_camera_outlined,
        title: '拍照识别',
        subtitle: '记录食材包装、小票或标签照片',
        color: AppColors.primaryDark,
        primaryLabel: pickingAttachment ? '处理中' : '添加照片',
        primaryIcon: pickingAttachment
            ? const SizedBox(
                width: 18,
                height: 18,
                child: CircularProgressIndicator(strokeWidth: 2),
              )
            : const Icon(Icons.add_photo_alternate_outlined),
        onPrimaryPressed: pickingAttachment ? null : onPickAttachment,
      ),
      _CaptureCard(
        icon: Icons.receipt_long_outlined,
        title: '订单识别',
        subtitle: '订单截图或粘贴文本，预览后批量入库',
        color: AppColors.warning,
        primaryLabel: recognizing ? '识别中' : '图片导入',
        primaryIcon: recognizing
            ? const SizedBox(
                width: 18,
                height: 18,
                child: CircularProgressIndicator(strokeWidth: 2),
              )
            : const Icon(Icons.image_search_outlined),
        onPrimaryPressed: recognizing ? null : onRecognizeOrder,
        secondaryLabel: parsingText ? '解析中' : '粘贴文本',
        secondaryIcon: parsingText
            ? const SizedBox(
                width: 18,
                height: 18,
                child: CircularProgressIndicator(strokeWidth: 2),
              )
            : const Icon(Icons.content_paste_outlined),
        onSecondaryPressed: parsingText ? null : onPasteOrderText,
      ),
    ];

    return LayoutBuilder(
      builder: (context, constraints) {
        final columns = constraints.maxWidth >= AppBreakpoints.wideGrid ? 2 : 1;
        final width =
            (constraints.maxWidth - AppSpacing.cardGap * (columns - 1)) /
                columns;
        return Wrap(
          spacing: AppSpacing.cardGap,
          runSpacing: AppSpacing.cardGap,
          children:
              cards.map((card) => SizedBox(width: width, child: card)).toList(),
        );
      },
    );
  }
}

class _CaptureCard extends StatelessWidget {
  const _CaptureCard({
    required this.icon,
    required this.title,
    required this.subtitle,
    required this.color,
    required this.primaryLabel,
    required this.primaryIcon,
    required this.onPrimaryPressed,
    this.secondaryLabel,
    this.secondaryIcon,
    this.onSecondaryPressed,
  });

  final IconData icon;
  final String title;
  final String subtitle;
  final Color color;
  final String primaryLabel;
  final Widget primaryIcon;
  final VoidCallback? onPrimaryPressed;
  final String? secondaryLabel;
  final Widget? secondaryIcon;
  final VoidCallback? onSecondaryPressed;

  @override
  Widget build(BuildContext context) {
    return SectionCard(
      color: AppColors.surfaceWarm,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                width: 44,
                height: 44,
                decoration: BoxDecoration(
                  color: color.withValues(alpha: 0.14),
                  borderRadius: BorderRadius.circular(AppRadii.large),
                ),
                child: Icon(icon, color: color),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      title,
                      style: Theme.of(context).textTheme.titleMedium?.copyWith(
                            color: AppColors.textPrimary,
                            fontWeight: FontWeight.w900,
                          ),
                    ),
                    const SizedBox(height: 3),
                    Text(
                      subtitle,
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                            color: AppColors.textSecondary,
                          ),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: AppSpacing.fieldGap),
          SizedBox(
            width: double.infinity,
            child: FilledButton.icon(
              onPressed: onPrimaryPressed,
              icon: primaryIcon,
              label: Text(primaryLabel),
            ),
          ),
          if (secondaryLabel != null && secondaryIcon != null) ...[
            const SizedBox(height: 10),
            SizedBox(
              width: double.infinity,
              child: OutlinedButton.icon(
                onPressed: onSecondaryPressed,
                icon: secondaryIcon!,
                label: Text(secondaryLabel!),
              ),
            ),
          ],
        ],
      ),
    );
  }
}

enum _OrderImageSource { gallery, file, camera }

const _storageLocationOptions = [
  '冷藏',
  '冷冻',
  '常温',
  '药箱',
  '浴室',
  '其他',
];

class _SelectedOrderImage {
  const _SelectedOrderImage({
    required this.bytes,
    required this.mimeType,
    required this.name,
    this.path,
  });

  final Uint8List bytes;
  final String mimeType;
  final String name;
  final String? path;

  static Future<_SelectedOrderImage> fromImagePicker(XFile file) async {
    return _SelectedOrderImage(
      bytes: await file.readAsBytes(),
      mimeType: _mimeTypeForImage(
        mimeType: file.mimeType,
        name: file.name,
        path: file.path,
      ),
      name: file.name.isEmpty ? 'image' : file.name,
      path: file.path.isEmpty ? null : file.path,
    );
  }

  static Future<_SelectedOrderImage> fromFileSelector(
    file_selector.XFile file,
  ) async {
    return _SelectedOrderImage(
      bytes: await file.readAsBytes(),
      mimeType: _mimeTypeForImage(
        mimeType: file.mimeType,
        name: file.name,
        path: file.path,
      ),
      name: file.name.isEmpty ? 'image' : file.name,
      path: file.path.isEmpty ? null : file.path,
    );
  }
}

Future<String> _saveSelectedImage(
  _SelectedOrderImage image,
  String folderName,
) async {
  return LocalImageStore.saveImage(
    bytes: image.bytes,
    folderName: folderName,
    originalName: image.name,
    mimeType: image.mimeType,
  );
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

class _DateField extends StatelessWidget {
  const _DateField({
    required this.label,
    required this.value,
    required this.onTap,
  });

  final String label;
  final DateTime? value;
  final VoidCallback onTap;

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
