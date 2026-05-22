/// Configuración de conexión al backend.
///
/// Producción: Render cloud (https://rutai-backend.onrender.com)
/// Desarrollo: Descomentar las líneas de localhost/10.0.2.2

class AppConfig {
  // ── Producción (Render) ──
  static const String baseUrl = 'https://rutai-backend.onrender.com';

  // ── Desarrollo local (descomentar si trabajas en local) ──
  // import 'dart:io'; // ← mover al top del archivo si usas esto
  // static String get baseUrl => Platform.isAndroid
  //     ? 'http://10.0.2.2:8000'
  //     : 'http://127.0.0.1:8000';

  static String get wsBaseUrl => baseUrl.replaceFirst('https', 'wss');
}
