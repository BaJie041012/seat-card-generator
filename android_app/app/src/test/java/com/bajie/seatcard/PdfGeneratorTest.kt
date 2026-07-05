package com.bajie.seatcard

import android.content.Context
import org.junit.Assert.*
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.RuntimeEnvironment
import org.robolectric.annotation.Config
import java.io.File

/**
 * PdfGenerator 单元测试（使用 Robolectric 模拟 Android 环境）
 *
 * 测试覆盖:
 * - formatName: 两字中文姓名全角空格插入
 * - sanitizeFileName: 文件名安全处理
 * - generateAll: 批量生成流程（目录结构、成功/失败列表）
 * - generateCombined: 合集生成（占位页）
 */
@RunWith(RobolectricTestRunner::class)
@Config(sdk = [33], manifest = Config.NONE)
class PdfGeneratorTest {

    private lateinit var context: Context
    private lateinit var generator: PdfGenerator

    @Before
    fun setUp() {
        context = RuntimeEnvironment.getApplication()
        generator = PdfGenerator(context)
    }

    // ==================== formatName 测试 ====================

    @Test
    fun formatName_twoChineseChars_insertsSpace() {
        assertEquals("张\u3000三", generator.formatName("张三"))
    }

    @Test
    fun formatName_threeOrMoreChars_unchanged() {
        assertEquals("张三丰", generator.formatName("张三丰"))
    }

    @Test
    fun formatName_singleChar_unchanged() {
        assertEquals("张", generator.formatName("张"))
    }

    @Test
    fun formatName_emptyString_unchanged() {
        assertEquals("", generator.formatName(""))
    }

    @Test
    fun formatName_twoEnglishChars_unchanged() {
        // 非中文字符不插入全角空格
        assertEquals("AB", generator.formatName("AB"))
    }

    @Test
    fun formatName_mixedTwoChars_unchanged() {
        // 混合字符（非全中文）不插入
        assertEquals("A张", generator.formatName("A张"))
    }

    @Test
    fun formatName_fourChineseChars_unchanged() {
        assertEquals("张三李四", generator.formatName("张三李四"))
    }

    // ==================== sanitizeFileName 测试 ====================

    @Test
    fun sanitizeFileName_removesIllegalChars() {
        val result = generator.sanitizeFileName("file<>name")
        assertFalse(result.contains("<"))
        assertFalse(result.contains(">"))
    }

    @Test
    fun sanitizeFileName_removesColon() {
        val result = generator.sanitizeFileName("file:name")
        assertFalse(result.contains(":"))
    }

    @Test
    fun sanitizeFileName_removesSlash() {
        val result = generator.sanitizeFileName("file/name")
        assertFalse(result.contains("/"))
    }

    @Test
    fun sanitizeFileName_removesBackslash() {
        val result = generator.sanitizeFileName("file\\name")
        assertFalse(result.contains("\\"))
    }

    @Test
    fun sanitizeFileName_removesQuestionMark() {
        val result = generator.sanitizeFileName("file?name")
        assertFalse(result.contains("?"))
    }

    @Test
    fun sanitizeFileName_removesAsterisk() {
        val result = generator.sanitizeFileName("file*name")
        assertFalse(result.contains("*"))
    }

    @Test
    fun sanitizeFileName_removesPipe() {
        val result = generator.sanitizeFileName("file|name")
        assertFalse(result.contains("|"))
    }

    @Test
    fun sanitizeFileName_truncatesAt50() {
        val longName = "a".repeat(100)
        assertEquals(50, generator.sanitizeFileName(longName).length)
    }

    @Test
    fun sanitizeFileName_preservesChinese() {
        assertEquals("张三的席卡", generator.sanitizeFileName("张三的席卡"))
    }

    @Test
    fun sanitizeFileName_emptyString() {
        assertEquals("", generator.sanitizeFileName(""))
    }

    @Test
    fun sanitizeFileName_normalNameUnchanged() {
        assertEquals("正常文件名", generator.sanitizeFileName("正常文件名"))
    }

    // ==================== generateAll 测试 ====================

    @Test
    fun generateAll_createsOutputDirectories() {
        val tmpDir = createTempDir("seatcard_test")
        try {
            val persons = listOf(PersonInfo(name = "张三"))
            generator.generateAll(
                persons = persons,
                template = TemplateType.V4,
                displayType = DisplayType.NAME,
                eventName = "测试活动",
                outputDir = tmpDir
            )

            assertTrue(File(tmpDir, "pdf").exists())
        } finally {
            tmpDir.deleteRecursively()
        }
    }

    @Test
    fun generateAll_returnsCorrectStructure() {
        val tmpDir = createTempDir("seatcard_test")
        try {
            val persons = listOf(
                PersonInfo(name = "张三", company = "A公司"),
                PersonInfo(name = "李四", company = "B公司")
            )
            val (successCards, failedNames, outputDir) = generator.generateAll(
                persons = persons,
                template = TemplateType.V4,
                displayType = DisplayType.NAME,
                eventName = "测试",
                outputDir = tmpDir
            )

            assertEquals(tmpDir.absolutePath, outputDir)
            assertTrue(failedNames.isEmpty())
        } finally {
            tmpDir.deleteRecursively()
        }
    }

    @Test
    fun generateAll_emptyPersonsList() {
        val tmpDir = createTempDir("seatcard_test")
        try {
            val (successCards, failedNames, _) = generator.generateAll(
                persons = emptyList(),
                template = TemplateType.V4,
                displayType = DisplayType.NAME,
                eventName = "",
                outputDir = tmpDir
            )

            assertTrue(successCards.isEmpty())
            assertTrue(failedNames.isEmpty())
        } finally {
            tmpDir.deleteRecursively()
        }
    }

    @Test
    fun generateAll_companyDisplayType() {
        val tmpDir = createTempDir("seatcard_test")
        try {
            val persons = listOf(PersonInfo(name = "张三", company = "测试公司"))
            val (successCards, _, _) = generator.generateAll(
                persons = persons,
                template = TemplateType.V4,
                displayType = DisplayType.COMPANY,
                eventName = "",
                outputDir = tmpDir
            )

            assertEquals(1, successCards.size)
            assertEquals("张三", successCards[0].personName)
        } finally {
            tmpDir.deleteRecursively()
        }
    }

    @Test
    fun generateAll_companyDisplayFallbackToName() {
        val tmpDir = createTempDir("seatcard_test")
        try {
            val persons = listOf(PersonInfo(name = "张三", company = ""))
            val (successCards, failedNames, _) = generator.generateAll(
                persons = persons,
                template = TemplateType.V4,
                displayType = DisplayType.COMPANY,
                eventName = "",
                outputDir = tmpDir
            )

            assertEquals(1, successCards.size)
            assertTrue(failedNames.isEmpty())
        } finally {
            tmpDir.deleteRecursively()
        }
    }

    @Test
    fun generateAll_v5Template() {
        val tmpDir = createTempDir("seatcard_test")
        try {
            val persons = listOf(PersonInfo(name = "张三"))
            val (successCards, _, _) = generator.generateAll(
                persons = persons,
                template = TemplateType.V5,
                displayType = DisplayType.NAME,
                eventName = "",
                outputDir = tmpDir
            )

            assertEquals(1, successCards.size)
        } finally {
            tmpDir.deleteRecursively()
        }
    }

    @Test
    fun generateAll_multiplePersonsCreatesCombined() {
        val tmpDir = createTempDir("seatcard_test")
        try {
            val persons = listOf(
                PersonInfo(name = "张三"),
                PersonInfo(name = "李四"),
                PersonInfo(name = "王五")
            )
            generator.generateAll(
                persons = persons,
                template = TemplateType.V4,
                displayType = DisplayType.NAME,
                eventName = "",
                outputDir = tmpDir
            )

            val combinedFiles = tmpDir.listFiles()?.filter {
                it.name.startsWith("席卡合集_")
            }
            assertNotNull(combinedFiles)
            assertTrue(combinedFiles!!.isNotEmpty())
        } finally {
            tmpDir.deleteRecursively()
        }
    }

    @Test
    fun generateAll_singlePersonNoCombined() {
        val tmpDir = createTempDir("seatcard_test")
        try {
            val persons = listOf(PersonInfo(name = "张三"))
            generator.generateAll(
                persons = persons,
                template = TemplateType.V4,
                displayType = DisplayType.NAME,
                eventName = "",
                outputDir = tmpDir
            )

            val combinedFiles = tmpDir.listFiles()?.filter {
                it.name.startsWith("席卡合集_")
            }
            assertTrue(combinedFiles == null || combinedFiles.isEmpty())
        } finally {
            tmpDir.deleteRecursively()
        }
    }

    // ==================== generateCombined 测试 ====================

    @Test
    fun generateCombined_createsFile() {
        val tmpDir = createTempDir("seatcard_test")
        try {
            val outputFile = File(tmpDir, "combined.pdf")
            generator.generateCombined(emptyList(), outputFile)
            assertTrue(outputFile.exists())
        } finally {
            tmpDir.deleteRecursively()
        }
    }

    @Test
    fun generateCombined_skipsNonexistentFiles() {
        val tmpDir = createTempDir("seatcard_test")
        try {
            val outputFile = File(tmpDir, "combined.pdf")
            val fakePaths = listOf("/nonexistent/file1.pdf", "/nonexistent/file2.pdf")
            generator.generateCombined(fakePaths, outputFile)
            assertTrue(outputFile.exists())
        } finally {
            tmpDir.deleteRecursively()
        }
    }

    // ==================== Models 测试 ====================

    @Test
    fun personInfo_defaultValues() {
        val person = PersonInfo(name = "张三")
        assertEquals("张三", person.name)
        assertEquals("", person.company)
        assertEquals("", person.position)
        assertEquals("", person.originalLine)
    }

    @Test
    fun templateType_displayNames() {
        assertTrue(TemplateType.V4.displayName.contains("v4"))
        assertTrue(TemplateType.V5.displayName.contains("v5"))
    }

    @Test
    fun displayType_displayNames() {
        assertTrue(DisplayType.NAME.displayName.contains("姓名"))
        assertTrue(DisplayType.COMPANY.displayName.contains("公司"))
    }

    @Test
    fun cardResult_defaultErrorMessage() {
        val result = CardResult(personName = "张三", pdfPath = "/path", success = true)
        assertEquals("", result.errorMessage)
    }
}
