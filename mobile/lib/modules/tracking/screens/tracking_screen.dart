/// CU15 — Pantalla de Tracking en Tiempo Real.
///
/// WS /assignments/ws/track/{incident_id}:
///   - Recibe actualizaciones de posición del técnico.
///   - Envía posición del cliente/técnico si está habilitado.
///
/// Implementación con flutter_map y OSM (OpenStreetMap) sin API Keys.
library;

import 'dart:async';
import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:geolocator/geolocator.dart';
import 'package:http/http.dart' as http;
import 'package:latlong2/latlong.dart';

import '../../../core/api_client.dart';
import '../../../core/location_service.dart';
import '../../../config.dart';

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
  final MapController _mapController = MapController();

  LatLng? _myPosition;
  LatLng? _remotePosition;
  String? _remoteRole;
  String? _remoteTimestamp;

  bool _sendingLocation = false;
  bool _proximityAlertShown = false;
  StreamSubscription<dynamic>? _sub;
  String _status = 'Conectando...';
  
  double _distanceKm = 0.0;
  int _etaMinutes = 0;

  @override
  void initState() {
    super.initState();
    _initMyPosition();
    _connect();
  }
  
  Future<void> _initMyPosition() async {
    try {
      final pos = await Geolocator.getCurrentPosition(desiredAccuracy: LocationAccuracy.high);
      if (mounted) {
        setState(() {
          _myPosition = LatLng(pos.latitude, pos.longitude);
        });
        _updateMapBounds();
      }
    } catch (_) {}
  }

  void _calculateDistanceAndETA() {
    if (_myPosition == null || _remotePosition == null) return;
    
    // Distancia en metros
    const distance = Distance();
    final meters = distance.as(LengthUnit.Meter, _myPosition!, _remotePosition!);
    
    setState(() {
      _distanceKm = meters / 1000.0;
      // Asumimos velocidad urbana promedio de 30 km/h (500 metros por minuto)
      _etaMinutes = (meters / 500).ceil();
    });
  }

  void _updateMapBounds() {
    if (_myPosition == null) return;
    
    if (_remotePosition != null) {
      // Ajustar bounds para mostrar ambos
      final bounds = LatLngBounds.fromPoints([_myPosition!, _remotePosition!]);
      _mapController.fitCamera(CameraFit.bounds(
        bounds: bounds,
        padding: const EdgeInsets.all(50.0),
      ));
    } else {
      // Centrar solo en mi posición
      _mapController.move(_myPosition!, 15.0);
    }
  }

  Future<void> _checkProximity() async {
    if (_proximityAlertShown || widget.role != 'cliente' || _distanceKm == 0) return;
    
    if (_distanceKm < 0.5) { // menos de 500 metros
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
  }

  void _connect() {
    _trackingService.connectTracking(widget.incidentId);
    setState(() => _status = '🟢 Conectado');

    _sub = _trackingService.locationStream?.listen(
      (data) {
        if (data is Map<String, dynamic>) {
          final type = data['type'] as String?;
          if (type == 'location_update') {
            final lat = (data['lat'] as num?)?.toDouble();
            final lng = (data['lng'] as num?)?.toDouble();
            
            if (lat != null && lng != null) {
              setState(() {
                _remotePosition = LatLng(lat, lng);
                _remoteRole = data['role'] as String?;
                _remoteTimestamp = data['timestamp'] as String?;
                _status = '📍 Ubicación recibida';
              });
              
              _calculateDistanceAndETA();
              _updateMapBounds();
              _checkProximity();
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
      
      // Actualizar posición propia localmente también
      Geolocator.getPositionStream(
        locationSettings: const LocationSettings(accuracy: LocationAccuracy.high, distanceFilter: 10)
      ).listen((pos) {
        if (mounted && _sendingLocation) {
          setState(() {
            _myPosition = LatLng(pos.latitude, pos.longitude);
            _calculateDistanceAndETA();
          });
        }
      });
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
              'Incidente #${widget.incidentId} · $_status',
              style: const TextStyle(color: Colors.white38, fontSize: 11),
            ),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.my_location, color: Color(0xFF00F2FF)),
            onPressed: _updateMapBounds,
            tooltip: 'Centrar mapa',
          ),
        ],
      ),
      body: Stack(
        children: [
          // 1. EL MAPA (OSM via flutter_map)
          FlutterMap(
            mapController: _mapController,
            options: MapOptions(
              initialCenter: _myPosition ?? const LatLng(-17.7833, -63.1821), // Santa Cruz fallback
              initialZoom: 14.0,
            ),
            children: [
              TileLayer(
                urlTemplate: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
                userAgentPackageName: 'com.rutaigeoproxi.app',
              ),
              // Línea conectando ambos puntos
              if (_myPosition != null && _remotePosition != null)
                PolylineLayer(
                  polylines: [
                    Polyline(
                      points: [_myPosition!, _remotePosition!],
                      strokeWidth: 4.0,
                      color: const Color(0xFF00F2FF).withOpacity(0.7),
                    ),
                  ],
                ),
              // Marcadores
              MarkerLayer(
                markers: [
                  // Mi posición (Cliente)
                  if (_myPosition != null)
                    Marker(
                      point: _myPosition!,
                      width: 50,
                      height: 50,
                      child: const _MapPin(
                        icon: Icons.person_pin_circle,
                        color: Color(0xFF00F2FF),
                      ),
                    ),
                  // Posición remota (Técnico)
                  if (_remotePosition != null)
                    Marker(
                      point: _remotePosition!,
                      width: 50,
                      height: 50,
                      child: const _MapPin(
                        icon: Icons.directions_car,
                        color: Color(0xFFFF6B6B),
                      ),
                    ),
                ],
              ),
            ],
          ),
          
          // 2. PANEL INFERIOR (Estilo Yango/Uber)
          Positioned(
            bottom: 0,
            left: 0,
            right: 0,
            child: Container(
              padding: const EdgeInsets.all(20),
              decoration: const BoxDecoration(
                color: Color(0xFF111629),
                borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
                boxShadow: [
                  BoxShadow(color: Colors.black54, blurRadius: 20, offset: Offset(0, -5))
                ],
              ),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  // Info del Técnico / Distancia
                  Row(
                    children: [
                      Container(
                        padding: const EdgeInsets.all(12),
                        decoration: BoxDecoration(
                          color: const Color(0xFF00F2FF).withOpacity(0.1),
                          shape: BoxShape.circle,
                        ),
                        child: const Icon(Icons.engineering, color: Color(0xFF00F2FF), size: 28),
                      ),
                      const SizedBox(width: 16),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              _remoteRole == 'tecnico' ? 'Técnico Asignado' : 'Esperando Técnico...',
                              style: const TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.bold),
                            ),
                            const SizedBox(height: 4),
                            if (_remotePosition != null)
                              Text(
                                'A ${_distanceKm.toStringAsFixed(1)} km de distancia',
                                style: const TextStyle(color: Colors.white54, fontSize: 13),
                              )
                            else
                              const Text('Ubicación no disponible', style: TextStyle(color: Colors.white54, fontSize: 13)),
                          ],
                        ),
                      ),
                      if (_remotePosition != null)
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                          decoration: BoxDecoration(
                            color: const Color(0xFF00F2FF).withOpacity(0.2),
                            borderRadius: BorderRadius.circular(12),
                          ),
                          child: Column(
                            children: [
                              Text('$_etaMinutes', style: const TextStyle(color: Color(0xFF00F2FF), fontSize: 18, fontWeight: FontWeight.bold)),
                              const Text('MIN', style: TextStyle(color: Color(0xFF00F2FF), fontSize: 10, fontWeight: FontWeight.bold)),
                            ],
                          ),
                        ),
                    ],
                  ),
                  const SizedBox(height: 20),
                  
                  // Botón Diagnóstico IA
                  SizedBox(
                    height: 52,
                    child: ElevatedButton.icon(
                      onPressed: _isLoadingAI ? null : _showAIDiagnosis,
                      icon: _isLoadingAI 
                        ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(color: Colors.black, strokeWidth: 2))
                        : const Icon(Icons.psychology),
                      label: const Text(
                        'VER DIAGNÓSTICO IA',
                        style: TextStyle(fontWeight: FontWeight.bold),
                      ),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.white,
                        foregroundColor: Colors.black,
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                      ),
                    ),
                  ),
                  const SizedBox(height: 12),

                  // Botón toggle GPS
                  SizedBox(
                    height: 52,
                    child: ElevatedButton.icon(
                      onPressed: _toggleSendLocation,
                      icon: Icon(_sendingLocation ? Icons.location_off : Icons.my_location),
                      label: Text(
                        _sendingLocation ? 'DETENER MI GPS' : 'COMPARTIR MI GPS',
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
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  bool _isLoadingAI = false;

  Future<void> _showAIDiagnosis() async {
    setState(() => _isLoadingAI = true);
    try {
      final response = await http.get(
        Uri.parse('${AppConfig.baseUrl}/incidents/${widget.incidentId}'),
        headers: {'Authorization': 'Bearer ${await ApiClient.getToken()}'},
      );
      if (response.statusCode == 200) {
        final data = jsonDecode(utf8.decode(response.bodyBytes));
        if (!mounted) return;
        _showAIBottomSheet(data);
      } else {
        throw Exception('Error al cargar datos IA');
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Error: $e')));
      }
    } finally {
      if (mounted) setState(() => _isLoadingAI = false);
    }
  }

  void _showAIBottomSheet(Map<String, dynamic> data) {
    showModalBottomSheet(
      context: context,
      backgroundColor: const Color(0xFF111629),
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      isScrollControlled: true,
      builder: (context) {
        return Padding(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Row(
                children: [
                  Icon(Icons.auto_awesome, color: Color(0xFF00F2FF), size: 28),
                  SizedBox(width: 10),
                  Text('Diagnóstico de Inteligencia Artificial', style: TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.bold)),
                ],
              ),
              const SizedBox(height: 20),
              _buildIARow('📝 Transcripción Audio (Whisper):', data['transcripcion_audio'] ?? 'No disponible'),
              const SizedBox(height: 12),
              _buildIARow('🏷️ Categoría Visual (Roboflow):', data['categoria'] ?? 'Desconocida'),
              const SizedBox(height: 12),
              _buildIARow('⚠️ Nivel de Prioridad:', data['severidad'] ?? 'Normal'),
              const SizedBox(height: 12),
              _buildIARow('🧠 Resumen Analítico (Groq):', data['resumen_ia'] ?? 'Procesando...'),
              const SizedBox(height: 24),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: () => Navigator.pop(context),
                  style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFF00F2FF), foregroundColor: Colors.black, padding: const EdgeInsets.symmetric(vertical: 16)),
                  child: const Text('CERRAR PANEL', style: TextStyle(fontWeight: FontWeight.bold)),
                ),
              )
            ],
          ),
        );
      },
    );
  }

  Widget _buildIARow(String title, String content) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(title, style: const TextStyle(color: Color(0xFF00F2FF), fontSize: 13, fontWeight: FontWeight.bold)),
        const SizedBox(height: 4),
        Text(content, style: const TextStyle(color: Colors.white, fontSize: 14)),
      ],
    );
  }
}

class _MapPin extends StatelessWidget {
  final IconData icon;
  final Color color;

  const _MapPin({required this.icon, required this.color});

  @override
  Widget build(BuildContext context) {
    return Stack(
      alignment: Alignment.center,
      children: [
        Container(
          width: 40,
          height: 40,
          decoration: BoxDecoration(
            color: color.withOpacity(0.2),
            shape: BoxShape.circle,
          ),
        ),
        Container(
          width: 30,
          height: 30,
          decoration: BoxDecoration(
            color: color,
            shape: BoxShape.circle,
            border: Border.all(color: Colors.white, width: 2),
            boxShadow: const [BoxShadow(color: Colors.black26, blurRadius: 5, offset: Offset(0, 2))],
          ),
          child: Icon(icon, color: Colors.white, size: 18),
        ),
      ],
    );
  }
}
