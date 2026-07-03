package com.bajie.seatcard

/** 人员信息 */
data class PersonInfo(
    val name: String,
    val company: String = "",
    val position: String = "",
    val originalLine: String = ""
)

/** 模板类型 */
enum class TemplateType(val displayName: String, val description: String) {
    V4("详细模板 (v4)", "活动名称 + 姓名/公司，楷体排版"),
    V5("简洁模板 (v5)", "仅姓名/公司，大字体醒目显示")
}

/** 显示模式 */
enum class DisplayType(val displayName: String) {
    NAME("按姓名显示"),
    COMPANY("按公司名显示")
}

/** 生成结果 */
data class GenerateResult(
    val successCards: List<CardResult>,
    val failedNames: List<String>,
    val outputDir: String
)

data class CardResult(
    val personName: String,
    val pdfPath: String,
    val success: Boolean,
    val errorMessage: String = ""
)
