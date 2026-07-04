package com.bajie.seatcard

import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Before
import org.junit.Test
import java.lang.reflect.Method

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
    private lateinit var parseMethod: Method
    private lateinit var fallbackMethod: Method

    @Before
    fun setUp() {
        service = MiniMaxService(apiKey = "test-key")

        // 通过反射访问 private 方法
        parseMethod = MiniMaxService::class.java.getDeclaredMethod(
            "parseAiResponse", String::class.java
        ).apply { isAccessible = true }

        fallbackMethod = MiniMaxService::class.java.getDeclaredMethod(
            "fallbackParse", String::class.java
        ).apply { isAccessible = true }
    }

    // ==================== parseAiResponse 测试 ====================

    @Test
    fun parseAiResponse_validJsonArray() {
        val input = """[{"name":"张三","company":"测试公司","position":"工程师"}]"""
        @Suppress("UNCHECKED_CAST")
        val result = parseMethod.invoke(service, input) as List<PersonInfo>

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
        @Suppress("UNCHECKED_CAST")
        val result = parseMethod.invoke(service, input) as List<PersonInfo>

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
        @Suppress("UNCHECKED_CAST")
        val result = parseMethod.invoke(service, input) as List<PersonInfo>

        assertEquals(1, result.size)
        assertEquals("张三", result[0].name)
    }

    @Test
    fun parseAiResponse_emptyArray() {
        val input = "[]"
        @Suppress("UNCHECKED_CAST")
        val result = parseMethod.invoke(service, input) as List<PersonInfo>

        assertTrue(result.isEmpty())
    }

    @Test
    fun parseAiResponse_noBrackets() {
        val input = "这不是 JSON"
        @Suppress("UNCHECKED_CAST")
        val result = parseMethod.invoke(service, input) as List<PersonInfo>

        assertTrue(result.isEmpty())
    }

    @Test
    fun parseAiResponse_malformedJson() {
        val input = "[{invalid json}]"
        @Suppress("UNCHECKED_CAST")
        val result = parseMethod.invoke(service, input) as List<PersonInfo>

        assertTrue(result.isEmpty())
    }

    @Test
    fun parseAiResponse_skipsEmptyNames() {
        val input = """[{"name":"","company":"公司","position":"职位"},{"name":"张三","company":"","position":""}]"""
        @Suppress("UNCHECKED_CAST")
        val result = parseMethod.invoke(service, input) as List<PersonInfo>

        assertEquals(1, result.size)
        assertEquals("张三", result[0].name)
    }

    @Test
    fun parseAiResponse_trimsWhitespace() {
        val input = """[{"name":" 张三 ","company":" 公司 ","position":" 职位 "}]"""
        @Suppress("UNCHECKED_CAST")
        val result = parseMethod.invoke(service, input) as List<PersonInfo>

        assertEquals("张三", result[0].name)
        assertEquals("公司", result[0].company)
        assertEquals("职位", result[0].position)
    }

    @Test
    fun parseAiResponse_missingFields() {
        val input = """[{"name":"张三"}]"""
        @Suppress("UNCHECKED_CAST")
        val result = parseMethod.invoke(service, input) as List<PersonInfo>

        assertEquals(1, result.size)
        assertEquals("张三", result[0].name)
        assertEquals("", result[0].company)
        assertEquals("", result[0].position)
    }

    @Test
    fun parseAiResponse_emptyString() {
        @Suppress("UNCHECKED_CAST")
        val result = parseMethod.invoke(service, "") as List<PersonInfo>

        assertTrue(result.isEmpty())
    }

    @Test
    fun parseAiResponse_onlyClosingBracket() {
        val input = "]}["
        @Suppress("UNCHECKED_CAST")
        val result = parseMethod.invoke(service, input) as List<PersonInfo>

        assertTrue(result.isEmpty())
    }

    // ==================== fallbackParse 测试 ====================

    @Test
    fun fallbackParse_commaSeparated() {
        val input = "张三,李四,王五"
        @Suppress("UNCHECKED_CAST")
        val result = fallbackMethod.invoke(service, input) as List<PersonInfo>

        assertEquals(3, result.size)
        assertEquals("张三", result[0].name)
        assertEquals("李四", result[1].name)
        assertEquals("王五", result[2].name)
    }

    @Test
    fun fallbackParse_semicolonSeparated() {
        val input = "张三;李四;王五"
        @Suppress("UNCHECKED_CAST")
        val result = fallbackMethod.invoke(service, input) as List<PersonInfo>

        assertEquals(3, result.size)
    }

    @Test
    fun fallbackParse_chinesePunctuation() {
        val input = "张三，李四，王五"
        @Suppress("UNCHECKED_CAST")
        val result = fallbackMethod.invoke(service, input) as List<PersonInfo>

        assertEquals(3, result.size)
        assertEquals("张三", result[0].name)
        assertEquals("李四", result[1].name)
        assertEquals("王五", result[2].name)
    }

    @Test
    fun fallbackParse_newlineSeparated() {
        val input = "张三\n李四\n王五"
        @Suppress("UNCHECKED_CAST")
        val result = fallbackMethod.invoke(service, input) as List<PersonInfo>

        assertEquals(3, result.size)
    }

    @Test
    fun fallbackParse_numberedList() {
        val input = "1. 张三\n2. 李四\n3. 王五"
        @Suppress("UNCHECKED_CAST")
        val result = fallbackMethod.invoke(service, input) as List<PersonInfo>

        assertEquals(3, result.size)
        assertEquals("张三", result[0].name)
        assertEquals("李四", result[1].name)
    }

    @Test
    fun fallbackParse_chineseNumberedList() {
        val input = "1、张三\n2、李四"
        @Suppress("UNCHECKED_CAST")
        val result = fallbackMethod.invoke(service, input) as List<PersonInfo>

        assertEquals(2, result.size)
        assertEquals("张三", result[0].name)
    }

    @Test
    fun fallbackParse_removesDuplicates() {
        val input = "张三,李四,张三"
        @Suppress("UNCHECKED_CAST")
        val result = fallbackMethod.invoke(service, input) as List<PersonInfo>

        assertEquals(2, result.size)
    }

    @Test
    fun fallbackParse_filtersTooShort() {
        val input = "张,张三,李四"
        @Suppress("UNCHECKED_CAST")
        val result = fallbackMethod.invoke(service, input) as List<PersonInfo>

        // 单字 "张" 长度 < 2，被过滤
        assertEquals(2, result.size)
    }

    @Test
    fun fallbackParse_filtersTooLong() {
        val longName = "a".repeat(21)
        val input = "张三,$longName,李四"
        @Suppress("UNCHECKED_CAST")
        val result = fallbackMethod.invoke(service, input) as List<PersonInfo>

        // 超长名称被过滤
        assertEquals(2, result.size)
    }

    @Test
    fun fallbackParse_emptyInput() {
        @Suppress("UNCHECKED_CAST")
        val result = fallbackMethod.invoke(service, "") as List<PersonInfo>

        assertTrue(result.isEmpty())
    }

    @Test
    fun fallbackParse_mixedSeparators() {
        val input = "张三，李四;王五\n赵六"
        @Suppress("UNCHECKED_CAST")
        val result = fallbackMethod.invoke(service, input) as List<PersonInfo>

        assertEquals(4, result.size)
    }

    @Test
    fun fallbackParse_trimsWhitespace() {
        val input = " 张三 , 李四 , 王五 "
        @Suppress("UNCHECKED_CAST")
        val result = fallbackMethod.invoke(service, input) as List<PersonInfo>

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
        // 通过反射验证字段已更新
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
