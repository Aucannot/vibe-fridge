import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:vibe_fridge/data/webdav_backup_service.dart';
import 'package:vibe_fridge/data/webdav_backup_store.dart';

void main() {
  test('round-trips backup against local WebDAV server', () async {
    final server = await _LocalWebDavServer.start(
      username: 'tester',
      password: 'app-password',
    );
    addTearDown(server.close);
    final service = WebDavBackupService();
    addTearDown(service.close);
    final settings = WebDavBackupSettings(
      serverUrl: server.baseUrl,
      remoteDirectory: 'vibe-fridge/backups',
      username: 'tester',
      password: 'app-password',
    );

    await service.validateConfiguration(settings);
    final upload = await service.uploadBackup(
      settings: settings,
      fileName: 'vibe-fridge-backup-20260619-120000.json',
      backupJson: '{"metadata":{"version":1},"items":[{"name":"牛奶"}]}',
    );
    final restored = await service.downloadLatestBackup(settings);

    expect(upload.uri.path,
        '/dav/vibe-fridge/backups/vibe-fridge-backup-20260619-120000.json');
    expect(restored.fileName, 'vibe-fridge-backup-20260619-120000.json');
    expect(restored.backupJson, contains('"牛奶"'));
    expect(server.requests, contains('MKCOL /dav/vibe-fridge/'));
    expect(server.requests, contains('PUT ${upload.uri.path}'));
    expect(server.requests, contains('PROPFIND /dav/vibe-fridge/backups/'));
    expect(server.requests, contains('GET ${upload.uri.path}'));
  });

  test('uploads backup through WebDAV PUT with basic auth', () async {
    final seen = <String>[];
    late String putBody;
    final service = WebDavBackupService(
      client: MockClient((request) async {
        seen.add('${request.method} ${request.url.path}');
        if (request.method == 'MKCOL') {
          return http.Response('', 201);
        }
        if (request.method == 'PUT') {
          expect(request.url.toString(),
              'https://dav.example.com/dav/vibe-fridge/backups/vibe-fridge-backup-20260619-120000.json');
          expect(
            request.headers['authorization'],
            'Basic ${base64Encode(utf8.encode('alice:secret'))}',
          );
          expect(
            request.headers['content-type'],
            'application/json; charset=utf-8',
          );
          putBody = request.body;
          return http.Response('', 201);
        }
        fail('Unexpected request: ${request.method} ${request.url}');
      }),
    );
    addTearDown(service.close);

    final result = await service.uploadBackup(
      settings: const WebDavBackupSettings(
        serverUrl: 'https://dav.example.com/dav',
        remoteDirectory: 'vibe-fridge/backups',
        username: 'alice',
        password: 'secret',
      ),
      fileName: 'vibe-fridge-backup-20260619-120000.json',
      backupJson: '{"data":{}}',
    );

    expect(result.fileName, 'vibe-fridge-backup-20260619-120000.json');
    expect(putBody, '{"data":{}}');
    expect(seen, [
      'MKCOL /dav/vibe-fridge/',
      'MKCOL /dav/vibe-fridge/backups/',
      'PUT /dav/vibe-fridge/backups/vibe-fridge-backup-20260619-120000.json',
    ]);
  });

  test('downloads latest generated backup from WebDAV listing', () async {
    final service = WebDavBackupService(
      client: MockClient((request) async {
        if (request.method == 'MKCOL') {
          return http.Response('', 405);
        }
        if (request.method == 'PROPFIND') {
          expect(request.headers['depth'], '1');
          return http.Response('''
<d:multistatus xmlns:d="DAV:">
  <d:response>
    <d:href>/dav/vibe-fridge/backups/</d:href>
  </d:response>
  <d:response>
    <d:href>/dav/vibe-fridge/backups/vibe-fridge-backup-20260618-090000.json</d:href>
  </d:response>
  <d:response>
    <d:href>/dav/vibe-fridge/backups/vibe-fridge-backup-20260619-120000.json</d:href>
  </d:response>
  <d:response>
    <d:href>/dav/vibe-fridge/backups/notes.txt</d:href>
  </d:response>
</d:multistatus>
''', 207);
        }
        if (request.method == 'GET') {
          expect(
            request.url.toString(),
            'https://dav.example.com/dav/vibe-fridge/backups/vibe-fridge-backup-20260619-120000.json',
          );
          return http.Response('{"metadata":{"version":1},"data":{}}', 200);
        }
        fail('Unexpected request: ${request.method} ${request.url}');
      }),
    );
    addTearDown(service.close);

    final result = await service.downloadLatestBackup(
      const WebDavBackupSettings(
        serverUrl: 'https://dav.example.com/dav',
        remoteDirectory: 'vibe-fridge/backups',
      ),
    );

    expect(result.fileName, 'vibe-fridge-backup-20260619-120000.json');
    expect(result.backupJson, contains('"metadata"'));
  });

  test('maps authentication failure to user-facing message', () async {
    final service = WebDavBackupService(
      client: MockClient((_) async => http.Response('forbidden', 403)),
    );
    addTearDown(service.close);

    expect(
      () => service.validateConfiguration(
        const WebDavBackupSettings(
          serverUrl: 'https://dav.example.com/dav',
          remoteDirectory: '',
          username: 'alice',
          password: 'wrong',
        ),
      ),
      throwsA(
        isA<WebDavBackupException>()
            .having(
              (error) => error.type,
              'type',
              WebDavBackupErrorType.authentication,
            )
            .having(
              (error) => error.userMessage,
              'userMessage',
              'WebDAV 鉴权失败：请检查用户名和密码',
            ),
      ),
    );
  });

  test('maps network failure to actionable WebDAV copy', () async {
    final service = WebDavBackupService(
      client: MockClient((_) async {
        throw http.ClientException('XMLHttpRequest error.');
      }),
    );
    addTearDown(service.close);

    expect(
      () => service.validateConfiguration(
        const WebDavBackupSettings(
          serverUrl: 'https://dav.example.com/dav',
        ),
      ),
      throwsA(
        isA<WebDavBackupException>()
            .having(
              (error) => error.type,
              'type',
              WebDavBackupErrorType.network,
            )
            .having(
              (error) => error.userMessage,
              'userMessage',
              contains('云盘的网页访问设置'),
            ),
      ),
    );
  });

  test('rejects invalid backup directory path', () {
    final service = WebDavBackupService(client: MockClient((_) async {
      fail('No request should be sent for invalid configuration');
    }));
    addTearDown(service.close);

    expect(
      () => service.validateConfiguration(
        const WebDavBackupSettings(
          serverUrl: 'https://dav.example.com/dav',
          remoteDirectory: '../private',
        ),
      ),
      throwsA(
        isA<WebDavBackupException>().having(
          (error) => error.type,
          'type',
          WebDavBackupErrorType.configuration,
        ),
      ),
    );
  });
}

class _LocalWebDavServer {
  _LocalWebDavServer._(
    this._server, {
    required this.baseUrl,
    required String username,
    required String password,
  }) : _authHeader =
            'Basic ${base64Encode(utf8.encode('$username:$password'))}' {
    _subscription = _server.listen(_handleRequest);
  }

  final HttpServer _server;
  final String baseUrl;
  final String _authHeader;
  final requests = <String>[];
  final _directories = <String>{'/dav/'};
  final _files = <String, String>{};
  late final StreamSubscription<HttpRequest> _subscription;

  static Future<_LocalWebDavServer> start({
    required String username,
    required String password,
  }) async {
    final server = await HttpServer.bind(InternetAddress.loopbackIPv4, 0);
    return _LocalWebDavServer._(
      server,
      baseUrl: 'http://${server.address.host}:${server.port}/dav',
      username: username,
      password: password,
    );
  }

  Future<void> close() async {
    await _subscription.cancel();
    await _server.close(force: true);
  }

  Future<void> _handleRequest(HttpRequest request) async {
    requests.add('${request.method} ${request.uri.path}');
    if (request.headers.value(HttpHeaders.authorizationHeader) != _authHeader) {
      request.response.statusCode = HttpStatus.unauthorized;
      await request.response.close();
      return;
    }

    switch (request.method) {
      case 'MKCOL':
        _handleMkcol(request);
        break;
      case 'PROPFIND':
        _handlePropfind(request);
        break;
      case 'PUT':
        await _handlePut(request);
        break;
      case 'GET':
        _handleGet(request);
        break;
      default:
        request.response.statusCode = HttpStatus.methodNotAllowed;
    }
    await request.response.close();
  }

  void _handleMkcol(HttpRequest request) {
    final path = _ensureTrailingSlash(request.uri.path);
    if (_directories.add(path)) {
      request.response.statusCode = HttpStatus.created;
    } else {
      request.response.statusCode = HttpStatus.methodNotAllowed;
    }
  }

  void _handlePropfind(HttpRequest request) {
    final directoryPath = _ensureTrailingSlash(request.uri.path);
    if (!_directories.contains(directoryPath)) {
      request.response.statusCode = HttpStatus.notFound;
      return;
    }

    request.response
      ..statusCode = 207
      ..headers.contentType =
          ContentType('application', 'xml', charset: 'utf-8')
      ..write(_multistatus(directoryPath));
  }

  Future<void> _handlePut(HttpRequest request) async {
    final directoryPath = _ensureTrailingSlash(
      request.uri.path.substring(0, request.uri.path.lastIndexOf('/') + 1),
    );
    if (!_directories.contains(directoryPath)) {
      request.response.statusCode = HttpStatus.notFound;
      return;
    }
    _files[request.uri.path] = await utf8.decoder.bind(request).join();
    request.response.statusCode = HttpStatus.created;
  }

  void _handleGet(HttpRequest request) {
    final body = _files[request.uri.path];
    if (body == null) {
      request.response.statusCode = HttpStatus.notFound;
      return;
    }
    request.response
      ..statusCode = HttpStatus.ok
      ..headers.contentType = ContentType.json
      ..write(body);
  }

  String _multistatus(String directoryPath) {
    final hrefs = <String>[
      directoryPath,
      ..._files.keys.where((path) => path.startsWith(directoryPath)),
    ];
    final responses = hrefs
        .map(
          (href) => '''
  <d:response>
    <d:href>$href</d:href>
  </d:response>''',
        )
        .join('\n');
    return '''
<d:multistatus xmlns:d="DAV:">
$responses
</d:multistatus>
''';
  }

  String _ensureTrailingSlash(String path) {
    return path.endsWith('/') ? path : '$path/';
  }
}
