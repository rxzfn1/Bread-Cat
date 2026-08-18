from pathlib import Path

root = Path('mnemonic-bridge-v0.4')
svc = root/'app/src/main/java/com/bbdc/memo/bridge/BridgeAccessibilityService.java'
main = root/'app/src/main/java/com/bbdc/memo/bridge/MainActivity.java'
manifest = root/'app/src/main/AndroidManifest.xml'
gradle = root/'app/build.gradle'

def req(text, old, new, label):
    if old not in text:
        raise SystemExit(f'patch marker missing: {label}')
    return text.replace(old, new, 1)

s = svc.read_text()

# Search-only behavior: tapping the overlay while already inside MaiMemo must not start the old
# copy/return/paste state machine.
old_handle = '''    private void handleBubbleTap() {
        String pkg = activePackage();
        if (MAIMEMO_PACKAGE.equals(pkg)) {
            if (stage == Stage.RETURNING_BBDC || stage == Stage.PASTING) {
                Toast.makeText(this, "memory 正在返回不背单词，请稍等…", Toast.LENGTH_SHORT).show();
                return;
            }
            if (targetWord == null || targetWord.trim().isEmpty() || stage == Stage.IDLE) {
                Toast.makeText(this, "当前没有正在处理的单词，请先从不背单词点击 memory 开始", Toast.LENGTH_LONG).show();
                return;
            }
            // Manual acknowledgement is intentionally allowed from OPENING/SEARCHING/WAITING_COPY.
            // The user tapping here explicitly means: "I have copied the mnemonic already".
            if (stage != Stage.WAITING_COPY) setStage(Stage.WAITING_COPY);
            Toast.makeText(this, "已确认你复制完成，正在返回“" + targetWord + "”的笔记…", Toast.LENGTH_SHORT).show();
            beginReturnToBbdc();
            return;
        }
        startBridgeFlow();
    }
'''
new_handle = '''    private void handleBubbleTap() {
        String pkg = activePackage();
        if (MAIMEMO_PACKAGE.equals(pkg)) {
            Toast.makeText(this, "当前已在墨墨。memory 1.2 只负责从不背单词识词并自动搜索", Toast.LENGTH_SHORT).show();
            return;
        }
        startBridgeFlow();
    }
'''
s = req(s, old_handle, new_handle, 'search-only bubble tap')

# When the exact result is found, finish the flow instead of entering WAITING_COPY.
old_exact = '''        if (exact != null) {
            boolean clicked = exact.performAction(AccessibilityNodeInfo.ACTION_CLICK);
            exact.recycle();
            root.recycle();
            setStage(Stage.WAITING_COPY);
            Toast.makeText(this, clicked
                    ? "已进入“" + targetWord + "”，请选择助记并复制"
                    : "已找到“" + targetWord + "”，请手动点结果并复制助记",
                    Toast.LENGTH_LONG).show();
            return;
        }
'''
new_exact = '''        if (exact != null) {
            String searched = targetWord;
            boolean clicked = exact.performAction(AccessibilityNodeInfo.ACTION_CLICK);
            exact.recycle();
            root.recycle();
            resetFlowSilently();
            Toast.makeText(this, clicked
                    ? "已完成搜索：“" + searched + "”"
                    : "已找到“" + searched + "”，请手动点一下搜索结果",
                    Toast.LENGTH_LONG).show();
            return;
        }
'''
s = req(s, old_exact, new_exact, 'finish after exact search')

# If MaiMemo accepted the text but its result UI is not exposed to accessibility, stop cleanly.
old_wait = '''    private void waitForCopyManual() {
        setStage(Stage.WAITING_COPY);
        Toast.makeText(this, "已把“" + targetWord + "”填入墨墨；若未进入词条，请手动点结果，复制助记后会自动返回", Toast.LENGTH_LONG).show();
    }
'''
new_wait = '''    private void waitForCopyManual() {
        String searched = targetWord;
        resetFlowSilently();
        Toast.makeText(this, "已把“" + searched + "”填入墨墨并提交搜索；若没有自动进入词条，请手动点一下结果", Toast.LENGTH_LONG).show();
    }
'''
s = req(s, old_wait, new_wait, 'disable old copy return state')

# The older copy listener can remain compiled, but search-only mode will never leave the flow in
# WAITING_COPY, so clipboard/long-click events cannot trigger an automatic return.
svc.write_text(s)

# Do not hide memory from Recents. On ColorOS-like systems users can lock the task if they want
# stronger background persistence; hiding it made troubleshooting and OEM behavior worse.
ma = manifest.read_text()
ma = ma.replace('\n            android:excludeFromRecents="true"', '')
manifest.write_text(ma)

m = main.read_text()
m = m.replace('v1.0 起 memory 不再出现在最近任务列表，普通清理最近任务不会主动移除它。',
              'v1.2 为无障碍搜索专用版：只负责不背单词识词 → 打开墨墨 → 填词并搜索。建议在最近任务中给 memory 加锁，避免手机管家强力清理。')
m = m.replace('''                "③ memory 读取当前单词并打开墨墨，尝试自动搜索。\\n" +
                "④ 在墨墨选择需要的助记并复制。\\n" +
                "⑤ 复制完成后，再点击一次屏幕侧边的 memory 悬浮图标，表示‘我已经复制好了’。\\n" +
                "⑥ memory 自动返回原来的不背单词页面并打开对应笔记；随后你在笔记输入框长按选择‘粘贴’。\\n\\n" +''',
'''                "③ memory 读取不背单词页面上方最大、独立显示的目标词。\\n" +
                "④ 自动打开墨墨，找到搜索框并填入目标词。\\n" +
                "⑤ 自动提交搜索，并尽量进入完全匹配的词条。\\n\\n" +''')
main.write_text(m)

g = gradle.read_text()
g = g.replace('versionCode 10', 'versionCode 12').replace("versionName '1.0.0'", "versionName '1.2.0'")
gradle.write_text(g)

print('memory v1.2 accessibility search-only patch applied')
