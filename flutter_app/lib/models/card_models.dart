/// 席卡生成系统 - 数据模型
/// 包含人员信息、生成结果等核心数据结构

/// 人员信息数据类
class PersonInfo {
  final String name;
  final String company;
  final String position;
  final String originalLine;

  const PersonInfo({
    required this.name,
    this.company = '',
    this.position = '',
    this.originalLine = '',
  });

  factory PersonInfo.fromJson(Map<String, dynamic> json) {
    return PersonInfo(
      name: json['name']?.toString() ?? '',
      company: json['company']?.toString() ?? '',
      position: json['position']?.toString() ?? '',
      originalLine: json['original_line']?.toString() ?? '',
    );
  }
}

/// 单个席卡的生成结果
class CardResult {
  final String displayName; // 显示的名称（姓名或公司名）
  final String filePath;    // 生成的PDF文件路径
  final bool success;
  final String? error;

  const CardResult({
    required this.displayName,
    required this.filePath,
    this.success = true,
    this.error,
  });
}

/// 批量生成结果
class GenerateResult {
  final List<CardResult> cards;
  final String? combinedPdfPath; // 合并后的PDF路径
  final String outputDir;
  final List<String> failedNames;

  const GenerateResult({
    required this.cards,
    this.combinedPdfPath,
    required this.outputDir,
    this.failedNames = const [],
  });

  int get successCount => cards.where((c) => c.success).length;
  int get failCount => cards.where((c) => !c.success).length;
}

/// 显示类型
enum DisplayType {
  name,    // 显示姓名
  company, // 显示公司名
}
