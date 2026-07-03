// ==============================================================================
// 文件名称: result_page.dart
// 功能描述: 生成结果页面，展示席卡生成的汇总统计、单个席卡列表和失败信息
// 创建日期: 2026-07-03
// 作    者: 戒者有八
// 版本: 2.0.0
// 描述: 本文件展示席卡生成完成后的结果，支持打开和分享生成的 PDF 文件
// ==============================================================================
/// 结果展示页面模块 - 席卡生成结果的查看和管理界面
///
/// 本文件实现了席卡生成完成后的结果展示界面，主要功能包括:
///     - 汇总统计: 显示成功、失败和总计的席卡数量
///     - 合并 PDF 操作: 如果生成了合并 PDF，提供打开和分享功能
///     - 单个席卡列表: 展示每个成功生成的席卡，支持打开和分享
///     - 失败信息展示: 列出所有生成失败的席卡及其错误原因
///     - 输出目录信息: 显示文件保存的目录路径
///
/// 设计思路:
///     - 使用 StatelessWidget 实现，因为页面不需要管理自身状态
///     - 所有数据通过构造函数传入的 GenerateResult 对象提供
///     - 使用 ListView 实现可滚动的结果列表
///     - 通过 share_plus 插件实现系统级文件分享
///     - 通过 open_filex 插件实现调用系统默认应用打开文件
///
/// 使用方式:
///     1. 从主页生成完成后自动跳转至此页面
///     2. 查看生成结果汇总
///     3. 点击打开按钮使用系统默认应用查看 PDF 文件
///     4. 点击分享按钮通过系统分享功能发送 PDF 文件
///
/// 依赖关系:
///     - dart:io: 用于文件存在性检查
///     - share_plus: 系统级文件分享插件
///     - open_filex: 调用系统默认应用打开文件
///     - card_models.dart: 数据模型定义（GenerateResult、CardResult）
///
/// 核心组件:
///     - ResultPage: 结果页面 StatelessWidget 类
///     - _shareFile: 文件分享方法
///     - _openFile: 文件打开方法
///     - _buildStat: 统计数字构建辅助方法
// ==============================================================================

// ---- 导入依赖模块 ----
import 'dart:io';                                    // Dart IO 库，用于文件操作（检查文件是否存在）
import 'package:flutter/material.dart';              // Flutter 材料设计组件库
import 'package:share_plus/share_plus.dart';         // 系统级文件分享插件
import 'package:open_filex/open_filex.dart';         // 调用系统默认应用打开文件
import '../models/card_models.dart';                 // 导入数据模型（GenerateResult、CardResult）

// ------------------------------------------------------------------------------
// ResultPage - 结果展示页面 Widget 类
// 功能: 展示席卡生成结果，提供文件打开和分享功能
// 设计思路: 使用 StatelessWidget，所有数据通过 GenerateResult 参数传入
// ------------------------------------------------------------------------------

/// 结果展示页面 Widget 类
///
/// 这是席卡生成完成后的结果展示页面，采用 StatelessWidget 实现，
/// 因为页面不需要管理自身状态，所有数据都从外部传入。
///
/// 页面布局从上到下:
///     1. 汇总统计卡片: 显示成功/失败/总计数量，以及合并 PDF 的操作入口
///     2. 单个席卡列表: 展示每个成功生成的席卡文件
///     3. 失败列表: 展示生成失败的席卡及错误原因（如有）
///     4. 输出目录信息: 显示文件保存路径
///
/// 属性说明:
///     - result: GenerateResult 对象，包含所有席卡的生成结果数据
class ResultPage extends StatelessWidget {
  /// 生成结果数据
  /// 包含所有席卡的生成结果、合并 PDF 路径、输出目录等信息
  final GenerateResult result;

  /// 构造函数
  ///
  /// 参数:
  ///     key: Widget 的标识键（可选）
  ///     result: GenerateResult - 生成结果数据，必填参数
  const ResultPage({super.key, required this.result});

  // ------------------------------------------------------------------------------
  // 文件操作方法 - _shareFile
  // 功能: 通过系统分享功能分享指定的 PDF 文件
  // ------------------------------------------------------------------------------

  /// 分享文件
  ///
  /// 将指定路径的文件通过系统分享功能发送出去。
  /// 分享前会检查文件是否存在，不存在时显示错误提示。
  ///
  /// 参数:
  ///     context: BuildContext - Flutter 构建上下文，用于显示错误提示
  ///     filePath: String - 要分享的文件绝对路径
  ///
  /// 返回值:
  ///     Future<void>: 异步操作，无返回值
  ///
  /// 设计说明:
  ///     - 先检查文件是否存在，避免分享不存在的文件导致崩溃
  ///     - 使用 share_plus 插件的 shareXFiles 方法实现系统级分享
  ///     - 文件不存在时通过 SnackBar 提示用户
  Future<void> _shareFile(BuildContext context, String filePath) async {
    // 创建文件对象，用于检查文件是否存在
    final file = File(filePath);
    // 异步检查文件是否存在
    if (!await file.exists()) {
      // 文件不存在，检查 Widget 是否仍然挂载
      if (context.mounted) {
        // 显示"文件不存在"的错误提示
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('文件不存在')),
        );
      }
      return; // 终止分享操作
    }
    // 调用系统分享功能，将文件作为 XFile 分享出去
    // XFile 是 share_plus 插件定义的文件包装类，支持跨平台文件分享
    await Share.shareXFiles([XFile(filePath)]);
  }

  // ------------------------------------------------------------------------------
  // 文件操作方法 - _openFile
  // 功能: 使用系统默认应用打开指定的 PDF 文件
  // ------------------------------------------------------------------------------

  /// 打开文件
  ///
  /// 使用系统默认应用打开指定路径的文件。
  /// 打开失败时显示错误提示信息。
  ///
  /// 参数:
  ///     context: BuildContext - Flutter 构建上下文，用于显示错误提示
  ///     filePath: String - 要打开的文件绝对路径
  ///
  /// 返回值:
  ///     Future<void>: 异步操作，无返回值
  ///
  /// 设计说明:
  ///     - 使用 open_filex 插件调用系统默认应用（如 PDF 阅读器）打开文件
  ///     - 检查返回结果类型，非 ResultType.done 表示打开失败
  ///     - 失败时通过 SnackBar 显示具体的错误信息
  Future<void> _openFile(BuildContext context, String filePath) async {
    // 调用系统默认应用打开文件，返回操作结果
    final result = await OpenFilex.open(filePath);
    // 检查操作结果是否成功
    if (result.type != ResultType.done && context.mounted) {
      // 打开失败，显示错误信息（result.message 包含具体的错误原因）
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('打开失败: ${result.message}')),
      );
    }
  }

  // ------------------------------------------------------------------------------
  // UI 构建方法 - build
  // 功能: 构建结果展示页面的完整 UI 界面
  // ------------------------------------------------------------------------------

  /// 构建结果页面 UI
  ///
  /// 构建完整的結果页面布局，从上到下包含:
  ///     1. AppBar: 标题栏，显示"生成结果"
  ///     2. 汇总统计卡片: 成功/失败/总计数量 + 合并 PDF 操作入口
  ///     3. 单个席卡列表: 每个成功生成的席卡，带打开和分享按钮
  ///     4. 失败列表: 生成失败的席卡及错误原因（条件渲染）
  ///     5. 输出目录信息: 文件保存路径
  ///
  /// 参数:
  ///     context: BuildContext - Flutter 构建上下文，用于访问主题和导航
  ///
  /// 返回值:
  ///     Widget: 构建完成的页面 Widget 树
  @override
  Widget build(BuildContext context) {
    // ==== 数据预处理 ====
    // 从生成结果中筛选出成功的席卡列表
    final successCards = result.cards.where((c) => c.success).toList();
    // 从生成结果中筛选出失败的席卡列表
    final failedCards = result.cards.where((c) => !c.success).toList();

    return Scaffold(
      // ==== 顶部导航栏 ====
      appBar: AppBar(
        title: const Text('生成结果'), // 页面标题
      ),

      // ==== 页面主体内容 ====
      // 使用 ListView 实现可滚动的结果列表
      body: ListView(
        padding: const EdgeInsets.all(16), // 四周内边距 16 像素
        children: [
          // ==== 汇总统计卡片 ====
          // 显示生成结果的统计信息和合并 PDF 操作入口
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16), // 卡片内边距
              child: Column(
                children: [
                  // ---- 统计数字行 ----
                  // 水平排列三个统计数字: 成功、失败、总计
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceAround, // 均匀分布
                    children: [
                      // 成功数量统计，绿色显示
                      _buildStat(context, '成功', result.successCount, Colors.green),
                      // 失败数量统计，红色显示
                      _buildStat(context, '失败', result.failCount, Colors.red),
                      // 总计数量统计，蓝色显示
                      _buildStat(context, '总计', result.cards.length, Colors.blue),
                    ],
                  ),

                  // ---- 合并 PDF 操作区域 ----
                  // 条件渲染: 仅在存在合并 PDF 文件时显示
                  if (result.combinedPdfPath != null) ...[
                    const Divider(height: 24), // 分隔线，高度 24 像素（包含上下间距）
                    // 合并 PDF 文件的操作入口
                    ListTile(
                      leading: const Icon(Icons.picture_as_pdf, color: Colors.red), // PDF 图标
                      title: const Text('席卡合集 PDF'),       // 标题
                      subtitle: const Text('包含所有席卡的合并文件'), // 副标题说明
                      trailing: Row(
                        mainAxisSize: MainAxisSize.min, // 最小宽度，避免占据过多空间
                        children: [
                          // 打开按钮: 使用系统默认应用打开合并 PDF
                          IconButton(
                            icon: const Icon(Icons.open_in_new), // 打开图标
                            onPressed: () => _openFile(context, result.combinedPdfPath!), // 调用打开方法
                          ),
                          // 分享按钮: 通过系统分享功能分享合并 PDF
                          IconButton(
                            icon: const Icon(Icons.share), // 分享图标
                            onPressed: () => _shareFile(context, result.combinedPdfPath!), // 调用分享方法
                          ),
                        ],
                      ),
                    ),
                  ],
                ],
              ),
            ),
          ),

          const SizedBox(height: 16), // 统计卡片与席卡列表之间的间距

          // ==== 单个席卡列表标题 ====
          Text('单个席卡', style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: 8), // 标题与列表之间的间距

          // ==== 成功席卡列表 ====
          // 使用展开运算符 (...) 将 map 生成的 Iterable 展开为列表元素
          // 每个成功的席卡渲染为一个 Card，包含打开和分享按钮
          ...successCards.map((card) => Card(
                child: ListTile(
                  leading: const Icon(Icons.check_circle, color: Colors.green), // 绿色对勾图标
                  // 标题显示席卡的显示名称（姓名或公司名）
                  title: Text(card.displayName),
                  // 副标题显示文件名（从完整路径中提取最后一段）
                  subtitle: Text(File(card.filePath).uri.pathSegments.last),
                  trailing: Row(
                    mainAxisSize: MainAxisSize.min, // 最小宽度
                    children: [
                      // 打开按钮: 使用系统默认应用打开单个席卡 PDF
                      IconButton(
                        icon: const Icon(Icons.open_in_new, size: 20), // 稍小的打开图标
                        onPressed: () => _openFile(context, card.filePath), // 调用打开方法
                      ),
                      // 分享按钮: 通过系统分享功能分享单个席卡 PDF
                      IconButton(
                        icon: const Icon(Icons.share, size: 20), // 稍小的分享图标
                        onPressed: () => _shareFile(context, card.filePath), // 调用分享方法
                      ),
                    ],
                  ),
                ),
              )),

          // ==== 失败席卡列表 ====
          // 条件渲染: 仅在存在失败的席卡时显示此区域
          if (failedCards.isNotEmpty) ...[
            const SizedBox(height: 16), // 与上方列表的间距
            // 失败列表标题
            Text('生成失败', style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 8), // 标题与列表之间的间距
            // 遍历失败的席卡，每个渲染为一个带错误颜色的 Card
            ...failedCards.map((card) => Card(
                  // 使用主题的错误容器颜色作为背景，醒目提示
                  color: Theme.of(context).colorScheme.errorContainer,
                  child: ListTile(
                    // 错误图标，使用主题的 error 颜色
                    leading: Icon(Icons.error,
                        color: Theme.of(context).colorScheme.error),
                    // 标题显示失败席卡的显示名称
                    title: Text(card.displayName),
                    // 副标题显示错误原因，如果 error 为 null 则显示"未知错误"
                    subtitle: Text(card.error ?? '未知错误'),
                  ),
                )),
          ],

          const SizedBox(height: 24), // 列表与底部信息之间的间距

          // ==== 输出目录信息卡片 ====
          // 显示文件保存的目录路径，方便用户查找文件
          Card(
            // 使用主题的低容器表面颜色作为背景
            color: Theme.of(context).colorScheme.surfaceContainerLow,
            child: Padding(
              padding: const EdgeInsets.all(12), // 卡片内边距
              child: Text(
                '文件保存在: ${result.outputDir}', // 显示输出目录路径
                style: const TextStyle(fontSize: 12), // 小号字体，次要信息
              ),
            ),
          ),
        ],
      ),
    );
  }

  // ------------------------------------------------------------------------------
  // 辅助 UI 方法 - _buildStat
  // 功能: 构建统计数字组件（数字 + 标签的垂直排列）
  // ------------------------------------------------------------------------------

  /// 构建统计数字组件
  ///
  /// 创建一个垂直排列的统计组件，包含大字号的数字和小字号的标签。
  /// 用于在汇总统计卡片中显示成功、失败、总计的数量。
  ///
  /// 参数:
  ///     context: BuildContext - Flutter 构建上下文，用于访问主题样式
  ///     label: String - 统计标签文字（如"成功"、"失败"、"总计"）
  ///     count: int - 统计数量
  ///     color: Color - 数字显示颜色
  ///
  /// 返回值:
  ///     Widget: 包含数字和标签的垂直排列组件
  ///
  /// 设计说明:
  ///     - 数字使用 28 号加粗字体，颜色由参数指定
  ///     - 标签使用主题定义的 bodySmall 样式，颜色为默认文字颜色
  Widget _buildStat(BuildContext context, String label, int count, Color color) {
    return Column(
      children: [
        // 统计数字，大字号加粗，颜色由参数指定
        Text('$count',
            style: TextStyle(fontSize: 28, fontWeight: FontWeight.bold, color: color)),
        // 统计标签，使用主题的小号文字样式
        Text(label, style: Theme.of(context).textTheme.bodySmall),
      ],
    );
  }
}
