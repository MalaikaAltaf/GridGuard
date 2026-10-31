import 'package:flutter/material.dart';
import 'package:feather_icons/feather_icons.dart';
import '../theme.dart';
import '../models/case_model.dart';
import 'inspection_form_screen.dart';

class CaseDetailScreen extends StatelessWidget {
  final CaseModel caseData;

  const CaseDetailScreen({super.key, required this.caseData});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        leading: IconButton(
          icon: const Icon(FeatherIcons.chevronLeft),
          onPressed: () => Navigator.of(context).pop(),
        ),
        title: const Text('Case Detail', style: TextStyle(fontSize: 16)),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            _buildInfoRow('ADDRESS', caseData.address),
            const SizedBox(height: 12),
            _buildInfoRow('METER ID', caseData.meterId),
            const SizedBox(height: 24),
            _buildExplanationSlip(),
            if (caseData.assignmentNote != null) ...[
              const SizedBox(height: 16),
              _buildNoteCallout(),
            ],
            const SizedBox(height: 32),
            ElevatedButton.icon(
              onPressed: () {
                Navigator.of(context).push(
                  MaterialPageRoute(builder: (_) => InspectionFormScreen(caseId: caseData.id)),
                );
              },
              icon: const Icon(FeatherIcons.playCircle, size: 18),
              label: const Text('Start Inspection'),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildInfoRow(String label, String value) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label,
          style: AppTheme.monoTextStyle.copyWith(
            fontSize: 10.5,
            color: AppTheme.inkFaint,
            letterSpacing: 1.2,
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 4),
        Text(
          value,
          style: const TextStyle(
            fontSize: 15,
            fontWeight: FontWeight.bold,
            color: AppTheme.ink,
            height: 1.4,
          ),
        ),
      ],
    );
  }

  Widget _buildExplanationSlip() {
    return Stack(
      clipBehavior: Clip.none,
      children: [
        Container(
          margin: const EdgeInsets.only(top: 8),
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: const Color(0xFFFBF8EF),
            border: Border(
              left: const BorderSide(color: AppTheme.copper, width: 4),
              top: const BorderSide(color: AppTheme.seam),
              right: const BorderSide(color: AppTheme.seam),
              bottom: const BorderSide(color: AppTheme.seam),
            ),
            borderRadius: BorderRadius.circular(6),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                caseData.explanationEn,
                style: const TextStyle(fontSize: 14.5, height: 1.6),
              ),
              const Divider(color: AppTheme.seam, height: 24),
              Text(
                caseData.explanationUr,
                style: AppTheme.urduTextStyle.copyWith(fontSize: 16, height: 1.8),
                textAlign: TextAlign.right,
              ),
            ],
          ),
        ),
        Positioned(
          top: -1,
          left: 14,
          child: Container(
            color: AppTheme.panelRaised,
            padding: const EdgeInsets.symmetric(horizontal: 6),
            child: Text(
              'WHY THIS CONSUMER WAS FLAGGED',
              style: AppTheme.monoTextStyle.copyWith(
                fontSize: 9,
                fontWeight: FontWeight.bold,
                color: AppTheme.inkFaint,
                letterSpacing: 1.2,
              ),
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildNoteCallout() {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: AppTheme.panelMid,
        border: Border.all(color: AppTheme.seam),
        borderRadius: BorderRadius.circular(6),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Icon(FeatherIcons.messageSquare, size: 15, color: AppTheme.inkFaint),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              caseData.assignmentNote!,
              style: const TextStyle(fontSize: 13.5, color: AppTheme.inkSoft, height: 1.5),
            ),
          ),
        ],
      ),
    );
  }
}
