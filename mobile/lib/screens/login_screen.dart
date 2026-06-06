import 'package:flutter/material.dart';

import '../backend.dart';
import '../modules/auth/screens/forgot_password_screen.dart';
import '../modules/auth/screens/register_screen.dart';
import '../modules/auth/services/saved_accounts.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key, required this.onLoggedIn});

  final VoidCallback onLoggedIn;

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _email = TextEditingController();
  final _password = TextEditingController();
  String? _error;
  bool _loading = false;
  List<SavedAccount> _savedAccounts = [];

  @override
  void initState() {
    super.initState();
    _loadSaved();
  }

  Future<void> _loadSaved() async {
    final list = await SavedAccountsManager.getSavedAccounts();
    if (mounted) setState(() => _savedAccounts = list);
  }

  @override
  void dispose() {
    _email.dispose();
    _password.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    setState(() {
      _error = null;
      _loading = true;
    });
    final err = await Backend.login(_email.text.trim(), _password.text);
    if (!mounted) return;
    setState(() => _loading = false);
    if (err == null) {
      final email = _email.text.trim();
      final pwd = _password.text;
      final alreadySaved = _savedAccounts.any((a) => a.email.toLowerCase() == email.toLowerCase() && a.password == pwd);
      
      if (!alreadySaved) {
        final save = await showDialog<bool>(
          context: context,
          builder: (ctx) => AlertDialog(
            backgroundColor: const Color(0xFF111629),
            title: const Text('Guardar contraseña', style: TextStyle(color: Colors.white)),
            content: Text('¿Deseas guardar la contraseña para $email?', style: const TextStyle(color: Colors.white70)),
            actions: [
              TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('No', style: TextStyle(color: Colors.white54))),
              TextButton(onPressed: () => Navigator.pop(ctx, true), child: const Text('Sí, guardar', style: TextStyle(color: Color(0xFF00F2FF)))),
            ],
          ),
        );
        if (save == true) {
          await SavedAccountsManager.saveAccount(email, pwd);
        }
      }
      widget.onLoggedIn();
    } else {
      setState(
        () => _error = err.length > 120 ? 'Credenciales incorrectas.' : err,
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('RutAIGeoProxi - Login')),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          const Text(
            'Inicia sesión en RutAIGeoProxi',
            style: TextStyle(color: Colors.white54),
          ),
          const SizedBox(height: 16),
          if (_savedAccounts.isNotEmpty) ...[
            DropdownButtonFormField<SavedAccount>(
              dropdownColor: const Color(0xFF111629),
              decoration: const InputDecoration(
                labelText: 'Cuentas Guardadas',
                filled: true,
                fillColor: Color(0xFF111629),
              ),
              style: const TextStyle(color: Colors.white),
              items: _savedAccounts.map((acc) {
                return DropdownMenuItem(
                  value: acc,
                  child: Text(acc.email),
                );
              }).toList(),
              onChanged: (acc) {
                if (acc != null) {
                  _email.text = acc.email;
                  _password.text = acc.password;
                }
              },
              hint: const Text('Seleccionar cuenta guardada...', style: TextStyle(color: Colors.white54)),
            ),
            const SizedBox(height: 16),
          ],
          TextField(
            controller: _email,
            style: const TextStyle(color: Colors.white),
            decoration: const InputDecoration(labelText: 'Correo', filled: true, fillColor: Color(0xFF111629)),
            keyboardType: TextInputType.emailAddress,
            autocorrect: false,
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _password,
            style: const TextStyle(color: Colors.white),
            decoration: const InputDecoration(labelText: 'Contrasena', filled: true, fillColor: Color(0xFF111629)),
            obscureText: true,
          ),
          if (_error != null) ...[
            const SizedBox(height: 8),
            Text(_error!, style: const TextStyle(color: Colors.red)),
          ],
          const SizedBox(height: 16),
          FilledButton(
            onPressed: _loading ? null : _submit,
            child: Text(_loading ? 'Entrando...' : 'Entrar'),
          ),
          TextButton(
            onPressed: _loading
                ? null
                : () {
                    Navigator.of(context).push(
                      MaterialPageRoute<void>(
                        builder: (_) => const RegisterScreen(),
                      ),
                    );
                  },
            child: const Text('Crear cuenta'),
          ),
          TextButton(
            onPressed: _loading
                ? null
                : () {
                    Navigator.of(context).push(
                      MaterialPageRoute<void>(
                        builder: (_) => const ForgotPasswordScreen(),
                      ),
                    );
                  },
            child: const Text('Olvide mi contrasena'),
          ),
        ],
      ),
    );
  }
}
