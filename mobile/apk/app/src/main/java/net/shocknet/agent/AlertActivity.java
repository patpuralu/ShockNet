package net.shocknet.agent;

import android.app.Activity;
import android.content.Intent;
import android.graphics.Color;
import android.graphics.Typeface;
import android.os.*;
import android.view.*;
import android.view.animation.*;
import android.widget.*;
import java.net.*;


public class AlertActivity extends Activity {

    // Extras del Intent
    public static final String EXTRA_NOTIF_ID  = "notif_id";
    public static final String EXTRA_TITLE     = "title";
    public static final String EXTRA_MESSAGE   = "message";
    public static final String EXTRA_THEME     = "theme";
    public static final String EXTRA_IMAGE_URL = "image_url";
    public static final String EXTRA_ENCRYPTED = "encrypted";
    public static final String EXTRA_KIOSK     = "kiosk";

    private String notifId;
    private boolean kiosk;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        
        getWindow().addFlags(
            WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON      |
            WindowManager.LayoutParams.FLAG_TURN_SCREEN_ON      |
            WindowManager.LayoutParams.FLAG_SHOW_WHEN_LOCKED    |
            WindowManager.LayoutParams.FLAG_DISMISS_KEYGUARD
        );

       
        getWindow().getDecorView().setSystemUiVisibility(
            View.SYSTEM_UI_FLAG_LAYOUT_STABLE
            | View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION
            | View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN
            | View.SYSTEM_UI_FLAG_HIDE_NAVIGATION
            | View.SYSTEM_UI_FLAG_FULLSCREEN
            | View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY
        );

        
        notifId         = getIntent().getStringExtra(EXTRA_NOTIF_ID);
        String title    = getIntent().getStringExtra(EXTRA_TITLE);
        String message  = getIntent().getStringExtra(EXTRA_MESSAGE);
        String theme    = getIntent().getStringExtra(EXTRA_THEME);
        boolean encrypted = getIntent().getBooleanExtra(EXTRA_ENCRYPTED, false);
        kiosk           = getIntent().getBooleanExtra(EXTRA_KIOSK, true);

        if (title   == null) title   = "Aviso";
        if (message == null) message = "";
        if (theme   == null) theme   = "cyber";

        if (theme.equals("aurora")) {
            buildAurora(title, message, encrypted);
        } else {
            buildCyber(title, message, encrypted);
        }
    }

    private void buildCyber(String title, String message, boolean encrypted) {
        FrameLayout root = new FrameLayout(this);
        root.setBackgroundColor(Color.BLACK);

        // Scanlines
        View scanlines = new View(this) {
            @Override protected void onDraw(android.graphics.Canvas c) {
                android.graphics.Paint p = new android.graphics.Paint();
                p.setColor(Color.parseColor("#001a1a"));
                p.setStrokeWidth(1f);
                for (int y = 0; y < getHeight(); y += 3)
                    c.drawLine(0, y, getWidth(), y, p);
            }
        };
        scanlines.setLayoutParams(new FrameLayout.LayoutParams(
            FrameLayout.LayoutParams.MATCH_PARENT,
            FrameLayout.LayoutParams.MATCH_PARENT));
        root.addView(scanlines);

        // Glow superior cian
        View glow = new View(this) {
            @Override protected void onDraw(android.graphics.Canvas c) {
                android.graphics.Paint p = new android.graphics.Paint();
                p.setColor(Color.parseColor("#00f0ff"));
                p.setAlpha(18);
                p.setMaskFilter(new android.graphics.BlurMaskFilter(
                    dp(120), android.graphics.BlurMaskFilter.Blur.NORMAL));
                c.drawCircle(getWidth()/2f, 0, dp(200), p);
            }
        };
        glow.setLayoutParams(new FrameLayout.LayoutParams(
            FrameLayout.LayoutParams.MATCH_PARENT,
            FrameLayout.LayoutParams.MATCH_PARENT));
        root.addView(glow);

        // Layout principal
        LinearLayout layout = new LinearLayout(this);
        layout.setOrientation(LinearLayout.VERTICAL);
        layout.setPadding(dp(24), dp(48), dp(24), dp(40));

        // Cabecera de terminal
        LinearLayout termHdr = new LinearLayout(this);
        termHdr.setOrientation(LinearLayout.HORIZONTAL);
        termHdr.setGravity(Gravity.CENTER_VERTICAL);
        termHdr.setPadding(0, 0, 0, dp(16));

        // Dot parpadeante
        View dot = new View(this);
        dot.setBackgroundColor(Color.parseColor("#00f0ff"));
        LinearLayout.LayoutParams dotP = new LinearLayout.LayoutParams(dp(8), dp(8));
        dotP.rightMargin = dp(12);
        dot.setLayoutParams(dotP);
        AlphaAnimation dotBlink = new AlphaAnimation(0.2f, 1f);
        dotBlink.setDuration(700);
        dotBlink.setRepeatMode(Animation.REVERSE);
        dotBlink.setRepeatCount(Animation.INFINITE);
        dot.startAnimation(dotBlink);
        termHdr.addView(dot);

        TextView termLbl = new TextView(this);
        String pid = notifId != null && notifId.length() >= 8
            ? notifId.substring(0, 8) : "00000000";
        termLbl.setText("SHOCKNET :: ALERTA :: " + pid);
        termLbl.setTextColor(Color.parseColor("#003a3a"));
        termLbl.setTextSize(10);
        termLbl.setLetterSpacing(0.1f);
        termHdr.addView(termLbl);
        layout.addView(termHdr);

     
        View hline = new View(this);
        hline.setBackgroundColor(Color.parseColor("#00f0ff"));
        hline.setAlpha(0.15f);
        LinearLayout.LayoutParams hlP = new LinearLayout.LayoutParams(
            LinearLayout.LayoutParams.MATCH_PARENT, 1);
        hlP.bottomMargin = dp(28);
        hline.setLayoutParams(hlP);
        layout.addView(hline);

        // Badge cifrado
        if (encrypted) {
            TextView encBadge = new TextView(this);
            encBadge.setText("// AES-256 ENCRYPTED");
            encBadge.setTextColor(Color.parseColor("#004444"));
            encBadge.setTextSize(9);
            encBadge.setLetterSpacing(0.12f);
            LinearLayout.LayoutParams ebP = new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.WRAP_CONTENT,
                LinearLayout.LayoutParams.WRAP_CONTENT);
            ebP.bottomMargin = dp(12);
            encBadge.setLayoutParams(ebP);
            layout.addView(encBadge);
        }

        
        TextView tvTitle = new TextView(this);
        tvTitle.setText(title.toUpperCase());
        tvTitle.setTextColor(Color.parseColor("#00f0ff"));
        tvTitle.setTextSize(42);
        tvTitle.setTypeface(Typeface.DEFAULT_BOLD);
        tvTitle.setLetterSpacing(0.04f);
        tvTitle.setLineSpacing(dp(-4), 1f);
      
        AnimationSet glitchSet = new AnimationSet(false);
        TranslateAnimation glitch1 = new TranslateAnimation(-dp(2), dp(2), 0, 0);
        glitch1.setDuration(80);
        glitch1.setStartOffset(2000);
        glitch1.setRepeatCount(1);
        glitch1.setRepeatMode(Animation.REVERSE);
        glitchSet.addAnimation(glitch1);
        tvTitle.startAnimation(glitchSet);
        LinearLayout.LayoutParams titleP = new LinearLayout.LayoutParams(
            LinearLayout.LayoutParams.MATCH_PARENT,
            LinearLayout.LayoutParams.WRAP_CONTENT);
        titleP.bottomMargin = dp(28);
        tvTitle.setLayoutParams(titleP);
        layout.addView(tvTitle);

        LinearLayout msgBox = new LinearLayout(this);
        msgBox.setOrientation(LinearLayout.HORIZONTAL);
        msgBox.setPadding(0, 0, 0, dp(32));

        View msgBorder = new View(this);
        msgBorder.setBackgroundColor(Color.parseColor("#00f0ff"));
        msgBorder.setAlpha(0.4f);
        LinearLayout.LayoutParams mbP = new LinearLayout.LayoutParams(dp(2),
            LinearLayout.LayoutParams.MATCH_PARENT);
        mbP.rightMargin = dp(14);
        msgBorder.setLayoutParams(mbP);
        msgBox.addView(msgBorder);

        TextView tvMsg = new TextView(this);
        tvMsg.setText(message);
        tvMsg.setTextColor(Color.parseColor("#007777"));
        tvMsg.setTextSize(14);
        tvMsg.setLineSpacing(dp(3), 1f);
        msgBox.addView(tvMsg);
        layout.addView(msgBox);

        // Spacer
        layout.addView(new View(this), new LinearLayout.LayoutParams(
            0, 0, 1f));

        Button btn = new Button(this);
        btn.setText("> ACK_");
        btn.setTextColor(Color.parseColor("#00f0ff"));
        btn.setTextSize(14);
        btn.setLetterSpacing(0.2f);
        btn.setAllCaps(false);
        btn.setBackgroundColor(Color.TRANSPARENT);
        btn.setTypeface(Typeface.MONOSPACE);
        btn.setBackground(getBorderDrawable("#00f0ff", 1));
        btn.setPadding(dp(28), dp(14), dp(28), dp(14));
        btn.setOnClickListener(v -> acknowledge());
        LinearLayout.LayoutParams btnP = new LinearLayout.LayoutParams(
            LinearLayout.LayoutParams.WRAP_CONTENT,
            LinearLayout.LayoutParams.WRAP_CONTENT);
        btn.setLayoutParams(btnP);
        layout.addView(btn);

        root.addView(layout);
        setContentView(root);
        animateEntrance(layout);
    }

    private void buildAurora(String title, String message, boolean encrypted) {
        FrameLayout root = new FrameLayout(this);
        root.setBackgroundColor(Color.parseColor("#07000e"));

        View aurora = new View(this) {
            @Override protected void onDraw(android.graphics.Canvas c) {
                android.graphics.Paint p = new android.graphics.Paint();
                p.setMaskFilter(new android.graphics.BlurMaskFilter(
                    dp(200), android.graphics.BlurMaskFilter.Blur.NORMAL));
                // esquina superior izquierda
                p.setColor(Color.parseColor("#50009a"));
                p.setAlpha(140);
                c.drawCircle(0, 0, dp(280), p);
                // esquina inferior derecha
                p.setColor(Color.parseColor("#9900cc"));
                p.setAlpha(100);
                c.drawCircle(getWidth(), getHeight(), dp(240), p);
            }
        };
        aurora.setLayoutParams(new FrameLayout.LayoutParams(
            FrameLayout.LayoutParams.MATCH_PARENT,
            FrameLayout.LayoutParams.MATCH_PARENT));
        root.addView(aurora);

        
        LinearLayout layout = new LinearLayout(this);
        layout.setOrientation(LinearLayout.VERTICAL);

    
        LinearLayout topSection = new LinearLayout(this);
        topSection.setOrientation(LinearLayout.VERTICAL);
        topSection.setGravity(Gravity.BOTTOM);
        topSection.setPadding(dp(28), dp(60), dp(28), dp(28));
        topSection.setLayoutParams(new LinearLayout.LayoutParams(
            LinearLayout.LayoutParams.MATCH_PARENT, 0, 1f));

        LinearLayout labelRow = new LinearLayout(this);
        labelRow.setOrientation(LinearLayout.HORIZONTAL);
        labelRow.setGravity(Gravity.CENTER_VERTICAL);
        labelRow.setPadding(0, 0, 0, dp(14));

        View labelLine = new View(this);
        labelLine.setBackgroundColor(Color.parseColor("#c060ff"));
        labelLine.setAlpha(0.5f);
        LinearLayout.LayoutParams llP = new LinearLayout.LayoutParams(dp(20), dp(1));
        llP.rightMargin = dp(10);
        labelLine.setLayoutParams(llP);
        labelRow.addView(labelLine);

        TextView alertLabel = new TextView(this);
        alertLabel.setText("SHOCKNET  //  ALERTA");
        alertLabel.setTextColor(Color.parseColor("#5a0088"));
        alertLabel.setTextSize(10);
        alertLabel.setLetterSpacing(0.22f);
        labelRow.addView(alertLabel);
        topSection.addView(labelRow);

        TextView tvTitle = new TextView(this);
        tvTitle.setText(title.toUpperCase());
        tvTitle.setTextColor(Color.WHITE);
        tvTitle.setTextSize(54);
        tvTitle.setTypeface(Typeface.DEFAULT_BOLD);
        tvTitle.setLetterSpacing(-0.02f);
        tvTitle.setLineSpacing(dp(-6), 1f);
        topSection.addView(tvTitle);

        layout.addView(topSection);

        View divider = new View(this);
        divider.setBackgroundColor(Color.parseColor("#c060ff"));
        divider.setAlpha(0.2f);
        layout.addView(divider, new LinearLayout.LayoutParams(
            LinearLayout.LayoutParams.MATCH_PARENT, dp(1)));

        LinearLayout bottomSection = new LinearLayout(this);
        bottomSection.setOrientation(LinearLayout.VERTICAL);
        bottomSection.setPadding(dp(28), dp(28), dp(28), dp(50));
        bottomSection.setLayoutParams(new LinearLayout.LayoutParams(
            LinearLayout.LayoutParams.MATCH_PARENT, 0, 1f));

        // Badge cifrado
        if (encrypted) {
            TextView encBadge = new TextView(this);
            encBadge.setText("// AES-256");
            encBadge.setTextColor(Color.parseColor("#3a0055"));
            encBadge.setTextSize(9);
            encBadge.setLetterSpacing(0.12f);
            LinearLayout.LayoutParams ebP = new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.WRAP_CONTENT,
                LinearLayout.LayoutParams.WRAP_CONTENT);
            ebP.bottomMargin = dp(14);
            encBadge.setLayoutParams(ebP);
            bottomSection.addView(encBadge);
        }

        // Mensaje
        TextView tvMsg = new TextView(this);
        tvMsg.setText(message);
        tvMsg.setTextColor(Color.parseColor("#7a5a99"));
        tvMsg.setTextSize(15);
        tvMsg.setLineSpacing(dp(4), 1f);
        LinearLayout.LayoutParams msgP = new LinearLayout.LayoutParams(
            LinearLayout.LayoutParams.MATCH_PARENT,
            LinearLayout.LayoutParams.WRAP_CONTENT);
        msgP.bottomMargin = dp(32);
        tvMsg.setLayoutParams(msgP);
        bottomSection.addView(tvMsg);

        // Spacer
        bottomSection.addView(new View(this), new LinearLayout.LayoutParams(0,0,1f));

        Button btn = new Button(this);
        btn.setText("ENTENDIDO");
        btn.setTextColor(Color.parseColor("#d090ff"));
        btn.setTextSize(13);
        btn.setLetterSpacing(0.18f);
        btn.setAllCaps(true);
        btn.setBackground(getBorderDrawable("#c060ff", 1));
        btn.setPadding(dp(36), dp(16), dp(36), dp(16));
        btn.setOnClickListener(v -> acknowledge());
        LinearLayout.LayoutParams btnP = new LinearLayout.LayoutParams(
            LinearLayout.LayoutParams.WRAP_CONTENT,
            LinearLayout.LayoutParams.WRAP_CONTENT);
        btn.setLayoutParams(btnP);
        bottomSection.addView(btn);

        layout.addView(bottomSection);
        root.addView(layout);
        setContentView(root);
        animateEntrance(layout);
    }

    // Animación de entrada 
    private void animateEntrance(View view) {
        AlphaAnimation fadeIn = new AlphaAnimation(0f, 1f);
        fadeIn.setDuration(400);
        fadeIn.setInterpolator(new DecelerateInterpolator());
        TranslateAnimation slideUp = new TranslateAnimation(0, 0, dp(30), 0);
        slideUp.setDuration(400);
        slideUp.setInterpolator(new DecelerateInterpolator(2f));
        AnimationSet set = new AnimationSet(true);
        set.addAnimation(fadeIn);
        set.addAnimation(slideUp);
        view.startAnimation(set);
    }

    // Confirmar lectura y cerrar
    private void acknowledge() {
        // Notificar al servidor HTTP local
        new Thread(() -> {
            try {
                URL url = new URL("http://127.0.0.1:"
                    + Prefs.httpPort(AlertActivity.this) + "/read");
                java.net.HttpURLConnection conn =
                    (java.net.HttpURLConnection) url.openConnection();
                conn.setRequestMethod("POST");
                conn.setDoOutput(true);
                conn.setConnectTimeout(2000);
                conn.setReadTimeout(2000);
                conn.setRequestProperty("Content-Type", "application/json");
                String body = "{\"id\":\"" + (notifId != null ? notifId : "") + "\"}";
                conn.getOutputStream().write(body.getBytes());
                conn.getOutputStream().flush();
                conn.getResponseCode();
                conn.disconnect();
            } catch (Exception ignored) {}
        }).start();

        finish();
        overridePendingTransition(0, android.R.anim.fade_out);
    }

  
    @Override
    public void onBackPressed() {
        if (!kiosk) {
            acknowledge();
        }
        
    }

    @Override
    public void onWindowFocusChanged(boolean hasFocus) {
        super.onWindowFocusChanged(hasFocus);
        if (hasFocus && kiosk) {
            getWindow().getDecorView().setSystemUiVisibility(
                View.SYSTEM_UI_FLAG_HIDE_NAVIGATION
                | View.SYSTEM_UI_FLAG_FULLSCREEN
                | View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY);
        }
    }

    private android.graphics.drawable.GradientDrawable getBorderDrawable(
            String colorHex, int strokeDp) {
        android.graphics.drawable.GradientDrawable gd =
            new android.graphics.drawable.GradientDrawable();
        gd.setColor(Color.TRANSPARENT);
        gd.setStroke(dp(strokeDp), Color.parseColor(colorHex));
        return gd;
    }

    private int dp(int v) {
        return Math.round(v * getResources().getDisplayMetrics().density);
    }
}
