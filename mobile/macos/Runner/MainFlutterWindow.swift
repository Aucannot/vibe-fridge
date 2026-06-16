import Cocoa
import FlutterMacOS
import UserNotifications

class MainFlutterWindow: NSWindow {
  private var notificationBridge: MacLocalNotificationBridge?

  override func awakeFromNib() {
    let flutterViewController = FlutterViewController()
    let windowFrame = self.frame
    self.contentViewController = flutterViewController
    self.setFrame(windowFrame, display: true)
    configureWindow()

    RegisterGeneratedPlugins(registry: flutterViewController)
    notificationBridge = MacLocalNotificationBridge(
      messenger: flutterViewController.engine.binaryMessenger
    )

    super.awakeFromNib()
  }

  private func configureWindow() {
    title = "vibe-fridge"
    minSize = NSSize(width: 390, height: 700)
    titleVisibility = .hidden
    titlebarAppearsTransparent = true
    isMovableByWindowBackground = true
    tabbingMode = .disallowed

    let preferredContentSize = NSSize(width: 430, height: 820)
    if frame.width < preferredContentSize.width ||
        frame.height < preferredContentSize.height {
      var preferredFrame = frameRect(
        forContentRect: NSRect(origin: .zero, size: preferredContentSize)
      )
      preferredFrame.origin = frame.origin
      setFrame(preferredFrame, display: true)
      center()
    }
  }
}

final class MacLocalNotificationBridge {
  private let channel: FlutterMethodChannel
  private let center = UNUserNotificationCenter.current()

  init(messenger: FlutterBinaryMessenger) {
    channel = FlutterMethodChannel(
      name: "vibe_fridge/local_notifications",
      binaryMessenger: messenger
    )
    channel.setMethodCallHandler(handle)
    NotificationCenter.default.addObserver(
      self,
      selector: #selector(notificationTapped(_:)),
      name: .vibeFridgeNotificationTapped,
      object: nil
    )
  }

  deinit {
    NotificationCenter.default.removeObserver(self)
  }

  private func handle(
    call: FlutterMethodCall,
    result: @escaping FlutterResult
  ) {
    switch call.method {
    case "initialize", "getPermissionStatus":
      permissionStatus(result: result)
    case "requestPermission":
      requestPermission(result: result)
    case "getLaunchItemId":
      let itemId = UserDefaults.standard.string(forKey: "notification_item_id")
      UserDefaults.standard.removeObject(forKey: "notification_item_id")
      result(itemId)
    case "scheduleInventoryReminders":
      scheduleInventoryReminders(arguments: call.arguments)
      result(nil)
    case "cancelAll":
      center.removeAllPendingNotificationRequests()
      result(nil)
    default:
      result(FlutterMethodNotImplemented)
    }
  }

  private func permissionStatus(result: @escaping FlutterResult) {
    center.getNotificationSettings { settings in
      DispatchQueue.main.async {
        let granted = settings.authorizationStatus == .authorized ||
          settings.authorizationStatus == .provisional
        result([
          "supported": true,
          "granted": granted,
          "status": self.statusText(settings.authorizationStatus)
        ])
      }
    }
  }

  private func requestPermission(result: @escaping FlutterResult) {
    center.requestAuthorization(options: [.alert, .sound, .badge]) {
      granted,
      _ in
      DispatchQueue.main.async {
        result([
          "supported": true,
          "granted": granted,
          "status": granted ? "granted" : "denied"
        ])
      }
    }
  }

  private func scheduleInventoryReminders(arguments: Any?) {
    center.removeAllPendingNotificationRequests()
    guard let payload = arguments as? [String: Any],
          let notifications = payload["notifications"] as? [[String: Any]]
    else {
      return
    }
    for row in notifications {
      guard let itemId = row["itemId"] as? String,
            let title = row["title"] as? String,
            let body = row["body"] as? String,
            let scheduledAtMillis = row["scheduledAtMillis"] as? NSNumber
      else {
        continue
      }
      let content = UNMutableNotificationContent()
      content.title = title
      content.body = body
      content.sound = .default
      content.userInfo = ["itemId": itemId]

      let scheduledDate = Date(
        timeIntervalSince1970: scheduledAtMillis.doubleValue / 1000
      )
      let interval = max(scheduledDate.timeIntervalSinceNow, 60)
      let trigger = UNTimeIntervalNotificationTrigger(
        timeInterval: interval,
        repeats: false
      )
      let request = UNNotificationRequest(
        identifier: "inventory-\(itemId)",
        content: content,
        trigger: trigger
      )
      center.add(request)
    }
  }

  @objc private func notificationTapped(_ notification: Notification) {
    guard let itemId = notification.userInfo?["itemId"] as? String else {
      return
    }
    channel.invokeMethod("notificationTapped", arguments: ["itemId": itemId])
  }

  private func statusText(
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
