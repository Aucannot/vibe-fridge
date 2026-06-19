import 'dart:async';

bool get supportsWebRouteState => false;

String getWebRouteState() => '';

Stream<String> getWebRouteStateChanges() => const Stream.empty();

bool isCurrentWebRoute(String route) => false;

void setWebRouteState(String route, {bool replace = false}) {}
