import 'package:shared_preferences/shared_preferences.dart';

class VlmSettings {
  const VlmSettings({
    required this.endpoint,
    required this.model,
    required this.apiKey,
  });

  final String endpoint;
  final String model;
  final String apiKey;

  bool get isConfigured =>
      endpoint.trim().isNotEmpty &&
      model.trim().isNotEmpty &&
      apiKey.trim().isNotEmpty;

  VlmSettings copyWith({
    String? endpoint,
    String? model,
    String? apiKey,
  }) {
    return VlmSettings(
      endpoint: endpoint ?? this.endpoint,
      model: model ?? this.model,
      apiKey: apiKey ?? this.apiKey,
    );
  }
}

class VlmSettingsStore {
  static const defaultEndpoint =
      'https://api.siliconflow.cn/v1/chat/completions';
  static const defaultModel = 'Qwen/Qwen2.5-VL-72B-Instruct';

  static const _endpointKey = 'vlm.endpoint';
  static const _modelKey = 'vlm.model';
  static const _apiKeyKey = 'vlm.api_key';

  Future<VlmSettings> load() async {
    final preferences = await SharedPreferences.getInstance();
    return VlmSettings(
      endpoint: preferences.getString(_endpointKey) ?? defaultEndpoint,
      model: preferences.getString(_modelKey) ?? defaultModel,
      apiKey: preferences.getString(_apiKeyKey) ?? '',
    );
  }

  Future<void> save(VlmSettings settings) async {
    final preferences = await SharedPreferences.getInstance();
    await Future.wait([
      preferences.setString(_endpointKey, settings.endpoint.trim()),
      preferences.setString(_modelKey, settings.model.trim()),
      preferences.setString(_apiKeyKey, settings.apiKey.trim()),
    ]);
  }
}
