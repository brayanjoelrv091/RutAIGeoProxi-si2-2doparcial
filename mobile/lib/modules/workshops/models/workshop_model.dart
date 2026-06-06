/// Modelos de Talleres (P3).
library;

class Workshop {
  final int id;
  final int usuarioPropietarioId;
  final String nombre;
  final String direccion;
  final double latitud;
  final double longitud;
  final String? telefono;
  final String? email;
  final List<String>? especialidades;
  final bool estaActivo;
  final double calificacionPromedio;
  final String creadoEn;
  final bool enLinea;

  const Workshop({
    required this.id,
    required this.usuarioPropietarioId,
    required this.nombre,
    required this.direccion,
    required this.latitud,
    required this.longitud,
    this.telefono,
    this.email,
    this.especialidades,
    required this.estaActivo,
    required this.calificacionPromedio,
    required this.creadoEn,
    this.enLinea = false,
  });

  factory Workshop.fromJson(Map<String, dynamic> j) => Workshop(
        id: j['id'] as int,
        usuarioPropietarioId: j['usuario_propietario_id'] as int,
        nombre: j['nombre'] as String,
        direccion: j['direccion'] as String,
        latitud: (j['latitud'] as num).toDouble(),
        longitud: (j['longitud'] as num).toDouble(),
        telefono: j['telefono'] as String?,
        email: j['email'] as String?,
        especialidades: (j['especialidades'] as List<dynamic>?)
            ?.map((e) => e as String)
            .toList(),
        estaActivo: j['esta_activo'] as bool,
        calificacionPromedio:
            (j['calificacion_promedio'] as num).toDouble(),
        creadoEn: j['creado_en'] as String,
        enLinea: j['en_linea'] as bool? ?? false,
      );
}

class Technician {
  final int id;
  final int tallerId;
  final String nombre;
  final String? telefono;
  final String? especialidad;
  final bool estaDisponible;
  final double? latitud;
  final double? longitud;

  const Technician({
    required this.id,
    required this.tallerId,
    required this.nombre,
    this.telefono,
    this.especialidad,
    required this.estaDisponible,
    this.latitud,
    this.longitud,
  });

  factory Technician.fromJson(Map<String, dynamic> j) => Technician(
        id: j['id'] as int,
        tallerId: j['taller_id'] as int,
        nombre: j['nombre'] as String,
        telefono: j['telefono'] as String?,
        especialidad: j['especialidad'] as String?,
        estaDisponible: j['esta_disponible'] as bool,
        latitud: j['latitud'] != null ? (j['latitud'] as num).toDouble() : null,
        longitud: j['longitud'] != null ? (j['longitud'] as num).toDouble() : null,
      );
}

class ServiceRequest {
  final int id;
  final int incidenteId;
  final int tallerId;
  final int? tecnicoId;
  final String estado;
  final String? notas;
  final String creadoEn;
  final String? actualizadoEn;
  
  // Información extendida del incidente (Join)
  final String? tituloIncidente;
  final String? categoriaIncidente;
  final String? severidadIncidente;

  const ServiceRequest({
    required this.id,
    required this.incidenteId,
    required this.tallerId,
    this.tecnicoId,
    required this.estado,
    this.notas,
    required this.creadoEn,
    this.actualizadoEn,
    this.tituloIncidente,
    this.categoriaIncidente,
    this.severidadIncidente,
  });

  factory ServiceRequest.fromJson(Map<String, dynamic> j) => ServiceRequest(
        id: j['id'] as int,
        incidenteId: j['incidente_id'] as int,
        tallerId: j['taller_id'] as int,
        tecnicoId: j['tecnico_id'] as int?,
        estado: j['estado'] as String,
        notas: j['notas'] as String?,
        creadoEn: j['creado_en'] as String,
        actualizadoEn: j['actualizado_en'] as String?,
        tituloIncidente: j['titulo_incidente'] as String?,
        categoriaIncidente: j['categoria_incidente'] as String?,
        severidadIncidente: j['severidad_incidente'] as String?,
      );
}

class ServiceHistory extends ServiceRequest {
  final String? tituloIncidente;
  final String? categoriaIncidente;
  final String? severidadIncidente;

  const ServiceHistory({
    required super.id,
    required super.incidenteId,
    required super.tallerId,
    super.tecnicoId,
    required super.estado,
    super.notas,
    required super.creadoEn,
    super.actualizadoEn,
    this.tituloIncidente,
    this.categoriaIncidente,
    this.severidadIncidente,
  });

  factory ServiceHistory.fromJson(Map<String, dynamic> j) => ServiceHistory(
        id: j['id'] as int,
        incidenteId: j['incidente_id'] as int,
        tallerId: j['taller_id'] as int,
        tecnicoId: j['tecnico_id'] as int?,
        estado: j['estado'] as String,
        notas: j['notas'] as String?,
        creadoEn: j['creado_en'] as String,
        actualizadoEn: j['actualizado_en'] as String?,
        tituloIncidente: j['titulo_incidente'] as String?,
        categoriaIncidente: j['categoria_incidente'] as String?,
        severidadIncidente: j['severidad_incidente'] as String?,
      );
}
