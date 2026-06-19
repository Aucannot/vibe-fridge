import 'package:shared_preferences/shared_preferences.dart';

import 'vlm_settings_store.dart';

class WebDavBackupSettings {
  const WebDavBackupSettings({
    this.serverUrl = '',
    this.remoteDirectory = WebDavBackupSettingsStore.defaultRemoteDirectory,
    this.username = '',
    this.password = '',
    this.hasStoredPassword = false,
  });

  final String serverUrl;
  final String remoteDirectory;
  final String username;
  final String password;
  final bool hasStoredPassword;

  bool get hasPassword => password.trim().isNotEmpty || hasStoredPassword;

  bool get isConfigured => serverUrl.trim().isNotEmpty;
}

class WebDavBackupSettingsStore {
  WebDavBackupSettingsStore({VlmSecretStore? secretStore})
      : _secretStore = secretStore ?? FlutterSecureSecretStore();

  static const defaultRemoteDirectory = 'vibe-fridge/backups';

  static const _serverUrlKey = 'webdav.server_url';
  static const _remoteDirectoryKey = 'webdav.remote_directory';
  static const _usernameKey = 'webdav.username';
  static const _securePasswordKey = 'webdav.secure_password';

  final VlmSecretStore _secretStore;

  Future<WebDavBackupSettings> load({bool revealPassword = true}) async {
    final preferences = await SharedPreferences.getInstance();
    final password = (await _secretStore.read(_securePasswordKey)) ?? '';
    return WebDavBackupSettings(
      serverUrl: preferences.getString(_serverUrlKey) ?? '',
      remoteDirectory:
          preferences.getString(_remoteDirectoryKey) ?? defaultRemoteDirectory,
      username: preferences.getString(_usernameKey) ?? '',
      password: revealPassword ? password : '',
      hasStoredPassword: password.trim().isNotEmpty,
    );
  }

  Future<void> save(
    WebDavBackupSettings settings, {
    bool preserveExistingPasswordIfBlank = true,
  }) async {
    final preferences = await SharedPreferences.getInstance();
    final trimmedPassword = settings.password.trim();
    await Future.wait([
      preferences.setString(_serverUrlKey, settings.serverUrl.trim()),
      preferences.setString(
        _remoteDirectoryKey,
        _normalizedRemoteDirectory(settings.remoteDirectory),
      ),
      preferences.setString(_usernameKey, settings.username.trim()),
    ]);

    if (trimmedPassword.isNotEmpty) {
      await _secretStore.write(_securePasswordKey, trimmedPassword);
      return;
    }
    if (!preserveExistingPasswordIfBlank) {
      await _secretStore.delete(_securePasswordKey);
    }
  }

  Future<void> clear() async {
    final preferences = await SharedPreferences.getInstance();
    await Future.wait([
      preferences.remove(_serverUrlKey),
      preferences.remove(_remoteDirectoryKey),
      preferences.remove(_usernameKey),
      _secretStore.delete(_securePasswordKey),
    ]);
  }

  String _normalizedRemoteDirectory(String value) {
    final trimmed = value.trim().replaceAll('\\', '/');
    final parts = trimmed
        .split('/')
        .map((part) => part.trim())
        .where((part) => part.isNotEmpty)
        .toList(growable: false);
    if (parts.isEmpty) {
      return defaultRemoteDirectory;
    }
    return parts.join('/');
  }
}
