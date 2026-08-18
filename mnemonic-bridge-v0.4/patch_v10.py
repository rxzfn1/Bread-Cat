from pathlib import Path
import re

root = Path('mnemonic-bridge-v0.4')
svc = root/'app/src/main/java/com/bbdc/memo/bridge/BridgeAccessibilityService.java'
main = root/'app/src/main/java/com/bbdc/memo/bridge/MainActivity.java'
manifest = root/'app/src/main/AndroidManifest.xml'
gradle = root/'app/build.gradle'

s = svc.read_text()

# 1) Fix BBDC current-word recognition.
# Old behavior split every short sentence into word candidates. A sentence word such as "When"
# inherited the bounds of the whole sentence block and could outrank the large vocabulary heading.
# New behavior is two-pass: first only standalone single-word nodes near the upper study-card area;
# sentence fragments are considered only as a last resort.
pattern = re.compile(r'    private String detectCurrentWord\(\) \{.*?\n    \}\n\n    private void collectCandidates', re.S)
replacement = r'''    private String detectCurrentWord() {
        AccessibilityNodeInfo root = getRootInActiveWindow();
        if (root == null) return "";
        List<Candidate> candidates = new ArrayList<>();
        collectCandidates(root, candidates, 0);
        root.recycle();

        int sw = getResources().getDisplayMetrics().widthPixels;
        int sh = getResources().getDisplayMetrics().heightPixels;

        Candidate best = chooseWordCandidate(candidates, sw, sh, true);
        if (best == null) best = chooseWordCandidate(candidates, sw, sh, false);
        return best == null ? "" : best.word;
    }

    private Candidate chooseWordCandidate(List<Candidate> candidates, int sw, int sh, boolean standaloneOnly) {
        Candidate best = null;
        for (Candidate c : candidates) {
            String low = c.word.toLowerCase(Locale.US);
            if (STOP.contains(low) || c.bounds.width() <= 0 || c.bounds.height() <= 0) continue;

            float cx = c.bounds.exactCenterX() / Math.max(1f, sw);
            float cy = c.bounds.exactCenterY() / Math.max(1f, sh);
            float wr = c.bounds.width() / Math.max(1f, sw);
            float hr = c.bounds.height() / Math.max(1f, sh);

            if (standaloneOnly) {
                if (!c.standalone) continue;
                // BBDC's large vocabulary heading is consistently in the upper part of the page.
                if (cy < .055f || cy > .34f) continue;
                if (wr > .70f || hr > .13f) continue;
            } else {
                // Last-resort fallback is still restricted so a huge sentence/paragraph node cannot win.
                if (cy < .045f || cy > .42f) continue;
                if (wr > .88f || hr > .20f) continue;
            }

            float vertical = 1f - Math.min(1f, Math.abs(cy - .15f) / .23f);
            float leftUpper = 1f - Math.min(1f, Math.abs(cx - .28f) / .58f);
            float visualHeight = Math.min(1.45f, hr / .032f);
            float compactBox = 1f - Math.min(1f, wr / .78f);
            float idBoost = containsAny(c.viewId.toLowerCase(Locale.ROOT),
                    "word", "lexis", "vocab", "head", "title") ? 1f : 0f;

            c.score = vertical * 5.2f
                    + visualHeight * 4.3f
                    + leftUpper * 1.4f
                    + compactBox * 2.0f
                    + idBoost * 4.0f
                    + (c.standalone ? 7.5f : -5.0f);

            if (best == null || c.score > best.score) best = c;
        }
        return best;
    }

    private void collectCandidates'''
new_s, count = pattern.subn(replacement, s, count=1)
if count != 1:
    raise SystemExit('detectCurrentWord replacement failed')
s = new_s

# Treat a single word with surrounding punctuation (for example "devour :") as a standalone node.
old_extract = '''    private void extractCandidates(CharSequence seq, Rect bounds, String id, List<Candidate> out) {
        if (seq == null) return;
        String s = seq.toString().trim();
        if (WORD.matcher(s).matches()) {
            out.add(new Candidate(normalizeWord(s), new Rect(bounds), true, id));
            return;
        }
        if (s.length() <= 100) {
            Matcher m = TOKEN.matcher(s);
            while (m.find()) out.add(new Candidate(normalizeWord(m.group()), new Rect(bounds), false, id));
        }
    }
'''
new_extract = '''    private void extractCandidates(CharSequence seq, Rect bounds, String id, List<Candidate> out) {
        if (seq == null) return;
        String raw = seq.toString().trim();
        if (raw.isEmpty()) return;

        String stripped = raw
                .replaceFirst("^[^A-Za-z]+", "")
                .replaceFirst("[^A-Za-z]+$", "")
                .trim();
        if (WORD.matcher(stripped).matches()) {
            out.add(new Candidate(normalizeWord(stripped), new Rect(bounds), true, id));
            return;
        }

        // Embedded words from examples/definitions are fallback-only candidates.
        if (raw.length() <= 100) {
            Matcher m = TOKEN.matcher(raw);
            while (m.find()) {
                out.add(new Candidate(normalizeWord(m.group()), new Rect(bounds), false, id));
            }
        }
    }
'''
if old_extract not in s:
    raise SystemExit('extractCandidates marker missing')
s = s.replace(old_extract, new_extract, 1)

# 2) If the launcher task is removed, do not treat that as a request to stop the overlay/service.
interrupt_marker = '    @Override public void onInterrupt() {}\n'
if interrupt_marker not in s:
    raise SystemExit('onInterrupt marker missing')
if 'public void onTaskRemoved(Intent rootIntent)' not in s:
    s = s.replace(interrupt_marker, interrupt_marker + '''\n    @Override\n    public void onTaskRemoved(Intent rootIntent) {\n        main.postDelayed(() -> {\n            if (Prefs.floatingEnabled(this) && bubble == null) showBubble();\n        }, 300L);\n        super.onTaskRemoved(rootIntent);\n    }\n''', 1)

svc.write_text(s)

# 3) Keep memory out of Recents entirely. The setup Activity is not part of the runtime workflow,
# so there is no reason for users/"clear all" to remove its task together with the accessibility tool.
ma = manifest.read_text()
ma = ma.replace('''        <activity\n            android:name=".MainActivity"\n            android:exported="true">''', '''        <activity\n            android:name=".MainActivity"\n            android:exported="true"\n            android:excludeFromRecents="true">''')
ma = ma.replace('''            android:exported="false"\n            android:label="memory"\n            android:permission="android.permission.BIND_ACCESSIBILITY_SERVICE">''', '''            android:exported="false"\n            android:label="memory"\n            android:stopWithTask="false"\n            android:permission="android.permission.BIND_ACCESSIBILITY_SERVICE">''')
manifest.write_text(ma)

# 4) Update help text so the new behavior is explicit.
m = main.read_text()
m = m.replace('''                "图标可拖动；不操作约 1.2 秒后自动吸附到最近的屏幕侧边，只露出三分之一。长按图标可取消本次流程。"));''', '''                "图标可拖动；不操作约 1.2 秒后自动吸附到最近的屏幕侧边，只露出三分之一。长按图标可取消本次流程。\\n\\n" +\n                "v1.0 起 memory 不再出现在最近任务列表，普通清理最近任务不会主动移除它。"));''')
main.write_text(m)

# version
g = gradle.read_text().replace('versionCode 9', 'versionCode 10').replace("versionName '0.9.0'", "versionName '1.0.0'")
gradle.write_text(g)

print('memory v1.0 recognition + recents persistence patch applied')
