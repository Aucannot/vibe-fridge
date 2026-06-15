import 'package:flutter/foundation.dart';

import '../models/todo_item.dart';
import 'todo_repository.dart';

class TodoController extends ChangeNotifier {
  TodoController(this.repository);

  final TodoRepository repository;

  bool isLoading = true;
  String? errorMessage;
  List<TodoItem> todos = [];

  Future<void> initialize() async {
    await repository.initialize();
    await refresh();
  }

  Future<void> refresh() async {
    isLoading = true;
    errorMessage = null;
    notifyListeners();

    try {
      todos = await repository.getTodos();
    } catch (error) {
      errorMessage = error.toString();
    } finally {
      isLoading = false;
      notifyListeners();
    }
  }

  List<TodoItem> get activeTodos =>
      todos.where((todo) => !todo.isCompleted).toList();

  List<TodoItem> get completedTodos =>
      todos.where((todo) => todo.isCompleted).toList();

  List<TodoItem> get todayTodos => activeTodos
      .where((todo) => todo.isOverdue || todo.isDueToday)
      .toList();

  List<TodoItem> get upcomingTodos =>
      activeTodos.where((todo) => todo.isUpcoming).toList();

  int get activeCount => activeTodos.length;
  int get completedCount => completedTodos.length;
  int get todayCount => todayTodos.length;

  Future<void> createTodo({
    required String title,
    String? notes,
    DateTime? dueDate,
    DateTime? reminderDate,
    String priority = TodoPriority.normal,
    bool isStarred = false,
  }) async {
    await repository.createTodo(
      title: title,
      notes: notes,
      dueDate: dueDate,
      reminderDate: reminderDate,
      priority: priority,
      isStarred: isStarred,
    );
    await refresh();
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
    await repository.updateTodo(
      todoId: todoId,
      title: title,
      notes: notes,
      dueDate: dueDate,
      reminderDate: reminderDate,
      priority: priority,
      isStarred: isStarred,
    );
    await refresh();
  }

  Future<void> setTodoCompleted(String todoId, bool isCompleted) async {
    await repository.setTodoCompleted(todoId, isCompleted);
    await refresh();
  }

  Future<void> setTodoStarred(String todoId, bool isStarred) async {
    await repository.setTodoStarred(todoId, isStarred);
    await refresh();
  }

  Future<void> deleteTodo(String todoId) async {
    await repository.deleteTodo(todoId);
    await refresh();
  }
}
