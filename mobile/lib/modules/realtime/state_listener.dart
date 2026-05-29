import 'dart:async';
import 'websocket_service.dart';

/// P8 · CU-25 — Listener reactivo de cambios de estado del incidente.
///
/// Filtra los mensajes WebSocket de tipo 'state_change' y expone
/// un Stream tipado para que el UI pueda reaccionar.

class StateChangeEvent {
  final int incidentId;
  final String estadoAnterior;
  final String estadoNuevo;
  final String label;
  final int? actorId;
  final String? actorRol;
  final List<String> transicionesDisponibles;
  final String timestamp;

  StateChangeEvent({
    required this.incidentId,
    required this.estadoAnterior,
    required this.estadoNuevo,
    required this.label,
    this.actorId,
    this.actorRol,
    required this.transicionesDisponibles,
    required this.timestamp,
  });

  factory StateChangeEvent.fromJson(Map<String, dynamic> json) => StateChangeEvent(
    incidentId: json['incident_id'] ?? 0,
    estadoAnterior: json['estado_anterior'] ?? '',
    estadoNuevo: json['estado_nuevo'] ?? '',
    label: json['label'] ?? '',
    actorId: json['actor_id'],
    actorRol: json['actor_rol'],
    transicionesDisponibles: List<String>.from(json['transiciones_disponibles'] ?? []),
    timestamp: json['timestamp'] ?? '',
  );

  /// ¿Es un estado terminal?
  bool get isTerminal => estadoNuevo == 'finalizado' || estadoNuevo == 'cancelado';

  /// Icono representativo del estado.
  String get icon {
    switch (estadoNuevo) {
      case 'pendiente': return '⏳';
      case 'buscando_taller': return '🔍';
      case 'taller_asignado': return '🏪';
      case 'en_camino': return '🚗';
      case 'en_atencion': return '🔧';
      case 'finalizado': return '✅';
      case 'cancelado': return '❌';
      default: return '❓';
    }
  }
}


class StateListener {
  final WebSocketService _ws;
  StreamSubscription? _sub;

  final _stateController = StreamController<StateChangeEvent>.broadcast();

  /// Stream de cambios de estado filtrados.
  Stream<StateChangeEvent> get stateChanges => _stateController.stream;

  StateListener(this._ws);

  /// Inicia la escucha de cambios de estado.
  void startListening() {
    _sub?.cancel();
    _sub = _ws.messages.listen((message) {
      if (message['type'] == 'state_change') {
        final event = StateChangeEvent.fromJson(message);
        _stateController.add(event);
      }
    });
  }

  /// Detiene la escucha.
  void stopListening() {
    _sub?.cancel();
    _sub = null;
  }

  void dispose() {
    stopListening();
    _stateController.close();
  }
}
