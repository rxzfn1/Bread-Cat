from pathlib import Path
root = Path('mnemonic-bridge-v0.4')
svc = root/'app/src/main/java/com/bbdc/memo/bridge/BridgeAccessibilityService.java'
gradle = root/'app/build.gradle'
main = root/'app/src/main/java/com/bbdc/memo/bridge/MainActivity.java'

def req(text, old, new, label):
    if old not in text:
        raise SystemExit(f'patch marker missing: {label}')
    return text.replace(old, new, 1)

s = svc.read_text()
s = req(s, 'import android.view.Gravity;\n', 'import android.view.Gravity;\nimport android.view.HapticFeedbackConstants;\n', 'haptic import')

s = req(s,
'''            if (e.getAction() == MotionEvent.ACTION_DOWN) {
                cancelDock();
                revealBubble(v, lp, size, reveal);
                down[0] = e.getRawX();
                down[1] = e.getRawY();
                down[2] = lp.x;
                down[3] = lp.y;
                downAt[0] = SystemClock.elapsedRealtime();
                moved[0] = false;
                v.animate().scaleX(0.96f).scaleY(0.96f).setDuration(80).start();
                return true;
            }
''',
'''            if (e.getAction() == MotionEvent.ACTION_DOWN) {
                cancelDock();
                // Do NOT move an edge-docked overlay while the finger is still down.
                // Moving the WindowManager view here can cancel the touch sequence on some phones.
                try { v.performHapticFeedback(HapticFeedbackConstants.KEYBOARD_TAP); } catch (Exception ignored) {}
                down[0] = e.getRawX();
                down[1] = e.getRawY();
                down[2] = lp.x;
                down[3] = lp.y;
                downAt[0] = SystemClock.elapsedRealtime();
                moved[0] = false;
                v.animate().scaleX(0.96f).scaleY(0.96f).setDuration(80).start();
                return true;
            }
''', 'stable down')

s = req(s,
'''                if (Math.abs(dx) > dp(7) || Math.abs(dy) > dp(7)) moved[0] = true;
                if (moved[0]) {
                    lp.x = clamp((int) (down[2] + dx), 0, Math.max(0, screenWidth - size));
                    lp.y = clamp((int) (down[3] + dy), 0, Math.max(0, screenHeight - size));
                    updateBubble(v, lp);
                }
''',
'''                if (!moved[0] && (Math.abs(dx) > dp(7) || Math.abs(dy) > dp(7))) {
                    moved[0] = true;
                    // Only reveal once this is definitely a drag, then rebase the drag origin
                    // so the icon does not jump when coming in from one-third edge docking.
                    revealBubble(v, lp, size, reveal);
                    down[2] = lp.x - dx;
                    down[3] = lp.y - dy;
                }
                if (moved[0]) {
                    lp.x = clamp((int) (down[2] + dx), 0, Math.max(0, screenWidth - size));
                    lp.y = clamp((int) (down[3] + dy), 0, Math.max(0, screenHeight - size));
                    updateBubble(v, lp);
                }
''', 'stable drag')

s = req(s,
'''        if (stage != Stage.IDLE) {
            Toast.makeText(this, "当前自动流程尚未结束，长按图标可取消", Toast.LENGTH_SHORT).show();
            return;
        }
        if (!BBDC_PACKAGE.equals(activePackage())) {
''',
'''        if (stage != Stage.IDLE) {
            long age = stageStartedAt == 0L ? 0L : SystemClock.elapsedRealtime() - stageStartedAt;
            if (age > 15000L && BBDC_PACKAGE.equals(activePackage())) {
                resetFlowSilently();
                Toast.makeText(this, "检测到上一流程卡住，已自动恢复，正在重新识别…", Toast.LENGTH_SHORT).show();
                main.postDelayed(this::startBridgeFlow, 140L);
                return;
            }
            Toast.makeText(this, "当前自动流程尚未结束；若已卡住，长按图标可取消", Toast.LENGTH_SHORT).show();
            return;
        }
        Toast.makeText(this, "已收到点击，正在读取当前单词…", Toast.LENGTH_SHORT).show();
        if (!BBDC_PACKAGE.equals(activePackage())) {
''', 'tap feedback and recovery')

s = req(s,
'''            if (looksLikeCopyConfirmation(event)) { beginReturnToBbdc(); return; }
        }
''',
'''            if (looksLikeCopyConfirmation(event) || eventLooksLikeSystemCopy(event)) {
                beginReturnToBbdc();
                return;
            }
        }
''', 'system copy event')

marker = '''    private boolean looksLikeCopyConfirmation(AccessibilityEvent event) {
'''
insert = '''    private boolean eventLooksLikeSystemCopy(AccessibilityEvent event) {
        if (event == null) return false;
        int type = event.getEventType();
        if (type != AccessibilityEvent.TYPE_VIEW_CLICKED
                && type != AccessibilityEvent.TYPE_ANNOUNCEMENT
                && type != AccessibilityEvent.TYPE_NOTIFICATION_STATE_CHANGED) return false;
        StringBuilder out = new StringBuilder();
        for (CharSequence text : event.getText()) if (text != null) out.append(' ').append(text);
        if (event.getContentDescription() != null) out.append(' ').append(event.getContentDescription());
        String t = out.toString().trim().replace(" ", "").toLowerCase(Locale.ROOT);
        if (type == AccessibilityEvent.TYPE_VIEW_CLICKED) {
            return t.equals("复制") || t.equals("copy") || t.contains("复制到剪贴板") || t.contains("copytoclipboard");
        }
        return t.contains("已复制") || t.contains("复制成功") || t.contains("copied");
    }

'''
if marker not in s:
    raise SystemExit('patch marker missing: insert system copy detector')
s = s.replace(marker, insert + marker, 1)
svc.write_text(s)

g = gradle.read_text().replace('versionCode 5','versionCode 6').replace("versionName '0.5.0'", "versionName '0.6.0'")
gradle.write_text(g)

m = main.read_text()
m = m.replace('v0.5 不读取剪贴板文字', 'v0.6 不读取剪贴板文字')
m = m.replace('图标可拖动；不操作约 1.2 秒后自动吸附到最近的屏幕侧边，只露出三分之一。长按图标可取消本次流程。', '图标可拖动；不操作约 1.2 秒后自动吸附到最近的屏幕侧边，只露出三分之一。v0.6 已修复贴边状态下偶发点击无响应；按下会先震动确认。长按图标可取消本次流程。')
main.write_text(m)
print('v0.6 stability patch applied')
