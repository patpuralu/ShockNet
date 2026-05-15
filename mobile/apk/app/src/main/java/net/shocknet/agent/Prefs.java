package net.shocknet.agent;

import android.content.Context;
import android.content.SharedPreferences;


public class Prefs {

    // Nombre del fichero de preferencias 
    private static final String FILE = "ShockNetPrefs";

    // Claves 
    public static final String HTTP_PORT    = "http_port";      // puerto HTTP del servidor local
    public static final String DEVICE_NAME  = "device_name";   // nombre que muestra el launcher en /ping
    public static final String AUTH_TOKEN   = "auth_token";    // token de seguridad (vacío = sin auth)
    public static final String AUTO_START   = "auto_start";    // arrancar al encender el móvil
    public static final String SLEEP_MIN    = "sleep_min";     // minutos de inactividad antes de sleep
    public static final String SOUND_ENABLED= "sound_enabled"; // vibrar/sonar al recibir aviso
    public static final String KIOSK_MODE   = "kiosk_mode";   // bloquear pantalla hasta confirmar
    public static final String LANGUAGE     = "language";      // "es" | "en"
    public static final String SERVICE_RUNNING = "svc_running"; // estado del servicio

    // Valores por defecto 
    public static final int    DEF_HTTP_PORT   = 9999;
    public static final int    DEF_SLEEP_MIN   = 10;
    public static final String DEF_DEVICE_NAME = "ShockNet Android";
    public static final String DEF_LANGUAGE    = "es";

    // Métodos de acceso 
    public static SharedPreferences get(Context ctx) {
        return ctx.getSharedPreferences(FILE, Context.MODE_PRIVATE);
    }

    public static int    getInt(Context ctx, String key, int def)       { return get(ctx).getInt(key, def); }
    public static String getString(Context ctx, String key, String def) { return get(ctx).getString(key, def); }
    public static boolean getBool(Context ctx, String key, boolean def) { return get(ctx).getBoolean(key, def); }

    public static void setInt(Context ctx, String key, int v)      { get(ctx).edit().putInt(key, v).apply(); }
    public static void setString(Context ctx, String key, String v) { get(ctx).edit().putString(key, v).apply(); }
    public static void setBool(Context ctx, String key, boolean v)  { get(ctx).edit().putBoolean(key, v).apply(); }

    // Getters con defaults incorporados 
    public static int     httpPort(Context ctx)    { return getInt(ctx, HTTP_PORT, DEF_HTTP_PORT); }
    public static String  deviceName(Context ctx)  { return getString(ctx, DEVICE_NAME, DEF_DEVICE_NAME); }
    public static String  authToken(Context ctx)   { return getString(ctx, AUTH_TOKEN, ""); }
    public static boolean autoStart(Context ctx)   { return getBool(ctx, AUTO_START, false); }
    public static int     sleepMin(Context ctx)    { return getInt(ctx, SLEEP_MIN, DEF_SLEEP_MIN); }
    public static boolean soundEnabled(Context ctx){ return getBool(ctx, SOUND_ENABLED, true); }
    public static boolean kioskMode(Context ctx)   { return getBool(ctx, KIOSK_MODE, true); }
    public static String  language(Context ctx)    { return getString(ctx, LANGUAGE, DEF_LANGUAGE); }
}
