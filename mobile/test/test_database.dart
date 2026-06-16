import 'package:sqflite_common_ffi/sqflite_ffi.dart';
import 'package:vibe_fridge/data/app_database.dart';

Future<AppDatabase> openTestDatabase({
  int version = AppDatabase.schemaVersion,
}) async {
  sqfliteFfiInit();
  final database = await databaseFactoryFfi.openDatabase(inMemoryDatabasePath);
  await database.execute('PRAGMA foreign_keys = ON');
  await AppDatabase.createSchemaForTesting(database, version: version);
  return AppDatabase.forTesting(database);
}
