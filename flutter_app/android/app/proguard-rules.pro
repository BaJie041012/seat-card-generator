# ==============================================================================
# 文件名称: proguard-rules.pro
# 功能描述: ProGuard/R8 混淆与压缩规则，确保 Flutter 插件在代码压缩后正常工作
# 创建日期: 2026-07-03
# 作    者: 戒者有八
# 版    本: 2.0.0
# ==============================================================================

# ---- Flutter 引擎 ----
# 保留 Flutter 引擎核心类，防止反射调用被移除
-keep class io.flutter.app.** { *; }
-keep class io.flutter.plugin.** { *; }
-keep class io.flutter.util.** { *; }
-keep class io.flutter.view.** { *; }
-keep class io.flutter.** { *; }
-keep class io.flutter.embedded.** { *; }

# ---- Google Gson（shared_preferences 等插件依赖）----
-keepattributes Signature
-keepattributes *Annotation*
-keep class com.google.gson.** { *; }
-keep class * implements com.google.gson.TypeAdapterFactory
-keep class * implements com.google.gson.JsonSerializer
-keep class * implements com.google.gson.JsonDeserializer

# ---- share_plus / open_filex / path_provider 等插件 ----
-keep class androidx.** { *; }
-dontwarn androidx.**

# ---- 保留 native 方法 ----
-keepclasseswithmembernames class * {
    native <methods>;
}

# ---- 保留枚举的 values() 和 valueOf() ----
-keepclassmembers enum * {
    public static **[] values();
    public static ** valueOf(java.lang.String);
}

# ---- Flutter 延迟组件引用的 Play Core 类（本项目未使用，仅消除 R8 警告）----
-dontwarn com.google.android.play.core.splitcompat.SplitCompatApplication
-dontwarn com.google.android.play.core.splitinstall.SplitInstallException
-dontwarn com.google.android.play.core.splitinstall.SplitInstallManager
-dontwarn com.google.android.play.core.splitinstall.SplitInstallManagerFactory
-dontwarn com.google.android.play.core.splitinstall.SplitInstallRequest$Builder
-dontwarn com.google.android.play.core.splitinstall.SplitInstallRequest
-dontwarn com.google.android.play.core.splitinstall.SplitInstallSessionState
-dontwarn com.google.android.play.core.splitinstall.SplitInstallStateUpdatedListener
-dontwarn com.google.android.play.core.tasks.OnFailureListener
-dontwarn com.google.android.play.core.tasks.OnSuccessListener
-dontwarn com.google.android.play.core.tasks.Task
