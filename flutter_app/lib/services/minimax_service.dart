// ============================================================================
// 文件名    : minimax_service.dart
// 描述      : MiniMax AI 服务层 —— 封装 MiniMax 大模型 API 的调用逻辑，
//             实现从自由文本中智能提取人员姓名、单位、职位等信息。
//             本服务复刻自 Python 端的 ai_service.py + text_extractor.py，
//             在 Flutter/Dart 环境中提供等价的 AI 文本提取能力。
// 作者      : 戒者有八
// 创建日期  : 2026-07-03
// 版本      : 2.0.0
// ============================================================================

// ---- 导入依赖 ----
import 'dart:convert';                      // JSON 编解码
import 'package:http/http.dart' as http;    // HTTP 网络请求库
import '../models/card_models.dart';        // 席卡数据模型（PersonInfo 等）

// ============================================================================
// 类名    : MiniMaxService
// 描述    : MiniMax AI 服务类，负责与 MiniMax 大模型 API 进行通信，
//           核心功能包括：
//             1. 调用 MiniMax Chat Completion 接口发送提示词
//             2. 解析 AI 返回的 JSON 结构化数据
//             3. 当 AI 调用失败时，提供本地正则 fallback 解析
//             4. 内置限流机制，防止请求过于频繁
// 属性    :
//           - apiKey        : MiniMax API 密钥，用于鉴权
//           - apiBaseUrl    : API 基础地址，默认为官方地址
//           - model         : 使用的模型名称，默认 MiniMax-M2.5
//           - maxTokens     : 单次请求最大生成 token 数
//           - temperature   : 生成温度，控制输出随机性（0~1）
//           - timeout       : HTTP 请求超时时间（秒）
//           - _lastRequestTime : 上次请求时间戳，用于限流
//           - _minInterval     : 两次请求之间的最小间隔
// 用法    :
//           final service = MiniMaxService(apiKey: 'your-key');
//           final people = await service.extractFromText('张三 北京公司 工程师');
// ============================================================================
class MiniMaxService {
  // ---- 公开配置属性 ----
  String apiKey;          // MiniMax API 密钥
  String apiBaseUrl;      // API 基础 URL（不含末尾斜杠）
  String model;           // 模型标识符
  int maxTokens;          // 最大生成 token 数
  double temperature;     // 采样温度，越高输出越随机
  int timeout;            // 请求超时秒数

  // ---- 限流相关属性 ----
  DateTime? _lastRequestTime;                           // 上一次请求的时间戳
  static const _minInterval = Duration(milliseconds: 500); // 最小请求间隔（500ms）

  // ========================================================================
  // 构造函数
  // 描述  : 初始化 MiniMaxService 实例，允许自定义所有配置参数
  // 参数  :
  //         - apiKey       (必填) API 密钥
  //         - apiBaseUrl   (可选) API 地址，默认 https://api.minimaxi.com/v1
  //         - model        (可选) 模型名，默认 MiniMax-M2.5
  //         - maxTokens    (可选) 最大 token，默认 2000
  //         - temperature  (可选) 温度，默认 0.7
  //         - timeout      (可选) 超时秒数，默认 30
  // ========================================================================
  MiniMaxService({
    required this.apiKey,
    this.apiBaseUrl = 'https://api.minimaxi.com/v1',
    this.model = 'MiniMax-M2.5',
    this.maxTokens = 2000,
    this.temperature = 0.7,
    this.timeout = 30,
  });

  // ========================================================================
  // 常量  : _extractPrompt
  // 描述  : AI 提取提示词（系统级 prompt），用于指导 MiniMax 大模型从自由文本中
  //         提取人员信息。提示词中详细定义了：
  //           - 任务说明：从文本中识别姓名、单位、职位
  //           - 支持的输入格式示例（制表符分隔、逗号分隔、职务在前、混合格式等）
  //           - 智能分析规则（姓名/单位/职位的识别特征）
  //           - 输出格式要求（严格 JSON 数组格式）
  //           - 注意事项（空值处理、称谓去除、完整性要求等）
  //         该提示词与 Python 端 text_extractor.py 中的提示词保持一致。
  // ========================================================================
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

  // ========================================================================
  // 方法  : _rateLimit
  // 描述  : 限流控制 —— 确保两次 API 请求之间至少间隔 _minInterval（500ms），
  //         防止因请求过于频繁而触发 API 的速率限制。
  // 参数  : 无
  // 返回  : Future<void> —— 如果需要等待，则异步等待到满足间隔要求
  // ========================================================================
  Future<void> _rateLimit() async {
    // 如果之前有过请求记录，则计算距上次请求经过的时间
    if (_lastRequestTime != null) {
      final elapsed = DateTime.now().difference(_lastRequestTime!); // 计算已过去的时间
      // 如果间隔不足最小要求，则等待剩余的时间
      if (elapsed < _minInterval) {
        await Future.delayed(_minInterval - elapsed); // 等待差值时长
      }
    }
    // 更新上次请求时间为当前时间
    _lastRequestTime = DateTime.now();
  }

  // ========================================================================
  // 方法  : _callApi
  // 描述  : 调用 MiniMax Chat Completion API，发送 prompt 并获取 AI 生成的文本。
  //         内置自动重试机制：当请求失败（网络异常或 HTTP 非 200）时，
  //         最多重试 3 次，采用指数退避策略（1s, 2s, 4s）。
  // 参数  :
  //         - prompt     (String)  发送给 AI 的完整提示词
  //         - retryCount (int)     当前重试次数（内部递归使用，默认 0）
  // 返回  : Future<String> —— AI 生成的文本内容（choices[0].message.content）
  // 异常  :
  //         - 当 API Key 为空时抛出配置异常
  //         - 当重试次数耗尽且仍失败时抛出请求异常
  // ========================================================================
  Future<String> _callApi(String prompt, {int retryCount = 0}) async {
    // ---- 前置校验：检查 API Key 是否已配置 ----
    if (apiKey.isEmpty) {
      throw Exception('API Key 未配置，请先在设置中填写 MiniMax API Key');
    }

    // ---- 限流控制：确保请求间隔 ----
    await _rateLimit();

    // ---- 构造请求 URL：拼接基础地址与 chat/completions 路径 ----
    // 先用正则去除基础地址末尾的多余斜杠，避免 URL 中出现双斜杠
    final url = Uri.parse('${apiBaseUrl.replaceAll(RegExp(r'/+$'), '')}/chat/completions');

    // ---- 构造请求体（JSON 格式） ----
    final body = jsonEncode({
      'model': model,               // 指定使用的模型
      'messages': [
        {'role': 'user', 'content': prompt}, // 用户消息（即提示词）
      ],
      'max_tokens': maxTokens,       // 限制生成的最大 token 数
      'temperature': temperature,    // 控制生成的随机性
    });

    try {
      // ---- 发送 HTTP POST 请求，并设置超时 ----
      final response = await http
          .post(url,
              headers: {
                'Content-Type': 'application/json',        // 请求体为 JSON
                'Authorization': 'Bearer $apiKey',         // Bearer Token 鉴权
              },
              body: body)
          .timeout(Duration(seconds: timeout)); // 超时控制

      // ---- 处理响应：成功（HTTP 200） ----
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body); // 解析响应 JSON
        // 检查 choices 字段是否存在且非空
        if (data['choices'] != null && (data['choices'] as List).isNotEmpty) {
          // 返回第一条对话的 AI 回复内容
          return data['choices'][0]['message']['content'] ?? '';
        }
        // choices 为空或格式异常
        throw Exception('API 响应格式异常');
      } else {
        // ---- 处理响应：失败（HTTP 非 200） ----
        final errorBody = response.body; // 保存错误响应体用于异常信息
        // 如果重试次数未达上限（最多 3 次），则进行指数退避重试
        if (retryCount < 3) {
          // 指数退避：第 1 次等 1s，第 2 次等 2s，第 3 次等 4s
          await Future.delayed(Duration(seconds: (1 << retryCount)));
          // 递归调用自身，重试次数 +1
          return _callApi(prompt, retryCount: retryCount + 1);
        }
        // 重试次数已耗尽，抛出异常并附带 HTTP 状态码和错误详情
        throw Exception('API 请求失败 (${response.statusCode}): $errorBody');
      }
    } catch (e) {
      // ---- 异常处理：网络异常等捕获 ----
      // 如果是可重试的异常且重试次数未耗尽，则继续重试
      if (retryCount < 3 && e is! Exception) {
        await Future.delayed(Duration(seconds: (1 << retryCount))); // 指数退避
        return _callApi(prompt, retryCount: retryCount + 1);        // 递归重试
      }
      // 否则直接向上抛出异常
      rethrow;
    }
  }

  // ========================================================================
  // 方法  : extractFromText
  // 描述  : 从自由文本中提取人员信息的主入口方法。
  //         工作流程：
  //           1. 将用户文本拼接到提取提示词后，构造完整的 AI prompt
  //           2. 调用 MiniMax API 获取 AI 的结构化提取结果
  //           3. 解析 AI 返回的 JSON，得到 PersonInfo 列表
  //           4. 如果 AI 提取成功且结果非空，直接返回
  //           5. 如果 AI 调用失败或返回为空，降级到本地正则 fallback 解析
  // 参数  :
  //         - text (String) 待提取的原始文本（可能包含多人的姓名、单位、职位）
  // 返回  : Future<List<PersonInfo>> —— 提取到的人员信息列表
  // ========================================================================
  Future<List<PersonInfo>> extractFromText(String text) async {
    // ---- 构造完整提示词：系统提示 + 用户文本 ----
    final prompt = '$_extractPrompt\n\n请提取以下文本：\n$text';

    try {
      // ---- 尝试通过 AI 提取 ----
      final content = await _callApi(prompt);           // 调用 API 获取 AI 回复
      final results = _parseAiResponse(content);        // 解析 AI 返回的 JSON
      if (results.isNotEmpty) return results;           // 如果解析到有效结果则直接返回
    } catch (_) {
      // AI 调用失败（网络异常、API 异常等），静默捕获，走 fallback 路径
    }

    // ---- AI 失败或结果为空时，降级到本地正则解析 ----
    return _fallbackParse(text);
  }

  // ========================================================================
  // 方法  : _parseAiResponse
  // 描述  : 解析 AI 返回的文本内容，从中提取 JSON 数组并转换为 PersonInfo 列表。
  //         AI 返回的内容可能包含额外的说明文字，因此需要定位 JSON 数组的
  //         起始位置（第一个 '['）和结束位置（最后一个 ']'），提取中间的 JSON 字符串。
  // 参数  :
  //         - content (String) AI 返回的原始文本内容
  // 返回  : List<PersonInfo> —— 解析成功的人员信息列表；解析失败返回空列表
  // ========================================================================
  List<PersonInfo> _parseAiResponse(String content) {
    try {
      // ---- 定位 JSON 数组的边界 ----
      final jsonStart = content.indexOf('[');           // 找到第一个 '[' 的位置
      final jsonEnd = content.lastIndexOf(']');         // 找到最后一个 ']' 的位置
      // 如果没有找到合法的 JSON 数组边界，返回空列表
      if (jsonStart == -1 || jsonEnd <= jsonStart) return [];

      // ---- 提取 JSON 字符串并解析 ----
      final jsonStr = content.substring(jsonStart, jsonEnd + 1); // 截取 JSON 部分
      final List<dynamic> data = jsonDecode(jsonStr);            // 解析为动态列表

      // ---- 将 JSON 数据映射为 PersonInfo 对象列表 ----
      return data
          .whereType<Map<String, dynamic>>()           // 过滤出 Map 类型的元素
          .map((item) => PersonInfo(
                name: item['name']?.toString() ?? '',      // 姓名字段
                company: item['company']?.toString() ?? '', // 单位字段
                position: item['position']?.toString() ?? '', // 职位字段
                originalLine: '',                           // AI 提取无原始行，留空
              ))
          .where((p) => p.name.isNotEmpty)             // 过滤掉姓名为空的无效记录
          .toList();
    } catch (_) {
      // JSON 解析失败（格式异常等），返回空列表
      return [];
    }
  }

  // ========================================================================
  // 方法  : _fallbackParse
  // 描述  : 降级解析方案 —— 当 AI 调用不可用时，使用本地正则表达式对文本进行
  //         简单的分割和过滤，提取出可能是姓名的文本片段。
  //         此方法不进行单位和职位的提取，仅提取姓名。
  //         处理逻辑：
  //           1. 按常见分隔符（逗号、分号、顿号、换行等）分割文本
  //           2. 去除每段开头的序号（如 "1." "2．" "3、"）
  //           3. 过滤条件：长度 2~20 字符、不含特殊字符、不重复
  // 参数  :
  //         - text (String) 待解析的原始文本
  // 返回  : List<PersonInfo> —— 解析出的姓名列表（仅含 name 和 originalLine）
  // ========================================================================
  List<PersonInfo> _fallbackParse(String text) {
    // ---- 按常见中英文分隔符分割文本 ----
    final parts = text.split(RegExp(r'[,，;；、\n\r]+')); // 支持逗号、分号、顿号、换行
    // 用于去重的集合（记录已出现的姓名）
    final seen = <String>{};
    // 最终结果列表
    final results = <PersonInfo>[];

    // ---- 遍历每个分割片段，逐一处理 ----
    for (final part in parts) {
      // 去除开头的序号标记（如 "1." "2．" "3、" 等）
      var name = part.replaceAll(RegExp(r'^\s*\d+[.．、]\s*'), '').trim();
      // ---- 有效性过滤 ----
      // 条件：非空、长度在 2~20 之间（合理姓名长度范围）
      if (name.isNotEmpty && name.length >= 2 && name.length <= 20) {
        // 条件：不重复 且 不包含文件系统特殊字符（防止路径注入）
        if (!seen.contains(name) && !RegExp(r'[<>:"/\\|?*\[\]{}]').hasMatch(name)) {
          seen.add(name); // 标记为已见，防止重复
          // 构造 PersonInfo 对象（仅含姓名和原始行）
          results.add(PersonInfo(name: name, originalLine: part.trim()));
        }
      }
    }
    return results;
  }
}
