import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:vibe_fridge/widgets/app_cards.dart';

void main() {
  testWidgets('error snackbar keeps technical details behind explicit copy', (
    tester,
  ) async {
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: Builder(
            builder: (context) => TextButton(
              onPressed: () => showAppErrorSnackBar(
                context,
                message: '保存失败',
                error: StateError('SQLite internal path'),
                stackTrace: StackTrace.fromString(
                  'package:vibe_fridge/internal.dart 1:1',
                ),
              ),
              child: const Text('触发错误'),
            ),
          ),
        ),
      ),
    );

    await tester.tap(find.text('触发错误'));
    await tester.pump();

    expect(find.text('保存失败'), findsOneWidget);
    expect(find.text('复制详情'), findsOneWidget);
    expect(find.textContaining('SQLite'), findsNothing);
    expect(find.textContaining('internal.dart'), findsNothing);
  });
}
