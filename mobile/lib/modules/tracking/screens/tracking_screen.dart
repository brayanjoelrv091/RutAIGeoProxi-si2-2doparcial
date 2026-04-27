/// CU15 — Pantalla de Tracking en Tiempo Real.
///
/// WS /assignments/ws/track/{incident_id}:
///   - Recibe actualizaciones de posición del técnico.
///   - Envía posición del cliente/técnico si está habilitado.
///
/// Muestra un mapa simplificado con coordenadas y permite activar
/// el envío de GPS propio. (Mapa real con google_maps_flutter requeriría
/// API key adicional — se usa visualización con coordenadas por ahora.)
library;

import 'dart:async';

import 'package:flutter/material.dart';
import 'package:geolocator/geolocator.dart';

import '../../../core/api_client.dart';
import '../../../core/location_service.dart';

class TrackingScreen extends StatefulWidget {
  final int incidentId;
  final String role; // 'cliente' | 'tecnico'

  const TrackingScreen({
    super.key,
    required this.incidentId,
    required this.role,
  });

  @override
  State<TrackingScreen> createState() => _TrackingScreenState();
}

class _TrackingScreenState extends State<TrackingScreen> {
  final LocationTrackingService _trackingService = LocationTrackingService();

  double? _remoteLat;
  double? _remoteLng;
  String? _remoteRole;
  String? _remoteTimestamp;

  bool _sendingLocation = false;
  bool _proximityAlertShown = false;
  StreamSubscription<dynamic>? _sub;
  String _status = 'Conectando...';

  @override
  void initState() {
    super.initState();
    _connect();
  }

  Future<void> _checkProximity(double tLat, double tLng) async {
    if (_proximityAlertShown || widget.role != 'cliente') return;
    try {
      final pos = await Geolocator.getLastKnownPosition();
      if (pos == null) return;
      final distanceMeters = Geolocator.distanceBetween(pos.latitude, pos.longitude, tLat, tLng);
      if (distanceMeters < 500) {
        _proximityAlertShown = true;
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: const Text(
                '🚨 ¡PREPÁRATE! El técnico está a menos de 500 metros.',
                style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
              ),
              backgroundColor: const Color(0xFFFF6B6B),
              behavior: SnackBarBehavior.floating,
              margin: const EdgeInsets.only(top: 50, left: 20, right: 20),
              dismissDirection: DismissDirection.up,
              duration: const Duration(seconds: 10),
            ),
          );
        }
      }
    } catch (_) {}
  }

  void _connect() {
    _trackingService.connectTracking(widget.incidentId);
    setState(() => _status = '🟢 Conectado — Incidente #${widget.incidentId}');

    _sub = _trackingService.locationStream?.listen(
      (data) {
        if (data is Map<String, dynamic>) {
          final type = data['type'] as String?;
          if (type == 'location_update') {
            setState(() {
              _remoteLat = (data['lat'] as num?)?.toDouble();
              _remoteLng = (data['lng'] as num?)?.toDouble();
              _remoteRole = data['role'] as String?;
              _remoteTimestamp = data['timestamp'] as String?;
            });
            if (_remoteLat != null && _remoteLng != null) {
              _checkProximity(_remoteLat!, _remoteLng!);
            }
          }
        }
      },
      onError: (e) => setState(() => _status = '🔴 Error de conexión'),
      onDone: () => setState(() => _status = '🟡 Desconectado'),
    );
  }

  void _toggleSendLocation() {
    if (_sendingLocation) {
      _trackingService.stopTracking();
      setState(() => _sendingLocation = false);
    } else {
      _trackingService.startSendingLocation(widget.role);
      setState(() => _sendingLocation = true);
    }
  }

  @override
  void dispose() {
    _sub?.cancel();
    _trackingService.stopTracking();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0A0E1A),
      appBar: AppBar(
        backgroundColor: const Color(0xFF111629),
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('Tracking en Tiempo Real', style: TextStyle(color: Color(0xFF00F2FF), fontSize: 15)),
            Text(
              'Incidente #${widget.incidentId}',
              style: const TextStyle(color: Colors.white38, fontSize: 11),
            ),
          ],
        ),
      ),
      body: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Estado de conexión
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
              decoration: BoxDecoration(
                color: const Color(0xFF111629),
                borderRadius: BorderRadius.circular(10),
                border: Border.all(color: const Color(0xFF00F2FF).withValues(alpha: 0.2)),
              ),
              child: Text(
                _status,
                style: const TextStyle(color: Color(0xFF00F2FF), fontSize: 13),
              ),
            ),
            const SizedBox(height: 20),

            // Ubicación remota recibida
            Container(
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                color: const Color(0xFF111629),
                borderRadius: BorderRadius.circular(14),
                border: Border.all(
                  color: _remoteLat != null
                      ? Colors.greenAccent.withValues(alpha: 0.3)
                      : Colors.white12,
                ),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Icon(
                        Icons.location_on,
                        color: _remoteLat != null ? Colors.greenAccent : Colors.white24,
                        size: 20,
                      ),
                      const SizedBox(width: 8),
                      Text(
                        _remoteRole != null
                            ? 'Ubicación del ${_remoteRole == "tecnico" ? "Técnico" : "Cliente"}'
                            : 'Sin ubicación recibida',
                        style: TextStyle(
                          color: _remoteLat != null ? Colors.white : Colors.white38,
                          fontWeight: FontWeight.w600,
                          fontSize: 14,
                        ),
                      ),
                    ],
                  ),
                  if (_remoteLat != null) ...[
                    const SizedBox(height: 12),
                    _CoordRow('Latitud', _remoteLat!.toStringAsFixed(6)),
                    const SizedBox(height: 6),
                    _CoordRow('Longitud', _remoteLng!.toStringAsFixed(6)),
                    if (_remoteTimestamp != null) ...[
                      const SizedBox(height: 6),
                      _CoordRow(
                        'Actualizado',
                        _remoteTimestamp!.length > 19
                            ? _remoteTimestamp!.substring(11, 19)
                            : _remoteTimestamp!,
                      ),
                    ],
                  ] else
                    const Padding(
                      padding: EdgeInsets.only(top: 10),
                      child: Text(
                        'Esperando actualizaciones de posición...',
                        style: TextStyle(color: Colors.white38, fontSize: 13),
                      ),
                    ),
                ],
              ),
            ),

            const SizedBox(height: 20),

            // Rol propio
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: const Color(0xFF111629),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: Colors.white12),
              ),
              child: Row(
                children: [
                  const Icon(Icons.person_pin_circle, color: Color(0xFF00F2FF), size: 20),
                  const SizedBox(width: 8),
                  Text(
                    'Tu rol: ${widget.role}',
                    style: const TextStyle(color: Colors.white70, fontSize: 14),
                  ),
                  const Spacer(),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                    decoration: BoxDecoration(
                      color: _sendingLocation
                          ? Colors.greenAccent.withValues(alpha: 0.15)
                          : Colors.white12,
                      borderRadius: BorderRadius.circular(20),
                    ),
                    child: Text(
                      _sendingLocation ? 'Enviando GPS' : 'GPS inactivo',
                      style: TextStyle(
                        color: _sendingLocation ? Colors.greenAccent : Colors.white38,
                        fontSize: 11,
                      ),
                    ),
                  ),
                ],
              ),
            ),

            const Spacer(),

            // Botón toggle GPS
            SizedBox(
              height: 52,
              child: ElevatedButton.icon(
                onPressed: _toggleSendLocation,
                icon: Icon(_sendingLocation ? Icons.location_off : Icons.my_location),
                label: Text(
                  _sendingLocation ? 'DETENER ENVÍO DE GPS' : 'INICIAR ENVÍO DE GPS',
                  style: const TextStyle(fontWeight: FontWeight.bold),
                ),
                style: ElevatedButton.styleFrom(
                  backgroundColor: _sendingLocation
                      ? const Color(0xFFFF6B6B)
                      : const Color(0xFF00F2FF),
                  foregroundColor: Colors.black,
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                ),
              ),
            ),
            const SizedBox(height: 12),
          ],
        ),
      ),
    );
  }
}

class _CoordRow extends StatelessWidget {
  final String label;
  final String value;

  const _CoordRow(this.label, this.value);

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Text('$label: ', style: const TextStyle(color: Colors.white38, fontSize: 13)),
        Text(value, style: const TextStyle(color: Colors.white, fontSize: 13, fontFamily: 'monospace')),
      ],
    );
  }
}
