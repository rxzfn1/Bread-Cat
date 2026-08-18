package com.bbdc.memo.bridge;

import android.accessibilityservice.AccessibilityServiceInfo;
import android.app.Activity;
import android.content.Context;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.os.Build;
import android.os.Bundle;
import android.provider.Settings;
import android.view.ViewGroup;
import android.view.accessibility.AccessibilityManager;
import android.widget.Button;
import android.widget.CheckBox;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;

import java.util.List;

public class MainActivity extends Activity {
    private TextView status;
    private CheckBox floating;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(buildUi());
    }

    @Override
    protected void onResume() {
        super.onResume();
        refreshStatus();
        floating.setChecked(Prefs.floatingEnabled(this));
    }

    private ScrollView buildUi() {
        ScrollView scroll = new ScrollView(this);
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        int p = Ui.dp(this, 20);
        root.setPadding(p, p, p, p);
        scroll.addView(root, new ViewGroup.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));

        root.addView(Ui.title(this, "助记悬浮桥", 28));
        root.addView(Ui.body(this,
                "不背单词 → 自动识词 → 墨墨搜索 → 你选择助记并复制 → 自动返回 → 安全粘贴到笔记。"));

        status = Ui.body(this, "");
        root.addView(status);

        Button accessibility = Ui.button(this, "1. 打开无障碍设置并启用“助记悬浮桥”");
        accessibility.setOnClickListener(v -> startActivity(new Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS)));
        root.addView(accessibility);

        floating = new CheckBox(this);
        floating.setText("2. 显示透明悬浮图标（空闲自动贴边）");
        floating.setChecked(Prefs.floatingEnabled(this));
        floating.setOnCheckedChangeListener((buttonView, checked) -> {
            Prefs.setFloatingEnabled(this, checked);
            BridgeAccessibilityService service = BridgeAccessibilityService.getInstance();
            if (service != null) service.refreshBubblePreference();
        });
        root.addView(floating);

        Button cancel = Ui.button(this, "取消当前自动流程");
        cancel.setOnClickListener(v -> {
            BridgeAccessibilityService service = BridgeAccessibilityService.getInstance();
            if (service != null) service.resetFlow();
            else Toast.makeText(this, "辅助服务还没有启动", Toast.LENGTH_SHORT).show();
        });
        root.addView(cancel);

        root.addView(Ui.title(this, "怎么用", 18));
        root.addView(Ui.body(this,
                "① 在不背单词打开当前学习单词。\n" +
                "② 点击屏幕侧边的透明图标。\n" +
                "③ 工具读取当前单词并打开墨墨，尝试自动搜索。\n" +
                "④ 你在墨墨选择需要的助记，然后点击墨墨里的“复制”。\n" +
                "⑤ 工具检测到复制后返回不背单词，打开笔记并执行系统粘贴。\n\n" +
                "图标可拖动；不操作约 1.2 秒后自动吸附到最近的屏幕侧边，只露出三分之一。长按图标可取消本次流程。"));

        root.addView(Ui.title(this, "说明", 18));
        root.addView(Ui.body(this,
                "本工具不读取墨墨账号数据，也不读取剪贴板内容。自动化依赖 Android 无障碍节点；如果两款 App 后续大改界面，搜索按钮或笔记入口可能需要再次适配。"));

        return scroll;
    }

    private void refreshStatus() {
        boolean enabled = isOurAccessibilityEnabled();
        boolean bbdc = installed(BridgeAccessibilityService.BBDC_PACKAGE);
        boolean momo = installed(BridgeAccessibilityService.MAIMEMO_PACKAGE);
        status.setText("状态：辅助服务 " + (enabled ? "✓" : "✗")
                + "    不背单词 " + (bbdc ? "✓" : "✗")
                + "    墨墨 " + (momo ? "✓" : "✗"));
    }

    private boolean installed(String pkg) {
        try {
            if (Build.VERSION.SDK_INT >= 33) {
                getPackageManager().getPackageInfo(pkg, PackageManager.PackageInfoFlags.of(0));
            } else {
                //noinspection deprecation
                getPackageManager().getPackageInfo(pkg, 0);
            }
            return true;
        } catch (Exception e) {
            return false;
        }
    }

    private boolean isOurAccessibilityEnabled() {
        AccessibilityManager am = (AccessibilityManager) getSystemService(Context.ACCESSIBILITY_SERVICE);
        List<AccessibilityServiceInfo> services = am.getEnabledAccessibilityServiceList(
                AccessibilityServiceInfo.FEEDBACK_ALL_MASK);
        String packageName = getPackageName();
        for (AccessibilityServiceInfo info : services) {
            String id = info.getId();
            if (id != null && id.contains(packageName)) return true;
        }
        return false;
    }
}
