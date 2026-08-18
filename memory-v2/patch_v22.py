from pathlib import Path
import re

root = Path('memory-v2')
app_gradle = root / 'app/build.gradle'
manifest = root / 'app/src/main/AndroidManifest.xml'
main = root / 'app/src/main/java/com/memory/bridge/MainActivity.java'
svc = root / 'app/src/main/java/com/memory/bridge/CaptureOverlayService.java'

# Version bump.
g = app_gradle.read_text(encoding='utf-8')
g = g.replace('versionCode 20', 'versionCode 22').replace("versionName '2.0.0'", "versionName '2.2.0'")
g = g.replace('versionCode 21', 'versionCode 22').replace("versionName '2.1.0'", "versionName '2.2.0'")
app_gradle.write_text(g, encoding='utf-8')

# No API/network permission in 2.2.
m = manifest.read_text(encoding='utf-8')
m = m.replace('    <uses-permission android:name="android.permission.INTERNET" />\n', '')
manifest.write_text(m, encoding='utf-8')

# Simplify UI: remove Token/API controls completely.
s = main.read_text(encoding='utf-8')
s = s.replace('    private EditText tokenInput;\n', '')

pattern = re.compile(r'''        TextView apiTitle = text\("2\. 墨墨官方 Open API Token（推荐）".*?        root\.addView\(openMaimemo, smallButtonLp\(\)\);\n''', re.S)
replacement = '''        TextView modeTitle = text("2. 无 API 直达墨墨搜索", 17, Color.rgb(25, 25, 29));
        modeTitle.setTypeface(null, 1);
        LinearLayout.LayoutParams mp2 = new LinearLayout.LayoutParams(-1, -2);
        mp2.topMargin = dp(24);
        root.addView(modeTitle, mp2);

        TextView modeHelp = text("点悬浮图标后：OCR 识别当前大号英文单词 → 自动复制 → 优先调用墨墨对外暴露的搜索入口并带入单词。若当前墨墨版本没有开放搜索入口，则会打开墨墨并保留单词在剪贴板。", 14, Color.rgb(97, 97, 104));
        modeHelp.setLineSpacing(0, 1.3f);
        LinearLayout.LayoutParams mh = new LinearLayout.LayoutParams(-1, -2);
        mh.topMargin = dp(8);
        root.addView(modeHelp, mh);
'''
s, n = pattern.subn(replacement, s, count=1)
if n != 1:
    raise SystemExit('main API UI block not found')

s = s.replace('Button start = button("3. 启动悬浮识词");', 'Button start = button("3. 启动悬浮识词");')
s = s.replace('        getPreferencesStore().edit().putString("maimemo_token", tokenInput.getText().toString().trim()).apply();\n', '')

# Replace guide with no-API flow.
guide_pattern = re.compile(r'''        TextView guide = text\(\n.*?                14, Color\.rgb\(83, 83, 90\)\);''', re.S)
guide_replacement = '''        TextView guide = text(
                "使用方式\\n\\n" +
                "在不背单词页面点 memory 悬浮图标 → OCR 识别当前大号英文词 → 自动复制该词 → memory 尝试直接调用墨墨的系统搜索入口并把词作为查询内容传入。\\n\\n" +
                "如果你的墨墨版本没有对第三方开放搜索 Intent，memory 会自动打开墨墨，同时单词已经在剪贴板中；这时只需在墨墨搜索框粘贴即可。\\n\\n" +
                "本版本不调用任何墨墨 API，不需要 Token，也不使用无障碍权限。",
                14, Color.rgb(83, 83, 90));'''
s, n = guide_pattern.subn(guide_replacement, s, count=1)
if n != 1:
    raise SystemExit('main guide block not found')

s = s.replace('TextView badge = text("memory 2.0 · 无障碍版"', 'TextView badge = text("memory 2.2 · 无 API 版"')
main.write_text(s, encoding='utf-8')

# OCR result should go straight to MaiMemo search; no API branch.
s = svc.read_text(encoding='utf-8')
s = s.replace('import android.content.pm.ServiceInfo;\n', 'import android.content.pm.ServiceInfo;\nimport android.content.pm.ResolveInfo;\nimport android.content.pm.PackageManager;\n')

old = '''                    String token = prefs().getString("maimemo_token", "").trim();
                    if (token.isEmpty()) {
                        openMaimemoFallback(word, "未设置墨墨 API Token");
                    } else {
                        fetchMaimemoNotes(word, token);
                    }
'''
if old not in s:
    raise SystemExit('OCR API branch not found')
s = s.replace(old, '                    openMaimemoSearch(word);\n', 1)

insert_marker = '    private void openMaimemoFallback(String word, String reason) {'
if insert_marker not in s:
    raise SystemExit('openMaimemoFallback marker not found')

search_method = r'''    private void openMaimemoSearch(String word) {
        hidePanel();
        copyText(word);

        // 1) Standard Android searchable-activity contract.
        try {
            Intent search = new Intent(Intent.ACTION_SEARCH);
            search.setPackage(MAIMEMO_PACKAGE);
            search.putExtra(android.app.SearchManager.QUERY, word);
            search.putExtra("query", word);
            search.putExtra("word", word);
            search.putExtra("keyword", word);
            search.putExtra("spelling", word);
            search.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TOP | Intent.FLAG_ACTIVITY_SINGLE_TOP);
            if (canResolve(search)) {
                startActivity(search);
                toast("已识别并搜索：" + word);
                return;
            }
        } catch (Exception ignored) {}

        // 2) Some dictionary/word apps expose ACTION_PROCESS_TEXT instead of ACTION_SEARCH.
        try {
            Intent process = new Intent(Intent.ACTION_PROCESS_TEXT);
            process.setPackage(MAIMEMO_PACKAGE);
            process.setType("text/plain");
            process.putExtra(Intent.EXTRA_PROCESS_TEXT, word);
            process.putExtra(Intent.EXTRA_PROCESS_TEXT_READONLY, true);
            process.putExtra(android.app.SearchManager.QUERY, word);
            process.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            if (canResolve(process)) {
                startActivity(process);
                toast("已把 “" + word + "” 发送到墨墨");
                return;
            }
        } catch (Exception ignored) {}

        // 3) Fallback: launch MaiMemo with common query extras. If ignored, clipboard still contains the word.
        Intent launch = getPackageManager().getLaunchIntentForPackage(MAIMEMO_PACKAGE);
        if (launch == null) {
            showMessagePanel("没有找到墨墨背单词", "已复制单词 “" + word + "”。", null);
            return;
        }
        launch.putExtra(android.app.SearchManager.QUERY, word);
        launch.putExtra("query", word);
        launch.putExtra("word", word);
        launch.putExtra("keyword", word);
        launch.putExtra("spelling", word);
        launch.putExtra("search_word", word);
        launch.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_REORDER_TO_FRONT | Intent.FLAG_ACTIVITY_SINGLE_TOP);
        try {
            startActivity(launch);
            toast("已识别并复制 “" + word + "”。如果墨墨没有自动搜索，请在搜索框粘贴");
        } catch (Exception e) {
            showMessagePanel("打开墨墨失败", "单词 “" + word + "” 已复制到剪贴板。", null);
        }
    }

    private boolean canResolve(Intent intent) {
        try {
            java.util.List<ResolveInfo> matches = getPackageManager().queryIntentActivities(intent, PackageManager.MATCH_DEFAULT_ONLY);
            return matches != null && !matches.isEmpty();
        } catch (Exception e) {
            return false;
        }
    }

'''
s = s.replace(insert_marker, search_method + insert_marker, 1)

# We no longer enter the old fallback-return state from OCR.
s = s.replace('toast("memory 已启动。现在可以回到不背单词使用悬浮图标");', 'toast("memory 已启动。回到不背单词后点悬浮图标即可识词并打开墨墨搜索");')
svc.write_text(s, encoding='utf-8')

print('memory 2.2 no-API search-intent patch applied')
