import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:feather_icons/feather_icons.dart';
import '../theme.dart';
import '../providers/providers.dart';
import '../models/case_model.dart';

class MyCasesScreen extends ConsumerStatefulWidget {
  const MyCasesScreen({super.key});

  @override
  ConsumerState<MyCasesScreen> createState() => _MyCasesScreenState();
}

class _MyCasesScreenState extends ConsumerState<MyCasesScreen> {
  @override
  void initState() {
    super.initState();
    Future.microtask(() => ref.read(casesProvider.notifier).syncCases());
  }

  @override
  Widget build(BuildContext context) {
    final casesState = ref.watch(casesProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('My Cases', style: TextStyle(fontSize: 16)),
        actions: [
          IconButton(
            icon: const Icon(FeatherIcons.refreshCw, size: 19),
            onPressed: () {
              ref.read(casesProvider.notifier).syncCases();
            },
          ),
        ],
      ),
      body: Column(
        children: [
          _buildPillRow(),
          _buildDemoBanner(),
          Expanded(
            child: casesState.when(
              loading: () => const Center(child: CircularProgressIndicator()),
              error: (err, stack) => Center(child: Text('Error: $err')),
              data: (cases) {
                if (cases.isEmpty) return _buildEmptyState();
                return ListView.separated(
                  padding: const EdgeInsets.all(16),
                  itemCount: cases.length,
                  separatorBuilder: (context, index) => const SizedBox(height: 14),
                  itemBuilder: (context, index) {
                    return _buildCaseRow(cases[index]);
                  },
                );
              },
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildPillRow() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
      decoration: const BoxDecoration(
        color: AppTheme.panelMid,
        border: Border(bottom: BorderSide(color: AppTheme.seam)),
      ),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 4),
            decoration: BoxDecoration(
              color: AppTheme.panelRaised,
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: AppTheme.riskLow),
            ),
            child: Row(
              children: [
                const Icon(FeatherIcons.wifi, size: 11, color: AppTheme.riskLowDim),
                const SizedBox(width: 5),
                Text(
                  'Online',
                  style: AppTheme.monoTextStyle.copyWith(fontSize: 10.5, fontWeight: FontWeight.bold, color: AppTheme.riskLowDim),
                )
              ],
            ),
          ),
          const Spacer(),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 4),
            decoration: BoxDecoration(
              color: AppTheme.panelRaised,
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: AppTheme.steel),
            ),
            child: const Text(
              'EN',
              style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: AppTheme.steelDeep),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildDemoBanner() {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 6, horizontal: 10),
      decoration: const BoxDecoration(
        gradient: LinearGradient(
          colors: [Color(0xFFD9A53C), AppTheme.alertAmber, AppTheme.alertAmberDeep],
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
          stops: [0.0, 0.55, 1.0],
        ),
        border: Border(bottom: BorderSide(color: AppTheme.alertAmberDeep, width: 2)),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Icon(FeatherIcons.alertTriangle, size: 12, color: AppTheme.alertAmberText),
          const SizedBox(width: 6),
          Text(
            'Demo / benchmark data — not live DISCO data',
            style: AppTheme.monoTextStyle.copyWith(fontSize: 10.5, fontWeight: FontWeight.bold, color: AppTheme.alertAmberText),
          )
        ],
      ),
    );
  }

  Widget _buildEmptyState() {
    return Column(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        Container(
          width: 56,
          height: 56,
          decoration: BoxDecoration(
            color: AppTheme.panelWell,
            shape: BoxShape.circle,
            boxShadow: const [BoxShadow(color: Colors.black26, blurRadius: 4, offset: Offset(0, 2))],
          ),
          child: const Icon(FeatherIcons.inbox, size: 26, color: AppTheme.inkFaint),
        ),
        const SizedBox(height: 12),
        const Text('No cases assigned', style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold)),
        const SizedBox(height: 8),
        const Text('When an officer assigns you a case, it\'ll show up here.', style: TextStyle(fontSize: 13, color: AppTheme.inkSoft)),
      ],
    );
  }

  Widget _buildCaseRow(CaseModel c) {
    return InkWell(
      onTap: () {
        // Navigate to case detail
      },
      child: Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: AppTheme.panelRaised,
          border: Border.all(color: AppTheme.seam),
          borderRadius: BorderRadius.circular(10),
        ),
        child: Row(
          children: [
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(c.address, style: const TextStyle(fontSize: 14.5, fontWeight: FontWeight.bold, height: 1.3)),
                  const SizedBox(height: 6),
                  Wrap(
                    spacing: 8,
                    runSpacing: 4,
                    children: [
                      _buildRiskBadge(c.riskBand),
                      _buildStatusChip(c.status),
                      _buildSyncChip(c.isSynced),
                    ],
                  ),
                ],
              ),
            ),
            const Icon(FeatherIcons.chevronRight, color: AppTheme.inkFaint, size: 18),
          ],
        ),
      ),
    );
  }

  Widget _buildRiskBadge(String band) {
    // simplified badge
    Color color;
    String label;
    if (band == 'high') { color = AppTheme.riskHigh; label = 'High'; }
    else if (band == 'medium') { color = AppTheme.riskMed; label = 'Medium'; }
    else { color = AppTheme.riskLow; label = 'Low'; }

    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          width: 20, height: 20,
          decoration: BoxDecoration(color: color, shape: BoxShape.circle),
        ),
        const SizedBox(width: 5),
        Text(label, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
      ],
    );
  }

  Widget _buildStatusChip(String status) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
      decoration: BoxDecoration(
        color: const Color(0xFFE3EDF2),
        border: Border.all(color: AppTheme.steel),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Text(status, style: const TextStyle(fontSize: 10, color: AppTheme.steelDeep, fontWeight: FontWeight.bold)),
    );
  }

  Widget _buildSyncChip(bool isSynced) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
      decoration: BoxDecoration(
        color: isSynced ? const Color(0xFFDDE9DD) : const Color(0xFFF5E9CD),
        border: Border.all(color: isSynced ? AppTheme.riskLow : AppTheme.alertAmber),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Text(isSynced ? 'Synced' : 'Pending', style: TextStyle(fontSize: 10, color: isSynced ? AppTheme.riskLowDim : AppTheme.alertAmberText, fontWeight: FontWeight.bold)),
    );
  }
}
