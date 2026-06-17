import 'package:flutter_test/flutter_test.dart';
import 'package:vibe_fridge/main.dart';

void main() {
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
