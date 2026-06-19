import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  test('Android manifest keeps local notification platform wiring', () {
    final manifest = _read('android/app/src/main/AndroidManifest.xml');

    _expectAllContains(manifest, [
      'android.permission.POST_NOTIFICATIONS',
      'android.permission.RECEIVE_BOOT_COMPLETED',
      'android.intent.action.BOOT_COMPLETED',
      'android.intent.action.MY_PACKAGE_REPLACED',
    ]);
    expect(
      _containsElementWithAttributes(manifest, 'receiver', [
        'android:name=".ReminderNotificationReceiver"',
        'android:exported="false"',
      ]),
      isTrue,
    );
    expect(
      _containsElementWithAttributes(manifest, 'receiver', [
        'android:name=".ReminderBootReceiver"',
        'android:enabled="true"',
        'android:exported="true"',
      ]),
      isTrue,
    );
    expect(
      _containsElementWithAttributes(manifest, 'activity', [
        'android:name=".MainActivity"',
        'android:launchMode="singleTop"',
      ]),
      isTrue,
    );
  });

  test('Android native notification code matches Dart channel contract', () {
    final dartService = _read('lib/data/local_notification_service.dart');
    final contract = _read(
      'android/app/src/main/kotlin/com/vibefridge/vibe_fridge/'
      'LocalNotificationContract.kt',
    );
    final activity = _read(
      'android/app/src/main/kotlin/com/vibefridge/vibe_fridge/MainActivity.kt',
    );
    final scheduler = _read(
      'android/app/src/main/kotlin/com/vibefridge/vibe_fridge/'
      'LocalReminderScheduler.kt',
    );
    final notificationReceiver = _read(
      'android/app/src/main/kotlin/com/vibefridge/vibe_fridge/'
      'ReminderNotificationReceiver.kt',
    );
    final bootReceiver = _read(
      'android/app/src/main/kotlin/com/vibefridge/vibe_fridge/'
      'ReminderBootReceiver.kt',
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
    _expectAllContains(contract, [
      'const val channelName = "vibe_fridge/local_notifications"',
      'const val prefsName = "vibe_fridge_notifications"',
      'const val scheduledItemIdsKey = "scheduled_item_ids"',
      'const val scheduledNotificationsKey = "scheduled_notifications"',
      'const val testNotificationRequestCode = 4818',
      'const val extraItemId = "item_id"',
      'fun requestCodeFor(itemId: String): Int',
    ]);
    _expectAllContains(activity, [
      'LocalNotificationContract.channelName',
      '"initialize" -> result.success(permissionStatus())',
      '"getPermissionStatus" -> result.success(permissionStatus())',
      '"requestPermission" -> requestNotificationPermission(result)',
      '"getLaunchItemId" -> {',
      '"scheduleInventoryReminders" -> {',
      'LocalReminderScheduler.scheduleFromChannel',
      '"sendTestNotification" -> sendTestNotification(result)',
      '"cancelAll" -> {',
      'LocalReminderScheduler.cancelScheduledReminders(this)',
      'intent.getStringExtra(LocalNotificationContract.extraItemId)',
      '"notificationTapped"',
      'mapOf("itemId" to itemId)',
      'Manifest.permission.POST_NOTIFICATIONS',
      'setContentTitle("库存提醒测试")',
      'LocalNotificationContract.testNotificationRequestCode',
    ]);
    _expectAllContains(scheduler, [
      'fun restoreScheduledReminders(context: Context)',
      'scheduleRows(context, loadRows(context))',
      'Intent(context, ReminderNotificationReceiver::class.java)',
      'LocalNotificationContract.extraItemId',
      'PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE',
      'alarmManager.set(AlarmManager.RTC_WAKEUP, triggerAt, pendingIntent)',
      'LocalNotificationContract.scheduledItemIdsKey',
      'LocalNotificationContract.scheduledNotificationsKey',
      'row["itemId"] as? String',
      'row["scheduledAtMillis"] as? Number',
      'itemId.isBlank() || scheduledAtMillis <= 0L',
    ]);
    _expectAllContains(notificationReceiver, [
      'intent.getStringExtra(LocalNotificationContract.extraItemId)',
      'itemId.isBlank()',
      'hasNotificationPermission(context)',
      'Manifest.permission.POST_NOTIFICATIONS',
      'PackageManager.PERMISSION_GRANTED',
      'Intent(context, MainActivity::class.java)',
      'putExtra(LocalNotificationContract.extraItemId, itemId)',
      'setContentIntent(pendingIntent)',
      'setAutoCancel(true)',
      'catch (ignored: SecurityException)',
      'notificationManager.notify',
    ]);
    _expectAllContains(bootReceiver, [
      'Intent.ACTION_BOOT_COMPLETED',
      'Intent.ACTION_MY_PACKAGE_REPLACED',
      'LocalReminderScheduler.restoreScheduledReminders(context)',
    ]);
  });

  test('Android native notification code rejects malformed reminder ids', () {
    final scheduler = _read(
      'android/app/src/main/kotlin/com/vibefridge/vibe_fridge/'
      'LocalReminderScheduler.kt',
    );
    final notificationReceiver = _read(
      'android/app/src/main/kotlin/com/vibefridge/vibe_fridge/'
      'ReminderNotificationReceiver.kt',
    );

    expect(
      RegExp(
        r'if\s*\(\s*itemId\.isBlank\(\)\s*\|\|\s*scheduledAtMillis\s*<=\s*0L\s*\)\s*\{\s*return@mapNotNull null\s*\}',
        multiLine: true,
      ).hasMatch(scheduler),
      isTrue,
    );
    expect(
      RegExp(
        r'if\s*\(\s*itemId\.isBlank\(\)\s*\)\s*\{\s*return\s*\}',
        multiLine: true,
      ).hasMatch(notificationReceiver),
      isTrue,
    );
  });
}

String _read(String path) => File(path).readAsStringSync();

void _expectAllContains(String source, List<String> expectedValues) {
  for (final expected in expectedValues) {
    expect(source, contains(expected),
        reason: 'Missing source token: $expected');
  }
}

bool _containsElementWithAttributes(
  String source,
  String elementName,
  List<String> attributes,
) {
  final elementPattern = RegExp('<$elementName\\b[^>]*>', dotAll: true);
  return elementPattern
      .allMatches(source)
      .map((match) => match.group(0)!)
      .any((element) => attributes.every(element.contains));
}
