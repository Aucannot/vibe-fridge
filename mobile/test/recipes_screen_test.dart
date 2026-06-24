import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:vibe_fridge/data/app_database.dart';
import 'package:vibe_fridge/data/inventory_controller.dart';
import 'package:vibe_fridge/data/inventory_repository.dart';
import 'package:vibe_fridge/data/local_notification_service.dart';
import 'package:vibe_fridge/models/inventory_item.dart';
import 'package:vibe_fridge/models/recipe_suggestion.dart';

import 'test_database.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  late AppDatabase appDatabase;

  setUp(() async {
    SharedPreferences.setMockInitialValues({});
    appDatabase = await openTestDatabase();
  });

  tearDown(() async {
    await appDatabase.database.close();
  });

  test('recipe cooking deduction updates inventory through controller',
      () async {
    final repository = InventoryRepository(appDatabase);
    await repository.seedDefaults();
    await repository.createItem(
      name: '食谱扣减测试鸡蛋',
      quantity: 3,
      unit: '个',
      expiryDate: DateTime.now().add(const Duration(days: 1)),
    );
    await repository.createItem(
      name: '食谱扣减测试番茄',
      quantity: 2,
      unit: '个',
      expiryDate: DateTime.now().add(const Duration(days: 2)),
    );

    final controller = InventoryController(
      repository,
      notificationService: _FakeNotificationService(),
    );
    addTearDown(controller.dispose);

    final egg = await _activeItem(repository, '食谱扣减测试鸡蛋');
    final tomato = await _activeItem(repository, '食谱扣减测试番茄');
    final suggestion = RecipeSuggestion(
      id: 'recipe-cook-test',
      title: '番茄炒蛋',
      summary: '验证做菜后会扣减库存',
      estimatedMinutes: 12,
      inventoryUses: [
        RecipeInventoryUse(item: egg, quantity: 2),
        RecipeInventoryUse(item: tomato),
      ],
      missingIngredients: const [],
      steps: const ['打散鸡蛋', '炒熟番茄和鸡蛋'],
    );

    for (final use in suggestion.inventoryUses) {
      await controller.updateItemQuantity(use.item.id, -use.quantity);
    }

    final updatedEgg = await repository.getItem(egg.id);
    final updatedTomato = await repository.getItem(tomato.id);
    expect(updatedEgg?.quantity, 1);
    expect(updatedTomato?.quantity, 1);
  });
}

Future<InventoryItem> _activeItem(
  InventoryRepository repository,
  String name,
) async {
  final items = await repository.getActiveItems(limit: 20);
  return items.singleWhere((item) => item.name == name);
}

class _FakeNotificationService extends LocalNotificationService {
  _FakeNotificationService()
      : super(channel: const MethodChannel('vibe_fridge/fake_notifications'));

  @override
  void setOnNotificationTap(void Function(String itemId)? handler) {}

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
