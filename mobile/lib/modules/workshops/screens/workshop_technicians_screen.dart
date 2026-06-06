import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../../core/api_client.dart';
import '../models/workshop_model.dart';
import '../services/workshop_service.dart';

class WorkshopTechniciansScreen extends StatefulWidget {
  final Workshop workshop;

  const WorkshopTechniciansScreen({super.key, required this.workshop});

  @override
  State<WorkshopTechniciansScreen> createState() =>
      _WorkshopTechniciansScreenState();
}

class _WorkshopTechniciansScreenState extends State<WorkshopTechniciansScreen> {
  List<Technician> _technicians = [];
  bool _loading = true;
  String _error = '';

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = '';
    });
    try {
      final list = await WorkshopService.listTechnicians(widget.workshop.id);
      setState(() => _technicians = list);
    } on ApiException catch (e) {
      setState(() => _error = e.message);
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Map<String, List<Technician>> _groupBySpecialty(List<Technician> list) {
    final Map<String, List<Technician>> map = {};
    for (var t in list) {
      final spec = t.especialidad?.isNotEmpty == true ? t.especialidad! : 'General';
      if (!map.containsKey(spec)) map[spec] = [];
      map[spec]!.add(t);
    }
    return map;
  }

  Future<void> _callPhone(String? phone) async {
    if (phone == null || phone.isEmpty) return;
    final Uri url = Uri(scheme: 'tel', path: phone);
    if (await canLaunchUrl(url)) {
      await launchUrl(url);
    } else {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('No se pudo lanzar la llamada')),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final grouped = _groupBySpecialty(_technicians);

    return Scaffold(
      backgroundColor: const Color(0xFF0A0E1A),
      appBar: AppBar(
        backgroundColor: const Color(0xFF111629),
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('Técnicos', style: TextStyle(color: Color(0xFF0096FF), fontSize: 16)),
            Text(
              widget.workshop.nombre,
              style: const TextStyle(color: Colors.white54, fontSize: 12),
            ),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh, color: Color(0xFF0096FF)),
            onPressed: _load,
          ),
        ],
      ),
      body: _buildBody(grouped),
    );
  }

  Widget _buildBody(Map<String, List<Technician>> grouped) {
    if (_loading) {
      return const Center(child: CircularProgressIndicator(color: Color(0xFF0096FF)));
    }
    if (_error.isNotEmpty) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.error_outline, color: Color(0xFFFF6B6B), size: 48),
              const SizedBox(height: 12),
              Text(_error, style: const TextStyle(color: Color(0xFFFF6B6B))),
              const SizedBox(height: 16),
              ElevatedButton(onPressed: _load, child: const Text('Reintentar')),
            ],
          ),
        ),
      );
    }
    if (_technicians.isEmpty) {
      return const Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.people_outline, color: Colors.white24, size: 64),
            SizedBox(height: 16),
            Text('Este taller no tiene técnicos registrados', style: TextStyle(color: Colors.white54, fontSize: 16)),
          ],
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: _load,
      color: const Color(0xFF0096FF),
      child: ListView.builder(
        padding: const EdgeInsets.all(16),
        itemCount: grouped.length,
        itemBuilder: (ctx, i) {
          final specialty = grouped.keys.elementAt(i);
          final techs = grouped[specialty]!;
          return Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Padding(
                padding: const EdgeInsets.only(top: 8, bottom: 12),
                child: Text(
                  specialty,
                  style: const TextStyle(
                    color: Color(0xFF0096FF),
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
              ...techs.map((t) => _buildTechCard(t)),
              const SizedBox(height: 16),
            ],
          );
        },
      ),
    );
  }

  Widget _buildTechCard(Technician tech) {
    final available = tech.estaDisponible;
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFF111629),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: Colors.white.withValues(alpha: 0.1)),
      ),
      child: Row(
        children: [
          Container(
            width: 48,
            height: 48,
            decoration: BoxDecoration(
              color: const Color(0xFF0096FF).withValues(alpha: 0.1),
              shape: BoxShape.circle,
            ),
            child: const Icon(Icons.person, color: Color(0xFF0096FF)),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  tech.nombre,
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 16,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                const SizedBox(height: 4),
                Row(
                  children: [
                    Icon(
                      available ? Icons.check_circle : Icons.do_not_disturb_on,
                      color: available ? const Color(0xFF00C853) : const Color(0xFFFF1744),
                      size: 14,
                    ),
                    const SizedBox(width: 4),
                    Text(
                      available ? 'Disponible' : 'Ocupado',
                      style: TextStyle(
                        color: available ? const Color(0xFF00C853) : const Color(0xFFFF1744),
                        fontSize: 12,
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
          if (tech.telefono != null && tech.telefono!.isNotEmpty)
            IconButton(
              icon: const Icon(Icons.phone, color: Color(0xFF0096FF)),
              onPressed: () => _callPhone(tech.telefono),
              tooltip: 'Llamar al técnico',
            ),
        ],
      ),
    );
  }
}
