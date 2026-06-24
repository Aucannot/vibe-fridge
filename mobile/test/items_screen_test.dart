import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:vibe_fridge/data/app_database.dart';
import 'package:vibe_fridge/data/inventory_controller.dart';
import 'package:vibe_fridge/data/inventory_repository.dart';
import 'package:vibe_fridge/data/local_notification_service.dart';
import 'package:vibe_fridge/models/shopping_list_item.dart';
import 'package:vibe_fridge/screens/items_screen.dart';
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

  testWidgets('shopping view confirms before converting checked items',
      (tester) async {
    tester.view.physicalSize = const Size(430, 1400);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    final controller = _FakeShoppingController(
      InventoryRepository(appDatabase),
      convertedCount: 1,
      notificationService: _FakeNotificationService(),
    );
    addTearDown(controller.dispose);

    await tester.pumpWidget(
      MaterialApp(
        theme: AppTheme.light(),
        home: Scaffold(
          body: ItemsScreen(controller: controller),
        ),
      ),
    );
    await tester.pump();

    await tester.tap(find.text('采购'));
    await tester.pumpAndSettle();

    expect(find.text('已买到'), findsOneWidget);
    expect(find.text('转换测试牛奶'), findsOneWidget);
    expect(find.text('2盒 · 备注：已经买到'), findsOneWidget);

    final convertButton = find.widgetWithText(FilledButton, '入库');
    expect(convertButton, findsOneWidget);

    await tester.tap(convertButton);
    await tester.pumpAndSettle();

    expect(find.text('采购项入库'), findsOneWidget);
    expect(find.text('确定将 1 个已买到采购项转为库存记录吗？'), findsOneWidget);

    await tester.tap(find.widgetWithText(TextButton, '取消'));
    await tester.pumpAndSettle();

    expect(controller.convertCalls, 0);
    expect(find.text('已入库 1 项'), findsNothing);

    await tester.tap(convertButton);
    await tester.pumpAndSettle();
    await tester.tap(find.widgetWithText(FilledButton, '确认入库'));
    await tester.pumpAndSettle();

    expect(controller.convertCalls, 1);
    expect(find.text('已入库 1 项'), findsOneWidget);
  });
}

class _FakeShoppingController extends InventoryController {
  _FakeShoppingController(
    super.repository, {
    required this.convertedCount,
    required LocalNotificationService notificationService,
  }) : super(notificationService: notificationService) {
    final now = DateTime(2026, 6, 19);
    isLoading = false;
    shoppingListItems = [
      ShoppingListItem(
        id: 'shopping-checked-1',
        name: '转换测试牛奶',
        categoryId: 'cat-food',
        categoryName: '食品',
        quantity: 2,
        unit: '盒',
        note: '已经买到',
        source: 'manual',
        isChecked: true,
        checkedAt: now,
        createdAt: now,
        updatedAt: now,
      ),
    ];
  }

  final int convertedCount;
  int convertCalls = 0;

  @override
  Future<int> convertCheckedShoppingItemsToInventory() async {
    convertCalls += 1;
    return convertedCount;
  }
}

class _FakeNotificationService extends LocalNotificationService {
  _FakeNotificationService()
      : super(channel: const MethodChannel('vibe_fridge/fake_notifications'));

  @override
  void setOnNotificationTap(void Function(String itemId)? handler) {}
}
