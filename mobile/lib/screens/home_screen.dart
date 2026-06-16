import 'package:flutter/material.dart';
import '../data/inventory_controller.dart';
import '../models/inventory_item.dart';
import '../theme/app_theme.dart';
import '../widgets/app_cards.dart';
import '../widgets/icon_mapper.dart';
import 'item_detail_screen.dart';

class HomeScreen extends StatelessWidget {
  const HomeScreen({
    super.key,
    required this.controller,
    required this.onAddPressed,
  });

  final InventoryController controller;
  final VoidCallback onAddPressed;

  @override
  Widget build(BuildContext context) {
    final stats = controller.stats;
    return RefreshIndicator(
      onRefresh: controller.refresh,
      child: ListView(
        padding: const EdgeInsets.only(bottom: 24),
        children: [
          PageHeader(
            title: 'vibe-fridge',
            subtitle: '库存、保质期和提醒集中管理',
            action: IconButton.filled(
              tooltip: '添加物品',
              onPressed: onAddPressed,
              icon: const Icon(Icons.add),
            ),
          ),
          ContentWidth(
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 20),
              child: LayoutBuilder(
                builder: (context, constraints) {
                  final columns = constraints.maxWidth >= 720 ? 4 : 2;
                  return GridView.count(
                    crossAxisCount: columns,
                    crossAxisSpacing: 12,
                    mainAxisSpacing: 12,
                    shrinkWrap: true,
                    physics: const NeverScrollableScrollPhysics(),
                    childAspectRatio: columns == 4 ? 1.05 : 0.84,
                    children: [
                      MetricCard(
                        label: '库存总量',
                        value: '${stats.totalQuantity}',
                        supportingText: '${stats.activeBatchCount} 个批次',
                        icon: Icons.inventory_2_outlined,
                        color: AppColors.primary,
                      ),
                      MetricCard(
                        label: '即将过期',
                        value: '${stats.expiringSoonCount}',
                        supportingText: '7 天内需要处理',
                        icon: Icons.schedule_outlined,
                        color: AppColors.warning,
                      ),
                      MetricCard(
                        label: '已过期',
                        value: '${stats.expiredCount}',
                        supportingText: '未标记消耗的记录',
                        icon: Icons.warning_amber_outlined,
                        color: AppColors.error,
                      ),
                      MetricCard(
                        label: 'Wiki 条目',
                        value: '${stats.registeredWikiCount}',
                        supportingText: '已注册物品定义',
                        icon: Icons.menu_book_outlined,
                        color: AppColors.secondary,
                      ),
                    ],
                  );
                },
              ),
            ),
          ),
          const SizedBox(height: 20),
          ContentWidth(
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 20),
              child: _ExpiringSection(controller: controller),
            ),
          ),
          const SizedBox(height: 20),
          ContentWidth(
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 20),
              child: _CategorySummary(controller: controller),
            ),
          ),
        ],
      ),
    );
  }
}

class _ExpiringSection extends StatelessWidget {
  const _ExpiringSection({required this.controller});

  final InventoryController controller;

  @override
  Widget build(BuildContext context) {
    final items = controller.expiringItems;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          '近期提醒',
          style: Theme.of(context).textTheme.titleLarge?.copyWith(
                fontWeight: FontWeight.w800,
                color: AppColors.textPrimary,
              ),
        ),
        const SizedBox(height: 12),
        if (items.isEmpty)
          const EmptyState(
            icon: Icons.check_circle_outline,
            title: '暂无临期物品',
            message: '7 天内没有需要处理的库存记录。',
          )
        else
          ...items.take(5).map(
                (item) => Padding(
                  padding: const EdgeInsets.only(bottom: 10),
                  child: _InventoryTile(controller: controller, item: item),
                ),
              ),
      ],
    );
  }
}

class _CategorySummary extends StatelessWidget {
  const _CategorySummary({required this.controller});

  final InventoryController controller;

  @override
  Widget build(BuildContext context) {
    final counts = controller.stats.categoryCounts;
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
          const SizedBox(height: 14),
          if (counts.isEmpty)
            Text(
              '暂无库存分类数据',
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: AppColors.textSecondary,
                  ),
            )
          else
            Wrap(
              spacing: 10,
              runSpacing: 10,
              children: counts
                  .map(
                    (count) => StatusPill(
                      label: '${count.categoryName} ${count.count}',
                      color: AppColors.primary,
                      backgroundColor: AppColors.primaryContainer,
                    ),
                  )
                  .toList(),
            ),
        ],
      ),
    );
  }
}

class _InventoryTile extends StatelessWidget {
  const _InventoryTile({
    required this.controller,
    required this.item,
  });

  final InventoryController controller;
  final InventoryItem item;

  @override
  Widget build(BuildContext context) {
    final days = item.daysUntilExpiry;
    final status = days == null
        ? '无到期日'
        : days < 0
            ? '已过期 ${days.abs()} 天'
            : days == 0
                ? '今天到期'
                : '$days 天后到期';

    return SectionCard(
      onTap: () async {
        await Navigator.of(context).push(
          MaterialPageRoute(
            builder: (_) => ItemDetailScreen(
              controller: controller,
              itemId: item.id,
            ),
          ),
        );
        await controller.refresh();
      },
      child: Row(
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
                  '${item.quantity}${item.unit ?? ''} · ${item.categoryName ?? '未分类'}',
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                        color: AppColors.textSecondary,
                      ),
                ),
              ],
            ),
          ),
          StatusPill(
            label: status,
            icon: Icons.schedule_outlined,
            color: AppColors.warning,
            backgroundColor: AppColors.warningContainer,
          ),
        ],
      ),
    );
  }
}
