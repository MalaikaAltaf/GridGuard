class Inspection {
  final String id;
  final String caseId;
  final String outcome;
  final List<String> tamperingType;
  final String note;
  final String? photoPath;
  final double? gpsLat;
  final double? gpsLng;
  final DateTime submittedAt;
  final bool isSynced;

  Inspection({
    required this.id,
    required this.caseId,
    required this.outcome,
    required this.tamperingType,
    required this.note,
    this.photoPath,
    this.gpsLat,
    this.gpsLng,
    required this.submittedAt,
    this.isSynced = false,
  });

  factory Inspection.fromJson(Map<String, dynamic> json) {
    return Inspection(
      id: json['id'],
      caseId: json['case_id'],
      outcome: json['outcome'],
      tamperingType: json['tampering_type'] != null 
          ? List<String>.from(json['tampering_type'])
          : [],
      note: json['note'] ?? '',
      photoPath: json['photo_path'],
      gpsLat: json['gps_lat'],
      gpsLng: json['gps_lng'],
      submittedAt: DateTime.parse(json['submitted_at']),
      isSynced: json['is_synced'] == 1,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'case_id': caseId,
      'outcome': outcome,
      'tampering_type': tamperingType,
      'note': note,
      'photo_path': photoPath,
      'gps_lat': gpsLat,
      'gps_lng': gpsLng,
      'submitted_at': submittedAt.toIso8601String(),
      'is_synced': isSynced ? 1 : 0,
    };
  }
}
