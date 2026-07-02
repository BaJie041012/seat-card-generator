import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/card_models.dart';

/// 席卡生成 API 服务
class ApiService {
  String _baseUrl;
  static const Duration _timeout = Duration(seconds: 120);

  ApiService({String? baseUrl})
      : _baseUrl = baseUrl ?? 'http://localhost:8000';

  String get baseUrl => _baseUrl;

  set baseUrl(String url) {
    _baseUrl = url.replaceAll(RegExp(r'/+$'), '');
  }

  /// 健康检查
  Future<bool> healthCheck() async {
    try {
      final response =
          await http.get(Uri.parse('$_baseUrl/api/health')).timeout(_timeout);
      return response.statusCode == 200;
    } catch (_) {
      return false;
    }
  }

  /// 获取模板列表
  Future<TemplateInfo> getTemplates() async {
    try {
      final response = await http
          .get(Uri.parse('$_baseUrl/api/templates'))
          .timeout(_timeout);
      if (response.statusCode == 200) {
        return TemplateInfo.fromJson(
            jsonDecode(response.body) as Map<String, dynamic>);
      }
      return TemplateInfo(success: false);
    } catch (e) {
      return TemplateInfo(success: false);
    }
  }

  /// 生成席卡
  Future<GenerateCardsResponse> generateCards(
      GenerateCardsRequest request) async {
    try {
      final response = await http
          .post(
            Uri.parse('$_baseUrl/api/generate-cards'),
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode(request.toJson()),
          )
          .timeout(_timeout);

      final data = jsonDecode(response.body) as Map<String, dynamic>;
      return GenerateCardsResponse.fromJson(data);
    } catch (e) {
      return GenerateCardsResponse(
        success: false,
        error: '连接服务器失败: $e',
      );
    }
  }

  /// 获取文件下载 URL
  String getDownloadUrl(String fileId) {
    return '$_baseUrl/download/$fileId';
  }
}
