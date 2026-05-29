import 'dart:async';
import 'dart:convert';
import 'package:web_socket_channel/web_socket_channel.dart';
import '../../config.dart';

/// P8 · CU-24 — Servicio WebSocket bidireccional con auto-reconnect.
///
/// Características:
///   - Reconexión automática con backoff exponencial
///   - Heartbeat cada 30s
///   - Buffer de mensajes durante desconexión
///   - Tipos de evento: state_change, location_update, notification, heartbeat

enum WSConnectionState { connecting, connected, disconnected, reconnecting }

class WebSocketService {
  WebSocketChannel? _channel;
  Timer? _heartbeatTimer;
  Timer? _reconnectTimer;

  final _messageController = StreamController<Map<String, dynamic>>.broadcast();
  final _stateController = StreamController<WSConnectionState>.broadcast();
  final List<Map<String, dynamic>> _pendingMessages = [];

  String _url = '';
  String _token = '';
  int _reconnectAttempts = 0;
  static const int _maxReconnectAttempts = 10;
  bool _intentionalClose = false;

  /// Stream de mensajes entrantes.
  Stream<Map<String, dynamic>> get messages => _messageController.stream;

  /// Stream de estado de conexión.
  Stream<WSConnectionState> get connectionState => _stateController.stream;

  /// ¿Está conectado?
  bool get isConnected => _channel != null;

  // ══════════════════════════════════════════════════════════════════
  // PUBLIC API
  // ══════════════════════════════════════════════════════════════════

  /// Conecta al canal de un incidente específico.
  void connectToIncident(int incidentId, String token) {
    _token = token;
    final wsBase = AppConfig.apiBaseUrl.replaceFirst('http', 'ws');
    _url = '$wsBase/realtime/ws/incidents/$incidentId?token=$token';
    _connect();
  }

  /// Conecta al canal de notificaciones de un usuario.
  void connectToNotifications(int userId, String token) {
    _token = token;
    final wsBase = AppConfig.apiBaseUrl.replaceFirst('http', 'ws');
    _url = '$wsBase/realtime/ws/notifications/$userId?token=$token';
    _connect();
  }

  /// Envía un mensaje. Si no hay conexión, lo encola.
  void send(Map<String, dynamic> message) {
    if (_channel != null) {
      _channel!.sink.add(jsonEncode(message));
    } else {
      _pendingMessages.add(message);
    }
  }

  /// Envía una actualización de ubicación GPS.
  void sendLocationUpdate({
    required double lat,
    required double lng,
    String role = 'tecnico',
    double? precisionM,
    double? velocidadKmh,
    double? heading,
  }) {
    send({
      'type': 'location_update',
      'lat': lat,
      'lng': lng,
      'role': role,
      'precision_m': precisionM,
      'velocidad_kmh': velocidadKmh,
      'heading': heading,
    });
  }

  /// Envía una solicitud de cambio de estado.
  void sendStateChange(String nuevoEstado, {String? notas}) {
    send({
      'type': 'state_change',
      'nuevo_estado': nuevoEstado,
      'notas': notas,
    });
  }

  /// Desconecta limpiamente.
  void disconnect() {
    _intentionalClose = true;
    _heartbeatTimer?.cancel();
    _reconnectTimer?.cancel();
    _channel?.sink.close(1000, 'Client disconnect');
    _channel = null;
    _stateController.add(WSConnectionState.disconnected);
  }

  void dispose() {
    disconnect();
    _messageController.close();
    _stateController.close();
  }

  // ══════════════════════════════════════════════════════════════════
  // INTERNALS
  // ══════════════════════════════════════════════════════════════════

  void _connect() {
    if (_url.isEmpty) return;

    _intentionalClose = false;
    _stateController.add(WSConnectionState.connecting);

    try {
      _channel = WebSocketChannel.connect(Uri.parse(_url));

      _channel!.stream.listen(
        (data) {
          _stateController.add(WSConnectionState.connected);
          _reconnectAttempts = 0;
          _startHeartbeat();

          try {
            final message = jsonDecode(data as String) as Map<String, dynamic>;
            _messageController.add(message);
          } catch (e) {
            print('[WebSocketService] Error parseando mensaje: $e');
          }
        },
        onDone: () {
          _channel = null;
          _heartbeatTimer?.cancel();
          _stateController.add(WSConnectionState.disconnected);

          if (!_intentionalClose) {
            _scheduleReconnect();
          }
        },
        onError: (error) {
          print('[WebSocketService] Error: $error');
          _channel = null;
          _stateController.add(WSConnectionState.disconnected);

          if (!_intentionalClose) {
            _scheduleReconnect();
          }
        },
      );

      // Flush mensajes pendientes
      _flushPending();

    } catch (e) {
      print('[WebSocketService] Error de conexión: $e');
      _stateController.add(WSConnectionState.disconnected);
      _scheduleReconnect();
    }
  }

  void _scheduleReconnect() {
    if (_reconnectAttempts >= _maxReconnectAttempts || _intentionalClose) {
      print('[WebSocketService] Max reconexiones alcanzado o cierre intencional.');
      return;
    }

    _stateController.add(WSConnectionState.reconnecting);
    final delay = Duration(
      milliseconds: (1000 * (1 << _reconnectAttempts)).clamp(1000, 30000),
    );
    _reconnectAttempts++;

    print('[WebSocketService] Reconectando en ${delay.inMilliseconds}ms '
          '(intento $_reconnectAttempts)');

    _reconnectTimer?.cancel();
    _reconnectTimer = Timer(delay, () {
      if (!_intentionalClose) {
        _connect();
      }
    });
  }

  void _startHeartbeat() {
    _heartbeatTimer?.cancel();
    _heartbeatTimer = Timer.periodic(const Duration(seconds: 30), (_) {
      send({'type': 'heartbeat'});
    });
  }

  void _flushPending() {
    final pending = List<Map<String, dynamic>>.from(_pendingMessages);
    _pendingMessages.clear();
    for (final msg in pending) {
      send(msg);
    }
  }
}
