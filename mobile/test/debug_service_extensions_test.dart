import 'package:flutter_test/flutter_test.dart';
import 'package:vibe_fridge/data/debug_service_extensions.dart';
import 'package:vibe_fridge/data/local_notification_service.dart';
import 'package:vibe_fridge/data/vlm_settings_store.dart';

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

  test('secure storage smoke writes reads and deletes a temporary key',
      () async {
    final secretStore = _MemorySecretStore();

    final result = await runDebugSecureStorageSmoke(
      secretStore: secretStore,
      now: DateTime.fromMicrosecondsSinceEpoch(1234),
    );

    expect(result, {
      'wrote': true,
      'readBackMatches': true,
      'deleted': true,
      'keyPrefix': 'debug.secure_storage_smoke',
    });
    expect(secretStore.values, isEmpty);
  });
}

class _MemorySecretStore implements VlmSecretStore {
  final values = <String, String>{};

  @override
  Future<String?> read(String key) async {
    return values[key];
  }

  @override
  Future<void> write(String key, String value) async {
    values[key] = value;
  }

  @override
  Future<void> delete(String key) async {
    values.remove(key);
  }
}
