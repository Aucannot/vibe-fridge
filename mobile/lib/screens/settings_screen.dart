import 'package:flutter/material.dart';

import '../data/inventory_controller.dart';
import '../theme/app_theme.dart';
import '../widgets/app_cards.dart';

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key, required this.controller});

  final InventoryController controller;

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  bool _importing = false;

  @override
  Widget build(BuildContext context) {
    return RefreshIndicator(
      onRefresh: widget.controller.refresh,
      child: ListView(
        padding: const EdgeInsets.only(bottom: 24),
        children: [
          const PageHeader(
            title: '设置',
            subtitle: 'Flutter 迁移期间的运行状态',
          ),
          ContentWidth(
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 20),
              child: Column(
                children: [
                  SectionCard(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          '本地数据',
                          style: Theme.of(context).textTheme.titleMedium?.copyWith(
                                fontWeight: FontWeight.w900,
                              ),
                        ),
                        const SizedBox(height: 12),
                        const _SettingRow(
                          icon: Icons.storage_outlined,
                          label: '数据库',
                          value: 'Flutter 独立 SQLite',
                        ),
                        const _SettingRow(
                          icon: Icons.notifications_outlined,
                          label: '默认提醒',
                          value: '过期前 3 天',
                        ),
                        _SettingRow(
                          icon: Icons.menu_book_outlined,
                          label: 'Wiki 条目',
                          value: '${widget.controller.stats.registeredWikiCount}',
                        ),
                        const SizedBox(height: 12),
                        SizedBox(
                          width: double.infinity,
                          child: OutlinedButton.icon(
                            onPressed: _importing ? null : _importLegacyAsset,
                            icon: _importing
                                ? const SizedBox(
                                    width: 18,
                                    height: 18,
                                    child: CircularProgressIndicator(strokeWidth: 2),
                                  )
                                : const Icon(Icons.upload_file_outlined),
                            label: Text(_importing ? '导入中' : '导入 legacy_inventory.json'),
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 14),
                  SectionCard(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          '迁移状态',
                          style: Theme.of(context).textTheme.titleMedium?.copyWith(
                                fontWeight: FontWeight.w900,
                              ),
                        ),
                        const SizedBox(height: 12),
                        const _MigrationStep(text: 'Flutter 工程源码已建立', done: true),
                        const _MigrationStep(text: '核心模型和 SQLite 服务已迁移', done: true),
                        const _MigrationStep(text: 'Android/macOS 平台目录已生成', done: true),
                        const _MigrationStep(text: '旧 SQLite JSON 导入通道已实现', done: true),
                        const _MigrationStep(text: '完整 Xcode 与 Android SDK 待配置', done: false),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Future<void> _importLegacyAsset() async {
    setState(() => _importing = true);
    try {
      final result = await widget.controller.importLegacyAsset();
      if (!mounted) {
        return;
      }
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            result.total == 0
                ? '没有可导入的数据'
                : '导入完成：${result.items} 条库存，${result.wikis} 个 Wiki，${result.tags} 个标签',
          ),
        ),
      );
    } catch (error) {
      if (!mounted) {
        return;
      }
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('导入失败：$error')),
      );
    } finally {
      if (mounted) {
        setState(() => _importing = false);
      }
    }
  }
}

class _SettingRow extends StatelessWidget {
  const _SettingRow({
    required this.icon,
    required this.label,
    required this.value,
  });

  final IconData icon;
  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 9),
      child: Row(
        children: [
          Icon(icon, color: AppColors.secondary),
          const SizedBox(width: 12),
          Expanded(
            child: Text(
              label,
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: AppColors.textSecondary,
                  ),
            ),
          ),
          Text(
            value,
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  color: AppColors.textPrimary,
                  fontWeight: FontWeight.w800,
                ),
          ),
        ],
      ),
    );
  }
}

class _MigrationStep extends StatelessWidget {
  const _MigrationStep({required this.text, required this.done});

  final String text;
  final bool done;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 7),
      child: Row(
        children: [
          Icon(
            done ? Icons.check_circle : Icons.radio_button_unchecked,
            color: done ? AppColors.success : AppColors.textHint,
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Text(
              text,
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: done ? AppColors.textPrimary : AppColors.textSecondary,
                    fontWeight: done ? FontWeight.w700 : FontWeight.w500,
                  ),
            ),
          ),
        ],
      ),
    );
  }
}
