import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:shared_preferences/shared_preferences.dart';

class VlmSettings {
  const VlmSettings({
    required this.endpoint,
    required this.model,
    required this.apiKey,
    this.hasStoredApiKey = false,
  });

  final String endpoint;
  final String model;
  final String apiKey;
  final bool hasStoredApiKey;

  bool get hasApiKey => apiKey.trim().isNotEmpty || hasStoredApiKey;

  bool get isConfigured =>
      endpoint.trim().isNotEmpty && model.trim().isNotEmpty && hasApiKey;

  bool get hasUsableApiKey => apiKey.trim().isNotEmpty;

  VlmSettings copyWith({
    String? endpoint,
    String? model,
    String? apiKey,
    bool? hasStoredApiKey,
  }) {
    return VlmSettings(
      endpoint: endpoint ?? this.endpoint,
      model: model ?? this.model,
      apiKey: apiKey ?? this.apiKey,
      hasStoredApiKey: hasStoredApiKey ?? this.hasStoredApiKey,
    );
  }
}

abstract class VlmSecretStore {
  Future<String?> read(String key);
  Future<void> write(String key, String value);
  Future<void> delete(String key);
}

class FlutterSecureVlmSecretStore implements VlmSecretStore {
  FlutterSecureVlmSecretStore({
    FlutterSecureStorage storage = const FlutterSecureStorage(),
  }) : _storage = storage;

  final FlutterSecureStorage _storage;
  static const _macOsOptions = MacOsOptions(
    useDataProtectionKeyChain: false,
  );

  @override
  Future<String?> read(String key) {
    return _storage.read(key: key, mOptions: _macOsOptions);
  }

  @override
  Future<void> write(String key, String value) {
    return _storage.write(key: key, value: value, mOptions: _macOsOptions);
  }

  @override
  Future<void> delete(String key) {
    return _storage.delete(key: key, mOptions: _macOsOptions);
  }
}

class VlmSettingsStore {
  VlmSettingsStore({VlmSecretStore? secretStore})
      : _secretStore = secretStore ?? FlutterSecureVlmSecretStore();

  static const defaultEndpoint =
      'https://api.siliconflow.cn/v1/chat/completions';
  static const defaultModel = 'Qwen/Qwen2.5-VL-72B-Instruct';

  static const _endpointKey = 'vlm.endpoint';
  static const _modelKey = 'vlm.model';
  static const _legacyApiKeyKey = 'vlm.api_key';
  static const _secureApiKeyKey = 'vlm.secure_api_key';

  final VlmSecretStore _secretStore;

  Future<VlmSettings> load({bool revealApiKey = true}) async {
    final preferences = await SharedPreferences.getInstance();
    final apiKey = await _loadAndMigrateApiKey(preferences);
    final hasStoredApiKey = apiKey.trim().isNotEmpty;
    return VlmSettings(
      endpoint: preferences.getString(_endpointKey) ?? defaultEndpoint,
      model: preferences.getString(_modelKey) ?? defaultModel,
      apiKey: revealApiKey ? apiKey : '',
      hasStoredApiKey: hasStoredApiKey,
    );
  }

  Future<void> save(
    VlmSettings settings, {
    bool preserveExistingApiKeyIfBlank = true,
  }) async {
    final preferences = await SharedPreferences.getInstance();
    final trimmedApiKey = settings.apiKey.trim();
    await Future.wait([
      preferences.setString(_endpointKey, settings.endpoint.trim()),
      preferences.setString(_modelKey, settings.model.trim()),
      preferences.remove(_legacyApiKeyKey),
    ]);

    if (trimmedApiKey.isNotEmpty) {
      await _secretStore.write(_secureApiKeyKey, trimmedApiKey);
      return;
    }
    if (!preserveExistingApiKeyIfBlank) {
      await _secretStore.delete(_secureApiKeyKey);
    }
  }

  Future<void> clear() async {
    final preferences = await SharedPreferences.getInstance();
    await Future.wait([
      preferences.setString(_endpointKey, ''),
      preferences.setString(_modelKey, ''),
      preferences.remove(_legacyApiKeyKey),
      _secretStore.delete(_secureApiKeyKey),
    ]);
  }

  Future<void> resetToDefaults() async {
    await save(
      const VlmSettings(
        endpoint: defaultEndpoint,
        model: defaultModel,
        apiKey: '',
      ),
      preserveExistingApiKeyIfBlank: false,
    );
  }

  Future<String> _loadAndMigrateApiKey(
    SharedPreferences preferences,
  ) async {
    final secureApiKey = (await _secretStore.read(_secureApiKeyKey)) ?? '';
    final legacyApiKey = preferences.getString(_legacyApiKeyKey) ?? '';
    if (secureApiKey.trim().isEmpty && legacyApiKey.trim().isNotEmpty) {
      await _secretStore.write(_secureApiKeyKey, legacyApiKey.trim());
      await preferences.remove(_legacyApiKeyKey);
      return legacyApiKey.trim();
    }
    if (legacyApiKey.isNotEmpty) {
      await preferences.remove(_legacyApiKeyKey);
    }
    return secureApiKey;
  }
}
