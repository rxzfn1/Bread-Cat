from pathlib import Path

root = Path('memory-v2')
app = root / 'app'
java = app / 'src/main/java/com/memory/bridge'
res_values = app / 'src/main/res/values'
res_drawable = app / 'src/main/res/drawable'
for p in [java, res_values, res_drawable]:
    p.mkdir(parents=True, exist_ok=True)

(root / 'settings.gradle').write_text(r'''pluginManagement {
    repositories {
        google()
        mavenCentral()
        gradlePluginPortal()
    }
}
dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
    }
}
rootProject.name = 'memory-v2'
include ':app'
''', encoding='utf-8')

(root / 'build.gradle').write_text(r'''plugins {
    id 'com.android.application' version '8.7.2' apply false
}
''', encoding='utf-8')

(app / 'build.gradle').write_text(r'''plugins {
    id 'com.android.application'
}

android {
    namespace 'com.memory.bridge'
    compileSdk 35

    defaultConfig {
        applicationId 'com.memory.bridge'
        minSdk 26
        targetSdk 35
        versionCode 20
        versionName '2.0.0'
    }

    buildTypes {
        release {
            minifyEnabled false
            proguardFiles getDefaultProguardFile('proguard-android-optimize.txt'), 'proguard-rules.pro'
        }
    }

    compileOptions {
        sourceCompatibility JavaVersion.VERSION_17
        targetCompatibility JavaVersion.VERSION_17
    }
}

dependencies {
    implementation 'com.google.mlkit:text-recognition:16.0.1'
}
''', encoding='utf-8')

(app / 'proguard-rules.pro').write_text('', encoding='utf-8')

(app / 'src/main/AndroidManifest.xml').write_text(r'''<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android">

    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.SYSTEM_ALERT_WINDOW" />
    <uses-permission android:name="android.permission.FOREGROUND_SERVICE" />
    <uses-permission android:name="android.permission.FOREGROUND_SERVICE_MEDIA_PROJECTION" />
    <uses-permission android:name="android.permission.POST_NOTIFICATIONS" />

    <queries>
        <package android:name="cn.com.langeasy.LangEasyLexis" />
        <package android:name="com.maimemo.android.momo" />
    </queries>

    <application
        android:allowBackup="false"
        android:usesCleartextTraffic="false"
        android:label="memory"
        android:icon="@drawable/ic_overlay_bridge"
        android:theme="@style/AppTheme">

        <activity
            android:name=".MainActivity"
            android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>

        <service
            android:name=".CaptureOverlayService"
            android:exported="false"
            android:stopWithTask="false"
            android:foregroundServiceType="mediaProjection" />
    </application>
</manifest>
''', encoding='utf-8')

(res_values / 'styles.xml').write_text(r'''<?xml version="1.0" encoding="utf-8"?>
<resources>
    <style name="AppTheme" parent="android:style/Theme.Material.Light.NoActionBar">
        <item name="android:fontFamily">sans</item>
        <item name="android:colorAccent">#111114</item>
        <item name="android:navigationBarColor">#FAFAFB</item>
        <item name="android:statusBarColor">#FAFAFB</item>
        <item name="android:windowLightStatusBar">true</item>
    </style>
</resources>
''', encoding='utf-8')

(java / 'MainActivity.java').write_text(r'''package com.memory.bridge;

import android.Manifest;
import android.app.Activity;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.graphics.Color;
import android.graphics.drawable.GradientDrawable;
import android.media.projection.MediaProjectionManager;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.provider.Settings;
import android.text.InputType;
import android.view.Gravity;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;

public class MainActivity extends Activity {
    private static final int REQ_OVERLAY = 1001;
    private static final int REQ_CAPTURE = 1002;
    private static final int REQ_NOTIFY = 1003;
    private boolean pendingStart = false;
    private EditText tokenInput;
    private TextView overlayStatus;
    private TextView serviceStatus;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(buildUi());
        if (Build.VERSION.SDK_INT >= 33 && checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) {
            requestPermissions(new String[]{Manifest.permission.POST_NOTIFICATIONS}, REQ_NOTIFY);
        }
    }

    @Override
    protected void onResume() {
        super.onResume();
        refreshStatus();
        if (pendingStart && Settings.canDrawOverlays(this)) {
            pendingStart = false;
            getWindow().getDecorView().postDelayed(this::requestScreenCapture, 350);
        }
    }

    private View buildUi() {
        ScrollView scroll = new ScrollView(this);
        scroll.setFillViewport(true);
        scroll.setBackgroundColor(Color.rgb(250, 250, 251));

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(dp(22), dp(26), dp(22), dp(34));
        scroll.addView(root, new ScrollView.LayoutParams(-1, -2));

        TextView badge = text("memory 2.0 · 无障碍版", 13, Color.rgb(105, 105, 112));
        root.addView(badge);

        TextView title = text("memory", 34, Color.rgb(20, 20, 23));
        title.setTypeface(null, 1);
        LinearLayout.LayoutParams tp = new LinearLayout.LayoutParams(-1, -2);
        tp.topMargin = dp(6);
        root.addView(title, tp);

        TextView intro = text("不再使用无障碍权限。点悬浮图标后，memory 只截取当前屏幕的一帧，在本机 OCR 识别不背单词页面上方的大号英文词。", 15, Color.rgb(84, 84, 91));
        intro.setLineSpacing(0, 1.28f);
        LinearLayout.LayoutParams ip = new LinearLayout.LayoutParams(-1, -2);
        ip.topMargin = dp(10);
        ip.bottomMargin = dp(20);
        root.addView(intro, ip);

        LinearLayout card = card();
        overlayStatus = text("悬浮窗权限：检查中", 15, Color.rgb(38, 38, 42));
        serviceStatus = text("识词服务：未启动", 15, Color.rgb(38, 38, 42));
        card.addView(overlayStatus, rowLp());
        card.addView(serviceStatus, rowLp());
        root.addView(card);

        Button overlay = button("1. 授予悬浮窗权限");
        overlay.setOnClickListener(v -> requestOverlayPermission());
        root.addView(overlay, buttonLp());

        TextView apiTitle = text("2. 墨墨官方 Open API Token（推荐）", 17, Color.rgb(25, 25, 29));
        apiTitle.setTypeface(null, 1);
        LinearLayout.LayoutParams ap = new LinearLayout.LayoutParams(-1, -2);
        ap.topMargin = dp(24);
        root.addView(apiTitle, ap);

        TextView apiHelp = text("在墨墨背单词：我的 → 更多设置 → 实验功能 → 开放 API，复制 Token 后粘贴到下面。Token 只保存在本机，memory 查询时直接连接 open.maimemo.com。", 14, Color.rgb(97, 97, 104));
        apiHelp.setLineSpacing(0, 1.3f);
        LinearLayout.LayoutParams ah = new LinearLayout.LayoutParams(-1, -2);
        ah.topMargin = dp(8);
        root.addView(apiHelp, ah);

        tokenInput = new EditText(this);
        tokenInput.setSingleLine(false);
        tokenInput.setMinLines(2);
        tokenInput.setMaxLines(4);
        tokenInput.setTextSize(14);
        tokenInput.setHint("粘贴墨墨 Open API Token；不填也可以使用打开墨墨的兜底模式");
        tokenInput.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_VARIATION_PASSWORD | InputType.TYPE_TEXT_FLAG_MULTI_LINE);
        tokenInput.setPadding(dp(14), dp(12), dp(14), dp(12));
        tokenInput.setBackground(round(Color.WHITE, 14, Color.rgb(225,225,229)));
        tokenInput.setText(getPreferencesStore().getString("maimemo_token", ""));
        LinearLayout.LayoutParams ep = new LinearLayout.LayoutParams(-1, -2);
        ep.topMargin = dp(10);
        root.addView(tokenInput, ep);

        Button save = button("保存 Token");
        save.setOnClickListener(v -> {
            getPreferencesStore().edit().putString("maimemo_token", tokenInput.getText().toString().trim()).apply();
            Toast.makeText(this, "Token 已保存到本机", Toast.LENGTH_SHORT).show();
        });
        root.addView(save, buttonLp());

        Button openMaimemo = secondaryButton("打开墨墨获取 Token");
        openMaimemo.setOnClickListener(v -> {
            launchPackage("com.maimemo.android.momo");
            Toast.makeText(this, "进入：我的 → 更多设置 → 实验功能 → 开放 API", Toast.LENGTH_LONG).show();
        });
        root.addView(openMaimemo, smallButtonLp());

        Button start = button("3. 启动悬浮识词");
        start.setOnClickListener(v -> startFlow());
        LinearLayout.LayoutParams sp = buttonLp();
        sp.topMargin = dp(24);
        root.addView(start, sp);

        Button stop = secondaryButton("停止 memory 悬浮识词");
        stop.setOnClickListener(v -> {
            Intent i = new Intent(this, CaptureOverlayService.class).setAction(CaptureOverlayService.ACTION_STOP);
            startService(i);
            getWindow().getDecorView().postDelayed(this::refreshStatus, 400);
        });
        root.addView(stop, smallButtonLp());

        TextView guide = text(
                "使用方式\n\n" +
                "A. 已填写墨墨 Token：\n" +
                "在不背单词页面点悬浮图标 → OCR 识别大号单词 → memory 直接从墨墨官方 API 读取助记 → 在悬浮面板选择一条并复制 → 你打开不背单词笔记后粘贴。\n\n" +
                "B. 没有填写 Token：\n" +
                "点悬浮图标 → OCR 识词并复制单词 → 自动打开墨墨 → 你搜索/复制助记 → 再点一次悬浮图标 → 自动回到不背单词。\n\n" +
                "屏幕捕获只用于你点击悬浮图标时的 OCR，不保存截图。Android 要求每次重新启动屏幕捕获会话时由你确认一次，但不再需要任何无障碍高敏感授权。",
                14, Color.rgb(83, 83, 90));
        guide.setLineSpacing(0, 1.35f);
        LinearLayout.LayoutParams gp = new LinearLayout.LayoutParams(-1, -2);
        gp.topMargin = dp(28);
        root.addView(guide, gp);

        return scroll;
    }

    private void startFlow() {
        getPreferencesStore().edit().putString("maimemo_token", tokenInput.getText().toString().trim()).apply();
        if (!Settings.canDrawOverlays(this)) {
            pendingStart = true;
            requestOverlayPermission();
            return;
        }
        requestScreenCapture();
    }

    private void requestOverlayPermission() {
        try {
            Intent i = new Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION, Uri.parse("package:" + getPackageName()));
            startActivityForResult(i, REQ_OVERLAY);
        } catch (Exception e) {
            startActivity(new Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION));
        }
    }

    private void requestScreenCapture() {
        MediaProjectionManager mpm = (MediaProjectionManager) getSystemService(MEDIA_PROJECTION_SERVICE);
        if (mpm == null) {
            Toast.makeText(this, "系统不支持屏幕捕获", Toast.LENGTH_LONG).show();
            return;
        }
        startActivityForResult(mpm.createScreenCaptureIntent(), REQ_CAPTURE);
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode == REQ_CAPTURE) {
            if (resultCode != RESULT_OK || data == null) {
                Toast.makeText(this, "没有获得屏幕捕获授权，悬浮识词未启动", Toast.LENGTH_LONG).show();
                return;
            }
            Intent svc = new Intent(this, CaptureOverlayService.class)
                    .setAction(CaptureOverlayService.ACTION_START)
                    .putExtra(CaptureOverlayService.EXTRA_RESULT_CODE, resultCode)
                    .putExtra(CaptureOverlayService.EXTRA_RESULT_DATA, data);
            if (Build.VERSION.SDK_INT >= 26) startForegroundService(svc); else startService(svc);
            Toast.makeText(this, "memory 已启动。现在可以回到不背单词使用悬浮图标", Toast.LENGTH_LONG).show();
            getWindow().getDecorView().postDelayed(this::refreshStatus, 600);
        }
    }

    private SharedPreferences getPreferencesStore() {
        return getSharedPreferences("memory_v2", MODE_PRIVATE);
    }

    private void refreshStatus() {
        if (overlayStatus != null) {
            overlayStatus.setText(Settings.canDrawOverlays(this) ? "悬浮窗权限：已允许" : "悬浮窗权限：未允许");
        }
        if (serviceStatus != null) {
            boolean active = getPreferencesStore().getBoolean("projection_active", false);
            serviceStatus.setText(active ? "识词服务：运行中" : "识词服务：未启动");
        }
    }

    private void launchPackage(String pkg) {
        Intent i = getPackageManager().getLaunchIntentForPackage(pkg);
        if (i == null) {
            Toast.makeText(this, "没有找到对应 App", Toast.LENGTH_LONG).show();
            return;
        }
        i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_REORDER_TO_FRONT);
        startActivity(i);
    }

    private LinearLayout card() {
        LinearLayout v = new LinearLayout(this);
        v.setOrientation(LinearLayout.VERTICAL);
        v.setPadding(dp(16), dp(10), dp(16), dp(10));
        v.setBackground(round(Color.WHITE, 16, Color.rgb(232,232,235)));
        return v;
    }

    private LinearLayout.LayoutParams rowLp() {
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(-1, -2);
        lp.topMargin = dp(6);
        lp.bottomMargin = dp(6);
        return lp;
    }

    private Button button(String s) {
        Button b = new Button(this);
        b.setText(s);
        b.setTextSize(15);
        b.setTextColor(Color.WHITE);
        b.setAllCaps(false);
        b.setBackground(round(Color.rgb(24,24,27), 14, Color.TRANSPARENT));
        return b;
    }

    private Button secondaryButton(String s) {
        Button b = new Button(this);
        b.setText(s);
        b.setTextSize(14);
        b.setTextColor(Color.rgb(35,35,39));
        b.setAllCaps(false);
        b.setBackground(round(Color.WHITE, 14, Color.rgb(225,225,229)));
        return b;
    }

    private LinearLayout.LayoutParams buttonLp() {
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(-1, dp(52));
        lp.topMargin = dp(14);
        return lp;
    }

    private LinearLayout.LayoutParams smallButtonLp() {
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(-1, dp(48));
        lp.topMargin = dp(8);
        return lp;
    }

    private TextView text(String s, int sp, int color) {
        TextView t = new TextView(this);
        t.setText(s);
        t.setTextSize(sp);
        t.setTextColor(color);
        return t;
    }

    static GradientDrawable round(int fill, int radiusDp, int stroke) {
        GradientDrawable g = new GradientDrawable();
        g.setColor(fill);
        g.setCornerRadius(radiusDp * 3f);
        if (stroke != Color.TRANSPARENT) g.setStroke(1, stroke);
        return g;
    }

    private int dp(int v) {
        return (int) (v * getResources().getDisplayMetrics().density + 0.5f);
    }
}
''', encoding='utf-8')

(java / 'CaptureOverlayService.java').write_text(r'''package com.memory.bridge;

import android.app.*;
import android.content.*;
import android.content.pm.ServiceInfo;
import android.graphics.*;
import android.graphics.drawable.GradientDrawable;
import android.hardware.display.DisplayManager;
import android.hardware.display.VirtualDisplay;
import android.media.Image;
import android.media.ImageReader;
import android.media.projection.MediaProjection;
import android.media.projection.MediaProjectionManager;
import android.os.*;
import android.provider.Settings;
import android.view.*;
import android.widget.*;

import com.google.mlkit.vision.common.InputImage;
import com.google.mlkit.vision.text.Text;
import com.google.mlkit.vision.text.TextRecognition;
import com.google.mlkit.vision.text.TextRecognizer;
import com.google.mlkit.vision.text.latin.TextRecognizerOptions;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.*;
import java.net.*;
import java.nio.ByteBuffer;
import java.util.*;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.regex.Pattern;

public class CaptureOverlayService extends Service {
    public static final String ACTION_START = "com.memory.bridge.START";
    public static final String ACTION_STOP = "com.memory.bridge.STOP";
    public static final String EXTRA_RESULT_CODE = "resultCode";
    public static final String EXTRA_RESULT_DATA = "resultData";

    private static final int NOTIFICATION_ID = 42;
    private static final String CHANNEL_ID = "memory_capture";
    private static final String BBDC_PACKAGE = "cn.com.langeasy.LangEasyLexis";
    private static final String MAIMEMO_PACKAGE = "com.maimemo.android.momo";
    private static final Pattern WORD = Pattern.compile("^[A-Za-z][A-Za-z'’-]{1,34}$");

    private final Handler main = new Handler(Looper.getMainLooper());
    private HandlerThread workerThread;
    private Handler worker;
    private WindowManager wm;
    private ImageView bubble;
    private View panel;
    private WindowManager.LayoutParams bubbleLp;
    private MediaProjection projection;
    private VirtualDisplay virtualDisplay;
    private ImageReader imageReader;
    private TextRecognizer recognizer;
    private int screenW, screenH, densityDpi;
    private final AtomicBoolean capturePending = new AtomicBoolean(false);
    private final AtomicBoolean ocrBusy = new AtomicBoolean(false);
    private boolean fallbackAwaitReturn = false;
    private Runnable dockRunnable;

    @Override
    public void onCreate() {
        super.onCreate();
        workerThread = new HandlerThread("memory-v2-worker");
        workerThread.start();
        worker = new Handler(workerThread.getLooper());
        wm = (WindowManager) getSystemService(WINDOW_SERVICE);
        recognizer = TextRecognition.getClient(TextRecognizerOptions.DEFAULT_OPTIONS);
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        if (intent != null && ACTION_STOP.equals(intent.getAction())) {
            stopSelf();
            return START_NOT_STICKY;
        }
        if (intent == null || !ACTION_START.equals(intent.getAction())) return START_NOT_STICKY;

        ensureNotificationChannel();
        Notification n = buildNotification();
        if (Build.VERSION.SDK_INT >= 29) {
            startForeground(NOTIFICATION_ID, n, ServiceInfo.FOREGROUND_SERVICE_TYPE_MEDIA_PROJECTION);
        } else {
            startForeground(NOTIFICATION_ID, n);
        }

        int resultCode = intent.getIntExtra(EXTRA_RESULT_CODE, Activity.RESULT_CANCELED);
        Intent resultData = intent.getParcelableExtra(EXTRA_RESULT_DATA);
        if (resultCode != Activity.RESULT_OK || resultData == null) {
            toast("屏幕捕获授权无效，请重新打开 memory 启动");
            stopSelf();
            return START_NOT_STICKY;
        }

        try {
            startProjection(resultCode, resultData);
            showBubble();
            prefs().edit().putBoolean("projection_active", true).apply();
        } catch (Exception e) {
            toast("启动失败：" + e.getClass().getSimpleName());
            stopSelf();
        }
        return START_NOT_STICKY;
    }

    private void startProjection(int resultCode, Intent resultData) {
        cleanupProjection();
        android.util.DisplayMetrics dm = new android.util.DisplayMetrics();
        wm.getDefaultDisplay().getRealMetrics(dm);
        screenW = dm.widthPixels;
        screenH = dm.heightPixels;
        densityDpi = dm.densityDpi;

        MediaProjectionManager mpm = (MediaProjectionManager) getSystemService(MEDIA_PROJECTION_SERVICE);
        projection = mpm.getMediaProjection(resultCode, resultData);
        projection.registerCallback(new MediaProjection.Callback() {
            @Override public void onStop() {
                toast("屏幕捕获会话已结束；需要时重新打开 memory 启动即可");
                stopSelf();
            }
        }, main);

        imageReader = ImageReader.newInstance(screenW, screenH, PixelFormat.RGBA_8888, 2);
        imageReader.setOnImageAvailableListener(this::onImageAvailable, worker);
        virtualDisplay = projection.createVirtualDisplay(
                "memory-v2-capture",
                screenW, screenH, densityDpi,
                DisplayManager.VIRTUAL_DISPLAY_FLAG_AUTO_MIRROR,
                imageReader.getSurface(), null, worker);
    }

    private void onImageAvailable(ImageReader reader) {
        Image image = null;
        try {
            image = reader.acquireLatestImage();
            if (image == null) return;
            if (!capturePending.compareAndSet(true, false)) return;
            Bitmap bitmap = imageToBitmap(image);
            main.post(() -> { if (bubble != null) bubble.setAlpha(1f); });
            if (bitmap != null) runOcr(bitmap);
            else {
                ocrBusy.set(false);
                toast("截图读取失败，请再点一次");
            }
        } catch (Exception e) {
            capturePending.set(false);
            ocrBusy.set(false);
            toast("截图失败，请再点一次");
        } finally {
            if (image != null) image.close();
        }
    }

    private Bitmap imageToBitmap(Image image) {
        Image.Plane[] planes = image.getPlanes();
        if (planes.length == 0) return null;
        ByteBuffer buffer = planes[0].getBuffer();
        int pixelStride = planes[0].getPixelStride();
        int rowStride = planes[0].getRowStride();
        int rowPadding = rowStride - pixelStride * screenW;
        int bitmapW = screenW + rowPadding / Math.max(1, pixelStride);
        Bitmap padded = Bitmap.createBitmap(bitmapW, screenH, Bitmap.Config.ARGB_8888);
        padded.copyPixelsFromBuffer(buffer);
        Bitmap cropped = Bitmap.createBitmap(padded, 0, 0, screenW, screenH);
        if (padded != cropped) padded.recycle();
        return cropped;
    }

    private void runOcr(Bitmap bitmap) {
        InputImage input = InputImage.fromBitmap(bitmap, 0);
        recognizer.process(input)
                .addOnSuccessListener(text -> {
                    String word = chooseMainWord(text, bitmap.getWidth(), bitmap.getHeight());
                    bitmap.recycle();
                    ocrBusy.set(false);
                    if (word.isEmpty()) {
                        showMessagePanel("没有识别到目标单词",
                                "memory 没找到页面上方的大号英文单词。请确保当前停留在不背单词的单词学习页，再点一次悬浮图标。",
                                null);
                        return;
                    }
                    toast("识别到：" + word);
                    String token = prefs().getString("maimemo_token", "").trim();
                    if (token.isEmpty()) {
                        openMaimemoFallback(word, "未设置墨墨 API Token");
                    } else {
                        fetchMaimemoNotes(word, token);
                    }
                })
                .addOnFailureListener(e -> {
                    bitmap.recycle();
                    ocrBusy.set(false);
                    showMessagePanel("OCR 识别失败", "请再点一次悬浮图标。", null);
                });
    }

    private String chooseMainWord(Text text, int w, int h) {
        List<OcrCandidate> candidates = new ArrayList<>();
        for (Text.TextBlock block : text.getTextBlocks()) {
            for (Text.Line line : block.getLines()) {
                for (Text.Element el : line.getElements()) {
                    Rect b = el.getBoundingBox();
                    if (b == null) continue;
                    String cleaned = cleanWord(el.getText());
                    if (cleaned.isEmpty()) continue;
                    float cy = b.exactCenterY() / Math.max(1f, h);
                    float cx = b.exactCenterX() / Math.max(1f, w);
                    float hr = b.height() / Math.max(1f, h);
                    float wr = b.width() / Math.max(1f, w);
                    candidates.add(new OcrCandidate(cleaned, b, cy, cx, hr, wr));
                }
            }
        }
        OcrCandidate best = choosePass(candidates, true);
        if (best == null) best = choosePass(candidates, false);
        return best == null ? "" : best.word;
    }

    private OcrCandidate choosePass(List<OcrCandidate> list, boolean strictTop) {
        OcrCandidate best = null;
        for (OcrCandidate c : list) {
            if (strictTop) {
                if (c.cy < .065f || c.cy > .245f) continue;
            } else {
                if (c.cy < .055f || c.cy > .39f) continue;
            }
            if (c.cx < .04f || c.cx > .88f) continue;
            if (c.wr > .70f || c.hr > .12f) continue;

            float targetY = strictTop ? .145f : .19f;
            float yScore = 1f - Math.min(1f, Math.abs(c.cy - targetY) / .24f);
            float heightScore = Math.min(2.0f, c.hr / .028f);
            float compact = 1f - Math.min(1f, c.wr / .70f);
            c.score = heightScore * 8.5f + yScore * 4.0f + compact * 1.3f;
            if (best == null || c.score > best.score) best = c;
        }
        return best;
    }

    private String cleanWord(String raw) {
        if (raw == null) return "";
        String s = raw.trim()
                .replaceFirst("^[^A-Za-z]+", "")
                .replaceFirst("[^A-Za-z]+$", "")
                .trim();
        return WORD.matcher(s).matches() ? s : "";
    }

    private void fetchMaimemoNotes(String word, String token) {
        worker.post(() -> {
            try {
                String vocUrl = "https://open.maimemo.com/open/api/v1/vocabulary?spelling=" + URLEncoder.encode(word, "UTF-8");
                JSONObject v = getJson(vocUrl, token);
                if (!v.optBoolean("success", false)) throw new IOException(apiError(v));
                JSONObject data = v.optJSONObject("data");
                JSONObject voc = data == null ? null : data.optJSONObject("voc");
                String vocId = voc == null ? "" : voc.optString("id", "");
                if (vocId.isEmpty()) throw new IOException("墨墨没有找到这个单词");

                String notesUrl = "https://open.maimemo.com/open/api/v1/notes?voc_id=" + URLEncoder.encode(vocId, "UTF-8");
                JSONObject n = getJson(notesUrl, token);
                if (!n.optBoolean("success", false)) throw new IOException(apiError(n));
                JSONObject nd = n.optJSONObject("data");
                JSONArray arr = nd == null ? null : nd.optJSONArray("notes");
                List<MemoNote> notes = new ArrayList<>();
                if (arr != null) {
                    for (int i = 0; i < arr.length(); i++) {
                        JSONObject item = arr.optJSONObject(i);
                        if (item == null) continue;
                        if ("DELETED".equalsIgnoreCase(item.optString("status"))) continue;
                        String note = item.optString("note", "").trim();
                        if (note.isEmpty()) continue;
                        notes.add(new MemoNote(item.optString("note_type", "助记"), note));
                        if (notes.size() >= 24) break;
                    }
                }
                main.post(() -> showNotesPanel(word, notes));
            } catch (Exception e) {
                String msg = e.getMessage() == null ? "网络或 Token 异常" : e.getMessage();
                main.post(() -> showApiError(word, msg));
            }
        });
    }

    private JSONObject getJson(String url, String token) throws Exception {
        HttpURLConnection c = (HttpURLConnection) new URL(url).openConnection();
        c.setRequestMethod("GET");
        c.setConnectTimeout(9000);
        c.setReadTimeout(12000);
        c.setRequestProperty("Accept", "application/json");
        c.setRequestProperty("Authorization", "Bearer " + token);
        int code = c.getResponseCode();
        InputStream in = code >= 200 && code < 300 ? c.getInputStream() : c.getErrorStream();
        String body = readAll(in);
        c.disconnect();
        if (code == 401 || code == 403) throw new IOException("墨墨 Token 无效或已失效");
        if (code < 200 || code >= 300) throw new IOException("墨墨 API 返回 HTTP " + code);
        return new JSONObject(body);
    }

    private String apiError(JSONObject o) {
        JSONArray errors = o.optJSONArray("errors");
        if (errors != null && errors.length() > 0) {
            JSONObject e = errors.optJSONObject(0);
            if (e != null) {
                String s = e.optString("msg", e.optString("info", ""));
                if (!s.isEmpty()) return s;
            }
        }
        return "墨墨 API 请求失败";
    }

    private String readAll(InputStream in) throws IOException {
        if (in == null) return "";
        BufferedReader r = new BufferedReader(new InputStreamReader(in));
        StringBuilder b = new StringBuilder();
        String line;
        while ((line = r.readLine()) != null) b.append(line);
        return b.toString();
    }

    private void showNotesPanel(String word, List<MemoNote> notes) {
        hidePanel();
        LinearLayout outer = new LinearLayout(this);
        outer.setOrientation(LinearLayout.VERTICAL);
        outer.setPadding(dp(18), dp(16), dp(18), dp(14));
        outer.setBackground(round(Color.rgb(252,252,253), 22, Color.rgb(224,224,228)));

        LinearLayout header = new LinearLayout(this);
        header.setOrientation(LinearLayout.HORIZONTAL);
        header.setGravity(Gravity.CENTER_VERTICAL);
        TextView title = text(word, 27, Color.rgb(22,22,25));
        title.setTypeface(null, 1);
        header.addView(title, new LinearLayout.LayoutParams(0, -2, 1f));
        TextView close = text("×", 30, Color.rgb(92,92,99));
        close.setGravity(Gravity.CENTER);
        close.setOnClickListener(v -> hidePanel());
        header.addView(close, new LinearLayout.LayoutParams(dp(44), dp(44)));
        outer.addView(header);

        TextView source = text("墨墨官方开放 API · " + notes.size() + " 条助记", 12, Color.rgb(121,121,128));
        LinearLayout.LayoutParams slp = new LinearLayout.LayoutParams(-1, -2);
        slp.bottomMargin = dp(10);
        outer.addView(source, slp);

        ScrollView scroll = new ScrollView(this);
        LinearLayout list = new LinearLayout(this);
        list.setOrientation(LinearLayout.VERTICAL);
        scroll.addView(list, new ScrollView.LayoutParams(-1, -2));

        if (notes.isEmpty()) {
            TextView empty = text("墨墨 API 没有返回可用助记。你也可以打开墨墨 App 手动查看。", 15, Color.rgb(74,74,80));
            empty.setPadding(0, dp(18), 0, dp(18));
            list.addView(empty);
        } else {
            int index = 1;
            for (MemoNote n : notes) {
                LinearLayout card = new LinearLayout(this);
                card.setOrientation(LinearLayout.VERTICAL);
                card.setPadding(dp(14), dp(12), dp(14), dp(12));
                card.setBackground(round(Color.WHITE, 14, Color.rgb(232,232,236)));

                TextView type = text(index + " · " + n.type, 12, Color.rgb(126,126,133));
                card.addView(type);
                TextView body = text(n.text, 15, Color.rgb(35,35,39));
                body.setLineSpacing(0, 1.25f);
                LinearLayout.LayoutParams blp = new LinearLayout.LayoutParams(-1, -2);
                blp.topMargin = dp(7);
                card.addView(body, blp);

                Button copy = smallDarkButton("复制这条助记");
                copy.setOnClickListener(v -> {
                    copyText(n.text);
                    hidePanel();
                    toast("助记已复制。现在点不背单词的笔记入口，再粘贴即可");
                });
                LinearLayout.LayoutParams clp = new LinearLayout.LayoutParams(-1, dp(42));
                clp.topMargin = dp(10);
                card.addView(copy, clp);

                LinearLayout.LayoutParams cp = new LinearLayout.LayoutParams(-1, -2);
                cp.bottomMargin = dp(10);
                list.addView(card, cp);
                index++;
            }
        }

        LinearLayout.LayoutParams scrollLp = new LinearLayout.LayoutParams(-1, 0, 1f);
        outer.addView(scroll, scrollLp);

        Button open = secondaryButton("复制单词并打开墨墨");
        open.setOnClickListener(v -> {
            hidePanel();
            openMaimemoFallback(word, "手动查看墨墨");
        });
        LinearLayout.LayoutParams olp = new LinearLayout.LayoutParams(-1, dp(44));
        olp.topMargin = dp(8);
        outer.addView(open, olp);

        showPanelView(outer);
    }

    private void showApiError(String word, String error) {
        LinearLayout actions = new LinearLayout(this);
        actions.setOrientation(LinearLayout.VERTICAL);
        Button open = smallDarkButton("复制单词并打开墨墨");
        open.setOnClickListener(v -> {
            hidePanel();
            openMaimemoFallback(word, error);
        });
        actions.addView(open, new LinearLayout.LayoutParams(-1, dp(44)));
        Button settings = secondaryButton("打开 memory 更新 Token");
        settings.setOnClickListener(v -> {
            hidePanel();
            Intent i = new Intent(this, MainActivity.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            startActivity(i);
        });
        LinearLayout.LayoutParams sp = new LinearLayout.LayoutParams(-1, dp(44));
        sp.topMargin = dp(8);
        actions.addView(settings, sp);
        showMessagePanel("墨墨 API 暂时不可用", error, actions);
    }

    private void showMessagePanel(String title, String message, View extra) {
        hidePanel();
        LinearLayout outer = new LinearLayout(this);
        outer.setOrientation(LinearLayout.VERTICAL);
        outer.setPadding(dp(18), dp(16), dp(18), dp(16));
        outer.setBackground(round(Color.rgb(252,252,253), 20, Color.rgb(224,224,228)));
        TextView t = text(title, 21, Color.rgb(24,24,27));
        t.setTypeface(null, 1);
        outer.addView(t);
        TextView m = text(message, 15, Color.rgb(74,74,80));
        m.setLineSpacing(0, 1.3f);
        LinearLayout.LayoutParams mp = new LinearLayout.LayoutParams(-1, -2);
        mp.topMargin = dp(10);
        mp.bottomMargin = dp(14);
        outer.addView(m, mp);
        if (extra != null) outer.addView(extra);
        Button close = secondaryButton("关闭");
        close.setOnClickListener(v -> hidePanel());
        LinearLayout.LayoutParams cp = new LinearLayout.LayoutParams(-1, dp(44));
        cp.topMargin = dp(10);
        outer.addView(close, cp);
        showPanelView(outer);
    }

    private void showPanelView(View v) {
        panel = v;
        WindowManager.LayoutParams lp = new WindowManager.LayoutParams(
                Math.min(screenW - dp(24), dp(520)),
                Math.min((int)(screenH * .70f), dp(650)),
                WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY,
                WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE |
                        WindowManager.LayoutParams.FLAG_NOT_TOUCH_MODAL |
                        WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN,
                PixelFormat.TRANSLUCENT);
        lp.gravity = Gravity.CENTER;
        try { wm.addView(panel, lp); } catch (Exception ignored) { panel = null; }
    }

    private void hidePanel() {
        if (panel != null) {
            try { wm.removeView(panel); } catch (Exception ignored) {}
            panel = null;
        }
    }

    private void openMaimemoFallback(String word, String reason) {
        copyText(word);
        fallbackAwaitReturn = true;
        Intent i = getPackageManager().getLaunchIntentForPackage(MAIMEMO_PACKAGE);
        if (i == null) {
            fallbackAwaitReturn = false;
            showMessagePanel("没有找到墨墨背单词", "单词 “" + word + "” 已经复制到剪贴板。", null);
            return;
        }
        i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_REORDER_TO_FRONT);
        try {
            startActivity(i);
            toast("已复制 “" + word + "”。在墨墨查好并复制助记后，再点 memory 悬浮图标返回不背单词");
        } catch (Exception e) {
            fallbackAwaitReturn = false;
        }
    }

    private void returnToBbdc() {
        Intent i = getPackageManager().getLaunchIntentForPackage(BBDC_PACKAGE);
        fallbackAwaitReturn = false;
        if (i == null) {
            toast("没有找到不背单词 App");
            return;
        }
        i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_REORDER_TO_FRONT);
        try {
            startActivity(i);
            toast("已回到不背单词。请打开这个单词的笔记，再粘贴刚才复制的助记");
        } catch (Exception e) {
            toast("返回不背单词失败");
        }
    }

    private void showBubble() {
        if (!Settings.canDrawOverlays(this) || wm == null || bubble != null) return;
        final int size = dp(56);
        final int reveal = Math.max(dp(18), size / 3);
        final int hidden = size - reveal;

        bubble = new ImageView(this);
        bubble.setImageResource(com.memory.bridge.R.drawable.ic_overlay_bridge);
        bubble.setScaleType(ImageView.ScaleType.FIT_CENTER);
        bubble.setBackgroundColor(Color.TRANSPARENT);
        bubble.setContentDescription("memory 悬浮识词");

        bubbleLp = new WindowManager.LayoutParams(
                size, size,
                WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY,
                WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE |
                        WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS |
                        WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN,
                PixelFormat.TRANSLUCENT);
        bubbleLp.gravity = Gravity.TOP | Gravity.START;
        SharedPreferences p = prefs();
        int savedY = p.getInt("bubble_y", (int)(screenH * .33f));
        String side = p.getString("bubble_side", "right");
        bubbleLp.x = "left".equals(side) ? -hidden : screenW - reveal;
        bubbleLp.y = clamp(savedY, 0, Math.max(0, screenH - size));

        final float[] down = new float[4];
        final long[] downAt = new long[1];
        final boolean[] moved = new boolean[1];
        final String[] currentSide = new String[]{side};

        bubble.setOnTouchListener((v, e) -> {
            if (e.getAction() == MotionEvent.ACTION_DOWN) {
                cancelDock();
                down[0] = e.getRawX();
                down[1] = e.getRawY();
                down[2] = bubbleLp.x;
                down[3] = bubbleLp.y;
                downAt[0] = SystemClock.elapsedRealtime();
                moved[0] = false;
                v.animate().scaleX(.96f).scaleY(.96f).setDuration(70).start();
                return true;
            }
            if (e.getAction() == MotionEvent.ACTION_MOVE) {
                float dx = e.getRawX() - down[0];
                float dy = e.getRawY() - down[1];
                if (!moved[0] && (Math.abs(dx) > dp(6) || Math.abs(dy) > dp(6))) {
                    moved[0] = true;
                    if (bubbleLp.x < 0) bubbleLp.x = 0;
                    if (bubbleLp.x > screenW - size) bubbleLp.x = screenW - size;
                    down[2] = bubbleLp.x;
                    down[0] = e.getRawX();
                    down[3] = bubbleLp.y;
                    down[1] = e.getRawY();
                    dx = dy = 0;
                }
                if (moved[0]) {
                    bubbleLp.x = clamp((int)(down[2] + dx), 0, Math.max(0, screenW - size));
                    bubbleLp.y = clamp((int)(down[3] + dy), 0, Math.max(0, screenH - size));
                    try { wm.updateViewLayout(v, bubbleLp); } catch (Exception ignored) {}
                }
                return true;
            }
            if (e.getAction() == MotionEvent.ACTION_UP || e.getAction() == MotionEvent.ACTION_CANCEL) {
                v.animate().scaleX(1f).scaleY(1f).setDuration(90).start();
                long held = SystemClock.elapsedRealtime() - downAt[0];
                if (moved[0]) {
                    currentSide[0] = (bubbleLp.x + size / 2 < screenW / 2) ? "left" : "right";
                    prefs().edit().putInt("bubble_y", bubbleLp.y).putString("bubble_side", currentSide[0]).apply();
                } else if (held >= 650) {
                    fallbackAwaitReturn = false;
                    toast("memory 当前流程已重置");
                } else if (e.getAction() == MotionEvent.ACTION_UP) {
                    revealBubble(currentSide[0], size);
                    handleBubbleTap();
                }
                scheduleDock(currentSide[0], size, reveal, hidden);
                return true;
            }
            return false;
        });

        try {
            wm.addView(bubble, bubbleLp);
            scheduleDock(side, size, reveal, hidden);
        } catch (Exception e) {
            bubble = null;
        }
    }

    private void handleBubbleTap() {
        if (fallbackAwaitReturn) {
            returnToBbdc();
            return;
        }
        if (ocrBusy.get() || capturePending.get()) {
            toast("memory 正在识别，请稍等");
            return;
        }
        hidePanel();
        if (imageReader == null || projection == null) {
            toast("屏幕捕获会话已失效，请重新打开 memory 启动");
            return;
        }
        ocrBusy.set(true);
        if (bubble != null) bubble.setAlpha(0f);
        main.postDelayed(() -> {
            capturePending.set(true);
            main.postDelayed(() -> {
                if (capturePending.compareAndSet(true, false)) {
                    ocrBusy.set(false);
                    if (bubble != null) bubble.setAlpha(1f);
                    toast("没有拿到新截图，请再点一次");
                }
            }, 1800);
        }, 120);
    }

    private void revealBubble(String side, int size) {
        if (bubble == null) return;
        bubbleLp.x = "left".equals(side) ? 0 : screenW - size;
        try { wm.updateViewLayout(bubble, bubbleLp); } catch (Exception ignored) {}
    }

    private void scheduleDock(String side, int size, int reveal, int hidden) {
        cancelDock();
        dockRunnable = () -> {
            if (bubble == null) return;
            bubbleLp.x = "left".equals(side) ? -hidden : screenW - reveal;
            try { wm.updateViewLayout(bubble, bubbleLp); } catch (Exception ignored) {}
        };
        main.postDelayed(dockRunnable, 1400);
    }

    private void cancelDock() {
        if (dockRunnable != null) main.removeCallbacks(dockRunnable);
        dockRunnable = null;
    }

    private SharedPreferences prefs() {
        return getSharedPreferences("memory_v2", MODE_PRIVATE);
    }

    private void copyText(String text) {
        ClipboardManager cm = (ClipboardManager) getSystemService(CLIPBOARD_SERVICE);
        if (cm != null) cm.setPrimaryClip(ClipData.newPlainText("memory", text));
    }

    private void ensureNotificationChannel() {
        if (Build.VERSION.SDK_INT >= 26) {
            NotificationManager nm = (NotificationManager) getSystemService(NOTIFICATION_SERVICE);
            NotificationChannel ch = new NotificationChannel(CHANNEL_ID, "memory 屏幕识词", NotificationManager.IMPORTANCE_LOW);
            ch.setDescription("保持一次屏幕捕获会话，用于你点击悬浮图标时做本地 OCR");
            nm.createNotificationChannel(ch);
        }
    }

    private Notification buildNotification() {
        Intent open = new Intent(this, MainActivity.class);
        PendingIntent pi = PendingIntent.getActivity(this, 0, open, PendingIntent.FLAG_IMMUTABLE | PendingIntent.FLAG_UPDATE_CURRENT);
        Notification.Builder b = Build.VERSION.SDK_INT >= 26 ? new Notification.Builder(this, CHANNEL_ID) : new Notification.Builder(this);
        return b.setContentTitle("memory 正在运行")
                .setContentText("仅在你点击悬浮图标时识别当前屏幕，不保存截图")
                .setSmallIcon(android.R.drawable.ic_menu_view)
                .setOngoing(true)
                .setContentIntent(pi)
                .build();
    }

    private void cleanupProjection() {
        if (virtualDisplay != null) { try { virtualDisplay.release(); } catch (Exception ignored) {} virtualDisplay = null; }
        if (imageReader != null) { try { imageReader.close(); } catch (Exception ignored) {} imageReader = null; }
        if (projection != null) { try { projection.stop(); } catch (Exception ignored) {} projection = null; }
    }

    @Override
    public void onDestroy() {
        prefs().edit().putBoolean("projection_active", false).apply();
        cancelDock();
        hidePanel();
        if (bubble != null) {
            try { wm.removeView(bubble); } catch (Exception ignored) {}
            bubble = null;
        }
        cleanupProjection();
        if (recognizer != null) try { recognizer.close(); } catch (Exception ignored) {}
        if (workerThread != null) workerThread.quitSafely();
        super.onDestroy();
    }

    @Override public IBinder onBind(Intent intent) { return null; }

    private void toast(String s) { main.post(() -> Toast.makeText(this, s, Toast.LENGTH_LONG).show()); }

    private TextView text(String s, int sp, int color) {
        TextView t = new TextView(this);
        t.setText(s);
        t.setTextSize(sp);
        t.setTextColor(color);
        return t;
    }

    private Button smallDarkButton(String s) {
        Button b = new Button(this);
        b.setText(s);
        b.setTextSize(13);
        b.setTextColor(Color.WHITE);
        b.setAllCaps(false);
        b.setBackground(round(Color.rgb(25,25,28), 12, Color.TRANSPARENT));
        return b;
    }

    private Button secondaryButton(String s) {
        Button b = new Button(this);
        b.setText(s);
        b.setTextSize(13);
        b.setTextColor(Color.rgb(42,42,47));
        b.setAllCaps(false);
        b.setBackground(round(Color.WHITE, 12, Color.rgb(224,224,228)));
        return b;
    }

    private GradientDrawable round(int fill, int radiusDp, int stroke) {
        GradientDrawable g = new GradientDrawable();
        g.setColor(fill);
        g.setCornerRadius(dp(radiusDp));
        if (stroke != Color.TRANSPARENT) g.setStroke(dp(1), stroke);
        return g;
    }

    private int dp(int v) { return (int)(v * getResources().getDisplayMetrics().density + .5f); }
    private int clamp(int v, int min, int max) { return Math.max(min, Math.min(max, v)); }

    private static final class OcrCandidate {
        final String word; final Rect bounds; final float cy, cx, hr, wr; float score;
        OcrCandidate(String word, Rect bounds, float cy, float cx, float hr, float wr) {
            this.word = word; this.bounds = bounds; this.cy = cy; this.cx = cx; this.hr = hr; this.wr = wr;
        }
    }

    private static final class MemoNote {
        final String type, text;
        MemoNote(String type, String text) { this.type = type; this.text = text; }
    }
}
''', encoding='utf-8')

print('memory-v2 project generated')
