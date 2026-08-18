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

# v1.3 uses explicit second-tap confirmation in MaiMemo. Clipboard changes/copy events must NOT
# auto-return, otherwise a normal copy can race with the user's intended confirmation tap.
old_clip = '''            clipChangedListener = () -> {
                if (stage != Stage.WAITING_COPY) return;
                main.postDelayed(this::beginReturnToBbdc, 120);
            };
'''
new_clip = '''            clipChangedListener = () -> {
                // v1.3: do not auto-return on clipboard changes.
                // Returning starts only when the user taps the memory bubble in MaiMemo.
            };
'''
s = req(s, old_clip, new_clip, 'disable clipboard auto return')

old_copy_events = '''        if (stage == Stage.WAITING_COPY) {
            int type = event.getEventType();
            if (type == AccessibilityEvent.TYPE_VIEW_CLICKED || type == AccessibilityEvent.TYPE_VIEW_LONG_CLICKED) {
                AccessibilityNodeInfo src = event.getSource();
                boolean copy = looksLikeCopyAction(src);
                if (src != null) src.recycle();
                if (copy) { beginReturnToBbdc(); return; }
            }
            if (looksLikeCopyConfirmation(event)) { beginReturnToBbdc(); return; }
        }

'''
new_copy_events = '''        if (stage == Stage.WAITING_COPY) {
            // Manual-confirm mode: copy events never trigger navigation.
        }

'''
s = req(s, old_copy_events, new_copy_events, 'disable copy event auto return')

# Manual second tap in MaiMemo is provided by the v0.9 routing patch. Keep its state machine,
# but make the user-visible wording explicit.
s = s.replace('已确认你复制完成，正在返回“', '已收到确认，正在返回“')
s = s.replace('Toast.makeText(this, "正在返回不背单词并打开对应笔记…", Toast.LENGTH_SHORT).show();',
              'Toast.makeText(this, "正在回到不背单词并打开“" + targetWord + "”的笔记…", Toast.LENGTH_SHORT).show();')

svc.write_text(s)

# Keep memory in Recents so OEM systems can lock it. The accessibility service itself remains
# android:stopWithTask="false" from the v1.0 persistence patch.
ma = manifest.read_text()
ma = ma.replace('\n            android:excludeFromRecents="true"', '')
manifest.write_text(ma)

m = main.read_text()
m = m.replace('v1.0 起 memory 不再出现在最近任务列表，普通清理最近任务不会主动移除它。',
              'v1.3：建议在最近任务里给 memory 加锁，并在“后台省电设置”里允许后台运行。普通清理任务不应撤销无障碍授权；若厂商系统主动关闭了无障碍开关，仍需由你在系统设置中重新确认。')
m = m.replace('v0.9：墨墨里再次点击悬浮图标即视为“已复制完成”，不再依赖系统复制事件；memory 会返回原单词并打开笔记，最后由你手动粘贴。',
              'v1.3：墨墨里复制助记后再次点击 memory，才执行返回；memory 优先用系统返回回到原来的不背单词学习页并自动打开笔记，最后由你手动粘贴。')
main.write_text(m)

g = gradle.read_text()
g = g.replace('versionCode 10', 'versionCode 13').replace("versionName '1.0.0'", "versionName '1.3.0'")
gradle.write_text(g)

print('memory v1.3 manual return + note patch applied')
