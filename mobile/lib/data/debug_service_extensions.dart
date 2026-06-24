import 'dart:convert';
import 'dart:developer' as developer;

import 'package:flutter/foundation.dart';

import 'inventory_controller.dart';
import 'local_notification_service.dart';
import 'vlm_settings_store.dart';

@visibleForTesting
Map<String, Object?> debugNotificationPermissionPayload(
  LocalNotificationPermissionSnapshot permission,
) {
  return {
    'supported': permission.supported,
    'granted': permission.granted,
    'status': permission.status,
    'displayText': permission.displayText,
  };
}

@visibleForTesting
Map<String, Object?> debugNotificationTestPayload(
  LocalNotificationTestResult result,
) {
  return {
    'sent': result.sent,
    'skippedReason': result.skippedReason,
    'displayText': result.displayText,
    'permission': debugNotificationPermissionPayload(result.permission),
  };
}

@visibleForTesting
Future<Map<String, Object?>> runDebugSecureStorageSmoke({
  VlmSecretStore? secretStore,
  DateTime? now,
}) async {
  final store = secretStore ?? FlutterSecureSecretStore();
  final timestamp = (now ?? DateTime.now()).microsecondsSinceEpoch;
  final key = 'debug.secure_storage_smoke.$timestamp';
  final value = 'vibe-fridge-smoke-$timestamp';
  var wrote = false;
  var readBackMatches = false;
  var deleted = false;

  try {
    await store.write(key, value);
    wrote = true;
    readBackMatches = await store.read(key) == value;
  } finally {
    await store.delete(key);
    final afterDelete = await store.read(key);
    deleted = afterDelete == null || afterDelete.isEmpty;
  }
  return {
    'wrote': wrote,
    'readBackMatches': readBackMatches,
    'deleted': deleted,
    'keyPrefix': 'debug.secure_storage_smoke',
  };
}

void registerDebugServiceExtensions(InventoryController controller) {
  if (!kDebugMode) {
    return;
  }
  developer.registerExtension(
    'ext.vibe_fridge.notificationStatus',
    (method, parameters) async {
      final permission =
          await controller.notificationService.getPermissionStatus();
      return developer.ServiceExtensionResponse.result(jsonEncode(
        debugNotificationPermissionPayload(permission),
      ));
    },
  );
  developer.registerExtension(
    'ext.vibe_fridge.notificationTest',
    (method, parameters) async {
      final result =
          await controller.notificationService.sendTestNotification();
      return developer.ServiceExtensionResponse.result(jsonEncode(
        debugNotificationTestPayload(result),
      ));
    },
  );
  developer.registerExtension(
    'ext.vibe_fridge.secureStorageSmoke',
    (method, parameters) async {
      return developer.ServiceExtensionResponse.result(jsonEncode(
        await runDebugSecureStorageSmoke(),
      ));
    },
  );
}
