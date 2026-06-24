import 'dart:async';

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

const bootstrapInitializationTimeout = Duration(seconds: 12);

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const VibeFridgeBootstrapApp());
}

@visibleForTesting
Future<InventoryController> loadInventoryControllerForBootstrap() async {
  final database = await withBootstrapTimeout(
    AppDatabase.open(),
    operation: '打开本地资料',
  );
  final repository = InventoryRepository(database);
  final controller = InventoryController(repository);
  await withBootstrapTimeout(
    controller.initialize(),
    operation: '加载库存资料',
  );
  registerDebugServiceExtensions(controller);
  return controller;
}

typedef BootstrapControllerLoader = Future<InventoryController> Function();

class VibeFridgeBootstrapApp extends StatefulWidget {
  const VibeFridgeBootstrapApp({
    super.key,
    this.controllerLoader = loadInventoryControllerForBootstrap,
  });

  final BootstrapControllerLoader controllerLoader;

  @override
  State<VibeFridgeBootstrapApp> createState() => _VibeFridgeBootstrapAppState();
}

class _VibeFridgeBootstrapAppState extends State<VibeFridgeBootstrapApp> {
  InventoryController? _controller;
  Object? _error;
  StackTrace? _stackTrace;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => _loadController());
  }

  Future<void> _loadController() async {
    try {
      final controller = await widget.controllerLoader();
      if (!mounted) {
        return;
      }
      setState(() => _controller = controller);
    } catch (error, stackTrace) {
      if (!mounted) {
        return;
      }
      setState(() {
        _error = error;
        _stackTrace = stackTrace;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final controller = _controller;
    if (controller != null) {
      return VibeFridgeApp(controller: controller);
    }
    final error = _error;
    final stackTrace = _stackTrace;
    if (error != null && stackTrace != null) {
      return VibeFridgeBootstrapErrorApp(
        error: error,
        stackTrace: stackTrace,
      );
    }
    return const VibeFridgeBootstrapLoadingApp();
  }
}

@visibleForTesting
Future<T> withBootstrapTimeout<T>(
  Future<T> future, {
  required String operation,
  Duration timeout = bootstrapInitializationTimeout,
}) {
  return future.timeout(
    timeout,
    onTimeout: () {
      throw TimeoutException('启动初始化超时：$operation', timeout);
    },
  );
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

class VibeFridgeBootstrapLoadingApp extends StatelessWidget {
  const VibeFridgeBootstrapLoadingApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'vibe-fridge',
      theme: AppTheme.light(),
      themeMode: ThemeMode.light,
      home: Scaffold(
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
                        color: AppColors.primaryContainer,
                        borderRadius: BorderRadius.circular(AppRadii.large),
                      ),
                      child: const Icon(
                        Icons.kitchen_outlined,
                        color: AppColors.primary,
                      ),
                    ),
                    const SizedBox(height: AppSpacing.fieldGap),
                    Text(
                      '正在整理你的库存',
                      style:
                          Theme.of(context).textTheme.headlineSmall?.copyWith(
                                color: AppColors.textPrimary,
                                fontWeight: FontWeight.w900,
                              ),
                    ),
                    const SizedBox(height: AppSpacing.cardGap),
                    Text(
                      '这通常只需要几秒。',
                      style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                            color: AppColors.textSecondary,
                          ),
                    ),
                    const SizedBox(height: AppSpacing.sectionGap),
                    const LinearProgressIndicator(minHeight: 4),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
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
