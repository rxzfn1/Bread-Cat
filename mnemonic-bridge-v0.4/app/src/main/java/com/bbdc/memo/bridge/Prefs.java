package com.bbdc.memo.bridge;

import android.content.Context;
import android.content.SharedPreferences;

final class Prefs {
    private static final String FILE = "bridge_prefs";
    private static final String KEY_FLOAT = "float_enabled";
    private static final String KEY_BUBBLE_X = "bubble_x";
    private static final String KEY_BUBBLE_Y = "bubble_y";

    private Prefs() {}

    private static SharedPreferences sp(Context c) {
        return c.getSharedPreferences(FILE, Context.MODE_PRIVATE);
    }

    static boolean floatingEnabled(Context c) {
        return sp(c).getBoolean(KEY_FLOAT, true);
    }

    static void setFloatingEnabled(Context c, boolean value) {
        sp(c).edit().putBoolean(KEY_FLOAT, value).apply();
    }

    static int bubbleX(Context c) {
        return sp(c).getInt(KEY_BUBBLE_X, Integer.MIN_VALUE);
    }

    static int bubbleY(Context c) {
        return sp(c).getInt(KEY_BUBBLE_Y, dp(c, 240));
    }

    static void setBubblePosition(Context c, int x, int y) {
        sp(c).edit().putInt(KEY_BUBBLE_X, x).putInt(KEY_BUBBLE_Y, y).apply();
    }

    private static int dp(Context c, int v) {
        return (int) (v * c.getResources().getDisplayMetrics().density + 0.5f);
    }
}
