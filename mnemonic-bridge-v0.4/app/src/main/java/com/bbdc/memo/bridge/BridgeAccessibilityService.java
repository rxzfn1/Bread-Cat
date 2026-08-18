package com.bbdc.memo.bridge;

import android.accessibilityservice.AccessibilityService;
import android.accessibilityservice.AccessibilityServiceInfo;
import android.content.Intent;
import android.graphics.BitmapFactory;
import android.graphics.Color;
import android.graphics.PixelFormat;
import android.graphics.Rect;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.os.SystemClock;
import android.util.Base64;
import android.view.Gravity;
import android.view.MotionEvent;
import android.view.View;
import android.view.WindowManager;
import android.view.accessibility.AccessibilityEvent;
import android.view.accessibility.AccessibilityNodeInfo;
import android.widget.ImageView;
import android.widget.Toast;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Set;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public class BridgeAccessibilityService extends AccessibilityService {
    static final String BBDC_PACKAGE = "cn.com.langeasy.LangEasyLexis";
    static final String MAIMEMO_PACKAGE = "com.maimemo.android.momo";

    private static final Pattern WORD = Pattern.compile("^[A-Za-z][A-Za-z'’-]{1,34}$");
    private static final Pattern TOKEN = Pattern.compile("(?<![A-Za-z])[A-Za-z][A-Za-z'’-]{1,34}(?![A-Za-z])");
    private static final Set<String> STOP = new HashSet<>(Arrays.asList(
            "next", "back", "note", "notes", "review", "learn", "word", "words",
            "collins", "oxford", "us", "uk", "done", "save", "cancel", "english",
            "example", "examples", "menu", "more", "close", "open", "play", "pause",
            "new", "old", "easy", "hard", "skip", "known", "unknown", "edit", "copy",
            "search", "memo", "mnemonic", "sentence", "phrase", "definition", "detail"));

    private static final long LONG_PRESS_MS = 650L;
    private static final long FLOW_STALE_MS = 5 * 60 * 1000L;
    private static final long AUTO_DOCK_MS = 1200L;

    private static final String OVERLAY_ICON_BASE64 = "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";

    private enum Stage { IDLE, OPENING_MAIMEMO, SEARCHING_MAIMEMO, WAITING_COPY, RETURNING_BBDC, PASTING }

    private static volatile BridgeAccessibilityService instance;
    private final Handler main = new Handler(Looper.getMainLooper());
    private WindowManager wm;
    private View bubble;
    private String currentPackage = "";
    private String targetWord = "";
    private Stage stage = Stage.IDLE;
    private long stageStartedAt = 0L;
    private long generation = 0L;
    private boolean driveScheduled = false;
    private Runnable dockRunnable;

    public static BridgeAccessibilityService getInstance() { return instance; }

    @Override
    protected void onServiceConnected() {
        super.onServiceConnected();
        instance = this;
        AccessibilityServiceInfo info = getServiceInfo();
        info.eventTypes = AccessibilityEvent.TYPE_WINDOW_STATE_CHANGED
                | AccessibilityEvent.TYPE_WINDOW_CONTENT_CHANGED
                | AccessibilityEvent.TYPE_VIEW_CLICKED
                | AccessibilityEvent.TYPE_VIEW_FOCUSED
                | AccessibilityEvent.TYPE_VIEW_TEXT_CHANGED
                | AccessibilityEvent.TYPE_VIEW_TEXT_SELECTION_CHANGED
                | AccessibilityEvent.TYPE_NOTIFICATION_STATE_CHANGED
                | AccessibilityEvent.TYPE_ANNOUNCEMENT;
        info.feedbackType = AccessibilityServiceInfo.FEEDBACK_GENERIC;
        info.flags |= AccessibilityServiceInfo.FLAG_REPORT_VIEW_IDS
                | AccessibilityServiceInfo.FLAG_RETRIEVE_INTERACTIVE_WINDOWS;
        info.notificationTimeout = 100;
        setServiceInfo(info);
        wm = (WindowManager) getSystemService(WINDOW_SERVICE);
        refreshBubblePreference();
        Toast.makeText(this, "助记悬浮桥已启动", Toast.LENGTH_SHORT).show();
    }

    @Override
    public void onAccessibilityEvent(AccessibilityEvent event) {
        if (event == null) return;
        if (event.getPackageName() != null) currentPackage = event.getPackageName().toString();

        if (stage != Stage.IDLE && stageStartedAt > 0
                && SystemClock.elapsedRealtime() - stageStartedAt > FLOW_STALE_MS) {
            resetFlowSilently();
        }

        if (MAIMEMO_PACKAGE.equals(currentPackage)) {
            if (stage == Stage.OPENING_MAIMEMO || stage == Stage.SEARCHING_MAIMEMO) {
                scheduleDriveMaimemo(180);
            } else if (stage == Stage.WAITING_COPY) {
                if (event.getEventType() == AccessibilityEvent.TYPE_VIEW_CLICKED && looksLikeCopyAction(event.getSource())) {
                    beginReturnToBbdc();
                } else if (looksLikeCopyConfirmation(event)) {
                    beginReturnToBbdc();
                }
            }
        } else if (BBDC_PACKAGE.equals(currentPackage) && stage == Stage.RETURNING_BBDC) {
            schedulePasteFlow(240);
        }
    }

    @Override public void onInterrupt() {}

    @Override
    public void onDestroy() {
        removeBubble();
        main.removeCallbacksAndMessages(null);
        instance = null;
        super.onDestroy();
    }

    public void refreshBubblePreference() {
        main.post(() -> {
            if (Prefs.floatingEnabled(this)) showBubble();
            else removeBubble();
        });
    }

    public void resetFlow() {
        resetFlowSilently();
        Toast.makeText(this, "已取消本次助记流程", Toast.LENGTH_SHORT).show();
    }

    private void resetFlowSilently() {
        generation++;
        driveScheduled = false;
        targetWord = "";
        setStage(Stage.IDLE);
    }

    private void setStage(Stage next) {
        stage = next;
        stageStartedAt = next == Stage.IDLE ? 0L : SystemClock.elapsedRealtime();
    }

    private void postFlow(long g, long delay, Runnable action) {
        main.postDelayed(() -> { if (g == generation) action.run(); }, delay);
    }

    private void showBubble() {
        if (wm == null || bubble != null) return;
        final int size = dp(54);
        final int reveal = size / 3;
        final int hidden = size - reveal;
        final int screenWidth = getResources().getDisplayMetrics().widthPixels;
        final int screenHeight = getResources().getDisplayMetrics().heightPixels;

        ImageView icon = new ImageView(this);
        byte[] bytes = Base64.decode(OVERLAY_ICON_BASE64, Base64.DEFAULT);
        icon.setImageBitmap(BitmapFactory.decodeByteArray(bytes, 0, bytes.length));
        icon.setScaleType(ImageView.ScaleType.FIT_CENTER);
        icon.setBackgroundColor(Color.TRANSPARENT);
        icon.setContentDescription("助记悬浮桥");

        WindowManager.LayoutParams lp = new WindowManager.LayoutParams(
                size, size,
                WindowManager.LayoutParams.TYPE_ACCESSIBILITY_OVERLAY,
                WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE
                        | WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN
                        | WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS,
                PixelFormat.TRANSLUCENT);
        lp.gravity = Gravity.TOP | Gravity.START;
        int savedX = Prefs.bubbleX(this);
        lp.x = savedX == Integer.MIN_VALUE ? screenWidth - reveal : savedX;
        lp.y = clamp(Prefs.bubbleY(this), 0, Math.max(0, screenHeight - size));

        final float[] down = new float[4];
        final long[] downAt = new long[1];
        final boolean[] moved = new boolean[1];

        icon.setOnTouchListener((v, e) -> {
            if (e.getAction() == MotionEvent.ACTION_DOWN) {
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
            if (e.getAction() == MotionEvent.ACTION_MOVE) {
                float dx = e.getRawX() - down[0];
                float dy = e.getRawY() - down[1];
                if (Math.abs(dx) > dp(7) || Math.abs(dy) > dp(7)) moved[0] = true;
                if (moved[0]) {
                    lp.x = clamp((int) (down[2] + dx), 0, Math.max(0, screenWidth - size));
                    lp.y = clamp((int) (down[3] + dy), 0, Math.max(0, screenHeight - size));
                    updateBubble(v, lp);
                }
                return true;
            }
            if (e.getAction() == MotionEvent.ACTION_UP || e.getAction() == MotionEvent.ACTION_CANCEL) {
                v.animate().scaleX(1f).scaleY(1f).setDuration(100).start();
                long held = SystemClock.elapsedRealtime() - downAt[0];
                if (moved[0]) {
                    Prefs.setBubblePosition(this, lp.x, lp.y);
                } else if (held >= LONG_PRESS_MS) {
                    resetFlow();
                } else if (e.getAction() == MotionEvent.ACTION_UP) {
                    startBridgeFlow();
                }
                scheduleDock(v, lp, size, reveal, hidden);
                return true;
            }
            return false;
        });

        bubble = icon;
        try {
            wm.addView(icon, lp);
            scheduleDock(icon, lp, size, reveal, hidden);
        } catch (Exception e) {
            bubble = null;
        }
    }

    private void cancelDock() {
        if (dockRunnable != null) main.removeCallbacks(dockRunnable);
        dockRunnable = null;
    }

    private void scheduleDock(View view, WindowManager.LayoutParams lp, int size, int reveal, int hidden) {
        cancelDock();
        dockRunnable = () -> {
            if (bubble != view) return;
            int screenWidth = getResources().getDisplayMetrics().widthPixels;
            int center = lp.x + size / 2;
            lp.x = center < screenWidth / 2 ? -hidden : screenWidth - reveal;
            updateBubble(view, lp);
            Prefs.setBubblePosition(this, lp.x, lp.y);
        };
        main.postDelayed(dockRunnable, AUTO_DOCK_MS);
    }

    private void revealBubble(View view, WindowManager.LayoutParams lp, int size, int reveal) {
        int screenWidth = getResources().getDisplayMetrics().widthPixels;
        if (lp.x < 0) lp.x = 0;
        else if (lp.x > screenWidth - size) lp.x = screenWidth - size;
        updateBubble(view, lp);
    }

    private void updateBubble(View view, WindowManager.LayoutParams lp) {
        try { wm.updateViewLayout(view, lp); } catch (Exception ignored) {}
    }

    private void removeBubble() {
        cancelDock();
        if (wm != null && bubble != null) {
            try { wm.removeView(bubble); } catch (Exception ignored) {}
            bubble = null;
        }
    }

    private void startBridgeFlow() {
        if (stage != Stage.IDLE) {
            Toast.makeText(this, "当前自动流程尚未结束，长按图标可取消", Toast.LENGTH_SHORT).show();
            return;
        }
        if (!BBDC_PACKAGE.equals(activePackage())) {
            Toast.makeText(this, "请先回到不背单词的单词学习页", Toast.LENGTH_LONG).show();
            return;
        }
        String word = detectCurrentWord();
        if (word.isEmpty()) {
            Toast.makeText(this, "没有可靠识别到当前英文单词，请稍微滑动页面后重试", Toast.LENGTH_LONG).show();
            return;
        }
        generation++;
        long g = generation;
        targetWord = word;
        setStage(Stage.OPENING_MAIMEMO);
        Intent launch = getPackageManager().getLaunchIntentForPackage(MAIMEMO_PACKAGE);
        if (launch == null) {
            resetFlowSilently();
            Toast.makeText(this, "没有找到墨墨背单词", Toast.LENGTH_LONG).show();
            return;
        }
        launch.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_REORDER_TO_FRONT);
        try {
            startActivity(launch);
            Toast.makeText(this, "识别到：" + targetWord + "，正在打开墨墨…", Toast.LENGTH_SHORT).show();
            postFlow(g, 500, () -> driveMaimemo(g, 0));
        } catch (Exception e) {
            resetFlowSilently();
            Toast.makeText(this, "打开墨墨失败", Toast.LENGTH_LONG).show();
        }
    }

    private void scheduleDriveMaimemo(long delay) {
        if (driveScheduled) return;
        driveScheduled = true;
        long g = generation;
        postFlow(g, delay, () -> {
            driveScheduled = false;
            driveMaimemo(g, 0);
        });
    }

    private void driveMaimemo(long g, int attempt) {
        if (g != generation || (stage != Stage.OPENING_MAIMEMO && stage != Stage.SEARCHING_MAIMEMO)) return;
        if (!MAIMEMO_PACKAGE.equals(activePackage())) {
            retryMaimemo(g, attempt);
            return;
        }
        AccessibilityNodeInfo root = getRootInActiveWindow();
        if (root == null) {
            retryMaimemo(g, attempt);
            return;
        }

        AccessibilityNodeInfo edit = findBestSearchEditable(root);
        if (edit != null) {
            setStage(Stage.SEARCHING_MAIMEMO);
            boolean ok = setText(edit, targetWord);
            edit.recycle();
            root.recycle();
            if (ok) {
                postFlow(g, 600, () -> chooseExactResult(g, 0));
            } else retryMaimemo(g, attempt);
            return;
        }

        AccessibilityNodeInfo search = findClickableByKeywords(root,
                new String[]{"搜索", "查词", "搜词", "搜索单词", "词典", "search"});
        if (search != null) {
            boolean clicked = search.performAction(AccessibilityNodeInfo.ACTION_CLICK);
            search.recycle();
            root.recycle();
            if (clicked) {
                setStage(Stage.SEARCHING_MAIMEMO);
                postFlow(g, 420, () -> driveMaimemo(g, attempt + 1));
            } else retryMaimemo(g, attempt);
            return;
        }
        root.recycle();
        retryMaimemo(g, attempt);
    }

    private void retryMaimemo(long g, int attempt) {
        if (attempt < 9) postFlow(g, 350, () -> driveMaimemo(g, attempt + 1));
        else {
            setStage(Stage.WAITING_COPY);
            Toast.makeText(this, "没识别到墨墨搜索控件，请手动搜索“" + targetWord + "”；复制助记后仍会自动返回", Toast.LENGTH_LONG).show();
        }
    }

    private void chooseExactResult(long g, int attempt) {
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

    private void waitForCopyManual() {
        setStage(Stage.WAITING_COPY);
        Toast.makeText(this, "已把“" + targetWord + "”填入墨墨；若未进入词条，请手动点结果，复制助记后会自动返回", Toast.LENGTH_LONG).show();
    }

    private void beginReturnToBbdc() {
        if (stage != Stage.WAITING_COPY) return;
        long g = generation;
        setStage(Stage.RETURNING_BBDC);
        Toast.makeText(this, "检测到复制，正在返回不背单词…", Toast.LENGTH_SHORT).show();
        performGlobalAction(GLOBAL_ACTION_BACK);
        postFlow(g, 800, () -> returnToBbdc(g, 0));
    }

    private void returnToBbdc(long g, int attempt) {
        if (g != generation || stage != Stage.RETURNING_BBDC) return;
        if (BBDC_PACKAGE.equals(activePackage())) {
            schedulePasteFlow(250);
            return;
        }
        if (attempt == 0) {
            Intent launch = getPackageManager().getLaunchIntentForPackage(BBDC_PACKAGE);
            if (launch != null) {
                launch.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_REORDER_TO_FRONT);
                try { startActivity(launch); } catch (Exception ignored) {}
                postFlow(g, 900, () -> returnToBbdc(g, 1));
                return;
            }
        }
        failPaste("助记已复制，但没有自动回到不背单词");
    }

    private void schedulePasteFlow(long delay) {
        long g = generation;
        setStage(Stage.PASTING);
        postFlow(g, delay, () -> openNoteAndPaste(g, 0));
    }

    private void openNoteAndPaste(long g, int attempt) {
        if (g != generation || stage != Stage.PASTING) return;
        AccessibilityNodeInfo root = getRootInActiveWindow();
        if (root == null || root.getPackageName() == null || !BBDC_PACKAGE.equals(root.getPackageName().toString())) {
            if (root != null) root.recycle();
            if (attempt < 8) postFlow(g, 350, () -> openNoteAndPaste(g, attempt + 1));
            else failPaste("已经返回，但没有找到不背单词当前页面");
            return;
        }

        AccessibilityNodeInfo editor = findBestNoteEditable(root, false);
        if (editor != null) {
            boolean ok = pasteInto(editor);
            editor.recycle();
            root.recycle();
            finishPaste(ok);
            return;
        }

        AccessibilityNodeInfo note = findClickableByKeywords(root,
                new String[]{"添加笔记", "写笔记", "我的笔记", "笔记", "备注"});
        if (note != null) {
            boolean clicked = note.performAction(AccessibilityNodeInfo.ACTION_CLICK);
            note.recycle();
            root.recycle();
            if (clicked) postFlow(g, 500, () -> pasteAfterNoteOpened(g, 0));
            else failPaste("找到了笔记入口，但点击失败");
            return;
        }
        root.recycle();
        if (attempt < 8) postFlow(g, 350, () -> openNoteAndPaste(g, attempt + 1));
        else failPaste("没有找到不背单词的笔记入口");
    }

    private void pasteAfterNoteOpened(long g, int attempt) {
        if (g != generation || stage != Stage.PASTING) return;
        AccessibilityNodeInfo root = getRootInActiveWindow();
        if (root == null) {
            if (attempt < 8) postFlow(g, 350, () -> pasteAfterNoteOpened(g, attempt + 1));
            else failPaste("笔记窗口没有稳定打开");
            return;
        }
        AccessibilityNodeInfo editor = findBestNoteEditable(root, true);
        if (editor == null) {
            root.recycle();
            if (attempt < 8) postFlow(g, 350, () -> pasteAfterNoteOpened(g, attempt + 1));
            else failPaste("没有找到可靠的笔记输入框");
            return;
        }
        boolean ok = pasteInto(editor);
        editor.recycle();
        root.recycle();
        finishPaste(ok);
    }

    private boolean pasteInto(AccessibilityNodeInfo edit) {
        if (edit == null || (!edit.isEditable() && !classContains(edit, "EditText"))) return false;
        edit.performAction(AccessibilityNodeInfo.ACTION_FOCUS);
        edit.performAction(AccessibilityNodeInfo.ACTION_CLICK);
        CharSequence existing = edit.getText();
        if (existing != null && existing.length() > 0) {
            Bundle args = new Bundle();
            args.putInt(AccessibilityNodeInfo.ACTION_ARGUMENT_SELECTION_START_INT, existing.length());
            args.putInt(AccessibilityNodeInfo.ACTION_ARGUMENT_SELECTION_END_INT, existing.length());
            edit.performAction(AccessibilityNodeInfo.ACTION_SET_SELECTION, args);
        }
        return edit.performAction(AccessibilityNodeInfo.ACTION_PASTE);
    }

    private void finishPaste(boolean ok) {
        String word = targetWord;
        resetFlowSilently();
        Toast.makeText(this, ok
                ? "“" + word + "”的助记已粘贴到笔记，请确认保存"
                : "已返回不背单词，但自动粘贴失败；助记仍在剪贴板，可手动粘贴",
                Toast.LENGTH_LONG).show();
    }

    private void failPaste(String reason) {
        resetFlowSilently();
        Toast.makeText(this, reason + "。助记仍在剪贴板，可手动粘贴。", Toast.LENGTH_LONG).show();
    }

    private String detectCurrentWord() {
        AccessibilityNodeInfo root = getRootInActiveWindow();
        if (root == null) return "";
        List<Candidate> candidates = new ArrayList<>();
        collectCandidates(root, candidates, 0);
        root.recycle();
        int sw = getResources().getDisplayMetrics().widthPixels;
        int sh = getResources().getDisplayMetrics().heightPixels;
        Candidate best = null;
        for (Candidate c : candidates) {
            String low = c.word.toLowerCase(Locale.US);
            if (STOP.contains(low) || c.bounds.width() <= 0 || c.bounds.height() <= 0) continue;
            float cx = c.bounds.exactCenterX() / Math.max(1f, sw);
            float cy = c.bounds.exactCenterY() / Math.max(1f, sh);
            float h = c.bounds.height() / Math.max(1f, sh);
            float center = 1f - Math.min(1f, Math.abs(cx - .5f) * 2f);
            float vertical = 1f - Math.min(1f, Math.abs(cy - .30f) / .34f);
            float size = Math.min(1.2f, h / .035f);
            float idBoost = containsAny(c.viewId.toLowerCase(Locale.ROOT), "word", "lexis", "vocab") ? 1f : 0f;
            c.score = center * 2f + vertical * 2.8f + size * 2.3f
                    + (c.standalone ? 2.2f : 0f) + idBoost * 2.2f;
            if (best == null || c.score > best.score) best = c;
        }
        return best == null ? "" : best.word;
    }

    private void collectCandidates(AccessibilityNodeInfo node, List<Candidate> out, int depth) {
        if (node == null || depth > 28) return;
        if (node.isVisibleToUser()) {
            Rect bounds = new Rect();
            node.getBoundsInScreen(bounds);
            extractCandidates(node.getText(), bounds, safeId(node), out);
            extractCandidates(node.getContentDescription(), bounds, safeId(node), out);
        }
        for (int i = 0; i < node.getChildCount(); i++) {
            AccessibilityNodeInfo child = node.getChild(i);
            if (child != null) {
                collectCandidates(child, out, depth + 1);
                child.recycle();
            }
        }
    }

    private void extractCandidates(CharSequence seq, Rect bounds, String id, List<Candidate> out) {
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

    private AccessibilityNodeInfo findBestSearchEditable(AccessibilityNodeInfo root) {
        List<AccessibilityNodeInfo> edits = new ArrayList<>();
        collectEditables(root, edits);
        AccessibilityNodeInfo best = null;
        int bestScore = Integer.MIN_VALUE;
        for (AccessibilityNodeInfo edit : edits) {
            int score = 0;
            String text = nodeText(edit).toLowerCase(Locale.ROOT);
            String id = safeId(edit).toLowerCase(Locale.ROOT);
            if (containsAny(text, "搜索", "search", "查词", "单词")) score += 6;
            if (containsAny(id, "search", "query", "keyword", "word_search")) score += 8;
            if (score > bestScore) {
                if (best != null) best.recycle();
                best = AccessibilityNodeInfo.obtain(edit);
                bestScore = score;
            }
        }
        for (AccessibilityNodeInfo edit : edits) edit.recycle();
        if (bestScore >= 4 || edits.size() == 1) return best;
        if (best != null) best.recycle();
        return null;
    }

    private AccessibilityNodeInfo findBestNoteEditable(AccessibilityNodeInfo root, boolean allowSingle) {
        List<AccessibilityNodeInfo> edits = new ArrayList<>();
        collectEditables(root, edits);
        String page = treeText(root, 1400).toLowerCase(Locale.ROOT);
        boolean noteContext = containsAny(page, "笔记", "备注", "note", "memo");
        AccessibilityNodeInfo best = null;
        int bestScore = Integer.MIN_VALUE;
        for (AccessibilityNodeInfo edit : edits) {
            int score = noteContext ? 2 : 0;
            String text = nodeText(edit).toLowerCase(Locale.ROOT);
            String id = safeId(edit).toLowerCase(Locale.ROOT);
            if (containsAny(text, "笔记", "备注", "note", "memo", "写下")) score += 8;
            if (containsAny(id, "note", "memo", "remark", "comment")) score += 10;
            if (score > bestScore) {
                if (best != null) best.recycle();
                best = AccessibilityNodeInfo.obtain(edit);
                bestScore = score;
            }
        }
        for (AccessibilityNodeInfo edit : edits) edit.recycle();
        if (bestScore >= 6 || (allowSingle && noteContext && edits.size() == 1)) return best;
        if (best != null) best.recycle();
        return null;
    }

    private void collectEditables(AccessibilityNodeInfo node, List<AccessibilityNodeInfo> out) {
        if (node == null) return;
        if (node.isVisibleToUser() && (node.isEditable() || classContains(node, "EditText"))) {
            out.add(AccessibilityNodeInfo.obtain(node));
        }
        for (int i = 0; i < node.getChildCount(); i++) {
            AccessibilityNodeInfo child = node.getChild(i);
            if (child != null) {
                collectEditables(child, out);
                child.recycle();
            }
        }
    }

    private AccessibilityNodeInfo findClickableExactText(AccessibilityNodeInfo node, String exact) {
        if (node == null) return null;
        if (!node.isEditable() && nodeText(node).trim().equalsIgnoreCase(exact)) {
            AccessibilityNodeInfo click = clickableSelfOrParent(node, 4);
            if (click != null && !click.isEditable()) return click;
            if (click != null) click.recycle();
        }
        for (int i = 0; i < node.getChildCount(); i++) {
            AccessibilityNodeInfo child = node.getChild(i);
            if (child == null) continue;
            AccessibilityNodeInfo result = findClickableExactText(child, exact);
            child.recycle();
            if (result != null) return result;
        }
        return null;
    }

    private AccessibilityNodeInfo findClickableByKeywords(AccessibilityNodeInfo node, String[] keys) {
        if (node == null) return null;
        String text = nodeText(node).replace(" ", "").toLowerCase(Locale.ROOT);
        String id = safeId(node).toLowerCase(Locale.ROOT);
        for (String key0 : keys) {
            String key = key0.replace(" ", "").toLowerCase(Locale.ROOT);
            if (text.contains(key) || id.contains(key)) {
                AccessibilityNodeInfo click = clickableSelfOrParent(node, 5);
                if (click != null) return click;
            }
        }
        for (int i = 0; i < node.getChildCount(); i++) {
            AccessibilityNodeInfo child = node.getChild(i);
            if (child == null) continue;
            AccessibilityNodeInfo result = findClickableByKeywords(child, keys);
            child.recycle();
            if (result != null) return result;
        }
        return null;
    }

    private AccessibilityNodeInfo clickableSelfOrParent(AccessibilityNodeInfo node, int maxHops) {
        AccessibilityNodeInfo cur = AccessibilityNodeInfo.obtain(node);
        for (int i = 0; i <= maxHops && cur != null; i++) {
            if (cur.isClickable()) return cur;
            AccessibilityNodeInfo parent = cur.getParent();
            cur.recycle();
            cur = parent;
        }
        return null;
    }

    private boolean looksLikeCopyAction(AccessibilityNodeInfo node) {
        AccessibilityNodeInfo cur = node == null ? null : AccessibilityNodeInfo.obtain(node);
        int hops = 0;
        while (cur != null && hops++ < 6) {
            String text = nodeText(cur).replace(" ", "").toLowerCase(Locale.ROOT);
            String id = safeId(cur).toLowerCase(Locale.ROOT);
            if (text.contains("复制") || text.equals("copy") || id.contains("copy") || id.contains("clipboard")) {
                cur.recycle();
                return true;
            }
            AccessibilityNodeInfo parent = cur.getParent();
            cur.recycle();
            cur = parent;
        }
        return false;
    }

    private boolean looksLikeCopyConfirmation(AccessibilityEvent event) {
        StringBuilder out = new StringBuilder();
        for (CharSequence text : event.getText()) if (text != null) out.append(' ').append(text);
        if (event.getContentDescription() != null) out.append(' ').append(event.getContentDescription());
        String t = out.toString().replace(" ", "").toLowerCase(Locale.ROOT);
        return t.contains("已复制") || t.contains("复制成功") || t.contains("复制到剪贴板")
                || t.contains("copied") || t.contains("copiedtoclipboard");
    }

    private boolean setText(AccessibilityNodeInfo edit, String text) {
        Bundle args = new Bundle();
        args.putCharSequence(AccessibilityNodeInfo.ACTION_ARGUMENT_SET_TEXT_CHARSEQUENCE, text);
        return edit.performAction(AccessibilityNodeInfo.ACTION_SET_TEXT, args);
    }

    private String activePackage() {
        AccessibilityNodeInfo root = getRootInActiveWindow();
        if (root != null) {
            try {
                if (root.getPackageName() != null) return root.getPackageName().toString();
            } finally {
                root.recycle();
            }
        }
        return currentPackage;
    }

    private String nodeText(AccessibilityNodeInfo node) {
        StringBuilder out = new StringBuilder();
        if (node.getText() != null) out.append(node.getText());
        if (node.getHintText() != null) out.append(' ').append(node.getHintText());
        if (node.getContentDescription() != null) out.append(' ').append(node.getContentDescription());
        return out.toString();
    }

    private String treeText(AccessibilityNodeInfo node, int maxChars) {
        StringBuilder out = new StringBuilder();
        appendTreeText(node, out, maxChars);
        return out.toString();
    }

    private void appendTreeText(AccessibilityNodeInfo node, StringBuilder out, int maxChars) {
        if (node == null || out.length() >= maxChars) return;
        String text = nodeText(node);
        if (!text.isEmpty()) out.append(' ').append(text);
        for (int i = 0; i < node.getChildCount() && out.length() < maxChars; i++) {
            AccessibilityNodeInfo child = node.getChild(i);
            if (child != null) {
                appendTreeText(child, out, maxChars);
                child.recycle();
            }
        }
    }

    private String safeId(AccessibilityNodeInfo node) {
        return node.getViewIdResourceName() == null ? "" : node.getViewIdResourceName();
    }

    private boolean classContains(AccessibilityNodeInfo node, String text) {
        return node.getClassName() != null && node.getClassName().toString().contains(text);
    }

    private boolean containsAny(String haystack, String... needles) {
        for (String needle : needles) if (haystack.contains(needle)) return true;
        return false;
    }

    private String normalizeWord(String word) {
        return word.replace('’', '\'').trim();
    }

    private int dp(int value) {
        return (int) (value * getResources().getDisplayMetrics().density + 0.5f);
    }

    private int clamp(int value, int min, int max) {
        return Math.max(min, Math.min(max, value));
    }

    private static final class Candidate {
        final String word;
        final Rect bounds;
        final boolean standalone;
        final String viewId;
        float score;

        Candidate(String word, Rect bounds, boolean standalone, String viewId) {
            this.word = word;
            this.bounds = bounds;
            this.standalone = standalone;
            this.viewId = viewId == null ? "" : viewId;
        }
    }
}
