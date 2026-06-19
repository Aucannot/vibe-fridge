import 'dart:convert';
import 'dart:developer' as developer;

import 'package:flutter/foundation.dart';

import 'inventory_controller.dart';
import 'local_notification_service.dart';

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
}
