import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:feather_icons/feather_icons.dart';
import '../theme.dart';
import '../providers/providers.dart';
import '../models/inspection.dart';

class InspectionFormScreen extends ConsumerStatefulWidget {
  final String caseId;

  const InspectionFormScreen({super.key, required this.caseId});

  @override
  ConsumerState<InspectionFormScreen> createState() => _InspectionFormScreenState();
}

class _InspectionFormScreenState extends ConsumerState<InspectionFormScreen> {
  String? _outcome;
  final Set<String> _tamperingTypes = {};
  final TextEditingController _noteController = TextEditingController();

  void _saveInspection() {
    if (_outcome == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Choose an outcome before saving.')),
      );
      return;
    }

    final inspection = Inspection(
      id: DateTime.now().millisecondsSinceEpoch.toString(),
      caseId: widget.caseId,
      outcome: _outcome!,
      tamperingType: _tamperingTypes.toList(),
      note: _noteController.text,
      submittedAt: DateTime.now(),
    );

    ref.read(syncProvider.notifier).submitInspection(inspection);
    Navigator.of(context).popUntil((route) => route.isFirst);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        leading: IconButton(
          icon: const Icon(FeatherIcons.chevronLeft),
          onPressed: () => Navigator.of(context).pop(),
        ),
        title: const Text('Inspection Form', style: TextStyle(fontSize: 16)),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            _buildSectionTitle('OUTCOME'),
            const SizedBox(height: 10),
            _buildOutcomeOption('confirmed', 'Confirmed theft'),
            const SizedBox(height: 8),
            _buildOutcomeOption('honest', 'Honest / no issue'),
            const SizedBox(height: 8),
            _buildOutcomeOption('inconclusive', 'Inconclusive'),
            
            const SizedBox(height: 24),
            _buildSectionTitle('TAMPERING TYPE'),
            const Text('Select all that apply', style: TextStyle(fontSize: 11.5, color: AppTheme.inkFaint)),
            const SizedBox(height: 10),
            _buildCheckItem('bypass', 'Bypass wire found on service line'),
            _buildCheckItem('reversed', 'Meter reversed'),
            _buildCheckItem('remote', 'Remote-control device'),

            const SizedBox(height: 24),
            _buildSectionTitle('NOTE'),
            const SizedBox(height: 10),
            TextField(
              controller: _noteController,
              maxLines: 4,
              decoration: const InputDecoration(
                hintText: 'Add any details from the site visit...',
              ),
            ),
            
            const SizedBox(height: 32),
            ElevatedButton(
              onPressed: _saveInspection,
              child: const Text('Save Inspection'),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSectionTitle(String title) {
    return Text(
      title,
      style: const TextStyle(
        fontSize: 11,
        fontWeight: FontWeight.bold,
        letterSpacing: 1.2,
        color: AppTheme.inkSoft,
      ),
    );
  }

  Widget _buildOutcomeOption(String value, String label) {
    final isSelected = _outcome == value;
    return InkWell(
      onTap: () => setState(() => _outcome = value),
      child: Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: isSelected ? const Color(0xFFF6E9DC) : AppTheme.panelRaised,
          border: Border.all(
            color: isSelected ? AppTheme.copper : AppTheme.panelWellDk,
            width: 1.5,
          ),
          borderRadius: BorderRadius.circular(10),
        ),
        child: Row(
          children: [
            Container(
              width: 22, height: 22,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                border: Border.all(
                  color: isSelected ? AppTheme.copper : AppTheme.seamDark,
                  width: 2,
                ),
              ),
              padding: const EdgeInsets.all(3),
              child: isSelected
                  ? Container(decoration: const BoxDecoration(shape: BoxShape.circle, color: AppTheme.copper))
                  : null,
            ),
            const SizedBox(width: 12),
            Text(label, style: const TextStyle(fontSize: 14.5, fontWeight: FontWeight.bold)),
          ],
        ),
      ),
    );
  }

  Widget _buildCheckItem(String value, String label) {
    final isChecked = _tamperingTypes.contains(value);
    return InkWell(
      onTap: () {
        setState(() {
          if (isChecked) {
            _tamperingTypes.remove(value);
          } else {
            _tamperingTypes.add(value);
          }
        });
      },
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 13, horizontal: 4),
        decoration: const BoxDecoration(
          border: Border(bottom: BorderSide(color: AppTheme.panelMid)),
        ),
        child: Row(
          children: [
            Container(
              width: 22, height: 22,
              decoration: BoxDecoration(
                color: isChecked ? AppTheme.riskLow : AppTheme.panelWell,
                borderRadius: BorderRadius.circular(5),
              ),
              child: isChecked ? const Icon(FeatherIcons.check, size: 14, color: Colors.white) : null,
            ),
            const SizedBox(width: 12),
            Expanded(child: Text(label, style: const TextStyle(fontSize: 14, height: 1.4))),
          ],
        ),
      ),
    );
  }
}
