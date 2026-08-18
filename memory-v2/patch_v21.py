from pathlib import Path
import re

root = Path('memory-v2')
app_gradle = root / 'app/build.gradle'
manifest = root / 'app/src/main/AndroidManifest.xml'
svc = root / 'app/src/main/java/com/memory/bridge/CaptureOverlayService.java'

# Version bump.
g = app_gradle.read_text(encoding='utf-8')
g = g.replace('versionCode 20', 'versionCode 21').replace("versionName '2.0.0'", "versionName '2.1.0'")
app_gradle.write_text(g, encoding='utf-8')

# Best-effort task restore requires only a normal Android permission. If the OEM hides other tasks,
# memory will fall back to asking the user to switch back manually rather than launching BBDC home.
m = manifest.read_text(encoding='utf-8')
if 'android.permission.REORDER_TASKS' not in m:
    m = m.replace('<uses-permission android:name="android.permission.INTERNET" />',
                  '<uses-permission android:name="android.permission.INTERNET" />\n    <uses-permission android:name="android.permission.REORDER_TASKS" />')
manifest.write_text(m, encoding='utf-8')

s = svc.read_text(encoding='utf-8')

# 1) Official MaiMemo API returns top-level {"voc": ...} and {"notes": [...]}, not
#    {"success":true,"data":{...}}. Keep a compatibility fallback in case the API is wrapped later.
old = '''                JSONObject v = getJson(vocUrl, token);
                if (!v.optBoolean("success", false)) throw new IOException(apiError(v));
                JSONObject data = v.optJSONObject("data");
                JSONObject voc = data == null ? null : data.optJSONObject("voc");
                String vocId = voc == null ? "" : voc.optString("id", "");
                if (vocId.isEmpty()) throw new IOException("墨墨没有找到这个单词");

                String notesUrl = "https://open.maimemo.com/open/api/v1/notes?voc_id=" + URLEncoder.encode(vocId, "UTF-8");
                JSONObject n = getJson(notesUrl, token);
                if (!n.optBoolean("success", false)) throw new IOException(apiError(n));
                JSONObject nd = n.optJSONObject("data");
                JSONArray arr = nd == null ? null : nd.optJSONArray("notes");
'''
new = '''                JSONObject v = getJson(vocUrl, token);
                JSONObject voc = v.optJSONObject("voc");
                if (voc == null) {
                    JSONObject wrapped = v.optJSONObject("data");
                    if (wrapped != null) voc = wrapped.optJSONObject("voc");
                }
                String vocId = voc == null ? "" : voc.optString("id", "");
                if (vocId.isEmpty()) throw new IOException(apiError(v));

                String notesUrl = "https://open.maimemo.com/open/api/v1/notes?voc_id=" + URLEncoder.encode(vocId, "UTF-8");
                JSONObject n = getJson(notesUrl, token);
                JSONArray arr = n.optJSONArray("notes");
                if (arr == null) {
                    JSONObject wrapped = n.optJSONObject("data");
                    if (wrapped != null) arr = wrapped.optJSONArray("notes");
                }
'''
if old not in s:
    raise SystemExit('MaiMemo parser marker not found')
s = s.replace(old, new, 1)

# 2) Make it explicit that Open API notes are the authenticated user's own notes.
s = s.replace('"墨墨官方开放 API · " + notes.size() + " 条助记"',
              '"墨墨官方开放 API · 我的助记 " + notes.size() + " 条"')
s = s.replace('"墨墨 API 没有返回可用助记。你也可以打开墨墨 App 手动查看。"',
              '"这个单词没有返回你自己创建的墨墨助记。墨墨 App 里的社区/他人助记不属于开放 API 的个人助记列表，可以点下面按钮去墨墨查看。"')

# 3) Capture BBDC task id before opening MaiMemo, when OEM/API allows visibility.
if 'private int bbdcTaskId = -1;' not in s:
    s = s.replace('    private boolean fallbackAwaitReturn = false;\n',
                  '    private boolean fallbackAwaitReturn = false;\n    private int bbdcTaskId = -1;\n', 1)

s = s.replace('''    private void openMaimemoFallback(String word, String reason) {
        copyText(word);
''', '''    private void openMaimemoFallback(String word, String reason) {
        rememberBbdcTaskBestEffort();
        copyText(word);
''', 1)

# Insert helper methods before returnToBbdc.
marker = '    private void returnToBbdc() {'
if marker not in s:
    raise SystemExit('returnToBbdc marker not found')
helpers = '''    private void rememberBbdcTaskBestEffort() {
        bbdcTaskId = -1;
        try {
            ActivityManager am = (ActivityManager) getSystemService(ACTIVITY_SERVICE);
            if (am == null) return;
            for (ActivityManager.RunningTaskInfo info : am.getRunningTasks(24)) {
                if (info == null) continue;
                ComponentName top = info.topActivity;
                ComponentName base = info.baseActivity;
                boolean match = (top != null && BBDC_PACKAGE.equals(top.getPackageName()))
                        || (base != null && BBDC_PACKAGE.equals(base.getPackageName()));
                if (match) {
                    bbdcTaskId = info.id;
                    return;
                }
            }
        } catch (Exception ignored) {}
    }

    private boolean restoreBbdcTaskBestEffort() {
        if (bbdcTaskId < 0) return false;
        try {
            ActivityManager am = (ActivityManager) getSystemService(ACTIVITY_SERVICE);
            if (am == null) return false;
            am.moveTaskToFront(bbdcTaskId, ActivityManager.MOVE_TASK_WITH_HOME);
            return true;
        } catch (Exception ignored) {
            return false;
        }
    }

'''
s = s.replace(marker, helpers + marker, 1)

# Replace the old behavior that re-launched BBDC's launcher activity (which resets to home).
pattern = re.compile(r'''    private void returnToBbdc\(\) \{\n        Intent i = getPackageManager\(\)\.getLaunchIntentForPackage\(BBDC_PACKAGE\);\n        fallbackAwaitReturn = false;\n        if \(i == null\) \{\n            toast\("没有找到不背单词 App"\);\n            return;\n        \}\n        i\.addFlags\(Intent\.FLAG_ACTIVITY_NEW_TASK \| Intent\.FLAG_ACTIVITY_REORDER_TO_FRONT\);\n        try \{\n            startActivity\(i\);\n            toast\("已回到不背单词。请打开这个单词的笔记，再粘贴刚才复制的助记"\);\n        \} catch \(Exception e\) \{\n            toast\("返回不背单词失败"\);\n        \}\n    \}''')
replacement = '''    private void returnToBbdc() {
        fallbackAwaitReturn = false;
        if (restoreBbdcTaskBestEffort()) {
            toast("已切回原来的不背单词学习任务，当前背词位置会尽量保持不变");
            return;
        }
        showMessagePanel(
                "请切回不背单词",
                "为了不把你的学习进度重置到首页，memory 这次不会重新启动不背单词。请使用系统“最近任务”切回刚才的不背单词页面，原来的单词位置会保留。",
                null);
    }'''
s2, count = pattern.subn(replacement, s, count=1)
if count != 1:
    raise SystemExit('returnToBbdc body marker not found')
s = s2

# Better error if vocabulary response is structurally unexpected.
s = s.replace('        return "墨墨 API 请求失败";\n',
              '        String message = o.optString("message", o.optString("msg", ""));\n        if (!message.isEmpty()) return message;\n        return "墨墨 API 返回格式异常";\n', 1)

svc.write_text(s, encoding='utf-8')
print('memory 2.1 patch applied')
