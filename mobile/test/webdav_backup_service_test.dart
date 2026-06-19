import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:vibe_fridge/data/webdav_backup_service.dart';
import 'package:vibe_fridge/data/webdav_backup_store.dart';

void main() {
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
