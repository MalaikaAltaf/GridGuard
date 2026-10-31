import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../api/api_client.dart';
import '../local_db/database_helper.dart';
import '../models/case_model.dart';
import '../models/inspection.dart';
import '../models/user.dart';

final apiClientProvider = Provider<ApiClient>((ref) => ApiClient());
final databaseHelperProvider = Provider<DatabaseHelper>((ref) => DatabaseHelper.instance);

final authProvider = StateNotifierProvider<AuthNotifier, User?>((ref) {
  return AuthNotifier(ref.read(apiClientProvider));
});

class AuthNotifier extends StateNotifier<User?> {
  final ApiClient _apiClient;

  AuthNotifier(this._apiClient) : super(null);

  Future<void> login(String email, String password) async {
    final user = await _apiClient.login(email, password);
    state = user;
  }

  void logout() {
    state = null;
  }
}

final casesProvider = StateNotifierProvider<CasesNotifier, AsyncValue<List<CaseModel>>>((ref) {
  return CasesNotifier(
    ref.read(apiClientProvider),
    ref.read(databaseHelperProvider),
  );
});

class CasesNotifier extends StateNotifier<AsyncValue<List<CaseModel>>> {
  final ApiClient _apiClient;
  final DatabaseHelper _dbHelper;

  CasesNotifier(this._apiClient, this._dbHelper) : super(const AsyncValue.loading()) {
    _loadLocalCases();
  }

  Future<void> _loadLocalCases() async {
    try {
      final localCases = await _dbHelper.getCases();
      if (localCases.isNotEmpty) {
        state = AsyncValue.data(localCases);
      }
    } catch (e) {
      // Ignore local fetch error for initial load
    }
  }

  Future<void> syncCases() async {
    state = const AsyncValue.loading();
    try {
      // Mock API call failure if offline, assuming it will throw Exception
      final remoteCases = await _apiClient.getMyCases();
      await _dbHelper.insertCases(remoteCases);
      state = AsyncValue.data(remoteCases);
    } catch (e) {
      // If offline, just show local cases
      final localCases = await _dbHelper.getCases();
      state = AsyncValue.data(localCases);
    }
  }
}

final syncProvider = StateNotifierProvider<SyncNotifier, bool>((ref) {
  return SyncNotifier(
    ref.read(apiClientProvider),
    ref.read(databaseHelperProvider),
  );
});

class SyncNotifier extends StateNotifier<bool> {
  final ApiClient _apiClient;
  final DatabaseHelper _dbHelper;

  SyncNotifier(this._apiClient, this._dbHelper) : super(false);

  Future<void> submitInspection(Inspection inspection) async {
    // Save locally first
    await _dbHelper.insertInspection(inspection);
    
    // Attempt sync
    syncPendingInspections();
  }

  Future<void> syncPendingInspections() async {
    state = true; // Syncing
    try {
      final unsynced = await _dbHelper.getUnsyncedInspections();
      for (var inspection in unsynced) {
        try {
          await _apiClient.submitInspection(inspection);
          await _dbHelper.markInspectionAsSynced(inspection.id);
        } catch (e) {
          // Sync failed for this item, remain unsynced
        }
      }
    } finally {
      state = false;
    }
  }
}
