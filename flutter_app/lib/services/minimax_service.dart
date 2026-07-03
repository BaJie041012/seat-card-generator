/// MiniMax AI 服务 — 直连 API，实现文本提取
/// 复刻自 Python 端 ai_service.py + text_extractor.py
import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/card_models.dart';

class MiniMaxService {
  String apiKey;
  String apiBaseUrl;
  String model;
  int maxTokens;
  double temperature;
  int timeout;

  DateTime? _lastRequestTime;
  static const _minInterval = Duration(milliseconds: 500);

  MiniMaxService({
    required this.apiKey,
    this.apiBaseUrl = 'https://api.minimaxi.com/v1',
    this.model = 'MiniMax-M2.5',
    this.maxTokens = 2000,
    this.temperature = 0.7,
    this.timeout = 30,
  });

  // AI 提取提示词（与 Python 端一致）
  static const _extractPrompt = '''你是一个智能文本信息提取助手，擅长从各种格式的文本中自动分析和提取人员信息。

## 任务说明
请仔细分析输入文本，自动识别并提取每个人的姓名、工作单位和职位信息。

## 支持的输入格式示例

### 格式1：制表符/空格分隔
张三    北京科技有限公司    高级工程师
李四    上海数据科技集团    产品经理

### 格式2：逗号分隔
张三，北京科技有限公司，高级工程师；李四，上海数据科技集团，产品经理

### 格式3：职务在前
新疆生产建设兵团第八师副师长、石河子市人民政府副市长 欧阳伟

### 格式4：混合格式
1. 张三 - 北京科技有限公司 - 高级工程师
2. 李四，上海数据科技集团，产品经理

## 智能分析规则

### 姓名识别规则：
- 通常是2-4个汉字的人名
- 位于文本开头或职务前面
- 可能包含"先生"、"女士"等称谓（需去除称谓提取纯姓名）

### 单位识别规则：
- 通常包含"公司"、"集团"、"有限公司"、"股份"、"科技"、"部门"、"局"、"厅"、"委员会"等关键词
- 不包含职位信息

### 职位识别规则：
- 通常包含"经理"、"总监"、"工程师"、"主任"、"局长"、"部长"、"主席"、"董事长"、"总经理"、"副总"、"首席"等关键词

## 输出格式要求
请严格按照以下JSON格式返回结果，不要包含其他任何说明文字：
[
  {"name": "姓名", "company": "单位", "position": "职位"},
  {"name": "姓名", "company": "单位", "position": "职位"}
]

## 注意事项
1. 如果某字段无法识别或不存在，请填空字符串 ""
2. 确保每个人对应一条记录
3. 去除姓名中的称谓（如"先生"、"女士"）
4. 单位名称应完整，不包含职位
5. 职位应提取完整的职务名称

开始提取：''';

  /// 限流
  Future<void> _rateLimit() async {
    if (_lastRequestTime != null) {
      final elapsed = DateTime.now().difference(_lastRequestTime!);
      if (elapsed < _minInterval) {
        await Future.delayed(_minInterval - elapsed);
      }
    }
    _lastRequestTime = DateTime.now();
  }

  /// 调用 MiniMax API
  Future<String> _callApi(String prompt, {int retryCount = 0}) async {
    if (apiKey.isEmpty) {
      throw Exception('API Key 未配置，请先在设置中填写 MiniMax API Key');
    }

    await _rateLimit();

    final url = Uri.parse('${apiBaseUrl.replaceAll(RegExp(r'/+$'), '')}/chat/completions');
    final body = jsonEncode({
      'model': model,
      'messages': [
        {'role': 'user', 'content': prompt},
      ],
      'max_tokens': maxTokens,
      'temperature': temperature,
    });

    try {
      final response = await http
          .post(url,
              headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer $apiKey',
              },
              body: body)
          .timeout(Duration(seconds: timeout));

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        if (data['choices'] != null && (data['choices'] as List).isNotEmpty) {
          return data['choices'][0]['message']['content'] ?? '';
        }
        throw Exception('API 响应格式异常');
      } else {
        final errorBody = response.body;
        if (retryCount < 3) {
          await Future.delayed(Duration(seconds: (1 << retryCount)));
          return _callApi(prompt, retryCount: retryCount + 1);
        }
        throw Exception('API 请求失败 (${response.statusCode}): $errorBody');
      }
    } catch (e) {
      if (retryCount < 3 && e is! Exception) {
        await Future.delayed(Duration(seconds: (1 << retryCount)));
        return _callApi(prompt, retryCount: retryCount + 1);
      }
      rethrow;
    }
  }

  /// 从文本中提取人员信息
  Future<List<PersonInfo>> extractFromText(String text) async {
    final prompt = '$_extractPrompt\n\n请提取以下文本：\n$text';

    try {
      final content = await _callApi(prompt);
      final results = _parseAiResponse(content);
      if (results.isNotEmpty) return results;
    } catch (_) {
      // AI 失败，走 fallback
    }

    return _fallbackParse(text);
  }

  /// 解析 AI 返回的 JSON
  List<PersonInfo> _parseAiResponse(String content) {
    try {
      final jsonStart = content.indexOf('[');
      final jsonEnd = content.lastIndexOf(']');
      if (jsonStart == -1 || jsonEnd <= jsonStart) return [];

      final jsonStr = content.substring(jsonStart, jsonEnd + 1);
      final List<dynamic> data = jsonDecode(jsonStr);

      return data
          .whereType<Map<String, dynamic>>()
          .map((item) => PersonInfo(
                name: item['name']?.toString() ?? '',
                company: item['company']?.toString() ?? '',
                position: item['position']?.toString() ?? '',
                originalLine: '',
              ))
          .where((p) => p.name.isNotEmpty)
          .toList();
    } catch (_) {
      return [];
    }
  }

  /// Fallback：正则分割
  List<PersonInfo> _fallbackParse(String text) {
    final parts = text.split(RegExp(r'[,，;；、\n\r]+'));
    final seen = <String>{};
    final results = <PersonInfo>[];

    for (final part in parts) {
      var name = part.replaceAll(RegExp(r'^\s*\d+[.．、]\s*'), '').trim();
      if (name.isNotEmpty && name.length >= 2 && name.length <= 20) {
        if (!seen.contains(name) && !RegExp(r'[<>:"/\\|?*\[\]{}]').hasMatch(name)) {
          seen.add(name);
          results.add(PersonInfo(name: name, originalLine: part.trim()));
        }
      }
    }
    return results;
  }
}
