package com.bajie.seatcard

import org.junit.Assert.*
import org.junit.Before
import org.junit.Test

/**
 * MiniMaxService 单元测试
 *
 * 测试覆盖:
 * - parseAiResponse: AI 响应解析（JSON 提取、边界情况）
 * - fallbackParse: 本地正则切分（逗号/分号/换行分隔）
 * - extractPersonInfo: API Key 校验、fallback 触发
 * - updateConfig: 运行时配置更新
 */
class MiniMaxServiceTest {

    private lateinit var service: MiniMaxService

    @Before
    fun setUp() {
        service = MiniMaxService(apiKey = "test-key")
    }

    // ==================== parseAiResponse 测试 ====================

    @Test
    fun parseAiResponse_validJsonArray() {
        val input = """[{"name":"张三","company":"测试公司","position":"工程师"}]"""
        val result = service.parseAiResponse(input)

        assertEquals(1, result.size)
        assertEquals("张三", result[0].name)
        assertEquals("测试公司", result[0].company)
        assertEquals("工程师", result[0].position)
    }

    @Test
    fun parseAiResponse_multiplePersons() {
        val input = """[
            {"name":"张三","company":"A公司","position":"工程师"},
            {"name":"李四","company":"B公司","position":"设计师"},
            {"name":"王五","company":"C公司","position":"产品经理"}
        ]"""
        val result = service.parseAiResponse(input)

        assertEquals(3, result.size)
        assertEquals("张三", result[0].name)
        assertEquals("李四", result[1].name)
        assertEquals("王五", result[2].name)
    }

    @Test
    fun parseAiResponse_jsonWithSurroundingText() {
        val input = """好的，以下是提取结果：
[{"name":"张三","company":"公司","position":"职位"}]
希望这对你有帮助。"""
        val result = service.parseAiResponse(input)

        assertEquals(1, result.size)
        assertEquals("张三", result[0].name)
    }

    @Test
    fun parseAiResponse_emptyArray() {
        val result = service.parseAiResponse("[]")
        assertTrue(result.isEmpty())
    }

    @Test
    fun parseAiResponse_noBrackets() {
        val result = service.parseAiResponse("这不是 JSON")
        assertTrue(result.isEmpty())
    }

    @Test
    fun parseAiResponse_malformedJson() {
        val result = service.parseAiResponse("[{invalid json}]")
        assertTrue(result.isEmpty())
    }

    @Test
    fun parseAiResponse_skipsEmptyNames() {
        val input = """[{"name":"","company":"公司","position":"职位"},{"name":"张三","company":"","position":""}]"""
        val result = service.parseAiResponse(input)

        assertEquals(1, result.size)
        assertEquals("张三", result[0].name)
    }

    @Test
    fun parseAiResponse_trimsWhitespace() {
        val input = """[{"name":" 张三 ","company":" 公司 ","position":" 职位 "}]"""
        val result = service.parseAiResponse(input)

        assertEquals("张三", result[0].name)
        assertEquals("公司", result[0].company)
        assertEquals("职位", result[0].position)
    }

    @Test
    fun parseAiResponse_missingFields() {
        val input = """[{"name":"张三"}]"""
        val result = service.parseAiResponse(input)

        assertEquals(1, result.size)
        assertEquals("张三", result[0].name)
        assertEquals("", result[0].company)
        assertEquals("", result[0].position)
    }

    @Test
    fun parseAiResponse_emptyString() {
        val result = service.parseAiResponse("")
        assertTrue(result.isEmpty())
    }

    @Test
    fun parseAiResponse_onlyClosingBracket() {
        val result = service.parseAiResponse("]}[")
        assertTrue(result.isEmpty())
    }

    // ==================== fallbackParse 测试 ====================

    @Test
    fun fallbackParse_commaSeparated() {
        val result = service.fallbackParse("张三,李四,王五")

        assertEquals(3, result.size)
        assertEquals("张三", result[0].name)
        assertEquals("李四", result[1].name)
        assertEquals("王五", result[2].name)
    }

    @Test
    fun fallbackParse_semicolonSeparated() {
        val result = service.fallbackParse("张三;李四;王五")
        assertEquals(3, result.size)
    }

    @Test
    fun fallbackParse_chinesePunctuation() {
        val result = service.fallbackParse("张三，李四，王五")

        assertEquals(3, result.size)
        assertEquals("张三", result[0].name)
        assertEquals("李四", result[1].name)
        assertEquals("王五", result[2].name)
    }

    @Test
    fun fallbackParse_newlineSeparated() {
        val result = service.fallbackParse("张三\n李四\n王五")
        assertEquals(3, result.size)
    }

    @Test
    fun fallbackParse_numberedList() {
        val result = service.fallbackParse("1. 张三\n2. 李四\n3. 王五")

        assertEquals(3, result.size)
        assertEquals("张三", result[0].name)
        assertEquals("李四", result[1].name)
    }

    @Test
    fun fallbackParse_chineseNumberedList() {
        val result = service.fallbackParse("1、张三\n2、李四")

        assertEquals(2, result.size)
        assertEquals("张三", result[0].name)
    }

    @Test
    fun fallbackParse_removesDuplicates() {
        val result = service.fallbackParse("张三,李四,张三")
        assertEquals(2, result.size)
    }

    @Test
    fun fallbackParse_filtersTooShort() {
        val result = service.fallbackParse("张,张三,李四")
        // 单字 "张" 长度 < 2，被过滤
        assertEquals(2, result.size)
    }

    @Test
    fun fallbackParse_filtersTooLong() {
        val longName = "a".repeat(21)
        val result = service.fallbackParse("张三,$longName,李四")
        // 超长名称被过滤
        assertEquals(2, result.size)
    }

    @Test
    fun fallbackParse_emptyInput() {
        val result = service.fallbackParse("")
        assertTrue(result.isEmpty())
    }

    @Test
    fun fallbackParse_mixedSeparators() {
        val result = service.fallbackParse("张三，李四;王五\n赵六")
        assertEquals(4, result.size)
    }

    @Test
    fun fallbackParse_trimsWhitespace() {
        val result = service.fallbackParse(" 张三 , 李四 , 王五 ")

        assertEquals(3, result.size)
        assertEquals("张三", result[0].name)
        assertEquals("李四", result[1].name)
    }

    // ==================== extractPersonInfo 测试 ====================

    @Test
    fun extractPersonInfo_blankApiKey_returnsFailure() {
        val noKeyService = MiniMaxService(apiKey = "")
        val result = noKeyService.extractPersonInfo("张三,李四")

        assertTrue(result.isFailure)
        assertTrue(result.exceptionOrNull()!!.message!!.contains("API Key"))
    }

    @Test
    fun extractPersonInfo_blankApiKey_whitespace() {
        val noKeyService = MiniMaxService(apiKey = "   ")
        val result = noKeyService.extractPersonInfo("张三,李四")

        assertTrue(result.isFailure)
    }

    // ==================== updateConfig 测试 ====================

    @Test
    fun updateConfig_changesFields() {
        service.updateConfig("https://new.api.com", "new-key", "new-model")
        // 通过反射验证字段已更新（字段仍为 private）
        val baseUrlField = MiniMaxService::class.java.getDeclaredField("baseUrl")
        baseUrlField.isAccessible = true
        assertEquals("https://new.api.com", baseUrlField.get(service))

        val apiKeyField = MiniMaxService::class.java.getDeclaredField("apiKey")
        apiKeyField.isAccessible = true
        assertEquals("new-key", apiKeyField.get(service))

        val modelField = MiniMaxService::class.java.getDeclaredField("model")
        modelField.isAccessible = true
        assertEquals("new-model", modelField.get(service))
    }
}
