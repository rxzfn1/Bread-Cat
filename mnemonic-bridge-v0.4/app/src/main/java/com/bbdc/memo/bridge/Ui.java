package com.bbdc.memo.bridge;

import android.content.Context;
import android.graphics.Color;
import android.graphics.Typeface;
import android.util.TypedValue;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;

final class Ui {
    private Ui() {}

    static int dp(Context c, int v) {
        return (int) TypedValue.applyDimension(TypedValue.COMPLEX_UNIT_DIP, v, c.getResources().getDisplayMetrics());
    }

    static TextView title(Context c, String text, int sp) {
        TextView v = new TextView(c);
        v.setText(text);
        v.setTextSize(sp);
        v.setTextColor(Color.rgb(24, 24, 27));
        v.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        v.setPadding(0, dp(c, 10), 0, dp(c, 8));
        return v;
    }

    static TextView body(Context c, String text) {
        TextView v = new TextView(c);
        v.setText(text);
        v.setTextSize(14);
        v.setTextColor(Color.rgb(82, 82, 91));
        v.setLineSpacing(0, 1.18f);
        v.setPadding(0, dp(c, 6), 0, dp(c, 8));
        return v;
    }

    static Button button(Context c, String text) {
        Button b = new Button(c);
        b.setText(text);
        b.setAllCaps(false);
        b.setTextSize(14);
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, dp(c, 50));
        lp.setMargins(0, dp(c, 6), 0, dp(c, 6));
        b.setLayoutParams(lp);
        return b;
    }
}
