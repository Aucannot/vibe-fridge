import 'package:flutter/material.dart';

import '../data/todo_controller.dart';
import '../models/todo_item.dart';
import '../theme/app_theme.dart';
import '../widgets/app_cards.dart';

enum _TodoFilter { all, today, upcoming, done }

class TodoScreen extends StatefulWidget {
  const TodoScreen({super.key, required this.controller});

  final TodoController controller;

  @override
  State<TodoScreen> createState() => _TodoScreenState();
}

class _TodoScreenState extends State<TodoScreen> {
  _TodoFilter _filter = _TodoFilter.all;

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: widget.controller,
      builder: (context, _) {
        final todos = _visibleTodos;
        return RefreshIndicator(
          onRefresh: widget.controller.refresh,
          child: ListView(
            padding: const EdgeInsets.only(bottom: 24),
            children: [
              PageHeader(
                title: '我的任务',
                subtitle:
                    '${_headerDate(DateTime.now())} · ${widget.controller.activeCount} 个待办',
                action: IconButton.filled(
                  tooltip: '添加任务',
                  onPressed: () => _openEditor(),
                  icon: const Icon(Icons.add),
                ),
              ),
              if (widget.controller.errorMessage != null)
                ContentWidth(
                  child: Padding(
                    padding: const EdgeInsets.fromLTRB(20, 0, 20, 12),
                    child: SectionCard(
                      child: Text(
                        widget.controller.errorMessage!,
                        style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                              color: AppColors.error,
                            ),
                      ),
                    ),
                  ),
                ),
              ContentWidth(
                child: Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 20),
                  child: Row(
                    children: [
                      Expanded(
                        child: _stat(
                          '待办',
                          '${widget.controller.activeCount}',
                          Icons.radio_button_unchecked,
                          AppColors.primary,
                        ),
                      ),
                      const SizedBox(width: 10),
                      Expanded(
                        child: _stat(
                          '今日',
                          '${widget.controller.todayCount}',
                          Icons.today_outlined,
                          AppColors.warning,
                        ),
                      ),
                      const SizedBox(width: 10),
                      Expanded(
                        child: _stat(
                          '完成',
                          '${widget.controller.completedCount}',
                          Icons.task_alt,
                          AppColors.success,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 14),
              ContentWidth(
                child: Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 20),
                  child: _filters(),
                ),
              ),
              const SizedBox(height: 12),
              ContentWidth(
                child: Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 20),
                  child: widget.controller.isLoading &&
                          widget.controller.todos.isEmpty
                      ? const SectionCard(
                          child: Center(child: CircularProgressIndicator()),
                        )
                      : _todoList(todos),
                ),
              ),
            ],
          ),
        );
      },
    );
  }

  List<TodoItem> get _visibleTodos {
    switch (_filter) {
      case _TodoFilter.all:
        return widget.controller.todos;
      case _TodoFilter.today:
        return widget.controller.todayTodos;
      case _TodoFilter.upcoming:
        return widget.controller.upcomingTodos;
      case _TodoFilter.done:
        return widget.controller.completedTodos;
    }
  }

  Widget _stat(String label, String value, IconData icon, Color color) {
    return SectionCard(
      padding: const EdgeInsets.all(12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(icon, size: 18, color: color),
              const Spacer(),
              Text(
                value,
                style: Theme.of(context).textTheme.titleLarge?.copyWith(
                      color: AppColors.textPrimary,
                      fontWeight: FontWeight.w900,
                    ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            label,
            style: Theme.of(context).textTheme.labelLarge?.copyWith(
                  color: AppColors.textSecondary,
                  fontWeight: FontWeight.w700,
                ),
          ),
        ],
      ),
    );
  }

  Widget _filters() {
    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      child: Row(
        children: _TodoFilter.values.map((filter) {
          return Padding(
            padding: const EdgeInsets.only(right: 8),
            child: ChoiceChip(
              label: Text(_filterLabel(filter)),
              selected: _filter == filter,
              onSelected: (_) => setState(() => _filter = filter),
            ),
          );
        }).toList(),
      ),
    );
  }

  Widget _todoList(List<TodoItem> todos) {
    if (todos.isEmpty) {
      return const EmptyState(
        icon: Icons.checklist_rtl_outlined,
        title: '这里很清爽',
        message: '点击右上角 +，把采购、整理和临期处理任务记下来。',
      );
    }
    return Column(
      children: todos
          .map(
            (todo) => Padding(
              padding: const EdgeInsets.only(bottom: 10),
              child: _todoTile(todo),
            ),
          )
          .toList(),
    );
  }

  Widget _todoTile(TodoItem todo) {
    return SectionCard(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
      onTap: () => _openEditor(todo),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Padding(
            padding: const EdgeInsets.only(top: 2),
            child: InkWell(
              borderRadius: BorderRadius.circular(999),
              onTap: () => widget.controller.setTodoCompleted(
                todo.id,
                !todo.isCompleted,
              ),
              child: Container(
                width: 30,
                height: 30,
                decoration: BoxDecoration(
                  color: todo.isCompleted ? AppColors.primary : Colors.white,
                  shape: BoxShape.circle,
                  border: Border.all(
                    color: todo.isCompleted
                        ? AppColors.primary
                        : AppColors.divider,
                    width: 1.5,
                  ),
                ),
                child: todo.isCompleted
                    ? const Icon(Icons.check, size: 18, color: Colors.white)
                    : null,
              ),
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  todo.title,
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        color: todo.isCompleted
                            ? AppColors.textHint
                            : AppColors.textPrimary,
                        decoration: todo.isCompleted
                            ? TextDecoration.lineThrough
                            : null,
                        fontWeight: FontWeight.w800,
                      ),
                ),
                if (todo.hasNotes) ...[
                  const SizedBox(height: 4),
                  Text(
                    todo.notes!,
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                    style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                          color: AppColors.textSecondary,
                        ),
                  ),
                ],
                const SizedBox(height: 10),
                Wrap(
                  spacing: 8,
                  runSpacing: 6,
                  children: [
                    StatusPill(
                      label: _dueLabel(todo),
                      icon: Icons.event_available_outlined,
                      color: _dueColor(todo),
                      backgroundColor: _dueBackground(todo),
                    ),
                    if (todo.priority != TodoPriority.normal)
                      StatusPill(
                        label: _priorityLabel(todo.priority),
                        icon: Icons.flag_outlined,
                        color: _priorityColor(todo.priority),
                        backgroundColor: _priorityBackground(todo.priority),
                      ),
                  ],
                ),
              ],
            ),
          ),
          IconButton(
            tooltip: todo.isStarred ? '取消重点' : '标为重点',
            onPressed: () => widget.controller.setTodoStarred(
              todo.id,
              !todo.isStarred,
            ),
            icon: Icon(
              todo.isStarred ? Icons.star_rounded : Icons.star_border_rounded,
              color: todo.isStarred ? AppColors.accent : AppColors.textHint,
            ),
          ),
        ],
      ),
    );
  }

  Future<void> _openEditor([TodoItem? todo]) async {
    await showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      useSafeArea: true,
      builder: (_) => _TodoEditor(
        controller: widget.controller,
        todo: todo,
      ),
    );
  }
}

class _TodoEditor extends StatefulWidget {
  const _TodoEditor({required this.controller, this.todo});

  final TodoController controller;
  final TodoItem? todo;

  @override
  State<_TodoEditor> createState() => _TodoEditorState();
}

class _TodoEditorState extends State<_TodoEditor> {
  late final TextEditingController _titleController;
  late final TextEditingController _notesController;
  DateTime? _dueDate;
  String _priority = TodoPriority.normal;
  bool _isStarred = false;
  bool _isSaving = false;

  bool get _isEditing => widget.todo != null;

  @override
  void initState() {
    super.initState();
    final todo = widget.todo;
    _titleController = TextEditingController(text: todo?.title ?? '');
    _notesController = TextEditingController(text: todo?.notes ?? '');
    _dueDate = todo?.dueDate;
    _priority = TodoPriority.normalize(todo?.priority);
    _isStarred = todo?.isStarred ?? false;
  }

  @override
  void dispose() {
    _titleController.dispose();
    _notesController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.only(bottom: MediaQuery.of(context).viewInsets.bottom),
      child: SingleChildScrollView(
        child: Padding(
          padding: const EdgeInsets.fromLTRB(20, 10, 20, 24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Center(
                child: Container(
                  width: 40,
                  height: 4,
                  margin: const EdgeInsets.only(bottom: 8),
                  decoration: BoxDecoration(
                    color: AppColors.divider,
                    borderRadius: BorderRadius.circular(999),
                  ),
                ),
              ),
              Row(
                children: [
                  TextButton(
                    onPressed: _isSaving ? null : () => Navigator.pop(context),
                    child: const Text('取消'),
                  ),
                  Expanded(
                    child: Text(
                      _isEditing ? '编辑任务' : '添加任务',
                      textAlign: TextAlign.center,
                      style: Theme.of(context).textTheme.titleMedium?.copyWith(
                            fontWeight: FontWeight.w900,
                          ),
                    ),
                  ),
                  TextButton(
                    onPressed: _isSaving ? null : _save,
                    child: _isSaving
                        ? const SizedBox(
                            width: 18,
                            height: 18,
                            child: CircularProgressIndicator(strokeWidth: 2),
                          )
                        : const Text('保存'),
                  ),
                ],
              ),
              const SizedBox(height: 8),
              TextField(
                controller: _titleController,
                autofocus: !_isEditing,
                textInputAction: TextInputAction.done,
                decoration: const InputDecoration(
                  hintText: '你想做什么？',
                  prefixIcon: Icon(Icons.task_alt_outlined),
                ),
                onSubmitted: (_) => _save(),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: _notesController,
                minLines: 2,
                maxLines: 4,
                decoration: const InputDecoration(
                  hintText: '备注，例如：采购、整理或临期处理信息',
                  prefixIcon: Icon(Icons.notes_outlined),
                ),
              ),
              const SizedBox(height: 14),
              SectionCard(
                padding: EdgeInsets.zero,
                child: Column(
                  children: [
                    ListTile(
                      leading: const Icon(Icons.event_available_outlined),
                      title: const Text('截止日期'),
                      subtitle: Text(
                        _dueDate == null ? '不设置日期' : _formatDate(_dueDate!),
                      ),
                      trailing: _dueDate == null
                          ? const Icon(Icons.chevron_right)
                          : IconButton(
                              tooltip: '清除日期',
                              onPressed: () => setState(() => _dueDate = null),
                              icon: const Icon(Icons.close),
                            ),
                      onTap: _pickDate,
                    ),
                    const Divider(height: 1),
                    SwitchListTile(
                      value: _isStarred,
                      onChanged: (value) => setState(() => _isStarred = value),
                      secondary: Icon(
                        _isStarred
                            ? Icons.star_rounded
                            : Icons.star_border_rounded,
                        color: _isStarred ? AppColors.accent : AppColors.textHint,
                      ),
                      title: const Text('重点任务'),
                      subtitle: const Text('在列表顶部优先展示'),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 12),
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: [
                  for (final priority in [
                    TodoPriority.low,
                    TodoPriority.normal,
                    TodoPriority.high,
                  ])
                    ChoiceChip(
                      label: Text(_priorityLabel(priority)),
                      selected: _priority == priority,
                      onSelected: (_) => setState(() => _priority = priority),
                    ),
                  ActionChip(
                    label: const Text('今天'),
                    onPressed: () => setState(
                      () => _dueDate = _dateOnly(DateTime.now()),
                    ),
                  ),
                  ActionChip(
                    label: const Text('明天'),
                    onPressed: () => setState(
                      () => _dueDate = _dateOnly(
                        DateTime.now().add(const Duration(days: 1)),
                      ),
                    ),
                  ),
                ],
              ),
              if (_isEditing) ...[
                const SizedBox(height: 16),
                TextButton.icon(
                  style: TextButton.styleFrom(foregroundColor: AppColors.error),
                  onPressed: _isSaving ? null : _delete,
                  icon: const Icon(Icons.delete_outline),
                  label: const Text('删除任务'),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }

  Future<void> _pickDate() async {
    final now = DateTime.now();
    final picked = await showDatePicker(
      context: context,
      initialDate: _dueDate ?? now,
      firstDate: DateTime(now.year - 1),
      lastDate: DateTime(now.year + 5),
    );
    if (picked == null || !mounted) {
      return;
    }
    setState(() => _dueDate = _dateOnly(picked));
  }

  Future<void> _save() async {
    final title = _titleController.text.trim();
    if (title.isEmpty) {
      _showMessage('先写一个任务标题');
      return;
    }

    setState(() => _isSaving = true);
    try {
      final todo = widget.todo;
      if (todo == null) {
        await widget.controller.createTodo(
          title: title,
          notes: _notesController.text,
          dueDate: _dueDate,
          priority: _priority,
          isStarred: _isStarred,
        );
      } else {
        await widget.controller.updateTodo(
          todoId: todo.id,
          title: title,
          notes: _notesController.text,
          dueDate: _dueDate,
          priority: _priority,
          isStarred: _isStarred,
        );
      }
      if (mounted) {
        Navigator.pop(context);
      }
    } catch (error) {
      _showMessage(error.toString());
    } finally {
      if (mounted) {
        setState(() => _isSaving = false);
      }
    }
  }

  Future<void> _delete() async {
    final todo = widget.todo;
    if (todo == null) {
      return;
    }
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('删除任务？'),
        content: Text('“${todo.title}” 删除后无法恢复。'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('取消'),
          ),
          TextButton(
            style: TextButton.styleFrom(foregroundColor: AppColors.error),
            onPressed: () => Navigator.pop(context, true),
            child: const Text('删除'),
          ),
        ],
      ),
    );
    if (confirmed != true || !mounted) {
      return;
    }

    setState(() => _isSaving = true);
    try {
      await widget.controller.deleteTodo(todo.id);
      if (mounted) {
        Navigator.pop(context);
      }
    } catch (error) {
      _showMessage(error.toString());
    } finally {
      if (mounted) {
        setState(() => _isSaving = false);
      }
    }
  }

  void _showMessage(String message) {
    if (!mounted) {
      return;
    }
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message)),
    );
  }
}

String _filterLabel(_TodoFilter filter) {
  switch (filter) {
    case _TodoFilter.all:
      return '全部';
    case _TodoFilter.today:
      return '今天';
    case _TodoFilter.upcoming:
      return '即将到来';
    case _TodoFilter.done:
      return '已完成';
  }
}

String _headerDate(DateTime date) {
  const weekdays = ['星期一', '星期二', '星期三', '星期四', '星期五', '星期六', '星期日'];
  return '${date.month}月${date.day}日 ${weekdays[date.weekday - 1]}';
}

String _formatDate(DateTime date) {
  final today = _dateOnly(DateTime.now());
  final value = _dateOnly(date);
  if (value == today) {
    return '今天';
  }
  if (value == today.add(const Duration(days: 1))) {
    return '明天';
  }
  return '${date.month}月${date.day}日';
}

String _dueLabel(TodoItem todo) {
  if (todo.isCompleted) {
    return '已完成';
  }
  final due = todo.dueDate;
  if (due == null) {
    return '无截止';
  }
  final today = _dateOnly(DateTime.now());
  final value = _dateOnly(due);
  if (value == today) {
    return '今天';
  }
  if (value == today.add(const Duration(days: 1))) {
    return '明天';
  }
  if (value.isBefore(today)) {
    return '逾期 ${today.difference(value).inDays} 天';
  }
  return '${due.month}月${due.day}日';
}

Color _dueColor(TodoItem todo) {
  if (todo.isCompleted) {
    return AppColors.success;
  }
  if (todo.isOverdue) {
    return AppColors.error;
  }
  if (todo.isDueToday) {
    return AppColors.warning;
  }
  if (todo.dueDate == null) {
    return AppColors.textHint;
  }
  return AppColors.secondary;
}

Color _dueBackground(TodoItem todo) {
  if (todo.isCompleted) {
    return AppColors.successContainer;
  }
  if (todo.isOverdue) {
    return AppColors.errorContainer;
  }
  if (todo.isDueToday) {
    return AppColors.warningContainer;
  }
  if (todo.dueDate == null) {
    return AppColors.surfaceVariant;
  }
  return AppColors.secondaryContainer;
}

String _priorityLabel(String priority) {
  switch (TodoPriority.normalize(priority)) {
    case TodoPriority.high:
      return '高优先级';
    case TodoPriority.low:
      return '低优先级';
    case TodoPriority.normal:
    default:
      return '普通';
  }
}

Color _priorityColor(String priority) {
  switch (TodoPriority.normalize(priority)) {
    case TodoPriority.high:
      return AppColors.error;
    case TodoPriority.low:
      return AppColors.textHint;
    case TodoPriority.normal:
    default:
      return AppColors.primary;
  }
}

Color _priorityBackground(String priority) {
  switch (TodoPriority.normalize(priority)) {
    case TodoPriority.high:
      return AppColors.errorContainer;
    case TodoPriority.low:
      return AppColors.surfaceVariant;
    case TodoPriority.normal:
    default:
      return AppColors.primaryContainer;
  }
}

DateTime _dateOnly(DateTime value) {
  return DateTime(value.year, value.month, value.day);
}
