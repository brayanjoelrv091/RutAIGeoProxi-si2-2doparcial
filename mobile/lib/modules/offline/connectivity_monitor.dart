import 'dart:async';

/// P8 · CU-21 — Monitor de conectividad de red.
///
/// Provee un Stream<bool> reactivo que emite true/false
/// según el estado de la conexión a internet.
///
/// Nota: En Flutter mobile real se usaría el paquete `connectivity_plus`.
/// Esta implementación es un wrapper ligero que funciona sin dependencias
/// externas adicionales, usando ping HTTP como fallback.

import 'package:http/http.dart' as http;
import '../../config.dart';

class ConnectivityMonitor {
  final _controller = StreamController<bool>.broadcast();
  Timer? _pollTimer;
  bool _lastState = true;

  /// Stream reactivo del estado de conexión.
  Stream<bool> get onConnectivityChanged => _controller.stream;

  /// Estado actual de conexión.
  bool get isOnline => _lastState;

  /// Inicia el monitoreo periódico (polling cada 10s).
  void startMonitoring({Duration interval = const Duration(seconds: 10)}) {
    _pollTimer?.cancel();
    _checkNow(); // Check inmediato
    _pollTimer = Timer.periodic(interval, (_) => _checkNow());
  }

  /// Detiene el monitoreo.
  void stopMonitoring() {
    _pollTimer?.cancel();
    _pollTimer = null;
  }

  /// Verifica la conectividad ahora.
  Future<bool> checkNow() async {
    return _checkNow();
  }

  Future<bool> _checkNow() async {
    try {
      final response = await http
          .get(Uri.parse('${AppConfig.apiBaseUrl}/'))
          .timeout(const Duration(seconds: 5));

      final isOnline = response.statusCode == 200;
      _updateState(isOnline);
      return isOnline;
    } catch (_) {
      _updateState(false);
      return false;
    }
  }

  void _updateState(bool newState) {
    if (newState != _lastState) {
      _lastState = newState;
      _controller.add(newState);
      print('[ConnectivityMonitor] Estado: ${newState ? "ONLINE ✅" : "OFFLINE ❌"}');
    }
  }

  void dispose() {
    stopMonitoring();
    _controller.close();
  }
}
