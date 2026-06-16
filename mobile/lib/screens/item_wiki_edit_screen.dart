import 'package:flutter/material.dart';

import '../data/inventory_controller.dart';
import '../models/item_wiki.dart';
import '../theme/app_theme.dart';
import '../widgets/app_cards.dart';

class ItemWikiEditScreen extends StatefulWidget {
  const ItemWikiEditScreen({
    super.key,
    required this.controller,
    required this.wiki,
  });

  final InventoryController controller;
  final ItemWiki wiki;

  @override
  State<ItemWikiEditScreen> createState() => _ItemWikiEditScreenState();
}

class _ItemWikiEditScreenState extends State<ItemWikiEditScreen> {
  final _formKey = GlobalKey<FormState>();
  late final TextEditingController _nameController;
  late final TextEditingController _iconController;
  late final TextEditingController _descriptionController;
  late final TextEditingController _unitController;
  late final TextEditingController _expiryDaysController;
  late final TextEditingController _defaultReminderDaysController;
  late final TextEditingController _storageController;
  late final TextEditingController _notesController;
  late String? _categoryId;
  bool _saving = false;

  @override
  void initState() {
    super.initState();
    final wiki = widget.wiki;
    _nameController = TextEditingController(text: wiki.name);
    _iconController = TextEditingController(text: wiki.icon ?? '');
    _descriptionController =
        TextEditingController(text: wiki.description ?? '');
    _unitController = TextEditingController(text: wiki.defaultUnit ?? '');
    _expiryDaysController = TextEditingController(
      text: wiki.suggestedExpiryDays?.toString() ?? '',
    );
    _defaultReminderDaysController =
        TextEditingController(text: '${wiki.defaultReminderDays}');
    _storageController =
        TextEditingController(text: wiki.storageLocation ?? '');
    _notesController = TextEditingController(text: wiki.notes ?? '');
    _categoryId = wiki.categoryId ??
        (widget.controller.categories.isEmpty
            ? null
            : widget.controller.categories.first.id);
  }

  @override
  void dispose() {
    _nameController.dispose();
    _iconController.dispose();
    _descriptionController.dispose();
    _unitController.dispose();
    _expiryDaysController.dispose();
    _defaultReminderDaysController.dispose();
    _storageController.dispose();
    _notesController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('编辑物品资料')),
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
                        const SizedBox(height: AppSpacing.cardGap),
                        DropdownButtonFormField<String>(
                          initialValue: _categoryId,
                          decoration: const InputDecoration(
                            labelText: '分类',
                            prefixIcon: Icon(Icons.category_outlined),
                          ),
                          items: widget.controller.categories
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
                        const SizedBox(height: AppSpacing.cardGap),
                        TextFormField(
                          controller: _iconController,
                          decoration: const InputDecoration(
                            labelText: '图标标识',
                            prefixIcon: Icon(Icons.emoji_symbols_outlined),
                          ),
                        ),
                        const SizedBox(height: AppSpacing.cardGap),
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
                        TextFormField(
                          controller: _unitController,
                          decoration: const InputDecoration(
                            labelText: '默认单位',
                            prefixIcon: Icon(Icons.straighten_outlined),
                          ),
                        ),
                        const SizedBox(height: AppSpacing.cardGap),
                        TextFormField(
                          controller: _expiryDaysController,
                          keyboardType: TextInputType.number,
                          decoration: const InputDecoration(
                            labelText: '建议保质期（天）',
                            prefixIcon: Icon(Icons.event_available_outlined),
                          ),
                          validator: (value) {
                            if (value == null || value.trim().isEmpty) {
                              return null;
                            }
                            final parsed = int.tryParse(value);
                            if (parsed == null || parsed <= 0) {
                              return '请输入大于 0 的整数';
                            }
                            return null;
                          },
                        ),
                        const SizedBox(height: AppSpacing.cardGap),
                        TextFormField(
                          controller: _defaultReminderDaysController,
                          keyboardType: TextInputType.number,
                          decoration: const InputDecoration(
                            labelText: '默认提醒提前天数',
                            prefixIcon: Icon(Icons.alarm_outlined),
                            suffixText: '天',
                          ),
                          validator: (value) {
                            final parsed = int.tryParse(value ?? '');
                            if (parsed == null || parsed < 0) {
                              return '请输入 0 或更大的整数';
                            }
                            return null;
                          },
                        ),
                        const SizedBox(height: AppSpacing.cardGap),
                        TextFormField(
                          controller: _storageController,
                          decoration: const InputDecoration(
                            labelText: '建议存放位置',
                            prefixIcon: Icon(Icons.kitchen_outlined),
                          ),
                        ),
                        const SizedBox(height: AppSpacing.cardGap),
                        TextFormField(
                          controller: _notesController,
                          minLines: 2,
                          maxLines: 4,
                          decoration: const InputDecoration(
                            labelText: '备注',
                            alignLabelWithHint: true,
                            prefixIcon: Icon(Icons.edit_note_outlined),
                          ),
                        ),
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
                      label: Text(_saving ? '保存中' : '保存资料'),
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

  Future<void> _save() async {
    if (!_formKey.currentState!.validate()) {
      return;
    }

    setState(() => _saving = true);
    try {
      await widget.controller.updateWiki(
        wikiId: widget.wiki.id,
        name: _nameController.text,
        categoryId: _categoryId,
        icon: _iconController.text,
        description: _descriptionController.text,
        defaultUnit: _unitController.text,
        suggestedExpiryDays: _expiryDaysController.text.trim().isEmpty
            ? null
            : int.parse(_expiryDaysController.text),
        defaultReminderDays: int.parse(_defaultReminderDaysController.text),
        storageLocation: _storageController.text,
        notes: _notesController.text,
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
