import 'package:path/path.dart' as p;
import 'package:path_provider/path_provider.dart';
import 'package:sqflite/sqflite.dart';

class AppDatabase {
  AppDatabase._(this.database);

  final Database database;

  static Future<AppDatabase> open() async {
    final directory = await getApplicationSupportDirectory();
    final path = p.join(directory.path, 'vibe_fridge_flutter.db');
    final database = await openDatabase(
      path,
      version: 1,
      onConfigure: (db) async {
        await db.execute('PRAGMA foreign_keys = ON');
      },
      onCreate: (db, version) async {
        await _createSchema(db);
      },
    );
    return AppDatabase._(database);
  }

  static Future<void> _createSchema(Database db) async {
    await db.execute('''
      CREATE TABLE item_wiki_categories (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL UNIQUE,
        icon TEXT,
        color TEXT,
        sort_order INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
      )
    ''');

    await db.execute('''
      CREATE TABLE item_wikis (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        icon TEXT,
        description TEXT,
        category_id TEXT REFERENCES item_wiki_categories(id) ON DELETE SET NULL,
        default_unit TEXT,
        suggested_expiry_days INTEGER,
        storage_location TEXT,
        notes TEXT,
        image_path TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
      )
    ''');

    await db.execute('''
      CREATE TABLE items (
        id TEXT PRIMARY KEY,
        wiki_id TEXT NOT NULL REFERENCES item_wikis(id) ON DELETE CASCADE,
        name TEXT NOT NULL,
        description TEXT,
        quantity INTEGER NOT NULL DEFAULT 1,
        unit TEXT,
        purchase_date TEXT,
        expiry_date TEXT,
        reminder_date TEXT,
        status TEXT NOT NULL DEFAULT 'active',
        is_reminder_enabled INTEGER NOT NULL DEFAULT 1,
        consumed_at TEXT,
        predicted_expiry_date TEXT,
        prediction_confidence REAL,
        image_path TEXT,
        source_app TEXT,
        source_order_id TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
      )
    ''');

    await db.execute('''
      CREATE TABLE tags (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL UNIQUE,
        color TEXT,
        created_at TEXT NOT NULL
      )
    ''');

    await db.execute('''
      CREATE TABLE item_tags (
        item_id TEXT NOT NULL REFERENCES items(id) ON DELETE CASCADE,
        tag_id TEXT NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
        created_at TEXT NOT NULL,
        PRIMARY KEY (item_id, tag_id)
      )
    ''');

    await db.execute('''
      CREATE TABLE reminder_logs (
        id TEXT PRIMARY KEY,
        item_id TEXT NOT NULL REFERENCES items(id) ON DELETE CASCADE,
        reminder_type TEXT NOT NULL,
        message TEXT NOT NULL,
        sent_at TEXT NOT NULL,
        is_success INTEGER NOT NULL DEFAULT 1,
        error_message TEXT
      )
    ''');

    await db.execute(
      'CREATE INDEX idx_item_wikis_name ON item_wikis(lower(name))',
    );
    await db.execute(
      'CREATE INDEX idx_item_wikis_category ON item_wikis(category_id)',
    );
    await db.execute('CREATE INDEX idx_items_wiki ON items(wiki_id)');
    await db.execute('CREATE INDEX idx_items_status ON items(status)');
    await db.execute('CREATE INDEX idx_items_expiry ON items(expiry_date)');
    await db.execute('CREATE INDEX idx_items_reminder ON items(reminder_date)');
  }

  Future<void> seedDefaults() async {
    final categoryCount = Sqflite.firstIntValue(
      await database.rawQuery('SELECT COUNT(*) FROM item_wiki_categories'),
    );
    if ((categoryCount ?? 0) == 0) {
      await _seedCategories(database);
    }

    final wikiCount = Sqflite.firstIntValue(
      await database.rawQuery('SELECT COUNT(*) FROM item_wikis'),
    );
    if ((wikiCount ?? 0) == 0) {
      await _seedWikisAndItems(database);
    }
  }

  static Future<void> _seedCategories(Database db) async {
    final now = DateTime.now().toIso8601String();
    final rows = [
      {
        'id': 'cat-food',
        'name': '食品',
        'icon': 'restaurant',
        'color': '#1B8B7A',
        'sort_order': 1,
      },
      {
        'id': 'cat-daily',
        'name': '日用品',
        'icon': 'home',
        'color': '#4E7BC7',
        'sort_order': 2,
      },
      {
        'id': 'cat-cosmetics',
        'name': '化妆品',
        'icon': 'palette',
        'color': '#E49A41',
        'sort_order': 3,
      },
      {
        'id': 'cat-medicine',
        'name': '药品',
        'icon': 'medical_services',
        'color': '#D95C5C',
        'sort_order': 4,
      },
      {
        'id': 'cat-other',
        'name': '其他',
        'icon': 'category',
        'color': '#7C8B87',
        'sort_order': 99,
      },
    ];

    for (final row in rows) {
      await db.insert(
        'item_wiki_categories',
        {
          ...row,
          'created_at': now,
          'updated_at': now,
        },
        conflictAlgorithm: ConflictAlgorithm.ignore,
      );
    }
  }

  static Future<void> _seedWikisAndItems(Database db) async {
    final now = DateTime.now();
    final nowText = now.toIso8601String();
    final wikis = [
      {
        'id': 'wiki-milk',
        'name': '鲜牛奶',
        'icon': 'local_drink',
        'description': '巴氏杀菌鲜牛奶，需要冷藏保存',
        'category_id': 'cat-food',
        'default_unit': '盒',
        'suggested_expiry_days': 7,
        'storage_location': '冷藏',
      },
      {
        'id': 'wiki-egg',
        'name': '鸡蛋',
        'icon': 'egg_alt',
        'description': '新鲜鸡蛋，建议冷藏保存以延长保质期',
        'category_id': 'cat-food',
        'default_unit': '个',
        'suggested_expiry_days': 30,
        'storage_location': '冷藏',
      },
      {
        'id': 'wiki-bread',
        'name': '面包',
        'icon': 'bakery_dining',
        'description': '切片面包，常温保存',
        'category_id': 'cat-food',
        'default_unit': '袋',
        'suggested_expiry_days': 7,
        'storage_location': '常温',
      },
      {
        'id': 'wiki-toothpaste',
        'name': '牙膏',
        'icon': 'clean_hands',
        'description': '口腔清洁用品',
        'category_id': 'cat-daily',
        'default_unit': '支',
        'suggested_expiry_days': 365,
        'storage_location': '常温',
      },
      {
        'id': 'wiki-cold-medicine',
        'name': '感冒药',
        'icon': 'medication',
        'description': '常用感冒药，注意批次有效期',
        'category_id': 'cat-medicine',
        'default_unit': '盒',
        'suggested_expiry_days': 730,
        'storage_location': '常温',
      },
    ];

    for (final wiki in wikis) {
      await db.insert(
        'item_wikis',
        {
          ...wiki,
          'notes': null,
          'image_path': null,
          'created_at': nowText,
          'updated_at': nowText,
        },
        conflictAlgorithm: ConflictAlgorithm.ignore,
      );
    }

    String dateOnly(DateTime date) {
      return DateTime(date.year, date.month, date.day).toIso8601String();
    }

    final items = [
      {
        'id': 'item-milk-1',
        'wiki_id': 'wiki-milk',
        'name': '鲜牛奶',
        'quantity': 2,
        'unit': '盒',
        'purchase_date': dateOnly(now.subtract(const Duration(days: 1))),
        'expiry_date': dateOnly(now.add(const Duration(days: 3))),
      },
      {
        'id': 'item-egg-1',
        'wiki_id': 'wiki-egg',
        'name': '鸡蛋',
        'quantity': 12,
        'unit': '个',
        'purchase_date': dateOnly(now.subtract(const Duration(days: 8))),
        'expiry_date': dateOnly(now.add(const Duration(days: 20))),
      },
      {
        'id': 'item-bread-1',
        'wiki_id': 'wiki-bread',
        'name': '面包',
        'quantity': 1,
        'unit': '袋',
        'purchase_date': dateOnly(now.subtract(const Duration(days: 4))),
        'expiry_date': dateOnly(now.add(const Duration(days: 1))),
      },
      {
        'id': 'item-cold-medicine-1',
        'wiki_id': 'wiki-cold-medicine',
        'name': '感冒药',
        'quantity': 1,
        'unit': '盒',
        'purchase_date': dateOnly(now.subtract(const Duration(days: 80))),
        'expiry_date': dateOnly(now.add(const Duration(days: 220))),
      },
    ];

    for (final item in items) {
      final expiry = DateTime.parse(item['expiry_date']! as String);
      await db.insert(
        'items',
        {
          ...item,
          'description': null,
          'reminder_date': dateOnly(expiry.subtract(const Duration(days: 3))),
          'status': 'active',
          'is_reminder_enabled': 1,
          'consumed_at': null,
          'predicted_expiry_date': null,
          'prediction_confidence': null,
          'image_path': null,
          'source_app': null,
          'source_order_id': null,
          'created_at': nowText,
          'updated_at': nowText,
        },
        conflictAlgorithm: ConflictAlgorithm.ignore,
      );
    }
  }
}
