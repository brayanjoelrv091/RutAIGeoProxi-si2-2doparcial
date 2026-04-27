import 'dart:io';
import 'package:flutter/material.dart';
import 'package:geolocator/geolocator.dart';
import 'package:image_picker/image_picker.dart';
import 'package:record/record.dart';
import 'package:path_provider/path_provider.dart';
import '../backend.dart';

class ReportIncidentScreen extends StatefulWidget {
  const ReportIncidentScreen({super.key});

  @override
  State<ReportIncidentScreen> createState() => _ReportIncidentScreenState();
}

class _ReportIncidentScreenState extends State<ReportIncidentScreen> {
  final _formKey = GlobalKey<FormState>();
  final _titleController = TextEditingController();
  final _descriptionController = TextEditingController();
  
  bool _loading = false;
  String? _error;
  
  // Hardware States
  Position? _currentPosition;
  File? _imageFile;
  File? _audioFile;
  
  // Audio Recorder State
  late AudioRecorder _audioRecorder;
  bool _isRecording = false;

  @override
  void initState() {
    super.initState();
    _audioRecorder = AudioRecorder();
  }

  @override
  void dispose() {
    _audioRecorder.dispose();
    _titleController.dispose();
    _descriptionController.dispose();
    super.dispose();
  }

  Future<void> _getGPS() async {
    bool serviceEnabled;
    LocationPermission permission;

    serviceEnabled = await Geolocator.isLocationServiceEnabled();
    if (!serviceEnabled) {
      _showError('Los servicios de ubicación están deshabilitados.');
      return;
    }

    permission = await Geolocator.checkPermission();
    if (permission == LocationPermission.denied) {
      permission = await Geolocator.requestPermission();
      if (permission == LocationPermission.denied) {
        _showError('Permisos de ubicación denegados.');
        return;
      }
    }
    
    if (permission == LocationPermission.deniedForever) {
      _showError('Los permisos de ubicación están permanentemente denegados.');
      return;
    }

    setState(() => _loading = true);
    try {
      final position = await Geolocator.getCurrentPosition();
      setState(() => _currentPosition = position);
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('📍 Ubicación GPS obtenida')),
      );
    } catch (e) {
      _showError('Error al obtener GPS: $e');
    } finally {
      setState(() => _loading = false);
    }
  }

  Future<void> _takePhoto() async {
    final ImagePicker picker = ImagePicker();
    try {
      final XFile? image = await picker.pickImage(
        source: ImageSource.camera,
        imageQuality: 80, // Comprimir un poco para envío rápido
      );
      if (image != null) {
        setState(() => _imageFile = File(image.path));
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('📸 Fotografía capturada')),
        );
      }
    } catch (e) {
      _showError('Error al abrir cámara: $e');
    }
  }

  Future<void> _toggleRecording() async {
    try {
      if (await _audioRecorder.hasPermission()) {
        if (_isRecording) {
          final path = await _audioRecorder.stop();
          setState(() {
            _isRecording = false;
            if (path != null) _audioFile = File(path);
          });
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('🎙️ Audio guardado para Whisper')),
          );
        } else {
          final dir = await getApplicationDocumentsDirectory();
          final path = '${dir.path}/audio_${DateTime.now().millisecondsSinceEpoch}.m4a';
          await _audioRecorder.start(
            const RecordConfig(encoder: AudioEncoder.aacLc),
            path: path,
          );
          setState(() => _isRecording = true);
        }
      } else {
        _showError('Permiso de micrófono denegado.');
      }
    } catch (e) {
      _showError('Error de grabación: $e');
    }
  }

  void _showError(String msg) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(msg), backgroundColor: Colors.redAccent),
    );
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    if (_currentPosition == null) {
      setState(() => _error = "Debe obtener su ubicación GPS primero.");
      return;
    }
    if (_imageFile == null) {
      setState(() => _error = "Se requiere una fotografía para la IA Roboflow.");
      return;
    }

    setState(() {
      _loading = true;
      _error = null;
    });

    final res = await Backend.reportIncident(
      title: _titleController.text,
      description: _descriptionController.text.isNotEmpty ? _descriptionController.text : null,
      lat: _currentPosition!.latitude,
      lng: _currentPosition!.longitude,
      address: "Ubicación detectada por GPS",
      image: _imageFile,
      audio: _audioFile,
    );

    if (mounted) {
      setState(() => _loading = false);
      if (res == null) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('🚨 Incidente enviado. IA procesando...'),
            backgroundColor: Color(0xFF00E676),
          ),
        );
        Navigator.pop(context);
      } else {
        setState(() => _error = res);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0A0E1A),
      appBar: AppBar(
        title: const Text('Reportar Emergencia'),
        backgroundColor: const Color(0xFF111629),
      ),
      body: Padding(
        padding: const EdgeInsets.all(20.0),
        child: Form(
          key: _formKey,
          child: ListView(
            children: [
              const Text(
                'Describa su emergencia vehicular',
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.white),
              ),
              const SizedBox(height: 8),
              const Text(
                'La IA analizará su foto y audio para asignar el mejor taller.',
                style: TextStyle(fontSize: 13, color: Colors.white54),
              ),
              const SizedBox(height: 24),

              // Botones de Hardware (GPS y Cámara)
              Row(
                children: [
                  Expanded(
                    child: _HardwareButton(
                      icon: Icons.gps_fixed,
                      label: _currentPosition != null ? 'GPS Listo' : 'Ubicación',
                      color: _currentPosition != null ? const Color(0xFF00E676) : const Color(0xFF00F2FF),
                      onTap: _getGPS,
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: _HardwareButton(
                      icon: Icons.camera_alt,
                      label: _imageFile != null ? 'Foto Lista' : 'Tomar Foto',
                      color: _imageFile != null ? const Color(0xFF00E676) : const Color(0xFF00F2FF),
                      onTap: _takePhoto,
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: _HardwareButton(
                      icon: _isRecording ? Icons.stop : Icons.mic,
                      label: _isRecording ? 'Grabando...' : (_audioFile != null ? 'Audio Listo' : 'Voz (Whisper)'),
                      color: _isRecording ? Colors.redAccent : (_audioFile != null ? const Color(0xFF00E676) : const Color(0xFF00F2FF)),
                      onTap: _toggleRecording,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 24),

              TextFormField(
                controller: _titleController,
                style: const TextStyle(color: Colors.white),
                decoration: InputDecoration(
                  labelText: 'Título del Problema',
                  labelStyle: const TextStyle(color: Colors.white54),
                  hintText: 'Ej: Motor sobrecalentado, Llanta pinchada',
                  hintStyle: const TextStyle(color: Colors.white24),
                  filled: true,
                  fillColor: const Color(0xFF111629),
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide.none),
                ),
                validator: (v) => v == null || v.isEmpty ? 'Requerido' : null,
              ),
              const SizedBox(height: 16),

              TextFormField(
                controller: _descriptionController,
                style: const TextStyle(color: Colors.white),
                decoration: InputDecoration(
                  labelText: 'Detalles adicionales (Opcional)',
                  labelStyle: const TextStyle(color: Colors.white54),
                  filled: true,
                  fillColor: const Color(0xFF111629),
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide.none),
                ),
                maxLines: 3,
              ),
              const SizedBox(height: 24),

              if (_error != null)
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: Colors.redAccent.withOpacity(0.1),
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: Colors.redAccent),
                  ),
                  child: Text(_error!, style: const TextStyle(color: Colors.redAccent)),
                ),
              const SizedBox(height: 16),

              ElevatedButton(
                onPressed: _loading || _isRecording ? null : _submit,
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFFFF6B6B),
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(vertical: 18),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                ),
                child: _loading 
                  ? const SizedBox(height: 20, width: 20, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2))
                  : const Text('ENVIAR PARA ANÁLISIS IA', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16, letterSpacing: 1)),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _HardwareButton extends StatelessWidget {
  final IconData icon;
  final String label;
  final Color color;
  final VoidCallback onTap;

  const _HardwareButton({required this.icon, required this.label, required this.color, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(12),
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 4),
        decoration: BoxDecoration(
          color: color.withOpacity(0.1),
          border: Border.all(color: color.withOpacity(0.5)),
          borderRadius: BorderRadius.circular(12),
        ),
        child: Column(
          children: [
            Icon(icon, color: color, size: 24),
            const SizedBox(height: 8),
            Text(label, textAlign: TextAlign.center, style: TextStyle(color: color, fontWeight: FontWeight.bold, fontSize: 11)),
          ],
        ),
      ),
    );
  }
}
