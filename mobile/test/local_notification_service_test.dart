import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:vibe_fridge/data/local_notification_service.dart';

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
      const LocalNotificationSyncResult(
        permission: granted,
        scheduledCount: 0,
        skippedReason: 'platform_internal_error',
      ).displayText,
      '同步失败，请稍后重试',
    );
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
