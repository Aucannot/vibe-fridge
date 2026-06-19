import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:vibe_fridge/data/app_database.dart';
import 'package:vibe_fridge/data/inventory_controller.dart';
import 'package:vibe_fridge/data/inventory_repository.dart';
import 'package:vibe_fridge/data/local_notification_service.dart';
import 'package:vibe_fridge/data/recipe_preferences_store.dart';
import 'package:vibe_fridge/data/vlm_settings_store.dart';
import 'package:vibe_fridge/screens/settings_screen.dart';
import 'package:vibe_fridge/theme/app_theme.dart';

import 'test_database.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  late AppDatabase appDatabase;

  setUp(() async {
    SharedPreferences.setMockInitialValues({});
    appDatabase = await openTestDatabase();
  });

  tearDown(() async {
    await appDatabase.database.close();
  });

  testWidgets('settings test notification action calls notification service',
      (tester) async {
    tester.view.physicalSize = const Size(430, 1200);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    final notificationService = _FakeNotificationService(
      testResult: const LocalNotificationTestResult(
        permission: LocalNotificationPermissionSnapshot(
          supported: true,
          granted: true,
          status: 'granted',
        ),
        sent: true,
      ),
    );
    final controller = InventoryController(
      InventoryRepository(appDatabase),
      notificationService: notificationService,
    );
    addTearDown(controller.dispose);

    await tester.pumpWidget(
      MaterialApp(
        theme: AppTheme.light(),
        home: Scaffold(
          body: SettingsScreen(
            controller: controller,
            vlmSettingsStore: VlmSettingsStore(
              secretStore: _MemorySecretStore(),
            ),
          ),
        ),
      ),
    );
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 200));

    final button = find.widgetWithText(OutlinedButton, '测试通知');
    expect(button, findsOneWidget);

    await tester.tap(button);
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 200));

    expect(notificationService.testCalls, 1);
    expect(find.text('已发送测试通知'), findsOneWidget);
  });

  testWidgets('settings does not expose app self-check controls',
      (tester) async {
    tester.view.physicalSize = const Size(430, 2200);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    final controller = InventoryController(
      InventoryRepository(appDatabase),
      notificationService: _FakeNotificationService(
        testResult: const LocalNotificationTestResult(
          permission: LocalNotificationPermissionSnapshot(
            supported: true,
            granted: true,
            status: 'granted',
          ),
          sent: true,
        ),
      ),
    );
    addTearDown(controller.dispose);

    await tester.pumpWidget(
      MaterialApp(
        theme: AppTheme.light(),
        home: Scaffold(
          body: SettingsScreen(
            controller: controller,
            vlmSettingsStore: VlmSettingsStore(
              secretStore: _MemorySecretStore(),
            ),
          ),
        ),
      ),
    );
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 200));

    expect(find.text('订单识别 AI'), findsOneWidget);
    expect(find.text('应用自检'), findsNothing);
    expect(find.text('核心闭环'), findsNothing);
    expect(find.widgetWithText(FilledButton, '运行自检'), findsNothing);
  });

  testWidgets('settings shows backup reminder with user-facing copy',
      (tester) async {
    tester.view.physicalSize = const Size(430, 1200);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    final controller = InventoryController(
      InventoryRepository(appDatabase),
      notificationService: _FakeNotificationService(
        testResult: const LocalNotificationTestResult(
          permission: LocalNotificationPermissionSnapshot(
            supported: true,
            granted: true,
            status: 'granted',
          ),
          sent: true,
        ),
      ),
    );
    controller.backupReminderState = const BackupReminderState(
      isPending: true,
      reason: '新增库存',
      dirtyCount: 10,
    );
    addTearDown(controller.dispose);

    await tester.pumpWidget(
      MaterialApp(
        theme: AppTheme.light(),
        home: Scaffold(
          body: SettingsScreen(
            controller: controller,
            vlmSettingsStore: VlmSettingsStore(
              secretStore: _MemorySecretStore(),
            ),
          ),
        ),
      ),
    );
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 200));

    expect(find.text('建议导出备份'), findsOneWidget);
    expect(find.text('因为新增库存，建议备份一次'), findsOneWidget);
    expect(find.text('累计 10 次库存资料变更尚未备份'), findsOneWidget);
    expect(find.widgetWithText(TextButton, '导出'), findsOneWidget);
  });

  testWidgets('settings saves recipe preferences from user inputs',
      (tester) async {
    tester.view.physicalSize = const Size(430, 1700);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    final recipePreferencesStore = RecipePreferencesStore();
    final controller = InventoryController(
      InventoryRepository(appDatabase),
      notificationService: _FakeNotificationService(
        testResult: const LocalNotificationTestResult(
          permission: LocalNotificationPermissionSnapshot(
            supported: true,
            granted: true,
            status: 'granted',
          ),
          sent: true,
        ),
      ),
    );
    addTearDown(controller.dispose);

    await tester.pumpWidget(
      MaterialApp(
        theme: AppTheme.light(),
        home: Scaffold(
          body: SettingsScreen(
            controller: controller,
            recipePreferencesStore: recipePreferencesStore,
            vlmSettingsStore: VlmSettingsStore(
              secretStore: _MemorySecretStore(),
            ),
          ),
        ),
      ),
    );

    final flavorField = _textFieldWithLabel('口味偏好');
    final dietaryField = _textFieldWithLabel('忌口/饮食限制');
    final toolsField = _textFieldWithLabel('可用厨具');
    final minutesField = _textFieldWithLabel('时间');
    final servingsField = _textFieldWithLabel('人数');
    await _pumpUntilFound(
      tester,
      flavorField,
      timeout: const Duration(seconds: 5),
    );

    await tester.enterText(flavorField, ' 清淡内测 ');
    await tester.enterText(dietaryField, ' 不吃辣 ');
    await tester.enterText(toolsField, ' 电饭煲 ');
    await tester.enterText(minutesField, '25');
    await tester.enterText(servingsField, '3');
    await tester.tap(find.widgetWithText(OutlinedButton, '保存食谱偏好'));
    await tester.pumpAndSettle();

    final loaded = await recipePreferencesStore.load();
    final savedFlavorField = tester.widget<TextField>(flavorField);
    final savedDietaryField = tester.widget<TextField>(dietaryField);
    final savedToolsField = tester.widget<TextField>(toolsField);
    final savedMinutesField = tester.widget<TextField>(minutesField);
    final savedServingsField = tester.widget<TextField>(servingsField);

    expect(find.text('食谱偏好已保存'), findsOneWidget);
    expect(loaded.flavorProfile, '清淡内测');
    expect(loaded.dietaryRestrictions, '不吃辣');
    expect(loaded.tools, '电饭煲');
    expect(loaded.cookMinutes, 25);
    expect(loaded.servings, 3);
    expect(savedFlavorField.controller?.text, '清淡内测');
    expect(savedDietaryField.controller?.text, '不吃辣');
    expect(savedToolsField.controller?.text, '电饭煲');
    expect(savedMinutesField.controller?.text, '25');
    expect(savedServingsField.controller?.text, '3');
  });

  testWidgets('settings confirms before resetting demo data', (tester) async {
    tester.view.physicalSize = const Size(430, 1300);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    final controller = _FakeResetDemoController(
      InventoryRepository(appDatabase),
      clearedRows: 9,
      notificationService: _FakeNotificationService(
        testResult: const LocalNotificationTestResult(
          permission: LocalNotificationPermissionSnapshot(
            supported: true,
            granted: true,
            status: 'granted',
          ),
          sent: true,
        ),
      ),
    );
    addTearDown(controller.dispose);

    await tester.pumpWidget(
      MaterialApp(
        theme: AppTheme.light(),
        home: Scaffold(
          body: SettingsScreen(
            controller: controller,
            vlmSettingsStore: VlmSettingsStore(
              secretStore: _MemorySecretStore(),
            ),
          ),
        ),
      ),
    );
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 200));

    final resetButton = find.widgetWithText(OutlinedButton, '重置示例数据');
    expect(resetButton, findsOneWidget);

    await tester.tap(resetButton);
    await tester.pumpAndSettle();

    expect(find.text('重置示例数据'), findsNWidgets(2));
    expect(find.text('仅清理并重建内置示例资料/库存，不会删除用户自己创建的数据。'), findsOneWidget);

    await tester.tap(find.widgetWithText(TextButton, '取消'));
    await tester.pumpAndSettle();

    expect(controller.resetDemoCalls, 0);
    expect(find.text('示例数据已重置，清理 9 条旧示例数据'), findsNothing);

    await tester.tap(resetButton);
    await tester.pumpAndSettle();
    await tester.tap(find.widgetWithText(FilledButton, '重置'));
    await tester.pumpAndSettle();

    expect(controller.resetDemoCalls, 1);
    expect(find.text('示例数据已重置，清理 9 条旧示例数据'), findsOneWidget);
  });

  testWidgets('settings keeps stored order recognition key hidden',
      (tester) async {
    tester.view.physicalSize = const Size(430, 1600);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    final secretStore = _MemorySecretStore();
    final vlmSettingsStore = VlmSettingsStore(secretStore: secretStore);
    await vlmSettingsStore.save(
      const VlmSettings(
        endpoint: 'https://local.test/v1/chat/completions',
        model: 'local-vlm',
        apiKey: 'stored-secret-key',
      ),
    );

    final controller = InventoryController(
      InventoryRepository(appDatabase),
      notificationService: _FakeNotificationService(
        testResult: const LocalNotificationTestResult(
          permission: LocalNotificationPermissionSnapshot(
            supported: true,
            granted: true,
            status: 'granted',
          ),
          sent: true,
        ),
      ),
    );
    addTearDown(controller.dispose);

    await tester.pumpWidget(
      MaterialApp(
        theme: AppTheme.light(),
        home: Scaffold(
          body: SettingsScreen(
            controller: controller,
            vlmSettingsStore: vlmSettingsStore,
          ),
        ),
      ),
    );

    final apiKeyFieldFinder = find.byWidgetPredicate(
      (widget) =>
          widget is TextField && widget.decoration?.labelText == 'API 密钥',
      description: 'API key text field',
    );
    await _pumpUntilFound(
      tester,
      apiKeyFieldFinder,
      timeout: const Duration(seconds: 5),
    );
    await tester.pump();

    final apiKeyField = tester.widget<TextField>(apiKeyFieldFinder);
    expect(apiKeyField.controller?.text, isEmpty);

    expect(find.text('订单识别 AI'), findsOneWidget);
    expect(find.text('已配置'), findsOneWidget);
    expect(find.text('本机安全保存'), findsOneWidget);
    expect(find.text('已安全保存，留空保持不变'), findsOneWidget);
    expect(find.text('已保存的密钥不会明文显示'), findsOneWidget);
    expect(find.text('stored-secret-key'), findsNothing);
  });

  testWidgets('settings clears order recognition config after confirmation',
      (tester) async {
    tester.view.physicalSize = const Size(430, 2200);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    final secretStore = _MemorySecretStore();
    final vlmSettingsStore = VlmSettingsStore(secretStore: secretStore);
    await vlmSettingsStore.save(
      const VlmSettings(
        endpoint: 'https://local.test/v1/chat/completions',
        model: 'local-vlm',
        apiKey: 'stored-secret-key',
      ),
    );

    final controller = InventoryController(
      InventoryRepository(appDatabase),
      notificationService: _FakeNotificationService(
        testResult: const LocalNotificationTestResult(
          permission: LocalNotificationPermissionSnapshot(
            supported: true,
            granted: true,
            status: 'granted',
          ),
          sent: true,
        ),
      ),
    );
    addTearDown(controller.dispose);

    await tester.pumpWidget(
      MaterialApp(
        theme: AppTheme.light(),
        home: Scaffold(
          body: SettingsScreen(
            controller: controller,
            vlmSettingsStore: vlmSettingsStore,
          ),
        ),
      ),
    );

    final clearButton = find.widgetWithIcon(
      IconButton,
      Icons.delete_outline,
    );
    await _pumpUntilFound(
      tester,
      clearButton,
      timeout: const Duration(seconds: 5),
    );
    await tester.ensureVisible(clearButton);
    await tester.tap(clearButton);
    await tester.pumpAndSettle();

    expect(find.text('清空订单识别配置'), findsOneWidget);
    expect(find.text('服务地址、模型名称和已保存的 API 密钥都会被清空。'), findsOneWidget);

    await tester.tap(find.widgetWithText(FilledButton, '清空'));
    await tester.pumpAndSettle();

    final endpointField = tester.widget<TextField>(
      find.byWidgetPredicate(
        (widget) =>
            widget is TextField && widget.decoration?.labelText == '服务地址',
        description: 'endpoint text field',
      ),
    );
    final modelField = tester.widget<TextField>(
      find.byWidgetPredicate(
        (widget) =>
            widget is TextField && widget.decoration?.labelText == '模型名称',
        description: 'model text field',
      ),
    );
    final apiKeyField = tester.widget<TextField>(
      find.byWidgetPredicate(
        (widget) =>
            widget is TextField && widget.decoration?.labelText == 'API 密钥',
        description: 'API key text field',
      ),
    );
    final loaded = await vlmSettingsStore.load();

    expect(endpointField.controller?.text, isEmpty);
    expect(modelField.controller?.text, isEmpty);
    expect(apiKeyField.controller?.text, isEmpty);
    expect(find.text('未配置'), findsOneWidget);
    expect(find.text('订单识别配置已清空'), findsOneWidget);
    expect(find.text('stored-secret-key'), findsNothing);
    expect(loaded.endpoint, isEmpty);
    expect(loaded.model, isEmpty);
    expect(loaded.apiKey, isEmpty);
    expect(loaded.hasStoredApiKey, isFalse);
  });
}

Future<void> _pumpUntilFound(
  WidgetTester tester,
  Finder finder, {
  required Duration timeout,
}) async {
  final stopwatch = Stopwatch()..start();
  while (finder.evaluate().isEmpty && stopwatch.elapsed < timeout) {
    await tester.pump(const Duration(milliseconds: 100));
  }
}

Finder _textFieldWithLabel(String label) {
  return find.byWidgetPredicate(
    (widget) => widget is TextField && widget.decoration?.labelText == label,
    description: '$label text field',
  );
}

class _FakeResetDemoController extends InventoryController {
  _FakeResetDemoController(
    super.repository, {
    required this.clearedRows,
    required LocalNotificationService notificationService,
  }) : super(notificationService: notificationService);

  final int clearedRows;
  int resetDemoCalls = 0;

  @override
  Future<int> resetDemoData() async {
    resetDemoCalls += 1;
    return clearedRows;
  }
}

class _FakeNotificationService extends LocalNotificationService {
  _FakeNotificationService({
    required this.testResult,
  }) : super(channel: const MethodChannel('vibe_fridge/fake_notifications'));

  final LocalNotificationTestResult testResult;
  int testCalls = 0;

  @override
  void setOnNotificationTap(void Function(String itemId)? handler) {}

  @override
  Future<String?> getLaunchItemId() async {
    return null;
  }

  @override
  Future<LocalNotificationSyncResult> syncInventoryReminders(
    InventoryRepository repository, {
    DateTime? now,
  }) async {
    return const LocalNotificationSyncResult(
      permission: LocalNotificationPermissionSnapshot(
        supported: true,
        granted: true,
        status: 'granted',
      ),
      scheduledCount: 0,
    );
  }

  @override
  Future<LocalNotificationTestResult> sendTestNotification() async {
    testCalls += 1;
    return testResult;
  }
}

class _MemorySecretStore implements VlmSecretStore {
  final _values = <String, String>{};

  @override
  Future<String?> read(String key) async {
    return _values[key];
  }

  @override
  Future<void> write(String key, String value) async {
    _values[key] = value;
  }

  @override
  Future<void> delete(String key) async {
    _values.remove(key);
  }
}
