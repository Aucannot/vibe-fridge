import 'dart:io' as io;

import 'package:flutter/material.dart';

import '../theme/app_theme.dart';
import 'app_cards.dart';

class ImageAttachmentCard extends StatelessWidget {
  const ImageAttachmentCard({
    super.key,
    required this.imagePath,
    required this.isBusy,
    required this.onPick,
    required this.onClear,
  });

  final String? imagePath;
  final bool isBusy;
  final VoidCallback onPick;
  final VoidCallback onClear;

  @override
  Widget build(BuildContext context) {
    final hasImage = imagePath != null && imagePath!.isNotEmpty;
    final supportingText =
        hasImage ? '这张照片会跟随当前库存批次保存' : '拍下包装、标签或小票，之后查看库存时能直接确认实物';
    return SectionCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                width: 42,
                height: 42,
                decoration: BoxDecoration(
                  color: AppColors.secondaryContainer,
                  borderRadius: BorderRadius.circular(14),
                ),
                child: const Icon(
                  Icons.photo_camera_outlined,
                  color: AppColors.secondary,
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      '物品照片',
                      style: Theme.of(context).textTheme.titleMedium?.copyWith(
                            color: AppColors.textPrimary,
                            fontWeight: FontWeight.w900,
                          ),
                    ),
                    const SizedBox(height: 3),
                    Text(
                      supportingText,
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                            color: AppColors.textSecondary,
                          ),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          _ImagePreview(imagePath: imagePath),
          const SizedBox(height: 12),
          Row(
            children: [
              Expanded(
                child: OutlinedButton.icon(
                  onPressed: isBusy ? null : onPick,
                  icon: isBusy
                      ? const SizedBox(
                          width: 18,
                          height: 18,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Icon(Icons.photo_camera_outlined),
                  label: Text(
                    isBusy ? '处理中' : (hasImage ? '重拍或更换' : '拍照或选择图片'),
                  ),
                ),
              ),
              if (hasImage) ...[
                const SizedBox(width: 12),
                IconButton.outlined(
                  tooltip: '移除附件',
                  onPressed: isBusy ? null : onClear,
                  icon: const Icon(Icons.close),
                ),
              ],
            ],
          ),
        ],
      ),
    );
  }
}

class _ImagePreview extends StatelessWidget {
  const _ImagePreview({required this.imagePath});

  final String? imagePath;

  @override
  Widget build(BuildContext context) {
    final hasImage = imagePath != null && imagePath!.isNotEmpty;
    if (!hasImage) {
      return Container(
        height: 132,
        width: double.infinity,
        alignment: Alignment.center,
        decoration: BoxDecoration(
          color: AppColors.surfaceVariant,
          borderRadius: BorderRadius.circular(AppRadii.medium),
          border: Border.all(color: AppColors.divider),
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(
              Icons.add_a_photo_outlined,
              color: AppColors.textSecondary,
              size: 32,
            ),
            const SizedBox(height: 8),
            Text(
              '还没有物品照片',
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: AppColors.textSecondary,
                    fontWeight: FontWeight.w700,
                  ),
            ),
          ],
        ),
      );
    }
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        ClipRRect(
          borderRadius: BorderRadius.circular(AppRadii.medium),
          child: Image.file(
            io.File(imagePath!),
            height: 180,
            width: double.infinity,
            fit: BoxFit.cover,
            errorBuilder: (context, error, stackTrace) {
              return Container(
                height: 132,
                width: double.infinity,
                alignment: Alignment.center,
                color: AppColors.surfaceVariant,
                child: const Icon(Icons.broken_image_outlined),
              );
            },
          ),
        ),
        const SizedBox(height: 8),
        SelectableText(
          imagePath!,
          style: Theme.of(context).textTheme.bodySmall?.copyWith(
                color: AppColors.textSecondary,
              ),
        ),
      ],
    );
  }
}
