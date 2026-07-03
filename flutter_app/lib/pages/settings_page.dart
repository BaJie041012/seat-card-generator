// ==============================================================================
// 文件名称: settings_page.dart
// 功能描述: 设置页面，提供 MiniMax API 配置界面，包括 API Key、API 地址和模型名称的设置
// 创建日期: 2026-07-03
// 作    者: 戒者有八
// 版本: 2.0.0
// 描述: 本文件实现应用程序的设置界面，用户在此配置 AI 服务的连接参数
// ==============================================================================
/// 设置页面模块 - MiniMax API 配置管理界面
///
/// 本文件实现了应用程序的设置界面，主要功能包括:
///     - API Key 配置: 支持输入和显示/隐藏切换的 API Key 输入框
///     - API 地址配置: 自定义 API 服务地址（通常使用默认值即可）
///     - 模型名称配置: 指定使用的 AI 模型名称
///     - 配置持久化: 保存的配置通过 SettingsService 持久化到本地存储
///     - 使用说明: 提供简洁的操作指引，帮助用户完成配置
///
/// 设计思路:
///     - 使用 StatefulWidget 管理输入控制器和页面状态
///     - 页面初始化时自动加载已保存的配置到输入框
///     - 保存后显示成功提示并自动返回上一页
///     - API Key 输入框支持明文/密文切换，保护敏感信息
///     - 使用 Card 组件分组展示配置项和使用说明
///
/// 使用方式:
///     1. 从主页右上角的设置图标进入此页面
///     2. 或在主页的 API Key 警告卡片中点击"去设置"进入
///     3. 填写或修改配置信息
///     4. 点击右上角"保存"按钮保存配置
///     5. 保存成功后自动返回上一页
///
/// 依赖关系:
///     - settings_service.dart: 设置持久化服务，负责读写配置数据
///
/// 核心组件:
///     - SettingsPage: 设置页面 StatefulWidget 类
///     - _SettingsPageState: 设置页面状态管理类，包含配置加载、保存和 UI 构建
// ==============================================================================

// ---- 导入依赖模块 ----
import 'package:flutter/material.dart';      // Flutter 材料设计组件库
import '../services/settings_service.dart';  // 导入设置服务（用于读写持久化配置）

// ------------------------------------------------------------------------------
// SettingsPage - 设置页面 Widget 类
// 功能: 定义设置页面的框架结构
// 设计思路: 继承 StatefulWidget，因为需要管理输入控制器和保存状态
// ------------------------------------------------------------------------------

/// 设置页面 Widget 类
///
/// 这是应用程序的设置入口页面，采用 StatefulWidget 实现，
/// 因为需要管理以下动态状态:
///     - 三个文本输入控制器的生命周期
///     - API Key 的显示/隐藏状态（_obscureApiKey）
///     - 配置是否已保存的状态（_saved）
///
/// 属性说明:
///     无额外属性，仅使用默认的 key 参数
///
/// 使用示例:
///     ```dart
///     Navigator.push(
///       context,
///       MaterialPageRoute(builder: (_) => const SettingsPage()),
///     );
///     ```
class SettingsPage extends StatefulWidget {
  /// 构造函数，接受可选的 key 参数
  /// const 构造函数确保 Widget 在编译时创建，提高性能
  const SettingsPage({super.key});

  /// 创建状态管理对象
  ///
  /// 返回值:
  ///     _SettingsPageState: 设置页面的状态管理实例
  @override
  State<SettingsPage> createState() => _SettingsPageState();
}

// ------------------------------------------------------------------------------
// _SettingsPageState - 设置页面状态管理类
// 功能: 管理设置页面的所有状态、配置加载/保存逻辑和 UI 构建
// 设计思路: 在 initState 中加载已有配置，用户修改后通过 _save 方法持久化
// ------------------------------------------------------------------------------

/// 设置页面状态管理类（私有类）
///
/// 负责管理设置页面的所有状态和业务逻辑，包括:
///     - 文本输入控制器的创建和销毁
///     - 从本地存储加载已保存的配置
///     - 将用户修改的配置保存到本地存储
///     - 构建设置界面的 UI 布局
///
/// 状态变量:
///     - _settingsService: 设置服务实例，用于读写持久化配置
///     - _apiKeyController: API Key 输入框的文本控制器
///     - _apiUrlController: API 地址输入框的文本控制器
///     - _modelController: 模型名称输入框的文本控制器
///     - _obscureApiKey: API Key 是否以密文显示，默认为 true（隐藏）
///     - _saved: 配置是否已保存，控制保存按钮的状态和文字
class _SettingsPageState extends State<SettingsPage> {
  // ---- 服务实例 ----
  /// 设置服务实例
  /// 用于读写本地持久化的配置信息（API Key、API 地址、模型名称等）
  final _settingsService = SettingsService();

  // ---- 文本输入控制器 ----
  /// API Key 输入框的文本控制器
  /// 用于获取和设置 API Key 输入框的内容
  final _apiKeyController = TextEditingController();

  /// API 地址输入框的文本控制器
  /// 用于获取和设置 API 服务地址输入框的内容
  final _apiUrlController = TextEditingController();

  /// 模型名称输入框的文本控制器
  /// 用于获取和设置 AI 模型名称输入框的内容
  final _modelController = TextEditingController();

  // ---- 页面状态变量 ----
  /// API Key 是否以密文显示
  /// true 表示隐藏（显示为圆点），false 表示明文显示
  /// 默认为 true，保护敏感的 API Key 信息
  bool _obscureApiKey = true;

  /// 配置是否已保存
  /// true 表示配置已成功保存，此时保存按钮变为"已保存"并禁用
  /// 防止用户重复保存
  bool _saved = false;

  // ------------------------------------------------------------------------------
  // 生命周期方法 - initState
  // 功能: 页面初始化时调用，加载已保存的配置
  // ------------------------------------------------------------------------------

  /// 初始化状态
  ///
  /// 在 Widget 首次插入到 Widget 树时调用，执行以下操作:
  ///     1. 调用父类的 initState 确保框架正常初始化
  ///     2. 从本地存储加载已保存的配置到输入框
  ///
  /// 设计说明:
  ///     配置加载是异步操作，在 _loadSettings 方法中实现，
  ///     避免在 initState 中直接执行异步操作导致框架报错
  @override
  void initState() {
    super.initState(); // 调用父类初始化，确保 Flutter 框架正常运作
    _loadSettings(); // 异步加载已保存的配置
  }

  // ------------------------------------------------------------------------------
  // 业务方法 - _loadSettings
  // 功能: 从本地存储加载已保存的配置到输入框
  // ------------------------------------------------------------------------------

  /// 加载已保存的配置
  ///
  /// 从本地持久化存储中读取 API Key、API 地址和模型名称，
  /// 并将它们填充到对应的文本输入框中，方便用户查看和修改。
  ///
  /// 返回值:
  ///     Future<void>: 异步操作，无返回值
  ///
  /// 设计说明:
  ///     - 使用 mounted 检查确保 Widget 仍然在树中，避免在已销毁的 Widget 上操作
  ///     - 三个配置项并行读取，提高加载效率
  Future<void> _loadSettings() async {
    // 从本地存储中并行读取三个配置项
    final key = await _settingsService.getApiKey();      // 读取 API Key
    final url = await _settingsService.getApiUrl();      // 读取 API 地址
    final model = await _settingsService.getModel();      // 读取模型名称
    // 检查 Widget 是否仍然挂载在树中
    if (mounted) {
      // 将读取到的配置值填充到对应的文本控制器中
      _apiKeyController.text = key;    // 设置 API Key 输入框内容
      _apiUrlController.text = url;    // 设置 API 地址输入框内容
      _modelController.text = model;   // 设置模型名称输入框内容
    }
  }

  // ------------------------------------------------------------------------------
  // 生命周期方法 - dispose
  // 功能: 页面销毁时调用，释放文本控制器资源
  // ------------------------------------------------------------------------------

  /// 释放资源
  ///
  /// 在 Widget 从 Widget 树中移除时调用，执行以下清理操作:
  ///     1. 释放 API Key 文本控制器
  ///     2. 释放 API 地址文本控制器
  ///     3. 释放模型名称文本控制器
  ///     4. 调用父类 dispose 完成框架级清理
  ///
  /// 重要说明:
  ///     TextEditingController 必须手动 dispose，否则会造成内存泄漏
  @override
  void dispose() {
    _apiKeyController.dispose();  // 释放 API Key 控制器
    _apiUrlController.dispose();  // 释放 API 地址控制器
    _modelController.dispose();   // 释放模型名称控制器
    super.dispose(); // 调用父类 dispose 完成框架级资源清理
  }

  // ------------------------------------------------------------------------------
  // 核心业务方法 - _save
  // 功能: 将输入框中的配置保存到本地持久化存储
  // ------------------------------------------------------------------------------

  /// 保存配置
  ///
  /// 将三个输入框中的配置值保存到本地持久化存储中，
  /// 保存成功后更新 UI 状态（按钮变为"已保存"），
  /// 显示 SnackBar 提示，并在短暂延迟后自动返回上一页。
  ///
  /// 返回值:
  ///     Future<void>: 异步操作，无返回值
  ///
  /// 设计说明:
  ///     - 保存前对输入值进行 trim 操作，去除首尾空白
  ///     - 保存成功后延迟 500ms 返回，让用户看到"已保存"状态
  ///     - 每个异步操作后都检查 mounted，防止 Widget 销毁后操作 UI
  Future<void> _save() async {
    // 将三个配置项保存到本地持久化存储，trim 去除首尾空白
    await _settingsService.saveApiKey(_apiKeyController.text.trim());  // 保存 API Key
    await _settingsService.saveApiUrl(_apiUrlController.text.trim());  // 保存 API 地址
    await _settingsService.saveModel(_modelController.text.trim());    // 保存模型名称
    // 更新 UI 状态为"已保存"
    setState(() => _saved = true);
    // 检查 Widget 是否仍然挂载
    if (mounted) {
      // 显示保存成功的 SnackBar 提示，持续 1 秒
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('设置已保存'), duration: Duration(seconds: 1)),
      );
      // 延迟 500ms 后自动返回上一页，让用户看到"已保存"状态
      Future.delayed(const Duration(milliseconds: 500), () {
        // 再次检查 mounted，防止延迟期间 Widget 已销毁
        if (mounted) Navigator.pop(context); // 返回上一页
      });
    }
  }

  // ------------------------------------------------------------------------------
  // UI 构建方法 - build
  // 功能: 构建设置页面的完整 UI 界面
  // ------------------------------------------------------------------------------

  /// 构建设置页面 UI
  ///
  /// 构建完整的设置页面布局，从上到下包含:
  ///     1. AppBar: 标题栏，包含"设置"标题和保存按钮
  ///     2. MiniMax API 配置卡片: 包含 API Key、API 地址、模型名称三个输入框
  ///     3. 使用说明卡片: 提供简洁的操作指引
  ///
  /// 参数:
  ///     context: BuildContext - Flutter 构建上下文，用于访问主题和导航
  ///
  /// 返回值:
  ///     Widget: 构建完成的页面 Widget 树
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      // ==== 顶部导航栏 ====
      appBar: AppBar(
        title: const Text('设置'), // 页面标题
        actions: [
          // ---- 保存按钮 ----
          // 使用 TextButton 作为右上角的操作按钮
          TextButton(
            // 已保存时禁用按钮（onPressed 设为 null），否则绑定 _save 方法
            onPressed: _saved ? null : _save,
            child: Text(
              _saved ? '已保存' : '保存', // 根据保存状态显示不同文字
              style: TextStyle(
                  fontWeight: FontWeight.bold,           // 加粗字体
                  color: _saved ? Colors.grey : null),   // 已保存时文字变灰
            ),
          ),
        ],
      ),

      // ==== 页面主体内容 ====
      // 使用 SingleChildScrollView 包裹，支持内容超出时滚动
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16), // 四周内边距 16 像素
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start, // 子组件左对齐
          children: [
            // ==== MiniMax API 配置卡片 ====
            // 包含 API Key、API 地址和模型名称三个配置项
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16), // 卡片内边距
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start, // 子组件左对齐
                  children: [
                    // ---- 卡片标题 ----
                    Text('MiniMax API',
                        style: Theme.of(context).textTheme.titleMedium), // 使用主题样式
                    const SizedBox(height: 12), // 标题与输入框之间的间距

                    // ---- API Key 输入框 ----
                    // 支持明文/密文切换，保护敏感的 API Key
                    TextField(
                      controller: _apiKeyController, // 绑定文本控制器
                      obscureText: _obscureApiKey, // 是否以密文显示
                      decoration: InputDecoration(
                        labelText: 'API Key', // 标签文字
                        hintText: '输入你的 MiniMax API Key', // 灰色提示文字
                        border: const OutlineInputBorder(), // 外边框样式
                        // 右侧的眼睛图标按钮，用于切换明文/密文显示
                        suffixIcon: IconButton(
                          // 根据当前状态显示不同的图标
                          icon: Icon(_obscureApiKey
                              ? Icons.visibility_off   // 当前密文，显示"不可见"图标
                              : Icons.visibility),     // 当前明文，显示"可见"图标
                          // 点击切换明文/密文状态
                          onPressed: () => setState(
                              () => _obscureApiKey = !_obscureApiKey), // 取反切换状态
                        ),
                      ),
                    ),
                    const SizedBox(height: 12), // 输入框之间的间距

                    // ---- API 地址输入框 ----
                    // 通常使用默认值即可，高级用户可自定义
                    TextField(
                      controller: _apiUrlController, // 绑定文本控制器
                      decoration: const InputDecoration(
                        labelText: 'API 地址', // 标签文字
                        border: OutlineInputBorder(), // 外边框样式
                      ),
                    ),
                    const SizedBox(height: 12), // 输入框之间的间距

                    // ---- 模型名称输入框 ----
                    // 指定使用的 AI 模型名称
                    TextField(
                      controller: _modelController, // 绑定文本控制器
                      decoration: const InputDecoration(
                        labelText: '模型名称', // 标签文字
                        border: OutlineInputBorder(), // 外边框样式
                      ),
                    ),
                  ],
                ),
              ),
            ),

            const SizedBox(height: 16), // 配置卡片与说明卡片之间的间距

            // ==== 使用说明卡片 ====
            // 提供简洁的操作指引，帮助用户完成 API 配置
            Card(
              // 使用主题的低容器表面颜色作为背景，与上方配置卡片形成视觉区分
              color: Theme.of(context).colorScheme.surfaceContainerLow,
              child: Padding(
                padding: const EdgeInsets.all(16), // 卡片内边距
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start, // 子组件左对齐
                  children: [
                    // ---- 说明标题 ----
                    Text('使用说明',
                        style: Theme.of(context).textTheme.titleSmall),
                    const SizedBox(height: 8), // 标题与内容之间的间距
                    // ---- 说明正文 ----
                    // 使用 const 常量优化性能，设置行高为 1.5 倍提升可读性
                    const Text(
                      '1. 前往 minimaxi.com 注册账号并获取 API Key\n'
                      '2. 将 API Key 填入上方输入框\n'
                      '3. API 地址默认即可，无需修改\n'
                      '4. 配置完成后返回主页即可开始生成席卡\n\n'
                      '席卡将直接在手机上生成 PDF 文件，\n'
                      '无需连接任何服务器。',
                      style: TextStyle(height: 1.5), // 行高 1.5 倍，提升可读性
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
