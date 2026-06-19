import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:vibe_fridge/data/vlm_settings_store.dart';

void main() {
  late _MemorySecretStore secretStore;

  setUp(() {
    secretStore = _MemorySecretStore();
  });

  test('fresh settings load default endpoint and model', () async {
    SharedPreferences.setMockInitialValues({});
    final store = VlmSettingsStore(secretStore: secretStore);

    final loaded = await store.load();

    expect(loaded.endpoint, VlmSettingsStore.defaultEndpoint);
    expect(loaded.model, VlmSettingsStore.defaultModel);
    expect(loaded.hasStoredApiKey, isFalse);
  });

  test('migrates legacy plaintext API key into secure storage', () async {
    SharedPreferences.setMockInitialValues({
      'vlm.endpoint': 'https://example.test/v1/chat/completions',
      'vlm.model': 'test-model',
      'vlm.api_key': 'legacy-secret',
    });
    final store = VlmSettingsStore(secretStore: secretStore);

    final editingSettings = await store.load(revealApiKey: false);
    final preferences = await SharedPreferences.getInstance();

    expect(editingSettings.apiKey, isEmpty);
    expect(editingSettings.hasStoredApiKey, isTrue);
    expect(preferences.getString('vlm.api_key'), isNull);
    expect(await secretStore.read('vlm.secure_api_key'), 'legacy-secret');

    final runtimeSettings = await store.load();
    expect(runtimeSettings.apiKey, 'legacy-secret');
  });

  test('blank save preserves existing secure API key', () async {
    SharedPreferences.setMockInitialValues({});
    final store = VlmSettingsStore(secretStore: secretStore);
    await store.save(
      const VlmSettings(
        endpoint: 'https://example.test/v1/chat/completions',
        model: 'test-model',
        apiKey: 'saved-secret',
      ),
    );

    await store.save(
      const VlmSettings(
        endpoint: 'https://example.test/v1/chat/completions',
        model: 'new-model',
        apiKey: '',
        hasStoredApiKey: true,
      ),
      preserveExistingApiKeyIfBlank: true,
    );

    final loaded = await store.load();
    expect(loaded.model, 'new-model');
    expect(loaded.apiKey, 'saved-secret');
  });

  test('clear keeps endpoint and model blank and removes secure API key',
      () async {
    SharedPreferences.setMockInitialValues({});
    final store = VlmSettingsStore(secretStore: secretStore);
    await store.save(
      const VlmSettings(
        endpoint: 'https://example.test/v1/chat/completions',
        model: 'test-model',
        apiKey: 'saved-secret',
      ),
    );

    await store.clear();
    final preferences = await SharedPreferences.getInstance();
    final loaded = await store.load();

    expect(preferences.getString('vlm.endpoint'), isEmpty);
    expect(preferences.getString('vlm.model'), isEmpty);
    expect(await secretStore.read('vlm.secure_api_key'), isNull);
    expect(loaded.endpoint, isEmpty);
    expect(loaded.model, isEmpty);
    expect(loaded.hasStoredApiKey, isFalse);
  });

  test('secure API key storage disables macOS data protection keychain',
      () async {
    final storage = _CapturingSecureStorage();
    final secretStore = FlutterSecureVlmSecretStore(storage: storage);

    await secretStore.write('vlm.secure_api_key', 'saved-secret');
    await secretStore.read('vlm.secure_api_key');
    await secretStore.delete('vlm.secure_api_key');

    expect(
      storage.macOsOptions,
      everyElement(
        containsPair('useDataProtectionKeyChain', 'false'),
      ),
    );
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

class _CapturingSecureStorage extends FlutterSecureStorage {
  final macOsOptions = <Map<String, String>>[];

  @override
  Future<void> write({
    required String key,
    required String? value,
    IOSOptions? iOptions,
    AndroidOptions? aOptions,
    LinuxOptions? lOptions,
    WebOptions? webOptions,
    MacOsOptions? mOptions,
    WindowsOptions? wOptions,
  }) async {
    macOsOptions.add(mOptions?.toMap() ?? const {});
  }

  @override
  Future<String?> read({
    required String key,
    IOSOptions? iOptions,
    AndroidOptions? aOptions,
    LinuxOptions? lOptions,
    WebOptions? webOptions,
    MacOsOptions? mOptions,
    WindowsOptions? wOptions,
  }) async {
    macOsOptions.add(mOptions?.toMap() ?? const {});
    return null;
  }

  @override
  Future<void> delete({
    required String key,
    IOSOptions? iOptions,
    AndroidOptions? aOptions,
    LinuxOptions? lOptions,
    WebOptions? webOptions,
    MacOsOptions? mOptions,
    WindowsOptions? wOptions,
  }) async {
    macOsOptions.add(mOptions?.toMap() ?? const {});
  }
}
