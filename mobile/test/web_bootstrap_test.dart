import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  test('web bootstrap clears stale service workers without registering one',
      () {
    final script = File('web/flutter_bootstrap.js').readAsStringSync();

    expect(script, contains('{{flutter_js}}'));
    expect(script, contains('{{flutter_build_config}}'));
    expect(script, isNot(contains('serviceWorkerSettings')));
    expect(script, isNot(contains('{{flutter_service_worker_version}}')));
    expect(script, contains('navigator.serviceWorker.getRegistrations()'));
    expect(script, contains('registration.unregister()'));
    expect(script, contains("cacheName.startsWith('flutter-')"));
    expect(script, contains('caches.delete(cacheName)'));
    expect(script, contains('window.location.reload()'));
    expect(script, contains('_flutter.loader.load();'));
  });
}
