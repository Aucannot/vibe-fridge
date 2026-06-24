import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:vibe_fridge/data/app_database.dart';
import 'package:vibe_fridge/data/inventory_controller.dart';
import 'package:vibe_fridge/data/inventory_repository.dart';
import 'package:vibe_fridge/data/local_notification_service.dart';
import 'package:vibe_fridge/models/item_wiki_category.dart';
import 'package:vibe_fridge/models/order_recognition.dart';
import 'package:vibe_fridge/screens/order_import_review_screen.dart';
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

  testWidgets(
      'review requires confirmation before importing low confidence row',
      (tester) async {
    tester.view.physicalSize = const Size(430, 2400);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    final controller = _FakeOrderImportController(
      InventoryRepository(appDatabase),
      notificationService: _FakeNotificationService(),
    );
    addTearDown(controller.dispose);

    await tester.pumpWidget(
      MaterialApp(
        theme: AppTheme.light(),
        home: OrderImportReviewScreen(
          controller: controller,
          result: _recognizedOrder(),
        ),
      ),
    );
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 200));

    expect(find.text('2/2 已选'), findsOneWidget);
    expect(find.text('1 可入库'), findsOneWidget);
    expect(find.text('1 需要确认'), findsOneWidget);
    expect(find.widgetWithText(FilledButton, '添加 1 个物品'), findsOneWidget);

    await tester.tap(find.widgetWithText(OutlinedButton, '标记已确认'));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 200));

    expect(find.text('2 可入库'), findsOneWidget);
    expect(find.text('1 需要确认'), findsNothing);
    expect(find.widgetWithText(FilledButton, '添加 2 个物品'), findsOneWidget);

    await tester.tap(find.widgetWithText(FilledButton, '添加 2 个物品'));
    await _pumpUntilFound(
      tester,
      find.text('确认批量入库'),
      timeout: const Duration(seconds: 5),
    );
    await tester.pump();

    expect(find.text('确认批量入库'), findsOneWidget);
    expect(find.text('将新增 2 条库存记录。重复跳过 0 条，仍需确认 0 条。'), findsOneWidget);

    await tester.tap(find.widgetWithText(FilledButton, '确认入库'));
    await _pumpUntilFound(
      tester,
      find.text('导入完成'),
      timeout: const Duration(seconds: 5),
    );
    await tester.pump();

    expect(controller.createCalls, 1);
    expect(controller.createdItems.map((item) => item.name), [
      '鲜牛奶',
      '赠品纸巾',
    ]);
    expect(controller.createdItems.map((item) => item.quantity), [2, 1]);
    expect(controller.createdItems.map((item) => item.unit), ['盒', '包']);
    expect(find.text('导入完成'), findsOneWidget);
    expect(find.text('新增'), findsWidgets);
    expect(find.text('2'), findsWidgets);
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

OrderRecognitionResult _recognizedOrder() {
  return OrderRecognitionResult(
    sourceApp: '手动粘贴',
    merchant: '盒马鲜生',
    orderId: 'REVIEW-001',
    purchaseDate: DateTime(2026, 6, 18),
    items: [
      OrderRecognitionItem(
        name: '鲜牛奶',
        quantity: 2,
        unit: '盒',
        categoryName: '食品',
        predictedExpiryDate: DateTime(2026, 6, 25),
        confidence: 0.92,
      ),
      const OrderRecognitionItem(
        name: '赠品纸巾',
        quantity: 1,
        unit: '包',
        categoryName: '日用品',
        notes: '赠品，低置信度，需要确认是否入库',
        confidence: 0.45,
      ),
    ],
  );
}

class _FakeOrderImportController extends InventoryController {
  _FakeOrderImportController(
    super.repository, {
    required LocalNotificationService notificationService,
  }) : super(notificationService: notificationService) {
    final now = DateTime(2026, 1, 1);
    categories = [
      ItemWikiCategory(
        id: 'cat-food',
        name: '食品',
        sortOrder: 1,
        createdAt: now,
        updatedAt: now,
      ),
      ItemWikiCategory(
        id: 'cat-daily',
        name: '日用品',
        sortOrder: 2,
        createdAt: now,
        updatedAt: now,
      ),
    ];
  }

  int duplicateChecks = 0;
  int createCalls = 0;
  List<OrderRecognitionItem> createdItems = const [];

  @override
  Future<List<OrderImportDuplicate>> findOrderImportDuplicates({
    required OrderRecognitionResult result,
    required List<OrderRecognitionItem> items,
  }) async {
    duplicateChecks += 1;
    return const [];
  }

  @override
  Future<OrderImportSummary> createItemsFromOrder({
    required OrderRecognitionResult result,
    required Iterable<OrderRecognitionItem> items,
    String? imagePath,
    int uncheckedCount = 0,
    int duplicateSkippedBeforeImport = 0,
    int needsManualReviewCount = 0,
  }) async {
    createCalls += 1;
    createdItems = items.toList();
    return OrderImportSummary(
      addedCount: createdItems.length,
      uncheckedCount: uncheckedCount,
      duplicateCount: duplicateSkippedBeforeImport,
      needsManualReviewCount: needsManualReviewCount,
    );
  }
}

class _FakeNotificationService extends LocalNotificationService {
  _FakeNotificationService()
      : super(channel: const MethodChannel('vibe_fridge/fake_notifications'));

  @override
  void setOnNotificationTap(void Function(String itemId)? handler) {}
}
