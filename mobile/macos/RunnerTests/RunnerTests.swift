import Cocoa
import FlutterMacOS
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
    XCTAssertEqual(requests[0].itemId, "item-milk-1")
    XCTAssertEqual(requests[0].identifier, "inventory-item-milk-1")
    XCTAssertEqual(requests[0].title, "鲜牛奶 今天到期")
    XCTAssertEqual(requests[0].body, "2盒 · 冷藏 · 打开查看详情")
    XCTAssertEqual(requests[0].userInfo["itemId"], "item-milk-1")
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

}
