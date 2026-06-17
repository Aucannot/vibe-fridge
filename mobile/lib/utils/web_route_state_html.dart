import 'dart:async';
import 'dart:js_interop';

import 'package:web/web.dart' as web;

bool get supportsWebRouteState => true;

String getWebRouteState() => _currentRoute();

Stream<String> getWebRouteStateChanges() {
  late final web.EventListener popStateListener;
  late final web.EventListener hashChangeListener;
  final controller = StreamController<String>.broadcast();

  controller.onListen = () {
    popStateListener = ((web.Event event) {
      controller.add(_currentRoute());
    }).toJS;
    hashChangeListener = ((web.Event event) {
      controller.add(_currentRoute());
    }).toJS;
    web.window.addEventListener('popstate', popStateListener);
    web.window.addEventListener('hashchange', hashChangeListener);
  };
  controller.onCancel = () async {
    web.window.removeEventListener('popstate', popStateListener);
    web.window.removeEventListener('hashchange', hashChangeListener);
  };

  return controller.stream;
}

void setWebRouteState(String route, {bool replace = false}) {
  final nextRoute = _normalizeRoute(route);
  final currentRoute = _currentRoute();
  final location = web.window.location;
  final hasHashRoute = location.hash.isNotEmpty;
  if (currentRoute == nextRoute && !hasHashRoute) {
    return;
  }

  final nextUrl = '${location.pathname}${_queryForRoute(nextRoute)}';
  if (replace || currentRoute == nextRoute) {
    web.window.history.replaceState(null, '', nextUrl);
  } else {
    web.window.history.pushState(null, '', nextUrl);
  }
  Timer.run(() => _clearHashRouteIfStillCurrent(nextRoute, nextUrl));
}

String _currentRoute() {
  final search = web.window.location.search;
  if (search.isEmpty || search == '?') {
    return '';
  }
  final query = Uri.splitQueryString(search.substring(1));
  final route = query['route'];
  if (route == null || route.trim().isEmpty) {
    return '';
  }
  final routeQuery = Map<String, String>.from(query)..remove('route');
  return Uri(
    path: _normalizeRoute(route),
    queryParameters: routeQuery.isEmpty ? null : routeQuery,
  ).toString();
}

String _queryForRoute(String route) {
  final uri = Uri.parse(route);
  final routeValue =
      uri.pathSegments.isEmpty ? 'home' : uri.pathSegments.join('/');
  final query = <String, String>{'route': routeValue};
  query.addAll(uri.queryParameters);
  return '?${Uri(queryParameters: query).query}';
}

String _normalizeRoute(String route) {
  final trimmed = route.trim();
  if (trimmed.isEmpty) {
    return '/home';
  }
  return trimmed.startsWith('/') ? trimmed : '/$trimmed';
}

void _clearHashRouteIfStillCurrent(String route, String url) {
  if (web.window.location.hash.isEmpty || _currentRoute() != route) {
    return;
  }
  web.window.history.replaceState(null, '', url);
}
