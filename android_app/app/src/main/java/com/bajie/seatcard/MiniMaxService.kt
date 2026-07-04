package com.bajie.seatcard

import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONArray
import org.json.JSONObject
import java.util.concurrent.TimeUnit

class MiniMaxService(
    private var baseUrl: String = "https://api.minimaxi.com/v1",
    private var apiKey: String = "",
    private var model: String = "MiniMax-M2.5"
) {
    private val client = OkHttpClient.Builder()
        .connectTimeout(30, TimeUnit.SECONDS)
        .readTimeout(30, TimeUnit.SECONDS)
        .writeTimeout(30, TimeUnit.SECONDS)
        .build()

    fun updateConfig(baseUrl: String, apiKey: String, model: String) {
        this.baseUrl = baseUrl
        this.apiKey = apiKey
        this.model = model
    }

    /**
     * 调用 MiniMax AI 从文本中提取人员信息。
     * 最多重试 3 次，每次间隔指数增长。
     */
    fun extractPersonInfo(text: String): Result<List<PersonInfo>> {
        if (apiKey.isBlank()) {
            return Result.failure(Exception("API Key 未配置，请先在设置中填写"))
        }

        val prompt = buildString {
            appendLine("你是一个智能文本信息提取助手。请从用户输入的文本中提取人员的姓名、单位和职位信息。")
            appendLine()
            appendLine("支持的输入格式：")
            appendLine("- 每行一个人，格式如：姓名 单位 职位（空格/逗号/制表符分隔）")
            appendLine("- 纯姓名列表（逗号/分号/换行分隔）")
            appendLine("- 混合文本（需要从中提取人员信息）")
            appendLine("- 带编号的列表")
            appendLine()
            appendLine("请严格以 JSON 数组格式返回，不要包含其他文字：")
            appendLine("""[{"name": "姓名", "company": "单位", "position": "职位"}]""")
            appendLine()
            appendLine("如果某个字段无法识别，请留空。")
            appendLine()
            appendLine("用户输入：")
            append(text)
        }

        var lastException: Exception? = null
        for (attempt in 0 until 3) {
            try {
                if (attempt > 0) {
                    Thread.sleep((1000L * (1 shl attempt)))
                }

                val jsonBody = JSONObject().apply {
                    put("model", model)
                    put("messages", JSONArray().apply {
                        put(JSONObject().apply {
                            put("role", "user")
                            put("content", prompt)
                        })
                    })
                    put("max_tokens", 2000)
                    put("temperature", 0.7)
                }

                val request = Request.Builder()
                    .url("${baseUrl.trimEnd('/')}/chat/completions")
                    .addHeader("Authorization", "Bearer $apiKey")
                    .addHeader("Content-Type", "application/json")
                    .post(jsonBody.toString().toRequestBody("application/json; charset=utf-8".toMediaType()))
                    .build()

                val response = client.newCall(request).execute()
                val responseBody = response.body?.string()
                response.close()

                if (!response.isSuccessful) {
                    lastException = Exception("API 返回错误: HTTP ${response.code}")
                    continue
                }

                if (responseBody != null) {
                    val data = JSONObject(responseBody)
                    val content = data.getJSONArray("choices")
                        .getJSONObject(0)
                        .getJSONObject("message")
                        .getString("content")
                    val persons = parseAiResponse(content)
                    if (persons.isNotEmpty()) {
                        return Result.success(persons)
                    }
                }
                lastException = Exception("AI 返回了空结果")
            } catch (e: Exception) {
                lastException = e
            }
        }

        // AI 失败，使用 fallback
        val fallback = fallbackParse(text)
        return if (fallback.isNotEmpty()) {
            Result.success(fallback)
        } else {
            Result.failure(lastException ?: Exception("无法从文本中提取人员信息"))
        }
    }

    internal fun parseAiResponse(response: String): List<PersonInfo> {
        val start = response.indexOf('[')
        val end = response.lastIndexOf(']')
        if (start < 0 || end < 0 || end <= start) return emptyList()

        return try {
            val jsonStr = response.substring(start, end + 1)
            val jsonArray = JSONArray(jsonStr)
            val result = mutableListOf<PersonInfo>()
            for (i in 0 until jsonArray.length()) {
                val obj = jsonArray.getJSONObject(i)
                val name = obj.optString("name", "").trim()
                if (name.isNotEmpty()) {
                    result.add(PersonInfo(
                        name = name,
                        company = obj.optString("company", "").trim(),
                        position = obj.optString("position", "").trim()
                    ))
                }
            }
            result
        } catch (e: Exception) {
            emptyList()
        }
    }

    /** Fallback：本地正则切分，仅提取姓名 */
    internal fun fallbackParse(text: String): List<PersonInfo> {
        val lines = text.split(Regex("[,;，；\\n]+"))
        val result = mutableListOf<PersonInfo>()
        val seen = mutableSetOf<String>()

        for (line in lines) {
            val trimmed = line.trim()
                .replace(Regex("^\\d+[.、)）\\s]+"), "")
                .trim()
            if (trimmed.isEmpty()) continue
            if (trimmed.length in 2..20 && trimmed !in seen) {
                seen.add(trimmed)
                result.add(PersonInfo(name = trimmed))
            }
        }
        return result
    }
}
