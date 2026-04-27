import 'dart:convert';
import 'dart:io';

import 'package:http/http.dart' as http;

import 'config.dart';
import 'session.dart';

class Backend {
  static Uri _uri(String path) => Uri.parse('${AppConfig.baseUrl}$path');

  static Future<Map<String, String>> _headers({
    bool jsonBody = false,
    bool withAuth = true,
  }) async {
    final headers = <String, String>{};
    if (jsonBody) headers['Content-Type'] = 'application/json';
    if (withAuth) {
      final token = await Session.getToken();
      if (token != null) headers['Authorization'] = 'Bearer $token';
    }
    return headers;
  }

  static Future<String?> login(String email, String password) async {
    final response = await http.post(
      _uri('/auth/login'),
      headers: await _headers(jsonBody: true, withAuth: false),
      body: jsonEncode({'email': email, 'password': password}),
    );
    if (response.statusCode != 200) return response.body;
    final data = jsonDecode(response.body) as Map<String, dynamic>;
    final token = data['access_token'] as String?;
    if (token != null) await Session.setToken(token);
    return null;
  }

  static Future<String?> register(
    String name,
    String email,
    String password,
  ) async {
    final response = await http.post(
      _uri('/auth/register'),
      headers: await _headers(jsonBody: true, withAuth: false),
      body: jsonEncode({
        'nombre': name,
        'email': email,
        'password': password,
        'rol': 'cliente',
      }),
    );
    if (response.statusCode == 201) return null;
    try {
      final error = jsonDecode(response.body);
      if (error is Map && error['detail'] != null) {
        return error['detail'].toString();
      }
    } catch (_) {}
    return 'Error ${response.statusCode}';
  }

  static Future<void> logout() async {
    final token = await Session.getToken();
    if (token == null) return;
    await http.post(_uri('/auth/logout'), headers: await _headers());
    await Session.setToken(null);
  }

  static Future<Map<String, dynamic>?> me() async {
    final response = await http.get(_uri('/me'), headers: await _headers());
    if (response.statusCode != 200) return null;

    final raw = jsonDecode(response.body) as Map<String, dynamic>;
    final vehiculos = (raw['vehiculos'] as List<dynamic>? ?? [])
        .whereType<Map<String, dynamic>>()
        .map(
          (vehicle) => <String, dynamic>{
            ...vehicle,
            'brand': vehicle['marca'],
            'model': vehicle['modelo'],
            'license_plate': vehicle['placa'],
          },
        )
        .toList();

    return {
      ...raw,
      'name': raw['nombre'],
      'role': raw['rol'],
      'vehicles': vehiculos,
    };
  }

  static Future<String?> addVehicle({
    required String brand,
    required String model,
    required String licensePlate,
    int? year,
  }) async {
    final body = <String, dynamic>{
      'marca': brand,
      'modelo': model,
      'placa': licensePlate,
    };
    if (year != null) body['anio'] = year;

    final response = await http.post(
      _uri('/me/vehicles'),
      headers: await _headers(jsonBody: true),
      body: jsonEncode(body),
    );
    if (response.statusCode == 201) return null;
    try {
      final error = jsonDecode(response.body);
      if (error is Map && error['detail'] != null) {
        return error['detail'].toString();
      }
    } catch (_) {}
    return 'Error ${response.statusCode}';
  }

  static Future<void> deleteVehicle(int id) async {
    await http.delete(_uri('/me/vehicles/$id'), headers: await _headers());
  }

  static Future<String?> forgotPassword(String email) async {
    final response = await http.post(
      _uri('/auth/forgot-password'),
      headers: await _headers(jsonBody: true, withAuth: false),
      body: jsonEncode({'email': email}),
    );
    if (response.statusCode == 200) {
      final data = jsonDecode(response.body) as Map<String, dynamic>;
      return data['debug_token']?.toString() ?? 'OK';
    }
    try {
      final error = jsonDecode(response.body);
      if (error is Map && error['detail'] != null) {
        return error['detail'].toString();
      }
    } catch (_) {}
    return 'Error ${response.statusCode}';
  }

  static Future<String?> resetPassword(
    String token,
    String newPassword,
  ) async {
    final response = await http.post(
      _uri('/auth/reset-password'),
      headers: await _headers(jsonBody: true, withAuth: false),
      body: jsonEncode({'token': token, 'new_password': newPassword}),
    );
    if (response.statusCode == 204) return null;
    try {
      final error = jsonDecode(response.body);
      if (error is Map && error['detail'] != null) {
        return error['detail'].toString();
      }
    } catch (_) {}
    return 'Error ${response.statusCode}';
  }

  static Future<String?> reportIncident({
    required String title,
    String? description,
    required double lat,
    required double lng,
    String? address,
    File? image,
    File? audio,
  }) async {
    final request = http.MultipartRequest('POST', _uri('/incidents'));
    request.headers.addAll(await _headers(withAuth: true));

    request.fields['titulo'] = title;
    request.fields['latitud'] = lat.toString();
    request.fields['longitud'] = lng.toString();
    if (description != null && description.isNotEmpty) {
      request.fields['descripcion'] = description;
    }
    if (address != null && address.isNotEmpty) {
      request.fields['direccion'] = address;
    }

    if (image != null) {
      request.files.add(
        await http.MultipartFile.fromPath('fotos', image.path),
      );
    }
    if (audio != null) {
      request.files.add(
        await http.MultipartFile.fromPath('audio', audio.path),
      );
    }

    final streamedResponse = await request.send();
    final response = await http.Response.fromStream(streamedResponse);

    if (response.statusCode == 201) return null;
    try {
      final error = jsonDecode(response.body);
      return error['detail']?.toString() ?? 'Error ${response.statusCode}';
    } catch (_) {}
    return 'Error ${response.statusCode}';
  }
}
