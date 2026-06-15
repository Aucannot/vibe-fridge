import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';

import 'data/app_database.dart';
import 'data/inventory_controller.dart';
import 'data/inventory_repository.dart';
import 'data/todo_controller.dart';
import 'data/todo_repository.dart';
import 'screens/app_shell.dart';
import 'theme/app_theme.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  final database = await AppDatabase.open();
  final repository = InventoryRepository(database);
  final controller = InventoryController(repository);
  final todoRepository = TodoRepository(database);
  final todoController = TodoController(todoRepository);
  await controller.initialize();
  await todoController.initialize();

  runApp(
    VibeFridgeApp(
      controller: controller,
      todoController: todoController,
    ),
  );
}

class VibeFridgeApp extends StatelessWidget {
  const VibeFridgeApp({
    super.key,
    required this.controller,
    required this.todoController,
  });

  final InventoryController controller;
  final TodoController todoController;

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'vibe-fridge',
      theme: AppTheme.light(),
      locale: const Locale('zh', 'CN'),
      supportedLocales: const [
        Locale('zh', 'CN'),
        Locale('en', 'US'),
      ],
      localizationsDelegates: const [
        GlobalMaterialLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
      ],
      home: AppShell(
        controller: controller,
        todoController: todoController,
      ),
    );
  }
}
