package net.shocknet.agent;

import android.util.Log;

import org.json.JSONObject;

import java.io.*;
import java.net.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import java.util.concurrent.*;

public class HttpServer implements Runnable {

    private static final String TAG = "ShockNet-HTTP";

    private final int              port;
    private final RequestHandler   handler;
    private       ServerSocket     serverSocket;
    private final ExecutorService  pool = Executors.newCachedThreadPool();
    private volatile boolean       running = false;

    
    private static volatile NotifModel lastNotif = null;

    
    public interface RequestHandler {
        void onNotify(NotifModel notif);
        void onRead(String notifId, String clientIp);
        String getDeviceName();
        String getLocalIp();
        String getAuthToken();
        byte[] takeScreenshot();   
    }

    public HttpServer(int port, RequestHandler handler) {
        this.port    = port;
        this.handler = handler;
    }

    // Arranque 
    @Override
    public void run() {
        try {
            serverSocket = new ServerSocket();
            serverSocket.setReuseAddress(true);
            serverSocket.bind(new InetSocketAddress(port));
            running = true;
            Log.i(TAG, "HTTP server escuchando en puerto " + port);

            while (running) {
                try {
                    
                    Socket client = serverSocket.accept();
                    pool.execute(() -> handleClient(client));
                } catch (SocketException e) {
                    if (running) Log.e(TAG, "Socket error: " + e.getMessage());
                }
            }
        } catch (Exception e) {
            Log.e(TAG, "Server fatal: " + e.getMessage());
        }
    }

    public void stop() {
        running = false;
        pool.shutdownNow();
        try { if (serverSocket != null) serverSocket.close(); } catch (Exception ignored) {}
    }

    public boolean isRunning() { return running; }

    private void handleClient(Socket client) {
        try {
            client.setSoTimeout(4000);
            InputStream  in  = client.getInputStream();
            OutputStream out = client.getOutputStream();

           
            BufferedReader reader = new BufferedReader(
                new InputStreamReader(in, StandardCharsets.UTF_8));

            String requestLine = reader.readLine();
            if (requestLine == null || requestLine.isEmpty()) return;

            
            String[] parts  = requestLine.split(" ");
            if (parts.length < 2) return;
            String method   = parts[0].toUpperCase();
            String fullPath = parts[1];
            String path     = fullPath.contains("?") ? fullPath.split("\\?")[0] : fullPath;

            // Leer resto de cabeceras
            Map<String, String> headers = new LinkedHashMap<>();
            int contentLength = 0;
            String line;
            while ((line = reader.readLine()) != null && !line.isEmpty()) {
                int colon = line.indexOf(':');
                if (colon > 0) {
                    String key = line.substring(0, colon).trim().toLowerCase();
                    String val = line.substring(colon + 1).trim();
                    headers.put(key, val);
                    if (key.equals("content-length")) {
                        try { contentLength = Integer.parseInt(val); } catch (Exception ignored) {}
                    }
                }
            }

            // Leer body si hay
            String body = "";
            if (contentLength > 0) {
                char[] cbuf = new char[contentLength];
                int total = 0;
                while (total < contentLength) {
                    int r = reader.read(cbuf, total, contentLength - total);
                    if (r < 0) break;
                    total += r;
                }
                body = new String(cbuf, 0, total);
            }

            // Autenticación
            String token = handler.getAuthToken();
            if (!token.isEmpty()) {
                String authHeader = headers.getOrDefault("authorization", "");
                if (!authHeader.equals("Bearer " + token)) {
                    sendResponse(out, 401, "application/json",
                        "{\"ok\":false,\"error\":\"Unauthorized\"}");
                    return;
                }
            }

            String clientIp = client.getInetAddress().getHostAddress();
            routeRequest(method, path, body, clientIp, out);

        } catch (Exception e) {
            Log.d(TAG, "Client error: " + e.getMessage());
        } finally {
            try { client.close(); } catch (Exception ignored) {}
        }
    }

    
    private void routeRequest(String method, String path, String body,
                               String clientIp, OutputStream out) throws IOException {

        // GET /ping
        if (method.equals("GET") && path.equals("/ping")) {
            JSONObject resp = new JSONObject();
            try {
                resp.put("ok",   true);
                resp.put("host", handler.getDeviceName());
                resp.put("ip",   handler.getLocalIp());
                resp.put("platform", "android");
                resp.put("version",  "1.0");
            } catch (Exception ignored) {}
            sendJson(out, 200, resp.toString());
            return;
        }

        // POST /notify
        if (method.equals("POST") && path.equals("/notify")) {
            try {
                JSONObject json = new JSONObject(body);
                String notifId  = NotifModel.generateId();
                NotifModel notif = NotifModel.fromJson(json, notifId);
                lastNotif = notif;
                handler.onNotify(notif);
                sendJson(out, 200, "{\"ok\":true,\"id\":\"" + notifId + "\"}");
            } catch (Exception e) {
                sendJson(out, 400, "{\"ok\":false,\"error\":\"" + e.getMessage() + "\"}");
            }
            return;
        }

        // POST /read
        if (method.equals("POST") && path.equals("/read")) {
            try {
                JSONObject json = new JSONObject(body);
                String id = json.optString("id", "");
                if (lastNotif != null && lastNotif.id.equals(id)) {
                    lastNotif.read = true;
                }
                handler.onRead(id, clientIp);
                sendJson(out, 200, "{\"ok\":true}");
            } catch (Exception e) {
                sendJson(out, 400, "{\"ok\":false}");
            }
            return;
        }

        // GET /pwa_check
        if (method.equals("GET") && path.equals("/pwa_check")) {
            if (lastNotif == null) {
                sendJson(out, 200, "{\"id\":null}");
            } else {
                try {
                    sendJson(out, 200, lastNotif.toJson().toString());
                } catch (Exception e) {
                    sendJson(out, 500, "{\"error\":\"json\"}");
                }
            }
            return;
        }

        // GET /status/<id>
        if (method.equals("GET") && path.startsWith("/status/")) {
            String id = path.substring("/status/".length());
            if (lastNotif != null && lastNotif.id.equals(id)) {
                try {
                    sendJson(out, 200, lastNotif.toJson().toString());
                } catch (Exception ignored) {
                    sendJson(out, 200, "{\"ok\":true,\"read\":" + lastNotif.read + "}");
                }
            } else {
                sendJson(out, 200, "{\"ok\":true,\"read\":false}");
            }
            return;
        }

        // GET /screenshot
        if (method.equals("GET") && path.equals("/screenshot")) {
            byte[] img = handler.takeScreenshot();
            if (img != null && img.length > 0) {
                // Devolver JPEG
                String hdr = "HTTP/1.1 200 OK\r\n"
                    + "Content-Type: image/jpeg\r\n"
                    + "Content-Length: " + img.length + "\r\n"
                    + "Connection: close\r\n\r\n";
                out.write(hdr.getBytes(StandardCharsets.UTF_8));
                out.write(img);
                out.flush();
            } else {
                sendJson(out, 503, "{\"error\":\"screenshot_unavailable\"}");
            }
            return;
        }

        // GET /themes
        if (method.equals("GET") && path.equals("/themes")) {
            sendJson(out, 200,
                "{\"cyber\":\"⚡ Cyber\",\"aurora\":\"✦ Aurora\"}");
            return;
        }

        // 404
        sendJson(out, 404, "{\"error\":\"not found\"}");
    }

    private void sendJson(OutputStream out, int code, String body) throws IOException {
        sendResponse(out, code, "application/json; charset=utf-8", body);
    }

    private void sendResponse(OutputStream out, int code, String contentType, String body)
            throws IOException {
        byte[] bytes = body.getBytes(StandardCharsets.UTF_8);
        String statusText = code == 200 ? "OK"
                          : code == 401 ? "Unauthorized"
                          : code == 404 ? "Not Found"
                          : "Error";
        String header = "HTTP/1.1 " + code + " " + statusText + "\r\n"
            + "Content-Type: " + contentType + "\r\n"
            + "Content-Length: " + bytes.length + "\r\n"
            + "Connection: close\r\n"
            + "Access-Control-Allow-Origin: *\r\n"
            + "\r\n";
        out.write(header.getBytes(StandardCharsets.UTF_8));
        out.write(bytes);
        out.flush();
    }

    public static NotifModel getLastNotif() { return lastNotif; }
    public static void clearLastNotif()     { lastNotif = null; }
}
