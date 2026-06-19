import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  test('macOS bridge keeps the Dart local notification channel contract', () {
    final dartService = _read('lib/data/local_notification_service.dart');
    final mainWindow = _read('macos/Runner/MainFlutterWindow.swift');
    final requestFactory = _read(
      'macos/Runner/MacLocalNotificationRequest.swift',
    );

    _expectAllContains(dartService, [
      "'vibe_fridge/local_notifications'",
      "'initialize'",
      "'getPermissionStatus'",
      "'requestPermission'",
      "'getLaunchItemId'",
      "'scheduleInventoryReminders'",
      "'sendTestNotification'",
      "'cancelAll'",
      "'notificationTapped'",
      "'notifications'",
      "arguments['itemId'] as String?",
    ]);
    _expectAllContains(mainWindow, [
      'FlutterMethodChannel(',
      'name: "vibe_fridge/local_notifications"',
      'case "initialize", "getPermissionStatus":',
      'case "requestPermission":',
      'case "getLaunchItemId":',
      'MacLocalNotificationTapHandler.consumeLaunchItemId()',
      'case "scheduleInventoryReminders":',
      'scheduleInventoryReminders(arguments: call.arguments)',
      'case "sendTestNotification":',
      'sendTestNotification(result: result)',
      'case "cancelAll":',
      'center.removeAllPendingNotificationRequests()',
      'MacLocalNotificationRequestFactory.requests',
      'MacDiagnosticNotificationRequestFactory.request()',
      'diagnostic.content()',
      'diagnostic.trigger()',
      'channel.invokeMethod("notificationTapped", arguments: ["itemId": itemId])',
    ]);
    _expectAllContains(requestFactory, [
      'payload["notifications"] as? [[String: Any]]',
      'row["itemId"] as? String',
      'row["title"] as? String',
      'row["body"] as? String',
      'row["scheduledAtMillis"] as? NSNumber',
      '["itemId": itemId]',
      'max(scheduledAt.timeIntervalSince(now), 60)',
      'MacDiagnosticNotificationRequestFactory',
      'identifier: "diagnostic-\\(id)"',
      'title: "库存提醒测试"',
      'body: "看到这条通知说明本地通知可用"',
      'triggerInterval: 1',
    ]);
  });

  test('macOS notification delegate routes taps into the launch target', () {
    final appDelegate = _read('macos/Runner/AppDelegate.swift');
    final requestSupport = _read(
      'macos/Runner/MacLocalNotificationRequest.swift',
    );

    _expectAllContains(appDelegate, [
      'UNUserNotificationCenter.current().delegate = self',
      'UNUserNotificationCenterDelegate',
      'willPresent notification: UNNotification',
      'completionHandler([.banner, .sound])',
      'completionHandler([.alert, .sound])',
      'didReceive response: UNNotificationResponse',
      'MacLocalNotificationTapHandler.handleTap',
      'response.notification.request.content.userInfo',
      'completionHandler()',
      'Notification.Name("vibeFridgeNotificationTapped")',
    ]);
    _expectAllContains(requestSupport, [
      'static let launchItemIdKey = "notification_item_id"',
      'userDefaults.set(itemId, forKey: launchItemIdKey)',
      'notificationCenter.post(',
      'name: .vibeFridgeNotificationTapped',
      'userInfo: ["itemId": itemId]',
      'consumeLaunchItemId(',
      'userDefaults.removeObject(forKey: launchItemIdKey)',
    ]);
  });
}

String _read(String path) => File(path).readAsStringSync();

void _expectAllContains(String source, List<String> expectedValues) {
  for (final expected in expectedValues) {
    expect(source, contains(expected),
        reason: 'Missing source token: $expected');
  }
}
