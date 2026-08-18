from pathlib import Path
root = Path('mnemonic-bridge-v0.4')
svc = root/'app/src/main/java/com/bbdc/memo/bridge/BridgeAccessibilityService.java'
main = root/'app/src/main/java/com/bbdc/memo/bridge/MainActivity.java'
manifest = root/'app/src/main/AndroidManifest.xml'
strings = root/'app/src/main/res/values/strings.xml'
gradle = root/'app/build.gradle'

def req(text, old, new, label):
    if old not in text:
        raise SystemExit(f'patch marker missing: {label}')
    return text.replace(old, new, 1)

# Accessibility service: decouple it from launcher task and allow cross-process controls.
s = svc.read_text()
s = req(s, 'import android.content.ClipboardManager;\n', 'import android.content.ClipboardManager;\nimport android.content.BroadcastReceiver;\nimport android.content.Context;\nimport android.content.IntentFilter;\n', 'receiver imports')
s = req(s,
'''    private ClipboardManager clipboardManager;
    private ClipboardManager.OnPrimaryClipChangedListener clipChangedListener;
''',
'''    private ClipboardManager clipboardManager;
    private ClipboardManager.OnPrimaryClipChangedListener clipChangedListener;
    static final String ACTION_REFRESH_BUBBLE = "com.bbdc.memo.bridge.action.REFRESH_BUBBLE";
    static final String ACTION_CANCEL_FLOW = "com.bbdc.memo.bridge.action.CANCEL_FLOW";
    private BroadcastReceiver controlReceiver;
''', 'receiver fields')

s = req(s,
'''        wm = (WindowManager) getSystemService(WINDOW_SERVICE);
        refreshBubblePreference();
        Toast.makeText(this, "助记悬浮桥已启动", Toast.LENGTH_SHORT).show();
''',
'''        controlReceiver = new BroadcastReceiver() {
            @Override public void onReceive(Context context, Intent intent) {
                if (intent == null || intent.getAction() == null) return;
                if (ACTION_REFRESH_BUBBLE.equals(intent.getAction())) {
                    boolean enabled = intent.getBooleanExtra("enabled", Prefs.floatingEnabled(BridgeAccessibilityService.this));
                    if (enabled) showBubble(); else removeBubble();
                } else if (ACTION_CANCEL_FLOW.equals(intent.getAction())) {
                    resetFlow();
                }
            }
        };
        IntentFilter filter = new IntentFilter();
        filter.addAction(ACTION_REFRESH_BUBBLE);
        filter.addAction(ACTION_CANCEL_FLOW);
        if (Build.VERSION.SDK_INT >= 33) registerReceiver(controlReceiver, filter, Context.RECEIVER_NOT_EXPORTED);
        else registerReceiver(controlReceiver, filter);

        wm = (WindowManager) getSystemService(WINDOW_SERVICE);
        refreshBubblePreference();
        Toast.makeText(this, "memory 已启动", Toast.LENGTH_SHORT).show();
''', 'register control receiver')

s = req(s,
'''        clipChangedListener = null;
        clipboardManager = null;
        main.removeCallbacksAndMessages(null);
''',
'''        clipChangedListener = null;
        clipboardManager = null;
        if (controlReceiver != null) {
            try { unregisterReceiver(controlReceiver); } catch (Exception ignored) {}
            controlReceiver = null;
        }
        main.removeCallbacksAndMessages(null);
''', 'unregister control receiver')

marker = '''    @Override public void onInterrupt() {}
'''
insert = '''    @Override
    public void onTaskRemoved(Intent rootIntent) {
        // Removing the launcher task must not be treated as disabling the accessibility service.
        // The service runs in its own process; if the overlay was temporarily missing, restore it.
        main.postDelayed(() -> {
            if (Prefs.floatingEnabled(this) && bubble == null) showBubble();
        }, 250L);
        super.onTaskRemoved(rootIntent);
    }

'''
if marker not in s:
    raise SystemExit('patch marker missing: onTaskRemoved')
s = s.replace(marker, marker + '\n' + insert, 1)
svc.write_text(s)

# Manifest: keep the SAME package/applicationId so the system permission identity stays the same.
# Put accessibility work into its own process so swiping the launcher task is less likely to kill it.
ma = manifest.read_text()
ma = req(ma, '<manifest xmlns:android="http://schemas.android.com/apk/res/android">', '<manifest xmlns:android="http://schemas.android.com/apk/res/android">\n\n    <uses-permission android:name="android.permission.REQUEST_IGNORE_BATTERY_OPTIMIZATIONS" />', 'battery permission')
ma = ma.replace('android:label="助记悬浮桥"', 'android:label="memory"')
ma = req(ma,
'''            android:exported="false"
            android:label="memory"
            android:permission="android.permission.BIND_ACCESSIBILITY_SERVICE">''',
'''            android:exported="false"
            android:label="memory"
            android:process=":memory_accessibility"
            android:stopWithTask="false"
            android:permission="android.permission.BIND_ACCESSIBILITY_SERVICE">''', 'separate accessibility process')
manifest.write_text(ma)

# Main activity: cross-process broadcasts + background stability setting.
m = main.read_text()
m = req(m, 'import android.os.Build;\n', 'import android.os.Build;\nimport android.os.PowerManager;\nimport android.net.Uri;\n', 'battery imports')
m = m.replace('Ui.title(this, "助记悬浮桥", 28)', 'Ui.title(this, "memory", 28)')
m = m.replace('打开无障碍设置并启用“助记悬浮桥”', '打开无障碍设置并启用“memory”')
m = m.replace('进入‘助记悬浮桥’的系统无障碍设置', '进入‘memory’的系统无障碍设置')

m = req(m,
'''        floating.setOnCheckedChangeListener((buttonView, checked) -> {
            Prefs.setFloatingEnabled(this, checked);
            BridgeAccessibilityService service = BridgeAccessibilityService.getInstance();
            if (service != null) service.refreshBubblePreference();
        });
''',
'''        floating.setOnCheckedChangeListener((buttonView, checked) -> {
            Prefs.setFloatingEnabled(this, checked);
            Intent control = new Intent(BridgeAccessibilityService.ACTION_REFRESH_BUBBLE)
                    .setPackage(getPackageName())
                    .putExtra("enabled", checked);
            sendBroadcast(control);
        });
''', 'cross process floating toggle')

m = req(m,
'''        Button cancel = Ui.button(this, "取消当前自动流程");
        cancel.setOnClickListener(v -> {
            BridgeAccessibilityService service = BridgeAccessibilityService.getInstance();
            if (service != null) service.resetFlow();
            else Toast.makeText(this, "辅助服务还没有启动", Toast.LENGTH_SHORT).show();
        });
        root.addView(cancel);
''',
'''        Button background = Ui.button(this, "允许 memory 后台稳定运行");
        background.setOnClickListener(v -> {
            try {
                PowerManager pm = (PowerManager) getSystemService(POWER_SERVICE);
                if (pm != null && pm.isIgnoringBatteryOptimizations(getPackageName())) {
                    Toast.makeText(this, "memory 已允许后台稳定运行", Toast.LENGTH_SHORT).show();
                    return;
                }
                Intent request = new Intent(Settings.ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS,
                        Uri.parse("package:" + getPackageName()));
                startActivity(request);
            } catch (Exception e) {
                try {
                    startActivity(new Intent(Settings.ACTION_IGNORE_BATTERY_OPTIMIZATION_SETTINGS));
                } catch (Exception ignored) {
                    startActivity(new Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS,
                            Uri.parse("package:" + getPackageName())));
                }
            }
        });
        root.addView(background);

        Button cancel = Ui.button(this, "取消当前自动流程");
        cancel.setOnClickListener(v -> {
            Intent control = new Intent(BridgeAccessibilityService.ACTION_CANCEL_FLOW)
                    .setPackage(getPackageName());
            sendBroadcast(control);
            Toast.makeText(this, "已发送取消指令", Toast.LENGTH_SHORT).show();
        });
        root.addView(cancel);
''', 'background button and cross process cancel')

m = m.replace('本工具', 'memory')
m = m.replace('v0.6 已修复贴边状态下偶发点击无响应；按下会先震动确认。', 'v0.7 将无障碍服务放到独立进程；划掉最近任务不会主动关闭服务。贴边状态下按下会先震动确认。')
main.write_text(m)

st = strings.read_text()
st = st.replace('<string name="app_name">助记悬浮桥</string>', '<string name="app_name">memory</string>')
st = st.replace('在你主动点击透明悬浮图标后', 'memory 在你主动点击透明悬浮图标后')
strings.write_text(st)

g = gradle.read_text().replace('versionCode 6', 'versionCode 7').replace("versionName '0.6.0'", "versionName '0.7.0'")
gradle.write_text(g)

print('memory v0.7 background persistence patch applied')
