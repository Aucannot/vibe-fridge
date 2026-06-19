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
import 'package:vibe_fridge/data/webdav_backup_service.dart';
import 'package:vibe_fridge/data/webdav_backup_store.dart';
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
    tester.view.physicalSize = const Size(430, 1700);
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
            webDavBackupSettingsStore: WebDavBackupSettingsStore(
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

    await tester.ensureVisible(button);
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
            webDavBackupSettingsStore: WebDavBackupSettingsStore(
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
            webDavBackupSettingsStore: WebDavBackupSettingsStore(
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

  testWidgets('settings saves WebDAV config without showing stored password',
      (tester) async {
    tester.view.physicalSize = const Size(430, 2400);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    final webDavSettingsStore = WebDavBackupSettingsStore(
      secretStore: _MemorySecretStore(),
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
            vlmSettingsStore: VlmSettingsStore(
              secretStore: _MemorySecretStore(),
            ),
            webDavBackupSettingsStore: webDavSettingsStore,
          ),
        ),
      ),
    );

    final serverUrlField = _textFieldWithLabel('WebDAV 服务地址');
    await _pumpUntilFound(
      tester,
      serverUrlField,
      timeout: const Duration(seconds: 5),
    );
    await tester.enterText(serverUrlField, ' https://dav.example.com/dav ');
    await tester.enterText(_textFieldWithLabel('备份目录'), ' /fridge/backups/ ');
    await tester.enterText(_textFieldWithLabel('用户名'), ' alice ');
    await tester.enterText(_textFieldWithLabel('密码或应用密码'), ' secret ');

    final saveButton = find.widgetWithText(OutlinedButton, '保存配置');
    await tester.ensureVisible(saveButton);
    await tester.tap(saveButton);
    await tester.pumpAndSettle();

    final loaded = await webDavSettingsStore.load();
    final passwordField = tester.widget<TextField>(
      _textFieldWithLabel('密码或应用密码'),
    );

    expect(find.text('WebDAV 配置已保存'), findsOneWidget);
    expect(find.text('本机安全保存'), findsWidgets);
    expect(find.text('secret'), findsNothing);
    expect(passwordField.controller?.text, isEmpty);
    expect(loaded.serverUrl, 'https://dav.example.com/dav');
    expect(loaded.remoteDirectory, 'fridge/backups');
    expect(loaded.username, 'alice');
    expect(loaded.password, 'secret');
  });

  testWidgets('settings uploads backup to WebDAV and marks backup exported',
      (tester) async {
    tester.view.physicalSize = const Size(430, 2400);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    final webDavService = _FakeWebDavBackupService();
    final controller = _FakeBackupController(
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
            webDavBackupSettingsStore: WebDavBackupSettingsStore(
              secretStore: _MemorySecretStore(),
            ),
            webDavBackupService: webDavService,
          ),
        ),
      ),
    );

    final serverUrlField = _textFieldWithLabel('WebDAV 服务地址');
    await _pumpUntilFound(
      tester,
      serverUrlField,
      timeout: const Duration(seconds: 5),
    );
    await tester.enterText(serverUrlField, 'https://dav.example.com/dav');
    await tester.enterText(_textFieldWithLabel('备份目录'), 'fridge/backups');
    await tester.enterText(_textFieldWithLabel('用户名'), 'alice');
    await tester.enterText(_textFieldWithLabel('密码或应用密码'), 'secret');

    final uploadButton = find.widgetWithText(FilledButton, '上传备份');
    await tester.ensureVisible(uploadButton);
    await tester.tap(uploadButton);
    await tester.pumpAndSettle();

    expect(webDavService.uploadCalls, 1);
    expect(controller.exportBackupCalls, 1);
    expect(controller.markBackupExportedCalls, 1);
    expect(webDavService.lastUploadSettings?.serverUrl,
        'https://dav.example.com/dav');
    expect(webDavService.lastUploadSettings?.password, 'secret');
    expect(webDavService.lastBackupJson, contains('"items"'));
    expect(find.text('备份已上传到 WebDAV'), findsOneWidget);
    expect(find.textContaining('最近上传：vibe-fridge-backup-'), findsOneWidget);
  });

  testWidgets('settings restores latest WebDAV backup after confirmation',
      (tester) async {
    tester.view.physicalSize = const Size(430, 2400);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    final webDavService = _FakeWebDavBackupService(
      downloadResult: WebDavBackupDownloadResult(
        fileName: 'vibe-fridge-backup-20260619-120000.json',
        uri: Uri.parse(
          'https://dav.example.com/dav/fridge/backups/vibe-fridge-backup-20260619-120000.json',
        ),
        backupJson: '{"metadata":{"format":"vibe-fridge"},"data":{}}',
      ),
    );
    final controller = _FakeBackupController(
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
            webDavBackupSettingsStore: WebDavBackupSettingsStore(
              secretStore: _MemorySecretStore(),
            ),
            webDavBackupService: webDavService,
          ),
        ),
      ),
    );

    final serverUrlField = _textFieldWithLabel('WebDAV 服务地址');
    await _pumpUntilFound(
      tester,
      serverUrlField,
      timeout: const Duration(seconds: 5),
    );
    await tester.enterText(serverUrlField, 'https://dav.example.com/dav');

    final restoreButton = find.widgetWithText(OutlinedButton, '恢复云备份');
    await tester.ensureVisible(restoreButton);
    await tester.tap(restoreButton);
    await tester.pumpAndSettle();

    expect(webDavService.downloadCalls, 1);
    expect(find.text('恢复云端备份'), findsOneWidget);
    expect(
      find.textContaining('vibe-fridge-backup-20260619-120000.json'),
      findsOneWidget,
    );

    await tester.tap(find.widgetWithText(FilledButton, '恢复'));
    await tester.pumpAndSettle();

    expect(controller.restoreBackupCalls, 1);
    expect(controller.restoredBackup?['metadata'], isA<Map>());
    expect(
      find.text('已从 WebDAV 恢复：vibe-fridge-backup-20260619-120000.json'),
      findsOneWidget,
    );
  });

  testWidgets('settings saves recipe preferences from user inputs',
      (tester) async {
    tester.view.physicalSize = const Size(430, 2300);
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
            webDavBackupSettingsStore: WebDavBackupSettingsStore(
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
    final saveButton = find.widgetWithText(OutlinedButton, '保存食谱偏好');
    await tester.ensureVisible(saveButton);
    await tester.tap(saveButton);
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
            webDavBackupSettingsStore: WebDavBackupSettingsStore(
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
            webDavBackupSettingsStore: WebDavBackupSettingsStore(
              secretStore: _MemorySecretStore(),
            ),
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
    tester.view.physicalSize = const Size(430, 2800);
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
            webDavBackupSettingsStore: WebDavBackupSettingsStore(
              secretStore: _MemorySecretStore(),
            ),
          ),
        ),
      ),
    );

    final clearButton = find.byWidgetPredicate(
      (widget) => widget is IconButton && widget.tooltip == '清空配置',
      description: 'order recognition clear button',
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
    expect(find.text('未配置'), findsWidgets);
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

class _FakeBackupController extends InventoryController {
  _FakeBackupController(
    super.repository, {
    required LocalNotificationService notificationService,
  }) : super(notificationService: notificationService);

  int exportBackupCalls = 0;
  int markBackupExportedCalls = 0;
  int restoreBackupCalls = 0;
  Map<String, dynamic>? restoredBackup;

  @override
  Future<Map<String, dynamic>> exportBackup() async {
    exportBackupCalls += 1;
    return {
      'metadata': {'format': 'vibe-fridge'},
      'data': {
        'items': [
          {'name': 'WebDAV 测试牛奶'},
        ],
      },
    };
  }

  @override
  Future<void> markBackupExported() async {
    markBackupExportedCalls += 1;
  }

  @override
  Future<BackupRestoreResult> restoreBackup(
    Map<String, dynamic> backup, {
    bool replaceExisting = true,
  }) async {
    restoreBackupCalls += 1;
    restoredBackup = backup;
    return const BackupRestoreResult(
      restoredRows: 1,
      preRestoreSnapshotId: 'snapshot-before-webdav-restore',
    );
  }
}

class _FakeWebDavBackupService extends WebDavBackupService {
  _FakeWebDavBackupService({
    WebDavBackupDownloadResult? downloadResult,
  }) : downloadResult = downloadResult ??
            WebDavBackupDownloadResult(
              fileName: 'vibe-fridge-backup-20260619-120000.json',
              uri: Uri.parse(
                'https://dav.example.com/dav/fridge/backups/vibe-fridge-backup-20260619-120000.json',
              ),
              backupJson: '{"metadata":{"format":"vibe-fridge"},"data":{}}',
            );

  final WebDavBackupDownloadResult downloadResult;
  int validateCalls = 0;
  int uploadCalls = 0;
  int downloadCalls = 0;
  WebDavBackupSettings? lastUploadSettings;
  String? lastBackupJson;

  @override
  Future<void> validateConfiguration(WebDavBackupSettings settings) async {
    validateCalls += 1;
  }

  @override
  Future<WebDavBackupUploadResult> uploadBackup({
    required WebDavBackupSettings settings,
    required String fileName,
    required String backupJson,
  }) async {
    uploadCalls += 1;
    lastUploadSettings = settings;
    lastBackupJson = backupJson;
    return WebDavBackupUploadResult(
      fileName: fileName,
      uri: Uri.parse('https://dav.example.com/dav/$fileName'),
    );
  }

  @override
  Future<WebDavBackupDownloadResult> downloadLatestBackup(
    WebDavBackupSettings settings,
  ) async {
    downloadCalls += 1;
    return downloadResult;
  }

  @override
  void close() {}
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
