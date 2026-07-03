package com.bajie.seatcard

import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.view.View
import android.widget.LinearLayout
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.FileProvider
import com.google.android.material.appbar.MaterialToolbar
import com.google.android.material.button.MaterialButton
import java.io.File

class ResultActivity : AppCompatActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setupUI()
    }

    private fun setupUI() {
        val pdfPaths = intent.getStringArrayListExtra("pdf_paths") ?: arrayListOf()
        val personNames = intent.getStringArrayListExtra("person_names") ?: arrayListOf()
        val failedNames = intent.getStringArrayListExtra("failed_names") ?: arrayListOf()

        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            fitsSystemWindows = true
        }

        // Toolbar
        val toolbar = MaterialToolbar(this).apply {
            title = "生成结果"
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

        // Summary
        val summaryText = TextView(this).apply {
            text = buildString {
                append("成功生成 ${pdfPaths.size} 张席卡")
                if (failedNames.isNotEmpty()) {
                    append("\n失败: ${failedNames.joinToString("、")}")
                }
            }
            textSize = 15f
            setPadding(0, 0, 0, 24)
        }
        content.addView(summaryText)

        // Each PDF card
        for (i in pdfPaths.indices) {
            val pdfPath = pdfPaths[i]
            val name = if (i < personNames.size) personNames[i] else "席卡 ${i + 1}"
            val pdfFile = File(pdfPath)

            val cardView = LinearLayout(this).apply {
                orientation = LinearLayout.HORIZONTAL
                setPadding(16, 16, 16, 16)
                layoutParams = LinearLayout.LayoutParams(
                    LinearLayout.LayoutParams.MATCH_PARENT,
                    LinearLayout.LayoutParams.WRAP_CONTENT
                ).apply { setMargins(0, 0, 0, 8) }
                background = resources.getDrawable(com.google.android.material.R.drawable.material_cursor_drawable)
            }

            // Name label
            val nameView = TextView(this).apply {
                text = name
                textSize = 16f
                layoutParams = LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1f)
            }
            cardView.addView(nameView)

            // File size
            if (pdfFile.exists()) {
                val sizeView = TextView(this).apply {
                    val sizeKb = pdfFile.length() / 1024.0
                    text = "%.0f KB".format(sizeKb)
                    textSize = 12f
                    setTextColor(resources.getColor(com.google.android.material.R.color.material_on_surface_emphasis_medium, theme))
                    setPadding(0, 0, 16, 0)
                }
                cardView.addView(sizeView)
            }

            // Open button
            val btnOpen = MaterialButton(this).apply {
                text = "打开"
                textSize = 12f
                minWidth = 0
                setOnClickListener { openPdf(pdfFile) }
            }
            cardView.addView(btnOpen)

            // Share button
            val btnShare = MaterialButton(this, null, com.google.android.material.R.attr.materialButtonOutlinedStyle).apply {
                text = "分享"
                textSize = 12f
                minWidth = 0
                setOnClickListener { sharePdf(pdfFile) }
            }
            cardView.addView(btnShare)

            content.addView(cardView)
        }

        // Back button
        val btnBack = MaterialButton(this).apply {
            text = "返回"
            layoutParams = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
            ).apply { setMargins(0, 24, 0, 0) }
            setOnClickListener { finish() }
        }
        content.addView(btnBack)

        scrollView.addView(content)
        root.addView(scrollView)
        setContentView(root)
    }

    private fun openPdf(file: File) {
        if (!file.exists()) return
        val uri = FileProvider.getUriForFile(this, "${packageName}.fileprovider", file)
        val intent = Intent(Intent.ACTION_VIEW).apply {
            setDataAndType(uri, "application/pdf")
            addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
        }
        startActivity(Intent.createChooser(intent, "打开 PDF"))
    }

    private fun sharePdf(file: File) {
        if (!file.exists()) return
        val uri = FileProvider.getUriForFile(this, "${packageName}.fileprovider", file)
        val intent = Intent(Intent.ACTION_SEND).apply {
            type = "application/pdf"
            putExtra(Intent.EXTRA_STREAM, uri)
            putExtra(Intent.EXTRA_SUBJECT, file.name)
        }
        startActivity(Intent.createChooser(intent, "分享席卡 PDF"))
    }
}
