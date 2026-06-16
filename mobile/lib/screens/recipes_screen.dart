import 'package:flutter/material.dart';

import '../data/ai_recipe_service.dart';
import '../data/inventory_controller.dart';
import '../data/recipe_preferences_store.dart';
import '../data/recipe_suggestion_service.dart';
import '../data/vlm_settings_store.dart';
import '../models/inventory_item.dart';
import '../models/recipe_suggestion.dart';
import '../theme/app_theme.dart';
import '../utils/date_formatters.dart';
import '../utils/web_route_state.dart';
import '../widgets/app_cards.dart';

class RecipesScreen extends StatefulWidget {
  const RecipesScreen({super.key, required this.controller});

  final InventoryController controller;

  @override
  State<RecipesScreen> createState() => _RecipesScreenState();
}

class _RecipesScreenState extends State<RecipesScreen> {
  final _service = RecipeSuggestionService();
  final _aiService = AiRecipeService();
  final _preferencesStore = RecipePreferencesStore();
  final _vlmSettingsStore = VlmSettingsStore();
  final Set<String> _favoriteIds = {};
  final List<String> _recentIds = [];
  RecipePreferences _preferences = const RecipePreferences();
  List<RecipeSuggestion>? _aiSuggestions;
  String? _aiMessage;
  bool _aiUsedFallback = false;
  bool _generatingAi = false;

  @override
  void initState() {
    super.initState();
    _loadPreferences();
  }

  @override
  void dispose() {
    _aiService.close();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final priority =
        _service.priorityConsumables(widget.controller.activeItems);
    final ruleSuggestions = _service.generate(widget.controller.activeItems);
    final suggestions = _aiSuggestions ?? ruleSuggestions;
    final favoriteSuggestions = suggestions
        .where((suggestion) => _favoriteIds.contains(suggestion.id))
        .toList();
    final recentSuggestions = <RecipeSuggestion>[];
    for (final id in _recentIds) {
      final suggestion = _suggestionById(suggestions, id);
      if (suggestion != null) {
        recentSuggestions.add(suggestion);
      }
    }

    return RefreshIndicator(
      onRefresh: widget.controller.refresh,
      child: ListView(
        padding: AppSpacing.pageListPadding,
        children: [
          const PageHeader(
            title: '食谱',
            subtitle: '优先消耗临期库存，先给出规则建议',
          ),
          PageSection(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                _PriorityConsumables(items: priority.take(6).toList()),
                const SizedBox(height: AppSpacing.fieldGap),
                _AiRecipeCard(
                  preferences: _preferences,
                  generating: _generatingAi,
                  hasAiSuggestions: _aiSuggestions != null,
                  usedFallback: _aiUsedFallback,
                  message: _aiMessage,
                  onGenerate: ruleSuggestions.isEmpty || _generatingAi
                      ? null
                      : _generateAiRecipes,
                  onReset: _aiSuggestions == null || _generatingAi
                      ? null
                      : _resetToRuleSuggestions,
                ),
                const SizedBox(height: AppSpacing.fieldGap),
                if (suggestions.isEmpty)
                  const EmptyState(
                    icon: Icons.restaurant_menu_outlined,
                    title: '还没有可推荐的食材',
                    message: '先添加一些食品库存，'
                        '食谱会优先使用临期物品。',
                  )
                else ...[
                  _RecipeSectionTitle(
                    title: '今日建议',
                    subtitle: '基于当前库存生成 '
                        '${suggestions.length} 个方案',
                  ),
                  const SizedBox(height: AppSpacing.compactPadding),
                  for (final suggestion in suggestions) ...[
                    _RecipeSuggestionCard(
                      suggestion: suggestion,
                      isFavorite: _favoriteIds.contains(suggestion.id),
                      onFavoriteToggle: () => _toggleFavorite(suggestion),
                      onTap: () => _openRecipe(suggestion),
                    ),
                    const SizedBox(height: AppSpacing.compactPadding),
                  ],
                ],
                if (favoriteSuggestions.isNotEmpty) ...[
                  const SizedBox(height: AppSpacing.compactPadding),
                  _RecipeSectionTitle(
                    title: '收藏',
                    subtitle: '${favoriteSuggestions.length} 个常用方案',
                  ),
                  const SizedBox(height: AppSpacing.compactPadding),
                  _CompactRecipeRail(
                    suggestions: favoriteSuggestions,
                    onTap: _openRecipe,
                  ),
                ],
                if (recentSuggestions.isNotEmpty) ...[
                  const SizedBox(height: AppSpacing.fieldGap),
                  const _RecipeSectionTitle(
                    title: '最近生成',
                    subtitle: '刚刚查看过的方案',
                  ),
                  const SizedBox(height: AppSpacing.compactPadding),
                  _CompactRecipeRail(
                    suggestions: recentSuggestions,
                    onTap: _openRecipe,
                  ),
                ],
              ],
            ),
          ),
        ],
      ),
    );
  }

  Future<void> _loadPreferences() async {
    final preferences = await _preferencesStore.load();
    if (!mounted) {
      return;
    }
    setState(() => _preferences = preferences);
  }

  Future<void> _generateAiRecipes() async {
    setState(() {
      _generatingAi = true;
      _aiMessage = null;
    });
    try {
      final settings = await _vlmSettingsStore.load();
      final result = await _aiService.generate(
        items: widget.controller.activeItems,
        preferences: _preferences,
        settings: settings,
      );
      if (!mounted) {
        return;
      }
      setState(() {
        _aiSuggestions = result.suggestions.isEmpty ? null : result.suggestions;
        _aiUsedFallback = result.usedFallback;
        _aiMessage =
            result.message ?? (result.usedFallback ? '已使用规则建议' : 'AI 食谱已生成');
      });
    } finally {
      if (mounted) {
        setState(() => _generatingAi = false);
      }
    }
  }

  void _resetToRuleSuggestions() {
    setState(() {
      _aiSuggestions = null;
      _aiMessage = null;
      _aiUsedFallback = false;
    });
  }

  void _toggleFavorite(RecipeSuggestion suggestion) {
    setState(() {
      if (_favoriteIds.contains(suggestion.id)) {
        _favoriteIds.remove(suggestion.id);
      } else {
        _favoriteIds.add(suggestion.id);
      }
    });
  }

  RecipeSuggestion? _suggestionById(
    List<RecipeSuggestion> suggestions,
    String id,
  ) {
    for (final suggestion in suggestions) {
      if (suggestion.id == id) {
        return suggestion;
      }
    }
    return null;
  }

  Future<void> _openRecipe(RecipeSuggestion suggestion) async {
    setState(() {
      _recentIds
        ..remove(suggestion.id)
        ..insert(0, suggestion.id);
      if (_recentIds.length > 5) {
        _recentIds.removeLast();
      }
    });
    setWebRouteState('/recipes/${suggestion.id}');
    await Navigator.of(context).push<void>(
      MaterialPageRoute(
        settings: RouteSettings(name: '/recipes/${suggestion.id}'),
        builder: (_) => RecipeDetailScreen(
          controller: widget.controller,
          suggestion: suggestion,
          isFavorite: _favoriteIds.contains(suggestion.id),
          onFavoriteToggle: () => _toggleFavorite(suggestion),
        ),
      ),
    );
    setWebRouteState('/recipes', replace: true);
    if (mounted) {
      setState(() {});
    }
  }
}

class RecipeDetailScreen extends StatefulWidget {
  const RecipeDetailScreen({
    super.key,
    required this.controller,
    required this.suggestion,
    required this.isFavorite,
    required this.onFavoriteToggle,
  });

  final InventoryController controller;
  final RecipeSuggestion suggestion;
  final bool isFavorite;
  final VoidCallback onFavoriteToggle;

  @override
  State<RecipeDetailScreen> createState() => _RecipeDetailScreenState();
}

class _RecipeDetailScreenState extends State<RecipeDetailScreen> {
  bool _cooking = false;
  late bool _isFavorite;

  @override
  void initState() {
    super.initState();
    _isFavorite = widget.isFavorite;
  }

  @override
  Widget build(BuildContext context) {
    final suggestion = widget.suggestion;
    return Scaffold(
      appBar: AppBar(
        title: const Text('食谱详情'),
        actions: [
          IconButton(
            tooltip: _isFavorite ? '取消收藏' : '收藏',
            onPressed: () {
              widget.onFavoriteToggle();
              setState(() => _isFavorite = !_isFavorite);
            },
            icon: Icon(_isFavorite ? Icons.favorite : Icons.favorite_border),
          ),
        ],
      ),
      body: ListView(
        padding: AppSpacing.detailListPadding,
        children: [
          ContentWidth(
            child: _RecipeHero(suggestion: suggestion),
          ),
          const SizedBox(height: AppSpacing.fieldGap),
          ContentWidth(
            child: _RecipeInventorySection(suggestion: suggestion),
          ),
          if (suggestion.missingIngredients.isNotEmpty) ...[
            const SizedBox(height: AppSpacing.fieldGap),
            ContentWidth(
              child: _MissingIngredients(items: suggestion.missingIngredients),
            ),
          ],
          const SizedBox(height: AppSpacing.fieldGap),
          ContentWidth(
            child: _RecipeSteps(steps: suggestion.steps),
          ),
          const SizedBox(height: AppSpacing.sectionGap),
          ContentWidth(
            child: SizedBox(
              width: double.infinity,
              child: FilledButton.icon(
                onPressed: _cooking ? null : _cookRecipe,
                icon: _cooking
                    ? const SizedBox(
                        width: 18,
                        height: 18,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Icon(Icons.check_circle_outline),
                label: Text(_cooking ? '扣减中' : '做这道菜并扣减库存'),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Future<void> _cookRecipe() async {
    setState(() => _cooking = true);
    try {
      for (final use in widget.suggestion.inventoryUses) {
        await widget.controller.updateItemQuantity(
          use.item.id,
          -use.quantity,
        );
      }
      if (!mounted) {
        return;
      }
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('库存已扣减')),
      );
      Navigator.of(context).pop();
    } finally {
      if (mounted) {
        setState(() => _cooking = false);
      }
    }
  }
}

class _AiRecipeCard extends StatelessWidget {
  const _AiRecipeCard({
    required this.preferences,
    required this.generating,
    required this.hasAiSuggestions,
    required this.usedFallback,
    required this.onGenerate,
    required this.onReset,
    this.message,
  });

  final RecipePreferences preferences;
  final bool generating;
  final bool hasAiSuggestions;
  final bool usedFallback;
  final VoidCallback? onGenerate;
  final VoidCallback? onReset;
  final String? message;

  @override
  Widget build(BuildContext context) {
    final statusColor = usedFallback ? AppColors.warning : AppColors.primary;
    final statusBackground =
        usedFallback ? AppColors.warningContainer : AppColors.primaryContainer;
    return SectionCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                width: 42,
                height: 42,
                decoration: BoxDecoration(
                  color: AppColors.primaryContainer,
                  borderRadius: BorderRadius.circular(14),
                ),
                child: const Icon(
                  Icons.auto_awesome_outlined,
                  color: AppColors.primary,
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'AI 食谱',
                      style: Theme.of(context).textTheme.titleMedium?.copyWith(
                            color: AppColors.textPrimary,
                            fontWeight: FontWeight.w900,
                          ),
                    ),
                    const SizedBox(height: 3),
                    Text(
                      _preferenceSummary(preferences),
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                            color: AppColors.textSecondary,
                          ),
                    ),
                  ],
                ),
              ),
              if (message != null)
                StatusPill(
                  label: usedFallback ? '规则兜底' : '已生成',
                  color: statusColor,
                  backgroundColor: statusBackground,
                ),
            ],
          ),
          if (message != null) ...[
            const SizedBox(height: 10),
            Text(
              message!,
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: AppColors.textSecondary,
                  ),
            ),
          ],
          const SizedBox(height: 12),
          Row(
            children: [
              Expanded(
                child: FilledButton.icon(
                  onPressed: onGenerate,
                  icon: generating
                      ? const SizedBox(
                          width: 18,
                          height: 18,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Icon(Icons.auto_awesome_outlined),
                  label: Text(generating ? '生成中' : '生成食谱'),
                ),
              ),
              if (hasAiSuggestions) ...[
                const SizedBox(width: 10),
                IconButton.outlined(
                  tooltip: '恢复规则建议',
                  onPressed: onReset,
                  icon: const Icon(Icons.restart_alt_outlined),
                ),
              ],
            ],
          ),
        ],
      ),
    );
  }
}

class _PriorityConsumables extends StatelessWidget {
  const _PriorityConsumables({required this.items});

  final List<InventoryItem> items;

  @override
  Widget build(BuildContext context) {
    return SectionCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _RecipeSectionTitle(
            title: '优先消耗',
            subtitle: items.isEmpty ? '暂无临期食品库存' : '按过期日、数量、分类排序',
          ),
          if (items.isNotEmpty) ...[
            const SizedBox(height: 12),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children:
                  items.map((item) => _InventoryChip(item: item)).toList(),
            ),
          ],
        ],
      ),
    );
  }
}

class _RecipeSuggestionCard extends StatelessWidget {
  const _RecipeSuggestionCard({
    required this.suggestion,
    required this.isFavorite,
    required this.onFavoriteToggle,
    required this.onTap,
  });

  final RecipeSuggestion suggestion;
  final bool isFavorite;
  final VoidCallback onFavoriteToggle;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return SectionCard(
      onTap: onTap,
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 48,
            height: 48,
            decoration: BoxDecoration(
              color: AppColors.warningContainer,
              borderRadius: BorderRadius.circular(16),
            ),
            child: const Icon(
              Icons.restaurant_menu_outlined,
              color: AppColors.warning,
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  suggestion.title,
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        color: AppColors.textPrimary,
                        fontWeight: FontWeight.w900,
                      ),
                ),
                const SizedBox(height: 4),
                Text(
                  suggestion.summary,
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                        color: AppColors.textSecondary,
                      ),
                ),
                const SizedBox(height: 10),
                Wrap(
                  spacing: 8,
                  runSpacing: 8,
                  children: [
                    StatusPill(
                      label: '${suggestion.estimatedMinutes} 分钟',
                      color: AppColors.primary,
                      backgroundColor: AppColors.primaryContainer,
                      icon: Icons.timer_outlined,
                    ),
                    StatusPill(
                      label: '消耗 ${suggestion.inventoryUses.length} 项',
                      color: AppColors.success,
                      backgroundColor: AppColors.successContainer,
                      icon: Icons.kitchen_outlined,
                    ),
                    if (suggestion.expiringUseCount > 0)
                      StatusPill(
                        label: '临期 ${suggestion.expiringUseCount}',
                        color: AppColors.warning,
                        backgroundColor: AppColors.warningContainer,
                        icon: Icons.schedule_outlined,
                      ),
                  ],
                ),
              ],
            ),
          ),
          IconButton(
            tooltip: isFavorite ? '取消收藏' : '收藏',
            onPressed: onFavoriteToggle,
            icon: Icon(isFavorite ? Icons.favorite : Icons.favorite_border),
          ),
        ],
      ),
    );
  }
}

class _RecipeHero extends StatelessWidget {
  const _RecipeHero({required this.suggestion});

  final RecipeSuggestion suggestion;

  @override
  Widget build(BuildContext context) {
    return SectionCard(
      padding: const EdgeInsets.all(18),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            suggestion.title,
            style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                  color: AppColors.textPrimary,
                  fontWeight: FontWeight.w900,
                ),
          ),
          const SizedBox(height: 8),
          Text(
            suggestion.summary,
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  color: AppColors.textSecondary,
                ),
          ),
          const SizedBox(height: 12),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              StatusPill(
                label: '${suggestion.estimatedMinutes} 分钟',
                color: AppColors.primary,
                backgroundColor: AppColors.primaryContainer,
                icon: Icons.timer_outlined,
              ),
              for (final tag in suggestion.tags)
                StatusPill(
                  label: tag,
                  color: AppColors.secondary,
                  backgroundColor: AppColors.secondaryContainer,
                ),
            ],
          ),
        ],
      ),
    );
  }
}

class _RecipeInventorySection extends StatelessWidget {
  const _RecipeInventorySection({required this.suggestion});

  final RecipeSuggestion suggestion;

  @override
  Widget build(BuildContext context) {
    return SectionCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const _RecipeSectionTitle(
            title: '将消耗库存',
            subtitle: '点击完成后会扣减这些批次',
          ),
          const SizedBox(height: 10),
          for (final use in suggestion.inventoryUses) _RecipeUseRow(use: use),
        ],
      ),
    );
  }
}

class _RecipeUseRow extends StatelessWidget {
  const _RecipeUseRow({required this.use});

  final RecipeInventoryUse use;

  @override
  Widget build(BuildContext context) {
    final days = use.item.daysUntilExpiry;
    final expiry = days == null
        ? '无到期日'
        : days < 0
            ? '已过期 ${days.abs()} 天'
            : days == 0
                ? '今天到期'
                : '$days 天后到期';
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Row(
        children: [
          Expanded(
            child: Text(
              use.item.name,
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: AppColors.textPrimary,
                    fontWeight: FontWeight.w800,
                  ),
            ),
          ),
          Text(
            '${use.quantityText} · $expiry',
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: AppColors.textSecondary,
                ),
          ),
        ],
      ),
    );
  }
}

class _MissingIngredients extends StatelessWidget {
  const _MissingIngredients({required this.items});

  final List<String> items;

  @override
  Widget build(BuildContext context) {
    return SectionCard(
      color: AppColors.warningContainer.withValues(alpha: 0.45),
      borderColor: AppColors.warning.withValues(alpha: 0.25),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const _RecipeSectionTitle(
            title: '可能还需要',
            subtitle: '调味料不计入库存扣减',
          ),
          const SizedBox(height: 10),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: items
                .map(
                  (item) => StatusPill(
                    label: item,
                    color: AppColors.warning,
                    backgroundColor: AppColors.surface,
                  ),
                )
                .toList(),
          ),
        ],
      ),
    );
  }
}

class _RecipeSteps extends StatelessWidget {
  const _RecipeSteps({required this.steps});

  final List<String> steps;

  @override
  Widget build(BuildContext context) {
    return SectionCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const _RecipeSectionTitle(
            title: '步骤',
            subtitle: '规则建议，可自行调整',
          ),
          const SizedBox(height: 10),
          for (var index = 0; index < steps.length; index += 1)
            _StepRow(index: index + 1, text: steps[index]),
        ],
      ),
    );
  }
}

class _StepRow extends StatelessWidget {
  const _StepRow({required this.index, required this.text});

  final int index;
  final String text;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 28,
            height: 28,
            alignment: Alignment.center,
            decoration: BoxDecoration(
              color: AppColors.primaryContainer,
              borderRadius: BorderRadius.circular(10),
            ),
            child: Text(
              '$index',
              style: Theme.of(context).textTheme.labelMedium?.copyWith(
                    color: AppColors.primary,
                    fontWeight: FontWeight.w900,
                  ),
            ),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Text(
              text,
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: AppColors.textPrimary,
                    fontWeight: FontWeight.w600,
                  ),
            ),
          ),
        ],
      ),
    );
  }
}

class _CompactRecipeRail extends StatelessWidget {
  const _CompactRecipeRail({required this.suggestions, required this.onTap});

  final List<RecipeSuggestion> suggestions;
  final ValueChanged<RecipeSuggestion> onTap;

  @override
  Widget build(BuildContext context) {
    return Wrap(
      spacing: 8,
      runSpacing: 8,
      children: suggestions
          .map(
            (suggestion) => ActionChip(
              avatar: const Icon(Icons.restaurant_menu_outlined, size: 18),
              label: Text(suggestion.title),
              onPressed: () => onTap(suggestion),
            ),
          )
          .toList(),
    );
  }
}

class _InventoryChip extends StatelessWidget {
  const _InventoryChip({required this.item});

  final InventoryItem item;

  @override
  Widget build(BuildContext context) {
    final expiry = formatDate(item.expiryDate);
    return StatusPill(
      label: '${item.name} · ${item.quantity}${item.unit ?? ''} · $expiry',
      color: item.daysUntilExpiry != null && item.daysUntilExpiry! <= 3
          ? AppColors.warning
          : AppColors.textSecondary,
      backgroundColor:
          item.daysUntilExpiry != null && item.daysUntilExpiry! <= 3
              ? AppColors.warningContainer
              : AppColors.surfaceVariant,
      icon: Icons.kitchen_outlined,
    );
  }
}

class _RecipeSectionTitle extends StatelessWidget {
  const _RecipeSectionTitle({
    required this.title,
    required this.subtitle,
  });

  final String title;
  final String subtitle;

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                title,
                style: Theme.of(context).textTheme.titleMedium?.copyWith(
                      color: AppColors.textPrimary,
                      fontWeight: FontWeight.w900,
                    ),
              ),
              const SizedBox(height: 3),
              Text(
                subtitle,
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: AppColors.textSecondary,
                    ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}

String _preferenceSummary(RecipePreferences preferences) {
  final parts = <String>[
    '${preferences.servings} 人',
    '${preferences.cookMinutes} 分钟内',
  ];
  if (preferences.flavorProfile.trim().isNotEmpty) {
    parts.add(preferences.flavorProfile.trim());
  }
  if (preferences.dietaryRestrictions.trim().isNotEmpty) {
    parts.add(preferences.dietaryRestrictions.trim());
  }
  if (preferences.tools.trim().isNotEmpty) {
    parts.add(preferences.tools.trim());
  }
  return parts.join(' · ');
}
