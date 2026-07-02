/// 生成席卡的请求模型
class GenerateCardsRequest {
  final String text;
  final String eventName;
  final String displayType;
  final String template;

  GenerateCardsRequest({
    required this.text,
    this.eventName = '',
    this.displayType = 'name',
    this.template = '席卡模板v5.docx',
  });

  Map<String, dynamic> toJson() => {
        'text': text,
        'event_name': eventName,
        'display_type': displayType,
        'template': template,
      };
}

/// 文件信息
class FileInfo {
  final String filename;
  final String fileId;
  final String type;

  FileInfo({
    required this.filename,
    required this.fileId,
    this.type = 'word',
  });

  factory FileInfo.fromJson(Map<String, dynamic> json) => FileInfo(
        filename: json['filename'] as String,
        fileId: json['file_id'] as String,
        type: json['type'] as String? ?? 'word',
      );
}

/// 生成席卡的响应
class GenerateCardsResponse {
  final bool success;
  final int count;
  final String? outputDir;
  final List<FileInfo> wordFiles;
  final List<FileInfo> pdfFiles;
  final List<String> failed;
  final String? reportId;
  final String? pdfCombinedId;
  final String? error;

  GenerateCardsResponse({
    required this.success,
    this.count = 0,
    this.outputDir,
    this.wordFiles = const [],
    this.pdfFiles = const [],
    this.failed = const [],
    this.reportId,
    this.pdfCombinedId,
    this.error,
  });

  factory GenerateCardsResponse.fromJson(Map<String, dynamic> json) {
    if (json['success'] == true) {
      return GenerateCardsResponse(
        success: true,
        count: json['count'] as int? ?? 0,
        outputDir: json['output_dir'] as String?,
        wordFiles: (json['word_files'] as List<dynamic>?)
                ?.map((e) => FileInfo.fromJson(e as Map<String, dynamic>))
                .toList() ??
            [],
        pdfFiles: (json['pdf_files'] as List<dynamic>?)
                ?.map((e) => FileInfo.fromJson(e as Map<String, dynamic>))
                .toList() ??
            [],
        failed: (json['failed'] as List<dynamic>?)
                ?.map((e) => e as String)
                .toList() ??
            [],
        reportId: json['report_id'] as String?,
        pdfCombinedId: json['pdf_combined_id'] as String?,
      );
    } else {
      return GenerateCardsResponse(
        success: false,
        error: json['error'] as String? ?? '未知错误',
      );
    }
  }
}

/// 模板信息
class TemplateInfo {
  final bool success;
  final List<String> templates;

  TemplateInfo({required this.success, this.templates = const []});

  factory TemplateInfo.fromJson(Map<String, dynamic> json) => TemplateInfo(
        success: json['success'] as bool? ?? false,
        templates: (json['templates'] as List<dynamic>?)
                ?.map((e) => e as String)
                .toList() ??
            [],
      );
}
