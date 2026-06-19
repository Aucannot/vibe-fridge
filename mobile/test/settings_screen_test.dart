import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:vibe_fridge/data/acceptance_test_service.dart';
import 'package:vibe_fridge/data/app_database.dart';
import 'package:vibe_fridge/data/inventory_controller.dart';
import 'package:vibe_fridge/data/inventory_repository.dart';
import 'package:vibe_fridge/data/local_notification_service.dart';
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

  testWidgets('settings self-check action reports all checks passing',
      (tester) async {
    tester.view.physicalSize = const Size(430, 1400);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    final controller = _FakeAcceptanceController(
      InventoryRepository(appDatabase),
      report: _passingAcceptanceReport(checkCount: 17),
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

    final button = find.widgetWithText(FilledButton, '运行自检');
    expect(button, findsOneWidget);
    await tester.ensureVisible(button);
    await tester.tap(button);

    await _pumpUntilFound(
      tester,
      find.text('应用自检通过：17/17'),
      timeout: const Duration(seconds: 8),
    );
    await tester.pump();

    expect(controller.acceptanceCalls, 1);
    expect(find.text('应用自检通过：17/17'), findsOneWidget);
    expect(find.text('17/17'), findsOneWidget);
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

AcceptanceReport _passingAcceptanceReport({required int checkCount}) {
  final startedAt = DateTime(2026);
  return AcceptanceReport(
    startedAt: startedAt,
    completedAt: startedAt.add(const Duration(milliseconds: 300)),
    checks: [
      for (var index = 0; index < checkCount; index += 1)
        AcceptanceCheckResult.passed(
          name: '自检项目 ${index + 1}',
          duration: const Duration(milliseconds: 1),
        ),
    ],
  );
}

class _FakeAcceptanceController extends InventoryController {
  _FakeAcceptanceController(
    super.repository, {
    required this.report,
    required LocalNotificationService notificationService,
  }) : super(notificationService: notificationService);

  final AcceptanceReport report;
  int acceptanceCalls = 0;

  @override
  Future<AcceptanceReport> runAcceptanceChecks() async {
    acceptanceCalls += 1;
    return report;
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
