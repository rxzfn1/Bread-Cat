from pathlib import Path

root = Path('mnemonic-bridge-v0.4')
main = root/'app/src/main/java/com/bbdc/memo/bridge/MainActivity.java'
svc = root/'app/src/main/java/com/bbdc/memo/bridge/BridgeAccessibilityService.java'
keep = root/'app/src/main/java/com/bbdc/memo/bridge/KeepAliveService.java'
manifest = root/'app/src/main/AndroidManifest.xml'
gradle = root/'app/build.gradle'

# 1) Keep app visible in Recents again so ColorOS users can lock it there.
ma = manifest.read_text()
ma = ma.replace('''        <activity
            android:name=".MainActivity"
            android:exported="true"
            android:excludeFromRecents="true">''', '''        <activity
            android:name=".MainActivity"
            android:exported="true">''')

# permissions needed by the user-visible keep-alive foreground service and battery allowlist request
if '<uses-permission android:name="android.permission.FOREGROUND_SERVICE" />' not in ma:
    ma = ma.replace('<manifest xmlns:android="http://schemas.android.com/apk/res/android">',
'''<manifest xmlns:android="http://schemas.android.com/apk/res/android">

    <uses-permission android:name="android.permission.FOREGROUND_SERVICE" />
    <uses-permission android:name="android.permission.FOREGROUND_SERVICE_SPECIAL_USE" />
    <uses-permission android:name="android.permission.REQUEST_IGNORE_BATTERY_OPTIMIZATIONS" />''')

service_insert = '''
        <service
            android:name=".KeepAliveService"
            android:exported="false"
            android:stopWithTask="false"
            android:foregroundServiceType="specialUse">
            <property
                android:name="android.app.PROPERTY_SPECIAL_USE_FGS_SUBTYPE"
                android:value="Keeps the user-enabled memory accessibility helper available while the vocabulary overlay is in use" />
        </service>
'''
if '.KeepAliveService' not in ma:
    ma = ma.replace('    </application>', service_insert + '    </application>')
manifest.write_text(ma)

# 2) User-visible foreground keep-alive service. START_STICKY requests restart after ordinary process reclaim.
keep.write_text(r'''package com.bbdc.memo.bridge;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.app.Service;
import android.content.Intent;
import android.os.Build;
import android.os.IBinder;

public class KeepAliveService extends Service {
    private static final String CHANNEL_ID = "memory_keep_alive";
    private static final int NOTIFICATION_ID = 1101;

    @Override
    public void onCreate() {
        super.onCreate();
        createChannel();
        startForeground(NOTIFICATION_ID, buildNotification());
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        return START_STICKY;
    }

    private void createChannel() {
        if (Build.VERSION.SDK_INT < 26) return;
        NotificationManager nm = getSystemService(NotificationManager.class);
        if (nm == null) return;
        NotificationChannel ch = new NotificationChannel(
                CHANNEL_ID,
                "memory 后台运行",
                NotificationManager.IMPORTANCE_LOW);
        ch.setDescription("保持 memory 的悬浮查词辅助功能可用");
        ch.setShowBadge(false);
        nm.createNotificationChannel(ch);
    }

    private Notification buildNotification() {
        Intent open = new Intent(this, MainActivity.class);
        PendingIntent pi = PendingIntent.getActivity(
                this, 0, open,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
        Notification.Builder b = Build.VERSION.SDK_INT >= 26
                ? new Notification.Builder(this, CHANNEL_ID)
                : new Notification.Builder(this);
        return b.setSmallIcon(R.drawable.ic_launcher)
                .setContentTitle("memory 正在运行")
                .setContentText("保持悬浮查词与返回笔记功能可用")
                .setOngoing(true)
                .setCategory(Notification.CATEGORY_SERVICE)
                .setContentIntent(pi)
                .build();
    }

    @Override public IBinder onBind(Intent intent) { return null; }
}
''')

# 3) Start keep-alive from visible Activity, and add direct setup helpers.
m = main.read_text()
if 'import android.content.ComponentName;' not in m:
    m = m.replace('import android.content.Context;\n', 'import android.content.Context;\nimport android.content.ComponentName;\n')
if 'import android.net.Uri;' not in m:
    m = m.replace('import android.os.Bundle;\n', 'import android.os.Bundle;\nimport android.net.Uri;\n')

m = m.replace('''        super.onCreate(savedInstanceState);
        setContentView(buildUi());
''', '''        super.onCreate(savedInstanceState);
        try {
            Intent keep = new Intent(this, KeepAliveService.class);
            if (Build.VERSION.SDK_INT >= 26) startForegroundService(keep); else startService(keep);
        } catch (Exception ignored) {}
        setContentView(buildUi());
''', 1)

old_battery = '''        Button background = Ui.button(this, "打开后台省电设置（建议允许 memory 后台运行）");
        background.setOnClickListener(v -> {
            try {
                startActivity(new Intent(Settings.ACTION_IGNORE_BATTERY_OPTIMIZATION_SETTINGS));
            } catch (Exception e) {
                startActivity(new Intent(Settings.ACTION_SETTINGS));
            }
        });
        root.addView(background);
'''
new_battery = '''        Button background = Ui.button(this, "1. 允许 memory 忽略电池优化");
        background.setOnClickListener(v -> {
            try {
                Intent i = new Intent(Settings.ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS,
                        Uri.parse("package:" + getPackageName()));
                startActivity(i);
            } catch (Exception e) {
                try { startActivity(new Intent(Settings.ACTION_IGNORE_BATTERY_OPTIMIZATION_SETTINGS)); }
                catch (Exception ignored) { startActivity(new Intent(Settings.ACTION_SETTINGS)); }
            }
        });
        root.addView(background);

        Button startup = Ui.button(this, "2. 打开自启动 / 关联启动设置");
        startup.setOnClickListener(v -> openStartupManager());
        root.addView(startup);

        Button appInfo = Ui.button(this, "3. 打开 memory 应用详情（后台运行设为允许）");
        appInfo.setOnClickListener(v -> {
            try {
                startActivity(new Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS,
                        Uri.parse("package:" + getPackageName())));
            } catch (Exception ignored) {}
        });
        root.addView(appInfo);
'''
if old_battery in m:
    m = m.replace(old_battery, new_battery, 1)
else:
    raise SystemExit('battery button marker missing')

# Add ColorOS helper method before refreshStatus.
marker = '    private void refreshStatus() {'
helper = r'''    private void openStartupManager() {
        Intent[] intents = new Intent[] {
                new Intent("com.coloros.safecenter.startupapp.permission.STARTUP_APP_LIST")
                        .setPackage("com.coloros.safecenter"),
                new Intent().setComponent(new ComponentName(
                        "com.oplus.safe", "com.oplus.safe.permission.startup.StartupAppListActivity")),
                new Intent().setComponent(new ComponentName(
                        "com.coloros.safecenter", "com.coloros.safecenter.permission.startup.StartupAppListActivity")),
                new Intent().setComponent(new ComponentName(
                        "com.coloros.safecenter", "com.coloros.safecenter.startupapp.StartupAppListActivity")),
                new Intent().setComponent(new ComponentName(
                        "com.coloros.safecenter", "com.coloros.safecenter.startupapp.AssociateStartActivity"))
        };
        for (Intent intent : intents) {
            try {
                if (getPackageManager().resolveActivity(intent, 0) != null) {
                    startActivity(intent);
                    Toast.makeText(this,
                            "请把 memory 的“自启动”和“关联启动”都设为允许", Toast.LENGTH_LONG).show();
                    return;
                }
            } catch (Exception ignored) {}
        }
        try {
            startActivity(new Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS,
                    Uri.parse("package:" + getPackageName())));
        } catch (Exception ignored) {
            startActivity(new Intent(Settings.ACTION_SETTINGS));
        }
    }

'''
if helper not in m:
    if marker not in m: raise SystemExit('refreshStatus marker missing')
    m = m.replace(marker, helper + marker, 1)

# Replace the v1.0 recents advice with v1.1 ColorOS-specific safe guidance.
m = m.replace('''                "v1.0 起 memory 不再出现在最近任务列表，普通清理最近任务不会主动移除它。"));''',
'''                "v1.1：memory 会保留在最近任务中。若你的手机是 OPPO / 一加 / 真我 / ColorOS，建议在最近任务里长按 memory 卡片并“锁定”，同时在系统设置中允许“自启动”和“关联启动”。不要用系统的“强行停止”。"));''')
main.write_text(m)

# 4) Best-effort restart of keep-alive whenever accessibility is connected.
s = svc.read_text()
needle = '    @Override protected void onServiceConnected() {\n'
if needle in s and 'KeepAliveService.class' not in s:
    s = s.replace(needle, needle + '''        try {\n            Intent keep = new Intent(this, KeepAliveService.class);\n            if (android.os.Build.VERSION.SDK_INT >= 26) startForegroundService(keep); else startService(keep);\n        } catch (Exception ignored) {}\n''', 1)
svc.write_text(s)

# version
g = gradle.read_text().replace('versionCode 10', 'versionCode 11').replace("versionName '1.0.0'", "versionName '1.1.0'")
gradle.write_text(g)

print('memory v1.1 ColorOS keep-alive patch applied')
