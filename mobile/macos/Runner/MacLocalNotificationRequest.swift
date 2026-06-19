import Foundation
import UserNotifications

struct MacLocalNotificationRequest {
  let itemId: String
  let title: String
  let body: String
  let scheduledAt: Date

  var identifier: String {
    "inventory-\(itemId)"
  }

  var userInfo: [String: String] {
    ["itemId": itemId]
  }

  func triggerInterval(now: Date = Date()) -> TimeInterval {
    max(scheduledAt.timeIntervalSince(now), 60)
  }
}

struct MacDiagnosticNotificationRequest {
  let identifier: String
  let title: String
  let body: String
  let triggerInterval: TimeInterval

  func content() -> UNMutableNotificationContent {
    let content = UNMutableNotificationContent()
    content.title = title
    content.body = body
    content.sound = .default
    return content
  }

  func trigger() -> UNTimeIntervalNotificationTrigger {
    UNTimeIntervalNotificationTrigger(
      timeInterval: triggerInterval,
      repeats: false
    )
  }
}

enum MacDiagnosticNotificationRequestFactory {
  static func request(
    id: String = UUID().uuidString
  ) -> MacDiagnosticNotificationRequest {
    MacDiagnosticNotificationRequest(
      identifier: "diagnostic-\(id)",
      title: "库存提醒测试",
      body: "看到这条通知说明本地通知可用",
      triggerInterval: 1
    )
  }
}

enum MacLocalNotificationRequestFactory {
  static func requests(from arguments: Any?) -> [MacLocalNotificationRequest] {
    guard let payload = arguments as? [String: Any],
          let notifications = payload["notifications"] as? [[String: Any]]
    else {
      return []
    }

    return notifications.compactMap { row in
      guard let itemId = row["itemId"] as? String,
            !itemId.isEmpty,
            let title = row["title"] as? String,
            let body = row["body"] as? String,
            let scheduledAtMillis = row["scheduledAtMillis"] as? NSNumber
      else {
        return nil
      }

      return MacLocalNotificationRequest(
        itemId: itemId,
        title: title,
        body: body,
        scheduledAt: Date(
          timeIntervalSince1970: scheduledAtMillis.doubleValue / 1000
        )
      )
    }
  }
}

struct MacLocalNotificationPermissionSnapshot {
  let granted: Bool
  let status: String

  var channelMap: [String: Any] {
    [
      "supported": true,
      "granted": granted,
      "status": status,
    ]
  }
}

enum MacLocalNotificationPermissionFactory {
  static func snapshot(
    for status: UNAuthorizationStatus
  ) -> MacLocalNotificationPermissionSnapshot {
    let granted = status == .authorized || status == .provisional
    return MacLocalNotificationPermissionSnapshot(
      granted: granted,
      status: statusText(status)
    )
  }

  private static func statusText(
    _ status: UNAuthorizationStatus
  ) -> String {
    switch status {
    case .authorized:
      return "granted"
    case .denied:
      return "denied"
    case .notDetermined:
      return "unknown"
    case .provisional:
      return "provisional"
    @unknown default:
      return "unknown"
    }
  }
}

enum MacLocalNotificationTapHandler {
  static let launchItemIdKey = "notification_item_id"

  @discardableResult
  static func handleTap(
    userInfo: [AnyHashable: Any],
    userDefaults: UserDefaults = .standard,
    notificationCenter: NotificationCenter = .default
  ) -> String? {
    guard let itemId = userInfo["itemId"] as? String, !itemId.isEmpty else {
      return nil
    }

    userDefaults.set(itemId, forKey: launchItemIdKey)
    notificationCenter.post(
      name: .vibeFridgeNotificationTapped,
      object: nil,
      userInfo: ["itemId": itemId]
    )
    return itemId
  }

  static func consumeLaunchItemId(
    userDefaults: UserDefaults = .standard
  ) -> String? {
    let itemId = userDefaults.string(forKey: launchItemIdKey)
    userDefaults.removeObject(forKey: launchItemIdKey)
    guard let itemId, !itemId.isEmpty else {
      return nil
    }
    return itemId
  }
}
