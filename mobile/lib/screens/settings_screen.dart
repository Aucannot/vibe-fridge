import 'package:flutter/material.dart';

import '../data/inventory_controller.dart';
import '../data/vlm_settings_store.dart';
import '../theme/app_theme.dart';
import '../widgets/app_cards.dart';

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key, required this.controller});

  final InventoryController controller;

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  final _vlmSettingsStore = VlmSettingsStore();
  final _vlmEndpointController = TextEditingController();
  final _vlmModelController = TextEditingController();
  final _vlmApiKeyController = TextEditingController();
  bool _importing = false;
  bool _loadingVlmSettings = true;
  bool _savingVlmSettings = false;

  @override
  void initState() {
    super.initState();
    _loadVlmSettings();
  }

  @override
  void dispose() {
    _vlmEndpointController.dispose();
    _vlmModelController.dispose();
    _vlmApiKeyController.dispose();
    super.dispose();
  }

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
                          style:
                              Theme.of(context).textTheme.titleMedium?.copyWith(
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
                          value:
                              '${widget.controller.stats.registeredWikiCount}',
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
                                    child: CircularProgressIndicator(
                                        strokeWidth: 2),
                                  )
                                : const Icon(Icons.upload_file_outlined),
                            label: Text(_importing
                                ? '导入中'
                                : '导入 legacy_inventory.json'),
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
                          '订单识别 VLM',
                          style:
                              Theme.of(context).textTheme.titleMedium?.copyWith(
                                    fontWeight: FontWeight.w900,
                                  ),
                        ),
                        const SizedBox(height: 12),
                        if (_loadingVlmSettings)
                          const Center(child: CircularProgressIndicator())
                        else ...[
                          _SettingRow(
                            icon: Icons.auto_awesome_outlined,
                            label: '配置状态',
                            value: _vlmApiKeyController.text.trim().isEmpty
                                ? '未配置'
                                : '已配置',
                          ),
                          const SizedBox(height: 12),
                          TextField(
                            controller: _vlmEndpointController,
                            textInputAction: TextInputAction.next,
                            decoration: const InputDecoration(
                              labelText: 'Endpoint',
                              prefixIcon: Icon(Icons.link_outlined),
                            ),
                          ),
                          const SizedBox(height: 12),
                          TextField(
                            controller: _vlmModelController,
                            textInputAction: TextInputAction.next,
                            decoration: const InputDecoration(
                              labelText: 'Model',
                              prefixIcon: Icon(Icons.memory_outlined),
                            ),
                          ),
                          const SizedBox(height: 12),
                          TextField(
                            controller: _vlmApiKeyController,
                            obscureText: true,
                            onChanged: (_) => setState(() {}),
                            decoration: const InputDecoration(
                              labelText: 'API Key',
                              prefixIcon: Icon(Icons.key_outlined),
                            ),
                          ),
                          const SizedBox(height: 12),
                          SizedBox(
                            width: double.infinity,
                            child: FilledButton.icon(
                              onPressed:
                                  _savingVlmSettings ? null : _saveVlmSettings,
                              icon: _savingVlmSettings
                                  ? const SizedBox(
                                      width: 18,
                                      height: 18,
                                      child: CircularProgressIndicator(
                                          strokeWidth: 2),
                                    )
                                  : const Icon(Icons.save_outlined),
                              label: Text(
                                  _savingVlmSettings ? '保存中' : '保存 VLM 配置'),
                            ),
                          ),
                        ],
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
                          style:
                              Theme.of(context).textTheme.titleMedium?.copyWith(
                                    fontWeight: FontWeight.w900,
                                  ),
                        ),
                        const SizedBox(height: 12),
                        const _MigrationStep(
                            text: 'Flutter 工程源码已建立', done: true),
                        const _MigrationStep(
                            text: '核心模型和 SQLite 服务已迁移', done: true),
                        const _MigrationStep(
                            text: 'Android/macOS 平台目录已生成', done: true),
                        const _MigrationStep(
                            text: '旧 SQLite JSON 导入通道已实现', done: true),
                        const _MigrationStep(
                            text: '订单截图 VLM 识别入库已接入', done: true),
                        const _MigrationStep(
                            text: '完整 Xcode 与 Android SDK 待配置', done: false),
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

  Future<void> _loadVlmSettings() async {
    final settings = await _vlmSettingsStore.load();
    if (!mounted) {
      return;
    }
    _vlmEndpointController.text = settings.endpoint;
    _vlmModelController.text = settings.model;
    _vlmApiKeyController.text = settings.apiKey;
    setState(() => _loadingVlmSettings = false);
  }

  Future<void> _saveVlmSettings() async {
    setState(() => _savingVlmSettings = true);
    try {
      await _vlmSettingsStore.save(
        VlmSettings(
          endpoint: _vlmEndpointController.text,
          model: _vlmModelController.text,
          apiKey: _vlmApiKeyController.text,
        ),
      );
      if (!mounted) {
        return;
      }
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('VLM 配置已保存')),
      );
      setState(() {});
    } catch (error) {
      if (!mounted) {
        return;
      }
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('保存失败：$error')),
      );
    } finally {
      if (mounted) {
        setState(() => _savingVlmSettings = false);
      }
    }
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
                    color:
                        done ? AppColors.textPrimary : AppColors.textSecondary,
                    fontWeight: done ? FontWeight.w700 : FontWeight.w500,
                  ),
            ),
          ),
        ],
      ),
    );
  }
}
