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
        result(
          MacLocalNotificationPermissionFactory
            .snapshot(for: settings.authorizationStatus)
            .channelMap
        )
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
    let notifications = MacLocalNotificationRequestFactory.requests(
      from: arguments
    )
    for notification in notifications {
      let content = UNMutableNotificationContent()
      content.title = notification.title
      content.body = notification.body
      content.sound = .default
      content.userInfo = notification.userInfo

      let trigger = UNTimeIntervalNotificationTrigger(
        timeInterval: notification.triggerInterval(),
        repeats: false
      )
      let request = UNNotificationRequest(
        identifier: notification.identifier,
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

}
