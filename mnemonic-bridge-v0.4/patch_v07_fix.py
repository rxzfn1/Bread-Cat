from pathlib import Path
p = Path('mnemonic-bridge-v0.4/app/src/main/java/com/bbdc/memo/bridge/BridgeAccessibilityService.java')
s = p.read_text()
if 'import android.os.Build;' not in s:
    marker = 'import android.os.Handler;\n'
    if marker not in s:
        raise SystemExit('Build import marker missing')
    s = s.replace(marker, 'import android.os.Build;\n' + marker, 1)
p.write_text(s)
print('memory v0.7 Build import fixed')
