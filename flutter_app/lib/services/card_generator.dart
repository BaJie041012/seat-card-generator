/// 席卡 PDF 本地生成服务
/// 使用 pdf 包直接在设备上生成席卡 PDF，无需服务器
import 'dart:io';
import 'dart:typed_data';
import 'package:flutter/services.dart' show rootBundle;
import 'package:pdf/pdf.dart';
import 'package:pdf/widgets.dart' as pw;
import 'package:path_provider/path_provider.dart';
import '../models/card_models.dart';

class CardGeneratorService {
  pw.Font? _chineseFont;

  /// 加载中文字体（Noto Sans SC）
  Future<pw.Font> _getChineseFont() async {
    if (_chineseFont != null) return _chineseFont!;
    final fontData = await rootBundle.load('assets/fonts/NotoSansSC-Regular.ttf');
    _chineseFont = pw.Font.ttf(fontData.buffer.asByteData());
    return _chineseFont!;
  }

  /// 格式化姓名：两字中文名中间加全角空格
  String _formatName(String name) {
    if (name.length == 2 && _isAllChinese(name)) {
      return '${name[0]}\u3000${name[1]}';
    }
    return name;
  }

  bool _isAllChinese(String text) {
    return text.runes.every((r) => r >= 0x4e00 && r <= 0x9fff);
  }

  /// 安全文件名
  String _sanitizeFilename(String name) {
    var safe = name.replaceAll(RegExp(r'[<>:"/\\|?*]'), '_');
    if (safe.length > 50) safe = safe.substring(0, 50);
    return safe;
  }

  /// 生成单个席卡 PDF
  Future<pw.Document> _generateCardPdf({
    required String displayText,
    required String eventName,
    required DisplayType displayType,
    required pw.Font chineseFont,
  }) async {
    final doc = pw.Document();
    final isName = displayType == DisplayType.name;
    final formattedText = isName ? _formatName(displayText) : displayText;

    // 字号：姓名72pt，公司名36pt（在PDF中按比例缩放，A4纸）
    final nameFontSize = isName ? 72.0 : 36.0;
    final eventFontSize = 16.0;

    final theme = pw.ThemeData.withFont(
      base: chineseFont,
    );

    doc.addPage(
      pw.Page(
        pageFormat: PdfPageFormat.a4,
        theme: theme,
        margin: const pw.EdgeInsets.all(40),
        build: (pw.Context context) => pw.Column(
          mainAxisAlignment: pw.MainAxisAlignment.center,
          children: [
            // 活动名称（顶部）
            if (eventName.isNotEmpty)
              pw.Padding(
                padding: const pw.EdgeInsets.only(bottom: 60),
                child: pw.Text(
                  eventName,
                  style: pw.TextStyle(
                    font: chineseFont,
                    fontSize: eventFontSize,
                    color: PdfColors.grey700,
                  ),
                  textAlign: pw.TextAlign.center,
                ),
              ),
            // 姓名/公司名（居中大字）
            pw.Flexible(
              child: pw.Text(
                formattedText,
                style: pw.TextStyle(
                  font: chineseFont,
                  fontSize: nameFontSize,
                  fontWeight: pw.FontWeight.bold,
                ),
                textAlign: pw.TextAlign.center,
              ),
            ),
          ],
        ),
      ),
    );

    return doc;
  }

  /// 批量生成席卡
  Future<GenerateResult> generateCards({
    required List<PersonInfo> infos,
    required String eventName,
    required DisplayType displayType,
  }) async {
    final font = await _getChineseFont();

    // 创建输出目录
    final baseDir = await getApplicationDocumentsDirectory();
    final now = DateTime.now();
    final timestamp =
        '${now.year}${now.month.toString().padLeft(2, '0')}${now.day.toString().padLeft(2, '0')}_${now.hour.toString().padLeft(2, '0')}${now.minute.toString().padLeft(2, '0')}${now.second.toString().padLeft(2, '0')}';
    final eventSuffix = eventName.isNotEmpty ? '_$eventName' : '';
    final folderName = '席卡${eventSuffix}_$timestamp';
    final outputDir = Directory('${baseDir.path}/$folderName');
    await outputDir.create(recursive: true);

    final cards = <CardResult>[];
    final failedNames = <String>[];
    final pdfFiles = <File>[];

    for (final info in infos) {
      final displayText = displayType == DisplayType.company
          ? (info.company.isNotEmpty ? info.company : info.name)
          : info.name;

      if (displayText.isEmpty) {
        failedNames.add(info.name.isEmpty ? '(空)' : info.name);
        continue;
      }

      try {
        final doc = await _generateCardPdf(
          displayText: displayText,
          eventName: eventName,
          displayType: displayType,
          chineseFont: font,
        );

        final safeName = _sanitizeFilename(displayText);
        final dateStr = '${now.year}${now.month.toString().padLeft(2, '0')}${now.day.toString().padLeft(2, '0')}';
        final filename = '席卡_${safeName}_$dateStr.pdf';
        final filePath = '${outputDir.path}/$filename';

        final file = File(filePath);
        await file.writeAsBytes(await doc.save());
        pdfFiles.add(file);

        cards.add(CardResult(
          displayName: displayText,
          filePath: filePath,
          success: true,
        ));
      } catch (e) {
        cards.add(CardResult(
          displayName: displayText,
          filePath: '',
          success: false,
          error: e.toString(),
        ));
        failedNames.add(displayText);
      }
    }

    // 生成合集 PDF（所有席卡在一个文档中）
    String? combinedPath;
    if (pdfFiles.length > 1) {
      try {
        final combinedDoc = pw.Document();
        final combinedTheme = pw.ThemeData.withFont(base: font);

        for (final info in infos) {
          final displayText = displayType == DisplayType.company
              ? (info.company.isNotEmpty ? info.company : info.name)
              : info.name;
          if (displayText.isEmpty) continue;

          final isName = displayType == DisplayType.name;
          final formattedText = isName ? _formatName(displayText) : displayText;
          final nameFontSize = isName ? 72.0 : 36.0;

          combinedDoc.addPage(pw.Page(
            pageFormat: PdfPageFormat.a4,
            theme: combinedTheme,
            margin: const pw.EdgeInsets.all(40),
            build: (pw.Context context) => pw.Column(
              mainAxisAlignment: pw.MainAxisAlignment.center,
              children: [
                if (eventName.isNotEmpty)
                  pw.Padding(
                    padding: const pw.EdgeInsets.only(bottom: 60),
                    child: pw.Text(eventName,
                        style: pw.TextStyle(font: font, fontSize: 16, color: PdfColors.grey700),
                        textAlign: pw.TextAlign.center),
                  ),
                pw.Flexible(
                  child: pw.Text(formattedText,
                      style: pw.TextStyle(font: font, fontSize: nameFontSize, fontWeight: pw.FontWeight.bold),
                      textAlign: pw.TextAlign.center),
                ),
              ],
            ),
          ));
        }

        final combinedFile = File('${outputDir.path}/席卡合集_$timestamp.pdf');
        await combinedFile.writeAsBytes(await combinedDoc.save());
        combinedPath = combinedFile.path;
      } catch (_) {
        // 合并失败不影响单个文件
      }
    }

    return GenerateResult(
      cards: cards,
      combinedPdfPath: combinedPath,
      outputDir: outputDir.path,
      failedNames: failedNames,
    );
  }
}
