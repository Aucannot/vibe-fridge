import '../models/inventory_item.dart';
import '../models/item_status.dart';
import '../models/recipe_suggestion.dart';

class RecipeSuggestionService {
  List<InventoryItem> priorityConsumables(List<InventoryItem> items) {
    final activeFood = items
        .where((item) => item.status == ItemStatus.active)
        .where((item) => _isFoodLike(item))
        .toList();
    activeFood.sort(_comparePriority);
    return activeFood;
  }

  List<RecipeSuggestion> generate(List<InventoryItem> items) {
    final priority = priorityConsumables(items);
    if (priority.isEmpty) {
      return const [];
    }

    final suggestions = <RecipeSuggestion>[];
    _addIfUseful(suggestions, _breakfast(priority));
    _addIfUseful(suggestions, _freshBowl(priority));
    _addIfUseful(suggestions, _stirFry(priority));
    _addIfUseful(suggestions, _warmSoup(priority));
    _addIfUseful(suggestions, _yogurtCup(priority));

    if (suggestions.length < 3) {
      _addIfUseful(suggestions, _cleanOutPlate(priority));
    }
    if (suggestions.length < 3) {
      _addIfUseful(suggestions, _quickHeat(priority));
    }
    if (suggestions.length < 3) {
      _addIfUseful(suggestions, _nextMealPrep(priority));
    }
    return suggestions.take(5).toList();
  }

  RecipeSuggestion? _breakfast(List<InventoryItem> priority) {
    final eggs = _firstMatch(priority, RegExp(r'鸡蛋|蛋'));
    final dairy = _firstMatch(priority, RegExp(r'牛奶|酸奶|奶'));
    final staple = _firstMatch(priority, RegExp(r'面包|吐司|燕麦|麦片|馒头'));
    final uses = _uses([eggs, dairy, staple]);
    if (uses.length < 2) {
      return null;
    }
    return RecipeSuggestion(
      id: 'quick-breakfast',
      title: '快手蛋奶早餐',
      summary: '优先消耗蛋奶和主食，适合早上 15 分钟完成。',
      estimatedMinutes: 15,
      inventoryUses: uses,
      missingIngredients: const ['盐或黑胡椒', '少量油'],
      tags: const ['早餐', '高频'],
      steps: const [
        '先处理最临期的蛋奶或主食。',
        '鸡蛋煎熟或做成蛋液，面包/燕麦加热。',
        '牛奶或酸奶搭配主食，按口味加少量调味。',
      ],
    );
  }

  RecipeSuggestion? _freshBowl(List<InventoryItem> priority) {
    final vegetables = priority
        .where(
          (item) => _matches(
            item,
            RegExp(r'生菜|黄瓜|番茄|西红柿|菠菜|青菜|玉米'),
          ),
        )
        .take(3)
        .toList();
    final protein = _firstMatch(priority, RegExp(r'鸡胸|鸡肉|牛肉|虾|鱼|豆腐|蛋'));
    final uses = _uses([...vegetables, protein]);
    if (uses.length < 2) {
      return null;
    }
    return RecipeSuggestion(
      id: 'fresh-bowl',
      title: '临期清爽拌碗',
      summary: '把快到期的蔬菜和蛋白做成一碗轻食。',
      estimatedMinutes: 20,
      inventoryUses: uses,
      missingIngredients: const ['酱油或油醋汁', '芝麻/坚果可选'],
      tags: const ['轻食', '临期优先'],
      steps: const [
        '蔬菜洗净切块，优先使用最早到期的批次。',
        '蛋白类煎熟、焯熟或切片。',
        '混合后加入酱汁，最后补少量盐或坚果。',
      ],
    );
  }

  RecipeSuggestion? _stirFry(List<InventoryItem> priority) {
    final starch = _firstMatch(priority, RegExp(r'米饭|面|粉|年糕|馒头'));
    final vegetables = priority
        .where((item) => _matches(item, RegExp(r'菜|菇|番茄|土豆|胡萝卜|洋葱')))
        .take(2)
        .toList();
    final protein = _firstMatch(priority, RegExp(r'蛋|鸡|牛|猪|虾|鱼|豆腐'));
    final uses = _uses([starch, ...vegetables, protein]);
    if (uses.length < 2) {
      return null;
    }
    return RecipeSuggestion(
      id: 'clean-out-stir-fry',
      title: '冰箱清空炒饭/炒面',
      summary: '适合处理少量剩余主食和零散蔬菜。',
      estimatedMinutes: 18,
      inventoryUses: uses,
      missingIngredients: const ['葱蒜', '酱油'],
      tags: const ['快手', '清库存'],
      steps: const [
        '把主食打散或焯热，蔬菜切小块。',
        '先炒蛋白和蔬菜，再加入主食。',
        '用酱油和少量盐调味，出锅前确认库存已扣减。',
      ],
    );
  }

  RecipeSuggestion? _warmSoup(List<InventoryItem> priority) {
    final vegetables = priority
        .where(
          (item) => _matches(
            item,
            RegExp(r'番茄|西红柿|土豆|萝卜|蘑菇|青菜|白菜'),
          ),
        )
        .take(3)
        .toList();
    final protein = _firstMatch(priority, RegExp(r'豆腐|鸡|牛|鱼|虾|蛋'));
    final uses = _uses([...vegetables, protein]);
    if (uses.length < 2) {
      return null;
    }
    return RecipeSuggestion(
      id: 'warm-soup',
      title: '暖汤消耗锅',
      summary: '把临期蔬菜做成一锅汤，容错高。',
      estimatedMinutes: 30,
      inventoryUses: uses,
      missingIngredients: const ['盐', '姜片或葱段'],
      tags: const ['晚餐', '温热'],
      steps: const [
        '蔬菜切块，蛋白类切小块或打散。',
        '锅中加水或高汤，先煮耐煮食材。',
        '最后加入叶菜和调味，煮熟即可。',
      ],
    );
  }

  RecipeSuggestion? _yogurtCup(List<InventoryItem> priority) {
    final yogurt = _firstMatch(priority, RegExp(r'酸奶|优格|yogurt'));
    final fruit = priority
        .where((item) => _matches(item, RegExp(r'苹果|香蕉|草莓|蓝莓|橙|葡萄|桃')))
        .take(2)
        .toList();
    final uses = _uses([yogurt, ...fruit]);
    if (uses.length < 2) {
      return null;
    }
    return RecipeSuggestion(
      id: 'yogurt-fruit-cup',
      title: '水果酸奶杯',
      summary: '用低置信度或临期水果做一个免开火甜品。',
      estimatedMinutes: 8,
      inventoryUses: uses,
      missingIngredients: const ['蜂蜜或坚果可选'],
      tags: const ['免开火', '甜品'],
      steps: const [
        '水果洗净切小块。',
        '酸奶打底，依次铺上水果。',
        '可加入蜂蜜或坚果，立即食用。',
      ],
    );
  }

  RecipeSuggestion _cleanOutPlate(List<InventoryItem> priority) {
    final uses = priority.take(3).map((item) {
      return RecipeInventoryUse(item: item);
    }).toList();
    return RecipeSuggestion(
      id: 'priority-clean-out',
      title: '临期优先拼盘',
      summary: '直接围绕最需要处理的食材组合一餐。',
      estimatedMinutes: 15,
      inventoryUses: uses,
      missingIngredients: const ['基础调味料'],
      tags: const ['兜底建议'],
      steps: const [
        '按过期日从近到远处理食材。',
        '能生食的做冷盘，需要加热的煎/炒/煮熟。',
        '完成后点击扣减库存，保持数据同步。',
      ],
    );
  }

  RecipeSuggestion _quickHeat(List<InventoryItem> priority) {
    final uses = priority.skip(1).take(3).map((item) {
      return RecipeInventoryUse(item: item);
    }).toList();
    if (uses.isEmpty) {
      uses.add(RecipeInventoryUse(item: priority.first));
    }
    return RecipeSuggestion(
      id: 'quick-heat-combo',
      title: '快手热炒组合',
      summary: '把临期食材做成一份热菜，适合没有完整菜谱时使用。',
      estimatedMinutes: 18,
      inventoryUses: uses,
      missingIngredients: const ['葱蒜或酱油'],
      tags: const ['兜底建议', '热菜'],
      steps: const [
        '把要消耗的食材切成相近大小。',
        '先处理需要更久加热的食材，再加入易熟食材。',
        '用基础调味收尾，完成后扣减对应库存。',
      ],
    );
  }

  RecipeSuggestion _nextMealPrep(List<InventoryItem> priority) {
    final uses = priority.take(2).map((item) {
      return RecipeInventoryUse(item: item);
    }).toList();
    return RecipeSuggestion(
      id: 'next-meal-prep',
      title: '明日便当预处理',
      summary: '先把最临期的食材处理成明天可直接搭配的一餐。',
      estimatedMinutes: 25,
      inventoryUses: uses,
      missingIngredients: const ['饭/面/主食可选'],
      tags: const ['备餐', '减少浪费'],
      steps: const [
        '优先处理今天或 3 天内到期的食材。',
        '加热成熟后分装，冷藏保存。',
        '明天搭配主食或沙拉食用，并保持库存同步。',
      ],
    );
  }

  List<RecipeInventoryUse> _uses(List<InventoryItem?> items) {
    final seen = <String>{};
    final uses = <RecipeInventoryUse>[];
    for (final item in items) {
      if (item == null || seen.contains(item.id)) {
        continue;
      }
      seen.add(item.id);
      uses.add(RecipeInventoryUse(item: item));
    }
    return uses;
  }

  InventoryItem? _firstMatch(List<InventoryItem> items, RegExp pattern) {
    for (final item in items) {
      if (_matches(item, pattern)) {
        return item;
      }
    }
    return null;
  }

  bool _matches(InventoryItem item, RegExp pattern) {
    return pattern.hasMatch(item.name) ||
        (item.categoryName != null && pattern.hasMatch(item.categoryName!));
  }

  bool _isFoodLike(InventoryItem item) {
    final category = item.categoryName ?? '';
    if (category.contains('药') || category.contains('日用品')) {
      return false;
    }
    return category.isEmpty ||
        category.contains('食品') ||
        category.contains('其他');
  }

  int _comparePriority(InventoryItem a, InventoryItem b) {
    final aDays = a.daysUntilExpiry ?? 9999;
    final bDays = b.daysUntilExpiry ?? 9999;
    final expiryCompare = aDays.compareTo(bDays);
    if (expiryCompare != 0) {
      return expiryCompare;
    }
    final quantityCompare = b.quantity.compareTo(a.quantity);
    if (quantityCompare != 0) {
      return quantityCompare;
    }
    return a.name.compareTo(b.name);
  }

  void _addIfUseful(
    List<RecipeSuggestion> suggestions,
    RecipeSuggestion? suggestion,
  ) {
    if (suggestion == null) {
      return;
    }
    if (suggestions.any((row) => row.id == suggestion.id)) {
      return;
    }
    suggestions.add(suggestion);
  }
}
