/// 设置持久化服务 — 基于 shared_preferences
import 'package:shared_preferences/shared_preferences.dart';

class SettingsService {
  static const _keyApiKey = 'minimax_api_key';
  static const _keyApiUrl = 'minimax_api_url';
  static const _keyModel = 'minimax_model';

  SharedPreferences? _prefs;

  Future<SharedPreferences> get prefs async {
    _prefs ??= await SharedPreferences.getInstance();
    return _prefs!;
  }

  static const _defaultApiKey = 'sk-api-mR_lRPZgFVmmyx7OCp83-zqdd2nlvTYM-akr0KyrDIa1ZvrZV4F0sKmKOXULeT8xP3xOYnyEh4_DJTb760jnSL_HfEU2zMOudelCxSObltogy0X0RXx5a2c';

  Future<String> getApiKey() async {
    final p = await prefs;
    return p.getString(_keyApiKey) ?? _defaultApiKey;
  }

  Future<void> saveApiKey(String key) async {
    final p = await prefs;
    await p.setString(_keyApiKey, key);
  }

  Future<String> getApiUrl() async {
    final p = await prefs;
    return p.getString(_keyApiUrl) ?? 'https://api.minimaxi.com/v1';
  }

  Future<void> saveApiUrl(String url) async {
    final p = await prefs;
    await p.setString(_keyApiUrl, url);
  }

  Future<String> getModel() async {
    final p = await prefs;
    return p.getString(_keyModel) ?? 'MiniMax-M2.5';
  }

  Future<void> saveModel(String model) async {
    final p = await prefs;
    await p.setString(_keyModel, model);
  }
}
