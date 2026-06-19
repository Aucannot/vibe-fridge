import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';

import 'inventory_repository.dart';

class LocalNotificationService {
  LocalNotificationService({
    MethodChannel channel = const MethodChannel(
      'vibe_fridge/local_notifications',
    ),
    bool? supportsPlatformNotifications,
  })  : _channel = channel,
        _supportsPlatformNotifications =
            supportsPlatformNotifications ?? !kIsWeb;

  final MethodChannel _channel;
  final bool _supportsPlatformNotifications;
  void Function(String itemId)? _onNotificationTap;

  void setOnNotificationTap(void Function(String itemId)? handler) {
    _onNotificationTap = handler;
    if (!_supportsPlatformNotifications) {
      return;
    }
    _channel.setMethodCallHandler((call) async {
      if (call.method != 'notificationTapped') {
        return null;
      }
      final arguments = call.arguments;
      final itemId = arguments is Map ? arguments['itemId'] as String? : null;
      if (itemId != null && itemId.isNotEmpty) {
        _onNotificationTap?.call(itemId);
      }
      return null;
    });
  }

  Future<LocalNotificationPermissionSnapshot> initialize() async {
    if (!_supportsPlatformNotifications) {
      return LocalNotificationPermissionSnapshot.unsupported;
    }
    return _permissionCall('initialize');
  }

  Future<LocalNotificationPermissionSnapshot> getPermissionStatus() async {
    if (!_supportsPlatformNotifications) {
      return LocalNotificationPermissionSnapshot.unsupported;
    }
    return _permissionCall('getPermissionStatus');
  }

  Future<LocalNotificationPermissionSnapshot> requestPermission() async {
    if (!_supportsPlatformNotifications) {
      return LocalNotificationPermissionSnapshot.unsupported;
    }
    return _permissionCall('requestPermission');
  }

  Future<LocalNotificationTestResult> sendTestNotification() async {
    final permission = await requestPermission();
    if (!permission.supported || !permission.granted) {
      return LocalNotificationTestResult(
        permission: permission,
        sent: false,
        skippedReason: permission.supported ? 'permission' : 'unsupported',
      );
    }

    try {
      await _channel.invokeMethod<void>('sendTestNotification');
      return LocalNotificationTestResult(
        permission: permission,
        sent: true,
      );
    } on MissingPluginException {
      return const LocalNotificationTestResult(
        permission: LocalNotificationPermissionSnapshot.unsupported,
        sent: false,
        skippedReason: 'missing_plugin',
      );
    } on PlatformException catch (error) {
      return LocalNotificationTestResult(
        permission: permission,
        sent: false,
        skippedReason: error.code,
      );
    }
  }

  Future<String?> getLaunchItemId() async {
    if (!_supportsPlatformNotifications) {
      return null;
    }
    try {
      final itemId = await _channel.invokeMethod<String>('getLaunchItemId');
      return itemId == null || itemId.isEmpty ? null : itemId;
    } on MissingPluginException {
      return null;
    } on PlatformException {
      return null;
    }
  }

  Future<LocalNotificationSyncResult> syncInventoryReminders(
    InventoryRepository repository, {
    DateTime? now,
  }) async {
    final permission = await getPermissionStatus();
    if (!permission.supported || !permission.granted) {
      return LocalNotificationSyncResult(
        permission: permission,
        scheduledCount: 0,
        skippedReason: permission.supported ? 'permission' : 'unsupported',
      );
    }

    final reminders = await repository.getPendingReminderNotifications(
      now: now,
    );
    try {
      await _channel.invokeMethod<void>('scheduleInventoryReminders', {
        'notifications': reminders.map((reminder) => reminder.toMap()).toList(),
      });
      return LocalNotificationSyncResult(
        permission: permission,
        scheduledCount: reminders.length,
      );
    } on MissingPluginException {
      return const LocalNotificationSyncResult(
        permission: LocalNotificationPermissionSnapshot.unsupported,
        scheduledCount: 0,
        skippedReason: 'missing_plugin',
      );
    } on PlatformException catch (error) {
      return LocalNotificationSyncResult(
        permission: permission,
        scheduledCount: 0,
        skippedReason: error.code,
      );
    }
  }

  Future<void> cancelAll() async {
    try {
      await _channel.invokeMethod<void>('cancelAll');
    } on MissingPluginException {
      return;
    } on PlatformException {
      return;
    }
  }

  Future<LocalNotificationPermissionSnapshot> _permissionCall(
    String method,
  ) async {
    try {
      final raw = await _channel.invokeMapMethod<String, Object?>(method);
      return LocalNotificationPermissionSnapshot.fromMap(raw);
    } on MissingPluginException {
      return LocalNotificationPermissionSnapshot.unsupported;
    } on PlatformException catch (error) {
      return LocalNotificationPermissionSnapshot(
        supported: true,
        granted: false,
        status: error.code,
      );
    }
  }
}

class LocalNotificationPermissionSnapshot {
  const LocalNotificationPermissionSnapshot({
    required this.supported,
    required this.granted,
    required this.status,
  });

  final bool supported;
  final bool granted;
  final String status;

  static const unsupported = LocalNotificationPermissionSnapshot(
    supported: false,
    granted: false,
    status: 'unsupported',
  );

  static const unknown = LocalNotificationPermissionSnapshot(
    supported: true,
    granted: false,
    status: 'unknown',
  );

  factory LocalNotificationPermissionSnapshot.fromMap(
    Map<String, Object?>? map,
  ) {
    if (map == null) {
      return unknown;
    }
    return LocalNotificationPermissionSnapshot(
      supported: map['supported'] != false,
      granted: map['granted'] == true,
      status: map['status'] as String? ?? 'unknown',
    );
  }

  String get displayText {
    if (!supported) {
      return '当前平台不可用';
    }
    if (granted) {
      return '已允许';
    }
    if (status == 'denied') {
      return '未授权';
    }
    return '未确认';
  }

  String? get availabilityHint {
    if (!supported) {
      return '当前平台暂不支持本地通知，提醒仍会显示在首页「今天要处理」。';
    }
    return null;
  }
}

class LocalNotificationSyncResult {
  const LocalNotificationSyncResult({
    required this.permission,
    required this.scheduledCount,
    this.skippedReason,
  });

  final LocalNotificationPermissionSnapshot permission;
  final int scheduledCount;
  final String? skippedReason;

  String get displayText {
    final reason = skippedReason;
    if (reason == null) {
      return '已同步 $scheduledCount 条提醒';
    }
    if (reason == 'permission') {
      return '通知未授权';
    }
    if (reason == 'unsupported') {
      return '当前平台不可用';
    }
    if (reason == 'missing_plugin') {
      return '当前平台不可用';
    }
    return '同步失败，请稍后重试';
  }
}

class LocalNotificationTestResult {
  const LocalNotificationTestResult({
    required this.permission,
    required this.sent,
    this.skippedReason,
  });

  final LocalNotificationPermissionSnapshot permission;
  final bool sent;
  final String? skippedReason;

  String get displayText {
    if (sent) {
      return '已发送测试通知';
    }
    final reason = skippedReason;
    if (reason == 'permission') {
      return '通知未授权';
    }
    if (reason == 'unsupported' || reason == 'missing_plugin') {
      return '当前平台不可用';
    }
    return '测试通知发送失败，请稍后重试';
  }
}
