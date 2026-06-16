import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:vibe_fridge/theme/app_theme.dart';

void main() {
  testWidgets('material shell smoke renders app chrome', (tester) async {
    await tester.pumpWidget(
      MaterialApp(
        debugShowCheckedModeBanner: false,
        theme: AppTheme.light(),
        home: Scaffold(
          body: const Center(child: Text('vibe-fridge')),
          bottomNavigationBar: NavigationBar(
            destinations: const [
              NavigationDestination(
                icon: Icon(Icons.home_outlined),
                label: '首页',
              ),
              NavigationDestination(
                icon: Icon(Icons.add_circle_outline),
                label: '添加',
              ),
            ],
          ),
        ),
      ),
    );

    expect(find.text('vibe-fridge'), findsOneWidget);
    expect(find.text('首页'), findsOneWidget);
    expect(find.text('添加'), findsOneWidget);
  });
}
