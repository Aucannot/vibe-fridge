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
  }) : super(channel: const MethodChannel('vibe_fridge/fake_notifications'));

  final LocalNotificationPermissionSnapshot requestPermissionResult;
  final LocalNotificationSyncResult syncResult;
  void Function(String itemId)? _onTap;
  int syncCalls = 0;

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
}
