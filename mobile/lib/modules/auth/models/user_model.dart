/// Modelos de Usuarios y Vehículos (P1).
library;

class Vehicle {
  final int id;
  final int usuarioId;
  final String marca;
  final String modelo;
  final String placa;
  final int? anio;
  final String? color;

  const Vehicle({
    required this.id,
    required this.usuarioId,
    required this.marca,
    required this.modelo,
    required this.placa,
    this.anio,
    this.color,
  });

  factory Vehicle.fromJson(Map<String, dynamic> j) => Vehicle(
        id: j['id'] as int,
        usuarioId: j['usuario_id'] as int,
        marca: j['marca'] as String,
        modelo: j['modelo'] as String,
        placa: j['placa'] as String,
        anio: j['anio'] as int?,
        color: j['color'] as String?,
      );
}

class UserProfile {
  final int id;
  final String nombre;
  final String email;
  final String? telefono;
  final bool estaActivo;
  final String rol;
  final List<Vehicle> vehiculos;

  const UserProfile({
    required this.id,
    required this.nombre,
    required this.email,
    this.telefono,
    required this.estaActivo,
    required this.rol,
    required this.vehiculos,
  });

  factory UserProfile.fromJson(Map<String, dynamic> j) => UserProfile(
        id: j['id'] as int,
        nombre: j['nombre'] as String,
        email: j['email'] as String,
        telefono: j['telefono'] as String?,
        estaActivo: j['esta_activo'] as bool,
        rol: j['rol'] as String,
        vehiculos: (j['vehiculos'] as List<dynamic>? ?? [])
            .map((v) => Vehicle.fromJson(v as Map<String, dynamic>))
            .toList(),
      );
}
