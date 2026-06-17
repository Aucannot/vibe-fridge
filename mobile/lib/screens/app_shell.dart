import 'dart:async';

import 'package:flutter/material.dart';

import '../data/inventory_controller.dart';
import '../utils/web_route_state.dart';
import 'add_item_screen.dart';
import 'home_screen.dart';
import 'item_detail_screen.dart';
import 'item_wiki_detail_screen.dart';
import 'items_screen.dart';
import 'recipes_screen.dart';
import 'settings_screen.dart';

class AppShell extends StatefulWidget {
  const AppShell({super.key, required this.controller});

  final InventoryController controller;

  @override
  State<AppShell> createState() => _AppShellState();
}

class _AppShellState extends State<AppShell> {
  static const _tabCount = 5;

  int _index = 0;
  final List<Widget?> _screens = List<Widget?>.filled(_tabCount, null);
  final _itemsScreenKey = GlobalKey<ItemsScreenState>();
  StreamSubscription<String>? _webRouteSubscription;

  @override
  void initState() {
    super.initState();
    widget.controller.addListener(_handleControllerChanged);
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) {
        return;
      }
      _initializeWebRouteState();
      _openPendingNotificationTarget();
    });
  }

  @override
  void didUpdateWidget(covariant AppShell oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.controller != widget.controller) {
      oldWidget.controller.removeListener(_handleControllerChanged);
      widget.controller.addListener(_handleControllerChanged);
      for (var index = 0; index < _screens.length; index += 1) {
        _screens[index] = null;
      }
    }
  }

  @override
  void dispose() {
    _webRouteSubscription?.cancel();
    widget.controller.removeListener(_handleControllerChanged);
    super.dispose();
  }

  void _select(int index) {
    setWebRouteState(_routeForIndex(index));
    setState(() {
      if (index == 0) {
        _screens[0] = null;
      }
      _index = index;
    });
  }

  void _openItems(ItemsScreenRequest request) {
    setWebRouteState(_routeForItemsRequest(request));
    setState(() {
      _index = 1;
    });
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) {
        return;
      }
      _itemsScreenKey.currentState?.applyRequest(request);
    });
  }

  void _initializeWebRouteState() {
    if (!supportsWebRouteState) {
      return;
    }
    final route = getWebRouteState();
    if (route.isEmpty) {
      setWebRouteState(_routeForIndex(_index), replace: true);
    } else {
      _applyWebRoute(route);
    }
    _webRouteSubscription = getWebRouteStateChanges().listen(_applyWebRoute);
  }

  void _applyWebRoute(String route) {
    final uri = Uri.tryParse(route);
    if (uri == null || !mounted) {
      return;
    }
    final index = _indexForWebRoute(uri);
    setState(() {
      if (index == 0) {
        _screens[0] = null;
      }
      _index = index;
    });
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) {
        return;
      }
      Navigator.of(context).popUntil((route) => route.isFirst);
      if (index == 1) {
        _itemsScreenKey.currentState?.applyRequest(_itemsRequestFromUri(uri));
        _openItemsDetailForRoute(uri);
      }
    });
  }

  int _indexForWebRoute(Uri uri) {
    final segment = uri.pathSegments.isEmpty ? 'home' : uri.pathSegments.first;
    return switch (segment) {
      'items' => 1,
      'add' => 2,
      'recipes' => 3,
      'settings' => 4,
      _ => 0,
    };
  }

  ItemsScreenRequest _itemsRequestFromUri(Uri uri) {
    return ItemsScreenRequest(
      target: _itemsTargetFromQuery(uri.queryParameters['view']),
      focus: _itemsFocusFromQuery(uri.queryParameters['focus']),
      keyword: uri.queryParameters['q'],
      categoryId: uri.queryParameters['category'],
    );
  }

  ItemsScreenTarget _itemsTargetFromQuery(String? value) {
    return switch (value) {
      'history' => ItemsScreenTarget.history,
      'shopping' => ItemsScreenTarget.shopping,
      _ => ItemsScreenTarget.catalog,
    };
  }

  ItemsScreenFocus? _itemsFocusFromQuery(String? value) {
    return switch (value) {
      'expired' => ItemsScreenFocus.expired,
      'dueToday' => ItemsScreenFocus.dueToday,
      'reminderDue' => ItemsScreenFocus.reminderDue,
      'expiring' => ItemsScreenFocus.expiring,
      'cleanup' => ItemsScreenFocus.cleanup,
      _ => null,
    };
  }

  Future<void> _openItemsDetailForRoute(Uri uri) async {
    if (uri.pathSegments.length < 3 || uri.pathSegments.first != 'items') {
      return;
    }
    final kind = uri.pathSegments[1];
    final id = uri.pathSegments[2];
    if (id.isEmpty) {
      return;
    }
    if (kind == 'item') {
      final route = '/items/item/$id';
      final detail = Navigator.of(context).push(
        MaterialPageRoute(
          settings: RouteSettings(name: route),
          builder: (_) => ItemDetailScreen(
            controller: widget.controller,
            itemId: id,
          ),
        ),
      );
      setWebRouteState(route, replace: true);
      await detail;
      setWebRouteState('/items', replace: true);
      return;
    }
    if (kind == 'wiki') {
      final route = '/items/wiki/$id';
      final detail = Navigator.of(context).push(
        MaterialPageRoute(
          settings: RouteSettings(name: route),
          builder: (_) => ItemWikiDetailScreen(
            controller: widget.controller,
            wikiId: id,
          ),
        ),
      );
      setWebRouteState(route, replace: true);
      await detail;
      setWebRouteState('/items', replace: true);
    }
  }

  String _routeForIndex(int index) {
    return switch (index) {
      1 => '/items',
      2 => '/add',
      3 => '/recipes',
      4 => '/settings',
      _ => '/home',
    };
  }

  String _routeForItemsRequest(ItemsScreenRequest request) {
    final query = <String, String>{};
    final view = switch (request.target) {
      ItemsScreenTarget.catalog => null,
      ItemsScreenTarget.history => 'history',
      ItemsScreenTarget.shopping => 'shopping',
    };
    final focus = switch (request.focus) {
      ItemsScreenFocus.expired => 'expired',
      ItemsScreenFocus.dueToday => 'dueToday',
      ItemsScreenFocus.reminderDue => 'reminderDue',
      ItemsScreenFocus.expiring => 'expiring',
      ItemsScreenFocus.cleanup => 'cleanup',
      null => null,
    };
    if (view != null) {
      query['view'] = view;
    }
    if (focus != null) {
      query['focus'] = focus;
    }
    if (request.keyword != null && request.keyword!.isNotEmpty) {
      query['q'] = request.keyword!;
    }
    if (request.categoryId != null && request.categoryId!.isNotEmpty) {
      query['category'] = request.categoryId!;
    }
    return Uri(
      path: '/items',
      queryParameters: query.isEmpty ? null : query,
    ).toString();
  }

  void _handleControllerChanged() {
    final itemId = widget.controller.consumeNotificationTappedItemId();
    if (itemId == null || !mounted) {
      return;
    }
    _openNotificationTarget(itemId);
  }

  void _openPendingNotificationTarget() {
    final itemId = widget.controller.consumeNotificationTappedItemId();
    if (itemId == null || !mounted) {
      return;
    }
    _openNotificationTarget(itemId);
  }

  void _openNotificationTarget(String itemId) {
    final route = '/items/item/$itemId';
    setWebRouteState(route);
    setState(() => _index = 1);
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) {
        return;
      }
      Navigator.of(context)
          .push(
        MaterialPageRoute(
          settings: RouteSettings(name: route),
          builder: (_) => ItemDetailScreen(
            controller: widget.controller,
            itemId: itemId,
          ),
        ),
      )
          .then((_) {
        setWebRouteState('/items', replace: true);
      });
      setWebRouteState(route, replace: true);
    });
  }

  Widget _screenForIndex(int index) {
    final existing = _screens[index];
    if (existing != null) {
      return existing;
    }

    final screen = switch (index) {
      0 => HomeScreen(
          controller: widget.controller,
          onAddPressed: () => _select(2),
          onTabSelected: _select,
          onItemsRequest: _openItems,
        ),
      1 => ItemsScreen(
          key: _itemsScreenKey,
          controller: widget.controller,
        ),
      2 => AddItemScreen(
          controller: widget.controller,
          onItemSaved: () => _select(1),
        ),
      3 => RecipesScreen(controller: widget.controller),
      4 => SettingsScreen(controller: widget.controller),
      _ => const SizedBox.shrink(),
    };
    _screens[index] = screen;
    return screen;
  }

  Widget _stackChild(int index) {
    if (index == _index || _screens[index] != null) {
      return _screenForIndex(index);
    }
    return const SizedBox.shrink();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: AnimatedBuilder(
          animation: widget.controller,
          builder: (context, _) {
            if (widget.controller.isLoading &&
                widget.controller.activeItems.isEmpty) {
              return const Center(child: CircularProgressIndicator());
            }
            return IndexedStack(
              index: _index,
              children: List.generate(_tabCount, _stackChild),
            );
          },
        ),
      ),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _index,
        onDestinationSelected: _select,
        destinations: const [
          NavigationDestination(
            icon: Icon(Icons.home_outlined),
            selectedIcon: Icon(Icons.home),
            label: '首页',
          ),
          NavigationDestination(
            icon: Icon(Icons.kitchen_outlined),
            selectedIcon: Icon(Icons.kitchen),
            label: '物品',
          ),
          NavigationDestination(
            icon: Icon(Icons.add_circle_outline),
            selectedIcon: Icon(Icons.add_circle),
            label: '添加',
          ),
          NavigationDestination(
            icon: Icon(Icons.restaurant_menu_outlined),
            selectedIcon: Icon(Icons.restaurant_menu),
            label: '食谱',
          ),
          NavigationDestination(
            icon: Icon(Icons.settings_outlined),
            selectedIcon: Icon(Icons.settings),
            label: '设置',
          ),
        ],
      ),
    );
  }
}
