package net.shocknet.agent;

import android.animation.ValueAnimator;
import android.app.Activity;
import android.content.Intent;
import android.graphics.Color;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.view.*;
import android.view.animation.*;
import android.widget.*;


public class SplashActivity extends Activity {

    private static final int SPLASH_DURATION_MS = 2500;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        getWindow().setFlags(
            WindowManager.LayoutParams.FLAG_FULLSCREEN,
            WindowManager.LayoutParams.FLAG_FULLSCREEN);
        getWindow().getDecorView().setSystemUiVisibility(
            View.SYSTEM_UI_FLAG_FULLSCREEN | View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN);

        buildUI();

       
        new Handler(Looper.getMainLooper()).postDelayed(() -> {
            Intent intent = new Intent(SplashActivity.this, MainActivity.class);
            startActivity(intent);
            overridePendingTransition(android.R.anim.fade_in, android.R.anim.fade_out);
            finish();
        }, SPLASH_DURATION_MS);
    }

    private void buildUI() {
        FrameLayout root = new FrameLayout(this);
        root.setBackgroundColor(Color.BLACK);

        View bgLines = new View(this) {
            @Override
            protected void onDraw(android.graphics.Canvas canvas) {
                super.onDraw(canvas);
                android.graphics.Paint p = new android.graphics.Paint();
                p.setColor(Color.parseColor("#E8192C"));
                p.setAlpha(18);
                p.setStrokeWidth(1f);
                int h = getHeight(), w = getWidth();
                for (int y = 0; y < h; y += 3) {
                    canvas.drawLine(0, y, w, y, p);
                }
            }
        };
        bgLines.setLayoutParams(new FrameLayout.LayoutParams(
            FrameLayout.LayoutParams.MATCH_PARENT,
            FrameLayout.LayoutParams.MATCH_PARENT));
        root.addView(bgLines);

        // Contenedor
        LinearLayout center = new LinearLayout(this);
        center.setOrientation(LinearLayout.VERTICAL);
        center.setGravity(Gravity.CENTER);
        FrameLayout.LayoutParams centerParams = new FrameLayout.LayoutParams(
            FrameLayout.LayoutParams.MATCH_PARENT,
            FrameLayout.LayoutParams.MATCH_PARENT);
        center.setLayoutParams(centerParams);

        View topBar = new View(this);
        topBar.setBackgroundColor(Color.parseColor("#E8192C"));
        LinearLayout.LayoutParams barP = new LinearLayout.LayoutParams(
            dp(80), dp(3));
        barP.gravity = Gravity.CENTER_HORIZONTAL;
        barP.bottomMargin = dp(32);
        topBar.setLayoutParams(barP);
        center.addView(topBar);

        // SHOCK (rojo) 
        TextView shock = new TextView(this);
        shock.setText("SHOCK");
        shock.setTextColor(Color.parseColor("#E8192C"));
        shock.setTextSize(52);
        shock.setTypeface(android.graphics.Typeface.DEFAULT_BOLD);
        shock.setGravity(Gravity.CENTER);
        shock.setLetterSpacing(0.1f);
        LinearLayout.LayoutParams shockP = new LinearLayout.LayoutParams(
            LinearLayout.LayoutParams.MATCH_PARENT,
            LinearLayout.LayoutParams.WRAP_CONTENT);
        shockP.bottomMargin = dp(-8);
        shock.setLayoutParams(shockP);
        center.addView(shock);

        // NET (blanco) 
        TextView net = new TextView(this);
        net.setText("NET");
        net.setTextColor(Color.WHITE);
        net.setTextSize(52);
        net.setTypeface(android.graphics.Typeface.DEFAULT_BOLD);
        net.setGravity(Gravity.CENTER);
        net.setLetterSpacing(0.1f);
        center.addView(net);

        TextView sub = new TextView(this);
        sub.setText(getString(R.string.splash_subtitle));
        sub.setTextColor(Color.parseColor("#444444"));
        sub.setTextSize(11);
        sub.setGravity(Gravity.CENTER);
        sub.setLetterSpacing(0.2f);
        LinearLayout.LayoutParams subP = new LinearLayout.LayoutParams(
            LinearLayout.LayoutParams.MATCH_PARENT,
            LinearLayout.LayoutParams.WRAP_CONTENT);
        subP.topMargin = dp(18);
        sub.setLayoutParams(subP);
        center.addView(sub);
 
        View loadBar = new View(this);
        loadBar.setBackgroundColor(Color.parseColor("#E8192C"));
        LinearLayout.LayoutParams loadP = new LinearLayout.LayoutParams(0, dp(2));
        loadP.gravity = Gravity.CENTER_HORIZONTAL;
        loadP.topMargin = dp(40);
        loadBar.setLayoutParams(loadP);
        center.addView(loadBar);

        root.addView(center);

        TextView version = new TextView(this);
        version.setText("v1.0  //  AGENT");
        version.setTextColor(Color.parseColor("#333333"));
        version.setTextSize(10);
        version.setLetterSpacing(0.12f);
        version.setGravity(Gravity.CENTER);
        FrameLayout.LayoutParams vp = new FrameLayout.LayoutParams(
            FrameLayout.LayoutParams.MATCH_PARENT,
            FrameLayout.LayoutParams.WRAP_CONTENT,
            Gravity.BOTTOM | Gravity.CENTER_HORIZONTAL);
        vp.bottomMargin = dp(32);
        version.setLayoutParams(vp);
        root.addView(version);

        setContentView(root);

        AnimationSet shockAnim = new AnimationSet(true);
        TranslateAnimation shockSlide = new TranslateAnimation(0,0, dp(40),0);
        shockSlide.setDuration(600);
        AlphaAnimation shockFade = new AlphaAnimation(0f, 1f);
        shockFade.setDuration(600);
        shockAnim.addAnimation(shockSlide);
        shockAnim.addAnimation(shockFade);
        shockAnim.setInterpolator(new DecelerateInterpolator(2f));
        shock.startAnimation(shockAnim);

        AnimationSet netAnim = new AnimationSet(true);
        TranslateAnimation netSlide = new TranslateAnimation(0,0, dp(40),0);
        netSlide.setDuration(600); netSlide.setStartOffset(100);
        AlphaAnimation netFade = new AlphaAnimation(0f,1f);
        netFade.setDuration(600); netFade.setStartOffset(100);
        netAnim.addAnimation(netSlide); netAnim.addAnimation(netFade);
        netAnim.setInterpolator(new DecelerateInterpolator(2f));
        net.startAnimation(netAnim);

        AlphaAnimation subAnim = new AlphaAnimation(0f, 1f);
        subAnim.setDuration(500); subAnim.setStartOffset(500);
        subAnim.setFillAfter(true);
        sub.setAlpha(0f); sub.startAnimation(subAnim);
        
        loadBar.post(() -> {
            int targetWidth = dp(120);
            ValueAnimator barAnim = ValueAnimator.ofInt(0, targetWidth);
            barAnim.setDuration(SPLASH_DURATION_MS - 400);
            barAnim.setStartDelay(400);
            barAnim.setInterpolator(new DecelerateInterpolator());
            barAnim.addUpdateListener(va -> {
                LinearLayout.LayoutParams lp = (LinearLayout.LayoutParams) loadBar.getLayoutParams();
                lp.width = (int) va.getAnimatedValue();
                loadBar.setLayoutParams(lp);
            });
            barAnim.start();
        });

        AlphaAnimation barFade = new AlphaAnimation(0f, 1f);
        barFade.setDuration(400);
        topBar.startAnimation(barFade);

        AlphaAnimation verAnim = new AlphaAnimation(0f, 1f);
        verAnim.setDuration(400); verAnim.setStartOffset(800); verAnim.setFillAfter(true);
        version.setAlpha(0f); version.startAnimation(verAnim);
    }

    private int dp(int v) {
        return Math.round(v * getResources().getDisplayMetrics().density);
    }
}
