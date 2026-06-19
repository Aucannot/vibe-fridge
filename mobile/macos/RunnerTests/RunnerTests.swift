import Cocoa
import FlutterMacOS
import Security
import UserNotifications
import XCTest
@testable import vibe_fridge

class RunnerTests: XCTestCase {

  func testNotificationRequestFactoryBuildsInventoryReminderRequest() {
    let scheduledAtMillis: Int64 = 1_782_000_000_000
    let requests = MacLocalNotificationRequestFactory.requests(from: [
      "notifications": [
        [
          "itemId": "item-milk-1",
          "title": "鲜牛奶 今天到期",
          "body": "2盒 · 冷藏 · 打开查看详情",
          "scheduledAtMillis": NSNumber(value: scheduledAtMillis),
        ]
      ]
    ])

    XCTAssertEqual(requests.count, 1)
    let content = requests[0].content()
    XCTAssertEqual(requests[0].itemId, "item-milk-1")
    XCTAssertEqual(requests[0].identifier, "inventory-item-milk-1")
    XCTAssertEqual(requests[0].title, "鲜牛奶 今天到期")
    XCTAssertEqual(requests[0].body, "2盒 · 冷藏 · 打开查看详情")
    XCTAssertEqual(requests[0].userInfo["itemId"], "item-milk-1")
    XCTAssertEqual(content.title, "鲜牛奶 今天到期")
    XCTAssertEqual(content.body, "2盒 · 冷藏 · 打开查看详情")
    XCTAssertEqual(content.userInfo["itemId"] as? String, "item-milk-1")
    XCTAssertNotNil(content.sound)
    XCTAssertEqual(
      requests[0].scheduledAt.timeIntervalSince1970,
      Double(scheduledAtMillis) / 1000,
      accuracy: 0.001
    )
  }

  func testNotificationRequestFactorySkipsMalformedRows() {
    let requests = MacLocalNotificationRequestFactory.requests(from: [
      "notifications": [
        [
          "itemId": "",
          "title": "空 item",
          "body": "无效",
          "scheduledAtMillis": NSNumber(value: 1_782_000_000_000),
        ],
        [
          "itemId": "item-without-time",
          "title": "缺少时间",
          "body": "无效",
        ],
        [
          "itemId": "item-bread-1",
          "title": "面包 2 天后到期",
          "body": "1袋 · 常温 · 打开查看详情",
          "scheduledAtMillis": NSNumber(value: 1_782_000_060_000),
        ],
      ],
    ])

    XCTAssertEqual(requests.count, 1)
    XCTAssertEqual(requests[0].itemId, "item-bread-1")
  }

  func testNotificationTriggerIntervalUsesMinimumDelay() {
    let request = MacLocalNotificationRequest(
      itemId: "item-past",
      title: "已到提醒",
      body: "打开查看详情",
      scheduledAt: Date(timeIntervalSince1970: 1_782_000_000)
    )
    let now = Date(timeIntervalSince1970: 1_782_000_120)

    XCTAssertEqual(request.triggerInterval(now: now), 60, accuracy: 0.001)
  }

  func testNotificationTriggerUsesFutureSchedule() {
    let scheduledAt = Date(timeIntervalSince1970: 1_782_000_300)
    let now = Date(timeIntervalSince1970: 1_782_000_120)
    let request = MacLocalNotificationRequest(
      itemId: "item-future",
      title: "未来提醒",
      body: "打开查看详情",
      scheduledAt: scheduledAt
    )
    let trigger = request.trigger(now: now)

    XCTAssertEqual(trigger.timeInterval, 180, accuracy: 0.001)
    XCTAssertFalse(trigger.repeats)
  }

  func testNotificationSchedulerAddsRequestsBeforeReportingSuccess() {
    let center = FakeNotificationSchedulingCenter()
    let done = expectation(description: "scheduler completion")
    let notifications = [
      MacLocalNotificationRequest(
        itemId: "item-milk-1",
        title: "鲜牛奶 今天到期",
        body: "2盒 · 冷藏 · 打开查看详情",
        scheduledAt: Date().addingTimeInterval(120)
      ),
      MacLocalNotificationRequest(
        itemId: "item-bread-1",
        title: "面包 明天到期",
        body: "1袋 · 常温 · 打开查看详情",
        scheduledAt: Date().addingTimeInterval(180)
      ),
    ]
    var completionError: Error?

    MacLocalNotificationScheduler.schedule(
      notifications,
      center: center
    ) { error in
      completionError = error
      done.fulfill()
    }

    wait(for: [done], timeout: 1)
    XCTAssertNil(completionError)
    XCTAssertEqual(center.removeAllPendingCalls, 1)
    XCTAssertEqual(
      center.addedRequests.map(\.identifier),
      ["inventory-item-milk-1", "inventory-item-bread-1"]
    )
    XCTAssertEqual(
      center.addedRequests[0].content.userInfo["itemId"] as? String,
      "item-milk-1"
    )
  }

  func testNotificationSchedulerReportsSystemAddFailure() {
    let center = FakeNotificationSchedulingCenter()
    let expectedError = NSError(
      domain: "vibe-fridge-tests",
      code: 42,
      userInfo: [NSLocalizedDescriptionKey: "add failed"]
    )
    center.errorsByIdentifier["inventory-item-bread-1"] = expectedError
    let done = expectation(description: "scheduler completion")
    let notifications = [
      MacLocalNotificationRequest(
        itemId: "item-milk-1",
        title: "鲜牛奶 今天到期",
        body: "2盒 · 冷藏 · 打开查看详情",
        scheduledAt: Date().addingTimeInterval(120)
      ),
      MacLocalNotificationRequest(
        itemId: "item-bread-1",
        title: "面包 明天到期",
        body: "1袋 · 常温 · 打开查看详情",
        scheduledAt: Date().addingTimeInterval(180)
      ),
    ]
    var completionError: NSError?

    MacLocalNotificationScheduler.schedule(
      notifications,
      center: center
    ) { error in
      completionError = error as NSError?
      done.fulfill()
    }

    wait(for: [done], timeout: 1)
    XCTAssertEqual(completionError?.domain, expectedError.domain)
    XCTAssertEqual(completionError?.code, expectedError.code)
    XCTAssertEqual(center.removeAllPendingCalls, 1)
    XCTAssertEqual(center.addedRequests.count, 2)
  }

  func testDiagnosticNotificationRequestBuildsImmediateTestNotification() {
    let request = MacDiagnosticNotificationRequestFactory.request(
      id: "test-id"
    )
    let content = request.content()
    let trigger = request.trigger()

    XCTAssertEqual(request.identifier, "diagnostic-test-id")
    XCTAssertEqual(request.title, "库存提醒测试")
    XCTAssertEqual(request.body, "看到这条通知说明本地通知可用")
    XCTAssertEqual(request.triggerInterval, 1, accuracy: 0.001)
    XCTAssertEqual(content.title, "库存提醒测试")
    XCTAssertEqual(content.body, "看到这条通知说明本地通知可用")
    XCTAssertEqual(trigger.timeInterval, 1, accuracy: 0.001)
    XCTAssertFalse(trigger.repeats)
  }

  func testPermissionSnapshotMapsAuthorizationStatusesForChannel() {
    let authorized = MacLocalNotificationPermissionFactory.snapshot(
      for: .authorized
    )
    XCTAssertTrue(authorized.granted)
    XCTAssertEqual(authorized.status, "granted")
    XCTAssertEqual(authorized.channelMap["supported"] as? Bool, true)
    XCTAssertEqual(authorized.channelMap["granted"] as? Bool, true)
    XCTAssertEqual(authorized.channelMap["status"] as? String, "granted")

    let provisional = MacLocalNotificationPermissionFactory.snapshot(
      for: .provisional
    )
    XCTAssertTrue(provisional.granted)
    XCTAssertEqual(provisional.status, "provisional")

    let denied = MacLocalNotificationPermissionFactory.snapshot(for: .denied)
    XCTAssertFalse(denied.granted)
    XCTAssertEqual(denied.status, "denied")

    let unknown = MacLocalNotificationPermissionFactory.snapshot(
      for: .notDetermined
    )
    XCTAssertFalse(unknown.granted)
    XCTAssertEqual(unknown.status, "unknown")
  }

  func testSystemNotificationCenterReportsRunnerPermissionStatus() {
    XCTAssertNotNil(Bundle.main.bundleIdentifier)

    let center = UNUserNotificationCenter.current()
    let done = expectation(description: "system permission status")
    var snapshot: MacLocalNotificationPermissionSnapshot?

    center.getNotificationSettings { settings in
      snapshot = MacLocalNotificationPermissionFactory.snapshot(
        for: settings.authorizationStatus
      )
      done.fulfill()
    }

    wait(for: [done], timeout: 5)
    XCTAssertEqual(snapshot?.channelMap["supported"] as? Bool, true)
    XCTAssertNotNil(snapshot?.status)
  }

  func testAppDelegateRegistersAsNotificationCenterDelegate() {
    let appDelegate = NSApp.delegate as? AppDelegate

    XCTAssertNotNil(appDelegate)
    XCTAssertTrue(
      UNUserNotificationCenter.current().delegate as? AppDelegate ===
        appDelegate
    )
  }

  func testSystemNotificationCenterAcceptsPendingRequestWhenAuthorized()
    throws
  {
    let center = UNUserNotificationCenter.current()
    let settings = notificationSettings(from: center)
    let snapshot = MacLocalNotificationPermissionFactory.snapshot(
      for: settings.authorizationStatus
    )
    guard snapshot.granted else {
      throw XCTSkip(
        "macOS notifications are not authorized for this test host; " +
        "permission, delivery, and click routing still need manual validation."
      )
    }

    let notification = MacLocalNotificationRequest(
      itemId: "system-smoke-\(UUID().uuidString)",
      title: "库存提醒系统测试",
      body: "这条请求用于验证系统是否接受待投递提醒",
      scheduledAt: Date().addingTimeInterval(3600)
    )
    let request = UNNotificationRequest(
      identifier: notification.identifier,
      content: notification.content(),
      trigger: notification.trigger()
    )
    defer {
      center.removePendingNotificationRequests(
        withIdentifiers: [request.identifier]
      )
    }

    let addDone = expectation(description: "system pending request add")
    var addError: Error?
    center.add(request) { error in
      addError = error
      addDone.fulfill()
    }
    wait(for: [addDone], timeout: 5)
    XCTAssertNil(addError)

    let pendingDone = expectation(description: "system pending request lookup")
    var pendingRequest: UNNotificationRequest?
    center.getPendingNotificationRequests { requests in
      pendingRequest = requests.first { candidate in
        candidate.identifier == request.identifier
      }
      pendingDone.fulfill()
    }
    wait(for: [pendingDone], timeout: 5)
    XCTAssertEqual(pendingRequest?.content.title, "库存提醒系统测试")
    XCTAssertEqual(
      pendingRequest?.content.userInfo["itemId"] as? String,
      notification.itemId
    )
  }

  func testNotificationTapHandlerStoresLaunchTargetAndPostsEvent() {
    let suiteName = "com.vibefridge.tests.\(UUID().uuidString)"
    let defaults = UserDefaults(suiteName: suiteName)!
    let center = NotificationCenter()
    let event = expectation(description: "notification tap event")
    var postedItemId: String?
    let observer = center.addObserver(
      forName: .vibeFridgeNotificationTapped,
      object: nil,
      queue: nil
    ) { notification in
      postedItemId = notification.userInfo?["itemId"] as? String
      event.fulfill()
    }
    defer {
      center.removeObserver(observer)
      defaults.removePersistentDomain(forName: suiteName)
    }

    let itemId = MacLocalNotificationTapHandler.handleTap(
      userInfo: ["itemId": " item-milk-1 "],
      userDefaults: defaults,
      notificationCenter: center
    )

    XCTAssertEqual(itemId, "item-milk-1")
    XCTAssertEqual(
      defaults.string(forKey: MacLocalNotificationTapHandler.launchItemIdKey),
      "item-milk-1"
    )
    wait(for: [event], timeout: 1)
    XCTAssertEqual(postedItemId, "item-milk-1")
    XCTAssertEqual(
      MacLocalNotificationTapHandler.consumeLaunchItemId(
        userDefaults: defaults
      ),
      "item-milk-1"
    )
    XCTAssertNil(
      defaults.string(forKey: MacLocalNotificationTapHandler.launchItemIdKey)
    )
  }

  func testNotificationTapHandlerIgnoresMalformedPayloads() {
    let suiteName = "com.vibefridge.tests.\(UUID().uuidString)"
    let defaults = UserDefaults(suiteName: suiteName)!
    let center = NotificationCenter()
    var eventCount = 0
    let observer = center.addObserver(
      forName: .vibeFridgeNotificationTapped,
      object: nil,
      queue: nil
    ) { _ in
      eventCount += 1
    }
    defer {
      center.removeObserver(observer)
      defaults.removePersistentDomain(forName: suiteName)
    }

    XCTAssertNil(
      MacLocalNotificationTapHandler.handleTap(
        userInfo: ["itemId": ""],
        userDefaults: defaults,
        notificationCenter: center
      )
    )
    XCTAssertNil(
      MacLocalNotificationTapHandler.handleTap(
        userInfo: ["itemId": "   "],
        userDefaults: defaults,
        notificationCenter: center
      )
    )
    XCTAssertNil(
      MacLocalNotificationTapHandler.handleTap(
        userInfo: ["itemId": 42],
        userDefaults: defaults,
        notificationCenter: center
      )
    )
    XCTAssertNil(
      defaults.string(forKey: MacLocalNotificationTapHandler.launchItemIdKey)
    )
    XCTAssertEqual(eventCount, 0)
  }

  func testNotificationTapHandlerClearsEmptyStoredLaunchTarget() {
    let suiteName = "com.vibefridge.tests.\(UUID().uuidString)"
    let defaults = UserDefaults(suiteName: suiteName)!
    defer {
      defaults.removePersistentDomain(forName: suiteName)
    }

    defaults.set(
      "   ",
      forKey: MacLocalNotificationTapHandler.launchItemIdKey
    )

    XCTAssertNil(
      MacLocalNotificationTapHandler.consumeLaunchItemId(
        userDefaults: defaults
      )
    )
    XCTAssertNil(
      defaults.string(forKey: MacLocalNotificationTapHandler.launchItemIdKey)
    )

    defaults.set(
      " item-milk-1 ",
      forKey: MacLocalNotificationTapHandler.launchItemIdKey
    )

    XCTAssertEqual(
      MacLocalNotificationTapHandler.consumeLaunchItemId(
        userDefaults: defaults
      ),
      "item-milk-1"
    )
  }

  func testKeychainCanStoreApiSecretWithoutDataProtectionEntitlement() {
    let account = "vlm-api-key-\(UUID().uuidString)"
    var query: [CFString: Any] = [
      kSecClass: kSecClassGenericPassword,
      kSecAttrAccount: account,
      kSecAttrService: "vibe-fridge-tests",
      kSecAttrAccessible: kSecAttrAccessibleWhenUnlocked,
      kSecValueData: Data("secret".utf8),
    ]
    if #available(macOS 10.15, *) {
      query[kSecUseDataProtectionKeychain] = false
    }
    defer {
      SecItemDelete(query as CFDictionary)
    }

    XCTAssertEqual(SecItemAdd(query as CFDictionary, nil), errSecSuccess)

    query.removeValue(forKey: kSecValueData)
    query[kSecReturnData] = true
    var result: AnyObject?
    XCTAssertEqual(
      SecItemCopyMatching(query as CFDictionary, &result),
      errSecSuccess
    )
    XCTAssertEqual(result as? Data, Data("secret".utf8))
    XCTAssertEqual(SecItemDelete(query as CFDictionary), errSecSuccess)
  }

  private func notificationSettings(
    from center: UNUserNotificationCenter
  ) -> UNNotificationSettings {
    let done = expectation(description: "system notification settings")
    var captured: UNNotificationSettings?

    center.getNotificationSettings { settings in
      captured = settings
      done.fulfill()
    }

    wait(for: [done], timeout: 5)
    return captured!
  }

}

private final class FakeNotificationSchedulingCenter:
  MacNotificationSchedulingCenter {
  var removeAllPendingCalls = 0
  var addedRequests: [UNNotificationRequest] = []
  var errorsByIdentifier: [String: Error] = [:]

  func removeAllPendingNotificationRequests() {
    removeAllPendingCalls += 1
  }

  func add(
    _ request: UNNotificationRequest,
    withCompletionHandler completionHandler: (@Sendable (Error?) -> Void)?
  ) {
    addedRequests.append(request)
    completionHandler?(errorsByIdentifier[request.identifier])
  }
}
