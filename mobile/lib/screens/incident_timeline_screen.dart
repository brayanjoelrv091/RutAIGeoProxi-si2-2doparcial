import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import '../config.dart';
import '../session.dart';

/// P8 · CU-25 — Pantalla Timeline de estados del incidente.
///
/// Muestra el historial completo de transiciones de estado
/// con línea de tiempo vertical, colores por estado, y actor info.

class IncidentTimelineScreen extends StatefulWidget {
  final int incidentId;

  const IncidentTimelineScreen({super.key, required this.incidentId});

  @override
  State<IncidentTimelineScreen> createState() => _IncidentTimelineScreenState();
}

class _IncidentTimelineScreenState extends State<IncidentTimelineScreen> {
  Map<String, dynamic>? _timeline;
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadTimeline();
  }

  Future<void> _loadTimeline() async {
    setState(() { _loading = true; _error = null; });

    try {
      final response = await http.get(
        Uri.parse('${AppConfig.apiBaseUrl}/realtime/incidents/${widget.incidentId}/timeline'),
        headers: {'Authorization': 'Bearer ${Session.token ?? ''}'},
      ).timeout(const Duration(seconds: 15));

      if (response.statusCode == 200) {
        setState(() {
          _timeline = jsonDecode(response.body);
          _loading = false;
        });
      } else {
        setState(() {
          _error = 'Error ${response.statusCode}';
          _loading = false;
        });
      }
    } catch (e) {
      setState(() {
        _error = 'Error de conexión: $e';
        _loading = false;
      });
    }
  }

  Color _stateColor(String state) {
    switch (state) {
      case 'pendiente': return const Color(0xFFF59E0B);
      case 'buscando_taller': return const Color(0xFF3B82F6);
      case 'taller_asignado': return const Color(0xFF8B5CF6);
      case 'en_camino': return const Color(0xFF06B6D4);
      case 'en_atencion': return const Color(0xFFF97316);
      case 'finalizado': return const Color(0xFF22C55E);
      case 'cancelado': return const Color(0xFFEF4444);
      default: return const Color(0xFF6B7280);
    }
  }

  String _stateIcon(String state) {
    switch (state) {
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

  String _rolIcon(String? rol) {
    switch (rol) {
      case 'admin': return '👤';
      case 'taller': return '🏪';
      case 'cliente': return '🚗';
      case 'sistema': return '⚙️';
      default: return '👤';
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0A0E1A),
      appBar: AppBar(
        title: Text('Timeline #${widget.incidentId}'),
        backgroundColor: const Color(0xFF111629),
        foregroundColor: const Color(0xFF00F2FF),
        elevation: 0,
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadTimeline,
          ),
        ],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator(color: Color(0xFF00F2FF)))
          : _error != null
              ? _buildError()
              : _buildTimeline(),
    );
  }

  Widget _buildError() {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Text('⚠️', style: TextStyle(fontSize: 48)),
          const SizedBox(height: 12),
          Text(_error!, style: const TextStyle(color: Colors.red, fontSize: 14)),
          const SizedBox(height: 16),
          ElevatedButton(
            onPressed: _loadTimeline,
            style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFF00F2FF)),
            child: const Text('Reintentar', style: TextStyle(color: Colors.black)),
          ),
        ],
      ),
    );
  }

  Widget _buildTimeline() {
    if (_timeline == null) return const SizedBox();

    final estadoActual = _timeline!['estado_actual'] ?? '';
    final labelActual = _timeline!['label_actual'] ?? '';
    final esTerminal = _timeline!['es_terminal'] ?? false;
    final eventos = (_timeline!['eventos'] as List<dynamic>?) ?? [];
    final transiciones = List<String>.from(_timeline!['transiciones_disponibles'] ?? []);

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        // Current state card
        Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: const Color(0xFF111629),
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: _stateColor(estadoActual).withOpacity(0.4)),
          ),
          child: Row(
            children: [
              Container(
                width: 12, height: 12,
                decoration: BoxDecoration(
                  color: _stateColor(estadoActual),
                  shape: BoxShape.circle,
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(labelActual,
                      style: TextStyle(
                        color: _stateColor(estadoActual),
                        fontSize: 16, fontWeight: FontWeight.bold,
                      ),
                    ),
                    if (esTerminal)
                      const Text('Estado Final',
                        style: TextStyle(color: Color(0xFF22C55E), fontSize: 11),
                      ),
                  ],
                ),
              ),
              Text(_stateIcon(estadoActual), style: const TextStyle(fontSize: 24)),
            ],
          ),
        ),

        // Available transitions
        if (!esTerminal && transiciones.isNotEmpty) ...[
          const SizedBox(height: 12),
          Wrap(
            spacing: 6,
            children: transiciones.map((t) => Chip(
              label: Text(t, style: const TextStyle(fontSize: 10, color: Colors.white70)),
              backgroundColor: _stateColor(t).withOpacity(0.15),
              side: BorderSide(color: _stateColor(t).withOpacity(0.3)),
              padding: EdgeInsets.zero,
              materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
            )).toList(),
          ),
        ],

        const SizedBox(height: 24),

        // Timeline events
        if (eventos.isEmpty)
          const Center(
            child: Padding(
              padding: EdgeInsets.all(40),
              child: Column(
                children: [
                  Text('📭', style: TextStyle(fontSize: 36)),
                  SizedBox(height: 8),
                  Text('Sin eventos aún', style: TextStyle(color: Colors.white38)),
                ],
              ),
            ),
          )
        else
          ...eventos.asMap().entries.map((entry) {
            final i = entry.key;
            final e = entry.value;
            final isLast = i == eventos.length - 1;
            return _buildEventItem(e, isLast);
          }),
      ],
    );
  }

  Widget _buildEventItem(Map<String, dynamic> event, bool isLast) {
    final estadoNuevo = event['estado_nuevo'] ?? '';
    final labelAnterior = event['label_anterior'] ?? '';
    final labelNuevo = event['label_nuevo'] ?? '';
    final actorRol = event['actor_rol'];
    final notas = event['notas'];
    final createdAt = event['creado_en'] ?? '';

    return IntrinsicHeight(
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Timeline line + dot
          SizedBox(
            width: 32,
            child: Column(
              children: [
                Container(
                  width: 14, height: 14,
                  decoration: BoxDecoration(
                    color: _stateColor(estadoNuevo),
                    shape: BoxShape.circle,
                    boxShadow: [
                      BoxShadow(
                        color: _stateColor(estadoNuevo).withOpacity(0.4),
                        blurRadius: 6,
                      ),
                    ],
                  ),
                ),
                if (!isLast)
                  Expanded(
                    child: Container(
                      width: 2,
                      color: _stateColor(estadoNuevo).withOpacity(0.2),
                    ),
                  ),
              ],
            ),
          ),

          const SizedBox(width: 12),

          // Event content
          Expanded(
            child: Container(
              margin: const EdgeInsets.only(bottom: 16),
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: const Color(0xFF0A0E1A).withOpacity(0.5),
                border: Border.all(color: const Color(0xFF1F2744).withOpacity(0.6)),
                borderRadius: BorderRadius.circular(10),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Transition
                  Row(
                    children: [
                      Text(labelAnterior,
                        style: TextStyle(
                          color: _stateColor(event['estado_anterior'] ?? ''),
                          fontSize: 12, fontWeight: FontWeight.w600,
                        ),
                      ),
                      const Padding(
                        padding: EdgeInsets.symmetric(horizontal: 6),
                        child: Text('→', style: TextStyle(color: Colors.white38, fontSize: 12)),
                      ),
                      Text(labelNuevo,
                        style: TextStyle(
                          color: _stateColor(estadoNuevo),
                          fontSize: 12, fontWeight: FontWeight.w600,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 6),
                  // Meta
                  Row(
                    children: [
                      Text('${_rolIcon(actorRol)} ${actorRol ?? 'sistema'}',
                        style: const TextStyle(color: Colors.white38, fontSize: 10),
                      ),
                      const SizedBox(width: 12),
                      Text(_formatTime(createdAt),
                        style: const TextStyle(color: Colors.white38, fontSize: 10),
                      ),
                    ],
                  ),
                  // Notes
                  if (notas != null && notas.isNotEmpty) ...[
                    const SizedBox(height: 8),
                    Container(
                      padding: const EdgeInsets.all(8),
                      decoration: BoxDecoration(
                        color: const Color(0xFF00F2FF).withOpacity(0.04),
                        borderRadius: BorderRadius.circular(6),
                        border: Border(
                          left: BorderSide(color: const Color(0xFF00F2FF).withOpacity(0.3), width: 2),
                        ),
                      ),
                      child: Text('💬 $notas',
                        style: const TextStyle(color: Colors.white54, fontSize: 11),
                      ),
                    ),
                  ],
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  String _formatTime(String dateStr) {
    try {
      final dt = DateTime.parse(dateStr);
      return '${dt.hour.toString().padLeft(2, '0')}:${dt.minute.toString().padLeft(2, '0')}:${dt.second.toString().padLeft(2, '0')} - ${dt.day}/${dt.month}/${dt.year}';
    } catch (_) {
      return dateStr;
    }
  }
}
