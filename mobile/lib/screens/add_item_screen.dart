import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../data/inventory_controller.dart';
import '../theme/app_theme.dart';
import '../widgets/app_cards.dart';

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
  DateTime? _purchaseDate = DateTime.now();
  DateTime? _expiryDate;
  String? _categoryId;
  bool _saving = false;

  @override
  void dispose() {
    _nameController.dispose();
    _quantityController.dispose();
    _unitController.dispose();
    _descriptionController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final categories = widget.controller.categories;
    final selectedCategoryId = _categoryId ?? (categories.isEmpty ? null : categories.first.id);

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
                          onChanged: (value) => setState(() => _categoryId = value),
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
                            onPicked: (date) => setState(() => _purchaseDate = date),
                          ),
                        ),
                        const SizedBox(height: 12),
                        _DateField(
                          label: '过期日期',
                          value: _expiryDate,
                          onTap: () => _pickDate(
                            initialDate: _expiryDate ?? DateTime.now().add(const Duration(days: 7)),
                            onPicked: (date) => setState(() => _expiryDate = date),
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 18),
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
        unit: _unitController.text.trim().isEmpty ? null : _unitController.text.trim(),
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
    final text = value == null ? '未设置' : DateFormat('yyyy-MM-dd').format(value!);
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
