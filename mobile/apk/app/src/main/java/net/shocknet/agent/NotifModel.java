package net.shocknet.agent;

import org.json.JSONObject;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Locale;

public class NotifModel {

    public final String id;
    public final String title;
    public final String message;
    public final String theme;       // "cyber" | "aurora"
    public final String imageUrl;
    public final boolean encrypted;
    public final String receivedAt;
    public       boolean read;

    public NotifModel(String id, String title, String message,
                      String theme, String imageUrl, boolean encrypted) {
        this.id         = id;
        this.title      = title;
        this.message    = message;
        this.theme      = (theme != null && !theme.isEmpty()) ? theme : "cyber";
        this.imageUrl   = imageUrl != null ? imageUrl : "";
        this.encrypted  = encrypted;
        this.read       = false;
        this.receivedAt = new SimpleDateFormat("HH:mm:ss", Locale.getDefault())
                              .format(new Date());
    }

    public static NotifModel fromJson(JSONObject obj, String notifId) throws Exception {
        return new NotifModel(
            notifId,
            obj.optString("title",     "Aviso"),
            obj.optString("message",   ""),
            obj.optString("theme",     "cyber"),
            obj.optString("image_url", ""),
            obj.optBoolean("_encrypted", false)
        );
    }

    public JSONObject toJson() throws Exception {
        JSONObject o = new JSONObject();
        o.put("id",      id);
        o.put("title",   title);
        o.put("message", message);
        o.put("icon",    theme.equals("aurora") ? "✦" : "⚡");
        o.put("read",    read);
        if (read) o.put("read_at", receivedAt);
        return o;
    }

    public static String generateId() {
        return new SimpleDateFormat("yyyyMMddHHmmssSSS", Locale.getDefault())
                   .format(new Date());
    }
}
