import 'package:flutter_test/flutter_test.dart';
import 'package:vibe_fridge/data/local_notification_service.dart';

void main() {
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
}
