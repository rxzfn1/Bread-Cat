from pathlib import Path
root = Path('mnemonic-bridge-v0.4')
svc = root/'app/src/main/java/com/bbdc/memo/bridge/BridgeAccessibilityService.java'
main = root/'app/src/main/java/com/bbdc/memo/bridge/MainActivity.java'
xml = root/'app/src/main/res/xml/accessibility_service_config.xml'
strings = root/'app/src/main/res/values/strings.xml'
gradle = root/'app/build.gradle'

def req(text, old, new, label):
    if old not in text:
        raise SystemExit(f'patch marker missing: {label}')
    return text.replace(old, new, 1)

s=svc.read_text()
s=req(s,'import android.content.Intent;\n','import android.content.Intent;\nimport android.content.ClipboardManager;\n','clipboard import')
s=req(s,'    private boolean driveScheduled = false;\n    private Runnable dockRunnable;\n','    private boolean driveScheduled = false;\n    private Runnable dockRunnable;\n    private ClipboardManager clipboardManager;\n    private ClipboardManager.OnPrimaryClipChangedListener clipChangedListener;\n','clipboard fields')
s=req(s,'                | AccessibilityEvent.TYPE_VIEW_CLICKED\n                | AccessibilityEvent.TYPE_VIEW_FOCUSED','                | AccessibilityEvent.TYPE_VIEW_CLICKED\n                | AccessibilityEvent.TYPE_VIEW_LONG_CLICKED\n                | AccessibilityEvent.TYPE_VIEW_FOCUSED','long click event')
s=req(s,'        info.flags |= AccessibilityServiceInfo.FLAG_REPORT_VIEW_IDS\n                | AccessibilityServiceInfo.FLAG_RETRIEVE_INTERACTIVE_WINDOWS;\n        info.notificationTimeout = 100;\n        setServiceInfo(info);\n        wm = (WindowManager) getSystemService(WINDOW_SERVICE);','        info.flags |= AccessibilityServiceInfo.FLAG_REPORT_VIEW_IDS\n                | AccessibilityServiceInfo.FLAG_RETRIEVE_INTERACTIVE_WINDOWS;\n        info.flags &= ~AccessibilityServiceInfo.FLAG_REQUEST_ACCESSIBILITY_BUTTON;\n        info.packageNames = new String[]{BBDC_PACKAGE, MAIMEMO_PACKAGE};\n        info.notificationTimeout = 100;\n        setServiceInfo(info);\n\n        clipboardManager = (ClipboardManager) getSystemService(CLIPBOARD_SERVICE);\n        if (clipboardManager != null) {\n            clipChangedListener = () -> {\n                if (stage != Stage.WAITING_COPY) return;\n                main.postDelayed(this::beginReturnToBbdc, 120);\n            };\n            clipboardManager.addPrimaryClipChangedListener(clipChangedListener);\n        }\n        wm = (WindowManager) getSystemService(WINDOW_SERVICE);','service setup')
s=req(s,'        if (MAIMEMO_PACKAGE.equals(currentPackage)) {\n            if (stage == Stage.OPENING_MAIMEMO || stage == Stage.SEARCHING_MAIMEMO) {\n                scheduleDriveMaimemo(180);\n            } else if (stage == Stage.WAITING_COPY) {\n                if (event.getEventType() == AccessibilityEvent.TYPE_VIEW_CLICKED && looksLikeCopyAction(event.getSource())) {\n                    beginReturnToBbdc();\n                } else if (looksLikeCopyConfirmation(event)) {\n                    beginReturnToBbdc();\n                }\n            }\n        } else if (BBDC_PACKAGE.equals(currentPackage) && stage == Stage.RETURNING_BBDC) {','        if (stage == Stage.WAITING_COPY) {\n            int type = event.getEventType();\n            if (type == AccessibilityEvent.TYPE_VIEW_CLICKED || type == AccessibilityEvent.TYPE_VIEW_LONG_CLICKED) {\n                AccessibilityNodeInfo src = event.getSource();\n                boolean copy = looksLikeCopyAction(src);\n                if (src != null) src.recycle();\n                if (copy) { beginReturnToBbdc(); return; }\n            }\n            if (looksLikeCopyConfirmation(event)) { beginReturnToBbdc(); return; }\n        }\n\n        if (MAIMEMO_PACKAGE.equals(currentPackage)) {\n            if (stage == Stage.OPENING_MAIMEMO || stage == Stage.SEARCHING_MAIMEMO) {\n                scheduleDriveMaimemo(180);\n            }\n        } else if (BBDC_PACKAGE.equals(currentPackage) && stage == Stage.RETURNING_BBDC) {','copy routing')
s=req(s,'    public void onDestroy() {\n        removeBubble();\n        main.removeCallbacksAndMessages(null);','    public void onDestroy() {\n        removeBubble();\n        if (clipboardManager != null && clipChangedListener != null) {\n            try { clipboardManager.removePrimaryClipChangedListener(clipChangedListener); } catch (Exception ignored) {}\n        }\n        clipChangedListener = null;\n        clipboardManager = null;\n        main.removeCallbacksAndMessages(null);','destroy listener')
s=req(s,'    private void setStage(Stage next) {\n        stage = next;\n        stageStartedAt = next == Stage.IDLE ? 0L : SystemClock.elapsedRealtime();\n    }','    private void setStage(Stage next) {\n        Stage previous = stage;\n        stage = next;\n        stageStartedAt = next == Stage.IDLE ? 0L : SystemClock.elapsedRealtime();\n        if (previous != Stage.WAITING_COPY && next == Stage.WAITING_COPY) setCopyObservationMode(true);\n        else if (previous == Stage.WAITING_COPY && next != Stage.WAITING_COPY) setCopyObservationMode(false);\n    }\n\n    private void setCopyObservationMode(boolean broaden) {\n        try {\n            AccessibilityServiceInfo info = getServiceInfo();\n            if (info == null) return;\n            info.packageNames = broaden ? null : new String[]{BBDC_PACKAGE, MAIMEMO_PACKAGE};\n            info.flags &= ~AccessibilityServiceInfo.FLAG_REQUEST_ACCESSIBILITY_BUTTON;\n            setServiceInfo(info);\n        } catch (Exception ignored) {}\n    }','dynamic copy observation')
svc.write_text(s)

x=xml.read_text().replace('typeViewClicked|typeViewFocused','typeViewClicked|typeViewLongClicked|typeViewFocused')
xml.write_text(x)

g=gradle.read_text().replace('versionCode 4','versionCode 5').replace("versionName '0.4.0'","versionName '0.5.0'")
gradle.write_text(g)

st=strings.read_text().replace('检测你点击“复制”后返回不背单词并对笔记框执行粘贴。','检测你执行复制（包括长按文字后使用系统复制）后返回不背单词并对笔记框执行粘贴。')
strings.write_text(st)

m=main.read_text()
m=req(m,'        Button cancel = Ui.button(this, "取消当前自动流程");','        Button shortcutSettings = Ui.button(this, "关闭系统额外的无障碍快捷悬浮按钮");\n        shortcutSettings.setOnClickListener(v -> {\n            Toast.makeText(this, "进入‘助记悬浮桥’的系统无障碍设置，只保留服务开启，把‘快捷方式/悬浮按钮’关闭", Toast.LENGTH_LONG).show();\n            startActivity(new Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS));\n        });\n        root.addView(shortcutSettings);\n\n        Button cancel = Ui.button(this, "取消当前自动流程");','shortcut button')
m=m.replace('④ 你在墨墨选择需要的助记，然后点击墨墨里的“复制”。','④ 你在墨墨选择需要的助记；直接点复制，或长按文字后点系统“复制”，都会继续流程。')
m=m.replace('本工具不读取墨墨账号数据，也不读取剪贴板内容。自动化依赖 Android 无障碍节点；如果两款 App 后续大改界面，搜索按钮或笔记入口可能需要再次适配。','v0.5 不读取剪贴板文字，只监听“剪贴板发生变化”来识别复制。若屏幕边缘还有白底黑色悬浮按钮，那是系统无障碍快捷按钮，不是本应用创建的第二个悬浮窗；请用上方按钮进入系统设置关闭“快捷方式/悬浮按钮”，只保留服务开启。')
main.write_text(m)
print('v0.5 patch applied')
