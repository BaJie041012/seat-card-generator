// ==============================================================================
// 文件名称: settings_service.dart
// 功能描述: 设置持久化服务模块，基于 shared_preferences 实现应用配置的本地持久化存储
// 创建日期: 2026-07-03
// 作    者: 戒者有八
// 版本: 2.0.0
// 描述: 本文件负责管理 Flutter 席卡生成器应用的所有用户可配置参数，包括 MiniMax API
//       密钥、API 服务地址和模型名称等。使用 shared_preferences 插件将配置持久化到
//       设备本地存储，确保应用重启后配置不丢失。
//
// 设计思路:
//     - 采用单例模式管理 SharedPreferences 实例，避免重复初始化
//     - 使用懒加载（lazy initialization）策略，首次访问时才创建实例
//     - 每个配置项提供独立的 getter/setter 方法，职责单一
//     - 为每个配置项设置合理的默认值，确保首次启动即可正常使用
//     - 使用 const 常量定义存储键名，避免硬编码字符串导致的拼写错误
//
// 使用方式:
//     1. 创建 SettingsService 实例
//     2. 调用 getApiKey() / getApiUrl() / getModel() 获取配置
//     3. 调用 saveApiKey() / saveApiUrl() / saveModel() 保存配置
//     4. 配置自动持久化，下次启动应用时自动恢复
//
// 依赖说明:
//     - shared_preferences: Flutter 官方本地存储插件
//     - 存储位置: Android 使用 SharedPreferences，iOS 使用 NSUserDefaults
// ==============================================================================

// ---- 导入依赖模块 ----
// shared_preferences: Flutter 官方提供的轻量级本地持久化存储插件
// 支持 Android (SharedPreferences) 和 iOS (NSUserDefaults) 平台
// 以键值对形式存储简单数据，适合存储配置参数
import 'package:shared_preferences/shared_preferences.dart';

// ==============================================================================
// 设置持久化服务类
// 功能: 管理应用的所有可配置参数，提供持久化存储和读取能力
// 设计思路:
//     - 使用懒加载模式管理 SharedPreferences 实例，避免在构造函数中执行异步操作
//     - 每个配置项提供独立的读取和保存方法，遵循单一职责原则
//     - 所有方法均为异步方法，因为 SharedPreferences 的读写操作是异步的
//     - 内置默认值机制，首次启动或配置丢失时自动使用默认值
// 属性说明:
//     - _keyApiKey: API 密钥的存储键名常量
//     - _keyApiUrl: API 服务地址的存储键名常量
//     - _keyModel: 模型名称的存储键名常量
//     - _prefs: SharedPreferences 实例缓存，避免重复获取
//     - _defaultApiKey: 内置的默认 API 密钥，供首次使用时使用
// ==============================================================================
class SettingsService {
  // ----------------------------------------------------------------------------
  // 存储键名常量定义
  // 功能: 定义 SharedPreferences 中各配置项的键名
  // 设计思路: 使用 static const 定义，编译期确定，避免运行时字符串拼接开销
  //           同时避免硬编码导致的拼写错误和维护困难
  // ----------------------------------------------------------------------------

  /// MiniMax API 密钥的存储键名
  /// 用于在 SharedPreferences 中标识 API 密钥配置项
  static const _keyApiKey = 'minimax_api_key';

  /// MiniMax API 服务地址的存储键名
  /// 用于在 SharedPreferences 中标识 API 基础 URL 配置项
  static const _keyApiUrl = 'minimax_api_url';

  /// MiniMax 模型名称的存储键名
  /// 用于在 SharedPreferences 中标识 AI 模型名称配置项
  static const _keyModel = 'minimax_model';

  // ----------------------------------------------------------------------------
  // SharedPreferences 实例缓存
  // 功能: 缓存 SharedPreferences 实例，避免每次操作都重新获取
  // 设计思路: 使用可空类型 + 空值合并赋值（??=），实现懒加载单例
  //           首次访问时异步获取实例并缓存，后续访问直接使用缓存
  // ----------------------------------------------------------------------------

  /// SharedPreferences 实例缓存
  /// 初始值为 null，首次访问 prefs getter 时自动初始化
  /// 后续访问直接返回缓存实例，避免重复的异步初始化开销
  SharedPreferences? _prefs;

  // ----------------------------------------------------------------------------
  // SharedPreferences 懒加载获取器
  // 功能: 提供异步的 SharedPreferences 实例访问，首次调用时自动初始化
  // 参数: 无
  // 返回值: Future<SharedPreferences> - SharedPreferences 实例的 Future
  // 设计思路:
  //     - 使用 ??= 运算符实现懒加载：仅在 _prefs 为 null 时执行初始化
  //     - 返回类型为非空的 SharedPreferences，调用方无需处理 null 情况
  //     - 使用 getter 而非普通方法，语义上更符合"获取属性"的使用场景
  // ----------------------------------------------------------------------------
  Future<SharedPreferences> get prefs async {
    // 如果缓存为空，则异步获取 SharedPreferences 单例并缓存
    // SharedPreferences.getInstance() 是异步操作，需要 await
    _prefs ??= await SharedPreferences.getInstance();
    // 返回已缓存的实例，使用 ! 断言非空（因为上面已经确保赋值）
    return _prefs!;
  }

  // ----------------------------------------------------------------------------
  // 默认 API 密钥
  // 功能: 提供内置的默认 API 密钥，确保首次启动应用时即可正常调用 AI 服务
  // 设计思路:
  //     - 使用 static const 定义，编译期确定，不可修改
  //     - 当用户未自行配置 API 密钥时，自动使用此默认密钥
  //     - 注意: 此密钥为应用内置的公共密钥，生产环境建议用户替换为私有密钥
  // ----------------------------------------------------------------------------

  /// 内置默认 API 密钥
  /// 当用户未在设置中配置自己的 API 密钥时使用此默认值
  /// 确保应用首次安装后即可正常调用 MiniMax AI 服务
  static const _defaultApiKey = 'sk-api-mR_lRPZgFVmmyx7OCp83-zqdd2nlvTYM-akr0KyrDIa1ZvrZV4F0sKmKOXULeT8xP3xOYnyEh4_DJTb760jnSL_HfEU2zMOudelCxSObltogy0X0RXx5a2c';

  // ============================================================================
  // API 密钥管理方法
  // 功能: 提供 API 密钥的读取和保存操作
  // 设计思路: getter 返回用户配置值或默认值，setter 将新值持久化到本地存储
  // ============================================================================

  // ----------------------------------------------------------------------------
  // 获取 API 密钥
  // 功能: 从本地存储读取用户配置的 API 密钥
  // 参数: 无
  // 返回值: Future<String> - API 密钥字符串
  // 设计思路:
  //     - 优先返回用户自行配置的密钥
  //     - 若用户未配置（getString 返回 null），则使用内置默认密钥
  //     - 使用 ?? 空值合并运算符简化默认值逻辑
  // ----------------------------------------------------------------------------
  /// 获取 API 密钥
  ///
  /// 从本地持久化存储中读取用户配置的 MiniMax API 密钥。
  /// 若用户未自行配置，则返回内置的默认密钥。
  ///
  /// 返回值:
  ///     String - MiniMax API 密钥字符串
  ///
  /// 使用场景:
  ///     调用 MiniMax AI 服务前获取认证密钥
  Future<String> getApiKey() async {
    // 获取 SharedPreferences 实例（首次调用时自动初始化）
    final p = await prefs;
    // 从本地存储读取 API 密钥，若不存在则返回内置默认密钥
    // getString 返回 String? 类型，使用 ?? 提供默认值
    return p.getString(_keyApiKey) ?? _defaultApiKey;
  }

  // ----------------------------------------------------------------------------
  // 保存 API 密钥
  // 功能: 将用户配置的 API 密钥持久化到本地存储
  // 参数:
  //     key (String): 用户输入的 API 密钥
  // 返回值: Future<void> - 异步操作完成信号
  // 设计思路:
  //     - 使用 setString 方法将字符串值写入 SharedPreferences
  //     - 写入操作是异步的，需要 await 确保写入完成
  // ----------------------------------------------------------------------------
  /// 保存 API 密钥
  ///
  /// 将用户配置的 MiniMax API 密钥持久化到本地存储。
  /// 写入操作完成后，下次调用 getApiKey() 将返回新保存的值。
  ///
  /// 参数:
  ///     key - 用户输入的 MiniMax API 密钥字符串
  ///
  /// 使用场景:
  ///     用户在设置页面修改 API 密钥后调用
  Future<void> saveApiKey(String key) async {
    // 获取 SharedPreferences 实例
    final p = await prefs;
    // 将 API 密钥写入本地存储，键名为 _keyApiKey
    // setString 返回 Future<bool>，await 确保写入操作完成
    await p.setString(_keyApiKey, key);
  }

  // ============================================================================
  // API 服务地址管理方法
  // 功能: 提供 API 服务基础 URL 的读取和保存操作
  // 设计思路: 默认指向 MiniMax 官方 API 地址，支持用户自定义（如代理地址）
  // ============================================================================

  // ----------------------------------------------------------------------------
  // 获取 API 服务地址
  // 功能: 从本地存储读取用户配置的 API 服务基础 URL
  // 参数: 无
  // 返回值: Future<String> - API 服务基础 URL 字符串
  // 设计思路:
  //     - 默认返回 MiniMax 官方 API 地址
  //     - 支持用户自定义地址（如使用代理或私有部署）
  // ----------------------------------------------------------------------------
  /// 获取 API 服务地址
  ///
  /// 从本地持久化存储中读取用户配置的 MiniMax API 服务基础 URL。
  /// 若用户未自行配置，则返回 MiniMax 官方 API 地址。
  ///
  /// 返回值:
  ///     String - MiniMax API 服务基础 URL
  ///
  /// 使用场景:
  ///     构建 API 请求时拼接基础 URL
  Future<String> getApiUrl() async {
    // 获取 SharedPreferences 实例
    final p = await prefs;
    // 从本地存储读取 API URL，若不存在则返回 MiniMax 官方默认地址
    // 默认地址指向 MiniMax API v1 版本
    return p.getString(_keyApiUrl) ?? 'https://api.minimaxi.com/v1';
  }

  // ----------------------------------------------------------------------------
  // 保存 API 服务地址
  // 功能: 将用户配置的 API 服务基础 URL 持久化到本地存储
  // 参数:
  //     url (String): 用户输入的 API 服务基础 URL
  // 返回值: Future<void> - 异步操作完成信号
  // ----------------------------------------------------------------------------
  /// 保存 API 服务地址
  ///
  /// 将用户配置的 MiniMax API 服务基础 URL 持久化到本地存储。
  ///
  /// 参数:
  ///     url - 用户输入的 API 服务基础 URL 字符串
  ///
  /// 使用场景:
  ///     用户在设置页面修改 API 地址后调用
  Future<void> saveApiUrl(String url) async {
    // 获取 SharedPreferences 实例
    final p = await prefs;
    // 将 API URL 写入本地存储，键名为 _keyApiUrl
    await p.setString(_keyApiUrl, url);
  }

  // ============================================================================
  // AI 模型名称管理方法
  // 功能: 提供 AI 模型名称的读取和保存操作
  // 设计思路: 默认使用 MiniMax-M2.5 模型，支持用户切换到其他模型
  // ============================================================================

  // ----------------------------------------------------------------------------
  // 获取模型名称
  // 功能: 从本地存储读取用户配置的 AI 模型名称
  // 参数: 无
  // 返回值: Future<String> - AI 模型名称字符串
  // 设计思路:
  //     - 默认返回 'MiniMax-M2.5'
  //     - 支持用户切换到 MiniMax 平台提供的其他模型
  // ----------------------------------------------------------------------------
  /// 获取 AI 模型名称
  ///
  /// 从本地持久化存储中读取用户配置的 MiniMax AI 模型名称。
  /// 若用户未自行配置，则返回默认模型 'MiniMax-M2.5'。
  ///
  /// 返回值:
  ///     String - MiniMax AI 模型名称
  ///
  /// 使用场景:
  ///     调用 AI 服务时指定使用的模型
  Future<String> getModel() async {
    // 获取 SharedPreferences 实例
    final p = await prefs;
    // 从本地存储读取模型名称，若不存在则返回默认模型 'MiniMax-M2.5'
    // MiniMax-M2.5 是 MiniMax 平台的主力模型，适合文本生成任务
    return p.getString(_keyModel) ?? 'MiniMax-M2.5';
  }

  // ----------------------------------------------------------------------------
  // 保存模型名称
  // 功能: 将用户配置的 AI 模型名称持久化到本地存储
  // 参数:
  //     model (String): 用户选择的 AI 模型名称
  // 返回值: Future<void> - 异步操作完成信号
  // ----------------------------------------------------------------------------
  /// 保存 AI 模型名称
  ///
  /// 将用户配置的 MiniMax AI 模型名称持久化到本地存储。
  ///
  /// 参数:
  ///     model - 用户选择的 AI 模型名称字符串
  ///
  /// 使用场景:
  ///     用户在设置页面切换 AI 模型后调用
  Future<void> saveModel(String model) async {
    // 获取 SharedPreferences 实例
    final p = await prefs;
    // 将模型名称写入本地存储，键名为 _keyModel
    await p.setString(_keyModel, model);
  }
}
