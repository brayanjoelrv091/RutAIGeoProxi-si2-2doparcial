/// Servicio de Autenticación Flutter (P1 — CU1-CU4).
library;

import 'dart:convert';
import '../../../core/api_client.dart';
import '../models/user_model.dart';
import 'package:shared_preferences/shared_preferences.dart';

class AuthService {
  // ── CU1 — Iniciar sesión ──────────────────────────────────────────

  static Future<String> login(String email, String password) async {
    final data = await ApiClient.post<Map<String, dynamic>>(
      '/auth/login',
      body: {'email': email, 'password': password},
      fromJson: (j) => j as Map<String, dynamic>,
      auth: false,
    );
    final token = data['access_token'] as String;
    await ApiClient.saveToken(token);
    return token;
  }

  // ── CU2 — Cerrar sesión ───────────────────────────────────────────

  static Future<void> logout() async {
    try {
      await ApiClient.post<void>('/auth/logout', fromJson: (_) {});
    } finally {
      await ApiClient.clearToken();
    }
  }

  // ── CU3 — Registrar usuario ───────────────────────────────────────

  static Future<UserProfile> register(
    String nombre,
    String email,
    String password,
  ) async {
    return ApiClient.post<UserProfile>(
      '/auth/register',
      body: {'nombre': nombre, 'email': email, 'password': password},
      fromJson: (j) => UserProfile.fromJson(j as Map<String, dynamic>),
      auth: false,
    );
  }

  // ── CU4a — Recuperar contraseña ───────────────────────────────────

  static Future<Map<String, dynamic>> forgotPassword(String email) async {
    return ApiClient.post<Map<String, dynamic>>(
      '/auth/forgot-password',
      body: {'email': email},
      fromJson: (j) => j as Map<String, dynamic>,
      auth: false,
    );
  }

  // ── CU4b — Restablecer contraseña ─────────────────────────────────

  static Future<void> resetPassword(String token, String newPassword) async {
    await ApiClient.post<void>(
      '/auth/reset-password',
      body: {'token': token, 'new_password': newPassword},
      fromJson: (_) {},
      auth: false,
    );
  }

  // ── CU6 — Ver perfil con vehículos ───────────────────────────────

  static Future<UserProfile> getMe() async {
    return ApiClient.get<UserProfile>(
      '/me',
      fromJson: (j) => UserProfile.fromJson(j as Map<String, dynamic>),
    );
  }

  static Future<UserProfile> updateProfile(
      {String? nombre, String? telefono}) async {
    final body = <String, dynamic>{};
    if (nombre != null) body['nombre'] = nombre;
    if (telefono != null) body['telefono'] = telefono;
    return ApiClient.patch<UserProfile>(
      '/me',
      body: body,
      fromJson: (j) => UserProfile.fromJson(j as Map<String, dynamic>),
    );
  }

  static Future<void> changePassword(String currentPassword, String newPassword) async {
    await ApiClient.patch<void>(
      '/me/password',
      body: {'current_password': currentPassword, 'new_password': newPassword},
      fromJson: (_) {},
    );
  }

  static Future<Map<String, dynamic>> addVehicle({
    required String marca,
    required String modelo,
    required String placa,
    int? anio,
    String? color,
  }) async {
    return ApiClient.post<Map<String, dynamic>>(
      '/me/vehicles',
      body: {
        'marca': marca,
        'modelo': modelo,
        'placa': placa,
        ...?anio == null ? null : {'anio': anio},
        ...?color == null ? null : {'color': color},
      },
      fromJson: (j) => j as Map<String, dynamic>,
    );
  }

  static Future<void> deleteVehicle(int vehicleId) async {
    await ApiClient.delete<void>(
      '/me/vehicles/$vehicleId',
      fromJson: (_) {},
    );
  }

  static Future<void> saveCredentials(String email, String password) async {
    final prefs = await SharedPreferences.getInstance();
    final jsonStr = prefs.getString('saved_accounts');
    Map<String, dynamic> accounts = {};
    if (jsonStr != null) {
      accounts = jsonDecode(jsonStr) as Map<String, dynamic>;
    }
    accounts[email] = password;
    await prefs.setString('saved_accounts', jsonEncode(accounts));
  }

  static Future<Map<String, String>> getAllSavedCredentials() async {
    final prefs = await SharedPreferences.getInstance();
    final jsonStr = prefs.getString('saved_accounts');
    if (jsonStr != null) {
      final decoded = jsonDecode(jsonStr) as Map<String, dynamic>;
      return decoded.map((key, value) => MapEntry(key, value.toString()));
    }
    return {};
  }

  static Future<void> clearSavedCredentials() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('saved_accounts');
  }

  // ── Helpers ───────────────────────────────────────────────────────

  static Future<String?> getRoleFromToken() async {
    final token = await ApiClient.getToken();
    if (token == null || token.isEmpty) return null;
    try {
      final parts = token.split('.');
      if (parts.length != 3) return null;
      final payload = utf8.decode(base64Url.decode(base64Url.normalize(parts[1])));
      final data = jsonDecode(payload) as Map<String, dynamic>;
      return data['rol'] as String?;
    } catch (e) {
      return null;
    }
  }

  static Future<bool> isLoggedIn() async {
    final token = await ApiClient.getToken();
    return token != null && token.isNotEmpty;
  }
}
