import 'package:flutter/material.dart';

import '../theme/app_theme.dart';
import 'app_cards.dart';

const inventoryTagOptions = ['临期优先', '已开封', '囤货', '常用', '易浪费'];

class TagSelectorCard extends StatelessWidget {
  const TagSelectorCard({
    super.key,
    required this.selectedTags,
    required this.onChanged,
  });

  final Set<String> selectedTags;
  final ValueChanged<Set<String>> onChanged;

  @override
  Widget build(BuildContext context) {
    return SectionCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            '标签',
            style: Theme.of(context).textTheme.titleMedium?.copyWith(
                  color: AppColors.textPrimary,
                  fontWeight: FontWeight.w900,
                ),
          ),
          const SizedBox(height: 4),
          Text(
            '用于筛选和标记处理优先级',
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: AppColors.textSecondary,
                ),
          ),
          const SizedBox(height: 12),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              for (final tag in inventoryTagOptions)
                FilterChip(
                  label: Text(tag),
                  selected: selectedTags.contains(tag),
                  onSelected: (selected) {
                    final next = Set<String>.from(selectedTags);
                    if (selected) {
                      next.add(tag);
                    } else {
                      next.remove(tag);
                    }
                    onChanged(next);
                  },
                ),
            ],
          ),
        ],
      ),
    );
  }
}
