import 'package:sqflite/sqflite.dart';
import 'package:uuid/uuid.dart';

import '../models/todo_item.dart';
import 'app_database.dart';

class TodoRepository {
  TodoRepository(this._appDatabase);

  final AppDatabase _appDatabase;
  final _uuid = const Uuid();

  Database get _db => _appDatabase.database;

  Future<void> initialize() async {
    await _ensureSchema();
    await _seedDefaults();
  }

  Future<List<TodoItem>> getTodos() async {
    final rows = await _db.query(
      'todos',
      orderBy: '''
        is_completed ASC,
        is_starred DESC,
        CASE priority WHEN 'high' THEN 0 WHEN 'normal' THEN 1 ELSE 2 END,
        due_date IS NULL ASC,
        due_date ASC,
        created_at DESC
      ''',
    );
    return rows.map(TodoItem.fromMap).toList();
  }

  Future<TodoItem?> getTodo(String todoId) async {
    final rows = await _db.query(
      'todos',
      where: 'id = ?',
      whereArgs: [todoId],
      limit: 1,
    );
    if (rows.isEmpty) {
      return null;
    }
    return TodoItem.fromMap(rows.first);
  }

  Future<void> createTodo({
    required String title,
    String? notes,
    DateTime? dueDate,
    DateTime? reminderDate,
    String priority = TodoPriority.normal,
    bool isStarred = false,
  }) async {
    final normalizedTitle = title.trim();
    if (normalizedTitle.isEmpty) {
      throw ArgumentError('任务标题不能为空');
    }

    final now = DateTime.now();
    final todo = TodoItem(
      id: _uuid.v4(),
      title: normalizedTitle,
      notes: _blankToNull(notes),
      dueDate: dueDate,
      reminderDate: reminderDate,
      priority: TodoPriority.normalize(priority),
      isStarred: isStarred,
      createdAt: now,
      updatedAt: now,
    );
    await _db.insert('todos', todo.toMap());
  }

  Future<void> updateTodo({
    required String todoId,
    required String title,
    String? notes,
    DateTime? dueDate,
    DateTime? reminderDate,
    required String priority,
    required bool isStarred,
  }) async {
    final normalizedTitle = title.trim();
    if (normalizedTitle.isEmpty) {
      throw ArgumentError('任务标题不能为空');
    }

    await _db.update(
      'todos',
      {
        'title': normalizedTitle,
        'notes': _blankToNull(notes),
        'due_date': _dateText(dueDate),
        'reminder_date': _dateText(reminderDate),
        'priority': TodoPriority.normalize(priority),
        'is_starred': isStarred ? 1 : 0,
        'updated_at': DateTime.now().toIso8601String(),
      },
      where: 'id = ?',
      whereArgs: [todoId],
    );
  }

  Future<void> setTodoCompleted(String todoId, bool isCompleted) async {
    final now = DateTime.now();
    await _db.update(
      'todos',
      {
        'is_completed': isCompleted ? 1 : 0,
        'completed_at': isCompleted ? now.toIso8601String() : null,
        'updated_at': now.toIso8601String(),
      },
      where: 'id = ?',
      whereArgs: [todoId],
    );
  }

  Future<void> setTodoStarred(String todoId, bool isStarred) async {
    await _db.update(
      'todos',
      {
        'is_starred': isStarred ? 1 : 0,
        'updated_at': DateTime.now().toIso8601String(),
      },
      where: 'id = ?',
      whereArgs: [todoId],
    );
  }

  Future<void> deleteTodo(String todoId) async {
    await _db.delete('todos', where: 'id = ?', whereArgs: [todoId]);
  }

  Future<void> _ensureSchema() async {
    await _db.execute('''
      CREATE TABLE IF NOT EXISTS todos (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        notes TEXT,
        due_date TEXT,
        reminder_date TEXT,
        priority TEXT NOT NULL DEFAULT 'normal',
        is_completed INTEGER NOT NULL DEFAULT 0,
        is_starred INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        completed_at TEXT
      )
    ''');
    await _db.execute(
      'CREATE INDEX IF NOT EXISTS idx_todos_completed ON todos(is_completed)',
    );
    await _db.execute(
      'CREATE INDEX IF NOT EXISTS idx_todos_due_date ON todos(due_date)',
    );
    await _db.execute(
      'CREATE INDEX IF NOT EXISTS idx_todos_priority ON todos(priority)',
    );
  }

  Future<void> _seedDefaults() async {
    final count = Sqflite.firstIntValue(
      await _db.rawQuery('SELECT COUNT(*) FROM todos'),
    );
    if ((count ?? 0) > 0) {
      return;
    }

    final now = DateTime.now();
    final today = _dateOnly(now);
    final rows = [
      TodoItem(
        id: 'todo-check-expiring',
        title: '检查临期食材',
        notes: '打开首页的近期提醒，把 3 天内到期的食材优先处理。',
        dueDate: today,
        priority: TodoPriority.high,
        isStarred: true,
        createdAt: now,
        updatedAt: now,
      ),
      TodoItem(
        id: 'todo-plan-shopping',
        title: '补全本周采购清单',
        notes: '根据库存缺口添加需要购买的食品和日用品。',
        dueDate: today.add(const Duration(days: 1)),
        priority: TodoPriority.normal,
        createdAt: now,
        updatedAt: now,
      ),
      TodoItem(
        id: 'todo-clean-fridge',
        title: '整理冷藏区',
        notes: '把同类食材放在一起，并确认开封日期。',
        dueDate: today.add(const Duration(days: 3)),
        priority: TodoPriority.low,
        createdAt: now,
        updatedAt: now,
      ),
    ];

    final batch = _db.batch();
    for (final todo in rows) {
      batch.insert(
        'todos',
        todo.toMap(),
        conflictAlgorithm: ConflictAlgorithm.ignore,
      );
    }
    await batch.commit(noResult: true);
  }
}

DateTime _dateOnly(DateTime value) {
  return DateTime(value.year, value.month, value.day);
}

String? _dateText(DateTime? value) {
  if (value == null) {
    return null;
  }
  return _dateOnly(value).toIso8601String();
}

String? _blankToNull(String? value) {
  final trimmed = value?.trim();
  if (trimmed == null || trimmed.isEmpty) {
    return null;
  }
  return trimmed;
}
