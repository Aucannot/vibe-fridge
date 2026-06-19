import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:vibe_fridge/data/app_database.dart';
import 'package:vibe_fridge/data/inventory_controller.dart';
import 'package:vibe_fridge/data/inventory_repository.dart';
import 'package:vibe_fridge/data/local_notification_service.dart';
import 'package:vibe_fridge/models/inventory_item.dart';
import 'package:vibe_fridge/models/item_status.dart';
import 'package:vibe_fridge/screens/app_shell.dart';
import 'package:vibe_fridge/theme/app_theme.dart';

import 'test_database.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  late AppDatabase appDatabase;

  setUp(() async {
    appDatabase = await openTestDatabase();
  });

  tearDown(() async {
    await appDatabase.database.close();
  });

  testWidgets('material shell smoke renders app chrome', (tester) async {
    await tester.pumpWidget(
      MaterialApp(
        debugShowCheckedModeBanner: false,
        theme: AppTheme.light(),
        home: Scaffold(
          body: const Center(child: Text('vibe-fridge')),
          bottomNavigationBar: NavigationBar(
            destinations: const [
              NavigationDestination(
                icon: Icon(Icons.home_outlined),
                label: '首页',
              ),
              NavigationDestination(
                icon: Icon(Icons.add_circle_outline),
                label: '添加',
              ),
            ],
          ),
        ),
      ),
    );

    expect(find.text('vibe-fridge'), findsOneWidget);
    expect(find.text('首页'), findsOneWidget);
    expect(find.text('添加'), findsOneWidget);
  });

  testWidgets('opens inventory detail when a notification tap is received',
      (tester) async {
    tester.view.physicalSize = const Size(430, 1000);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    final now = DateTime(2026, 6, 19);
    final item = InventoryItem(
      id: 'notification-item-1',
      wikiId: 'notification-wiki-1',
      name: '通知跳转测试牛奶',
      quantity: 3,
      unit: '盒',
      purchaseDate: DateTime(2026, 6, 18),
      expiryDate: DateTime(2026, 6, 25),
      reminderDate: DateTime(2026, 6, 22),
      reminderDaysBefore: 3,
      status: ItemStatus.active,
      isReminderEnabled: true,
      storageLocation: '冷藏',
      createdAt: now,
      updatedAt: now,
    );
    final repository = _FakeItemRepository(appDatabase, item: item);
    final notificationService = _FakeNotificationService();
    final controller = _FakeShellController(
      repository,
      notificationService: notificationService,
      item: item,
    );
    addTearDown(controller.dispose);

    await tester.pumpWidget(
      MaterialApp(
        debugShowCheckedModeBanner: false,
        theme: AppTheme.light(),
        home: AppShell(controller: controller),
      ),
    );
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 300));

    notificationService.tap(item.id);
    await tester.pump();
    await _pumpUntilFound(
      tester,
      find.text('数量操作'),
      timeout: const Duration(seconds: 5),
    );
    await tester.pump();

    expect(find.text('通知跳转测试牛奶'), findsWidgets);
    expect(find.text('数量操作'), findsOneWidget);
    expect(find.text('3 盒'), findsOneWidget);
    expect(find.text('冷藏'), findsWidgets);
  });
}

Future<void> _pumpUntilFound(
  WidgetTester tester,
  Finder finder, {
  required Duration timeout,
}) async {
  final stopwatch = Stopwatch()..start();
  while (finder.evaluate().isEmpty && stopwatch.elapsed < timeout) {
    await tester.pump(const Duration(milliseconds: 100));
  }
}

class _FakeItemRepository extends InventoryRepository {
  _FakeItemRepository(super.appDatabase, {required this.item});

  final InventoryItem item;

  @override
  Future<InventoryItem?> getItem(String itemId) async {
    return itemId == item.id ? item : null;
  }
}

class _FakeShellController extends InventoryController {
  _FakeShellController(
    super.repository, {
    required LocalNotificationService notificationService,
    required InventoryItem item,
  }) : super(notificationService: notificationService) {
    isLoading = false;
    activeItems = [item];
    expiringItems = [item];
    todayActionItems = [item];
  }
}

class _FakeNotificationService extends LocalNotificationService {
  _FakeNotificationService()
      : super(channel: const MethodChannel('vibe_fridge/fake_notifications'));

  void Function(String itemId)? _onTap;

  @override
  void setOnNotificationTap(void Function(String itemId)? handler) {
    _onTap = handler;
  }

  void tap(String itemId) {
    _onTap?.call(itemId);
  }

  @override
  Future<String?> getLaunchItemId() async {
    return null;
  }

  @override
  Future<LocalNotificationSyncResult> syncInventoryReminders(
    InventoryRepository repository, {
    DateTime? now,
  }) async {
    return const LocalNotificationSyncResult(
      permission: LocalNotificationPermissionSnapshot(
        supported: true,
        granted: true,
        status: 'granted',
      ),
      scheduledCount: 0,
    );
  }
}
