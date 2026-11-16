package com.videodetector

import android.annotation.SuppressLint
import android.graphics.Color
import android.net.Uri
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.view.Gravity
import android.view.View
import android.webkit.WebResourceRequest
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.Button
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.TextView
import android.widget.Toast
import android.app.Activity

class MainActivity : Activity() {
    private val foundLinks = linkedSetOf<String>()
    private lateinit var addressInput: EditText
    private lateinit var resultsBox: EditText
    private lateinit var statusLabel: TextView
    private lateinit var webView: WebView
    private var captureActive = false
    private var webVisible = true
    private lateinit var webToggleButton: Button
    private val uiHandler = Handler(Looper.getMainLooper())
    private var captureTimeout: Runnable? = null
    private var countdownTask: Runnable? = null
    private var captureDeadline = 0L

    @SuppressLint("SetJavaScriptEnabled")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        window.statusBarColor = Color.rgb(16, 42, 67)
        window.navigationBarColor = Color.rgb(16, 42, 67)

        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(16), dp(12), dp(16), dp(8))
            setBackgroundColor(Color.rgb(246, 248, 251))
        }

        val title = TextView(this).apply {
            text = "VideoDetector"
            textSize = 22f
            setTextColor(Color.rgb(16, 42, 67))
            setTypeface(null, android.graphics.Typeface.BOLD)
            gravity = Gravity.CENTER_VERTICAL
        }
        root.addView(title, LinearLayout.LayoutParams(-1, dp(38)))

        val urlRow = LinearLayout(this).apply { orientation = LinearLayout.HORIZONTAL }
        addressInput = EditText(this).apply {
            hint = "অনুমতিপ্রাপ্ত ওয়েবসাইটের URL দিন"
            textSize = 14f
            setSingleLine(true)
            setPadding(dp(10), 0, dp(10), 0)
            setBackgroundColor(Color.WHITE)
            inputType = android.text.InputType.TYPE_CLASS_TEXT or
                android.text.InputType.TYPE_TEXT_VARIATION_URI
        }
        urlRow.addView(addressInput, LinearLayout.LayoutParams(0, dp(48), 1f))
        val startButton = Button(this).apply {
            text = "Start"
            isAllCaps = false
            setOnClickListener { startCapture() }
        }
        urlRow.addView(startButton, LinearLayout.LayoutParams(dp(92), dp(48)).apply {
            leftMargin = dp(8)
        })
        root.addView(urlRow, LinearLayout.LayoutParams(-1, dp(52)))

        statusLabel = TextView(this).apply {
            text = "অনুমতিপ্রাপ্ত কনটেন্টে ব্যবহার করুন। URL ও Referer header সংগ্রহ করা হয় না।"
            textSize = 12f
            setTextColor(Color.rgb(71, 85, 105))
            gravity = Gravity.CENTER_VERTICAL
        }
        root.addView(statusLabel, LinearLayout.LayoutParams(-1, dp(38)))

        webToggleButton = Button(this).apply {
            text = "ওয়েবভিউ লুকান"
            isAllCaps = false
            setOnClickListener { toggleWebView() }
        }
        root.addView(webToggleButton, LinearLayout.LayoutParams(-1, dp(44)))

        webView = WebView(this).apply {
            setBackgroundColor(Color.WHITE)
            settings.javaScriptEnabled = true
            settings.domStorageEnabled = true
            settings.mediaPlaybackRequiresUserGesture = true
            webViewClient = object : WebViewClient() {
                override fun shouldOverrideUrlLoading(view: WebView?, request: WebResourceRequest?): Boolean {
                    val target = request?.url ?: return false
                    val currentHost = runCatching { Uri.parse(view?.url).host }.getOrNull()
                    val targetHost = target.host
                    // Stop external navigation (common for ad popups/redirects) but keep the current site usable.
                    return target.scheme !in listOf("http", "https") ||
                        (currentHost != null && targetHost != null && !targetHost.equals(currentHost, ignoreCase = true))
                }

                override fun onPageStarted(view: WebView?, url: String?, favicon: android.graphics.Bitmap?) {
                    super.onPageStarted(view, url, favicon)
                    if (captureActive) statusLabel.text = "পেজ লোড হচ্ছে…"
                }

                override fun onPageFinished(view: WebView?, url: String?) {
                    super.onPageFinished(view, url)
                    if (captureActive) startFortySecondWindow()
                }
            }
        }
        root.addView(webView, LinearLayout.LayoutParams(-1, 0, 1f).apply {
            topMargin = dp(4)
            bottomMargin = dp(6)
        })

        val outputHeader = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
        }
        val outputTitle = TextView(this).apply {
            text = "পাওয়া ভিডিও/স্ট্রিম URL"
            textSize = 14f
            setTypeface(null, android.graphics.Typeface.BOLD)
            setTextColor(Color.rgb(16, 42, 67))
        }
        outputHeader.addView(outputTitle, LinearLayout.LayoutParams(0, dp(36), 1f))
        val copyButton = Button(this).apply {
            text = "Copy"
            isAllCaps = false
            setOnClickListener { copyResults() }
        }
        outputHeader.addView(copyButton, LinearLayout.LayoutParams(dp(88), dp(40)))
        root.addView(outputHeader, LinearLayout.LayoutParams(-1, dp(40)))

        resultsBox = EditText(this).apply {
            hint = "ক্যাপচার হওয়া URL এখানে দেখা যাবে"
            textSize = 12f
            setTextColor(Color.rgb(30, 41, 59))
            setPadding(dp(10), dp(8), dp(10), dp(8))
            gravity = Gravity.TOP or Gravity.START
            inputType = android.text.InputType.TYPE_CLASS_TEXT or
                android.text.InputType.TYPE_TEXT_FLAG_MULTI_LINE
            setBackgroundColor(Color.WHITE)
            setSingleLine(false)
            minLines = 4
            maxLines = 6
        }
        root.addView(resultsBox, LinearLayout.LayoutParams(-1, dp(112)))
        setContentView(root)
    }

    private fun startCapture() {
        val entered = addressInput.text.toString().trim()
        if (entered.isEmpty()) {
            addressInput.error = "একটি URL দিন"
            return
        }
        val normalized = if (entered.startsWith("http://") || entered.startsWith("https://")) {
            entered
        } else {
            "https://$entered"
        }
        val uri = runCatching { Uri.parse(normalized) }.getOrNull()
        if (uri == null || uri.scheme !in setOf("http", "https") || uri.host.isNullOrBlank()) {
            addressInput.error = "সঠিক http/https URL দিন"
            return
        }
        stopCaptureWindow()
        foundLinks.clear()
        resultsBox.setText("")
        captureActive = true
        if (isVideoResource(normalized)) {
            addCapturedUrl(normalized)
            statusLabel.text = "সরাসরি ভিডিও URL যোগ হয়েছে।"
            startFortySecondWindow()
        } else {
            statusLabel.text = "পেজ খুলছি। লোড শেষ হলে ৪০ সেকেন্ডের সেশন শুরু হবে।"
            webView.loadUrl(normalized)
        }
    }

    private fun startFortySecondWindow() {
        if (!captureActive) return
        stopCaptureWindow()
        captureDeadline = android.os.SystemClock.elapsedRealtime() + 40_000L
        val countdown = object : Runnable {
            override fun run() {
                if (!captureActive) return
                val seconds = ((captureDeadline - android.os.SystemClock.elapsedRealtime() + 999) / 1000).coerceAtLeast(0)
                if (seconds == 0L) {
                    finishCaptureWindow()
                } else {
                    statusLabel.text = "৪০ সেকেন্ডের সেশন · বাকি ${seconds} সেকেন্ড · সরাসরি ভিডিও URL ফলাফলে পেস্ট করুন"
                    uiHandler.postDelayed(this, 1000L)
                }
            }
        }
        countdownTask = countdown
        uiHandler.post(countdown)
        captureTimeout = Runnable { finishCaptureWindow() }.also { uiHandler.postDelayed(it, 40_000L) }
    }

    private fun finishCaptureWindow() {
        if (!captureActive) return
        captureActive = false
        stopCaptureWindow()
        statusLabel.text = if (foundLinks.isEmpty())
            "৪০ সেকেন্ড শেষ। পেজের ভেতরের stream request স্বয়ংক্রিয়ভাবে পড়া হয় না।"
        else "৪০ সেকেন্ড শেষ · ${foundLinks.size}টি সরাসরি URL"
    }

    private fun stopCaptureWindow() {
        captureTimeout?.let(uiHandler::removeCallbacks)
        countdownTask?.let(uiHandler::removeCallbacks)
        captureTimeout = null
        countdownTask = null
    }

    private fun toggleWebView() {
        webVisible = !webVisible
        webView.visibility = if (webVisible) View.VISIBLE else View.GONE
        webToggleButton.text = if (webVisible) "ওয়েবভিউ লুকান" else "ওয়েবভিউ দেখান"
    }

    private fun isVideoResource(rawUrl: String): Boolean {
        val uri = runCatching { Uri.parse(rawUrl) }.getOrNull() ?: return false
        if (uri.scheme !in setOf("http", "https")) return false
        val path = uri.path.orEmpty().lowercase()
        return listOf(".m3u8", ".mpd", ".mp4", ".m4v", ".webm", ".mov", ".3gp")
            .any { path.endsWith(it) }
    }

    private fun addCapturedUrl(url: String) {
        if (foundLinks.add(url)) {
            val display = foundLinks.joinToString("\n\n")
            resultsBox.setText(display)
            statusLabel.text = "সরাসরি ভিডিও URL যোগ হয়েছে · মোট ${foundLinks.size}"
        }
    }

    private fun copyResults() {
        val text = resultsBox.text.toString().trim()
        if (text.isEmpty()) {
            Toast.makeText(this, "কপি করার মতো লিংক নেই", Toast.LENGTH_SHORT).show()
            return
        }
        val clipboard = getSystemService(CLIPBOARD_SERVICE) as android.content.ClipboardManager
        clipboard.setPrimaryClip(android.content.ClipData.newPlainText("VideoDetector URLs", text))
        Toast.makeText(this, "লিংক কপি হয়েছে", Toast.LENGTH_SHORT).show()
    }

    private fun dp(value: Int): Int = (value * resources.displayMetrics.density).toInt()

    @Deprecated("Deprecated in Android")
    override fun onBackPressed() {
        if (::webView.isInitialized && webView.canGoBack()) webView.goBack() else super.onBackPressed()
    }

    override fun onDestroy() {
        stopCaptureWindow()
        uiHandler.removeCallbacksAndMessages(null)
        if (::webView.isInitialized) webView.destroy()
        super.onDestroy()
    }
}
