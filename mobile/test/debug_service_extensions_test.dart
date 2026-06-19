import 'package:flutter_test/flutter_test.dart';
import 'package:vibe_fridge/data/debug_service_extensions.dart';
import 'package:vibe_fridge/data/local_notification_service.dart';

void main() {
  test('notification status debug payload keeps smoke contract stable', () {
    const permission = LocalNotificationPermissionSnapshot(
      supported: true,
      granted: false,
      status: 'unknown',
    );

    expect(debugNotificationPermissionPayload(permission), {
      'supported': true,
      'granted': false,
      'status': 'unknown',
      'displayText': '未确认',
    });
  });

  test('notification test debug payload nests permission details', () {
    const permission = LocalNotificationPermissionSnapshot(
      supported: true,
      granted: false,
      status: 'denied',
    );
    const result = LocalNotificationTestResult(
      permission: permission,
      sent: false,
      skippedReason: 'permission',
    );

    expect(debugNotificationTestPayload(result), {
      'sent': false,
      'skippedReason': 'permission',
      'displayText': '通知未授权',
      'permission': {
        'supported': true,
        'granted': false,
        'status': 'denied',
        'displayText': '未授权',
      },
    });
  });
}
