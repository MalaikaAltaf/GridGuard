import 'package:sqflite/sqflite.dart';
import 'package:path/path.dart';
import '../models/case_model.dart';
import '../models/inspection.dart';

class DatabaseHelper {
  static final DatabaseHelper instance = DatabaseHelper._init();
  static Database? _database;

  DatabaseHelper._init();

  Future<Database> get database async {
    if (_database != null) return _database!;
    _database = await _initDB('grid_guard.db');
    return _database!;
  }

  Future<Database> _initDB(String filePath) async {
    final dbPath = await getDatabasesPath();
    final path = join(dbPath, filePath);

    return await openDatabase(path, version: 1, onCreate: _createDB);
  }

  Future _createDB(Database db, int version) async {
    const idType = 'TEXT PRIMARY KEY';
    const textType = 'TEXT NOT NULL';
    const textNullableType = 'TEXT';
    const boolType = 'BOOLEAN NOT NULL';
    const realType = 'REAL NOT NULL';
    const realNullableType = 'REAL';

    await db.execute('''
CREATE TABLE cases (
  id $idType,
  consumer_id $textType,
  address $textType,
  external_ref $textType,
  risk_band $textType,
  score $realType,
  status $textType,
  assignment_note $textNullableType,
  explanation_text_en $textType,
  explanation_text_ur $textType,
  is_synced $boolType
)
''');

    await db.execute('''
CREATE TABLE inspections (
  id $idType,
  case_id $textType,
  outcome $textType,
  tampering_type $textType,
  note $textNullableType,
  photo_path $textNullableType,
  gps_lat $realNullableType,
  gps_lng $realNullableType,
  submitted_at $textType,
  is_synced $boolType
)
''');
  }

  Future<void> insertCases(List<CaseModel> cases) async {
    final db = await instance.database;
    Batch batch = db.batch();
    for (var c in cases) {
      batch.insert('cases', c.toJson(), conflictAlgorithm: ConflictAlgorithm.replace);
    }
    await batch.commit();
  }

  Future<List<CaseModel>> getCases() async {
    final db = await instance.database;
    final result = await db.query('cases');
    return result.map((json) => CaseModel.fromJson(json)).toList();
  }

  Future<void> insertInspection(Inspection inspection) async {
    final db = await instance.database;
    await db.insert('inspections', inspection.toJson(), conflictAlgorithm: ConflictAlgorithm.replace);
  }

  Future<List<Inspection>> getUnsyncedInspections() async {
    final db = await instance.database;
    final result = await db.query('inspections', where: 'is_synced = ?', whereArgs: [0]);
    return result.map((json) => Inspection.fromJson(json)).toList();
  }
  
  Future<List<Inspection>> getAllInspections() async {
    final db = await instance.database;
    final result = await db.query('inspections', orderBy: 'submitted_at DESC');
    return result.map((json) => Inspection.fromJson(json)).toList();
  }

  Future<void> markInspectionAsSynced(String id) async {
    final db = await instance.database;
    await db.update('inspections', {'is_synced': 1}, where: 'id = ?', whereArgs: [id]);
  }

  Future<void> close() async {
    final db = await instance.database;
    db.close();
  }
}
