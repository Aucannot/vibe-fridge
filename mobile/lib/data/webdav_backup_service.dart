import 'dart:convert';

import 'package:http/http.dart' as http;

import 'webdav_backup_store.dart';

class WebDavBackupService {
  WebDavBackupService({http.Client? client})
      : _client = client ?? http.Client();

  final http.Client _client;

  void close() {
    _client.close();
  }

  Future<void> validateConfiguration(WebDavBackupSettings settings) async {
    final directoryUri = await _ensureDirectory(settings);
    final response = await _send(
      'PROPFIND',
      directoryUri,
      settings,
      headers: const {'Depth': '0'},
      body: _propfindBody,
    );
    _throwForHttpFailure(response);
  }

  Future<WebDavBackupUploadResult> uploadBackup({
    required WebDavBackupSettings settings,
    required String fileName,
    required String backupJson,
  }) async {
    _validateBackupFileName(fileName);
    final directoryUri = await _ensureDirectory(settings);
    final fileUri = _appendPathSegment(directoryUri, fileName);
    final response = await _send(
      'PUT',
      fileUri,
      settings,
      headers: const {'Content-Type': 'application/json; charset=utf-8'},
      body: backupJson,
    );
    _throwForHttpFailure(response, successCodes: const {200, 201, 204});
    return WebDavBackupUploadResult(fileName: fileName, uri: fileUri);
  }

  Future<WebDavBackupDownloadResult> downloadLatestBackup(
    WebDavBackupSettings settings,
  ) async {
    final directoryUri = await _ensureDirectory(settings);
    final listResponse = await _send(
      'PROPFIND',
      directoryUri,
      settings,
      headers: const {'Depth': '1'},
      body: _propfindBody,
    );
    _throwForHttpFailure(listResponse);

    final entries = _parseBackupEntries(
      utf8.decode(listResponse.bodyBytes),
      directoryUri,
    );
    if (entries.isEmpty) {
      throw const WebDavBackupException(
        '没有找到由本应用上传的备份文件',
        type: WebDavBackupErrorType.notFound,
      );
    }
    entries.sort((left, right) => right.fileName.compareTo(left.fileName));
    final latest = entries.first;
    final downloadResponse = await _send('GET', latest.uri, settings);
    _throwForHttpFailure(downloadResponse);
    return WebDavBackupDownloadResult(
      fileName: latest.fileName,
      uri: latest.uri,
      backupJson: utf8.decode(downloadResponse.bodyBytes),
    );
  }

  Future<Uri> _ensureDirectory(WebDavBackupSettings settings) async {
    _validateSettings(settings);
    var current = _baseUri(settings.serverUrl);
    for (final segment in _remoteDirectorySegments(settings.remoteDirectory)) {
      current = _appendPathSegment(current, segment, trailingSlash: true);
      final response = await _send('MKCOL', current, settings);
      if (response.statusCode == 201 ||
          response.statusCode == 200 ||
          response.statusCode == 204 ||
          response.statusCode == 405) {
        continue;
      }
      _throwForHttpFailure(response, successCodes: const {201, 405});
    }
    return _ensureTrailingSlash(current);
  }

  Future<http.Response> _send(
    String method,
    Uri uri,
    WebDavBackupSettings settings, {
    Map<String, String> headers = const {},
    String? body,
  }) async {
    final request = http.Request(method, uri);
    request.headers.addAll(_authHeaders(settings));
    request.headers.addAll(headers);
    if (body != null) {
      request.bodyBytes = utf8.encode(body);
    }
    try {
      final streamed = await _client.send(request);
      return http.Response.fromStream(streamed);
    } on http.ClientException catch (error) {
      throw WebDavBackupException(
        '网络错误：${error.message}',
        type: WebDavBackupErrorType.network,
      );
    } on Exception catch (error) {
      throw WebDavBackupException(
        '网络错误：$error',
        type: WebDavBackupErrorType.network,
      );
    }
  }

  Map<String, String> _authHeaders(WebDavBackupSettings settings) {
    final username = settings.username.trim();
    final password = settings.password.trim();
    if (username.isEmpty && password.isEmpty) {
      return const {};
    }
    final token = base64Encode(utf8.encode('$username:$password'));
    return {'Authorization': 'Basic $token'};
  }

  Uri _baseUri(String rawUrl) {
    final uri = Uri.tryParse(rawUrl.trim());
    if (uri == null ||
        !uri.hasScheme ||
        (uri.scheme != 'http' && uri.scheme != 'https') ||
        uri.host.isEmpty) {
      throw const WebDavBackupException(
        '请填写完整的 http 或 https WebDAV 服务地址',
        type: WebDavBackupErrorType.configuration,
      );
    }
    if (uri.hasQuery || uri.hasFragment) {
      throw const WebDavBackupException(
        'WebDAV 服务地址不能包含查询参数或锚点',
        type: WebDavBackupErrorType.configuration,
      );
    }
    return _ensureTrailingSlash(uri);
  }

  Uri _appendPathSegment(
    Uri uri,
    String segment, {
    bool trailingSlash = false,
  }) {
    final baseSegments = uri.pathSegments
        .where((part) => part.isNotEmpty)
        .toList(growable: true);
    baseSegments.add(segment);
    final encodedPath = '/${baseSegments.map(Uri.encodeComponent).join('/')}'
        '${trailingSlash ? '/' : ''}';
    return uri.replace(path: encodedPath, query: null, fragment: null);
  }

  Uri _ensureTrailingSlash(Uri uri) {
    if (uri.path.endsWith('/')) {
      return uri.replace(query: null, fragment: null);
    }
    return uri.replace(path: '${uri.path}/', query: null, fragment: null);
  }

  List<String> _remoteDirectorySegments(String remoteDirectory) {
    final normalized = remoteDirectory.trim().replaceAll('\\', '/');
    final segments = normalized
        .split('/')
        .map((segment) => segment.trim())
        .where((segment) => segment.isNotEmpty)
        .toList(growable: false);
    for (final segment in segments) {
      if (segment == '.' || segment == '..') {
        throw const WebDavBackupException(
          '备份目录不能包含 . 或 ..',
          type: WebDavBackupErrorType.configuration,
        );
      }
    }
    return segments;
  }

  void _validateSettings(WebDavBackupSettings settings) {
    if (settings.serverUrl.trim().isEmpty) {
      throw const WebDavBackupException(
        '请先填写 WebDAV 服务地址',
        type: WebDavBackupErrorType.configuration,
      );
    }
    _remoteDirectorySegments(settings.remoteDirectory);
  }

  void _validateBackupFileName(String fileName) {
    if (!fileName.startsWith('vibe-fridge-backup-') ||
        !fileName.endsWith('.json') ||
        fileName.contains('/') ||
        fileName.contains('\\')) {
      throw const WebDavBackupException(
        '备份文件名不正确',
        type: WebDavBackupErrorType.configuration,
      );
    }
  }

  void _throwForHttpFailure(
    http.Response response, {
    Set<int> successCodes = const {200, 207},
  }) {
    if (successCodes.contains(response.statusCode)) {
      return;
    }
    if (response.statusCode == 401 || response.statusCode == 403) {
      throw WebDavBackupException(
        'HTTP ${response.statusCode}',
        type: WebDavBackupErrorType.authentication,
      );
    }
    if (response.statusCode == 404) {
      throw const WebDavBackupException(
        'HTTP 404',
        type: WebDavBackupErrorType.notFound,
      );
    }
    if (response.statusCode >= 500) {
      throw WebDavBackupException(
        'HTTP ${response.statusCode}',
        type: WebDavBackupErrorType.server,
      );
    }
    throw WebDavBackupException(
      'HTTP ${response.statusCode}',
      type: WebDavBackupErrorType.server,
    );
  }

  List<_WebDavBackupEntry> _parseBackupEntries(String xml, Uri directoryUri) {
    final entries = <_WebDavBackupEntry>[];
    final responseExp = RegExp(
      r'<(?:\w+:)?response\b[^>]*>([\s\S]*?)</(?:\w+:)?response>',
      caseSensitive: false,
    );
    final hrefExp = RegExp(
      r'<(?:\w+:)?href\b[^>]*>([\s\S]*?)</(?:\w+:)?href>',
      caseSensitive: false,
    );
    final responseMatches = responseExp.allMatches(xml).toList();
    final blocks = responseMatches.isEmpty
        ? <String>[xml]
        : responseMatches.map((match) => match.group(1) ?? '').toList();
    for (final block in blocks) {
      final hrefMatch = hrefExp.firstMatch(block);
      if (hrefMatch == null) {
        continue;
      }
      final href = _decodeXmlText(hrefMatch.group(1) ?? '').trim();
      if (href.isEmpty) {
        continue;
      }
      final uri = _resolveHref(href, directoryUri);
      final pathSegments = uri.pathSegments
          .where((segment) => segment.isNotEmpty)
          .map(Uri.decodeComponent)
          .toList(growable: false);
      if (pathSegments.isEmpty) {
        continue;
      }
      final fileName = pathSegments.last;
      if (!fileName.startsWith('vibe-fridge-backup-') ||
          !fileName.endsWith('.json')) {
        continue;
      }
      entries.add(_WebDavBackupEntry(fileName: fileName, uri: uri));
    }
    return entries;
  }

  Uri _resolveHref(String href, Uri directoryUri) {
    final parsed = Uri.parse(href);
    if (parsed.hasScheme) {
      return parsed;
    }
    if (href.startsWith('/')) {
      return directoryUri.replace(
        path: parsed.path,
        query: parsed.query.isEmpty ? null : parsed.query,
        fragment: null,
      );
    }
    return directoryUri.resolve(href);
  }

  String _decodeXmlText(String value) {
    return value
        .replaceAll('&amp;', '&')
        .replaceAll('&lt;', '<')
        .replaceAll('&gt;', '>')
        .replaceAll('&quot;', '"')
        .replaceAll('&apos;', "'");
  }
}

class WebDavBackupUploadResult {
  const WebDavBackupUploadResult({
    required this.fileName,
    required this.uri,
  });

  final String fileName;
  final Uri uri;
}

class WebDavBackupDownloadResult {
  const WebDavBackupDownloadResult({
    required this.fileName,
    required this.uri,
    required this.backupJson,
  });

  final String fileName;
  final Uri uri;
  final String backupJson;
}

enum WebDavBackupErrorType {
  configuration,
  network,
  authentication,
  server,
  notFound,
}

class WebDavBackupException implements Exception {
  const WebDavBackupException(
    this.message, {
    this.type = WebDavBackupErrorType.server,
  });

  final String message;
  final WebDavBackupErrorType type;

  String get userMessage {
    return switch (type) {
      WebDavBackupErrorType.configuration => 'WebDAV 配置错误：$message',
      WebDavBackupErrorType.network => '无法连接 WebDAV：请检查地址、网络或云盘的网页访问设置',
      WebDavBackupErrorType.authentication => 'WebDAV 鉴权失败：请检查用户名和密码',
      WebDavBackupErrorType.notFound => '没有找到可恢复的 WebDAV 备份',
      WebDavBackupErrorType.server => 'WebDAV 服务返回错误：请检查目录权限或稍后重试',
    };
  }

  @override
  String toString() => message;
}

class _WebDavBackupEntry {
  const _WebDavBackupEntry({
    required this.fileName,
    required this.uri,
  });

  final String fileName;
  final Uri uri;
}

const _propfindBody = '''
<?xml version="1.0" encoding="utf-8" ?>
<d:propfind xmlns:d="DAV:">
  <d:prop>
    <d:resourcetype />
    <d:getcontentlength />
  </d:prop>
</d:propfind>
''';
