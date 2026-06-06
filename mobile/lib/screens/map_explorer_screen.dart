import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import '../config.dart';
import '../session.dart';

class MapExplorerScreen extends StatefulWidget {
  const MapExplorerScreen({super.key});

  @override
  State<MapExplorerScreen> createState() => _MapExplorerScreenState();
}

class _MapExplorerScreenState extends State<MapExplorerScreen> {
  final MapController _mapController = MapController();
  final TextEditingController _searchCtrl = TextEditingController();

  List<Marker> _workshopMarkers = [];
  List<CircleMarker> _heatMarkers = [];
  List<dynamic> _searchResults = [];
  
  bool _showHeatmap = false;
  bool _loading = false;

  @override
  void initState() {
    super.initState();
    _loadWorkshops();
  }

  Future<void> _loadWorkshops([String query = '']) async {
    setState(() => _loading = true);
    try {
      final token = await Session.getToken();
      var url = '${Config.apiUrl}/api/v1/workshops/active';
      if (query.isNotEmpty) {
        url += '?search=${Uri.encodeComponent(query)}';
      }
      
      final res = await http.get(Uri.parse(url), headers: {'Authorization': 'Bearer $token'});
      if (res.statusCode == 200) {
        final data = jsonDecode(res.body) as List;
        final markers = data.map((ws) {
          final lat = (ws['latitud'] as num).toDouble();
          final lng = (ws['longitud'] as num).toDouble();
          return Marker(
            point: LatLng(lat, lng),
            width: 40,
            height: 40,
            child: GestureDetector(
              onTap: () {
                _showPopup(ws['nombre'], ws['direccion']);
              },
              child: Container(
                decoration: BoxDecoration(
                  color: const Color(0xFF00F2FF),
                  shape: BoxShape.circle,
                  boxShadow: [
                    BoxShadow(color: const Color(0xFF00F2FF).withOpacity(0.5), blurRadius: 10, spreadRadius: 2)
                  ]
                ),
                child: const Center(child: Text('🏪', style: TextStyle(fontSize: 18))),
              ),
            ),
          );
        }).toList();

        if (mounted) {
          setState(() {
            _workshopMarkers = markers;
          });
        }
      }
    } catch (e) {
      debugPrint('Error loading workshops: $e');
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  void _showPopup(String title, String subtitle) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: const Color(0xFF111629),
        title: Text(title, style: const TextStyle(color: Color(0xFF00F2FF))),
        content: Text(subtitle, style: const TextStyle(color: Colors.white)),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx), 
            child: const Text('Cerrar', style: TextStyle(color: Color(0xFF00F2FF)))
          )
        ],
      )
    );
  }

  Future<void> _search() async {
    final q = _searchCtrl.text.trim();
    if (q.isEmpty) {
      setState(() => _searchResults = []);
      _loadWorkshops();
      return;
    }

    _loadWorkshops(q); // Filter workshops

    // Search nominatim
    try {
      final url = 'https://nominatim.openstreetmap.org/search?q=${Uri.encodeComponent(q)}&format=json&limit=5';
      final res = await http.get(Uri.parse(url));
      if (res.statusCode == 200) {
        if (mounted) {
          setState(() {
            _searchResults = jsonDecode(res.body);
          });
        }
      }
    } catch (e) {
      debugPrint('Nominatim error: $e');
    }
  }

  Future<void> _toggleHeatmap(bool val) async {
    setState(() {
      _showHeatmap = val;
    });

    if (val && _heatMarkers.isEmpty) {
      try {
        final token = await Session.getToken();
        final res = await http.get(
          Uri.parse('${Config.apiUrl}/api/v1/incidents/heatmap'),
          headers: {'Authorization': 'Bearer $token'}
        );
        if (res.statusCode == 200) {
          final data = jsonDecode(res.body) as List;
          final circles = data.map((d) {
            final lat = (d['lat'] as num).toDouble();
            final lng = (d['lng'] as num).toDouble();
            final sev = d['severidad'] as String?;
            Color c = Colors.red.withOpacity(0.3);
            double rad = 30;
            if (sev == 'critico') {
              c = Colors.red.withOpacity(0.6);
              rad = 45;
            } else if (sev == 'mayor') {
              c = Colors.orange.withOpacity(0.4);
              rad = 35;
            }
            return CircleMarker(
              point: LatLng(lat, lng),
              color: c,
              borderColor: Colors.transparent,
              useRadiusInMeter: true,
              radius: rad,
            );
          }).toList();

          if (mounted) {
            setState(() {
              _heatMarkers = circles;
            });
          }
        }
      } catch (e) {
        debugPrint('Heatmap error: $e');
      }
    }
  }

  void _goTo(double lat, double lng) {
    _mapController.move(LatLng(lat, lng), 16);
    setState(() {
      _searchResults = [];
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0A0E1A),
      appBar: AppBar(
        title: const Text('Map Explorer'),
        backgroundColor: const Color(0xFF111629),
        foregroundColor: const Color(0xFF00F2FF),
      ),
      body: Stack(
        children: [
          FlutterMap(
            mapController: _mapController,
            options: const MapOptions(
              initialCenter: LatLng(-17.7833, -63.1821),
              initialZoom: 13,
            ),
            children: [
              TileLayer(
                urlTemplate: 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
                subdomains: const ['a','b','c','d'],
              ),
              if (_showHeatmap)
                CircleLayer(circles: _heatMarkers),
              MarkerLayer(markers: _workshopMarkers),
            ],
          ),

          // Search UI overlay
          Positioned(
            top: 10, left: 10, right: 10,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                  decoration: BoxDecoration(
                    color: const Color(0xFF1A1F35).withOpacity(0.9),
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(color: const Color(0xFF00F2FF).withOpacity(0.3))
                  ),
                  child: Column(
                    children: [
                      Row(
                        children: [
                          Expanded(
                            child: TextField(
                              controller: _searchCtrl,
                              style: const TextStyle(color: Colors.white),
                              decoration: const InputDecoration(
                                hintText: 'Buscar talleres o calles...',
                                hintStyle: TextStyle(color: Colors.white54),
                                border: InputBorder.none,
                              ),
                              onSubmitted: (_) => _search(),
                            ),
                          ),
                          IconButton(
                            icon: const Icon(Icons.search, color: Color(0xFF00F2FF)),
                            onPressed: _search,
                          )
                        ],
                      ),
                      Row(
                        children: [
                          Switch(
                            value: _showHeatmap, 
                            onChanged: _toggleHeatmap,
                            activeColor: const Color(0xFF00F2FF),
                          ),
                          const Text('Mostrar Zonas de Calor', style: TextStyle(color: Colors.white70, fontSize: 13)),
                          if (_loading) const Padding(
                            padding: EdgeInsets.only(left: 10),
                            child: SizedBox(width: 15, height: 15, child: CircularProgressIndicator(strokeWidth: 2)),
                          )
                        ],
                      )
                    ],
                  ),
                ),
                if (_searchResults.isNotEmpty)
                  Container(
                    margin: const EdgeInsets.top(8),
                    padding: const EdgeInsets.all(5),
                    decoration: BoxDecoration(
                      color: const Color(0xFF111629).withOpacity(0.95),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    constraints: const BoxConstraints(maxHeight: 200),
                    child: ListView.builder(
                      shrinkWrap: true,
                      itemCount: _searchResults.length,
                      itemBuilder: (ctx, i) {
                        final res = _searchResults[i];
                        return ListTile(
                          leading: const Icon(Icons.location_on, color: Colors.white54),
                          title: Text(res['display_name'] ?? '', style: const TextStyle(color: Colors.white, fontSize: 13)),
                          onTap: () {
                            final lat = double.tryParse(res['lat'] ?? '0') ?? 0;
                            final lon = double.tryParse(res['lon'] ?? '0') ?? 0;
                            _goTo(lat, lon);
                          },
                        );
                      },
                    ),
                  )
              ],
            ),
          )
        ],
      ),
    );
  }
}
