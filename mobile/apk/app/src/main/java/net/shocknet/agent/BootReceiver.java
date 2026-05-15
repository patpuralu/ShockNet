package net.shocknet.agent;

import android.content.*;
import android.os.Build;
import android.util.Log;

public class BootReceiver extends BroadcastReceiver {

    private static final String TAG = "ShockNet-Boot";

    @Override
    public void onReceive(Context context, Intent intent) {
        String action = intent.getAction();
        if (action == null) return;

        if (!action.equals(Intent.ACTION_BOOT_COMPLETED)
                && !action.equals(Intent.ACTION_MY_PACKAGE_REPLACED)) return;

        if (!Prefs.autoStart(context)) {
            Log.i(TAG, "Auto-start desactivado — no arrancando el servicio.");
            return;
        }

        Log.i(TAG, "Boot recibido — arrancando AgentService...");

        Intent svc = new Intent(context, AgentService.class);
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            context.startForegroundService(svc);
        } else {
            context.startService(svc);
        }
    }
}
