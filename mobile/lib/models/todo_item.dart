class TodoPriority {
  const TodoPriority._();

  static const low = 'low';
  static const normal = 'normal';
  static const high = 'high';

  static String normalize(String? value) {
    switch (value) {
      case low:
      case normal:
      case high:
        return value!;
      default:
        return normal;
    }
  }
}

class TodoItem {
  const TodoItem({
    required this.id,
    required this.title,
    this.notes,
    this.dueDate,
    this.reminderDate,
    this.priority = TodoPriority.normal,
    this.isCompleted = false,
    this.isStarred = false,
    required this.createdAt,
    required this.updatedAt,
    this.completedAt,
  });

  final String id;
  final String title;
  final String? notes;
  final DateTime? dueDate;
  final DateTime? reminderDate;
  final String priority;
  final bool isCompleted;
  final bool isStarred;
  final DateTime createdAt;
  final DateTime updatedAt;
  final DateTime? completedAt;

  bool get hasNotes => notes != null && notes!.trim().isNotEmpty;

  bool get isDueToday {
    final due = dueDate;
    if (due == null) {
      return false;
    }
    final today = _dateOnly(DateTime.now());
    return _dateOnly(due) == today;
  }

  bool get isOverdue {
    final due = dueDate;
    if (due == null || isCompleted) {
      return false;
    }
    final today = _dateOnly(DateTime.now());
    return _dateOnly(due).isBefore(today);
  }

  bool get isUpcoming {
    final due = dueDate;
    if (due == null || isCompleted) {
      return false;
    }
    final today = _dateOnly(DateTime.now());
    return _dateOnly(due).isAfter(today);
  }

  TodoItem copyWith({
    String? id,
    String? title,
    String? notes,
    DateTime? dueDate,
    DateTime? reminderDate,
    String? priority,
    bool? isCompleted,
    bool? isStarred,
    DateTime? createdAt,
    DateTime? updatedAt,
    DateTime? completedAt,
  }) {
    return TodoItem(
      id: id ?? this.id,
      title: title ?? this.title,
      notes: notes ?? this.notes,
      dueDate: dueDate ?? this.dueDate,
      reminderDate: reminderDate ?? this.reminderDate,
      priority: priority ?? this.priority,
      isCompleted: isCompleted ?? this.isCompleted,
      isStarred: isStarred ?? this.isStarred,
      createdAt: createdAt ?? this.createdAt,
      updatedAt: updatedAt ?? this.updatedAt,
      completedAt: completedAt ?? this.completedAt,
    );
  }

  Map<String, Object?> toMap() {
    return {
      'id': id,
      'title': title,
      'notes': notes,
      'due_date': _dateText(dueDate),
      'reminder_date': _dateText(reminderDate),
      'priority': TodoPriority.normalize(priority),
      'is_completed': isCompleted ? 1 : 0,
      'is_starred': isStarred ? 1 : 0,
      'created_at': createdAt.toIso8601String(),
      'updated_at': updatedAt.toIso8601String(),
      'completed_at': completedAt?.toIso8601String(),
    };
  }

  static TodoItem fromMap(Map<String, Object?> map) {
    return TodoItem(
      id: map['id'] as String,
      title: map['title'] as String,
      notes: _blankToNull(map['notes'] as String?),
      dueDate: _parseDate(map['due_date']),
      reminderDate: _parseDate(map['reminder_date']),
      priority: TodoPriority.normalize(map['priority'] as String?),
      isCompleted: _boolValue(map['is_completed']),
      isStarred: _boolValue(map['is_starred']),
      createdAt: _parseDate(map['created_at']) ?? DateTime.now(),
      updatedAt: _parseDate(map['updated_at']) ?? DateTime.now(),
      completedAt: _parseDate(map['completed_at']),
    );
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

DateTime? _parseDate(Object? value) {
  if (value is! String || value.trim().isEmpty) {
    return null;
  }
  return DateTime.tryParse(value);
}

String? _blankToNull(String? value) {
  final trimmed = value?.trim();
  if (trimmed == null || trimmed.isEmpty) {
    return null;
  }
  return trimmed;
}

bool _boolValue(Object? value) {
  if (value is bool) {
    return value;
  }
  if (value is int) {
    return value != 0;
  }
  if (value is String) {
    return value != '0' && value.toLowerCase() != 'false';
  }
  return false;
}
