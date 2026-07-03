// ==============================================================================
// 文件名称: main.dart
// 功能描述: 席卡生成系统 Flutter 应用入口文件
// 创建日期: 2026-07-03
// 作    者: 戒者有八
// 版本: 2.0.0
// 描述: 本文件是整个 Flutter 席卡生成系统的启动入口，负责初始化 Flutter 引擎
//       绑定、配置应用主题（亮色/暗色）、设置 Material 3 设计语言，并加载
//       首页（HomePage）作为应用的根页面组件。
// ==============================================================================

// ==============================================================================
// 导入依赖模块
// ==============================================================================
// 导入 Flutter Material Design 组件库，提供 MaterialApp、ThemeData 等核心组件
import 'package:flutter/material.dart';
// 导入首页组件，作为应用启动后展示的第一个页面
import 'pages/home_page.dart';

// ------------------------------------------------------------------------------
// 应用主入口函数
// 功能: 初始化 Flutter 引擎并启动应用
// 说明: 这是整个 Flutter 应用的入口点（类似 Python 中的 if __name__ == '__main__'）
// ------------------------------------------------------------------------------
/// 应用程序主入口函数
///
/// 功能说明:
///   1. 初始化 Flutter 引擎绑定（确保平台通道可用）
///   2. 启动根组件 [SeatCardApp]
///
/// 调用流程:
///   main() -> WidgetsFlutterBinding.ensureInitialized() -> runApp(SeatCardApp)
///
/// 注意事项:
///   - 必须在 runApp() 之前调用 WidgetsFlutterBinding.ensureInitialized()
///   - 确保在使用任何 Flutter 服务（如路径提供者、SharedPreferences 等）前完成初始化
void main() {
  // 初始化 Flutter 引擎绑定，确保平台通道（Platform Channel）可用
  // 这是使用任何 Flutter 服务前的必要步骤，类似于 Python 中的初始化配置
  WidgetsFlutterBinding.ensureInitialized();

  // 启动应用根组件 SeatCardApp
  // runApp() 是 Flutter 应用的启动函数，将给定组件挂载到屏幕上
  // 使用 const 构造函数创建实例，编译期优化，减少运行时开销
  runApp(const SeatCardApp());
}

// ------------------------------------------------------------------------------
// 应用根组件类
// 功能: 定义整个应用的基础配置，包括主题、路由、Material Design 风格等
// 设计思路: 继承 StatelessWidget（无状态组件），因为应用级配置在运行时不需要变化
// ------------------------------------------------------------------------------
/// 席卡生成系统应用根组件
///
/// 类说明:
///   [SeatCardApp] 是整个 Flutter 应用的根组件（Root Widget），负责：
///   - 配置 Material Design 3 主题（亮色/暗色双主题）
///   - 设置应用标题和调试选项
///   - 指定首页路由为 [HomePage]
///
/// 属性说明:
///   继承自 StatelessWidget，无自定义属性
///
/// 使用方式:
///   在 main() 函数中通过 runApp(const SeatCardApp()) 启动
///
/// 设计思路:
///   - 使用 StatelessWidget 而非 StatefulWidget，因为应用配置在启动后不需要动态更新
///   - 使用 const 构造函数，允许编译期常量优化，提升性能
///   - 支持 Material 3 设计规范，提供现代化的 UI 体验
class SeatCardApp extends StatelessWidget {
  /// 构造函数，使用 const 修饰以支持编译期常量实例化
  ///
  /// 参数说明:
  ///   [key] - 组件的唯一标识符，用于 Flutter 框架的组件树管理
  ///   super.key 将 key 传递给父类 StatelessWidget 的构造函数
  const SeatCardApp({super.key});

  // --------------------------------------------------------------------------
  // 组件构建方法
  // 功能: 构建应用的 UI 结构，返回 MaterialApp 作为应用的主框架
  // --------------------------------------------------------------------------
  /// 构建应用的主框架
  ///
  /// 参数说明:
  ///   [context] - BuildContext 对象，提供当前组件在组件树中的位置信息
  ///               可用于访问主题、媒体查询、导航等上下文数据
  ///
  /// 返回值:
  ///   MaterialApp - Flutter Material Design 应用主框架，包含：
  ///     - 应用标题: '席卡生成系统'
  ///     - 亮色主题: 蓝色种子色 + Material 3
  ///     - 暗色主题: 蓝色种子色 + Material 3（暗色模式）
  ///     - 主题模式: 跟随系统设置自动切换
  ///     - 首页: HomePage 组件
  ///
  /// 设计说明:
  ///   - 使用 colorSchemeSeed 自动生成完整的配色方案，减少手动配置
  ///   - 启用 Material 3 设计语言，提供现代化的视觉风格
  ///   - 关闭调试模式横幅（debugShowCheckedModeBanner: false），
  ///     避免右上角显示 "DEBUG" 标记，提升用户体验
  ///   - 使用 ThemeMode.system 让应用主题跟随系统设置，
  ///     用户开启深色模式时应用自动切换为暗色主题
  @override
  Widget build(BuildContext context) {
    // 返回 MaterialApp 作为应用的主框架
    // MaterialApp 是 Material Design 风格应用的顶层组件，提供：
    //   - 主题管理（亮色/暗色主题切换）
    //   - 路由导航管理
    //   - 国际化支持
    //   - 调试工具集成
    return MaterialApp(
      // 应用标题，在系统任务管理器中显示为应用名称
      title: '席卡生成系统',

      // 关闭调试模式横幅，避免右上角显示 "DEBUG" 标记
      // 正式发布时必须设置为 false，提升用户体验
      debugShowCheckedModeBanner: false,

      // ======================================================================
      // 亮色主题配置
      // 功能: 定义应用在亮色模式下的视觉风格
      // ======================================================================
      theme: ThemeData(
        // 使用蓝色作为种子色（seed color），Flutter 会自动生成完整的配色方案
        // colorSchemeSeed 是 Material 3 的新特性，替代了旧的 primaryColor 等属性
        colorSchemeSeed: Colors.blue,
        // 启用 Material 3 设计语言，提供最新的 Material Design 视觉风格
        // Material 3 引入了新的组件样式、排版规范和配色系统
        useMaterial3: true,
        // 设置亮度为亮色模式（浅色背景 + 深色文字）
        brightness: Brightness.light,
      ),

      // ======================================================================
      // 暗色主题配置
      // 功能: 定义应用在暗色模式下的视觉风格
      // ======================================================================
      darkTheme: ThemeData(
        // 暗色主题同样使用蓝色作为种子色，保持品牌一致性
        colorSchemeSeed: Colors.blue,
        // 暗色主题也启用 Material 3 设计语言
        useMaterial3: true,
        // 设置亮度为暗色模式（深色背景 + 浅色文字）
        // Flutter 会根据 brightness 自动调整背景色、文字颜色等
        brightness: Brightness.dark,
      ),

      // ======================================================================
      // 主题模式配置
      // 功能: 控制应用使用哪种主题（亮色/暗色/跟随系统）
      // ======================================================================
      // ThemeMode.system 表示跟随操作系统的主题设置
      // 当系统切换为深色模式时，应用自动切换为 darkTheme；反之使用 theme
      themeMode: ThemeMode.system,

      // ======================================================================
      // 首页路由配置
      // 功能: 指定应用启动后显示的第一个页面
      // ======================================================================
      // 使用 HomePage 作为首页，const 修饰以启用编译期优化
      // HomePage 是席卡生成系统的主操作界面，提供文件上传、参数配置、生成操作等功能
      home: const HomePage(),
    );
  }
}
