package net.shocknet.agent;

import android.app.*;
import android.content.*;
import android.graphics.Color;
import android.net.Uri;
import android.os.*;
import android.provider.Settings;
import android.view.*;
import android.view.animation.*;
import android.widget.*;

public class MainActivity extends Activity {

    private TextView  tvStatus, tvIp, tvPort;
    private Button    btnToggle;
    private EditText  etDeviceName, etHttpPort, etAuthToken, etSleepMin;
    private Switch    swAutoStart, swSound, swKiosk;
    private View      statusDot;
    private BroadcastReceiver statusReceiver;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        // Pantalla completa oscura
        getWindow().setStatusBarColor(Color.BLACK);
        getWindow().setNavigationBarColor(Color.parseColor("#0f0f0f"));

        buildUI();
        registerStatusReceiver();

        // Comprobar si el servicio ya estaba corriendo
        boolean wasRunning = Prefs.getBool(this, Prefs.SERVICE_RUNNING, false);
        updateUI(wasRunning, AgentService.getWifiIp(), Prefs.httpPort(this));

        // Pedir permiso de notificaciones (Android 13+)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            requestPermissions(new String[]{
                android.Manifest.permission.POST_NOTIFICATIONS}, 100);
        }
    }

    @Override
    protected void onResume() {
        super.onResume();
        boolean running = Prefs.getBool(this, Prefs.SERVICE_RUNNING, false);
        updateUI(running, AgentService.getWifiIp(), Prefs.httpPort(this));
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
        if (statusReceiver != null) unregisterReceiver(statusReceiver);
    }

    //Build UI 
    private void buildUI() {
        ScrollView root = new ScrollView(this);
        root.setBackgroundColor(Color.parseColor("#080808"));
        root.setFillViewport(true);

        LinearLayout layout = new LinearLayout(this);
        layout.setOrientation(LinearLayout.VERTICAL);
        layout.setBackgroundColor(Color.parseColor("#080808"));

        //  Barra superior
        View topBar = new View(this);
        topBar.setBackgroundColor(Color.parseColor("#E8192C"));
        layout.addView(topBar, new LinearLayout.LayoutParams(
            LinearLayout.LayoutParams.MATCH_PARENT, dp(3)));

        // Header 
        LinearLayout header = new LinearLayout(this);
        header.setOrientation(LinearLayout.VERTICAL);
        header.setBackgroundColor(Color.parseColor("#0f0f0f"));
        header.setPadding(dp(20), dp(20), dp(20), dp(18));

        // Logo row
        LinearLayout logoRow = new LinearLayout(this);
        logoRow.setOrientation(LinearLayout.HORIZONTAL);
        logoRow.setGravity(Gravity.CENTER_VERTICAL);
        logoRow.setPadding(0, 0, 0, dp(4));

        TextView shock = makeTv("SHOCK", 22, Color.parseColor("#E8192C"), true);
        shock.setLetterSpacing(0.06f);
        TextView net   = makeTv("NET",   22, Color.WHITE, true);
        net.setLetterSpacing(0.06f);
        TextView agent = makeTv("  //  AGENT", 11, Color.parseColor("#444444"), false);
        agent.setLetterSpacing(0.1f);
        logoRow.addView(shock);
        logoRow.addView(net);
        logoRow.addView(agent);
        header.addView(logoRow);

        // Estado en el header
        LinearLayout stRow = new LinearLayout(this);
        stRow.setOrientation(LinearLayout.HORIZONTAL);
        stRow.setGravity(Gravity.CENTER_VERTICAL);
        stRow.setPadding(0, dp(10), 0, 0);

        statusDot = new View(this);
        statusDot.setBackgroundColor(Color.parseColor("#333333"));
        LinearLayout.LayoutParams dotP = new LinearLayout.LayoutParams(dp(8), dp(8));
        dotP.rightMargin = dp(10);
        statusDot.setLayoutParams(dotP);
        stRow.addView(statusDot);

        tvStatus = makeTv(getString(R.string.status_stopped), 12, Color.parseColor("#555555"), false);
        tvStatus.setLetterSpacing(0.06f);
        stRow.addView(tvStatus);
        header.addView(stRow);

        // IP y puerto
        tvIp   = makeTv("IP: —", 11, Color.parseColor("#444444"), false);
        tvPort = makeTv("", 11, Color.parseColor("#333333"), false);
        LinearLayout.LayoutParams ipP = new LinearLayout.LayoutParams(
            LinearLayout.LayoutParams.MATCH_PARENT, LinearLayout.LayoutParams.WRAP_CONTENT);
        ipP.topMargin = dp(6);
        tvIp.setLayoutParams(ipP);
        header.addView(tvIp);
        header.addView(tvPort);

        layout.addView(header);

        // Separador 
        addDivider(layout);

        // Botón inicio / parada 
        LinearLayout btnSection = new LinearLayout(this);
        btnSection.setPadding(dp(20), dp(20), dp(20), dp(16));
        btnSection.setBackgroundColor(Color.parseColor("#080808"));

        btnToggle = new Button(this);
        btnToggle.setText(getString(R.string.btn_start));
        btnToggle.setTextColor(Color.WHITE);
        btnToggle.setTextSize(13);
        btnToggle.setLetterSpacing(0.14f);
        btnToggle.setAllCaps(true);
        btnToggle.setBackgroundColor(Color.parseColor("#E8192C"));
        btnToggle.setPadding(dp(20), dp(14), dp(20), dp(14));
        btnToggle.setOnClickListener(v -> toggleService());
        btnSection.addView(btnToggle, new LinearLayout.LayoutParams(
            LinearLayout.LayoutParams.MATCH_PARENT,
            LinearLayout.LayoutParams.WRAP_CONTENT));
        layout.addView(btnSection);

        addDivider(layout);

        //  Sección: Dispositivo 
        addSectionTitle(layout, getString(R.string.section_device));
        etDeviceName = addField(layout, getString(R.string.label_device_name),
            Prefs.deviceName(this),
            android.text.InputType.TYPE_CLASS_TEXT);
        etHttpPort   = addField(layout, getString(R.string.label_http_port),
            String.valueOf(Prefs.httpPort(this)),
            android.text.InputType.TYPE_CLASS_NUMBER);

        addDivider(layout);

        // Sección: Seguridad
        addSectionTitle(layout, getString(R.string.section_security));
        etAuthToken = addField(layout, getString(R.string.label_auth_token),
            Prefs.authToken(this),
            android.text.InputType.TYPE_CLASS_TEXT |
            android.text.InputType.TYPE_TEXT_VARIATION_PASSWORD);
        addInfo(layout, getString(R.string.info_auth_token));

        addDivider(layout);

        //  Sección: Comportamiento
        addSectionTitle(layout, getString(R.string.section_behavior));
        etSleepMin = addField(layout, getString(R.string.label_sleep_min),
            String.valueOf(Prefs.sleepMin(this)),
            android.text.InputType.TYPE_CLASS_NUMBER);

        swAutoStart = addSwitch(layout, getString(R.string.sw_auto_start),
            Prefs.autoStart(this));
        swSound     = addSwitch(layout, getString(R.string.sw_sound),
            Prefs.soundEnabled(this));
        swKiosk     = addSwitch(layout, getString(R.string.sw_kiosk),
            Prefs.kioskMode(this));
        addInfo(layout, getString(R.string.info_kiosk));

        addDivider(layout);

        //  Botón guardar
        LinearLayout saveRow = new LinearLayout(this);
        saveRow.setPadding(dp(20), dp(16), dp(20), dp(16));
        Button btnSave = new Button(this);
        btnSave.setText(getString(R.string.btn_save));
        btnSave.setTextColor(Color.parseColor("#E8192C"));
        btnSave.setTextSize(12);
        btnSave.setLetterSpacing(0.12f);
        btnSave.setAllCaps(true);
        btnSave.setBackgroundColor(Color.parseColor("#111111"));
        btnSave.setPadding(dp(20), dp(12), dp(20), dp(12));
        btnSave.setOnClickListener(v -> saveAndRestart());
        saveRow.addView(btnSave, new LinearLayout.LayoutParams(
            LinearLayout.LayoutParams.MATCH_PARENT,
            LinearLayout.LayoutParams.WRAP_CONTENT));
        layout.addView(saveRow);

        addDivider(layout);

        //  Sección: Info
        addSectionTitle(layout, getString(R.string.section_info));
        addInfo(layout, getString(R.string.info_how_it_works));

        // Versión y créditos
        TextView credits = makeTv("ShockNet Agent v1.0  //  github.com/patpuralu/ShockNet",
            10, Color.parseColor("#2a2a2a"), false);
        credits.setGravity(Gravity.CENTER);
        LinearLayout.LayoutParams cP = new LinearLayout.LayoutParams(
            LinearLayout.LayoutParams.MATCH_PARENT,
            LinearLayout.LayoutParams.WRAP_CONTENT);
        cP.topMargin = dp(24); cP.bottomMargin = dp(32);
        credits.setLayoutParams(cP);
        layout.addView(credits);

        root.addView(layout);
        setContentView(root);
    }

    // Lógica
    private void toggleService() {
        boolean running = Prefs.getBool(this, Prefs.SERVICE_RUNNING, false);
        if (running) {
            stopService(new Intent(this, AgentService.class));
            Prefs.setBool(this, Prefs.SERVICE_RUNNING, false);
            updateUI(false, "", Prefs.httpPort(this));
        } else {
            saveConfig();
            startForegroundService(new Intent(this, AgentService.class));
            Prefs.setBool(this, Prefs.SERVICE_RUNNING, true);
            
            new Handler(Looper.getMainLooper()).postDelayed(() -> {
                updateUI(true, AgentService.getWifiIp(), Prefs.httpPort(this));
                animateStatusDot();
            }, 600);
        }
    }

    private void saveConfig() {
        try {
            String name = etDeviceName.getText().toString().trim();
            int    port = Integer.parseInt(etHttpPort.getText().toString().trim());
            String tok  = etAuthToken.getText().toString().trim();
            int    slp  = Integer.parseInt(etSleepMin.getText().toString().trim());

            Prefs.setString(this, Prefs.DEVICE_NAME,   name.isEmpty() ? Prefs.DEF_DEVICE_NAME : name);
            Prefs.setInt   (this, Prefs.HTTP_PORT,      Math.max(1024, Math.min(65535, port)));
            Prefs.setString(this, Prefs.AUTH_TOKEN,     tok);
            Prefs.setInt   (this, Prefs.SLEEP_MIN,      Math.max(1, slp));
            Prefs.setBool  (this, Prefs.AUTO_START,     swAutoStart.isChecked());
            Prefs.setBool  (this, Prefs.SOUND_ENABLED,  swSound.isChecked());
            Prefs.setBool  (this, Prefs.KIOSK_MODE,     swKiosk.isChecked());
        } catch (NumberFormatException e) {
            Toast.makeText(this, getString(R.string.error_invalid_port),
                Toast.LENGTH_SHORT).show();
        }
    }

    private void saveAndRestart() {
        saveConfig();
        Toast.makeText(this, getString(R.string.toast_saved), Toast.LENGTH_SHORT).show();
        boolean running = Prefs.getBool(this, Prefs.SERVICE_RUNNING, false);
        if (running) {
            // Reiniciar el servicio para aplicar nueva config
            stopService(new Intent(this, AgentService.class));
            new Handler(Looper.getMainLooper()).postDelayed(() ->
                startForegroundService(new Intent(this, AgentService.class)), 500);
        }
    }

    private void updateUI(boolean running, String ip, int port) {
        if (statusDot == null) return;
        if (running) {
            statusDot.setBackgroundColor(Color.parseColor("#00d46a"));
            tvStatus.setText(getString(R.string.status_running));
            tvStatus.setTextColor(Color.parseColor("#00d46a"));
            tvIp.setText("IP: " + ip);
            tvIp.setTextColor(Color.parseColor("#555555"));
            tvPort.setText("PORT: " + port + "  //  " + ip + ":" + port);
            tvPort.setTextColor(Color.parseColor("#333333"));
            btnToggle.setText(getString(R.string.btn_stop));
            btnToggle.setBackgroundColor(Color.parseColor("#1a0000"));
            btnToggle.setTextColor(Color.parseColor("#E8192C"));
        } else {
            statusDot.setBackgroundColor(Color.parseColor("#333333"));
            tvStatus.setText(getString(R.string.status_stopped));
            tvStatus.setTextColor(Color.parseColor("#555555"));
            tvIp.setText("IP: —");
            tvIp.setTextColor(Color.parseColor("#333333"));
            tvPort.setText("");
            btnToggle.setText(getString(R.string.btn_start));
            btnToggle.setBackgroundColor(Color.parseColor("#E8192C"));
            btnToggle.setTextColor(Color.WHITE);
        }
    }

    private void animateStatusDot() {
        AlphaAnimation pulse = new AlphaAnimation(0.2f, 1f);
        pulse.setDuration(600);
        pulse.setRepeatMode(Animation.REVERSE);
        pulse.setRepeatCount(4);
        statusDot.startAnimation(pulse);
    }

    private void registerStatusReceiver() {
        statusReceiver = new BroadcastReceiver() {
            @Override
            public void onReceive(Context ctx, Intent intent) {
                boolean running = intent.getBooleanExtra(AgentService.EXTRA_RUNNING, false);
                String  ip      = intent.getStringExtra(AgentService.EXTRA_IP);
                int     port    = intent.getIntExtra(AgentService.EXTRA_PORT, 9999);
                updateUI(running, ip != null ? ip : "", port);
            }
        };
        IntentFilter filter = new IntentFilter(AgentService.ACTION_STATUS);
        registerReceiver(statusReceiver, filter, Context.RECEIVER_NOT_EXPORTED);
    }

    // UI Helpers
    private TextView makeTv(String text, float size, int color, boolean bold) {
        TextView tv = new TextView(this);
        tv.setText(text);
        tv.setTextSize(size);
        tv.setTextColor(color);
        if (bold) tv.setTypeface(android.graphics.Typeface.DEFAULT_BOLD);
        return tv;
    }

    private void addSectionTitle(LinearLayout parent, String text) {
        TextView tv = new TextView(this);
        tv.setText(text);
        tv.setTextColor(Color.parseColor("#E8192C"));
        tv.setTextSize(10);
        tv.setLetterSpacing(0.14f);
        tv.setTypeface(android.graphics.Typeface.DEFAULT_BOLD);
        LinearLayout.LayoutParams p = new LinearLayout.LayoutParams(
            LinearLayout.LayoutParams.MATCH_PARENT,
            LinearLayout.LayoutParams.WRAP_CONTENT);
        p.setMargins(dp(20), dp(20), dp(20), dp(6));
        tv.setLayoutParams(p);
        parent.addView(tv);
    }

    private EditText addField(LinearLayout parent, String hint, String value, int inputType) {
        LinearLayout wrap = new LinearLayout(this);
        wrap.setOrientation(LinearLayout.VERTICAL);
        wrap.setPadding(dp(20), dp(6), dp(20), dp(6));
        wrap.setBackgroundColor(Color.parseColor("#080808"));

        TextView lbl = new TextView(this);
        lbl.setText(hint);
        lbl.setTextColor(Color.parseColor("#555555"));
        lbl.setTextSize(10);
        lbl.setLetterSpacing(0.06f);
        wrap.addView(lbl);

        EditText et = new EditText(this);
        et.setText(value);
        et.setInputType(inputType);
        et.setTextColor(Color.WHITE);
        et.setHintTextColor(Color.parseColor("#333333"));
        et.setTextSize(14);
        et.setBackgroundColor(Color.parseColor("#0f0f0f"));
        et.setPadding(dp(12), dp(10), dp(12), dp(10));
        LinearLayout.LayoutParams ep = new LinearLayout.LayoutParams(
            LinearLayout.LayoutParams.MATCH_PARENT,
            LinearLayout.LayoutParams.WRAP_CONTENT);
        ep.topMargin = dp(4);
        et.setLayoutParams(ep);
        wrap.addView(et);
        parent.addView(wrap);
        return et;
    }

    private Switch addSwitch(LinearLayout parent, String text, boolean checked) {
        LinearLayout row = new LinearLayout(this);
        row.setOrientation(LinearLayout.HORIZONTAL);
        row.setGravity(Gravity.CENTER_VERTICAL);
        row.setPadding(dp(20), dp(12), dp(20), dp(12));
        row.setBackgroundColor(Color.parseColor("#080808"));

        TextView tv = new TextView(this);
        tv.setText(text);
        tv.setTextColor(Color.parseColor("#999999"));
        tv.setTextSize(13);
        tv.setLayoutParams(new LinearLayout.LayoutParams(0,
            LinearLayout.LayoutParams.WRAP_CONTENT, 1f));
        row.addView(tv);

        Switch sw = new Switch(this);
        sw.setChecked(checked);
        sw.setThumbTintList(android.content.res.ColorStateList.valueOf(
            Color.parseColor("#E8192C")));
        row.addView(sw);
        parent.addView(row);

        // Separador interno sutil
        View sep = new View(this);
        sep.setBackgroundColor(Color.parseColor("#111111"));
        parent.addView(sep, new LinearLayout.LayoutParams(
            LinearLayout.LayoutParams.MATCH_PARENT, 1));

        return sw;
    }

    private void addInfo(LinearLayout parent, String text) {
        TextView tv = new TextView(this);
        tv.setText(text);
        tv.setTextColor(Color.parseColor("#3a3a3a"));
        tv.setTextSize(11);
        tv.setLineSpacing(dp(2), 1f);
        LinearLayout.LayoutParams p = new LinearLayout.LayoutParams(
            LinearLayout.LayoutParams.MATCH_PARENT,
            LinearLayout.LayoutParams.WRAP_CONTENT);
        p.setMargins(dp(20), dp(8), dp(20), dp(8));
        tv.setLayoutParams(p);
        parent.addView(tv);
    }

    private void addDivider(LinearLayout parent) {
        View d = new View(this);
        d.setBackgroundColor(Color.parseColor("#141414"));
        parent.addView(d, new LinearLayout.LayoutParams(
            LinearLayout.LayoutParams.MATCH_PARENT, dp(1)));
    }

    private int dp(int v) {
        return Math.round(v * getResources().getDisplayMetrics().density);
    }
}
