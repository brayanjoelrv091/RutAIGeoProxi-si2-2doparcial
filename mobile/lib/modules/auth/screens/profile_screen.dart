import 'package:flutter/material.dart';
import '../services/auth_service.dart';
import '../models/user_model.dart';
import '../../../core/api_client.dart';

class ProfileScreen extends StatefulWidget {
  const ProfileScreen({super.key});

  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  UserProfile? _user;
  bool _loading = true;
  String _error = '';

  final _currentPassCtrl = TextEditingController();
  final _newPassCtrl = TextEditingController();
  final _passFormKey = GlobalKey<FormState>();
  bool _changingPass = false;
  bool _obscureCurrent = true;
  bool _obscureNew = true;

  @override
  void initState() {
    super.initState();
    _loadProfile();
  }

  Future<void> _loadProfile() async {
    setState(() {
      _loading = true;
      _error = '';
    });
    try {
      final user = await AuthService.getMe();
      setState(() => _user = user);
    } on ApiException catch (e) {
      setState(() => _error = e.message);
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _changePassword() async {
    if (!_passFormKey.currentState!.validate()) return;
    setState(() => _changingPass = true);
    try {
      await AuthService.changePassword(
        _currentPassCtrl.text,
        _newPassCtrl.text,
      );
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Contraseña actualizada exitosamente.'),
          backgroundColor: Colors.green,
        ),
      );
      _currentPassCtrl.clear();
      _newPassCtrl.clear();
      Navigator.pop(context); // Cierra el modal de cambiar contraseña
    } on ApiException catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Error: ${e.message}'),
          backgroundColor: Colors.red,
        ),
      );
    } finally {
      if (mounted) setState(() => _changingPass = false);
    }
  }

  void _showChangePasswordDialog() {
    _currentPassCtrl.clear();
    _newPassCtrl.clear();
    showDialog(
      context: context,
      builder: (context) {
        return StatefulBuilder(
          builder: (context, setStateDialog) {
            return AlertDialog(
              backgroundColor: const Color(0xFF111629),
              title: const Text('Cambiar Contraseña', style: TextStyle(color: Color(0xFF00F2FF))),
              content: Form(
                key: _passFormKey,
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    TextFormField(
                      controller: _currentPassCtrl,
                      obscureText: _obscureCurrent,
                      style: const TextStyle(color: Colors.white),
                      decoration: InputDecoration(
                        labelText: 'Contraseña Actual',
                        labelStyle: const TextStyle(color: Colors.white54),
                        suffixIcon: IconButton(
                          icon: Icon(_obscureCurrent ? Icons.visibility_off : Icons.visibility, color: Colors.white54),
                          onPressed: () => setStateDialog(() => _obscureCurrent = !_obscureCurrent),
                        ),
                        filled: true,
                        fillColor: const Color(0xFF0A0E1A),
                        border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
                      ),
                      validator: (v) => v == null || v.isEmpty ? 'Requerido' : null,
                    ),
                    const SizedBox(height: 16),
                    TextFormField(
                      controller: _newPassCtrl,
                      obscureText: _obscureNew,
                      style: const TextStyle(color: Colors.white),
                      decoration: InputDecoration(
                        labelText: 'Nueva Contraseña',
                        labelStyle: const TextStyle(color: Colors.white54),
                        suffixIcon: IconButton(
                          icon: Icon(_obscureNew ? Icons.visibility_off : Icons.visibility, color: Colors.white54),
                          onPressed: () => setStateDialog(() => _obscureNew = !_obscureNew),
                        ),
                        filled: true,
                        fillColor: const Color(0xFF0A0E1A),
                        border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
                      ),
                      validator: (v) {
                        if (v == null || v.isEmpty) return 'Requerido';
                        if (v.length < 8) return 'Mínimo 8 caracteres';
                        if (!RegExp(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z\d\w\W]{8,}$').hasMatch(v)) {
                          return 'Debe incluir al menos 1 mayúscula y 1 número';
                        }
                        return null;
                      },
                    ),
                  ],
                ),
              ),
              actions: [
                TextButton(
                  onPressed: _changingPass ? null : () => Navigator.pop(context),
                  child: const Text('Cancelar', style: TextStyle(color: Colors.white54)),
                ),
                ElevatedButton(
                  onPressed: _changingPass ? null : () {
                    _changePassword().then((_) {
                      if (mounted && _changingPass == false) {
                        // Dialog was closed or error occurred
                      }
                    });
                    setStateDialog(() {}); // Update button state
                  },
                  child: _changingPass 
                    ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.black))
                    : const Text('Actualizar'),
                ),
              ],
            );
          }
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0A0E1A),
      appBar: AppBar(
        title: const Text('Mi Perfil'),
      ),
      body: _buildBody(),
    );
  }

  Widget _buildBody() {
    if (_loading) {
      return const Center(child: CircularProgressIndicator(color: Color(0xFF00F2FF)));
    }
    if (_error.isNotEmpty) {
      return Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.error_outline, color: Color(0xFFFF6B6B), size: 48),
            const SizedBox(height: 12),
            Text(_error, style: const TextStyle(color: Color(0xFFFF6B6B))),
            const SizedBox(height: 16),
            ElevatedButton(onPressed: _loadProfile, child: const Text('Reintentar')),
          ],
        ),
      );
    }
    if (_user == null) return const SizedBox.shrink();

    return SingleChildScrollView(
      padding: const EdgeInsets.all(24),
      child: Column(
        children: [
          const CircleAvatar(
            radius: 50,
            backgroundColor: Color(0xFF111629),
            child: Icon(Icons.person, size: 50, color: Color(0xFF00F2FF)),
          ),
          const SizedBox(height: 24),
          _ProfileItem(icon: Icons.person_outline, label: 'Nombre', value: _user!.nombre),
          const SizedBox(height: 16),
          _ProfileItem(icon: Icons.email_outlined, label: 'Correo', value: _user!.email),
          const SizedBox(height: 16),
          _ProfileItem(icon: Icons.badge_outlined, label: 'Rol', value: _user!.rol.toUpperCase()),
          
          if (_user!.rol == 'admin' && _user!.tenantPlan != null) ...[
            const SizedBox(height: 16),
            _ProfileItem(
              icon: Icons.business_outlined, 
              label: 'Plan SaaS', 
              value: _user!.tenantPlan!.toUpperCase(),
              valueColor: const Color(0xFF00F2FF),
            ),
          ],

          const SizedBox(height: 32),
          SizedBox(
            width: double.infinity,
            child: ElevatedButton.icon(
              icon: const Icon(Icons.lock_outline),
              label: const Text('Cambiar Contraseña'),
              onPressed: _showChangePasswordDialog,
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFF111629),
                foregroundColor: const Color(0xFF00F2FF),
                padding: const EdgeInsets.symmetric(vertical: 16),
                side: const BorderSide(color: Color(0xFF00F2FF)),
              ),
            ),
          )
        ],
      ),
    );
  }
}

class _ProfileItem extends StatelessWidget {
  final IconData icon;
  final String label;
  final String value;
  final Color? valueColor;

  const _ProfileItem({required this.icon, required this.label, required this.value, this.valueColor});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFF1A1F35),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: const Color(0xFF2A3050)),
      ),
      child: Row(
        children: [
          Icon(icon, color: const Color(0xFF00F2FF), size: 28),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  label,
                  style: const TextStyle(color: Colors.white54, fontSize: 12),
                ),
                const SizedBox(height: 4),
                Text(
                  value,
                  style: TextStyle(
                    color: valueColor ?? Colors.white,
                    fontSize: 16,
                    fontWeight: FontWeight.w500,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
