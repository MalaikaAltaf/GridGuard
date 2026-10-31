class CaseModel {
  final String id;
  final String consumerId;
  final String address;
  final String meterId;
  final String riskBand;
  final double riskScore;
  final String status;
  final String? assignmentNote;
  final String explanationEn;
  final String explanationUr;
  final bool isSynced;

  CaseModel({
    required this.id,
    required this.consumerId,
    required this.address,
    required this.meterId,
    required this.riskBand,
    required this.riskScore,
    required this.status,
    this.assignmentNote,
    required this.explanationEn,
    required this.explanationUr,
    this.isSynced = true,
  });

  factory CaseModel.fromJson(Map<String, dynamic> json) {
    return CaseModel(
      id: json['id'],
      consumerId: json['consumer_id'] ?? '',
      address: json['address'] ?? '',
      meterId: json['external_ref'] ?? '',
      riskBand: json['risk_band'] ?? 'low',
      riskScore: json['score'] != null ? (json['score'] as num).toDouble() : 0.0,
      status: json['status'] ?? 'assigned',
      assignmentNote: json['assignment_note'],
      explanationEn: json['explanation_text_en'] ?? '',
      explanationUr: json['explanation_text_ur'] ?? '',
      isSynced: json['is_synced'] ?? true,
    );
  }

  /// Parses the CaseListItem shape returned by GET /cases and GET /cases/mine.
  /// Field names differ from the full CaseDetail shape.
  factory CaseModel.fromListJson(Map<String, dynamic> json) {
    return CaseModel(
      id: json['id']?.toString() ?? '',
      consumerId: json['consumer_id']?.toString() ?? '',
      address: json['consumer_address'] ?? json['address'] ?? '',
      meterId: json['consumer_external_ref'] ?? json['external_ref'] ?? '',
      riskBand: json['risk_band'] ?? 'low',
      // CaseListItem doesn't include score; default to 0 until detail is loaded
      riskScore: json['score'] != null ? (json['score'] as num).toDouble() : 0.0,
      status: json['status'] ?? 'assigned',
      assignmentNote: json['assignment_note'],
      explanationEn: json['explanation_text_en'] ?? '',
      explanationUr: json['explanation_text_ur'] ?? '',
      isSynced: true,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'consumer_id': consumerId,
      'address': address,
      'external_ref': meterId,
      'risk_band': riskBand,
      'score': riskScore,
      'status': status,
      'assignment_note': assignmentNote,
      'explanation_text_en': explanationEn,
      'explanation_text_ur': explanationUr,
      'is_synced': isSynced ? 1 : 0,
    };
  }
}
