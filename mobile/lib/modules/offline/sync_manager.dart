import 'dart:async';
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'offline_queue.dart';
import 'connectivity_monitor.dart';
import '../../config.dart';

/// P8 · CU-22 — Sincronización automática de incidentes offline.
///
/// Flujo:
///   1. ConnectivityMonitor detecta que la conexión volvió
///   2. SyncManager obtiene la cola de pendientes
///   3. Envía batch al endpoint /realtime/incidents/offline-sync
///   4. Marca como sincronizados los exitosos
///   5. Notifica al UI del resultado
///
/// Deduplicación (CU-23):
///   El backend rechaza duplicados por idempotency_key con status 'duplicate'
///   sin generar error. El item se marca como synced igualmente.

typedef SyncCallback = void Function(SyncResult result);

class SyncResult {
  final int total;
  final int created;
  final int duplicates;
  final int errors;
  final List<SyncItemResult> items;

  SyncResult({
    required this.total,
    required this.created,
    required this.duplicates,
    required this.errors,
    required this.items,
  });

  factory SyncResult.fromJson(Map<String, dynamic> json) => SyncResult(
    total: json['total'] ?? 0,
    created: json['created'] ?? 0,
    duplicates: json['duplicates'] ?? 0,
    errors: json['errors'] ?? 0,
    items: (json['results'] as List<dynamic>?)
        ?.map((e) => SyncItemResult.fromJson(e))
        .toList() ?? [],
  );

  factory SyncResult.empty() => SyncResult(
    total: 0, created: 0, duplicates: 0, errors: 0, items: [],
  );

  bool get hasErrors => errors > 0;
  bool get allSucceeded => errors == 0 && total > 0;
}

class SyncItemResult {
  final String idempotencyKey;
  final String status; // created | duplicate | error
  final int? incidentId;
  final String message;

  SyncItemResult({
    required this.idempotencyKey,
    required this.status,
    this.incidentId,
    required this.message,
  });

  factory SyncItemResult.fromJson(Map<String, dynamic> json) => SyncItemResult(
    idempotencyKey: json['idempotency_key'],
    status: json['status'],
    incidentId: json['incident_id'],
    message: json['message'],
  );
}


class SyncManager {
  final ConnectivityMonitor _connectivity;
  StreamSubscription? _connectivitySub;
  bool _isSyncing = false;
  SyncCallback? onSyncComplete;

  SyncManager({ConnectivityMonitor? connectivity})
    : _connectivity = connectivity ?? ConnectivityMonitor();

  /// Inicia el listener de conectividad para auto-sync.
  void startAutoSync(String token) {
    _connectivitySub?.cancel();
    _connectivitySub = _connectivity.onConnectivityChanged.listen((isOnline) {
      if (isOnline && !_isSyncing) {
        syncNow(token);
      }
    });
  }

  /// Detiene el auto-sync.
  void stopAutoSync() {
    _connectivitySub?.cancel();
    _connectivitySub = null;
  }

  /// Sincroniza manualmente la cola de pendientes.
  Future<SyncResult> syncNow(String token) async {
    if (_isSyncing) return SyncResult.empty();

    final pending = await OfflineQueue.getPending();
    if (pending.isEmpty) return SyncResult.empty();

    _isSyncing = true;

    try {
      final payload = {
        'items': pending.map((item) => {
          final json = item.toJson();
          json.remove('synced'); // No enviar flag interno
          return json;
        }).toList(),
      };

      final response = await http.post(
        Uri.parse('${AppConfig.apiBaseUrl}/realtime/incidents/offline-sync'),
        headers: {
          'Authorization': 'Bearer $token',
          'Content-Type': 'application/json',
        },
        body: jsonEncode(payload),
      ).timeout(const Duration(seconds: 30));

      if (response.statusCode == 200) {
        final result = SyncResult.fromJson(jsonDecode(response.body));

        // Marcar items sincronizados
        for (final item in result.items) {
          if (item.status == 'created' || item.status == 'duplicate') {
            await OfflineQueue.markSynced(item.idempotencyKey);
          }
        }

        // Limpiar items ya sincronizados
        await OfflineQueue.clearSynced();

        onSyncComplete?.call(result);
        return result;
      } else {
        print('[SyncManager] Error HTTP ${response.statusCode}: ${response.body}');
        return SyncResult.empty();
      }
    } catch (e) {
      print('[SyncManager] Error de sincronización: $e');
      return SyncResult.empty();
    } finally {
      _isSyncing = false;
    }
  }

  void dispose() {
    stopAutoSync();
  }
}
