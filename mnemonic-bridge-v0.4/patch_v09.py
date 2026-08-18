from pathlib import Path
root = Path('mnemonic-bridge-v0.4')
svc = root/'app/src/main/java/com/bbdc/memo/bridge/BridgeAccessibilityService.java'
main = root/'app/src/main/java/com/bbdc/memo/bridge/MainActivity.java'
gradle = root/'app/build.gradle'

def req(text, old, new, label):
    if old not in text:
        raise SystemExit(f'patch marker missing: {label}')
    return text.replace(old, new, 1)

s = svc.read_text()

# A tap has two meanings now:
# - in BBDC: start the lookup flow
# - in Maimemo: user manually confirms that the mnemonic has already been copied
s = req(s,
'''                } else if (e.getAction() == MotionEvent.ACTION_UP) {
                    revealBubble(v, lp, size, reveal);
                    startBridgeFlow();
                }
''',
'''                } else if (e.getAction() == MotionEvent.ACTION_UP) {
                    revealBubble(v, lp, size, reveal);
                    handleBubbleTap();
                }
''', 'route bubble tap by active app')

marker = '''    private void startBridgeFlow() {
'''
helper = '''    private void handleBubbleTap() {
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
if marker not in s:
    raise SystemExit('patch marker missing: bubble tap helper')
s = s.replace(marker, helper + marker, 1)

s = s.replace('Toast.makeText(this, "检测到复制，正在返回不背单词…", Toast.LENGTH_SHORT).show();',
              'Toast.makeText(this, "正在返回不背单词并打开对应笔记…", Toast.LENGTH_SHORT).show();')

# Be more tolerant while the original BBDC activity is being brought back to foreground.
s = s.replace('if (attempt < 8) postFlow(g, 350, () -> openNoteAndPaste(g, attempt + 1));',
              'if (attempt < 15) postFlow(g, 350, () -> openNoteAndPaste(g, attempt + 1));')
s = s.replace('if (attempt < 8) postFlow(g, 350, () -> pasteAfterNoteOpened(g, attempt + 1));',
              'if (attempt < 15) postFlow(g, 350, () -> pasteAfterNoteOpened(g, attempt + 1));')

# Widen semantic matching for BBDC note buttons/ids, but still avoid coordinate clicking.
s = req(s,
'''        AccessibilityNodeInfo note = findClickableByKeywords(root,
                new String[]{"添加笔记", "写笔记", "我的笔记", "笔记", "备注"});
''',
'''        AccessibilityNodeInfo note = findClickableByKeywords(root,
                new String[]{"添加笔记", "写笔记", "我的笔记", "笔记", "备注",
                        "note", "memo", "remark", "editnote", "edit_note", "addnote", "add_note"});
''', 'broaden note semantics')

# v0.9 intentionally leaves the final paste to the user. This is much more reliable across
# Android clipboard/privacy variants while still automating the cross-app navigation.
s = req(s,
'''        if (editor != null) {
            boolean ok = pasteInto(editor);
            editor.recycle();
            root.recycle();
            finishPaste(ok);
            return;
        }
''',
'''        if (editor != null) {
            focusNoteEditor(editor);
            editor.recycle();
            root.recycle();
            finishManualPastePrompt();
            return;
        }
''', 'manual paste on already-open note editor')

s = req(s,
'''        boolean ok = pasteInto(editor);
        editor.recycle();
        root.recycle();
        finishPaste(ok);
    }

    private boolean pasteInto(AccessibilityNodeInfo edit) {
''',
'''        focusNoteEditor(editor);
        editor.recycle();
        root.recycle();
        finishManualPastePrompt();
    }

    private void focusNoteEditor(AccessibilityNodeInfo edit) {
        if (edit == null) return;
        try { edit.performAction(AccessibilityNodeInfo.ACTION_FOCUS); } catch (Exception ignored) {}
        try { edit.performAction(AccessibilityNodeInfo.ACTION_CLICK); } catch (Exception ignored) {}
        CharSequence existing = edit.getText();
        if (existing != null && existing.length() > 0) {
            Bundle args = new Bundle();
            args.putInt(AccessibilityNodeInfo.ACTION_ARGUMENT_SELECTION_START_INT, existing.length());
            args.putInt(AccessibilityNodeInfo.ACTION_ARGUMENT_SELECTION_END_INT, existing.length());
            try { edit.performAction(AccessibilityNodeInfo.ACTION_SET_SELECTION, args); } catch (Exception ignored) {}
        }
    }

    private void finishManualPastePrompt() {
        String word = targetWord;
        resetFlowSilently();
        Toast.makeText(this,
                "已打开“" + word + "”的笔记输入框。助记还在剪贴板，请长按输入框选择“粘贴”",
                Toast.LENGTH_LONG).show();
    }

    private boolean pasteInto(AccessibilityNodeInfo edit) {
''', 'manual paste helper')

# If the note editor itself cannot be exposed through accessibility, keep the page open and
# make the manual fallback explicit instead of pretending the copy was lost.
s = s.replace('else failPaste("没有找到可靠的笔记输入框");',
              'else failPaste("笔记页面已打开，但没有识别到输入框；请手动点一下笔记输入区域后长按粘贴");')

svc.write_text(s)

m = main.read_text()
m = m.replace(
'''                "③ 工具读取当前单词并打开墨墨，尝试自动搜索。\\n" +
                "④ 你在墨墨选择需要的助记；直接点复制，或长按文字后点系统“复制”，都会继续流程。\\n" +
                "⑤ 工具检测到复制后返回不背单词，打开笔记并执行系统粘贴。\\n\\n" +''',
'''                "③ memory 读取当前单词并打开墨墨，尝试自动搜索。\\n" +
                "④ 在墨墨选择需要的助记并复制。\\n" +
                "⑤ 复制完成后，再点击一次屏幕侧边的 memory 悬浮图标，表示‘我已经复制好了’。\\n" +
                "⑥ memory 自动返回原来的不背单词页面并打开对应笔记；随后你在笔记输入框长按选择‘粘贴’。\\n\\n" +''')
m = m.replace('v0.8：贴边图标在完整接收点击后再弹出，避免触摸被取消；墨墨搜索增加“提交搜索/回车/搜索图标”多级兜底。',
              'v0.9：墨墨里再次点击悬浮图标即视为“已复制完成”，不再依赖系统复制事件；memory 会返回原单词并打开笔记，最后由你手动粘贴。')
main.write_text(m)

g = gradle.read_text().replace('versionCode 8', 'versionCode 9').replace("versionName '0.8.0'", "versionName '0.9.0'")
gradle.write_text(g)

print('memory v0.9 manual copy-confirm patch applied')
