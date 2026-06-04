import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../data/inventory_controller.dart';
import '../models/inventory_item.dart';
import '../theme/app_theme.dart';
import '../widgets/app_cards.dart';

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
  late DateTime? _purchaseDate;
  late DateTime? _expiryDate;
  late bool _isReminderEnabled;
  bool _saving = false;

  @override
  void initState() {
    super.initState();
    final item = widget.item;
    _quantityController = TextEditingController(text: '${item.quantity}');
    _unitController = TextEditingController(text: item.unit ?? '');
    _descriptionController =
        TextEditingController(text: item.description ?? '');
    _purchaseDate = item.purchaseDate;
    _expiryDate = item.expiryDate;
    _isReminderEnabled = item.isReminderEnabled;
  }

  @override
  void dispose() {
    _quantityController.dispose();
    _unitController.dispose();
    _descriptionController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('编辑库存')),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(20, 8, 20, 24),
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
                        const SizedBox(height: 12),
                        TextFormField(
                          controller: _unitController,
                          decoration: const InputDecoration(
                            labelText: '单位',
                            prefixIcon: Icon(Icons.straighten_outlined),
                          ),
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
                          onClear: () => setState(() => _expiryDate = null),
                        ),
                        const SizedBox(height: 8),
                        SwitchListTile(
                          contentPadding: EdgeInsets.zero,
                          value: _isReminderEnabled,
                          title: const Text('启用过期提醒'),
                          subtitle: const Text('默认在过期前 3 天提醒'),
                          onChanged: (value) {
                            setState(() => _isReminderEnabled = value);
                          },
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 18),
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
        isReminderEnabled: _isReminderEnabled,
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
