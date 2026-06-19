import 'package:flutter/material.dart';
import '../data/inventory_controller.dart';
import '../models/inventory_item.dart';
import '../models/inventory_stats.dart';
import '../theme/app_theme.dart';
import '../utils/web_route_state.dart';
import '../widgets/app_cards.dart';
import '../widgets/icon_mapper.dart';
import 'item_detail_screen.dart';
import 'items_screen.dart';

class HomeScreen extends StatelessWidget {
  const HomeScreen({
    super.key,
    required this.controller,
    required this.onAddPressed,
    required this.onTabSelected,
    required this.onItemsRequest,
  });

  final InventoryController controller;
  final VoidCallback onAddPressed;
  final ValueChanged<int> onTabSelected;
  final ValueChanged<ItemsScreenRequest> onItemsRequest;

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: controller,
      builder: (context, _) {
        final stats = controller.stats;
        return RefreshIndicator(
          onRefresh: controller.refresh,
          child: ListView(
            padding: AppSpacing.pageListPadding,
            children: [
              const PageHeader(
                title: '首页',
                subtitle: '今天先处理最容易浪费的库存',
                action: StatusPill(
                  label: 'vibe-fridge',
                  color: AppColors.primaryDark,
                  backgroundColor: AppColors.surfaceWarm,
                ),
              ),
              PageSection(
                child: _TodayOverviewCard(
                  controller: controller,
                  onFilterSelected: (focus) => onItemsRequest(
                    ItemsScreenRequest(focus: focus),
                  ),
                ),
              ),
              const SizedBox(height: AppSpacing.sectionGap),
              PageSection(
                child: _DashboardPair(
                  left: _ExpiringPriorityCard(controller: controller),
                  right: _CategorySummary(controller: controller),
                ),
              ),
              const SizedBox(height: AppSpacing.sectionGap),
              PageSection(
                child: _WeeklyOverview(stats: stats),
              ),
              const SizedBox(height: AppSpacing.sectionGap),
              PageSection(
                child: _QuickActionsSection(
                  onAddPressed: onAddPressed,
                  onOrderPressed: () => onTabSelected(2),
                  onRecipePressed: () => onTabSelected(3),
                  onCleanPressed: () => onItemsRequest(
                    const ItemsScreenRequest(focus: ItemsScreenFocus.cleanup),
                  ),
                ),
              ),
              const SizedBox(height: AppSpacing.sectionGap),
              PageSection(
                child: _TodayActionSection(controller: controller),
              ),
            ],
          ),
        );
      },
    );
  }
}

class _TodayOverviewCard extends StatelessWidget {
  const _TodayOverviewCard({
    required this.controller,
    required this.onFilterSelected,
  });

  final InventoryController controller;
  final ValueChanged<ItemsScreenFocus> onFilterSelected;

  @override
  Widget build(BuildContext context) {
    final items = controller.todayActionItems;
    final expired = items.where((item) {
      final days = item.daysUntilExpiry;
      return days != null && days < 0;
    }).length;
    final today = items.where((item) => item.daysUntilExpiry == 0).length;
    final reminders = items.where((item) => item.shouldRemind).length;
    final score = (100 -
            controller.stats.expiredCount * 12 -
            controller.stats.expiringSoonCount * 4)
        .clamp(0, 100);

    return SectionCard(
      color: AppColors.surfaceWarm,
      padding: const EdgeInsets.all(18),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Text(
                  '今天要处理',
                  style: Theme.of(context).textTheme.titleLarge?.copyWith(
                        color: AppColors.textPrimary,
                        fontWeight: FontWeight.w900,
                      ),
                ),
              ),
              GestureDetector(
                behavior: HitTestBehavior.opaque,
                onTap: () => onFilterSelected(ItemsScreenFocus.cleanup),
                child: StatusPill(
                  label: '${items.length} 件',
                  color:
                      items.isEmpty ? AppColors.primaryDark : AppColors.error,
                  backgroundColor: items.isEmpty
                      ? AppColors.primaryContainer
                      : AppColors.errorContainer,
                ),
              ),
            ],
          ),
          const SizedBox(height: 14),
          Wrap(
            spacing: 10,
            runSpacing: 10,
            children: [
              _SummaryChip(
                label: '已过期',
                value: '$expired',
                color: AppColors.error,
                backgroundColor: AppColors.errorContainer,
                onTap: () => onFilterSelected(ItemsScreenFocus.expired),
              ),
              _SummaryChip(
                label: '今日到期',
                value: '$today',
                color: AppColors.warning,
                backgroundColor: AppColors.warningContainer,
                onTap: () => onFilterSelected(ItemsScreenFocus.dueToday),
              ),
              _SummaryChip(
                label: '提醒到期',
                value: '$reminders',
                color: AppColors.primaryDark,
                backgroundColor: AppColors.primaryContainer,
                onTap: () => onFilterSelected(ItemsScreenFocus.reminderDue),
              ),
            ],
          ),
          const SizedBox(height: 16),
          Row(
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      '冰箱健康评分',
                      style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                            color: AppColors.textSecondary,
                            fontWeight: FontWeight.w700,
                          ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      '$score',
                      style: Theme.of(context).textTheme.displaySmall?.copyWith(
                            color: AppColors.primaryDark,
                            fontWeight: FontWeight.w900,
                          ),
                    ),
                  ],
                ),
              ),
              SizedBox(
                width: 132,
                child: MiniProgressBar(
                  value: score / 100,
                  color: score < 70 ? AppColors.warning : AppColors.primary,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _SummaryChip extends StatelessWidget {
  const _SummaryChip({
    required this.label,
    required this.value,
    required this.color,
    required this.backgroundColor,
    required this.onTap,
  });

  final String label;
  final String value;
  final Color color;
  final Color backgroundColor;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      behavior: HitTestBehavior.opaque,
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
        decoration: BoxDecoration(
          color: backgroundColor,
          borderRadius: BorderRadius.circular(AppRadii.medium),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(
              label,
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: color,
                    fontWeight: FontWeight.w700,
                  ),
            ),
            const SizedBox(width: 18),
            Text(
              value,
              style: Theme.of(context).textTheme.titleLarge?.copyWith(
                    color: color,
                    fontWeight: FontWeight.w900,
                  ),
            ),
          ],
        ),
      ),
    );
  }
}

class _DashboardPair extends StatelessWidget {
  const _DashboardPair({required this.left, required this.right});

  final Widget left;
  final Widget right;

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        if (constraints.maxWidth >= AppBreakpoints.wideGrid) {
          return Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(child: left),
              const SizedBox(width: AppSpacing.cardGap),
              Expanded(child: right),
            ],
          );
        }
        return Column(
          children: [
            left,
            const SizedBox(height: AppSpacing.cardGap),
            right,
          ],
        );
      },
    );
  }
}

class _TodayActionSection extends StatelessWidget {
  const _TodayActionSection({required this.controller});

  final InventoryController controller;

  @override
  Widget build(BuildContext context) {
    final items = controller.todayActionItems;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Expanded(
              child: Text(
                '今天要处理',
                style: Theme.of(context).textTheme.titleLarge?.copyWith(
                      fontWeight: FontWeight.w800,
                      color: AppColors.textPrimary,
                    ),
              ),
            ),
            Text(
              '${items.length} 项',
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: AppColors.textSecondary,
                    fontWeight: FontWeight.w700,
                  ),
            ),
          ],
        ),
        const SizedBox(height: 12),
        if (items.isEmpty)
          const EmptyState(
            icon: Icons.task_alt_outlined,
            title: '今天没有待处理',
            message: '到期、过期和提醒到期的库存'
                '会集中显示在这里。',
          )
        else
          ...items.take(5).map(
                (item) => Padding(
                  padding: const EdgeInsets.only(bottom: 10),
                  child: _InventoryTile(
                    controller: controller,
                    item: item,
                    status: _ActionStatus.fromItem(item),
                    showReminderActions: true,
                  ),
                ),
              ),
      ],
    );
  }
}

class _ExpiringPriorityCard extends StatelessWidget {
  const _ExpiringPriorityCard({required this.controller});

  final InventoryController controller;

  @override
  Widget build(BuildContext context) {
    final items = controller.expiringItems;
    return SectionCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            '临期优先',
            style: Theme.of(context).textTheme.titleMedium?.copyWith(
                  fontWeight: FontWeight.w900,
                  color: AppColors.textPrimary,
                ),
          ),
          const SizedBox(height: 12),
          if (items.isEmpty)
            Text(
              '7 天内没有需要处理的库存记录。',
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: AppColors.textSecondary,
                  ),
            )
          else
            ...items.take(3).map(
                  (item) => Padding(
                    padding: const EdgeInsets.only(bottom: 12),
                    child: _PriorityRow(
                      item: item,
                      onTap: () => _openItemDetail(context, item),
                    ),
                  ),
                ),
        ],
      ),
    );
  }

  Future<void> _openItemDetail(
    BuildContext context,
    InventoryItem item,
  ) async {
    final route = '/items/item/${item.id}';
    setWebRouteState(route);
    final detail = Navigator.of(context).push(
      MaterialPageRoute(
        settings: RouteSettings(name: route),
        builder: (_) => ItemDetailScreen(
          controller: controller,
          itemId: item.id,
        ),
      ),
    );
    setWebRouteState(route, replace: true);
    await detail;
    if (!supportsWebRouteState || isCurrentWebRoute(route)) {
      setWebRouteState('/home', replace: true);
    }
    await controller.refresh();
  }
}

class _PriorityRow extends StatelessWidget {
  const _PriorityRow({required this.item, required this.onTap});

  final InventoryItem item;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final days = item.daysUntilExpiry;
    final color = days != null && days <= 0
        ? AppColors.error
        : days != null && days <= 3
            ? AppColors.warning
            : AppColors.primaryDark;
    final label = days == null
        ? '无到期日'
        : days < 0
            ? '已过期 ${days.abs()} 天'
            : days == 0
                ? '今天到期'
                : '$days 天后到期';
    return GestureDetector(
      behavior: HitTestBehavior.opaque,
      onTap: onTap,
      child: Row(
        children: [
          Container(
            width: 44,
            height: 44,
            alignment: Alignment.center,
            decoration: BoxDecoration(
              color: color.withValues(alpha: 0.14),
              borderRadius: BorderRadius.circular(AppRadii.large),
            ),
            child: Icon(iconForName(item.wikiIcon), color: color),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  item.name,
                  style: Theme.of(context).textTheme.titleSmall?.copyWith(
                        color: AppColors.textPrimary,
                        fontWeight: FontWeight.w900,
                      ),
                ),
                const SizedBox(height: 2),
                Text(
                  '$label · ${item.storageLocation ?? '未设置位置'}',
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: AppColors.textSecondary,
                      ),
                ),
              ],
            ),
          ),
          StatusPill(
            label: '${item.quantity}${item.unit ?? ''}',
            color: color,
            backgroundColor: color.withValues(alpha: 0.14),
          ),
        ],
      ),
    );
  }
}

class _CategorySummary extends StatelessWidget {
  const _CategorySummary({required this.controller});

  final InventoryController controller;

  @override
  Widget build(BuildContext context) {
    final counts = controller.stats.categoryCounts;
    final total = counts.fold<int>(0, (sum, count) => sum + count.count);
    return SectionCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            '分类分布',
            style: Theme.of(context).textTheme.titleMedium?.copyWith(
                  fontWeight: FontWeight.w800,
                ),
          ),
          const SizedBox(height: AppSpacing.fieldGap),
          if (counts.isEmpty || total == 0)
            Text(
              '暂无库存分类数据',
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: AppColors.textSecondary,
                  ),
            )
          else
            ...counts.take(4).map(
                  (count) => Padding(
                    padding: const EdgeInsets.only(bottom: 12),
                    child: _CategoryBar(
                      label: count.categoryName,
                      count: count.count,
                      total: total,
                    ),
                  ),
                ),
        ],
      ),
    );
  }
}

class _CategoryBar extends StatelessWidget {
  const _CategoryBar({
    required this.label,
    required this.count,
    required this.total,
  });

  final String label;
  final int count;
  final int total;

  @override
  Widget build(BuildContext context) {
    final percent = total == 0 ? 0.0 : count / total;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Expanded(
              child: Text(
                label,
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                      color: AppColors.textPrimary,
                      fontWeight: FontWeight.w700,
                    ),
              ),
            ),
            Text(
              '${(percent * 100).round()}%',
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: AppColors.textSecondary,
                    fontWeight: FontWeight.w700,
                  ),
            ),
          ],
        ),
        const SizedBox(height: 7),
        MiniProgressBar(
          value: percent,
          color: switch (label) {
            '食品' => AppColors.primaryDark,
            '日用品' => AppColors.secondary,
            '药品' => AppColors.warning,
            _ => AppColors.error,
          },
        ),
      ],
    );
  }
}

class _WeeklyOverview extends StatelessWidget {
  const _WeeklyOverview({required this.stats});

  final InventoryStats stats;

  @override
  Widget build(BuildContext context) {
    final cards = [
      MetricCard(
        label: '库存批次',
        value: '${stats.activeBatchCount}',
        supportingText: '当前使用中',
        icon: Icons.inventory_outlined,
        color: AppColors.primaryDark,
      ),
      MetricCard(
        label: '总数量',
        value: '${stats.totalQuantity}',
        supportingText: '所有可用库存',
        icon: Icons.add_box_outlined,
        color: AppColors.secondary,
      ),
      MetricCard(
        label: '物品资料',
        value: '${stats.registeredWikiCount}',
        supportingText: '物品定义',
        icon: Icons.menu_book_outlined,
        color: AppColors.accent,
      ),
      MetricCard(
        label: '待提醒',
        value: '${stats.needingReminderCount}',
        supportingText: '提醒规则命中',
        icon: Icons.notifications_active_outlined,
        color: AppColors.warning,
      ),
    ];

    return SectionCard(
      color: AppColors.surfaceWarm,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            '本周库存概览',
            style: Theme.of(context).textTheme.titleMedium?.copyWith(
                  color: AppColors.textPrimary,
                  fontWeight: FontWeight.w900,
                ),
          ),
          const SizedBox(height: 14),
          LayoutBuilder(
            builder: (context, constraints) {
              final columns =
                  constraints.maxWidth >= AppBreakpoints.wideGrid ? 4 : 2;
              final width =
                  (constraints.maxWidth - AppSpacing.cardGap * (columns - 1)) /
                      columns;
              return Wrap(
                spacing: AppSpacing.cardGap,
                runSpacing: AppSpacing.cardGap,
                children: cards
                    .map(
                      (card) => SizedBox(
                        width: width,
                        child: card,
                      ),
                    )
                    .toList(),
              );
            },
          ),
        ],
      ),
    );
  }
}

class _QuickActionsSection extends StatelessWidget {
  const _QuickActionsSection({
    required this.onAddPressed,
    required this.onOrderPressed,
    required this.onRecipePressed,
    required this.onCleanPressed,
  });

  final VoidCallback onAddPressed;
  final VoidCallback onOrderPressed;
  final VoidCallback onRecipePressed;
  final VoidCallback onCleanPressed;

  @override
  Widget build(BuildContext context) {
    final actions = [
      WarmActionTile(
        icon: Icons.add_circle_outline,
        title: '添加物品',
        subtitle: '手动录入库存',
        onTap: onAddPressed,
      ),
      WarmActionTile(
        icon: Icons.document_scanner_outlined,
        title: '订单识别',
        subtitle: '截图或文本入库',
        onTap: onOrderPressed,
        color: AppColors.warning,
      ),
      WarmActionTile(
        icon: Icons.restaurant_menu_outlined,
        title: '智能菜谱',
        subtitle: '优先消耗临期',
        onTap: onRecipePressed,
        color: AppColors.accent,
      ),
      WarmActionTile(
        icon: Icons.cleaning_services_outlined,
        title: '清理建议',
        subtitle: '查看历史和临期',
        onTap: onCleanPressed,
        color: AppColors.secondary,
      ),
    ];
    return LayoutBuilder(
      builder: (context, constraints) {
        final columns = constraints.maxWidth >= AppBreakpoints.wideGrid ? 4 : 2;
        final width =
            (constraints.maxWidth - AppSpacing.cardGap * (columns - 1)) /
                columns;
        return Wrap(
          spacing: AppSpacing.cardGap,
          runSpacing: AppSpacing.cardGap,
          children: actions
              .map((action) => SizedBox(width: width, child: action))
              .toList(),
        );
      },
    );
  }
}

class _InventoryTile extends StatelessWidget {
  const _InventoryTile({
    required this.controller,
    required this.item,
    this.status,
    this.showReminderActions = false,
  });

  final InventoryController controller;
  final InventoryItem item;
  final _ActionStatus? status;
  final bool showReminderActions;

  @override
  Widget build(BuildContext context) {
    final tileStatus = status ?? _ActionStatus.expiry(item);

    return SectionCard(
      onTap: () async {
        final route = '/items/item/${item.id}';
        setWebRouteState(route);
        final detail = Navigator.of(context).push(
          MaterialPageRoute(
            settings: RouteSettings(name: route),
            builder: (_) => ItemDetailScreen(
              controller: controller,
              itemId: item.id,
            ),
          ),
        );
        setWebRouteState(route, replace: true);
        await detail;
        if (!supportsWebRouteState || isCurrentWebRoute(route)) {
          setWebRouteState('/home', replace: true);
        }
        await controller.refresh();
      },
      child: Column(
        children: [
          Row(
            children: [
              Container(
                width: 48,
                height: 48,
                decoration: BoxDecoration(
                  color: AppColors.secondaryContainer,
                  borderRadius: BorderRadius.circular(16),
                ),
                child: Icon(
                  iconForName(item.wikiIcon),
                  color: AppColors.secondary,
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      item.name,
                      style: Theme.of(context).textTheme.titleMedium?.copyWith(
                            fontWeight: FontWeight.w800,
                          ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      '${item.quantity}${item.unit ?? ''} · '
                      '${item.categoryName ?? '未分类'}',
                      style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                            color: AppColors.textSecondary,
                          ),
                    ),
                  ],
                ),
              ),
              StatusPill(
                label: tileStatus.label,
                icon: tileStatus.icon,
                color: tileStatus.color,
                backgroundColor: tileStatus.backgroundColor,
              ),
            ],
          ),
          if (showReminderActions) ...[
            const SizedBox(height: 12),
            Row(
              children: [
                Expanded(
                  child: OutlinedButton.icon(
                    onPressed: () => _snoozeReminder(context),
                    icon: const Icon(Icons.snooze_outlined),
                    label: const Text('稍后'),
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: OutlinedButton.icon(
                    onPressed: () => _ignoreReminder(context),
                    icon: const Icon(Icons.notifications_off_outlined),
                    label: const Text('忽略'),
                  ),
                ),
              ],
            ),
          ],
        ],
      ),
    );
  }

  Future<void> _snoozeReminder(BuildContext context) async {
    final messenger = ScaffoldMessenger.of(context);
    await controller.snoozeReminder(item.id);
    messenger.showSnackBar(
      SnackBar(content: Text('今天稍后再提醒：${item.name}')),
    );
  }

  Future<void> _ignoreReminder(BuildContext context) async {
    final messenger = ScaffoldMessenger.of(context);
    await controller.ignoreReminderForToday(item.id);
    messenger.showSnackBar(
      SnackBar(content: Text('今天不再提醒：${item.name}')),
    );
  }
}

class _ActionStatus {
  const _ActionStatus({
    required this.label,
    required this.icon,
    required this.color,
    required this.backgroundColor,
  });

  final String label;
  final IconData icon;
  final Color color;
  final Color backgroundColor;

  factory _ActionStatus.fromItem(InventoryItem item) {
    final days = item.daysUntilExpiry;
    if (days != null && days < 0) {
      return _ActionStatus(
        label: '已过期 ${days.abs()} 天',
        icon: Icons.warning_amber_outlined,
        color: AppColors.error,
        backgroundColor: AppColors.errorContainer,
      );
    }
    if (days == 0) {
      return const _ActionStatus(
        label: '今天到期',
        icon: Icons.event_busy_outlined,
        color: AppColors.warning,
        backgroundColor: AppColors.warningContainer,
      );
    }
    if (item.shouldRemind) {
      return const _ActionStatus(
        label: '提醒到期',
        icon: Icons.notifications_active_outlined,
        color: AppColors.primary,
        backgroundColor: AppColors.primaryContainer,
      );
    }
    return _ActionStatus.expiry(item);
  }

  factory _ActionStatus.expiry(InventoryItem item) {
    final days = item.daysUntilExpiry;
    final label = days == null
        ? '无到期日'
        : days < 0
            ? '已过期 ${days.abs()} 天'
            : days == 0
                ? '今天到期'
                : '$days 天后到期';
    return _ActionStatus(
      label: label,
      icon: Icons.schedule_outlined,
      color: days != null && days < 0 ? AppColors.error : AppColors.warning,
      backgroundColor: days != null && days < 0
          ? AppColors.errorContainer
          : AppColors.warningContainer,
    );
  }
}
