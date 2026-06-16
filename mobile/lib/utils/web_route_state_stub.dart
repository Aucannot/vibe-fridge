import 'dart:async';

bool get supportsWebRouteState => false;

String getWebRouteState() => '';

Stream<String> getWebRouteStateChanges() => const Stream.empty();

void setWebRouteState(String route, {bool replace = false}) {}
