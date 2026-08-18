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

# ---- service fixes ----
s = svc.read_text()

# 1) A normal tap should reveal the full icon only AFTER ACTION_UP, so we keep the v0.6
# anti-CANCEL behavior while restoring the visual response the user expects.
s = req(s,
'''                } else if (e.getAction() == MotionEvent.ACTION_UP) {
                    startBridgeFlow();
                }
                scheduleDock(v, lp, size, reveal, hidden);
''',
'''                } else if (e.getAction() == MotionEvent.ACTION_UP) {
                    revealBubble(v, lp, size, reveal);
                    startBridgeFlow();
                }
                scheduleDock(v, lp, size, reveal, hidden);
''', 'tap reveal on up')

# 2) More time for slow Maimemo cold starts and explicit progress feedback.
s = req(s,
'''        if (attempt < 9) postFlow(g, 350, () -> driveMaimemo(g, attempt + 1));
        else {
            setStage(Stage.WAITING_COPY);
            Toast.makeText(this, "没识别到墨墨搜索控件，请手动搜索“" + targetWord + "”；复制助记后仍会自动返回", Toast.LENGTH_LONG).show();
        }
''',
'''        if (attempt < 20) {
            if (attempt == 6) Toast.makeText(this, "墨墨已打开，正在继续寻找搜索入口…", Toast.LENGTH_SHORT).show();
            postFlow(g, 360, () -> driveMaimemo(g, attempt + 1));
        } else {
            setStage(Stage.WAITING_COPY);
            Toast.makeText(this, "暂时没识别到墨墨搜索控件，请手动搜索“" + targetWord + "”；复制后仍会自动返回", Toast.LENGTH_LONG).show();
        }
''', 'longer Maimemo retry')

# 3) After setting text, do not assume Maimemo automatically submits the query.
s = req(s,
'''            if (ok) {
                postFlow(g, 600, () -> chooseExactResult(g, 0));
            } else retryMaimemo(g, attempt);
''',
'''            if (ok) {
                Toast.makeText(this, "已填入“" + targetWord + "”，正在提交搜索…", Toast.LENGTH_SHORT).show();
                postFlow(g, 420, () -> chooseExactResult(g, 0));
            } else retryMaimemo(g, attempt);
''', 'search text feedback')

old_choose = '''    private void chooseExactResult(long g, int attempt) {
        if (g != generation || stage != Stage.SEARCHING_MAIMEMO) return;
        AccessibilityNodeInfo root = getRootInActiveWindow();
        if (root == null) {
            if (attempt < 8) postFlow(g, 350, () -> chooseExactResult(g, attempt + 1));
            else waitForCopyManual();
            return;
        }
        AccessibilityNodeInfo exact = findClickableExactText(root, targetWord);
        if (exact != null) {
            boolean clicked = exact.performAction(AccessibilityNodeInfo.ACTION_CLICK);
            exact.recycle();
            root.recycle();
            setStage(Stage.WAITING_COPY);
            Toast.makeText(this, clicked
                    ? "已搜索“" + targetWord + "”，选好助记后点墨墨里的复制"
                    : "已填入“" + targetWord + "”，请手动点搜索结果并复制助记",
                    Toast.LENGTH_LONG).show();
            return;
        }
        root.recycle();
        if (attempt < 8) postFlow(g, 350, () -> chooseExactResult(g, attempt + 1));
        else waitForCopyManual();
    }
'''
new_choose = '''    private void chooseExactResult(long g, int attempt) {
        if (g != generation || stage != Stage.SEARCHING_MAIMEMO) return;
        AccessibilityNodeInfo root = getRootInActiveWindow();
        if (root == null) {
            if (attempt < 16) postFlow(g, 330, () -> chooseExactResult(g, attempt + 1));
            else waitForCopyManual();
            return;
        }

        // First preference: if the exact word result is already visible, open it.
        AccessibilityNodeInfo exact = findClickableExactText(root, targetWord);
        if (exact != null) {
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

        // Maimemo versions differ: some need an explicit search/confirm action after ACTION_SET_TEXT.
        AccessibilityNodeInfo submit = findClickableByKeywords(root,
                new String[]{"搜索", "查词", "搜词", "确定", "search", "go"});
        if (submit != null) {
            boolean clicked = submit.performAction(AccessibilityNodeInfo.ACTION_CLICK);
            submit.recycle();
            if (clicked) {
                root.recycle();
                postFlow(g, 520, () -> chooseExactResult(g, attempt + 1));
                return;
            }
        }

        // Try the IME search/enter accessibility action on the actual editable field.
        AccessibilityNodeInfo edit = findBestSearchEditable(root);
        if (edit != null) {
            try { edit.performAction(AccessibilityNodeInfo.ACTION_FOCUS); } catch (Exception ignored) {}
            boolean entered = false;
            if (android.os.Build.VERSION.SDK_INT >= 30) {
                try {
                    entered = edit.performAction(
                            AccessibilityNodeInfo.AccessibilityAction.ACTION_IME_ENTER.getId());
                } catch (Exception ignored) {}
            }
            edit.recycle();
            if (entered) {
                root.recycle();
                postFlow(g, 520, () -> chooseExactResult(g, attempt + 1));
                return;
            }
        }

        // Conservative unlabeled-icon fallback: only click when there is exactly one likely
        // clickable image in the top-right search area. This avoids blindly using coordinates.
        if (attempt >= 6) {
            AccessibilityNodeInfo likely = findSingleTopRightAction(root);
            if (likely != null) {
                boolean clicked = likely.performAction(AccessibilityNodeInfo.ACTION_CLICK);
                likely.recycle();
                if (clicked) {
                    root.recycle();
                    postFlow(g, 520, () -> driveMaimemo(g, 0));
                    return;
                }
            }
        }

        root.recycle();
        if (attempt < 16) postFlow(g, 330, () -> chooseExactResult(g, attempt + 1));
        else waitForCopyManual();
    }
'''
s = req(s, old_choose, new_choose, 'replace chooseExactResult')

# 4) Conservative helper for unlabeled search icons.
marker = '''    private AccessibilityNodeInfo findClickableExactText(AccessibilityNodeInfo node, String exact) {
'''
helper = '''    private AccessibilityNodeInfo findSingleTopRightAction(AccessibilityNodeInfo root) {
        if (root == null) return null;
        List<AccessibilityNodeInfo> candidates = new ArrayList<>();
        collectTopRightActions(root, candidates);
        AccessibilityNodeInfo result = candidates.size() == 1
                ? AccessibilityNodeInfo.obtain(candidates.get(0)) : null;
        for (AccessibilityNodeInfo n : candidates) n.recycle();
        return result;
    }

    private void collectTopRightActions(AccessibilityNodeInfo node, List<AccessibilityNodeInfo> out) {
        if (node == null) return;
        if (node.isVisibleToUser() && node.isClickable() && !node.isEditable()) {
            Rect b = new Rect();
            node.getBoundsInScreen(b);
            int sw = getResources().getDisplayMetrics().widthPixels;
            int sh = getResources().getDisplayMetrics().heightPixels;
            String cls = node.getClassName() == null ? "" : node.getClassName().toString();
            String t = nodeText(node).toLowerCase(Locale.ROOT);
            String id = safeId(node).toLowerCase(Locale.ROOT);
            boolean imageLike = cls.contains("Image") || cls.contains("Button");
            boolean topRight = b.exactCenterX() > sw * 0.58f && b.exactCenterY() < sh * 0.20f;
            boolean searchNamed = containsAny(t, "搜索", "search", "查词")
                    || containsAny(id, "search", "query", "lookup");
            if (searchNamed || (imageLike && topRight && b.width() <= sw * 0.22f && b.height() <= sh * 0.14f)) {
                out.add(AccessibilityNodeInfo.obtain(node));
            }
        }
        for (int i = 0; i < node.getChildCount(); i++) {
            AccessibilityNodeInfo child = node.getChild(i);
            if (child != null) {
                collectTopRightActions(child, out);
                child.recycle();
            }
        }
    }

'''
if marker not in s:
    raise SystemExit('patch marker missing: helper insert')
s = s.replace(marker, helper + marker, 1)

# Rename service-visible strings without touching package identity.
s = s.replace('助记悬浮桥已启动', 'memory 已启动')
s = s.replace('助记悬浮桥', 'memory')
svc.write_text(s)

# ---- manifest/name ----
ma = manifest.read_text().replace('android:label="助记悬浮桥"', 'android:label="memory"')
manifest.write_text(ma)

st = strings.read_text().replace('<string name="app_name">助记悬浮桥</string>', '<string name="app_name">memory</string>')
st = st.replace('助记悬浮桥', 'memory')
strings.write_text(st)

# ---- main UI: keep one process; add a simple battery-settings entry ----
m = main.read_text()
m = m.replace('Ui.title(this, "助记悬浮桥", 28)', 'Ui.title(this, "memory", 28)')
m = m.replace('“助记悬浮桥”', '“memory”').replace('‘助记悬浮桥’', '‘memory’')
m = m.replace('助记悬浮桥', 'memory')

m = req(m,
'''        Button cancel = Ui.button(this, "取消当前自动流程");
''',
'''        Button background = Ui.button(this, "打开后台省电设置（建议允许 memory 后台运行）");
        background.setOnClickListener(v -> {
            try {
                startActivity(new Intent(Settings.ACTION_IGNORE_BATTERY_OPTIMIZATION_SETTINGS));
            } catch (Exception e) {
                startActivity(new Intent(Settings.ACTION_SETTINGS));
            }
        });
        root.addView(background);

        Button cancel = Ui.button(this, "取消当前自动流程");
''', 'battery settings button')

m = m.replace('v0.6 已修复贴边状态下偶发点击无响应；按下会先震动确认。',
              'v0.8：贴边图标在完整接收点击后再弹出，避免触摸被取消；墨墨搜索增加“提交搜索/回车/搜索图标”多级兜底。')
main.write_text(m)

# version
g = gradle.read_text().replace('versionCode 6', 'versionCode 8').replace("versionName '0.6.0'", "versionName '0.8.0'")
gradle.write_text(g)

print('memory v0.8 patch applied')
