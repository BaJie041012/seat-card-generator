package com.bajie.seatcard

import org.junit.Assert.*
import org.junit.Test

/**
 * MiniMaxService 单元测试
 *
 * 覆盖:
 *  - parseAiResponse: JSON 解析（正常/带说明文字/空/异常）
 *  - fallbackParse: 本地正则回退（逗号/分号/换行/去重/编号/边界）
 *  - extractPersonInfo: API Key 校验
 *  - updateConfig: 配置更新
 */
class MiniMaxServiceTest {

    private val service = MiniMaxService()

    // ========== parseAiResponse ==========

    @Test
    fun `parseAiResponse - standard JSON array`() {
        val input = """[{"name":"张三","company":"A公司","position":"工程师"},{"name":"李四","company":"B公司","position":"设计师"}]"""
        val result = service.parseAiResponse(input)
        assertEquals(2, result.size)
        assertEquals("张三", result[0].name)
        assertEquals("A公司", result[0].company)
        assertEquals("工程师", result[0].position)
        assertEquals("李四", result[1].name)
    }

    @Test
    fun `parseAiResponse - JSON embedded in explanation text`() {
        val input = """好的，以下是提取结果：
[{"name":"王五","company":"C公司","position":"产品经理"}]
希望对你有帮助！"""
        val result = service.parseAiResponse(input)
        assertEquals(1, result.size)
        assertEquals("王五", result[0].name)
    }

    @Test
    fun `parseAiResponse - empty array returns empty list`() {
        val result = service.parseAiResponse("[]")
        assertTrue(result.isEmpty())
    }

    @Test
    fun `parseAiResponse - no JSON returns empty list`() {
        val result = service.parseAiResponse("无法识别任何人员信息")
        assertTrue(result.isEmpty())
    }

    @Test
    fun `parseAiResponse - invalid JSON returns empty list`() {
        val result = service.parseAiResponse("[invalid json content}")
        assertTrue(result.isEmpty())
    }

    @Test
    fun `parseAiResponse - entry without name is skipped`() {
        val input = """[{"name":"","company":"空公司"},{"name":"赵六","company":"","position":""}]"""
        val result = service.parseAiResponse(input)
        assertEquals(1, result.size)
        assertEquals("赵六", result[0].name)
    }

    @Test
    fun `parseAiResponse - missing fields default to empty`() {
        val input = """[{"name":"孙七"}]"""
        val result = service.parseAiResponse(input)
        assertEquals(1, result.size)
        assertEquals("孙七", result[0].name)
        assertEquals("", result[0].company)
        assertEquals("", result[0].position)
    }

    // ========== fallbackParse ==========

    @Test
    fun `fallbackParse - comma separated names`() {
        val result = service.fallbackParse("张三,李四,王五")
        assertEquals(3, result.size)
        assertEquals("张三", result[0].name)
        assertEquals("李四", result[1].name)
        assertEquals("王五", result[2].name)
    }

    @Test
    fun `fallbackParse - Chinese comma separated`() {
        val result = service.fallbackParse("张三，李四，王五")
        assertEquals(3, result.size)
    }

    @Test
    fun `fallbackParse - semicolon separated`() {
        val result = service.fallbackParse("张三;李四;王五")
        assertEquals(3, result.size)
    }

    @Test
    fun `fallbackParse - newline separated`() {
        val result = service.fallbackParse("张三\n李四\n王五")
        assertEquals(3, result.size)
    }

    @Test
    fun `fallbackParse - numbered list`() {
        val result = service.fallbackParse("1.张三\n2、李四\n3）王五\n4.赵六")
        assertEquals(4, result.size)
        assertEquals("张三", result[0].name)
        assertEquals("李四", result[1].name)
        assertEquals("王五", result[2].name)
        assertEquals("赵六", result[3].name)
    }

    @Test
    fun `fallbackParse - deduplicates names`() {
        val result = service.fallbackParse("张三,张三,李四")
        assertEquals(2, result.size)
    }

    @Test
    fun `fallbackParse - skips empty lines`() {
        val result = service.fallbackParse("张三,,李四,\n,王五")
        assertEquals(3, result.size)
    }

    @Test
    fun `fallbackParse - skips single char entries`() {
        val result = service.fallbackParse("张,李四,王")
        assertEquals(1, result.size)
        assertEquals("李四", result[0].name)
    }

    @Test
    fun `fallbackParse - trims whitespace`() {
        val result = service.fallbackParse(" 张三 , 李四 , 王五 ")
        assertEquals(3, result.size)
        assertEquals("张三", result[0].name)
    }

    // ========== extractPersonInfo - API Key 校验 ==========

    @Test
    fun `extractPersonInfo - fails when API key is blank`() {
        val svc = MiniMaxService(apiKey = "")
        val result = svc.extractPersonInfo("张三,李四")
        assertTrue(result.isFailure)
        assertTrue(result.exceptionOrNull()?.message?.contains("API Key") == true)
    }

    @Test
    fun `extractPersonInfo - fails when API key is whitespace only`() {
        val svc = MiniMaxService(apiKey = "   ")
        val result = svc.extractPersonInfo("张三")
        assertTrue(result.isFailure)
    }

    // ========== updateConfig ==========

    @Test
    fun `updateConfig - changes configuration`() {
        val svc = MiniMaxService()
        svc.updateConfig("https://new-api.example.com", "new-key", "new-model")
        // 配置已更新，无法直接读取私有属性，
        // 但可以通过 extractPersonInfo 不再报 "API Key 未配置" 来间接验证
        // （会因为网络错误而失败，但错误信息不同）
        val result = svc.extractPersonInfo("测试")
        // 如果 apiKey 生效，不会返回 "API Key 未配置"
        val errorMsg = result.exceptionOrNull()?.message ?: ""
        assertFalse("API Key 应该已被更新", errorMsg.contains("API Key 未配置"))
    }
}
