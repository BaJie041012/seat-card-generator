// ==============================================================================
// 文件名称: home_page.dart
// 功能描述: 应用程序主页，提供人员信息输入、活动名称设置、显示类型选择及席卡生成功能
// 创建日期: 2026-07-03
// 作    者: 戒者有八
// 版本: 2.0.0
// 描述: 本文件是席卡生成系统的主界面，用户在此输入人员信息并触发生成流程
// ==============================================================================
/// 主页模块 - 席卡生成系统的核心入口页面
///
/// 本文件实现了应用程序的主界面，主要功能包括:
///     - 人员信息输入: 支持多种格式的人员信息批量输入
///     - 活动名称设置: 可选的活动名称字段，用于席卡标题
///     - 显示类型选择: 选择席卡上显示姓名还是公司名
///     - API Key 状态检测: 自动检测是否已配置 API Key，未配置时给出提示
///     - 一键生成: 调用 AI 服务提取人员信息，本地生成 PDF 席卡
///     - 结果跳转: 生成完成后自动跳转到结果页面
///
/// 设计思路:
///     - 使用 StatefulWidget 管理页面状态（加载中、API Key 状态等）
///     - 通过 SettingsService 读取本地持久化的配置信息
///     - 通过 MiniMaxService 调用 AI 接口提取人员信息
///     - 通过 CardGeneratorService 在本地生成 PDF 席卡文件
///     - 生成流程分为三步: AI提取 → 本地生成 → 跳转结果页
///
/// 使用方式:
///     1. 应用程序启动后自动加载此页面作为首页
///     2. 在输入框中填写人员信息（支持多种分隔格式）
///     3. 可选填写活动名称
///     4. 选择席卡显示内容（姓名/公司名）
///     5. 点击"生成席卡"按钮触发完整生成流程
///
/// 依赖关系:
///     - card_models.dart: 数据模型定义（DisplayType 枚举等）
///     - minimax_service.dart: AI 服务，用于提取人员信息
///     - card_generator.dart: 本地 PDF 席卡生成服务
///     - settings_service.dart: 设置持久化服务
///     - settings_page.dart: 设置页面（用于跳转配置 API Key）
///     - result_page.dart: 结果展示页面（用于跳转查看生成结果）
///
/// 核心组件:
///     - HomePage: 主页 StatefulWidget 类
///     - _HomePageState: 主页状态管理类，包含所有业务逻辑和 UI 构建
// ==============================================================================

// ---- 导入依赖模块 ----
import 'package:flutter/material.dart';          // Flutter 材料设计组件库
import '../models/card_models.dart';              // 导入数据模型（DisplayType 枚举、CardResult 等）
import '../services/minimax_service.dart';        // 导入 MiniMax AI 服务（用于提取人员信息）
import '../services/card_generator.dart';         // 导入席卡生成服务（用于本地生成 PDF）
import '../services/settings_service.dart';       // 导入设置服务（用于读写 API Key 等配置）
import 'settings_page.dart';                      // 导入设置页面（用于跳转配置）
import 'result_page.dart';                        // 导入结果页面（用于跳转查看结果）

// ------------------------------------------------------------------------------
// HomePage - 主页 Widget 类
// 功能: 定义席卡生成系统的主页面框架
// 设计思路: 继承 StatefulWidget，因为页面需要管理动态状态（加载状态、API Key 状态等）
// ------------------------------------------------------------------------------

/// 主页 Widget 类
///
/// 这是应用程序的主入口页面，采用 StatefulWidget 实现，
/// 因为需要管理以下动态状态:
///     - 生成按钮的加载状态（_isGenerating）
///     - API Key 是否已配置（_hasApiKey）
///     - 用户选择的显示类型（_displayType）
///
/// 属性说明:
///     无额外属性，仅使用默认的 key 参数
///
/// 使用示例:
///     ```dart
///     MaterialApp(
///       home: const HomePage(),
///     )
///     ```
class HomePage extends StatefulWidget {
  /// 构造函数，接受可选的 key 参数
  /// const 构造函数确保 Widget 在编译时创建，提高性能
  const HomePage({super.key});

  /// 创建状态管理对象
  ///
  /// 返回值:
  ///     _HomePageState: 主页的状态管理实例
  @override
  State<HomePage> createState() => _HomePageState();
}

// ------------------------------------------------------------------------------
// _HomePageState - 主页状态管理类
// 功能: 管理主页的所有状态、业务逻辑和 UI 构建
// 设计思路: 集中管理文本控制器、服务实例和页面状态，
//           在生命周期方法中完成初始化和资源释放
// ------------------------------------------------------------------------------

/// 主页状态管理类（私有类）
///
/// 负责管理主页的所有状态和业务逻辑，包括:
///     - 文本输入控制器管理
///     - API Key 状态检测
///     - 席卡生成流程编排
///     - UI 界面构建
///
/// 状态变量:
///     - _inputController: 人员信息输入框的文本控制器
///     - _eventController: 活动名称输入框的文本控制器
///     - _settingsService: 设置服务实例，用于读写持久化配置
///     - _displayType: 席卡显示类型（姓名/公司名），默认为姓名
///     - _isGenerating: 是否正在生成中，控制按钮和加载指示器
///     - _hasApiKey: API Key 是否已配置，控制警告提示的显示
class _HomePageState extends State<HomePage> {
  // ---- 文本输入控制器 ----
  /// 人员信息输入框的文本控制器
  /// 用于获取用户输入的人员信息文本，支持多行输入
  final _inputController = TextEditingController();

  /// 活动名称输入框的文本控制器
  /// 用于获取用户输入的活动名称，该名称将显示在席卡上
  final _eventController = TextEditingController();

  // ---- 服务实例 ----
  /// 设置服务实例
  /// 用于读写本地持久化的配置信息（API Key、API 地址、模型名称等）
  final _settingsService = SettingsService();

  // ---- 页面状态变量 ----
  /// 席卡显示类型
  /// 控制席卡上显示的内容：姓名（DisplayType.name）或公司名（DisplayType.company）
  /// 默认值为 DisplayType.name（显示姓名）
  DisplayType _displayType = DisplayType.name;

  /// 是否正在生成中
  /// 当为 true 时，生成按钮显示加载指示器并禁用点击
  /// 防止用户在生成过程中重复点击触发多次生成
  bool _isGenerating = false;

  /// API Key 是否已配置
  /// 当为 false 时，页面顶部显示警告卡片提示用户配置 API Key
  /// 在页面初始化时和从设置页返回时进行检查
  bool _hasApiKey = false;

  // ------------------------------------------------------------------------------
  // 生命周期方法 - initState
  // 功能: 页面初始化时调用，执行一次性设置
  // ------------------------------------------------------------------------------

  /// 初始化状态
  ///
  /// 在 Widget 首次插入到 Widget 树时调用，执行以下操作:
  ///     1. 调用父类的 initState 确保框架正常初始化
  ///     2. 检查 API Key 是否已配置，更新 UI 提示状态
  ///
  /// 设计说明:
  ///     API Key 检查是异步操作，在 _checkApiKey 方法中实现，
  ///     避免在 initState 中直接执行异步操作导致框架报错
  @override
  void initState() {
    super.initState(); // 调用父类初始化，确保 Flutter 框架正常运作
    _checkApiKey(); // 异步检查 API Key 是否已配置
  }

  // ------------------------------------------------------------------------------
  // 业务方法 - _checkApiKey
  // 功能: 检查 API Key 是否已配置，更新页面状态
  // ------------------------------------------------------------------------------

  /// 检查 API Key 配置状态
  ///
  /// 从本地持久化存储中读取 API Key，根据是否为空更新 _hasApiKey 状态。
  /// 当 _hasApiKey 为 false 时，页面顶部会显示警告提示卡片。
  ///
  /// 返回值:
  ///     Future<void>: 异步操作，无返回值
  ///
  /// 设计说明:
  ///     - 使用 mounted 检查确保 Widget 仍然在树中，避免 setState 报错
  ///     - 此方法在页面初始化和从设置页返回时都会被调用
  Future<void> _checkApiKey() async {
    // 从本地存储中读取 API Key
    final key = await _settingsService.getApiKey();
    // 检查 Widget 是否仍然挂载在树中，防止异步操作完成后 Widget 已销毁导致异常
    if (mounted) setState(() => _hasApiKey = key.isNotEmpty); // 更新 API Key 状态
  }

  // ------------------------------------------------------------------------------
  // 生命周期方法 - dispose
  // 功能: 页面销毁时调用，释放资源防止内存泄漏
  // ------------------------------------------------------------------------------

  /// 释放资源
  ///
  /// 在 Widget 从 Widget 树中移除时调用，执行以下清理操作:
  ///     1. 释放人员信息文本控制器占用的资源
  ///     2. 释放活动名称文本控制器占用的资源
  ///     3. 调用父类 dispose 完成框架级清理
  ///
  /// 重要说明:
  ///     TextEditingController 必须手动 dispose，否则会造成内存泄漏
  ///     必须在 super.dispose() 之前完成自有资源的释放
  @override
  void dispose() {
    _inputController.dispose(); // 释放人员信息输入控制器
    _eventController.dispose(); // 释放活动名称输入控制器
    super.dispose(); // 调用父类 dispose 完成框架级资源清理
  }

  // ------------------------------------------------------------------------------
  // 核心业务方法 - _generate
  // 功能: 执行完整的席卡生成流程（AI提取 → 本地生成 → 跳转结果）
  // ------------------------------------------------------------------------------

  /// 执行席卡生成流程
  ///
  /// 这是主页的核心业务方法，执行完整的三步生成流程:
  ///     Step 1: 调用 AI 服务从用户输入的文本中提取结构化人员信息
  ///     Step 2: 使用本地服务根据提取的人员信息生成 PDF 席卡文件
  ///     Step 3: 跳转到结果页面展示生成结果
  ///
  /// 返回值:
  ///     Future<void>: 异步操作，无返回值
  ///
  /// 异常处理:
  ///     - 输入为空时弹出提示并终止
  ///     - API Key 未配置时弹出提示并跳转到设置页
  ///     - AI 未提取到信息时弹出提示并终止
  ///     - 生成过程中发生异常时弹出错误提示
  ///
  /// 设计说明:
  ///     - 使用 try-catch 捕获所有异常，确保 UI 状态正确恢复
  ///     - 每个异步操作后都检查 mounted，防止 Widget 销毁后操作 UI
  ///     - 生成过程中设置 _isGenerating = true 禁用按钮防止重复触发
  Future<void> _generate() async {
    // ==== Step 0: 输入验证 ====
    // 获取用户输入的人员信息文本，并去除首尾空白字符
    final text = _inputController.text.trim();
    // 检查输入是否为空
    if (text.isEmpty) {
      // 输入为空时，显示 SnackBar 提示用户输入人员信息
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('请输入人员信息')),
      );
      return; // 终止生成流程
    }

    // ==== 检查 API Key 配置 ====
    // 从本地存储中读取 API Key
    final apiKey = await _settingsService.getApiKey();
    // 检查 API Key 是否为空
    if (apiKey.isEmpty) {
      // API Key 未配置，显示提示
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('请先配置 API Key')),
      );
      // 自动跳转到设置页面，引导用户配置 API Key
      Navigator.push(context, MaterialPageRoute(builder: (_) => const SettingsPage()));
      return; // 终止生成流程
    }

    // ==== 设置生成中状态 ====
    // 更新 UI 状态为"生成中"，按钮将显示加载指示器并禁用
    setState(() => _isGenerating = true);

    try {
      // ==== Step 1: AI 提取人员信息 ====
      // 从设置服务中读取 API 地址配置
      final apiUrl = await _settingsService.getApiUrl();
      // 从设置服务中读取模型名称配置
      final model = await _settingsService.getModel();

      // 创建 MiniMax AI 服务实例，传入 API Key、地址和模型名称
      final miniMax = MiniMaxService(
        apiKey: apiKey,           // API 访问密钥
        apiBaseUrl: apiUrl,       // API 服务地址
        model: model,             // AI 模型名称
      );

      // 调用 AI 服务从用户输入的文本中提取结构化人员信息
      // 返回 PersonInfo 列表，每个元素包含姓名、公司、职位等字段
      final infos = await miniMax.extractFromText(text);
      // 检查是否成功提取到人员信息
      if (infos.isEmpty) {
        // 未提取到信息，检查 Widget 是否仍然挂载
        if (!mounted) return;
        // 恢复生成状态为 false
        setState(() => _isGenerating = false);
        // 显示提示，告知用户未提取到人员信息
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('未提取到人员信息，请检查输入内容')),
        );
        return; // 终止生成流程
      }

      // ==== Step 2: 本地生成 PDF 席卡 ====
      // 创建席卡生成服务实例
      final generator = CardGeneratorService();
      // 调用生成服务，传入人员信息、活动名称和显示类型
      // 返回 GenerateResult 对象，包含所有席卡的生成结果
      final result = await generator.generateCards(
        infos: infos,                         // AI 提取的人员信息列表
        eventName: _eventController.text.trim(), // 活动名称（可选）
        displayType: _displayType,            // 席卡显示类型（姓名/公司名）
      );

      // 检查 Widget 是否仍然挂载（异步操作后必须检查）
      if (!mounted) return;
      // 恢复生成状态为 false，按钮恢复正常
      setState(() => _isGenerating = false);

      // ==== Step 3: 跳转结果页 ====
      // 使用 Navigator.push 跳转到结果页面，传递生成结果
      Navigator.push(context, MaterialPageRoute(
        builder: (_) => ResultPage(result: result), // 传入生成结果数据
      ));
    } catch (e) {
      // ==== 异常处理 ====
      // 检查 Widget 是否仍然挂载
      if (!mounted) return;
      // 恢复生成状态为 false
      setState(() => _isGenerating = false);
      // 显示错误信息，将异常对象转为字符串展示
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('生成失败: $e')),
      );
    }
  }

  // ------------------------------------------------------------------------------
  // UI 构建方法 - build
  // 功能: 构建主页的完整 UI 界面
  // ------------------------------------------------------------------------------

  /// 构建主页 UI
  ///
  /// 构建完整的页面布局，从上到下包含:
  ///     1. AppBar: 标题栏，包含"席卡生成系统"标题和设置按钮
  ///     2. API Key 警告卡片: 未配置 API Key 时显示（条件渲染）
  ///     3. 输入区域卡片: 包含人员信息输入框、活动名称输入框、显示类型选择器
  ///     4. 生成按钮: 触发生成流程，支持加载状态显示
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
        title: const Text('席卡生成系统'), // 页面标题
        actions: [
          // 设置按钮，点击后跳转到设置页面
          IconButton(
            icon: const Icon(Icons.settings), // 齿轮图标
            onPressed: () async {
              // 跳转到设置页面并等待返回
              await Navigator.push(
                context,
                MaterialPageRoute(builder: (_) => const SettingsPage()),
              );
              // 从设置页返回后重新检查 API Key 状态
              _checkApiKey();
            },
          ),
        ],
      ),

      // ==== 页面主体内容 ====
      // 使用 SingleChildScrollView 包裹，支持内容超出时滚动
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16), // 四周内边距 16 像素
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch, // 子组件横向拉伸填满
          children: [
            // ==== API Key 未配置警告卡片 ====
            // 条件渲染: 仅在 _hasApiKey 为 false 时显示
            if (!_hasApiKey)
              Card(
                // 使用主题的错误容器颜色作为背景，醒目提示
                color: Theme.of(context).colorScheme.errorContainer,
                child: Padding(
                  padding: const EdgeInsets.all(12), // 卡片内边距
                  child: Row(
                    children: [
                      // 警告图标，使用主题的 error 颜色
                      Icon(Icons.warning_amber,
                          color: Theme.of(context).colorScheme.error),
                      const SizedBox(width: 12), // 图标与文字之间的间距
                      // 警告文字，横向扩展填满剩余空间
                      Expanded(
                        child: Text(
                          '未配置 API Key，点击右侧设置按钮配置',
                          style: TextStyle(
                              color: Theme.of(context).colorScheme.onErrorContainer),
                        ),
                      ),
                      // "去设置"按钮，点击后跳转到设置页面
                      TextButton(
                        onPressed: () async {
                          // 跳转到设置页面并等待返回
                          await Navigator.push(
                            context,
                            MaterialPageRoute(builder: (_) => const SettingsPage()),
                          );
                          // 返回后重新检查 API Key 状态
                          _checkApiKey();
                        },
                        child: const Text('去设置'),
                      ),
                    ],
                  ),
                ),
              ),

            const SizedBox(height: 16), // 警告卡片与输入区域之间的间距

            // ==== 输入区域卡片 ====
            // 包含人员信息输入、活动名称输入和显示类型选择
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16), // 卡片内边距
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start, // 子组件左对齐
                  children: [
                    // ---- 人员信息标签 ----
                    Text('人员信息',
                        style: Theme.of(context).textTheme.titleMedium), // 使用主题样式
                    const SizedBox(height: 8), // 标签与输入框之间的间距

                    // ---- 人员信息多行输入框 ----
                    TextField(
                      controller: _inputController, // 绑定文本控制器
                      maxLines: 8,  // 最大显示行数，超出后滚动
                      minLines: 5,  // 最小显示行数，确保足够的输入空间
                      decoration: const InputDecoration(
                        // 提示文本，展示支持的输入格式示例
                        hintText: '输入人员信息，支持多种格式：\n'
                            '张三 北京科技有限公司 高级工程师\n'
                            '李四，上海数据集团，产品经理\n'
                            '王五 - 深圳创新科技 - 技术总监',
                        border: OutlineInputBorder(), // 使用外边框样式
                      ),
                    ),
                    const SizedBox(height: 16), // 输入框之间的间距

                    // ---- 活动名称输入框 ----
                    TextField(
                      controller: _eventController, // 绑定文本控制器
                      decoration: const InputDecoration(
                        labelText: '活动名称（可选）', // 标签文字，输入后浮起到边框上
                        hintText: '如：2026年度工作会议', // 灰色提示文字
                        border: OutlineInputBorder(), // 使用外边框样式
                      ),
                    ),
                    const SizedBox(height: 16), // 输入框与显示类型选择器之间的间距

                    // ---- 显示类型选择区域 ----
                    // 标签文字
                    Text('显示内容',
                        style: Theme.of(context).textTheme.titleSmall),
                    const SizedBox(height: 8), // 标签与选择器之间的间距

                    // 分段按钮选择器，用于选择席卡上显示的内容类型
                    SegmentedButton<DisplayType>(
                      segments: const [
                        // 选项1: 显示姓名
                        ButtonSegment(
                          value: DisplayType.name,       // 枚举值
                          label: Text('姓名'),            // 按钮文字
                          icon: Icon(Icons.person),       // 人物图标
                        ),
                        // 选项2: 显示公司名
                        ButtonSegment(
                          value: DisplayType.company,    // 枚举值
                          label: Text('公司名'),          // 按钮文字
                          icon: Icon(Icons.business),    // 公司图标
                        ),
                      ],
                      selected: {_displayType}, // 当前选中的值（集合形式）
                      // 选择变更回调，更新状态并刷新 UI
                      onSelectionChanged: (v) =>
                          setState(() => _displayType = v.first), // 取集合中第一个值
                    ),
                  ],
                ),
              ),
            ),

            const SizedBox(height: 16), // 输入区域与生成按钮之间的间距

            // ==== 生成按钮 ====
            // 使用 FilledButton.icon 同时显示图标和文字
            FilledButton.icon(
              // 生成中时禁用按钮（onPressed 设为 null），否则绑定 _generate 方法
              onPressed: _isGenerating ? null : _generate,
              // 图标区域: 生成中显示加载指示器，否则显示打印图标
              icon: _isGenerating
                  ? const SizedBox(
                      width: 20,                              // 加载指示器宽度
                      height: 20,                             // 加载指示器高度
                      child: CircularProgressIndicator(strokeWidth: 2), // 圆形加载动画
                    )
                  : const Icon(Icons.print), // 打印图标
              // 按钮文字: 生成中显示"生成中..."，否则显示"生成席卡"
              label: Text(_isGenerating ? '生成中...' : '生成席卡'),
              // 按钮样式配置
              style: FilledButton.styleFrom(
                minimumSize: const Size(double.infinity, 52), // 宽度填满，高度 52 像素
                textStyle: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold), // 文字样式
              ),
            ),
          ],
        ),
      ),
    );
  }
}
