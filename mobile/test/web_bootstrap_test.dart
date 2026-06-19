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

  test('web entry manages bootstrap caching and loading screen', () {
    final index = File('web/index.html').readAsStringSync();
    const cacheBustedBootstrapSource =
        r'bootstrapScript.src = `flutter_bootstrap.js?v=${Date.now()}`;';

    expect(
      index,
      contains(
        '<meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">',
      ),
    );
    expect(index, contains('<meta http-equiv="Pragma" content="no-cache">'));
    expect(index, contains('<meta http-equiv="Expires" content="0">'));
    expect(index, contains('document.createElement(\'script\')'));
    expect(index, contains('bootstrapScript.async = true'));
    expect(index, contains(cacheBustedBootstrapSource));
    expect(index, contains('document.body.appendChild(bootstrapScript)'));
    expect(index, contains("loadingScreen.classList.add('is-hidden')"));
    expect(index, contains("loadingScreen.style.opacity = '0'"));
    expect(index, contains("loadingScreen.style.pointerEvents = 'none'"));
    expect(index, contains("loadingScreen.style.visibility = 'hidden'"));
    expect(index, isNot(contains('<script src="flutter_bootstrap.js" async>')));
  });
}
