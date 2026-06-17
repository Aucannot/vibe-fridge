import 'dart:convert';

import 'package:file_selector/file_selector.dart' as file_selector;
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';

import '../data/acceptance_test_service.dart';
import '../data/inventory_controller.dart';
import '../data/inventory_repository.dart';
import '../data/recipe_preferences_store.dart';
import '../data/vlm_order_service.dart';
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
  final _recipeFlavorController = TextEditingController();
  final _recipeDietaryController = TextEditingController();
  final _recipeToolsController = TextEditingController();
  final _recipeMinutesController = TextEditingController();
  final _recipeServingsController = TextEditingController();
  final _vlmOrderService = VlmOrderService();
  final _recipePreferencesStore = RecipePreferencesStore();
  bool _importing = false;
  bool _exportingBackup = false;
  bool _restoringBackup = false;
  bool _exportingCsv = false;
  bool _loadingVlmSettings = true;
  bool _loadingRecipePreferences = true;
  bool _savingRecipePreferences = false;
  bool _savingVlmSettings = false;
  bool _testingVlmSettings = false;
  bool _runningAcceptance = false;
  bool _resettingDemoData = false;
  bool _syncingNotifications = false;
  bool _hasStoredVlmApiKey = false;
  String? _vlmTestMessage;
  bool? _vlmTestPassed;
  AcceptanceReport? _lastAcceptanceReport;
  LegacyImportResult? _lastLegacyImportResult;

  @override
  void initState() {
    super.initState();
    _loadVlmSettings();
    _loadRecipePreferences();
  }

  @override
  void dispose() {
    _vlmEndpointController.dispose();
    _vlmModelController.dispose();
    _vlmApiKeyController.dispose();
    _recipeFlavorController.dispose();
    _recipeDietaryController.dispose();
    _recipeToolsController.dispose();
    _recipeMinutesController.dispose();
    _recipeServingsController.dispose();
    _vlmOrderService.close();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final notificationsSupported =
        widget.controller.notificationPermission.supported;
    return RefreshIndicator(
      onRefresh: widget.controller.refresh,
      child: ListView(
        padding: AppSpacing.pageListPadding,
        children: [
          const PageHeader(
            title: '设置',
            subtitle: '管理提醒、备份和个人偏好',
          ),
          PageSection(
            child: Column(
              children: [
                SectionCard(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        '数据与备份',
                        style:
                            Theme.of(context).textTheme.titleMedium?.copyWith(
                                  fontWeight: FontWeight.w900,
                                ),
                      ),
                      const SizedBox(height: AppSpacing.cardGap),
                      _SettingRow(
                        icon: Icons.inventory_2_outlined,
                        label: '库存批次',
                        value: '${widget.controller.stats.activeBatchCount}',
                      ),
                      const _SettingRow(
                        icon: Icons.notifications_outlined,
                        label: '默认提醒',
                        value: '过期前 3 天',
                      ),
                      _SettingRow(
                        icon: Icons.menu_book_outlined,
                        label: '物品资料',
                        value: '${widget.controller.stats.registeredWikiCount}',
                      ),
                      const SizedBox(height: AppSpacing.cardGap),
                      SizedBox(
                        width: double.infinity,
                        child: OutlinedButton.icon(
                          onPressed: _importing ? null : _importLegacyAsset,
                          icon: _importing
                              ? const SizedBox(
                                  width: 18,
                                  height: 18,
                                  child:
                                      CircularProgressIndicator(strokeWidth: 2),
                                )
                              : const Icon(Icons.upload_file_outlined),
                          label: Text(_importing ? '导入中' : '导入旧版库存'),
                        ),
                      ),
                      if (_lastLegacyImportResult != null) ...[
                        const SizedBox(height: AppSpacing.compactPadding),
                        _LegacyImportResultSummary(
                          result: _lastLegacyImportResult!,
                          onShowLog: () => _showLegacyImportLog(
                            _lastLegacyImportResult!,
                          ),
                        ),
                      ],
                      const SizedBox(height: AppSpacing.compactPadding),
                      if (widget.controller.backupReminderState.isPending) ...[
                        _BackupReminderCard(
                          state: widget.controller.backupReminderState,
                          onExportBackup:
                              _exportingBackup ? null : _exportBackupJson,
                        ),
                        const SizedBox(height: AppSpacing.compactPadding),
                      ],
                      _DataFileActions(
                        exportingBackup: _exportingBackup,
                        restoringBackup: _restoringBackup,
                        exportingCsv: _exportingCsv,
                        onExportBackup: _exportBackupJson,
                        onRestoreBackup: _restoreBackupJson,
                        onExportCsv: _exportInventoryCsv,
                      ),
                      if (kDebugMode) ...[
                        const SizedBox(height: AppSpacing.cardGap),
                        SizedBox(
                          width: double.infinity,
                          child: OutlinedButton.icon(
                            onPressed:
                                _resettingDemoData ? null : _resetDemoData,
                            icon: _resettingDemoData
                                ? const _TinyProgress()
                                : const Icon(Icons.restart_alt_outlined),
                            label: Text(
                              _resettingDemoData ? '重置中' : '重置示例数据',
                            ),
                          ),
                        ),
                      ],
                    ],
                  ),
                ),
                const SizedBox(height: AppSpacing.fieldGap),
                SectionCard(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        '本地通知',
                        style:
                            Theme.of(context).textTheme.titleMedium?.copyWith(
                                  fontWeight: FontWeight.w900,
                                ),
                      ),
                      const SizedBox(height: AppSpacing.cardGap),
                      _SettingRow(
                        icon: Icons.notifications_active_outlined,
                        label: '权限状态',
                        value: widget
                            .controller.notificationPermission.displayText,
                      ),
                      _SettingRow(
                        icon: Icons.event_available_outlined,
                        label: '提醒调度',
                        value: widget.controller.lastNotificationSyncResult
                                ?.displayText ??
                            '尚未同步',
                      ),
                      const SizedBox(height: AppSpacing.cardGap),
                      Row(
                        children: [
                          Expanded(
                            child: OutlinedButton.icon(
                              onPressed: _syncingNotifications ||
                                      !notificationsSupported
                                  ? null
                                  : _requestNotificationPermission,
                              icon: _syncingNotifications
                                  ? const _TinyProgress()
                                  : const Icon(
                                      Icons.notification_add_outlined,
                                    ),
                              label: const Text('请求权限'),
                            ),
                          ),
                          const SizedBox(width: AppSpacing.cardGap),
                          Expanded(
                            child: FilledButton.icon(
                              onPressed: _syncingNotifications ||
                                      !notificationsSupported
                                  ? null
                                  : _syncLocalNotifications,
                              icon: _syncingNotifications
                                  ? const _TinyProgress()
                                  : const Icon(Icons.sync_outlined),
                              label: const Text('同步提醒'),
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: AppSpacing.fieldGap),
                SectionCard(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Expanded(
                            child: Text(
                              '食谱偏好',
                              style: Theme.of(context)
                                  .textTheme
                                  .titleMedium
                                  ?.copyWith(
                                    fontWeight: FontWeight.w900,
                                  ),
                            ),
                          ),
                          if (_savingRecipePreferences)
                            const SizedBox(
                              width: 18,
                              height: 18,
                              child: CircularProgressIndicator(strokeWidth: 2),
                            ),
                        ],
                      ),
                      const SizedBox(height: AppSpacing.cardGap),
                      if (_loadingRecipePreferences)
                        const Center(child: CircularProgressIndicator())
                      else ...[
                        TextField(
                          controller: _recipeFlavorController,
                          textInputAction: TextInputAction.next,
                          decoration: const InputDecoration(
                            labelText: '口味偏好',
                            hintText: '如清淡、川味、少油',
                            prefixIcon: Icon(Icons.tune_outlined),
                          ),
                        ),
                        const SizedBox(height: AppSpacing.cardGap),
                        TextField(
                          controller: _recipeDietaryController,
                          textInputAction: TextInputAction.next,
                          decoration: const InputDecoration(
                            labelText: '忌口/饮食限制',
                            hintText: '如不吃辣、低糖、素食',
                            prefixIcon: Icon(Icons.no_food_outlined),
                          ),
                        ),
                        const SizedBox(height: AppSpacing.cardGap),
                        TextField(
                          controller: _recipeToolsController,
                          textInputAction: TextInputAction.next,
                          decoration: const InputDecoration(
                            labelText: '可用厨具',
                            hintText: '如空气炸锅、电饭煲、平底锅',
                            prefixIcon: Icon(Icons.soup_kitchen_outlined),
                          ),
                        ),
                        const SizedBox(height: AppSpacing.cardGap),
                        Row(
                          children: [
                            Expanded(
                              child: TextField(
                                controller: _recipeMinutesController,
                                keyboardType: TextInputType.number,
                                textInputAction: TextInputAction.next,
                                decoration: const InputDecoration(
                                  labelText: '时间',
                                  suffixText: '分钟',
                                ),
                              ),
                            ),
                            const SizedBox(width: 10),
                            Expanded(
                              child: TextField(
                                controller: _recipeServingsController,
                                keyboardType: TextInputType.number,
                                decoration: const InputDecoration(
                                  labelText: '人数',
                                  suffixText: '人',
                                ),
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: AppSpacing.cardGap),
                        SizedBox(
                          width: double.infinity,
                          child: OutlinedButton.icon(
                            onPressed: _savingRecipePreferences
                                ? null
                                : _saveRecipePreferences,
                            icon: const Icon(Icons.save_outlined),
                            label: const Text('保存食谱偏好'),
                          ),
                        ),
                      ],
                    ],
                  ),
                ),
                const SizedBox(height: AppSpacing.fieldGap),
                SectionCard(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Expanded(
                            child: Text(
                              '自验收测试',
                              style: Theme.of(context)
                                  .textTheme
                                  .titleMedium
                                  ?.copyWith(
                                    fontWeight: FontWeight.w900,
                                  ),
                            ),
                          ),
                          if (_lastAcceptanceReport != null)
                            StatusPill(
                              label: _lastAcceptanceReport!.passed
                                  ? '全部通过'
                                  : '存在失败',
                              icon: _lastAcceptanceReport!.passed
                                  ? Icons.check_circle_outline
                                  : Icons.error_outline,
                              color: _lastAcceptanceReport!.passed
                                  ? AppColors.success
                                  : AppColors.error,
                              backgroundColor: _lastAcceptanceReport!.passed
                                  ? AppColors.successContainer
                                  : AppColors.errorContainer,
                            ),
                        ],
                      ),
                      const SizedBox(height: AppSpacing.cardGap),
                      _SettingRow(
                        icon: Icons.fact_check_outlined,
                        label: '核心闭环',
                        value: _lastAcceptanceReport == null
                            ? '未运行'
                            : '${_lastAcceptanceReport!.passedCount}/'
                                '${_lastAcceptanceReport!.checks.length}',
                      ),
                      if (_lastAcceptanceReport != null) ...[
                        _SettingRow(
                          icon: Icons.timer_outlined,
                          label: '耗时',
                          value: _formatDuration(
                            _lastAcceptanceReport!.duration,
                          ),
                        ),
                        const SizedBox(height: AppSpacing.compactPadding),
                        _AcceptanceResults(report: _lastAcceptanceReport!),
                        const SizedBox(height: AppSpacing.cardGap),
                      ] else
                        const SizedBox(height: AppSpacing.cardGap),
                      SizedBox(
                        width: double.infinity,
                        child: FilledButton.icon(
                          onPressed:
                              _runningAcceptance ? null : _runAcceptanceChecks,
                          icon: _runningAcceptance
                              ? const SizedBox(
                                  width: 18,
                                  height: 18,
                                  child: CircularProgressIndicator(
                                    strokeWidth: 2,
                                  ),
                                )
                              : const Icon(Icons.play_arrow_outlined),
                          label: Text(
                            _runningAcceptance ? '运行中' : '运行自验收',
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: AppSpacing.fieldGap),
                SectionCard(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        '订单识别 AI',
                        style:
                            Theme.of(context).textTheme.titleMedium?.copyWith(
                                  fontWeight: FontWeight.w900,
                                ),
                      ),
                      const SizedBox(height: AppSpacing.cardGap),
                      if (_loadingVlmSettings)
                        const Center(child: CircularProgressIndicator())
                      else ...[
                        _SettingRow(
                          icon: Icons.auto_awesome_outlined,
                          label: '配置状态',
                          value: !_hasVisibleOrStoredVlmApiKey ? '未配置' : '已配置',
                        ),
                        const _SettingRow(
                          icon: Icons.security_outlined,
                          label: 'API key 存储',
                          value: '系统安全存储',
                        ),
                        const SizedBox(height: AppSpacing.cardGap),
                        TextField(
                          controller: _vlmEndpointController,
                          textInputAction: TextInputAction.next,
                          decoration: const InputDecoration(
                            labelText: 'Endpoint',
                            prefixIcon: Icon(Icons.link_outlined),
                          ),
                        ),
                        const SizedBox(height: AppSpacing.cardGap),
                        TextField(
                          controller: _vlmModelController,
                          textInputAction: TextInputAction.next,
                          decoration: const InputDecoration(
                            labelText: 'Model',
                            prefixIcon: Icon(Icons.memory_outlined),
                          ),
                        ),
                        const SizedBox(height: AppSpacing.cardGap),
                        TextField(
                          controller: _vlmApiKeyController,
                          obscureText: true,
                          onChanged: (_) => setState(() {}),
                          decoration: InputDecoration(
                            labelText: 'API Key',
                            hintText: _hasStoredVlmApiKey
                                ? '已安全保存，留空保持不变'
                                : '只保存在系统安全存储',
                            helperText: _hasStoredVlmApiKey
                                ? '已保存的 key 不会明文显示'
                                : '仅保存在本机安全区域',
                            prefixIcon: const Icon(Icons.key_outlined),
                          ),
                        ),
                        const SizedBox(height: AppSpacing.cardGap),
                        if (_vlmTestMessage != null) ...[
                          _VlmTestResult(
                            message: _vlmTestMessage!,
                            passed: _vlmTestPassed == true,
                          ),
                          const SizedBox(height: AppSpacing.cardGap),
                        ],
                        _VlmSettingsActions(
                          saving: _savingVlmSettings,
                          testing: _testingVlmSettings,
                          onSave: _saveVlmSettings,
                          onTest: _testVlmSettings,
                          onReset: _resetVlmSettings,
                          onClear: _clearVlmSettings,
                        ),
                      ],
                    ],
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  bool get _hasVisibleOrStoredVlmApiKey =>
      _hasStoredVlmApiKey || _vlmApiKeyController.text.trim().isNotEmpty;

  Future<void> _loadVlmSettings() async {
    final settings = await _vlmSettingsStore.load(revealApiKey: false);
    if (!mounted) {
      return;
    }
    _vlmEndpointController.text = settings.endpoint;
    _vlmModelController.text = settings.model;
    _vlmApiKeyController.clear();
    setState(() {
      _hasStoredVlmApiKey = settings.hasStoredApiKey;
      _loadingVlmSettings = false;
    });
  }

  Future<void> _loadRecipePreferences() async {
    final preferences = await _recipePreferencesStore.load();
    if (!mounted) {
      return;
    }
    _recipeFlavorController.text = preferences.flavorProfile;
    _recipeDietaryController.text = preferences.dietaryRestrictions;
    _recipeToolsController.text = preferences.tools;
    _recipeMinutesController.text = '${preferences.cookMinutes}';
    _recipeServingsController.text = '${preferences.servings}';
    setState(() => _loadingRecipePreferences = false);
  }

  Future<void> _requestNotificationPermission() async {
    setState(() => _syncingNotifications = true);
    try {
      final permission =
          await widget.controller.requestNotificationPermission();
      if (!mounted) {
        return;
      }
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('通知权限：${permission.displayText}')),
      );
    } catch (error, stackTrace) {
      if (!mounted) {
        return;
      }
      showAppErrorSnackBar(
        context,
        message: '请求通知权限失败',
        error: error,
        stackTrace: stackTrace,
      );
    } finally {
      if (mounted) {
        setState(() => _syncingNotifications = false);
      }
    }
  }

  Future<void> _syncLocalNotifications() async {
    setState(() => _syncingNotifications = true);
    try {
      final result = await widget.controller.syncLocalNotifications();
      if (!mounted) {
        return;
      }
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(result.displayText)),
      );
    } catch (error, stackTrace) {
      if (!mounted) {
        return;
      }
      showAppErrorSnackBar(
        context,
        message: '同步本地通知失败',
        error: error,
        stackTrace: stackTrace,
      );
    } finally {
      if (mounted) {
        setState(() => _syncingNotifications = false);
      }
    }
  }

  Future<void> _saveRecipePreferences() async {
    setState(() => _savingRecipePreferences = true);
    try {
      await _recipePreferencesStore.save(
        RecipePreferences(
          flavorProfile: _recipeFlavorController.text,
          dietaryRestrictions: _recipeDietaryController.text,
          tools: _recipeToolsController.text,
          cookMinutes: int.tryParse(_recipeMinutesController.text) ?? 30,
          servings: int.tryParse(_recipeServingsController.text) ?? 2,
        ),
      );
      if (!mounted) {
        return;
      }
      await _loadRecipePreferences();
      if (!mounted) {
        return;
      }
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('食谱偏好已保存')),
      );
    } catch (error, stackTrace) {
      if (!mounted) {
        return;
      }
      showAppErrorSnackBar(
        context,
        message: '保存食谱偏好失败',
        error: error,
        stackTrace: stackTrace,
      );
    } finally {
      if (mounted) {
        setState(() => _savingRecipePreferences = false);
      }
    }
  }

  Future<void> _saveVlmSettings() async {
    setState(() => _savingVlmSettings = true);
    try {
      await _vlmSettingsStore.save(
        VlmSettings(
          endpoint: _vlmEndpointController.text,
          model: _vlmModelController.text,
          apiKey: _vlmApiKeyController.text,
          hasStoredApiKey: _hasStoredVlmApiKey,
        ),
        preserveExistingApiKeyIfBlank: true,
      );
      if (!mounted) {
        return;
      }
      final saved = await _vlmSettingsStore.load(revealApiKey: false);
      if (!mounted) {
        return;
      }
      _vlmApiKeyController.clear();
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('订单识别配置已保存')),
      );
      setState(() {
        _hasStoredVlmApiKey = saved.hasStoredApiKey;
        _vlmTestMessage = null;
        _vlmTestPassed = null;
      });
    } catch (error, stackTrace) {
      if (!mounted) {
        return;
      }
      showAppErrorSnackBar(
        context,
        message: '保存订单识别配置失败',
        error: error,
        stackTrace: stackTrace,
      );
    } finally {
      if (mounted) {
        setState(() => _savingVlmSettings = false);
      }
    }
  }

  Future<void> _testVlmSettings() async {
    setState(() {
      _testingVlmSettings = true;
      _vlmTestMessage = null;
      _vlmTestPassed = null;
    });
    try {
      final saved = await _vlmSettingsStore.load();
      final apiKey = _vlmApiKeyController.text.trim().isEmpty
          ? saved.apiKey
          : _vlmApiKeyController.text.trim();
      await _vlmOrderService.validateConfiguration(
        VlmSettings(
          endpoint: _vlmEndpointController.text,
          model: _vlmModelController.text,
          apiKey: apiKey,
          hasStoredApiKey: apiKey.isNotEmpty,
        ),
      );
      if (!mounted) {
        return;
      }
      setState(() {
        _vlmTestPassed = true;
        _vlmTestMessage = '配置可用';
      });
    } on OrderRecognitionException catch (error, stackTrace) {
      if (!mounted) {
        return;
      }
      final message = _vlmErrorMessage(error);
      setState(() {
        _vlmTestPassed = false;
        _vlmTestMessage = message;
      });
      showAppErrorSnackBar(
        context,
        message: message,
        error: error,
        stackTrace: stackTrace,
      );
    } catch (error, stackTrace) {
      if (!mounted) {
        return;
      }
      setState(() {
        _vlmTestPassed = false;
        _vlmTestMessage = '配置测试失败：$error';
      });
      showAppErrorSnackBar(
        context,
        message: '配置测试失败',
        error: error,
        stackTrace: stackTrace,
      );
    } finally {
      if (mounted) {
        setState(() => _testingVlmSettings = false);
      }
    }
  }

  Future<void> _resetVlmSettings() async {
    setState(() => _savingVlmSettings = true);
    try {
      await _vlmSettingsStore.resetToDefaults();
      if (!mounted) {
        return;
      }
      await _loadVlmSettings();
      if (!mounted) {
        return;
      }
      setState(() {
        _vlmTestMessage = null;
        _vlmTestPassed = null;
      });
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('已恢复默认订单识别配置')),
      );
    } finally {
      if (mounted) {
        setState(() => _savingVlmSettings = false);
      }
    }
  }

  Future<void> _clearVlmSettings() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('清空订单识别配置'),
        content: const Text(
          'Endpoint、model 和已保存的 API key 都会被清空。',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: const Text('取消'),
          ),
          FilledButton(
            onPressed: () => Navigator.of(context).pop(true),
            child: const Text('清空'),
          ),
        ],
      ),
    );
    if (confirmed != true) {
      return;
    }
    setState(() => _savingVlmSettings = true);
    try {
      await _vlmSettingsStore.clear();
      if (!mounted) {
        return;
      }
      _vlmEndpointController.clear();
      _vlmModelController.clear();
      _vlmApiKeyController.clear();
      setState(() {
        _hasStoredVlmApiKey = false;
        _vlmTestMessage = null;
        _vlmTestPassed = null;
      });
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('订单识别配置已清空')),
      );
    } finally {
      if (mounted) {
        setState(() => _savingVlmSettings = false);
      }
    }
  }

  Future<void> _exportBackupJson() async {
    setState(() => _exportingBackup = true);
    try {
      final fileName = 'vibe-fridge-backup-${_fileTimestamp()}.json';
      final location = await file_selector.getSaveLocation(
        suggestedName: fileName,
        acceptedTypeGroups: [_jsonTypeGroup],
      );
      if (location == null) {
        return;
      }
      final backup = await widget.controller.exportBackup();
      final text = const JsonEncoder.withIndent('  ').convert(backup);
      await _saveTextFile(
        path: location.path,
        fileName: fileName,
        mimeType: 'application/json',
        text: text,
      );
      await widget.controller.markBackupExported();
      if (!mounted) {
        return;
      }
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('备份已导出')),
      );
    } catch (error, stackTrace) {
      if (!mounted) {
        return;
      }
      showAppErrorSnackBar(
        context,
        message: '导出备份失败',
        error: error,
        stackTrace: stackTrace,
      );
    } finally {
      if (mounted) {
        setState(() => _exportingBackup = false);
      }
    }
  }

  Future<void> _restoreBackupJson() async {
    final file = await file_selector.openFile(
      acceptedTypeGroups: [_jsonTypeGroup],
    );
    if (file == null || !mounted) {
      return;
    }
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('恢复备份'),
        content: const Text(
          '会先创建恢复前快照，然后用备份替换当前库存数据。',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: const Text('取消'),
          ),
          FilledButton(
            onPressed: () => Navigator.of(context).pop(true),
            child: const Text('恢复'),
          ),
        ],
      ),
    );
    if (confirmed != true) {
      return;
    }

    setState(() => _restoringBackup = true);
    try {
      final decoded = jsonDecode(await file.readAsString());
      if (decoded is! Map) {
        throw const FormatException('备份文件格式不正确');
      }
      final result = await widget.controller.restoreBackup(
        Map<String, dynamic>.from(decoded),
      );
      if (!mounted) {
        return;
      }
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('恢复完成：${result.restoredRows} 条资料')),
      );
    } catch (error, stackTrace) {
      if (!mounted) {
        return;
      }
      showAppErrorSnackBar(
        context,
        message: '恢复备份失败',
        error: error,
        stackTrace: stackTrace,
      );
    } finally {
      if (mounted) {
        setState(() => _restoringBackup = false);
      }
    }
  }

  Future<void> _exportInventoryCsv() async {
    setState(() => _exportingCsv = true);
    try {
      final fileName = 'vibe-fridge-inventory-${_fileTimestamp()}.csv';
      final location = await file_selector.getSaveLocation(
        suggestedName: fileName,
        acceptedTypeGroups: [_csvTypeGroup],
      );
      if (location == null) {
        return;
      }
      final csv = await widget.controller.exportInventoryCsv();
      await _saveTextFile(
        path: location.path,
        fileName: fileName,
        mimeType: 'text/csv',
        text: csv,
      );
      if (!mounted) {
        return;
      }
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('库存表格已导出')),
      );
    } catch (error, stackTrace) {
      if (!mounted) {
        return;
      }
      showAppErrorSnackBar(
        context,
        message: '导出库存表格失败',
        error: error,
        stackTrace: stackTrace,
      );
    } finally {
      if (mounted) {
        setState(() => _exportingCsv = false);
      }
    }
  }

  Future<void> _saveTextFile({
    required String path,
    required String fileName,
    required String mimeType,
    required String text,
  }) async {
    final file = file_selector.XFile.fromData(
      Uint8List.fromList(utf8.encode(text)),
      mimeType: mimeType,
      name: fileName,
    );
    await file.saveTo(path);
  }

  Future<void> _importLegacyAsset() async {
    setState(() => _importing = true);
    try {
      final preview = await widget.controller.previewLegacyAssetImport();
      if (!mounted) {
        return;
      }
      final options = await showDialog<_LegacyImportOptions>(
        context: context,
        builder: (context) => _LegacyImportPreviewDialog(preview: preview),
      );
      if (options == null) {
        return;
      }

      final result = await widget.controller.importLegacyAsset(
        clearDemoBeforeImport: options.clearDemoData,
      );
      if (!mounted) {
        return;
      }
      setState(() => _lastLegacyImportResult = result);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            result.total == 0 && result.updates.total == 0
                ? '没有可导入的数据'
                : '导入完成：${result.items} 条库存，'
                    '${result.wikis} 个物品资料，${result.tags} 个标签，'
                    '健康检查${result.healthPassed ? '通过' : '未通过'}',
          ),
        ),
      );
    } catch (error, stackTrace) {
      if (!mounted) {
        return;
      }
      showAppErrorSnackBar(
        context,
        message: '导入失败',
        error: error,
        stackTrace: stackTrace,
      );
    } finally {
      if (mounted) {
        setState(() => _importing = false);
      }
    }
  }

  Future<void> _showLegacyImportLog(LegacyImportResult result) async {
    await showDialog<void>(
      context: context,
      builder: (context) => _LegacyImportLogDialog(result: result),
    );
  }

  Future<void> _resetDemoData() async {
    final confirmed = await showAppConfirmDialog(
      context,
      title: '重置示例数据',
      message: '仅清理并重建内置示例资料/库存，'
          '不会删除用户自己创建的数据。',
      confirmLabel: '重置',
    );
    if (!confirmed) {
      return;
    }

    setState(() => _resettingDemoData = true);
    try {
      final clearedRows = await widget.controller.resetDemoData();
      if (!mounted) {
        return;
      }
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            '示例数据已重置，清理 $clearedRows 行旧示例数据',
          ),
        ),
      );
    } catch (error, stackTrace) {
      if (!mounted) {
        return;
      }
      showAppErrorSnackBar(
        context,
        message: '重置示例数据失败',
        error: error,
        stackTrace: stackTrace,
      );
    } finally {
      if (mounted) {
        setState(() => _resettingDemoData = false);
      }
    }
  }

  Future<void> _runAcceptanceChecks() async {
    setState(() => _runningAcceptance = true);
    try {
      final report = await widget.controller.runAcceptanceChecks();
      if (!mounted) {
        return;
      }
      setState(() => _lastAcceptanceReport = report);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            report.passed
                ? '自验收通过：${report.passedCount}/${report.checks.length}'
                : '自验收失败：${report.passedCount}/${report.checks.length}',
          ),
        ),
      );
    } catch (error, stackTrace) {
      if (!mounted) {
        return;
      }
      showAppErrorSnackBar(
        context,
        message: '自验收无法运行',
        error: error,
        stackTrace: stackTrace,
      );
    } finally {
      if (mounted) {
        setState(() => _runningAcceptance = false);
      }
    }
  }
}

class _VlmTestResult extends StatelessWidget {
  const _VlmTestResult({
    required this.message,
    required this.passed,
  });

  final String message;
  final bool passed;

  @override
  Widget build(BuildContext context) {
    final color = passed ? AppColors.success : AppColors.error;
    final backgroundColor =
        passed ? AppColors.successContainer : AppColors.errorContainer;
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
      decoration: BoxDecoration(
        color: backgroundColor,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(
            passed ? Icons.check_circle_outline : Icons.error_outline,
            color: color,
            size: 20,
          ),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              message,
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: color,
                    fontWeight: FontWeight.w700,
                  ),
            ),
          ),
        ],
      ),
    );
  }
}

class _VlmSettingsActions extends StatelessWidget {
  const _VlmSettingsActions({
    required this.saving,
    required this.testing,
    required this.onSave,
    required this.onTest,
    required this.onReset,
    required this.onClear,
  });

  final bool saving;
  final bool testing;
  final VoidCallback onSave;
  final VoidCallback onTest;
  final VoidCallback onReset;
  final VoidCallback onClear;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        SizedBox(
          width: double.infinity,
          child: FilledButton.icon(
            onPressed: saving ? null : onSave,
            icon: saving
                ? const SizedBox(
                    width: 18,
                    height: 18,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : const Icon(Icons.save_outlined),
            label: Text(saving ? '保存中' : '保存订单识别配置'),
          ),
        ),
        const SizedBox(height: 10),
        Row(
          children: [
            Expanded(
              child: OutlinedButton.icon(
                onPressed: testing ? null : onTest,
                icon: testing
                    ? const SizedBox(
                        width: 18,
                        height: 18,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Icon(Icons.network_check_outlined),
                label: Text(testing ? '测试中' : '测试配置'),
              ),
            ),
            const SizedBox(width: 10),
            IconButton.outlined(
              tooltip: '恢复默认配置',
              onPressed: saving ? null : onReset,
              icon: const Icon(Icons.restart_alt_outlined),
            ),
            const SizedBox(width: 8),
            IconButton.outlined(
              tooltip: '清空配置',
              onPressed: saving ? null : onClear,
              icon: const Icon(Icons.delete_outline),
            ),
          ],
        ),
      ],
    );
  }
}

class _DataFileActions extends StatelessWidget {
  const _DataFileActions({
    required this.exportingBackup,
    required this.restoringBackup,
    required this.exportingCsv,
    required this.onExportBackup,
    required this.onRestoreBackup,
    required this.onExportCsv,
  });

  final bool exportingBackup;
  final bool restoringBackup;
  final bool exportingCsv;
  final VoidCallback onExportBackup;
  final VoidCallback onRestoreBackup;
  final VoidCallback onExportCsv;

  @override
  Widget build(BuildContext context) {
    final busy = exportingBackup || restoringBackup || exportingCsv;
    return Column(
      children: [
        Row(
          children: [
            Expanded(
              child: OutlinedButton.icon(
                onPressed: busy ? null : onExportBackup,
                icon: exportingBackup
                    ? const _TinyProgress()
                    : const Icon(Icons.download_outlined),
                label: Text(exportingBackup ? '导出中' : '导出备份'),
              ),
            ),
            const SizedBox(width: 10),
            Expanded(
              child: OutlinedButton.icon(
                onPressed: busy ? null : onRestoreBackup,
                icon: restoringBackup
                    ? const _TinyProgress()
                    : const Icon(Icons.restore_page_outlined),
                label: Text(restoringBackup ? '恢复中' : '恢复备份'),
              ),
            ),
          ],
        ),
        const SizedBox(height: 10),
        SizedBox(
          width: double.infinity,
          child: OutlinedButton.icon(
            onPressed: busy ? null : onExportCsv,
            icon: exportingCsv
                ? const _TinyProgress()
                : const Icon(Icons.table_view_outlined),
            label: Text(exportingCsv ? '导出中' : '导出库存表格'),
          ),
        ),
      ],
    );
  }
}

class _BackupReminderCard extends StatelessWidget {
  const _BackupReminderCard({
    required this.state,
    required this.onExportBackup,
  });

  final BackupReminderState state;
  final VoidCallback? onExportBackup;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: AppColors.warningContainer,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: AppColors.warning.withValues(alpha: 0.35)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Icon(Icons.backup_outlined, color: AppColors.warning),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  '建议导出备份',
                  style: Theme.of(context).textTheme.titleSmall?.copyWith(
                        color: AppColors.textPrimary,
                        fontWeight: FontWeight.w900,
                      ),
                ),
                const SizedBox(height: 3),
                Text(
                  state.message,
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: AppColors.textSecondary,
                      ),
                ),
                if (state.dirtyCount > 0) ...[
                  const SizedBox(height: 3),
                  Text(
                    '累计 ${state.dirtyCount} 行本地变更尚未导出',
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          color: AppColors.textHint,
                        ),
                  ),
                ],
              ],
            ),
          ),
          const SizedBox(width: 8),
          TextButton(
            onPressed: onExportBackup,
            child: const Text('导出'),
          ),
        ],
      ),
    );
  }
}

class _TinyProgress extends StatelessWidget {
  const _TinyProgress();

  @override
  Widget build(BuildContext context) {
    return const SizedBox(
      width: 18,
      height: 18,
      child: CircularProgressIndicator(strokeWidth: 2),
    );
  }
}

class _LegacyImportOptions {
  const _LegacyImportOptions({required this.clearDemoData});

  final bool clearDemoData;
}

class _LegacyImportPreviewDialog extends StatefulWidget {
  const _LegacyImportPreviewDialog({required this.preview});

  final LegacyImportPreview preview;

  @override
  State<_LegacyImportPreviewDialog> createState() =>
      _LegacyImportPreviewDialogState();
}

class _LegacyImportPreviewDialogState
    extends State<_LegacyImportPreviewDialog> {
  bool _clearDemoData = false;

  @override
  Widget build(BuildContext context) {
    final preview = widget.preview;
    return AlertDialog(
      title: const Text('预览旧版库存导入'),
      content: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _ImportCountRow(label: '源数据', counts: preview.source),
            _ImportCountRow(label: '将新增', counts: preview.inserts),
            _ImportCountRow(label: '将更新', counts: preview.updates),
            _ImportCountRow(label: '将跳过', counts: preview.skipped),
            if (preview.failedRows > 0)
              Padding(
                padding: const EdgeInsets.only(top: 8),
                child: StatusPill(
                  label: '${preview.failedRows} 行无法导入',
                  color: AppColors.error,
                  backgroundColor: AppColors.errorContainer,
                ),
              ),
            const SizedBox(height: 12),
            CheckboxListTile(
              value: _clearDemoData,
              contentPadding: EdgeInsets.zero,
              controlAffinity: ListTileControlAffinity.leading,
              onChanged: (value) {
                setState(() => _clearDemoData = value ?? false);
              },
              title: const Text('导入前清空示例资料/库存'),
              subtitle: const Text(
                '只清理内置演示数据，保留分类和用户数据。',
              ),
            ),
            if (preview.logs.isNotEmpty) ...[
              const SizedBox(height: 8),
              Text(
                '冲突预览',
                style: Theme.of(context).textTheme.labelLarge?.copyWith(
                      fontWeight: FontWeight.w900,
                    ),
              ),
              const SizedBox(height: 6),
              for (final log in preview.logs.take(5))
                _LegacyLogLine(entry: log),
              if (preview.logs.length > 5)
                Text(
                  '还有 ${preview.logs.length - 5} 条日志会在导入后展示',
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: AppColors.textHint,
                      ),
                ),
            ],
          ],
        ),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.of(context).pop(),
          child: const Text('取消'),
        ),
        FilledButton(
          onPressed: preview.hasImportableRows
              ? () => Navigator.of(context).pop(
                    _LegacyImportOptions(clearDemoData: _clearDemoData),
                  )
              : null,
          child: const Text('确认导入'),
        ),
      ],
    );
  }
}

class _LegacyImportResultSummary extends StatelessWidget {
  const _LegacyImportResultSummary({
    required this.result,
    required this.onShowLog,
  });

  final LegacyImportResult result;
  final VoidCallback onShowLog;

  @override
  Widget build(BuildContext context) {
    final health = result.healthReport;
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: AppColors.surfaceVariant,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: AppColors.divider),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Text(
                  '上次旧版库存导入',
                  style: Theme.of(context).textTheme.titleSmall?.copyWith(
                        fontWeight: FontWeight.w900,
                      ),
                ),
              ),
              StatusPill(
                label: result.healthPassed ? '健康' : '需检查',
                color:
                    result.healthPassed ? AppColors.success : AppColors.error,
                backgroundColor: result.healthPassed
                    ? AppColors.successContainer
                    : AppColors.errorContainer,
              ),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            '新增 ${result.total} 行，更新 ${result.updates.total} 行，'
            '跳过 ${result.skipped.total} 行，失败 ${result.failedRows} 行',
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: AppColors.textSecondary,
                ),
          ),
          if (result.clearedDemoRows > 0) ...[
            const SizedBox(height: 4),
            Text(
              '已清理 ${result.clearedDemoRows} 行示例数据',
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: AppColors.textSecondary,
                  ),
            ),
          ],
          if (health != null && !health.passed) ...[
            const SizedBox(height: 4),
            Text(
              health.summary,
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: AppColors.error,
                  ),
            ),
          ],
          const SizedBox(height: 8),
          Align(
            alignment: Alignment.centerRight,
            child: TextButton.icon(
              onPressed: onShowLog,
              icon: const Icon(Icons.list_alt_outlined),
              label: const Text('查看日志'),
            ),
          ),
        ],
      ),
    );
  }
}

class _LegacyImportLogDialog extends StatelessWidget {
  const _LegacyImportLogDialog({required this.result});

  final LegacyImportResult result;

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Text('旧版库存导入日志'),
      content: SizedBox(
        width: double.maxFinite,
        child: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              _ImportCountRow(
                label: '新增',
                counts: LegacyImportCounts(
                  categories: result.categories,
                  wikis: result.wikis,
                  items: result.items,
                  tags: result.tags,
                  itemTags: result.itemTags,
                ),
              ),
              _ImportCountRow(label: '更新', counts: result.updates),
              _ImportCountRow(label: '跳过', counts: result.skipped),
              const SizedBox(height: 10),
              if (result.logs.isEmpty)
                Text(
                  '没有详细日志。',
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                        color: AppColors.textSecondary,
                      ),
                )
              else
                for (final entry in result.logs.take(80))
                  _LegacyLogLine(entry: entry),
              if (result.logs.length > 80)
                Text(
                  '仅显示前 80 条，共 ${result.logs.length} 条。',
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: AppColors.textHint,
                      ),
                ),
            ],
          ),
        ),
      ),
      actions: [
        FilledButton(
          onPressed: () => Navigator.of(context).pop(),
          child: const Text('完成'),
        ),
      ],
    );
  }
}

class _ImportCountRow extends StatelessWidget {
  const _ImportCountRow({required this.label, required this.counts});

  final String label;
  final LegacyImportCounts counts;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        children: [
          SizedBox(
            width: 58,
            child: Text(
              label,
              style: Theme.of(context).textTheme.labelLarge?.copyWith(
                    color: AppColors.textSecondary,
                    fontWeight: FontWeight.w800,
                  ),
            ),
          ),
          Expanded(
            child: Text(
              '分类 ${counts.categories} · 资料 ${counts.wikis} · '
              '库存 ${counts.items} · 标签 ${counts.tags}',
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: AppColors.textPrimary,
                  ),
            ),
          ),
        ],
      ),
    );
  }
}

class _LegacyLogLine extends StatelessWidget {
  const _LegacyLogLine({required this.entry});

  final LegacyImportLogEntry entry;

  @override
  Widget build(BuildContext context) {
    final color = switch (entry.action) {
      'inserted' => AppColors.success,
      'updated' => AppColors.primary,
      'failed' => AppColors.error,
      _ => AppColors.textHint,
    };
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(Icons.circle, size: 8, color: color),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              '${_legacyActionLabel(entry.action)} · '
              '${entry.name}：${entry.reason}',
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: AppColors.textSecondary,
                  ),
            ),
          ),
        ],
      ),
    );
  }
}

String _legacyActionLabel(String action) {
  return switch (action) {
    'inserted' => '新增',
    'updated' => '更新',
    'failed' => '失败',
    _ => '跳过',
  };
}

String _vlmErrorMessage(OrderRecognitionException error) {
  switch (error.type) {
    case OrderRecognitionErrorType.configuration:
      return '配置错误：${error.message}';
    case OrderRecognitionErrorType.network:
      return '网络错误：请检查 endpoint 或网络连接';
    case OrderRecognitionErrorType.authentication:
      return '鉴权失败：请检查 API key';
    case OrderRecognitionErrorType.server:
      return '服务端错误：请检查 endpoint 和 model';
    case OrderRecognitionErrorType.responseFormat:
      return '返回不可解析：请确认模型兼容 chat completions';
    case OrderRecognitionErrorType.unsupportedImage:
      return '图片格式不支持：请换 PNG/JPG/WebP 再试';
  }
}

class _AcceptanceResults extends StatelessWidget {
  const _AcceptanceResults({required this.report});

  final AcceptanceReport report;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: report.checks
          .map(
            (check) => _AcceptanceCheckTile(check: check),
          )
          .toList(),
    );
  }
}

class _AcceptanceCheckTile extends StatelessWidget {
  const _AcceptanceCheckTile({required this.check});

  final AcceptanceCheckResult check;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(
            check.passed ? Icons.check_circle : Icons.error_outline,
            color: check.passed ? AppColors.success : AppColors.error,
            size: 20,
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  check.name,
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                        color: AppColors.textPrimary,
                        fontWeight: FontWeight.w700,
                      ),
                ),
                if (check.message != null) ...[
                  const SizedBox(height: 2),
                  Text(
                    check.message!,
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          color: AppColors.error,
                        ),
                  ),
                ],
              ],
            ),
          ),
          const SizedBox(width: 8),
          Text(
            _formatDuration(check.duration),
            style: Theme.of(context).textTheme.labelMedium?.copyWith(
                  color: AppColors.textHint,
                  fontWeight: FontWeight.w700,
                ),
          ),
        ],
      ),
    );
  }
}

String _formatDuration(Duration duration) {
  if (duration.inSeconds >= 1) {
    return '${duration.inSeconds}s';
  }
  return '${duration.inMilliseconds}ms';
}

String _fileTimestamp() {
  final now = DateTime.now();
  String two(int value) => value.toString().padLeft(2, '0');
  return '${now.year}${two(now.month)}${two(now.day)}-'
      '${two(now.hour)}${two(now.minute)}${two(now.second)}';
}

const _jsonTypeGroup = file_selector.XTypeGroup(
  label: '备份文件',
  extensions: ['json'],
  mimeTypes: ['application/json'],
);

const _csvTypeGroup = file_selector.XTypeGroup(
  label: '库存表格',
  extensions: ['csv'],
  mimeTypes: ['text/csv'],
);

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
