import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:vibe_fridge/data/vlm_settings_store.dart';
import 'package:vibe_fridge/data/webdav_backup_store.dart';

void main() {
  setUp(() {
    SharedPreferences.setMockInitialValues({});
  });

  test('stores WebDAV password securely and hides it when requested', () async {
    final secretStore = _MemorySecretStore();
    final store = WebDavBackupSettingsStore(secretStore: secretStore);

    await store.save(
      const WebDavBackupSettings(
        serverUrl: ' https://dav.example.com/dav ',
        remoteDirectory: ' /vibe-fridge/backups/ ',
        username: ' alice ',
        password: ' secret ',
      ),
    );

    final hidden = await store.load(revealPassword: false);
    final revealed = await store.load();

    expect(hidden.serverUrl, 'https://dav.example.com/dav');
    expect(hidden.remoteDirectory, 'vibe-fridge/backups');
    expect(hidden.username, 'alice');
    expect(hidden.password, isEmpty);
    expect(hidden.hasStoredPassword, isTrue);
    expect(revealed.password, 'secret');
  });

  test('preserves stored WebDAV password when saving blank password', () async {
    final secretStore = _MemorySecretStore();
    final store = WebDavBackupSettingsStore(secretStore: secretStore);

    await store.save(
      const WebDavBackupSettings(
        serverUrl: 'https://dav.example.com/dav',
        password: 'secret',
      ),
    );
    await store.save(
      const WebDavBackupSettings(
        serverUrl: 'https://dav.example.com/nextcloud',
        password: '',
      ),
    );

    final loaded = await store.load();

    expect(loaded.serverUrl, 'https://dav.example.com/nextcloud');
    expect(loaded.password, 'secret');
    expect(loaded.hasStoredPassword, isTrue);
  });
}

class _MemorySecretStore implements VlmSecretStore {
  final _values = <String, String>{};

  @override
  Future<String?> read(String key) async {
    return _values[key];
  }

  @override
  Future<void> write(String key, String value) async {
    _values[key] = value;
  }

  @override
  Future<void> delete(String key) async {
    _values.remove(key);
  }
}
