// ==============================================================================
// 文件名称: card_generator.dart
// 功能描述: 席卡 PDF 本地生成服务模块，使用 pdf 包在设备端直接生成席卡 PDF 文件
// 创建日期: 2026-07-03
// 作    者: 戒者有八
// 版本: 2.0.0
// 描述: 本文件负责席卡 PDF 的核心生成逻辑，包括单个席卡 PDF 的创建、批量席卡生成、
//       以及多席卡合集 PDF 的合并输出。所有 PDF 生成操作均在本地设备完成，无需网络
//       连接或服务器支持。支持中文显示（使用 Noto Sans SC 字体）、姓名格式化
//       （两字中文名中间加全角空格）、安全文件名处理等功能。
//
// 设计思路:
//     - 使用 pdf 包（pw 前缀）在设备端直接生成 PDF，无需服务器交互
//     - 中文字体采用懒加载模式，首次使用时从 assets 加载并缓存
//     - 支持两种显示模式：按姓名显示 和 按公司名显示
//     - 批量生成时同时输出单个席卡 PDF 和合集 PDF
//     - 使用 A4 纸张格式，适合打印输出
//     - 错误处理机制：单个席卡生成失败不影响其他席卡
//
// 使用方式:
//     1. 创建 CardGeneratorService 实例
//     2. 调用 generateCards() 方法传入人员列表和活动名称
//     3. 方法返回 GenerateResult 包含所有生成结果和输出路径
//     4. 生成的 PDF 文件保存在设备文档目录下的带时间戳文件夹中
//
// 依赖说明:
//     - dart:io: 文件系统操作（目录创建、文件写入）
//     - dart:typed_data: 字节数据处理
//     - flutter/services: 资源文件加载（字体文件）
//     - pdf: PDF 文档生成库
//     - path_provider: 获取设备文档目录路径
//     - card_models: 数据模型定义（PersonInfo、CardResult、GenerateResult 等）
// ==============================================================================

// ---- 导入依赖模块 ----

// dart:io: 提供文件系统操作能力，包括 Directory 和 File 类
// 用于创建输出目录和写入 PDF 文件
import 'dart:io';

// dart:typed_data: 提供 Uint8List 等字节数据类型
// PDF 文档保存后以字节流形式写入文件
import 'dart:typed_data';

// flutter/services: 提供 rootBundle 用于加载应用资源文件
// 此处用于从 assets/fonts/ 目录加载中文字体文件
import 'package:flutter/services.dart' show rootBundle;

// pdf 包: 提供 PDF 文档生成的核心能力
// PdfPageFormat: 页面格式定义（如 A4 尺寸）
// PdfColors: PDF 内置颜色常量
import 'package:pdf/pdf.dart';

// pdf/widgets: 提供 PDF 文档构建的高级组件（类似 Flutter Widget）
// 使用 pw 前缀避免与 Flutter 原生 Widget 命名冲突
// 主要使用: Document, Page, Column, Text, Padding, Flexible, ThemeData 等
import 'package:pdf/widgets.dart' as pw;

// path_provider: 获取设备平台的标准目录路径
// getApplicationDocumentsDirectory(): 获取应用文档目录
// Android: /data/data/<package>/files/Documents
// iOS: NSDocumentDirectory
import 'package:path_provider/path_provider.dart';

// 导入本地数据模型定义
// PersonInfo: 人员信息数据结构（姓名、公司、职位等）
// CardResult: 单个席卡生成结果
// GenerateResult: 批量生成汇总结果
// DisplayType: 显示类型枚举（按姓名/按公司）
import '../models/card_models.dart';

// ==============================================================================
// 席卡 PDF 生成服务类
// 功能: 提供席卡 PDF 的本地生成能力，支持单个生成和批量生成
// 设计思路:
//     - 中文字体采用懒加载 + 缓存策略，避免重复加载
//     - 单个席卡生成封装为独立方法，便于复用和维护
//     - 批量生成时自动创建带时间戳的输出目录，避免文件覆盖
//     - 同时生成单个 PDF 和合集 PDF，满足不同使用场景
//     - 完善的错误处理：单个失败不阻断整体流程
// 属性说明:
//     - _chineseFont: 中文字体缓存实例，首次加载后复用
// 核心方法:
//     - _getChineseFont(): 懒加载中文字体
//     - _formatName(): 格式化两字中文姓名
//     - _isAllChinese(): 判断文本是否全为中文字符
//     - _sanitizeFilename(): 清理文件名中的非法字符
//     - _generateCardPdf(): 生成单个席卡 PDF 文档
//     - generateCards(): 批量生成席卡（公开方法）
// ==============================================================================
class CardGeneratorService {
  // ----------------------------------------------------------------------------
  // 中文字体缓存
  // 功能: 缓存已加载的 Noto Sans SC 字体实例
  // 设计思路: 使用可空类型 + 懒加载，首次使用时加载并缓存，后续直接复用
  //           避免每次生成 PDF 都重新加载字体文件，提升性能
  // ----------------------------------------------------------------------------

  /// 中文字体缓存实例
  /// 初始值为 null，首次调用 _getChineseFont() 时从 assets 加载
  /// 加载完成后缓存，后续调用直接返回缓存实例
  pw.Font? _chineseFont;

  // ============================================================================
  // 字体管理方法
  // ============================================================================

  // ----------------------------------------------------------------------------
  // 加载中文字体（懒加载 + 缓存）
  // 功能: 从应用资源中加载 Noto Sans SC 中文字体
  // 参数: 无
  // 返回值: Future<pw.Font> - 加载完成的中文字体实例
  // 设计思路:
  //     - 首次调用时从 assets/fonts/ 目录加载 TTF 字体文件
  //     - 使用 rootBundle.load() 异步加载字体二进制数据
  //     - 将 ByteData 转换为 pw.Font 实例并缓存到 _chineseFont
  //     - 后续调用直接返回缓存实例，避免重复加载
  //     - Noto Sans SC 是 Google 提供的开源中文字体，覆盖常用汉字
  // ----------------------------------------------------------------------------
  /// 获取中文字体（懒加载）
  ///
  /// 从应用资源包中加载 Noto Sans SC 中文字体。首次调用时执行实际加载，
  /// 后续调用直接返回缓存的字体实例。
  ///
  /// 返回值:
  ///     pw.Font - 可用于 PDF 文本渲染的中文字体实例
  ///
  /// 字体来源:
  ///     assets/fonts/NotoSansSC-Regular.ttf (Google Noto Sans SC 常规体)
  Future<pw.Font> _getChineseFont() async {
    // 如果字体已缓存，直接返回，避免重复加载
    if (_chineseFont != null) return _chineseFont!;

    // 从应用资源包中异步加载字体文件
    // rootBundle.load() 返回 ByteData，包含字体的完整二进制数据
    final fontData = await rootBundle.load('assets/fonts/NotoSansSC-Regular.ttf');

    // 将字体二进制数据转换为 pdf 包可识别的 Font 对象
    // fontData.buffer 获取 ByteBuffer，asByteData() 转换为 ByteData
    // pw.Font.ttf() 从 TrueType 字体数据创建字体实例
    _chineseFont = pw.Font.ttf(fontData.buffer.asByteData());

    // 返回已加载并缓存的字体实例
    return _chineseFont!;
  }

  // ============================================================================
  // 姓名格式化与字符检测方法
  // ============================================================================

  // ----------------------------------------------------------------------------
  // 格式化姓名
  // 功能: 对两字中文姓名进行排版优化，在两个字之间插入全角空格
  // 参数:
  //     name (String): 原始姓名字符串
  // 返回值: String - 格式化后的姓名字符串
  // 设计思路:
  //     - 仅对两字纯中文姓名进行格式化（如 "张三" -> "张　三"）
  //     - 全角空格（\u3000）宽度与汉字相同，使两字姓名视觉上居中对称
  //     - 三字及以上姓名、包含非中文字符的姓名不做处理
  //     - 此格式化主要用于席卡打印时的美观排版
  // ----------------------------------------------------------------------------
  /// 格式化姓名
  ///
  /// 对两字中文姓名进行排版优化：在两个字之间插入全角空格（\u3000），
  /// 使两字姓名在席卡上显示时视觉居中、对称美观。
  ///
  /// 参数:
  ///     name - 原始姓名字符串
  ///
  /// 返回值:
  ///     String - 格式化后的姓名。两字中文名返回 "字１全角空格字２" 格式，
  ///              其他情况返回原始字符串
  ///
  /// 示例:
  ///     "张三" -> "张　三"（中间为全角空格）
  ///     "李四" -> "李　四"
  ///     "王小明" -> "王小明"（三字姓名不处理）
  ///     "John" -> "John"（非中文不处理）
  String _formatName(String name) {
    // 判断条件：姓名长度恰好为2 且 全部为中文字符
    // 两个条件同时满足时才进行格式化
    if (name.length == 2 && _isAllChinese(name)) {
      // 在两个汉字之间插入全角空格（Unicode \u3000）
      // 全角空格宽度等于一个汉字，使两字姓名视觉上等距对称
      return '${name[0]}\u3000${name[1]}';
    }
    // 不满足条件时返回原始姓名，不做任何修改
    return name;
  }

  // ----------------------------------------------------------------------------
  // 判断文本是否全为中文字符
  // 功能: 检查给定字符串中的每个字符是否都在 CJK 统一汉字范围内
  // 参数:
  //     text (String): 待检查的文本字符串
  // 返回值: bool - true 表示全部为中文字符，false 表示包含非中文字符
  // 设计思路:
  //     - 使用 Unicode 编码范围判断：CJK 统一汉字范围为 0x4E00 ~ 0x9FFF
  //     - 遍历字符串的每个 Unicode 码点（rune），检查是否全部在汉字范围内
  //     - 使用 every() 方法实现短路求值，遇到非汉字字符立即返回 false
  // ----------------------------------------------------------------------------
  /// 判断文本是否全为中文字符
  ///
  /// 检查给定字符串中的每个字符是否都在 CJK 统一汉字 Unicode 编码范围内
  /// （U+4E00 ~ U+9FFF）。
  ///
  /// 参数:
  ///     text - 待检查的文本字符串
  ///
  /// 返回值:
  ///     bool - true 表示所有字符均为中文字符，false 表示包含非中文字符
  ///
  /// 技术说明:
  ///     CJK 统一汉字（CJK Unified Ideographs）是 Unicode 中收录的基本汉字区块，
  ///     包含 20,992 个常用汉字，编码范围为 U+4E00 ~ U+9FFF
  bool _isAllChinese(String text) {
    // text.runes 获取字符串的 Unicode 码点迭代器
    // every() 方法检查每个码点是否都在 CJK 统一汉字范围内
    // 0x4e00 (19968) 是 "一" 的编码，0x9fff (40959) 是基本汉字的最后一个码点
    return text.runes.every((r) => r >= 0x4e00 && r <= 0x9fff);
  }

  // ============================================================================
  // 文件名安全处理方法
  // ============================================================================

  // ----------------------------------------------------------------------------
  // 安全文件名处理
  // 功能: 清理文件名中的非法字符，确保文件名在所有操作系统上合法
  // 参数:
  //     name (String): 原始文件名字符串
  // 返回值: String - 处理后的安全文件名字符串
  // 设计思路:
  //     - 使用正则表达式替换 Windows 文件名中的非法字符
  //     - 非法字符包括: < > : " / \ | ? * （Windows 文件名保留字符）
  //     - 将非法字符统一替换为下划线 '_'
  //     - 限制文件名最大长度为 50 字符，防止过长文件名导致问题
  // ----------------------------------------------------------------------------
  /// 安全文件名处理
  ///
  /// 清理文件名中的操作系统非法字符，确保生成的文件名在 Windows、macOS、
  /// Linux 等平台上均可正常使用。
  ///
  /// 参数:
  ///     name - 原始文件名字符串（可能包含姓名、公司名等用户输入）
  ///
  /// 返回值:
  ///     String - 处理后的安全文件名，非法字符已替换为下划线，长度不超过50
  ///
  /// 处理规则:
  ///     1. 将 < > : " / \ | ? * 替换为下划线 _
  ///     2. 截断超过 50 字符的文件名
  String _sanitizeFilename(String name) {
    // 使用正则表达式匹配 Windows 文件名中的非法字符
    // [<>:"/\\|?*] 匹配以下字符: < > : " / \ | ? *
    // 将这些字符全部替换为下划线 '_'，保持文件名可读性
    var safe = name.replaceAll(RegExp(r'[<>:"/\\|?*]'), '_');

    // 限制文件名最大长度为 50 字符
    // 防止过长姓名或公司名导致文件系统路径超长问题
    if (safe.length > 50) safe = safe.substring(0, 50);

    // 返回处理后的安全文件名
    return safe;
  }

  // ============================================================================
  // 单个席卡 PDF 生成方法
  // ============================================================================

  // ----------------------------------------------------------------------------
  // 生成单个席卡 PDF 文档
  // 功能: 根据显示文本、活动名称和显示类型，生成一个 A4 尺寸的席卡 PDF
  // 参数:
  //     displayText (String): 要显示的文本内容（姓名或公司名）
  //     eventName (String): 活动名称，显示在席卡顶部
  //     displayType (DisplayType): 显示类型，决定字号大小
  //     chineseFont (pw.Font): 用于中文文本渲染的字体
  // 返回值: Future<pw.Document> - 生成的 PDF 文档对象
  // 设计思路:
  //     - 使用 A4 纸张格式，适合打印输出
  //     - 姓名字号 72pt，公司名字号 36pt（姓名更醒目）
  //     - 活动名称字号 16pt，灰色显示，位于顶部
  //     - 内容垂直居中，活动名称与姓名之间有间距
  //     - 页边距 40pt，四周均匀
  // ----------------------------------------------------------------------------
  /// 生成单个席卡 PDF 文档
  ///
  /// 根据显示文本、活动名称和显示类型，生成一个 A4 尺寸的席卡 PDF 文档。
  /// 文档包含活动名称（顶部）和显示文本（居中）两部分内容。
  ///
  /// 参数:
  ///     displayText - 要显示的主要文本内容（姓名或公司名）
  ///     eventName - 活动名称，显示在席卡顶部，为空时不显示
  ///     displayType - 显示类型枚举，决定文本内容和字号
  ///     chineseFont - 用于中文文本渲染的字体实例
  ///
  /// 返回值:
  ///     pw.Document - 生成的 PDF 文档对象，调用方可通过 save() 获取字节数据
  ///
  /// 排版说明:
  ///     - 纸张: A4 (210mm x 297mm)
  ///     - 页边距: 四周各 40pt
  ///     - 姓名模式: 主文本 72pt 加粗
  ///     - 公司名模式: 主文本 36pt 加粗
  ///     - 活动名称: 16pt 灰色 (PdfColors.grey700)
  Future<pw.Document> _generateCardPdf({
    required String displayText,   // 要显示的主要文本（姓名或公司名）
    required String eventName,     // 活动名称（可选显示在顶部）
    required DisplayType displayType, // 显示类型：姓名 or 公司名
    required pw.Font chineseFont,  // 中文字体实例
  }) async {
    // 创建新的 PDF 文档实例
    // pw.Document 是 pdf 包的顶层文档对象，用于组织页面和内容
    final doc = pw.Document();

    // 判断当前是否为姓名显示模式
    // 姓名模式使用更大的字号（72pt），使姓名更醒目
    final isName = displayType == DisplayType.name;

    // 对显示文本进行格式化
    // 姓名模式：调用 _formatName 对两字中文名进行排版优化（加全角空格）
    // 公司名模式：直接使用原始文本，不做格式化
    final formattedText = isName ? _formatName(displayText) : displayText;

    // ---- 字号配置 ----
    // 根据显示类型设置不同的字号
    // 姓名模式使用 72pt 大字号，确保远距离可读
    // 公司名模式使用 36pt，因为公司名通常较长，需要较小字号避免溢出
    final nameFontSize = isName ? 72.0 : 36.0;
    // 活动名称字号固定为 16pt，作为辅助信息不应过于醒目
    final eventFontSize = 16.0;

    // ---- 主题配置 ----
    // 创建 PDF 主题数据，设置基础字体为中文字体
    // ThemeData.withFont() 创建包含指定字体的主题
    // base 参数设置默认字体，所有未单独指定字体的文本都使用此字体
    final theme = pw.ThemeData.withFont(
      base: chineseFont, // 设置基础字体为 Noto Sans SC
    );

    // ---- 构建 PDF 页面 ----
    // 向文档中添加一个 A4 尺寸的页面
    doc.addPage(
      pw.Page(
        // 页面格式: A4 (210mm x 297mm)，适合打印
        pageFormat: PdfPageFormat.a4,
        // 应用主题数据，确保中文字体生效
        theme: theme,
        // 页边距: 四周各 40pt，提供足够的留白
        margin: const pw.EdgeInsets.all(40),
        // 页面内容构建器
        // 使用 Column（纵向布局）组织内容，实现垂直居中
        build: (pw.Context context) => pw.Column(
          // 垂直方向居中对齐，使内容在页面中央
          mainAxisAlignment: pw.MainAxisAlignment.center,
          // 页面元素列表（从上到下排列）
          children: [
            // ---- 活动名称（顶部区域）----
            // 仅当活动名称非空时显示
            // 使用 if 条件渲染，空名称时不占用空间
            if (eventName.isNotEmpty)
              pw.Padding(
                // 底部留 60pt 间距，将活动名称与主文本分开
                padding: const pw.EdgeInsets.only(bottom: 60),
                child: pw.Text(
                  eventName, // 活动名称文本
                  style: pw.TextStyle(
                    font: chineseFont,     // 使用中文字体
                    fontSize: eventFontSize, // 16pt 字号
                    color: PdfColors.grey700, // 灰色，降低视觉优先级
                  ),
                  // 文本水平居中对齐
                  textAlign: pw.TextAlign.center,
                ),
              ),
            // ---- 姓名/公司名（主体区域）----
            // 使用 Flexible 包裹，允许文本在可用空间内自适应
            // 当文本过长时，Flexible 确保不会溢出页面边界
            pw.Flexible(
              child: pw.Text(
                formattedText, // 经过格式化的显示文本
                style: pw.TextStyle(
                  font: chineseFont,       // 使用中文字体
                  fontSize: nameFontSize,  // 姓名72pt / 公司名36pt
                  fontWeight: pw.FontWeight.bold, // 加粗，增强视觉效果
                ),
                // 文本水平居中对齐
                textAlign: pw.TextAlign.center,
              ),
            ),
          ],
        ),
      ),
    );

    // 返回构建完成的 PDF 文档对象
    return doc;
  }

  // ============================================================================
  // 批量席卡生成方法（公开接口）
  // ============================================================================

  // ----------------------------------------------------------------------------
  // 批量生成席卡
  // 功能: 根据人员列表批量生成席卡 PDF，包括单个文件和合集文件
  // 参数:
  //     infos (List<PersonInfo>): 人员信息列表
  //     eventName (String): 活动名称
  //     displayType (DisplayType): 显示类型（按姓名/按公司）
  // 返回值: Future<GenerateResult> - 批量生成结果，包含所有席卡的状态和路径
  // 设计思路:
  //     1. 加载中文字体（懒加载，首次调用时加载）
  //     2. 创建带时间戳的输出目录，避免文件覆盖
  //     3. 遍历人员列表，逐个生成席卡 PDF
  //     4. 当生成数量 > 1 时，额外生成合集 PDF
  //     5. 单个席卡失败不影响其他席卡的生成
  //     6. 返回 GenerateResult 汇总所有结果
  // ----------------------------------------------------------------------------
  /// 批量生成席卡
  ///
  /// 根据人员信息列表批量生成席卡 PDF 文件。为每个人生成独立的 PDF 文件，
  /// 同时生成一个包含所有席卡的合集 PDF。所有文件保存在带时间戳的目录中。
  ///
  /// 参数:
  ///     infos - 人员信息列表，每个 PersonInfo 包含姓名、公司等信息
  ///     eventName - 活动名称，显示在每个席卡的顶部
  ///     displayType - 显示类型：DisplayType.name 显示姓名，DisplayType.company 显示公司名
  ///
  /// 返回值:
  ///     GenerateResult - 批量生成结果，包含:
  ///         - cards: 每个席卡的生成结果列表
  ///         - combinedPdfPath: 合集 PDF 路径（可能为 null）
  ///         - outputDir: 输出目录路径
  ///         - failedNames: 生成失败的名称列表
  ///
  /// 输出目录格式:
  ///     <文档目录>/席卡_<活动名>_<YYYYMMDD_HHmmss>/
  ///
  /// 错误处理:
  ///     单个席卡生成失败时记录错误信息，继续处理下一个，不中断整体流程
  Future<GenerateResult> generateCards({
    required List<PersonInfo> infos,    // 人员信息列表
    required String eventName,          // 活动名称
    required DisplayType displayType,   // 显示类型：姓名 or 公司名
  }) async {
    // ---- 第一步: 加载中文字体 ----
    // 获取中文字体实例（懒加载，首次调用时从 assets 加载）
    // 所有席卡共用同一个字体实例，避免重复加载
    final font = await _getChineseFont();

    // ---- 第二步: 创建输出目录 ----
    // 获取设备的应用文档目录路径
    // 这是应用的标准文件存储位置，用户可通过文件管理器访问
    final baseDir = await getApplicationDocumentsDirectory();

    // 获取当前时间，用于生成时间戳
    final now = DateTime.now();

    // 构建时间戳字符串，格式: YYYYMMDD_HHmmss
    // 每个数字使用 padLeft(2, '0') 确保两位数格式（如 "03" 而非 "3"）
    final timestamp =
        '${now.year}${now.month.toString().padLeft(2, '0')}${now.day.toString().padLeft(2, '0')}_${now.hour.toString().padLeft(2, '0')}${now.minute.toString().padLeft(2, '0')}${now.second.toString().padLeft(2, '0')}';

    // 构建活动名称后缀
    // 活动名称非空时添加下划线前缀，为空时不添加
    final eventSuffix = eventName.isNotEmpty ? '_$eventName' : '';

    // 构建输出文件夹名称
    // 格式: "席卡_<活动名>_<时间戳>" 或 "席卡_<时间戳>"
    final folderName = '席卡${eventSuffix}_$timestamp';

    // 创建输出目录对象
    // 路径格式: <文档目录>/席卡_活动名_20260703_143025/
    final outputDir = Directory('${baseDir.path}/$folderName');

    // 递归创建目录，recursive: true 确保父目录也会自动创建
    await outputDir.create(recursive: true);

    // ---- 第三步: 初始化结果收集容器 ----
    // cards: 收集每个席卡的生成结果（成功/失败状态、文件路径等）
    final cards = <CardResult>[];
    // failedNames: 收集生成失败的人员名称，用于汇总报告
    final failedNames = <String>[];
    // pdfFiles: 收集成功生成的 PDF 文件对象，用于后续合并合集
    final pdfFiles = <File>[];

    // ---- 第四步: 遍历人员列表，逐个生成席卡 ----
    for (final info in infos) {
      // ---- 确定显示文本 ----
      // 根据显示类型选择要显示的文本内容
      // 公司名模式: 优先显示公司名，公司名为空时回退到姓名
      // 姓名模式: 直接显示姓名
      final displayText = displayType == DisplayType.company
          ? (info.company.isNotEmpty ? info.company : info.name)
          : info.name;

      // ---- 空值检查 ----
      // 如果显示文本为空，跳过此人并记录到失败列表
      if (displayText.isEmpty) {
        // 姓名为空时记录 "(空)"，否则记录实际姓名
        failedNames.add(info.name.isEmpty ? '(空)' : info.name);
        // 跳过当前人员，继续处理下一个
        continue;
      }

      try {
        // ---- 生成单个席卡 PDF ----
        // 调用 _generateCardPdf 方法创建 PDF 文档
        final doc = await _generateCardPdf(
          displayText: displayText,    // 显示文本（已根据模式选择）
          eventName: eventName,        // 活动名称
          displayType: displayType,    // 显示类型
          chineseFont: font,           // 中文字体
        );

        // ---- 构建文件名 ----
        // 对显示文本进行安全处理，替换非法字符
        final safeName = _sanitizeFilename(displayText);

        // 构建日期字符串，格式: YYYYMMDD
        final dateStr = '${now.year}${now.month.toString().padLeft(2, '0')}${now.day.toString().padLeft(2, '0')}';

        // 构建完整文件名，格式: "席卡_<安全名>_<日期>.pdf"
        final filename = '席卡_${safeName}_$dateStr.pdf';

        // 构建完整文件路径
        final filePath = '${outputDir.path}/$filename';

        // ---- 写入 PDF 文件 ----
        // 创建 File 对象
        final file = File(filePath);
        // 将 PDF 文档保存为字节流并写入文件
        // doc.save() 返回 Future<Uint8List>，包含完整的 PDF 二进制数据
        // file.writeAsBytes() 将字节数据写入磁盘文件
        await file.writeAsBytes(await doc.save());

        // 将成功生成的文件添加到列表，用于后续合集生成
        pdfFiles.add(file);

        // 记录成功结果
        cards.add(CardResult(
          displayName: displayText, // 显示的名称
          filePath: filePath,       // 生成的 PDF 文件完整路径
          success: true,            // 标记为成功
        ));
      } catch (e) {
        // ---- 异常处理 ----
        // 单个席卡生成失败时，记录失败结果但不中断整体流程
        // 继续处理下一个人员
        cards.add(CardResult(
          displayName: displayText, // 显示的名称
          filePath: '',             // 失败时无文件路径
          success: false,           // 标记为失败
          error: e.toString(),      // 记录错误信息，便于调试
        ));
        // 将失败的人员名称添加到失败列表
        failedNames.add(displayText);
      }
    }

    // ---- 第五步: 生成合集 PDF ----
    // 当成功生成的 PDF 文件数量大于 1 时，额外生成一个合集 PDF
    // 合集 PDF 将所有席卡合并到一个文档中，方便批量打印
    String? combinedPath;
    if (pdfFiles.length > 1) {
      try {
        // 创建合集 PDF 文档实例
        final combinedDoc = pw.Document();

        // 创建合集文档的主题，设置中文字体
        final combinedTheme = pw.ThemeData.withFont(base: font);

        // 遍历所有人员，为每个人在合集文档中添加一页
        for (final info in infos) {
          // 根据显示类型确定显示文本（与单个生成逻辑一致）
          final displayText = displayType == DisplayType.company
              ? (info.company.isNotEmpty ? info.company : info.name)
              : info.name;

          // 跳过显示文本为空的人员
          if (displayText.isEmpty) continue;

          // 判断是否为姓名模式
          final isName = displayType == DisplayType.name;
          // 格式化显示文本（姓名模式加全角空格）
          final formattedText = isName ? _formatName(displayText) : displayText;
          // 根据显示类型确定字号
          final nameFontSize = isName ? 72.0 : 36.0;

          // 向合集文档中添加一页，布局与单个席卡一致
          combinedDoc.addPage(pw.Page(
            // A4 纸张格式
            pageFormat: PdfPageFormat.a4,
            // 应用主题
            theme: combinedTheme,
            // 页边距 40pt
            margin: const pw.EdgeInsets.all(40),
            // 页面内容构建
            build: (pw.Context context) => pw.Column(
              // 垂直居中
              mainAxisAlignment: pw.MainAxisAlignment.center,
              children: [
                // 活动名称（顶部，条件渲染）
                if (eventName.isNotEmpty)
                  pw.Padding(
                    padding: const pw.EdgeInsets.only(bottom: 60),
                    child: pw.Text(eventName,
                        style: pw.TextStyle(font: font, fontSize: 16, color: PdfColors.grey700),
                        textAlign: pw.TextAlign.center),
                  ),
                // 姓名/公司名（居中主体）
                pw.Flexible(
                  child: pw.Text(formattedText,
                      style: pw.TextStyle(font: font, fontSize: nameFontSize, fontWeight: pw.FontWeight.bold),
                      textAlign: pw.TextAlign.center),
                ),
              ],
            ),
          ));
        }

        // 构建合集 PDF 文件路径
        // 文件名格式: "席卡合集_<时间戳>.pdf"
        final combinedFile = File('${outputDir.path}/席卡合集_$timestamp.pdf');

        // 将合集 PDF 文档保存为字节流并写入文件
        await combinedFile.writeAsBytes(await combinedDoc.save());

        // 记录合集 PDF 的文件路径
        combinedPath = combinedFile.path;
      } catch (_) {
        // 合集 PDF 生成失败时静默处理
        // 合并失败不影响已生成的单个席卡文件
        // 使用 _ 忽略异常详情，因为合并失败不是关键错误
      }
    }

    // ---- 第六步: 返回批量生成结果 ----
    // 构建并返回 GenerateResult 对象，汇总所有生成信息
    return GenerateResult(
      cards: cards,                   // 每个席卡的生成结果列表
      combinedPdfPath: combinedPath,  // 合集 PDF 路径（可能为 null）
      outputDir: outputDir.path,      // 输出目录的完整路径
      failedNames: failedNames,       // 生成失败的名称列表
    );
  }
}
