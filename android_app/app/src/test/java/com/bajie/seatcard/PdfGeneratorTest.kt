package com.bajie.seatcard

import org.junit.Assert.*
import org.junit.Test

/**
 * PdfGenerator 纯逻辑单元测试
 *
 * 覆盖:
 *  - formatName: 两字中文姓名插全角空格 / 非两字保持不变
 *  - sanitizeFileName: 非法字符替换 / 长度截断 / 正常名称
 *
 * 注意: generateAll / generateSingle 等依赖 Android PdfDocument 的方法
 *       需要在 Android 仪器化测试 (androidTest) 中运行，此处不覆盖。
 */
class PdfGeneratorTest {

    // 使用一个最小化的 PdfGenerator 实例来测试 internal 方法。
    // context 传 null 仅用于调用不依赖 context 的纯函数（formatName / sanitizeFileName）。
    // 这些方法不访问 context 字段，因此不会 NPE。
    private val generator = PdfGenerator(null as android.content.Context?)

    // ========== formatName ==========

    @Test
    fun `formatName - two char Chinese name gets full-width space`() {
        assertEquals("张\u3000三", generator.formatName("张三"))
    }

    @Test
    fun `formatName - three char name unchanged`() {
        assertEquals("欧阳修", generator.formatName("欧阳修"))
    }

    @Test
    fun `formatName - single char unchanged`() {
        assertEquals("张", generator.formatName("张"))
    }

    @Test
    fun `formatName - four char name unchanged`() {
        assertEquals("司马相如", generator.formatName("司马相如"))
    }

    @Test
    fun `formatName - empty string unchanged`() {
        assertEquals("", generator.formatName(""))
    }

    @Test
    fun `formatName - non-Chinese two chars unchanged`() {
        // formatName 只对两字且均为中文的情况插入空格
        assertEquals("AB", generator.formatName("AB"))
    }

    // ========== sanitizeFileName ==========

    @Test
    fun `sanitizeFileName - removes angle brackets`() {
        val result = generator.sanitizeFileName("file<name>test")
        assertFalse(result.contains("<"))
        assertFalse(result.contains(">"))
    }

    @Test
    fun `sanitizeFileName - removes quotes and colons`() {
        val result = generator.sanitizeFileName("file:\"name\"")
        assertFalse(result.contains(":"))
        assertFalse(result.contains("\""))
    }

    @Test
    fun `sanitizeFileName - removes backslash and pipe`() {
        val result = generator.sanitizeFileName("path\\name|test")
        assertFalse(result.contains("\\"))
        assertFalse(result.contains("|"))
    }

    @Test
    fun `sanitizeFileName - removes question mark and asterisk`() {
        val result = generator.sanitizeFileName("file?name*test")
        assertFalse(result.contains("?"))
        assertFalse(result.contains("*"))
    }

    @Test
    fun `sanitizeFileName - truncates to 50 chars`() {
        val longName = "a".repeat(100)
        val result = generator.sanitizeFileName(longName)
        assertEquals(50, result.length)
    }

    @Test
    fun `sanitizeFileName - preserves normal Chinese name`() {
        assertEquals("张三", generator.sanitizeFileName("张三"))
    }

    @Test
    fun `sanitizeFileName - empty string unchanged`() {
        assertEquals("", generator.sanitizeFileName(""))
    }

    @Test
    fun `sanitizeFileName - replaces all illegal chars in combination`() {
        val result = generator.sanitizeFileName("<>:\"/\\|?*")
        assertEquals("_________".take(9), result.replace("_", "_")) // all replaced
        assertEquals(9, result.length)
    }
}
