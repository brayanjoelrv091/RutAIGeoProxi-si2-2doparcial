import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';
import 'package:geolocator/geolocator.dart';
import '../modules/realtime/websocket_service.dart';
import '../modules/realtime/gps_tracker.dart';
import '../session.dart';

/// P8 · CU-26 — Pantalla de tracking GPS en vivo.
///
/// Muestra:
///   - Mapa OpenStreetMap con posición del técnico en vivo
///   - Indicadores de velocidad, dirección y precisión
///   - Estado de conexión WebSocket
///   - Botón para iniciar/detener tracking

class IncidentTrackingScreen extends StatefulWidget {
  final int incidentId;

  const IncidentTrackingScreen({super.key, required this.incidentId});

  @override
  State<IncidentTrackingScreen> createState() => _IncidentTrackingScreenState();
}

class _IncidentTrackingScreenState extends State<IncidentTrackingScreen> {
  final WebSocketService _ws = WebSocketService();
  late GPSTracker _gpsTracker;
  final MapController _mapController = MapController();

  WSConnectionState _connectionState = WSConnectionState.disconnected;
  Position? _currentPosition;
  final List<LatLng> _trackPoints = [];
  double _speed = 0;
  double _heading = 0;
  bool _isTracking = false;

  StreamSubscription? _wsSub;
  StreamSubscription? _wsStateSub;
  StreamSubscription? _gpsSub;

  @override
  void initState() {
    super.initState();
    _gpsTracker = GPSTracker(_ws);
    _initWebSocket();
  }

  void _initWebSocket() {
    final token = Session.token ?? '';
    _ws.connectToIncident(widget.incidentId, token);

    _wsStateSub = _ws.connectionState.listen((state) {
      if (mounted) setState(() => _connectionState = state);
    });

    _wsSub = _ws.messages.listen((msg) {
      if (msg['type'] == 'location_update' && mounted) {
        final lat = (msg['lat'] as num?)?.toDouble();
        final lng = (msg['lng'] as num?)?.toDouble();
        if (lat != null && lng != null) {
          setState(() {
            _trackPoints.add(LatLng(lat, lng));
            _speed = (msg['velocidad_kmh'] as num?)?.toDouble() ?? 0;
            _heading = (msg['heading'] as num?)?.toDouble() ?? 0;
          });
        }
      }
    });
  }

  Future<void> _toggleTracking() async {
    if (_isTracking) {
      _gpsTracker.stopTracking();
      _gpsSub?.cancel();
      setState(() => _isTracking = false);
    } else {
      final started = await _gpsTracker.startTracking(role: 'cliente');
      if (started) {
        _gpsSub = _gpsTracker.positions.listen((pos) {
          if (mounted) {
            setState(() {
              _currentPosition = pos;
              _trackPoints.add(LatLng(pos.latitude, pos.longitude));
              _speed = pos.speed * 3.6;
              _heading = pos.heading;
            });
            _mapController.move(LatLng(pos.latitude, pos.longitude), 16);
          }
        });
        setState(() => _isTracking = true);
      } else {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('No se pudo acceder al GPS')),
          );
        }
      }
    }
  }

  @override
  void dispose() {
    _wsSub?.cancel();
    _wsStateSub?.cancel();
    _gpsSub?.cancel();
    _gpsTracker.dispose();
    _ws.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0A0E1A),
      appBar: AppBar(
        title: Text('Tracking #${widget.incidentId}'),
        backgroundColor: const Color(0xFF111629),
        foregroundColor: const Color(0xFF00F2FF),
        elevation: 0,
        actions: [
          _buildConnectionIndicator(),
          const SizedBox(width: 12),
        ],
      ),
      body: Column(
        children: [
          // Mapa
          Expanded(
            child: FlutterMap(
              mapController: _mapController,
              options: MapOptions(
                initialCenter: _currentPosition != null
                    ? LatLng(_currentPosition!.latitude, _currentPosition!.longitude)
                    : const LatLng(-17.7833, -63.1821), // Santa Cruz default
                initialZoom: 14,
              ),
              children: [
                TileLayer(
                  urlTemplate: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
                ),
                // Track line
                if (_trackPoints.length > 1)
                  PolylineLayer(
                    polylines: [
                      Polyline(
                        points: _trackPoints,
                        color: const Color(0xFF00F2FF),
                        strokeWidth: 3,
                      ),
                    ],
                  ),
                // Current position marker
                if (_trackPoints.isNotEmpty)
                  MarkerLayer(
                    markers: [
                      Marker(
                        point: _trackPoints.last,
                        width: 40,
                        height: 40,
                        child: Container(
                          decoration: BoxDecoration(
                            color: const Color(0xFF00F2FF),
                            shape: BoxShape.circle,
                            boxShadow: [
                              BoxShadow(
                                color: const Color(0xFF00F2FF).withOpacity(0.5),
                                blurRadius: 12,
                                spreadRadius: 4,
                              ),
                            ],
                          ),
                          child: const Icon(Icons.navigation, color: Colors.black, size: 22),
                        ),
                      ),
                    ],
                  ),
              ],
            ),
          ),

          // Stats bar
          Container(
            padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 16),
            color: const Color(0xFF111629),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceAround,
              children: [
                _buildStat('${_speed.toStringAsFixed(1)}', 'km/h'),
                _buildStat(_headingLabel, 'Dirección'),
                _buildStat('${_trackPoints.length}', 'Puntos'),
              ],
            ),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _toggleTracking,
        backgroundColor: _isTracking ? Colors.red : const Color(0xFF00F2FF),
        foregroundColor: _isTracking ? Colors.white : Colors.black,
        icon: Icon(_isTracking ? Icons.stop : Icons.play_arrow),
        label: Text(_isTracking ? 'Detener' : 'Iniciar Tracking'),
      ),
    );
  }

  Widget _buildConnectionIndicator() {
    Color color;
    String label;
    switch (_connectionState) {
      case WSConnectionState.connected:
        color = Colors.green;
        label = 'Conectado';
      case WSConnectionState.connecting:
        color = Colors.yellow;
        label = 'Conectando...';
      case WSConnectionState.reconnecting:
        color = Colors.orange;
        label = 'Reconectando...';
      default:
        color = Colors.red;
        label = 'Desconectado';
    }
    return Row(
      children: [
        Container(
          width: 8, height: 8,
          decoration: BoxDecoration(color: color, shape: BoxShape.circle),
        ),
        const SizedBox(width: 6),
        Text(label, style: TextStyle(color: color, fontSize: 11)),
      ],
    );
  }

  Widget _buildStat(String value, String label) {
    return Column(
      children: [
        Text(
          value,
          style: const TextStyle(
            color: Color(0xFF00F2FF),
            fontSize: 18,
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 2),
        Text(
          label,
          style: TextStyle(color: Colors.white.withOpacity(0.4), fontSize: 10),
        ),
      ],
    );
  }

  String get _headingLabel {
    if (_heading >= 337.5 || _heading < 22.5) return 'N';
    if (_heading >= 22.5 && _heading < 67.5) return 'NE';
    if (_heading >= 67.5 && _heading < 112.5) return 'E';
    if (_heading >= 112.5 && _heading < 157.5) return 'SE';
    if (_heading >= 157.5 && _heading < 202.5) return 'S';
    if (_heading >= 202.5 && _heading < 247.5) return 'SO';
    if (_heading >= 247.5 && _heading < 292.5) return 'O';
    return 'NO';
  }
}
