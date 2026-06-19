import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:vibe_fridge/data/inventory_controller.dart';
import 'package:vibe_fridge/data/inventory_repository.dart';
import 'package:vibe_fridge/data/local_notification_service.dart';

import 'test_database.dart';

void main() {
  const channel = MethodChannel('vibe_fridge/local_notifications_test');

  TestWidgetsFlutterBinding.ensureInitialized();

  tearDown(() {
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(channel, null);
  });

  test('local notification sync result display text stays user friendly', () {
    const granted = LocalNotificationPermissionSnapshot(
      supported: true,
      granted: true,
      status: 'authorized',
    );
    const denied = LocalNotificationPermissionSnapshot(
      supported: true,
      granted: false,
      status: 'denied',
    );

    expect(
      const LocalNotificationSyncResult(
        permission: granted,
        scheduledCount: 3,
      ).displayText,
      '已同步 3 条提醒',
    );
    expect(
      const LocalNotificationSyncResult(
        permission: denied,
        scheduledCount: 0,
        skippedReason: 'permission',
      ).displayText,
      '通知未授权',
    );
    expect(
      const LocalNotificationSyncResult(
        permission: LocalNotificationPermissionSnapshot.unsupported,
        scheduledCount: 0,
        skippedReason: 'unsupported',
      ).displayText,
      '当前平台不可用',
    );
    expect(
      const LocalNotificationSyncResult(
        permission: LocalNotificationPermissionSnapshot.unsupported,
        scheduledCount: 0,
        skippedReason: 'missing_plugin',
      ).displayText,
      '当前平台不可用',
    );
    expect(
      LocalNotificationPermissionSnapshot.unsupported.availabilityHint,
      '当前平台暂不支持本地通知，提醒仍会显示在首页「今天要处理」。',
    );
    expect(granted.availabilityHint, isNull);
    expect(
      const LocalNotificationSyncResult(
        permission: granted,
        scheduledCount: 0,
        skippedReason: 'platform_internal_error',
      ).displayText,
      '同步失败，请稍后重试',
    );
    expect(
      const LocalNotificationTestResult(
        permission: granted,
        sent: true,
      ).displayText,
      '已发送测试通知',
    );
    expect(
      const LocalNotificationTestResult(
        permission: denied,
        sent: false,
        skippedReason: 'permission',
      ).displayText,
      '通知未授权',
    );
    expect(
      const LocalNotificationTestResult(
        permission: LocalNotificationPermissionSnapshot.unsupported,
        sent: false,
        skippedReason: 'unsupported',
      ).displayText,
      '当前平台不可用',
    );
    expect(
      const LocalNotificationTestResult(
        permission: granted,
        sent: false,
        skippedReason: 'platform_internal_error',
      ).displayText,
      '测试通知发送失败，请稍后重试',
    );
  });

  test('permission calls parse platform status snapshots', () async {
    final service = LocalNotificationService(channel: channel);
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(channel, (call) async {
      return switch (call.method) {
        'initialize' => {
            'supported': true,
            'granted': true,
            'status': 'granted',
          },
        'getPermissionStatus' => {
            'supported': true,
            'granted': false,
            'status': 'denied',
          },
        'requestPermission' => {
            'supported': false,
            'granted': false,
            'status': 'unsupported',
          },
        _ => null,
      };
    });

    final initialized = await service.initialize();
    expect(initialized.supported, isTrue);
    expect(initialized.granted, isTrue);
    expect(initialized.displayText, '已允许');

    final status = await service.getPermissionStatus();
    expect(status.supported, isTrue);
    expect(status.granted, isFalse);
    expect(status.displayText, '未授权');

    final requested = await service.requestPermission();
    expect(requested.supported, isFalse);
    expect(requested.granted, isFalse);
    expect(requested.displayText, '当前平台不可用');
  });

  test('permission calls degrade safely when platform throws', () async {
    final service = LocalNotificationService(channel: channel);
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(channel, (call) async {
      throw PlatformException(code: 'permission_check_failed');
    });

    final status = await service.getPermissionStatus();

    expect(status.supported, isTrue);
    expect(status.granted, isFalse);
    expect(status.status, 'permission_check_failed');
    expect(status.displayText, '未确认');
  });

  test('unsupported platform skips notification method channel calls',
      () async {
    final appDatabase = await openTestDatabase();
    addTearDown(() async {
      await appDatabase.database.close();
    });
    final repository = InventoryRepository(appDatabase);
    final calls = <String>[];
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(channel, (call) async {
      calls.add(call.method);
      fail('Unsupported platforms must not call notification channel.');
    });
    final service = LocalNotificationService(
      channel: channel,
      supportsPlatformNotifications: false,
    );

    final initialized = await service.initialize();
    final status = await service.getPermissionStatus();
    final requested = await service.requestPermission();
    final launchItemId = await service.getLaunchItemId();
    final testResult = await service.sendTestNotification();
    final syncResult = await service.syncInventoryReminders(repository);

    expect(initialized, LocalNotificationPermissionSnapshot.unsupported);
    expect(status, LocalNotificationPermissionSnapshot.unsupported);
    expect(requested, LocalNotificationPermissionSnapshot.unsupported);
    expect(launchItemId, isNull);
    expect(testResult.sent, isFalse);
    expect(testResult.skippedReason, 'unsupported');
    expect(syncResult.scheduledCount, 0);
    expect(syncResult.skippedReason, 'unsupported');
    expect(calls, isEmpty);
  });

  test('notification tap callback receives valid item id from platform',
      () async {
    final service = LocalNotificationService(channel: channel);
    final tappedItemIds = <String>[];
    service.setOnNotificationTap(tappedItemIds.add);

    await _sendPlatformCall(
      channel,
      const MethodCall('notificationTapped', {'itemId': 'item-123'}),
    );

    expect(tappedItemIds, ['item-123']);
  });

  test('notification tap callback ignores empty or malformed payloads',
      () async {
    final service = LocalNotificationService(channel: channel);
    final tappedItemIds = <String>[];
    service.setOnNotificationTap(tappedItemIds.add);

    await _sendPlatformCall(
      channel,
      const MethodCall('notificationTapped', {'itemId': ''}),
    );
    await _sendPlatformCall(
      channel,
      const MethodCall('notificationTapped', {'itemId': 42}),
    );
    await _sendPlatformCall(
      channel,
      const MethodCall('notificationTapped'),
    );

    expect(tappedItemIds, isEmpty);
  });

  test('get launch item id degrades safely when platform call fails', () async {
    final service = LocalNotificationService(channel: channel);
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(channel, (call) async {
      throw PlatformException(code: 'platform_unavailable');
    });

    expect(await service.getLaunchItemId(), isNull);
  });

  test('get launch item id returns only non-empty platform targets', () async {
    final service = LocalNotificationService(channel: channel);
    final returnedItemIds = <String?>['item-123', '', null];
    final calls = <String>[];
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(channel, (call) async {
      calls.add(call.method);
      return returnedItemIds.removeAt(0);
    });

    expect(await service.getLaunchItemId(), 'item-123');
    expect(await service.getLaunchItemId(), isNull);
    expect(await service.getLaunchItemId(), isNull);
    expect(calls, [
      'getLaunchItemId',
      'getLaunchItemId',
      'getLaunchItemId',
    ]);
  });

  test('send test notification requests permission before platform call',
      () async {
    final service = LocalNotificationService(channel: channel);
    final calls = <String>[];
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(channel, (call) async {
      calls.add(call.method);
      return switch (call.method) {
        'requestPermission' => {
            'supported': true,
            'granted': true,
            'status': 'granted',
          },
        'sendTestNotification' => null,
        _ => null,
      };
    });

    final result = await service.sendTestNotification();

    expect(result.sent, isTrue);
    expect(result.displayText, '已发送测试通知');
    expect(calls, ['requestPermission', 'sendTestNotification']);
  });

  test('send test notification stops when permission is denied', () async {
    final service = LocalNotificationService(channel: channel);
    final calls = <String>[];
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(channel, (call) async {
      calls.add(call.method);
      return {
        'supported': true,
        'granted': false,
        'status': 'denied',
      };
    });

    final result = await service.sendTestNotification();

    expect(result.sent, isFalse);
    expect(result.displayText, '通知未授权');
    expect(calls, ['requestPermission']);
  });

  test('sync inventory reminders sends pending reminder payload to platform',
      () async {
    final appDatabase = await openTestDatabase();
    addTearDown(() async {
      await appDatabase.database.close();
    });
    final repository = InventoryRepository(appDatabase);
    final service = LocalNotificationService(channel: channel);
    final now = DateTime(2026, 6, 19, 8, 30);

    await repository.createItem(
      name: '平台同步测试酸奶',
      quantity: 3,
      unit: '盒',
      purchaseDate: now.subtract(const Duration(days: 1)),
      expiryDate: DateTime(2026, 6, 21),
      storageLocation: '冷藏',
      reminderDaysBefore: 2,
    );

    final calls = <String>[];
    Object? scheduleArguments;
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(channel, (call) async {
      calls.add(call.method);
      return switch (call.method) {
        'getPermissionStatus' => {
            'supported': true,
            'granted': true,
            'status': 'granted',
          },
        'scheduleInventoryReminders' => scheduleArguments = call.arguments,
        _ => null,
      };
    });

    final result = await service.syncInventoryReminders(
      repository,
      now: now,
    );

    expect(result.scheduledCount, 1);
    expect(result.displayText, '已同步 1 条提醒');
    expect(calls, ['getPermissionStatus', 'scheduleInventoryReminders']);

    final payload = scheduleArguments as Map<Object?, Object?>;
    final notifications = payload['notifications'] as List<Object?>;
    final notification = notifications.single as Map<Object?, Object?>;
    expect(notification['title'], contains('平台同步测试酸奶'));
    expect(notification['body'], '3盒 · 冷藏 · 打开查看详情');
    expect(
      notification['scheduledAtMillis'],
      DateTime(2026, 6, 19, 9).millisecondsSinceEpoch,
    );
  });

  test('sync inventory reminders skips platform schedule when denied',
      () async {
    final appDatabase = await openTestDatabase();
    addTearDown(() async {
      await appDatabase.database.close();
    });
    final repository = InventoryRepository(appDatabase);
    final service = LocalNotificationService(channel: channel);
    final now = DateTime(2026, 6, 19, 8, 30);

    await repository.createItem(
      name: '未授权同步测试酸奶',
      quantity: 1,
      unit: '盒',
      purchaseDate: now.subtract(const Duration(days: 1)),
      expiryDate: DateTime(2026, 6, 21),
      reminderDaysBefore: 2,
    );

    final calls = <String>[];
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(channel, (call) async {
      calls.add(call.method);
      if (call.method == 'scheduleInventoryReminders') {
        fail('Denied notification permission must not schedule reminders.');
      }
      return {
        'supported': true,
        'granted': false,
        'status': 'denied',
      };
    });

    final result = await service.syncInventoryReminders(
      repository,
      now: now,
    );

    expect(result.scheduledCount, 0);
    expect(result.skippedReason, 'permission');
    expect(result.displayText, '通知未授权');
    expect(calls, ['getPermissionStatus']);
  });

  test('sync inventory reminders reports platform schedule failure', () async {
    final appDatabase = await openTestDatabase();
    addTearDown(() async {
      await appDatabase.database.close();
    });
    final repository = InventoryRepository(appDatabase);
    final service = LocalNotificationService(channel: channel);
    final now = DateTime(2026, 6, 19, 8, 30);

    await repository.createItem(
      name: '调度失败测试酸奶',
      quantity: 1,
      unit: '盒',
      purchaseDate: now.subtract(const Duration(days: 1)),
      expiryDate: DateTime(2026, 6, 21),
      reminderDaysBefore: 2,
    );

    final calls = <String>[];
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(channel, (call) async {
      calls.add(call.method);
      if (call.method == 'scheduleInventoryReminders') {
        throw PlatformException(code: 'schedule_failed');
      }
      return {
        'supported': true,
        'granted': true,
        'status': 'granted',
      };
    });

    final result = await service.syncInventoryReminders(
      repository,
      now: now,
    );

    expect(result.scheduledCount, 0);
    expect(result.skippedReason, 'schedule_failed');
    expect(result.displayText, '同步失败，请稍后重试');
    expect(calls, ['getPermissionStatus', 'scheduleInventoryReminders']);
  });

  test('inventory controller consumes notification tap target once', () async {
    final appDatabase = await openTestDatabase();
    addTearDown(() async {
      await appDatabase.database.close();
    });

    final notificationService = _FakeNotificationService();
    final controller = InventoryController(
      InventoryRepository(appDatabase),
      notificationService: notificationService,
    );
    addTearDown(controller.dispose);

    notificationService.tap('item-123');

    expect(controller.consumeNotificationTappedItemId(), 'item-123');
    expect(controller.consumeNotificationTappedItemId(), isNull);
  });

  test('inventory controller syncs reminders after permission is granted',
      () async {
    final appDatabase = await openTestDatabase();
    addTearDown(() async {
      await appDatabase.database.close();
    });

    final notificationService = _FakeNotificationService(
      requestPermissionResult: const LocalNotificationPermissionSnapshot(
        supported: true,
        granted: true,
        status: 'granted',
      ),
      syncResult: const LocalNotificationSyncResult(
        permission: LocalNotificationPermissionSnapshot(
          supported: true,
          granted: true,
          status: 'granted',
        ),
        scheduledCount: 2,
      ),
    );
    final controller = InventoryController(
      InventoryRepository(appDatabase),
      notificationService: notificationService,
    );
    addTearDown(controller.dispose);

    final permission = await controller.requestNotificationPermission();

    expect(permission.granted, isTrue);
    expect(notificationService.syncCalls, 1);
    expect(controller.lastNotificationSyncResult?.scheduledCount, 2);
  });

  test('inventory controller skips sync when permission is denied', () async {
    final appDatabase = await openTestDatabase();
    addTearDown(() async {
      await appDatabase.database.close();
    });

    final notificationService = _FakeNotificationService(
      requestPermissionResult: const LocalNotificationPermissionSnapshot(
        supported: true,
        granted: false,
        status: 'denied',
      ),
    );
    final controller = InventoryController(
      InventoryRepository(appDatabase),
      notificationService: notificationService,
    );
    addTearDown(controller.dispose);

    final permission = await controller.requestNotificationPermission();

    expect(permission.granted, isFalse);
    expect(notificationService.syncCalls, 0);
    expect(controller.lastNotificationSyncResult, isNull);
  });

  test('inventory controller updates permission after test notification',
      () async {
    final appDatabase = await openTestDatabase();
    addTearDown(() async {
      await appDatabase.database.close();
    });

    const permission = LocalNotificationPermissionSnapshot(
      supported: true,
      granted: true,
      status: 'granted',
    );
    final notificationService = _FakeNotificationService(
      testResult: const LocalNotificationTestResult(
        permission: permission,
        sent: true,
      ),
    );
    final controller = InventoryController(
      InventoryRepository(appDatabase),
      notificationService: notificationService,
    );
    addTearDown(controller.dispose);

    final result = await controller.sendTestNotification();

    expect(result.sent, isTrue);
    expect(notificationService.testCalls, 1);
    expect(controller.notificationPermission, permission);
  });
}

Future<void> _sendPlatformCall(MethodChannel channel, MethodCall call) async {
  final messenger =
      TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger;
  final encodedCall = channel.codec.encodeMethodCall(call);
  await messenger.handlePlatformMessage(
    channel.name,
    encodedCall,
    (ByteData? data) {},
  );
}

class _FakeNotificationService extends LocalNotificationService {
  _FakeNotificationService({
    this.requestPermissionResult =
        LocalNotificationPermissionSnapshot.unsupported,
    this.syncResult = const LocalNotificationSyncResult(
      permission: LocalNotificationPermissionSnapshot.unsupported,
      scheduledCount: 0,
      skippedReason: 'unsupported',
    ),
    this.testResult = const LocalNotificationTestResult(
      permission: LocalNotificationPermissionSnapshot.unsupported,
      sent: false,
      skippedReason: 'unsupported',
    ),
  }) : super(channel: const MethodChannel('vibe_fridge/fake_notifications'));

  final LocalNotificationPermissionSnapshot requestPermissionResult;
  final LocalNotificationSyncResult syncResult;
  final LocalNotificationTestResult testResult;
  void Function(String itemId)? _onTap;
  int syncCalls = 0;
  int testCalls = 0;

  @override
  void setOnNotificationTap(void Function(String itemId)? handler) {
    _onTap = handler;
  }

  void tap(String itemId) {
    _onTap?.call(itemId);
  }

  @override
  Future<LocalNotificationPermissionSnapshot> requestPermission() async {
    return requestPermissionResult;
  }

  @override
  Future<LocalNotificationSyncResult> syncInventoryReminders(
    InventoryRepository repository, {
    DateTime? now,
  }) async {
    syncCalls += 1;
    return syncResult;
  }

  @override
  Future<LocalNotificationTestResult> sendTestNotification() async {
    testCalls += 1;
    return testResult;
  }
}
