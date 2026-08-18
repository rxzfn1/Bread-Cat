from pathlib import Path
import re

root = Path('mnemonic-bridge-v0.4')
svc = root/'app/src/main/java/com/bbdc/memo/bridge/BridgeAccessibilityService.java'
main = root/'app/src/main/java/com/bbdc/memo/bridge/MainActivity.java'
manifest = root/'app/src/main/AndroidManifest.xml'
gradle = root/'app/build.gradle'

s = svc.read_text()

# 1) Word recognition: treat common centered separators as part of one displayed word,
# then remove only those separators before sending the word to MaiMemo.
# Hyphen is placed last in the Java regex character class so no Java string escape is needed.
s = s.replace(
    'private static final Pattern WORD = Pattern.compile("^[A-Za-z][A-Za-z\'’-]{1,34}$");',
    'private static final Pattern WORD = Pattern.compile("^[A-Za-z][A-Za-z\'’·•∙⋅・‧･-]{1,40}$");')
s = s.replace(
    'private static final Pattern TOKEN = Pattern.compile("(?<![A-Za-z])[A-Za-z][A-Za-z\'’-]{1,34}(?![A-Za-z])");',
    'private static final Pattern TOKEN = Pattern.compile("(?<![A-Za-z])[A-Za-z][A-Za-z\'’·•∙⋅・‧･-]{1,40}(?![A-Za-z])");')
s = s.replace(
    "return word.replace('’', '\\'').trim();",
    "return word.replace('’', '\\'').replaceAll(\"[·•∙⋅・‧･]\", \"\").trim();")

# 2) Manual confirmation only: copying in MaiMemo must not navigate by itself.
s = re.sub(
    r'clipChangedListener = \(\) -> \{.*?\n\s*\};',
    '''clipChangedListener = () -> {\n                // v1.4: clipboard changes never navigate.\n                // The second memory tap in MaiMemo is the explicit confirmation.\n            };''',
    s, count=1, flags=re.S)

s, n = re.subn(
    r'\n\s*if \(stage == Stage\.WAITING_COPY\) \{.*?\n\s*\}\n\n\s*if \(MAIMEMO_PACKAGE\.equals\(currentPackage\)\)',
    '\n\n        if (MAIMEMO_PACKAGE.equals(currentPackage))',
    s, count=1, flags=re.S)
if n != 1:
    raise SystemExit('WAITING_COPY event block not found')

# 3) No edge docking. Keep the full icon on-screen and remember the exact dragged position.
s = s.replace(
    'lp.x = savedX == Integer.MIN_VALUE ? screenWidth - reveal : savedX;',
    'lp.x = savedX == Integer.MIN_VALUE ? Math.max(0, screenWidth - size - dp(16)) : clamp(savedX, 0, Math.max(0, screenWidth - size));')
s = s.replace('                scheduleDock(v, lp, size, reveal, hidden);\n', '')
s = s.replace('            scheduleDock(icon, lp, size, reveal, hidden);\n', '')

# If an older saved position was one-third offscreen, reveal it once when the bubble is created.
s = s.replace(
    'lp.y = clamp(Prefs.bubbleY(this), 0, Math.max(0, screenHeight - size));',
    'lp.y = clamp(Prefs.bubbleY(this), 0, Math.max(0, screenHeight - size));\n        lp.x = clamp(lp.x, 0, Math.max(0, screenWidth - size));')

# 4) Explicit wording for the second tap return flow.
s = s.replace('已确认你复制完成，正在返回“', '已收到第二次点击，正在返回“')
s = s.replace('检测到复制，正在返回不背单词…', '正在返回不背单词并打开笔记…')
svc.write_text(s)

# 5) Keep memory visible in Recents so the user can lock it on OEM Android skins.
ma = manifest.read_text().replace('\n            android:excludeFromRecents="true"', '')
manifest.write_text(ma)

m = main.read_text()
m = m.replace('图标可拖动；不操作约 1.2 秒后自动吸附到最近的屏幕侧边，只露出三分之一。',
              '图标始终完整显示在屏幕上，可按住拖到任意位置；松手后停在当前位置，不再自动吸附。')
m = m.replace('图标可拖动；不操作约 1.2 秒后自动吸附到最近的屏幕侧边，只露出三分之一。v0.6 已修复贴边状态下偶发点击无响应；按下会先震动确认。',
              '图标始终完整显示在屏幕上，可按住拖到任意位置；松手后停在当前位置，不再自动吸附。按下会有轻微震动确认。')
m = m.replace('v1.0 起 memory 不再出现在最近任务列表，普通清理最近任务不会主动移除它。',
              '建议在最近任务中给 memory 加锁，并在后台/电池设置中允许后台运行，以减少厂商系统清理后停用无障碍服务的情况。')
m = m.replace('v0.9：墨墨里再次点击悬浮图标即视为“已复制完成”，不再依赖系统复制事件；memory 会返回原单词并打开笔记，最后由你手动粘贴。',
              'v1.4：墨墨里复制助记后再次点击 memory，才执行返回并打开不背单词当前词的笔记；悬浮图标不再吸边。中间带 ·/•/∙ 等分隔点的单词会按完整单词识别，搜索时自动去掉分隔点。')
main.write_text(m)

g = gradle.read_text()
g = g.replace('versionCode 10', 'versionCode 14').replace("versionName '1.0.0'", "versionName '1.4.0'")
gradle.write_text(g)

print('memory v1.4 free-drag + mid-dot + manual return patch applied')
