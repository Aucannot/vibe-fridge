import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  test('web database avoids shared-worker factory', () {
    final source = File('lib/data/app_database.dart').readAsStringSync();

    expect(
      source,
      contains('return databaseFactoryFfiWebBasicWebWorker;'),
      reason: 'The in-app browser can hang while starting the shared worker.',
    );
    expect(
      source,
      isNot(contains('return databaseFactoryFfiWeb;')),
    );
  });
}
