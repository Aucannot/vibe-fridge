import 'package:flutter/material.dart';

import '../theme/app_theme.dart';
import '../widgets/app_cards.dart';

class RecipesScreen extends StatelessWidget {
  const RecipesScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.only(bottom: 24),
      children: [
        const PageHeader(
          title: '食谱',
          subtitle: '后续会基于现有库存生成消耗建议',
        ),
        ContentWidth(
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 20),
            child: SectionCard(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Container(
                    width: 52,
                    height: 52,
                    decoration: BoxDecoration(
                      color: AppColors.warningContainer,
                      borderRadius: BorderRadius.circular(16),
                    ),
                    child: const Icon(
                      Icons.restaurant_menu_outlined,
                      color: AppColors.warning,
                    ),
                  ),
                  const SizedBox(height: 14),
                  Text(
                    '库存驱动的食谱入口',
                    style: Theme.of(context).textTheme.titleLarge?.copyWith(
                          fontWeight: FontWeight.w900,
                        ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    '这里会优先使用临期食材、冷藏食材和常用单位信息，为下一阶段 AI 食谱推荐保留入口。',
                    style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                          color: AppColors.textSecondary,
                        ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ],
    );
  }
}
