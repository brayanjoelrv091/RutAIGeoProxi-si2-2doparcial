import 'dart:async';
import 'package:geolocator/geolocator.dart';
import 'websocket_service.dart';

/// P8 · CU-26 — Streaming GPS en vivo + envío por WebSocket.
///
/// Características:
///   - Solicita permisos de ubicación
///   - Streaming de posición cada 3 segundos
///   - Envía automáticamente por WebSocket
///   - Incluye velocidad, heading y precisión
///   - Se detiene al llamar stopTracking()

class GPSTracker {
  final WebSocketService _ws;
  StreamSubscription<Position>? _positionSub;
  bool _isTracking = false;
  Position? _lastPosition;

  final _positionController = StreamController<Position>.broadcast();

  /// Stream local de posiciones para el UI.
  Stream<Position> get positions => _positionController.stream;

  /// ¿Está trackeando?
  bool get isTracking => _isTracking;

  /// Última posición conocida.
  Position? get lastPosition => _lastPosition;

  GPSTracker(this._ws);

  // ══════════════════════════════════════════════════════════════════
  // PUBLIC API
  // ══════════════════════════════════════════════════════════════════

  /// Inicia el tracking GPS y envía posiciones por WebSocket.
  Future<bool> startTracking({String role = 'tecnico'}) async {
    // Verificar permisos
    final hasPermission = await _checkPermissions();
    if (!hasPermission) return false;

    _isTracking = true;

    // Configuración del stream de ubicación
    const locationSettings = LocationSettings(
      accuracy: LocationAccuracy.high,
      distanceFilter: 10, // Metros mínimos entre actualizaciones
    );

    _positionSub = Geolocator.getPositionStream(
      locationSettings: locationSettings,
    ).listen(
      (Position position) {
        _lastPosition = position;
        _positionController.add(position);

        // Enviar por WebSocket
        _ws.sendLocationUpdate(
          lat: position.latitude,
          lng: position.longitude,
          role: role,
          precisionM: position.accuracy,
          velocidadKmh: (position.speed * 3.6), // m/s → km/h
          heading: position.heading,
        );
      },
      onError: (error) {
        print('[GPSTracker] Error de GPS: $error');
      },
    );

    print('[GPSTracker] Tracking iniciado como $role');
    return true;
  }

  /// Detiene el tracking GPS.
  void stopTracking() {
    _positionSub?.cancel();
    _positionSub = null;
    _isTracking = false;
    print('[GPSTracker] Tracking detenido');
  }

  void dispose() {
    stopTracking();
    _positionController.close();
  }

  // ══════════════════════════════════════════════════════════════════
  // PERMISSIONS
  // ══════════════════════════════════════════════════════════════════

  Future<bool> _checkPermissions() async {
    bool serviceEnabled = await Geolocator.isLocationServiceEnabled();
    if (!serviceEnabled) {
      print('[GPSTracker] Servicio de ubicación desactivado');
      return false;
    }

    LocationPermission permission = await Geolocator.checkPermission();
    if (permission == LocationPermission.denied) {
      permission = await Geolocator.requestPermission();
      if (permission == LocationPermission.denied) {
        print('[GPSTracker] Permiso de ubicación denegado');
        return false;
      }
    }

    if (permission == LocationPermission.deniedForever) {
      print('[GPSTracker] Permiso de ubicación denegado permanentemente');
      return false;
    }

    return true;
  }
}
