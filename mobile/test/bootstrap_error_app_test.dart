import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:vibe_fridge/data/inventory_controller.dart';
import 'package:vibe_fridge/main.dart';

void main() {
  test('bootstrap timeout reports stalled initialization', () async {
    final stalled = Completer<void>();

    await expectLater(
      withBootstrapTimeout(
        stalled.future,
        operation: '测试初始化',
        timeout: const Duration(milliseconds: 1),
      ),
      throwsA(
        isA<TimeoutException>()
            .having((error) => error.message, 'message', contains('测试初始化'))
            .having(
              (error) => error.duration,
              'duration',
              const Duration(milliseconds: 1),
            ),
      ),
    );
  });

  testWidgets('bootstrap app paints loading before initialization finishes',
      (tester) async {
    final stalled = Completer<InventoryController>();

    await tester.pumpWidget(
      VibeFridgeBootstrapApp(
        controllerLoader: () => stalled.future,
      ),
    );
    await tester.pump();

    expect(find.text('正在整理你的库存'), findsOneWidget);
    expect(find.text('这通常只需要几秒。'), findsOneWidget);
    expect(find.byType(LinearProgressIndicator), findsOneWidget);
  });

  testWidgets('bootstrap app shows user-safe error when loading fails',
      (tester) async {
    await tester.pumpWidget(
      VibeFridgeBootstrapApp(
        controllerLoader: () async {
          throw StateError('SQLite open failed: /tmp/private-path.db');
        },
      ),
    );
    await tester.pump();
    await tester.pump();

    expect(find.text('vibe-fridge 启动失败'), findsOneWidget);
    expect(find.text('复制错误详情'), findsOneWidget);
    expect(find.textContaining('SQLite'), findsNothing);
    expect(find.textContaining('/tmp/private-path.db'), findsNothing);
  });

  testWidgets('bootstrap error page hides technical details by default',
      (tester) async {
    await tester.pumpWidget(
      VibeFridgeBootstrapErrorApp(
        error: StateError('SQLite open failed: /tmp/private-path.db'),
        stackTrace: StackTrace.fromString(
          'package:vibe_fridge/data/app_database.dart 42:13',
        ),
      ),
    );

    expect(find.text('vibe-fridge 启动失败'), findsOneWidget);
    expect(find.text('复制错误详情'), findsOneWidget);
    expect(
      find.text('错误详情只会在你点击复制时写入剪贴板，页面不会直接展示诊断内容。'),
      findsOneWidget,
    );
    expect(find.textContaining('SQLite'), findsNothing);
    expect(find.textContaining('/tmp/private-path.db'), findsNothing);
    expect(find.textContaining('app_database.dart'), findsNothing);
  });
}
