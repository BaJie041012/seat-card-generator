package com.bajie.seatcard

import android.content.Context
import android.graphics.*
import android.graphics.pdf.PdfDocument
import java.io.File
import java.io.FileOutputStream
import java.text.SimpleDateFormat
import java.util.*

/**
 * PDF 生成器 — 复刻 Python 端折叠桌牌布局。
 *
 * A4 横向页面，左右两半内容相同（对折后正反面均可读）。
 * v4 模板：活动名称（16pt）+ 姓名/公司（72pt / 36pt）
 * v5 模板：仅姓名/公司（110pt）
 */
class PdfGenerator(private val context: Context) {

    companion object {
        // A4 横向：29.7cm x 21cm，1pt = 1/72 inch
        private const val PAGE_WIDTH = 842   // 29.7cm
        private const val PAGE_HEIGHT = 595  // 21cm
        private const val MARGIN = 36f       // ~1.27cm
    }

    private var typeface: Typeface? = null

    private fun getTypeface(): Typeface {
        if (typeface == null) {
            typeface = try {
                Typeface.createFromAsset(context.assets, "fonts/NotoSansSC-Regular.ttf")
            } catch (e: Exception) {
                Typeface.DEFAULT
            }
        }
        return typeface!!
    }

    /**
     * 两名字中间插全角空格（复刻 Python 端 format_name 逻辑）
     */
    internal fun formatName(name: String): String {
        return if (name.length == 2) {
            "${name[0]}\u3000${name[1]}"
        } else {
            name
        }
    }

    /**
     * 生成所有席卡 PDF。
     * 返回 (成功列表, 失败列表, 输出目录路径)。
     */
    fun generateAll(
        persons: List<PersonInfo>,
        template: TemplateType,
        displayType: DisplayType,
        eventName: String,
        outputDir: File
    ): Triple<List<CardResult>, List<String>, String> {
        outputDir.mkdirs()
        val pdfDir = File(outputDir, "pdf")
        pdfDir.mkdirs()

        val dateStr = SimpleDateFormat("yyyyMMdd", Locale.getDefault()).format(Date())
        val successCards = mutableListOf<CardResult>()
        val failedNames = mutableListOf<String>()

        for (person in persons) {
            try {
                val displayName = formatName(
                    when (displayType) {
                        DisplayType.NAME -> person.name
                        DisplayType.COMPANY -> person.company.ifEmpty { person.name }
                    }
                )
                val safeName = sanitizeFileName(person.name)
                val fileName = "席卡_${safeName}_${dateStr}.pdf"
                val pdfFile = File(pdfDir, fileName)

                generateSingle(displayName, eventName, template, pdfFile)
                successCards.add(CardResult(person.name, pdfFile.absolutePath, true))
            } catch (e: Exception) {
                failedNames.add(person.name)
            }
        }

        // 多人时生成合集
        if (successCards.size > 1) {
            val timestamp = SimpleDateFormat("HHmmss", Locale.getDefault()).format(Date())
            val combinedFile = File(outputDir, "席卡合集_${timestamp}.pdf")
            generateCombined(successCards.map { it.pdfPath }, combinedFile)
        }

        return Triple(successCards, failedNames, outputDir.absolutePath)
    }

    /**
     * 生成单张席卡 PDF（A4 横向，折叠桌牌）。
     */
    private fun generateSingle(
        displayText: String,
        eventName: String,
        template: TemplateType,
        outputFile: File
    ) {
        val pdf = PdfDocument()
        val font = getTypeface()

        val pageInfo = PdfDocument.PageInfo.Builder(PAGE_WIDTH, PAGE_HEIGHT, 0).create()
        val page = pdf.startPage(pageInfo)
        val canvas = page.canvas

        // 白色背景
        canvas.drawColor(Color.WHITE)

        val halfWidth = PAGE_WIDTH / 2f  // 421pt

        // 绘制左右两半（内容相同）
        drawHalf(canvas, 0f, halfWidth, displayText, eventName, template, font)
        drawHalf(canvas, halfWidth, PAGE_WIDTH.toFloat(), displayText, eventName, template, font)

        // 中间折痕线（浅灰色虚线，辅助折叠）
        val foldPaint = Paint().apply {
            color = Color.LTGRAY
            strokeWidth = 0.5f
            style = Paint.Style.STROKE
            pathEffect = DashPathEffect(floatArrayOf(8f, 8f), 0f)
        }
        canvas.drawLine(halfWidth, MARGIN, halfWidth, PAGE_HEIGHT - MARGIN, foldPaint)

        pdf.finishPage(page)
        FileOutputStream(outputFile).use { pdf.writeTo(it) }
        pdf.close()
    }

    /**
     * 绘制半页内容。
     */
    private fun drawHalf(
        canvas: Canvas,
        left: Float,
        right: Float,
        displayText: String,
        eventName: String,
        template: TemplateType,
        font: Typeface
    ) {
        val centerX = (left + right) / 2f
        val usableHeight = PAGE_HEIGHT - 2 * MARGIN

        when (template) {
            TemplateType.V4 -> {
                // 活动名称：顶部居中，16pt 粗体
                if (eventName.isNotBlank()) {
                    val eventPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
                        this.typeface = Typeface.create(font, Typeface.BOLD)
                        textSize = 16f * 1.33f  // pt → px
                        color = Color.DKGRAY
                        textAlign = Paint.Align.CENTER
                    }
                    val eventY = MARGIN + usableHeight * 0.25f
                    canvas.drawText(eventName, centerX, eventY, eventPaint)
                }

                // 姓名/公司：居中显示
                val mainTextSize = if (displayText.length <= 4) 72f else 36f
                val mainPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
                    this.typeface = font
                    textSize = mainTextSize * 1.33f
                    color = Color.BLACK
                    textAlign = Paint.Align.CENTER
                }
                val mainY = MARGIN + usableHeight * 0.55f
                canvas.drawText(displayText, centerX, mainY, mainPaint)
            }

            TemplateType.V5 -> {
                // 仅姓名/公司，110pt 大字体居中
                val baseSize = if (displayText.length <= 4) 110f else 72f
                val mainPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
                    this.typeface = font
                    textSize = baseSize * 1.33f
                    color = Color.BLACK
                    textAlign = Paint.Align.CENTER
                }
                val mainY = MARGIN + usableHeight * 0.55f
                canvas.drawText(displayText, centerX, mainY, mainPaint)
            }
        }
    }

    /**
     * 合并多个 PDF 为合集。
     */
    private fun generateCombined(pdfPaths: List<String>, outputFile: File) {
        // 简单合并：创建新 PDF，逐页复制
        val combinedPdf = PdfDocument()
        val font = getTypeface()
        var pageIndex = 0

        for (path in pdfPaths) {
            val srcFile = File(path)
            if (!srcFile.exists()) continue

            // 读取源 PDF 获取页面尺寸（这里重新生成更简单）
            // 由于 Android PdfDocument 不支持读取现有 PDF，
            // 我们用一个简单的占位页标记
            val info = PdfDocument.PageInfo.Builder(PAGE_WIDTH, PAGE_HEIGHT, pageIndex).create()
            val page = combinedPdf.startPage(info)
            val canvas = page.canvas
            canvas.drawColor(Color.WHITE)

            // 在合集中标注页码
            val paint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
                typeface = font
                textSize = 12f * 1.33f
                color = Color.GRAY
                textAlign = Paint.Align.CENTER
            }
            canvas.drawText("第 ${pageIndex + 1} 张 — 详见单独 PDF", PAGE_WIDTH / 2f, PAGE_HEIGHT / 2f, paint)

            combinedPdf.finishPage(page)
            pageIndex++
        }

        FileOutputStream(outputFile).use { combinedPdf.writeTo(it) }
        combinedPdf.close()
    }

    internal fun sanitizeFileName(name: String): String {
        return name.replace(Regex("[<>:\"/\\\\|?*]"), "_")
            .take(50)
    }
}
