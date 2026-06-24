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
      '_normalizeItemId(',
      "arguments is Map ? arguments['itemId'] : null",
    ]);
    _expectAllContains(mainWindow, [
      'FlutterMethodChannel(',
      'name: "vibe_fridge/local_notifications"',
      'case "initialize", "getPermissionStatus":',
      'case "requestPermission":',
      'case "getLaunchItemId":',
      'MacLocalNotificationTapHandler.consumeLaunchItemId()',
      'case "scheduleInventoryReminders":',
      'scheduleInventoryReminders(arguments: call.arguments, result: result)',
      'case "sendTestNotification":',
      'sendTestNotification(result: result)',
      'case "cancelAll":',
      'center.removeAllPendingNotificationRequests()',
      'MacLocalNotificationRequestFactory.requests',
      'MacLocalNotificationScheduler.schedule(',
      'center: center',
      'code: "schedule_failed"',
      'MacDiagnosticNotificationRequestFactory.request()',
      'diagnostic.content()',
      'diagnostic.trigger()',
      'let normalizedItemId = itemId.trimmingCharacters(',
      'guard !normalizedItemId.isEmpty else',
      'arguments: ["itemId": normalizedItemId]',
    ]);
    _expectAllContains(requestFactory, [
      'payload["notifications"] as? [[String: Any]]',
      'row["itemId"] as? String',
      'row["title"] as? String',
      'row["body"] as? String',
      'row["scheduledAtMillis"] as? NSNumber',
      '["itemId": itemId]',
      'content.userInfo = ["itemId": itemId]',
      'func trigger(now: Date = Date())',
      'max(scheduledAt.timeIntervalSince(now), 60)',
      'protocol MacNotificationSchedulingCenter',
      'MacLocalNotificationScheduler',
      'center.removeAllPendingNotificationRequests()',
      'center.add(request)',
      'group.notify(queue: .main)',
      'notification.content()',
      'notification.trigger()',
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
    expect(
      appDelegate,
      isNot(contains('super.applicationDidFinishLaunching(notification)')),
      reason:
          'FlutterAppDelegate does not implement this optional AppKit selector '
          'in the current runtime; calling super raises an NSInvalidArgumentException.',
    );
    _expectAllContains(requestSupport, [
      'static let launchItemIdKey = "notification_item_id"',
      'normalizedItemId(userInfo["itemId"])',
      'userDefaults.set(itemId, forKey: launchItemIdKey)',
      'notificationCenter.post(',
      'name: .vibeFridgeNotificationTapped',
      'userInfo: ["itemId": itemId]',
      'consumeLaunchItemId(',
      'userDefaults.removeObject(forKey: launchItemIdKey)',
      'trimmingCharacters(in: .whitespacesAndNewlines)',
      'normalized.isEmpty ? nil : normalized',
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
