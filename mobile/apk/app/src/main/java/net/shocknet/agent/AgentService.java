package net.shocknet.agent;

import android.app.*;
import android.content.*;
import android.net.wifi.WifiManager;
import android.os.*;
import android.util.Log;

import androidx.core.app.NotificationCompat;

import java.net.*;
import java.util.Enumeration;
import java.util.concurrent.atomic.AtomicBoolean;


public class AgentService extends Service implements HttpServer.RequestHandler {

    private static final String TAG          = "ShockNet-Service";
    private static final String CHANNEL_IDLE = "shocknet_idle";
    private static final String CHANNEL_ALERT= "shocknet_alert";

    // Broadcast interno para comunicar con MainActivity
    public static final String ACTION_STATUS = "net.shocknet.agent.STATUS";
    public static final String EXTRA_IP      = "ip";
    public static final String EXTRA_PORT    = "port";
    public static final String EXTRA_RUNNING = "running";

    private HttpServer        httpServer;
    private Thread            serverThread;
    private WifiManager.WifiLock wifiLock;
    private Handler           mainHandler;
    private final AtomicBoolean running = new AtomicBoolean(false);

    // Ciclo de vida 
    @Override
    public void onCreate() {
        super.onCreate();
        mainHandler = new Handler(Looper.getMainLooper());
        createNotificationChannels();

        
        WifiManager wifiMgr = (WifiManager) getApplicationContext()
            .getSystemService(Context.WIFI_SERVICE);
        if (wifiMgr != null) {
            wifiLock = wifiMgr.createWifiLock(
                WifiManager.WIFI_MODE_FULL_HIGH_PERF, "ShockNetWifiLock");
        }
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        if (running.getAndSet(true)) {
            
            broadcastStatus();
            return START_STICKY;
        }

        startForeground(1, buildIdleNotification());

        if (wifiLock != null && !wifiLock.isHeld()) wifiLock.acquire();

        int port = Prefs.httpPort(this);
        httpServer = new HttpServer(port, this);
        serverThread = new Thread(httpServer, "shocknet-http");
        serverThread.setDaemon(true);
        serverThread.start();

        Prefs.setBool(this, Prefs.SERVICE_RUNNING, true);
        Log.i(TAG, "AgentService iniciado en puerto " + port);

        broadcastStatus();
        return START_STICKY;  
    }

    @Override
    public void onDestroy() {
        running.set(false);
        if (httpServer  != null) httpServer.stop();
        if (serverThread != null) serverThread.interrupt();
        if (wifiLock != null && wifiLock.isHeld()) wifiLock.release();
        Prefs.setBool(this, Prefs.SERVICE_RUNNING, false);
        broadcastStatus();
        super.onDestroy();
    }

    @Override
    public IBinder onBind(Intent intent) { return null; }

  
    @Override
    public byte[] takeScreenshot() {

        return null;
    }

    @Override
    public void onNotify(NotifModel notif) {
        Log.i(TAG, "Aviso recibido: " + notif.title);
        updateForegroundNotif("⚡ " + notif.title, notif.message);

        
        mainHandler.post(() -> {
            Intent alert = buildAlertIntent(notif);
            
            alert.setFlags(
                Intent.FLAG_ACTIVITY_NEW_TASK        |
                Intent.FLAG_ACTIVITY_CLEAR_TOP       |
                Intent.FLAG_ACTIVITY_SINGLE_TOP      |
                Intent.FLAG_ACTIVITY_NO_USER_ACTION
            );
            startActivity(alert);
        });

    
        showAlertNotification(notif);

        // 3. Sonido / vibración
        if (Prefs.soundEnabled(this)) {
            mainHandler.post(this::vibrate);
        }
    }

    @Override
    public void onRead(String notifId, String clientIp) {
        Log.i(TAG, "Aviso " + notifId + " marcado como leído desde " + clientIp);
        // Volver a notificación de idle
        mainHandler.postDelayed(() ->
            startForeground(1, buildIdleNotification()), 2000);
    }

    @Override
    public String getDeviceName() {
        return Prefs.deviceName(this);
    }

    @Override
    public String getLocalIp() {
        return getWifiIp();
    }

    @Override
    public String getAuthToken() {
        return Prefs.authToken(this);
    }

    // Utilidades de red
    public static String getWifiIp() {
        try {
            Enumeration<NetworkInterface> interfaces =
                NetworkInterface.getNetworkInterfaces();
            while (interfaces.hasMoreElements()) {
                NetworkInterface iface = interfaces.nextElement();
                Enumeration<InetAddress> addrs = iface.getInetAddresses();
                while (addrs.hasMoreElements()) {
                    InetAddress addr = addrs.nextElement();
                    if (!addr.isLoopbackAddress()
                            && addr instanceof Inet4Address) {
                        return addr.getHostAddress();
                    }
                }
            }
        } catch (Exception e) {
            Log.e(TAG, "getWifiIp: " + e.getMessage());
        }
        return "0.0.0.0";
    }

  
    private void broadcastStatus() {
        Intent i = new Intent(ACTION_STATUS);
        i.putExtra(EXTRA_IP,      getWifiIp());
        i.putExtra(EXTRA_PORT,    Prefs.httpPort(this));
        i.putExtra(EXTRA_RUNNING, running.get());
        sendBroadcast(i);
    }

    // Vibración 
    private void vibrate() {
        Vibrator v = (Vibrator) getSystemService(Context.VIBRATOR_SERVICE);
        if (v == null || !v.hasVibrator()) return;
        long[] pattern = {0, 200, 100, 200, 100, 400};
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            v.vibrate(VibrationEffect.createWaveform(pattern, -1));
        } else {
            v.vibrate(pattern, -1);
        }
    }

    // Notificaciones 
    private void createNotificationChannels() {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.O) return;
        NotificationManager nm = getSystemService(NotificationManager.class);

       
        NotificationChannel idle = new NotificationChannel(
            CHANNEL_IDLE,
            getString(R.string.notif_channel_idle),
            NotificationManager.IMPORTANCE_MIN);
        idle.setShowBadge(false);
        idle.setSound(null, null);

        
        NotificationChannel alert = new NotificationChannel(
            CHANNEL_ALERT,
            getString(R.string.notif_channel_alert),
            NotificationManager.IMPORTANCE_HIGH);
        alert.enableVibration(true);
        alert.setBypassDnd(true);
        alert.setShowBadge(true);

        nm.createNotificationChannel(idle);
        nm.createNotificationChannel(alert);
    }

    private Notification buildIdleNotification() {
        String ip   = getWifiIp();
        int    port = Prefs.httpPort(this);
        return new NotificationCompat.Builder(this, CHANNEL_IDLE)
            .setSmallIcon(R.drawable.ic_shock_notif)
            .setContentTitle(getString(R.string.notif_idle_title))
            .setContentText(getString(R.string.notif_idle_text, ip, port))
            .setPriority(NotificationCompat.PRIORITY_MIN)
            .setSilent(true)
            .setOngoing(true)
            .build();
    }

    private void updateForegroundNotif(String title, String text) {
        Notification n = new NotificationCompat.Builder(this, CHANNEL_IDLE)
            .setSmallIcon(R.drawable.ic_shock_notif)
            .setContentTitle(title)
            .setContentText(text)
            .setPriority(NotificationCompat.PRIORITY_LOW)
            .setSilent(true)
            .setOngoing(true)
            .build();
        startForeground(1, n);
    }

    private Intent buildAlertIntent(NotifModel notif) {
        Intent i = new Intent(this, AlertActivity.class);
        i.putExtra(AlertActivity.EXTRA_NOTIF_ID,  notif.id);
        i.putExtra(AlertActivity.EXTRA_TITLE,     notif.title);
        i.putExtra(AlertActivity.EXTRA_MESSAGE,   notif.message);
        i.putExtra(AlertActivity.EXTRA_THEME,     notif.theme);
        i.putExtra(AlertActivity.EXTRA_IMAGE_URL, notif.imageUrl);
        i.putExtra(AlertActivity.EXTRA_ENCRYPTED, notif.encrypted);
        i.putExtra(AlertActivity.EXTRA_KIOSK,     Prefs.kioskMode(this));
        return i;
    }

    private void showAlertNotification(NotifModel notif) {
        Intent fullScreenIntent = buildAlertIntent(notif);
        fullScreenIntent.setFlags(
            Intent.FLAG_ACTIVITY_NEW_TASK |
            Intent.FLAG_ACTIVITY_CLEAR_TOP |
            Intent.FLAG_ACTIVITY_NO_USER_ACTION);

        
        PendingIntent pi = PendingIntent.getActivity(
            this, notif.id.hashCode(), fullScreenIntent,
            PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);

        Notification n = new NotificationCompat.Builder(this, CHANNEL_ALERT)
            .setSmallIcon(R.drawable.ic_shock_notif)
            .setContentTitle("⚡ " + notif.title)
            .setContentText(notif.message)
            .setPriority(NotificationCompat.PRIORITY_MAX)
            .setCategory(NotificationCompat.CATEGORY_CALL)   
            .setVisibility(NotificationCompat.VISIBILITY_PUBLIC)
            .setFullScreenIntent(pi, true)                   
            .setOngoing(false)
            .setAutoCancel(true)
            .build();

        NotificationManager nm = getSystemService(NotificationManager.class);
        if (nm != null) nm.notify(notif.id.hashCode(), n);
    }
}
