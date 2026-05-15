package net.shocknet.agent;

import android.app.*;
import android.content.Intent;
import android.content.SharedPreferences;
import android.os.*;
import android.util.Log;

import androidx.core.app.NotificationCompat;

import org.json.*;
import java.io.*;
import java.net.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicBoolean;

public class ShockNetService extends Service {

    private static final String TAG          = "ShockNet";
    private static final String CHANNEL_ID   = "shocknet_idle";
    private static final String CHANNEL_ACTIVE= "shocknet_alert";
    static  final String PREFS              = "ShockNetPrefs";
    static  final String PREF_AGENT_IP      = "agent_ip";
    static  final String PREF_AGENT_PORT    = "agent_port";
    static  final String PREF_UDP_PORT      = "udp_port";
    static  final String PREF_SLEEP_MIN     = "sleep_min";

    // Valores por defecto
    private static final int    DEFAULT_HTTP_PORT  = 9999;
    private static final int    DEFAULT_UDP_PORT   = 9998;
    private static final int    DEFAULT_SLEEP_MIN  = 5;
    private static final int    POLL_INTERVAL_MS   = 3_000;

    private SharedPreferences  prefs;
    private final AtomicBoolean active    = new AtomicBoolean(false);
    private final AtomicBoolean running   = new AtomicBoolean(false);

    private DatagramSocket    udpSocket;
    private ScheduledExecutorService scheduler;
    private ScheduledFuture<?> pollFuture;
    private ScheduledFuture<?> sleepFuture;
    private String lastNotifId = "";
    private long   lastMsgTime = 0;

    // ─────────────────────────────────────────────────────────
    @Override
    public void onCreate() {
        super.onCreate();
        prefs = getSharedPreferences(PREFS, MODE_PRIVATE);
        createChannels();
        scheduler = Executors.newScheduledThreadPool(2);
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        if (!running.getAndSet(true)) {
            startForeground(1, buildIdleNotification());
            new Thread(this::listenUDP, "shocknet-udp").start();
            Log.i(TAG, "Servicio iniciado — modo DORMIDO");
        }
        return START_STICKY;  
    }

    @Override
    public IBinder onBind(Intent intent) { return null; }

    @Override
    public void onDestroy() {
        running.set(false);
        if (udpSocket != null) udpSocket.close();
        if (scheduler  != null) scheduler.shutdownNow();
        super.onDestroy();
    }

    private void listenUDP() {
        int udpPort = prefs.getInt(PREF_UDP_PORT, DEFAULT_UDP_PORT);
        try {
            udpSocket = new DatagramSocket(udpPort);
            udpSocket.setSoTimeout(0);  // bloquea indefinidamente
            byte[] buf = new byte[64];
            DatagramPacket pkt = new DatagramPacket(buf, buf.length);

            Log.i(TAG, "UDP escuchando en puerto " + udpPort);

            while (running.get()) {
                try {
                    udpSocket.receive(pkt);   // BLOQUEADO aquí = 0% CPU
                    String msg = new String(pkt.getData(), 0, pkt.getLength()).trim();
                    Log.i(TAG, "UDP wake-up recibido: " + msg + " de " + pkt.getAddress());

                    // El launcher puede enviar la IP del agente en el paquete
                    // Formato: "SHOCK:<ip_agente>" o simplemente "SHOCK"
                    if (msg.startsWith("SHOCK")) {
                        if (msg.contains(":") && msg.split(":").length > 1) {
                            String newIp = msg.split(":")[1].trim();
                            if (!newIp.isEmpty()) {
                                prefs.edit().putString(PREF_AGENT_IP, newIp).apply();
                                Log.i(TAG, "IP agente actualizada: " + newIp);
                            }
                        }
                        wakeUp();
                    }
                } catch (SocketTimeoutException ignored) {
                } catch (SocketException e) {
                    if (running.get()) Log.e(TAG, "UDP error: " + e.getMessage());
                }
            }
        } catch (Exception e) {
            Log.e(TAG, "UDP listener fallo: " + e.getMessage());
        }
    }

    private synchronized void wakeUp() {
        if (active.getAndSet(true)) {
            
            resetSleepTimer();
            return;
        }
        Log.i(TAG, "ACTIVO — iniciando polling HTTP");
        updateNotification("⚡ Activo — escuchando avisos", true);
        lastMsgTime = System.currentTimeMillis();

        pollFuture = scheduler.scheduleWithFixedDelay(
            this::pollAgent, 0, POLL_INTERVAL_MS, TimeUnit.MILLISECONDS);

        resetSleepTimer();
    }

    private synchronized void resetSleepTimer() {
        if (sleepFuture != null) sleepFuture.cancel(false);
        long sleepMs = prefs.getInt(PREF_SLEEP_MIN, DEFAULT_SLEEP_MIN) * 60_000L;
        sleepFuture = scheduler.schedule(this::goSleep, sleepMs, TimeUnit.MILLISECONDS);
    }

    private synchronized void goSleep() {
        if (!active.getAndSet(false)) return;
        Log.i(TAG, "DORMIDO — volviendo a modo pasivo");
        if (pollFuture != null) { pollFuture.cancel(false); pollFuture = null; }
        updateNotification("En espera…", false);
    }

    // POLL AGENT — consulta /pwa_check 
    private void pollAgent() {
        String ip   = prefs.getString(PREF_AGENT_IP, "");
        int    port = prefs.getInt(PREF_AGENT_PORT, DEFAULT_HTTP_PORT);
        if (ip.isEmpty()) return;

        try {
            URL url = new URL("http://" + ip + ":" + port + "/pwa_check");
            HttpURLConnection conn = (HttpURLConnection) url.openConnection();
            conn.setConnectTimeout(2500);
            conn.setReadTimeout(2500);
            conn.setRequestMethod("GET");
            int code = conn.getResponseCode();
            if (code == 200) {
                BufferedReader br = new BufferedReader(
                    new InputStreamReader(conn.getInputStream()));
                StringBuilder sb = new StringBuilder();
                String line;
                while ((line = br.readLine()) != null) sb.append(line);
                br.close();
                conn.disconnect();
                handlePwaCheck(sb.toString());
            } else {
                conn.disconnect();
            }
        } catch (Exception e) {
            Log.d(TAG, "Poll error: " + e.getMessage());
        }
    }

    private void handlePwaCheck(String json) {
        try {
            JSONObject obj = new JSONObject(json);
            String id = obj.optString("id", "");
            if (id == null || id.equals("null") || id.isEmpty()) return;
            if (id.equals(lastNotifId)) return;  // ya lo mostramos

            lastNotifId = id;
            lastMsgTime = System.currentTimeMillis();
            resetSleepTimer();

            String title   = obj.optString("title",   "Aviso ShockNet");
            String message = obj.optString("message", "");
            String icon    = obj.optString("icon",    "⚡");

            Log.i(TAG, "Nuevo aviso recibido: " + title);
            launchAlert(id, title, message, icon);

        } catch (JSONException e) {
            Log.e(TAG, "JSON parse error: " + e.getMessage());
        }
    }

    // LANZAR ALERTA a pantalla completa 
    private void launchAlert(String id, String title, String message, String icon) {
        
        Intent fullScreenIntent = new Intent(this, AlertActivity.class);
        fullScreenIntent.putExtra("notif_id", id);
        fullScreenIntent.putExtra("title",    title);
        fullScreenIntent.putExtra("message",  message);
        fullScreenIntent.putExtra("icon",     icon);
        fullScreenIntent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK
                | Intent.FLAG_ACTIVITY_CLEAR_TOP
                | Intent.FLAG_ACTIVITY_SINGLE_TOP);

        PendingIntent pi = PendingIntent.getActivity(
            this, 0, fullScreenIntent,
            PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);

        Notification notif = new NotificationCompat.Builder(this, CHANNEL_ACTIVE)
            .setSmallIcon(android.R.drawable.ic_dialog_alert)
            .setContentTitle("⚡ " + title)
            .setContentText(message)
            .setPriority(NotificationCompat.PRIORITY_MAX)
            .setCategory(NotificationCompat.CATEGORY_ALARM)
            .setFullScreenIntent(pi, true)
            .setAutoCancel(true)
            .build();

        NotificationManager nm = getSystemService(NotificationManager.class);
        nm.notify(2, notif);

        startActivity(fullScreenIntent);
    }

    //  UTILIDADES 
    private void createChannels() {
        NotificationManager nm = getSystemService(NotificationManager.class);

        NotificationChannel idle = new NotificationChannel(
            CHANNEL_ID, "ShockNet — En espera",
            NotificationManager.IMPORTANCE_MIN);
        idle.setDescription("Icono discreto mientras el agente está dormido");
        idle.setShowBadge(false);

        NotificationChannel alert = new NotificationChannel(
            CHANNEL_ACTIVE, "ShockNet — Alertas",
            NotificationManager.IMPORTANCE_HIGH);
        alert.setDescription("Avisos recibidos del launcher");
        alert.enableVibration(true);
        alert.setBypassDnd(true);

        nm.createNotificationChannel(idle);
        nm.createNotificationChannel(alert);
    }

    private Notification buildIdleNotification() {
        return new NotificationCompat.Builder(this, CHANNEL_ID)
            .setSmallIcon(android.R.drawable.ic_menu_send)
            .setContentTitle("ShockNet Agent")
            .setContentText("En espera — sin consumo de recursos")
            .setPriority(NotificationCompat.PRIORITY_MIN)
            .setSilent(true)
            .build();
    }

    private void updateNotification(String text, boolean active) {
        Notification n = new NotificationCompat.Builder(this, CHANNEL_ID)
            .setSmallIcon(active
                ? android.R.drawable.ic_menu_send
                : android.R.drawable.ic_menu_send)
            .setContentTitle("ShockNet Agent")
            .setContentText(text)
            .setPriority(NotificationCompat.PRIORITY_MIN)
            .setSilent(true)
            .build();
        startForeground(1, n);
    }

    public static void sendWakeUp(String agentIp, int udpPort) {
        new Thread(() -> {
            try {
                DatagramSocket s = new DatagramSocket();
                s.setBroadcast(true);
                byte[] msg = ("SHOCK:" + agentIp).getBytes();
                DatagramPacket pkt = new DatagramPacket(
                    msg, msg.length,
                    InetAddress.getByName("255.255.255.255"), udpPort);
                s.send(pkt);
                s.close();
            } catch (Exception e) {
                Log.e(TAG, "WakeUp send error: " + e.getMessage());
            }
        }).start();
    }
}
