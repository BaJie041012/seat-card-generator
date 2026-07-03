package com.bajie.seatcard

import android.os.Bundle
import android.widget.LinearLayout
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import com.google.android.material.appbar.MaterialToolbar
import com.google.android.material.button.MaterialButton
import com.google.android.material.textfield.TextInputEditText
import com.google.android.material.textfield.TextInputLayout

class SettingsActivity : AppCompatActivity() {

    private val defaultApiKey = "sk-api-mR_lRPZgFVmmyx7OCp83-zqdd2nlvTYM-akr0KyrDIa1ZvrZV4F0sKmKOXULeT8xP3xOYnyEh4_DJTb760jnSL_HfEU2zMOudelCxSObltogy0X0RXx5a2c"

    private lateinit var apiKeyInput: TextInputEditText
    private lateinit var baseUrlInput: TextInputEditText
    private lateinit var modelInput: TextInputEditText

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setupUI()
        loadCurrentSettings()
    }

    private fun setupUI() {
        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            fitsSystemWindows = true
        }

        // Toolbar
        val toolbar = MaterialToolbar(this).apply {
            title = "设置"
            setBackgroundColor(resources.getColor(R.color.primary, theme))
            setTitleTextColor(resources.getColor(R.color.on_primary, theme))
            layoutParams = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                resources.getDimensionPixelSize(com.google.android.material.R.dimen.abc_action_bar_default_height_material)
            )
            setNavigationIcon(com.google.android.material.R.drawable.abc_ic_ab_back_material)
            setNavigationOnClickListener { finish() }
        }
        root.addView(toolbar)

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

        // --- API Key ---
        val apiKeyLayout = TextInputLayout(this).apply {
            hint = "API Key"
            helperText = "MiniMax API 密钥"
            layoutParams = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
            ).apply { setMargins(0, 0, 0, 24) }
        }
        apiKeyInput = TextInputEditText(this).apply {
            inputType = android.text.InputType.TYPE_CLASS_TEXT or android.text.InputType.TYPE_TEXT_VARIATION_PASSWORD
        }
        apiKeyLayout.addView(apiKeyInput)
        content.addView(apiKeyLayout)

        // --- Base URL ---
        val urlLayout = TextInputLayout(this).apply {
            hint = "API 地址"
            layoutParams = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
            ).apply { setMargins(0, 0, 0, 24) }
        }
        baseUrlInput = TextInputEditText(this).apply {
            inputType = android.text.InputType.TYPE_CLASS_TEXT or android.text.InputType.TYPE_TEXT_VARIATION_URI
        }
        urlLayout.addView(baseUrlInput)
        content.addView(urlLayout)

        // --- Model ---
        val modelLayout = TextInputLayout(this).apply {
            hint = "模型名称"
            layoutParams = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
            ).apply { setMargins(0, 0, 0, 32) }
        }
        modelInput = TextInputEditText(this)
        modelLayout.addView(modelInput)
        content.addView(modelLayout)

        // --- Save button ---
        val btnSave = MaterialButton(this).apply {
            text = "保存设置"
            layoutParams = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
            )
            setOnClickListener { saveSettings() }
        }
        content.addView(btnSave)

        // --- Reset button ---
        val btnReset = MaterialButton(this, null, com.google.android.material.R.attr.materialButtonOutlinedStyle).apply {
            text = "恢复默认"
            layoutParams = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
            ).apply { setMargins(0, 16, 0, 0) }
            setOnClickListener { resetToDefault() }
        }
        content.addView(btnReset)

        scrollView.addView(content)
        root.addView(scrollView)
        setContentView(root)
    }

    private fun loadCurrentSettings() {
        val prefs = getSharedPreferences("seatcard_settings", MODE_PRIVATE)
        apiKeyInput.setText(prefs.getString("api_key", defaultApiKey) ?: defaultApiKey)
        baseUrlInput.setText(prefs.getString("base_url", "https://api.minimaxi.com/v1") ?: "https://api.minimaxi.com/v1")
        modelInput.setText(prefs.getString("model", "MiniMax-M2.5") ?: "MiniMax-M2.5")
    }

    private fun saveSettings() {
        val prefs = getSharedPreferences("seatcard_settings", MODE_PRIVATE)
        prefs.edit().apply {
            putString("api_key", apiKeyInput.text?.toString()?.trim() ?: defaultApiKey)
            putString("base_url", baseUrlInput.text?.toString()?.trim() ?: "https://api.minimaxi.com/v1")
            putString("model", modelInput.text?.toString()?.trim() ?: "MiniMax-M2.5")
            apply()
        }
        Toast.makeText(this, "设置已保存", Toast.LENGTH_SHORT).show()
        finish()
    }

    private fun resetToDefault() {
        apiKeyInput.setText(defaultApiKey)
        baseUrlInput.setText("https://api.minimaxi.com/v1")
        modelInput.setText("MiniMax-M2.5")
        saveSettings()
    }
}
