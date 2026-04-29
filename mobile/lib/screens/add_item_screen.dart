import 'package:file_selector/file_selector.dart';
import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../data/inventory_controller.dart';
import '../data/vlm_order_service.dart';
import '../data/vlm_settings_store.dart';
import '../theme/app_theme.dart';
import '../widgets/app_cards.dart';
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
  DateTime? _purchaseDate = DateTime.now();
  DateTime? _expiryDate;
  String? _categoryId;
  bool _saving = false;
  bool _recognizing = false;

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
      padding: const EdgeInsets.only(bottom: 24),
      children: [
        const PageHeader(
          title: '添加物品',
          subtitle: '创建库存记录时会自动创建或关联 Wiki 条目',
        ),
        ContentWidth(
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 20),
            child: Form(
              key: _formKey,
              child: Column(
                children: [
                  SectionCard(
                    child: Row(
                      children: [
                        Container(
                          width: 44,
                          height: 44,
                          decoration: BoxDecoration(
                            color: AppColors.primary.withValues(alpha: 0.12),
                            borderRadius: BorderRadius.circular(16),
                          ),
                          child: const Icon(
                            Icons.document_scanner_outlined,
                            color: AppColors.primary,
                          ),
                        ),
                        const SizedBox(width: 14),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                '订单截图识别',
                                style: Theme.of(context)
                                    .textTheme
                                    .titleMedium
                                    ?.copyWith(
                                      fontWeight: FontWeight.w900,
                                    ),
                              ),
                              const SizedBox(height: 4),
                              Text(
                                '识别后预览确认，再批量添加库存',
                                style: Theme.of(context)
                                    .textTheme
                                    .bodyMedium
                                    ?.copyWith(
                                      color: AppColors.textSecondary,
                                    ),
                              ),
                            ],
                          ),
                        ),
                        const SizedBox(width: 12),
                        FilledButton.icon(
                          onPressed: _recognizing ? null : _recognizeOrder,
                          icon: _recognizing
                              ? const SizedBox(
                                  width: 18,
                                  height: 18,
                                  child:
                                      CircularProgressIndicator(strokeWidth: 2),
                                )
                              : const Icon(Icons.image_search_outlined),
                          label: Text(_recognizing ? '识别中' : '选择图片'),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 14),
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
                  const SizedBox(height: 14),
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
                  const SizedBox(height: 18),
                  SizedBox(
                    width: double.infinity,
                    child: FilledButton.icon(
                      onPressed:
                          _saving ? null : () => _save(selectedCategoryId),
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
      );
      _nameController.clear();
      _quantityController.text = '1';
      _unitController.clear();
      _descriptionController.clear();
      setState(() {
        _purchaseDate = DateTime.now();
        _expiryDate = null;
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
    setState(() => _recognizing = true);
    try {
      final file = await openFile(
        acceptedTypeGroups: const [
          XTypeGroup(
            label: '订单截图',
            extensions: ['png', 'jpg', 'jpeg', 'webp', 'heic'],
          ),
        ],
      );
      if (file == null) {
        return;
      }

      final settings = await _settingsStore.load();
      if (!settings.isConfigured) {
        if (!mounted) {
          return;
        }
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
              content: Text('请先在设置里配置 VLM endpoint、model 和 API key')),
        );
        return;
      }
      final bytes = await file.readAsBytes();
      final result = await _orderService.recognizeOrderImage(
        imageBytes: bytes,
        mimeType: _mimeTypeForFile(file),
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
            imagePath: file.path,
          ),
        ),
      );
      if (imported == true && mounted) {
        widget.onItemSaved();
      }
    } catch (error) {
      if (!mounted) {
        return;
      }
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('订单识别失败：$error')),
      );
    } finally {
      if (mounted) {
        setState(() => _recognizing = false);
      }
    }
  }
}

String _mimeTypeForFile(XFile file) {
  final mimeType = file.mimeType;
  if (mimeType != null && mimeType.isNotEmpty) {
    return mimeType;
  }
  final name = file.name.toLowerCase();
  if (name.endsWith('.png')) {
    return 'image/png';
  }
  if (name.endsWith('.webp')) {
    return 'image/webp';
  }
  if (name.endsWith('.heic')) {
    return 'image/heic';
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
