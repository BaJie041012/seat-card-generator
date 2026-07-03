package com.bajie.seatcard

import android.content.Intent
import android.os.Bundle
import android.view.Menu
import android.view.MenuItem
import android.view.View
import android.widget.*
import androidx.appcompat.app.AppCompatActivity
import com.google.android.material.appbar.MaterialToolbar
import com.google.android.material.button.MaterialButton
import com.google.android.material.progressindicator.LinearProgressIndicator
import com.google.android.material.radiobutton.MaterialRadioButton
import com.google.android.material.textfield.TextInputEditText
import com.google.android.material.textfield.TextInputLayout
import kotlinx.coroutines.*
import java.io.File

class MainActivity : AppCompatActivity() {

    private val miniMaxService = MiniMaxService()
    private val pdfGenerator by lazy { PdfGenerator(this) }
    private val scope = CoroutineScope(Dispatchers.Main + SupervisorJob())

    // Views
    private lateinit var inputText: TextInputEditText
    private lateinit var eventNameInput: TextInputEditText
    private lateinit var eventNameLayout: TextInputLayout
    private lateinit var radioV4: MaterialRadioButton
    private lateinit var radioV5: MaterialRadioButton
    private lateinit var radioName: MaterialRadioButton
    private lateinit var radioCompany: MaterialRadioButton
    private lateinit var btnGenerate: MaterialButton
    private lateinit var progressIndicator: LinearProgressIndicator
    private lateinit var statusText: TextView

    // Default API key
    private val defaultApiKey = "sk-api-mR_lRPZgFVmmyx7OCp83-zqdd2nlvTYM-akr0KyrDIa1ZvrZV4F0sKmKOXULeT8xP3xOYnyEh4_DJTb760jnSL_HfEU2zMOudelCxSObltogy0Xx5a2c"

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setupUI()
        loadSettings()
    }

    override fun onResume() {
        super.onResume()
        loadSettings()
    }

    override fun onDestroy() {
        super.onDestroy()
        scope.cancel()
    }

    private fun setupUI() {
        // Root layout
        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            fitsSystemWindows = true
        }

        // Toolbar
        val toolbar = MaterialToolbar(this).apply {
            title = "席卡生成"
            setBackgroundColor(resources.getColor(R.color.primary, theme))
            setTitleTextColor(resources.getColor(R.color.on_primary, theme))
            layoutParams = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                resources.getDimensionPixelSize(com.google.android.material.R.dimen.abc_action_bar_default_height_material)
            )
        }
        toolbar.inflateMenu(R.menu.main_menu)
        toolbar.setOnMenuItemClickListener { item ->
            when (item.itemId) {
                R.id.action_settings -> {
                    startActivity(Intent(this, SettingsActivity::class.java))
                    true
                }
                else -> false
            }
        }
        root.addView(toolbar)

        // Scrollable content
        val scrollView = android.widget.ScrollView(this).apply {
            layoutParams = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                0, 1f
            )
        }
        val content = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(48, 24, 48, 24)
        }

        // --- Input text area ---
        val inputLayout = TextInputLayout(this).apply {
            hint = "输入人员信息"
            helperText = "每行一人，或粘贴名单让 AI 自动识别\n格式：姓名 单位 职位（空格分隔）"
            layoutParams = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
            ).apply { setMargins(0, 0, 0, 24) }
        }
        inputText = TextInputEditText(this).apply {
            minLines = 5
            gravity = android.view.Gravity.TOP
            inputType = android.text.InputType.TYPE_CLASS_TEXT or android.text.InputType.TYPE_TEXT_FLAG_MULTI_LINE
        }
        inputLayout.addView(inputText)
        content.addView(inputLayout)

        // --- Event name (for v4) ---
        eventNameLayout = TextInputLayout(this).apply {
            hint = "活动名称（v4 模板显示）"
            layoutParams = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
            ).apply { setMargins(0, 0, 0, 24) }
        }
        eventNameInput = TextInputEditText(this).apply {
            setText("")
        }
        eventNameLayout.addView(eventNameInput)
        content.addView(eventNameLayout)

        // --- Template selector ---
        val templateLabel = TextView(this).apply {
            text = "选择模板"
            textSize = 14f
            setPadding(0, 0, 0, 8)
        }
        content.addView(templateLabel)

        val templateGroup = RadioGroup(this).apply {
            orientation = RadioGroup.HORIZONTAL
            layoutParams = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
            ).apply { setMargins(0, 0, 0, 24) }
        }
        radioV4 = MaterialRadioButton(this).apply {
            text = TemplateType.V4.displayName
            isChecked = true
            id = View.generateViewId()
        }
        radioV5 = MaterialRadioButton(this).apply {
            text = TemplateType.V5.displayName
            id = View.generateViewId()
        }
        templateGroup.addView(radioV4)
        templateGroup.addView(radioV5)
        content.addView(templateGroup)

        // Template change listener: show/hide event name
        templateGroup.setOnCheckedChangeListener { _, checkedId ->
            eventNameLayout.visibility = if (checkedId == radioV4.id)
                LinearLayout.LayoutParams.MATCH_PARENT else View.GONE
        }

        // --- Display type ---
        val displayLabel = TextView(this).apply {
            text = "显示内容"
            textSize = 14f
            setPadding(0, 0, 0, 8)
        }
        content.addView(displayLabel)

        val displayGroup = RadioGroup(this).apply {
            orientation = RadioGroup.HORIZONTAL
            layoutParams = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
            ).apply { setMargins(0, 0, 0, 32) }
        }
        radioName = MaterialRadioButton(this).apply {
            text = DisplayType.NAME.displayName
            isChecked = true
            id = View.generateViewId()
        }
        radioCompany = MaterialRadioButton(this).apply {
            text = DisplayType.COMPANY.displayName
            id = View.generateViewId()
        }
        displayGroup.addView(radioName)
        displayGroup.addView(radioCompany)
        content.addView(displayGroup)

        // --- Generate button ---
        btnGenerate = MaterialButton(this).apply {
            text = "生成席卡"
            layoutParams = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
            ).apply { setMargins(0, 0, 0, 16) }
        }
        btnGenerate.setOnClickListener { onGenerate() }
        content.addView(btnGenerate)

        // --- Progress ---
        progressIndicator = LinearProgressIndicator(this).apply {
            layoutParams = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
            ).apply { setMargins(0, 0, 0, 8) }
            visibility = View.GONE
            isIndeterminate = true
        }
        content.addView(progressIndicator)

        // --- Status text ---
        statusText = TextView(this).apply {
            textSize = 13f
            setTextColor(resources.getColor(com.google.android.material.R.color.material_on_surface_emphasis_medium, theme))
            visibility = View.GONE
        }
        content.addView(statusText)

        scrollView.addView(content)
        root.addView(scrollView)
        setContentView(root)
    }

    private fun loadSettings() {
        val prefs = getSharedPreferences("seatcard_settings", MODE_PRIVATE)
        val apiKey = prefs.getString("api_key", defaultApiKey) ?: defaultApiKey
        val baseUrl = prefs.getString("base_url", "https://api.minimaxi.com/v1") ?: "https://api.minimaxi.com/v1"
        val model = prefs.getString("model", "MiniMax-M2.5") ?: "MiniMax-M2.5"
        miniMaxService.updateConfig(baseUrl, apiKey, model)
    }

    private fun onGenerate() {
        val text = inputText.text?.toString()?.trim() ?: ""
        if (text.isEmpty()) {
            inputText.error = "请输入人员信息"
            return
        }

        val template = if (radioV4.isChecked) TemplateType.V4 else TemplateType.V5
        val displayType = if (radioName.isChecked) DisplayType.NAME else DisplayType.COMPANY
        val eventName = eventNameInput.text?.toString()?.trim() ?: ""

        // Disable UI
        btnGenerate.isEnabled = false
        progressIndicator.visibility = View.VISIBLE
        statusText.visibility = View.VISIBLE
        statusText.text = "正在调用 AI 识别人员信息..."

        scope.launch {
            try {
                // Step 1: AI extraction (on IO thread)
                val result = withContext(Dispatchers.IO) {
                    miniMaxService.extractPersonInfo(text)
                }

                val persons = result.getOrElse { e ->
                    statusText.text = "AI 识别失败: ${e.message}"
                    btnGenerate.isEnabled = true
                    progressIndicator.visibility = View.GONE
                    return@launch
                }

                if (persons.isEmpty()) {
                    statusText.text = "未识别到任何人员信息"
                    btnGenerate.isEnabled = true
                    progressIndicator.visibility = View.GONE
                    return@launch
                }

                statusText.text = "已识别 ${persons.size} 人，正在生成 PDF..."

                // Step 2: Generate PDFs
                val outputDir = File(filesDir, "output_${System.currentTimeMillis()}")
                val (successCards, failedNames, outputDirPath) = withContext(Dispatchers.IO) {
                    pdfGenerator.generateAll(persons, template, displayType, eventName, outputDir)
                }

                // Step 3: Show result
                statusText.text = buildString {
                    append("生成完成: ${successCards.size} 张成功")
                    if (failedNames.isNotEmpty()) {
                        append(", ${failedNames.size} 张失败")
                    }
                }

                btnGenerate.isEnabled = true
                progressIndicator.visibility = View.GONE

                // Navigate to result page
                val intent = Intent(this@MainActivity, ResultActivity::class.java).apply {
                    putStringArrayListExtra("pdf_paths", ArrayList(successCards.map { it.pdfPath }))
                    putStringArrayListExtra("person_names", ArrayList(successCards.map { it.personName }))
                    putStringArrayListExtra("failed_names", ArrayList(failedNames))
                    putExtra("output_dir", outputDirPath)
                }
                startActivity(intent)

            } catch (e: Exception) {
                statusText.text = "生成失败: ${e.message}"
                btnGenerate.isEnabled = true
                progressIndicator.visibility = View.GONE
            }
        }
    }
}
