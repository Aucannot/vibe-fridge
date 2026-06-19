import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter/services.dart';

import 'data/app_database.dart';
import 'data/debug_service_extensions.dart';
import 'data/inventory_controller.dart';
import 'data/inventory_repository.dart';
import 'screens/app_shell.dart';
import 'theme/app_theme.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  try {
    final database = await AppDatabase.open();
    final repository = InventoryRepository(database);
    final controller = InventoryController(repository);
    await controller.initialize();
    registerDebugServiceExtensions(controller);

    runApp(VibeFridgeApp(controller: controller));
  } catch (error, stackTrace) {
    runApp(
      VibeFridgeBootstrapErrorApp(
        error: error,
        stackTrace: stackTrace,
      ),
    );
  }
}

class VibeFridgeApp extends StatelessWidget {
  const VibeFridgeApp({super.key, required this.controller});

  final InventoryController controller;

  @override
  Widget build(BuildContext context) {
    return MaterialApp.router(
      debugShowCheckedModeBanner: false,
      title: 'vibe-fridge',
      theme: AppTheme.light(),
      themeMode: AppTheme.supportsDarkMode ? ThemeMode.system : ThemeMode.light,
      locale: const Locale('zh', 'CN'),
      supportedLocales: const [
        Locale('zh', 'CN'),
        Locale('en', 'US'),
      ],
      localizationsDelegates: const [
        GlobalMaterialLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
      ],
      routeInformationParser: const _VibeFridgeRouteParser(),
      routerDelegate: _VibeFridgeRouterDelegate(controller),
    );
  }
}

class _VibeFridgeRouteParser extends RouteInformationParser<String> {
  const _VibeFridgeRouteParser();

  @override
  Future<String> parseRouteInformation(
    RouteInformation routeInformation,
  ) {
    return SynchronousFuture(routeInformation.uri.toString());
  }

  @override
  RouteInformation restoreRouteInformation(String configuration) {
    return RouteInformation(uri: Uri.parse(configuration));
  }
}

class _VibeFridgeRouterDelegate extends RouterDelegate<String>
    with ChangeNotifier, PopNavigatorRouterDelegateMixin<String> {
  _VibeFridgeRouterDelegate(this.controller);

  final InventoryController controller;

  @override
  final GlobalKey<NavigatorState> navigatorKey = GlobalKey<NavigatorState>();

  String _configuration = '/';

  @override
  String get currentConfiguration => _configuration;

  @override
  Future<void> setNewRoutePath(String configuration) async {
    _configuration = configuration;
    notifyListeners();
  }

  @override
  Widget build(BuildContext context) {
    return Navigator(
      key: navigatorKey,
      pages: [
        MaterialPage<void>(
          child: AppShell(controller: controller),
        ),
      ],
      onDidRemovePage: (_) {},
    );
  }
}

class VibeFridgeBootstrapErrorApp extends StatelessWidget {
  const VibeFridgeBootstrapErrorApp({
    super.key,
    required this.error,
    required this.stackTrace,
  });

  final Object error;
  final StackTrace stackTrace;

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'vibe-fridge',
      theme: AppTheme.light(),
      themeMode: ThemeMode.light,
      home: _BootstrapErrorScreen(
        error: error,
        stackTrace: stackTrace,
      ),
    );
  }
}

class _BootstrapErrorScreen extends StatelessWidget {
  const _BootstrapErrorScreen({
    required this.error,
    required this.stackTrace,
  });

  final Object error;
  final StackTrace stackTrace;

  String get _details => '$error\n\n$stackTrace';

  void _copyDetails(BuildContext context) {
    Clipboard.setData(ClipboardData(text: _details));
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('错误详情已复制')),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(
              maxWidth: AppBreakpoints.contentMaxWidth,
            ),
            child: Padding(
              padding: const EdgeInsets.all(AppSpacing.pageHorizontal),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Container(
                    width: AppSizes.emptyIconContainer,
                    height: AppSizes.emptyIconContainer,
                    decoration: BoxDecoration(
                      color: AppColors.errorContainer,
                      borderRadius: BorderRadius.circular(AppRadii.large),
                    ),
                    child: const Icon(
                      Icons.error_outline,
                      color: AppColors.error,
                    ),
                  ),
                  const SizedBox(height: AppSpacing.fieldGap),
                  Text(
                    'vibe-fridge 启动失败',
                    style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                          color: AppColors.textPrimary,
                          fontWeight: FontWeight.w900,
                        ),
                  ),
                  const SizedBox(height: AppSpacing.cardGap),
                  Text(
                    '本地资料初始化没有完成。'
                    '请复制错误详情后反馈，'
                    '避免反复重装造成数据丢失。',
                    style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                          color: AppColors.textSecondary,
                        ),
                  ),
                  const SizedBox(height: AppSpacing.sectionGap),
                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.all(AppSpacing.cardPadding),
                    decoration: BoxDecoration(
                      color: AppColors.surface,
                      border: Border.all(color: AppColors.divider),
                      borderRadius: BorderRadius.circular(AppRadii.card),
                    ),
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Icon(
                          Icons.privacy_tip_outlined,
                          color: AppColors.primary,
                        ),
                        const SizedBox(width: AppSpacing.cardGap),
                        Expanded(
                          child: Text(
                            '错误详情只会在你点击复制时写入剪贴板，'
                            '页面不会直接展示诊断内容。',
                            style:
                                Theme.of(context).textTheme.bodySmall?.copyWith(
                                      color: AppColors.textSecondary,
                                    ),
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: AppSpacing.fieldGap),
                  SizedBox(
                    width: double.infinity,
                    child: FilledButton.icon(
                      onPressed: () => _copyDetails(context),
                      icon: const Icon(Icons.copy_outlined),
                      label: const Text('复制错误详情'),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
