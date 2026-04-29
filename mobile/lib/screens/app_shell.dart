import 'package:flutter/material.dart';

import '../data/inventory_controller.dart';
import 'add_item_screen.dart';
import 'home_screen.dart';
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
  int _index = 0;

  void _select(int index) {
    setState(() {
      _index = index;
    });
  }

  @override
  Widget build(BuildContext context) {
    final screens = [
      HomeScreen(controller: widget.controller, onAddPressed: () => _select(2)),
      ItemsScreen(controller: widget.controller),
      AddItemScreen(
        controller: widget.controller,
        onItemSaved: () => _select(1),
      ),
      const RecipesScreen(),
      SettingsScreen(controller: widget.controller),
    ];

    return Scaffold(
      body: SafeArea(
        child: AnimatedBuilder(
          animation: widget.controller,
          builder: (context, _) {
            if (widget.controller.isLoading && widget.controller.activeItems.isEmpty) {
              return const Center(child: CircularProgressIndicator());
            }
            return IndexedStack(index: _index, children: screens);
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
