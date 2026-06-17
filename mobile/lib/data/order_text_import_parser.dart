import '../models/order_recognition.dart';

OrderRecognitionResult parseOrderTextImport(String text) {
  final rawText = text.trim();
  if (rawText.isEmpty) {
    throw const FormatException('请先粘贴订单文本');
  }

  final lines = rawText
      .split(RegExp(r'\r?\n'))
      .map((line) => line.trim())
      .where((line) => line.isNotEmpty)
      .toList();
  final purchaseDate = _firstDate(lines);
  final items = <OrderRecognitionItem>[];

  for (final line in lines) {
    final item = _parseItemLine(line);
    if (item != null) {
      items.add(
        OrderRecognitionItem(
          name: item.name,
          quantity: item.quantity,
          unit: item.unit,
          categoryName: item.categoryName,
          purchaseDate: purchaseDate,
          notes: item.notes,
          confidence: item.confidence,
        ),
      );
    }
  }

  if (items.isEmpty) {
    throw const FormatException('没有解析到可入库的物品');
  }

  return OrderRecognitionResult(
    sourceApp: '手动粘贴',
    merchant: _merchant(lines),
    orderId: _orderId(lines),
    purchaseDate: purchaseDate,
    rawText: rawText,
    items: items,
  );
}

_ParsedTextItem? _parseItemLine(String line) {
  if (_shouldSkipLine(line)) {
    return null;
  }

  var cleaned = line
      .replaceFirst(RegExp(r'^\s*[\d一二三四五六七八九十]+[.)、]\s*'), '')
      .replaceAll(_pricePattern, ' ')
      .replaceAll(_datePattern, ' ')
      .replaceAll(_chineseDatePattern, ' ')
      .trim();
  if (cleaned.isEmpty) {
    return null;
  }

  final quantity = _quantity(cleaned);
  if (quantity.matchText != null) {
    cleaned = cleaned.replaceFirst(quantity.matchText!, ' ');
  }
  cleaned = cleaned
      .replaceAll(RegExp(r'\s{2,}'), ' ')
      .replaceAll(RegExp(r'^[,，;；:：/\-\s]+'), '')
      .replaceAll(RegExp(r'[,，;；:：/\-\s]+$'), '')
      .trim();
  if (cleaned.length < 2 || _looksLikeMetadata(cleaned)) {
    return null;
  }

  final isGift = RegExp(r'赠品|赠送').hasMatch(line);
  final confidence = isGift
      ? 0.55
      : quantity.matchText == null
          ? 0.62
          : 0.72;

  return _ParsedTextItem(
    name: cleaned,
    quantity: quantity.value,
    unit: quantity.unit,
    categoryName: _categoryForName(cleaned),
    notes: isGift ? '手动文本包含赠品，请确认是否入库' : null,
    confidence: confidence,
  );
}

bool _shouldSkipLine(String line) {
  final lower = line.toLowerCase();
  if (_looksLikeStandaloneReference(line)) {
    return true;
  }
  final nonInventoryPattern = RegExp(
    r'退款|退货|已退|取消|运费|配送费|包装费|'
    r'服务费|优惠|红包|实付|合计|总计',
  );
  if (nonInventoryPattern.hasMatch(line)) {
    return true;
  }
  final metadataPattern = RegExp(
    r'订单号|订单编号|下单时间|支付时间|购买日期|'
    r'收货地址|联系电话|商家[:：]|门店[:：]',
  );
  if (metadataPattern.hasMatch(line)) {
    return true;
  }
  return lower.startsWith('order id') ||
      lower.startsWith('order:') ||
      lower.startsWith('merchant:');
}

bool _looksLikeStandaloneReference(String line) {
  final text = line.trim();
  if (text.length < 5 ||
      text.contains(RegExp(r'\s')) ||
      text.contains(RegExp(r'[\u4e00-\u9fa5]'))) {
    return false;
  }
  return RegExp(r'^[A-Z]{2,}[A-Z0-9_-]*[-_#]\d[A-Z0-9_-]*$').hasMatch(text);
}

bool _looksLikeMetadata(String text) {
  if (_datePattern.hasMatch(text) || _chineseDatePattern.hasMatch(text)) {
    return true;
  }
  return RegExp(r'^[\d\s:：#\-_/]+$').hasMatch(text);
}

_QuantityGuess _quantity(String line) {
  final quantityLabel = RegExp(r'数量\s*[:：]?\s*(\d+)').firstMatch(line);
  if (quantityLabel != null) {
    return _QuantityGuess(
      value: _positiveInt(quantityLabel.group(1), fallback: 1),
      matchText: quantityLabel.group(0),
    );
  }

  final unitMatch = RegExp(
    r'(\d+)\s*(盒|瓶|袋|包|个|只|枚|根|斤|克|g|kg|ml|l|L|升|罐|杯|套|条|支|片|份|箱)',
  ).firstMatch(line);
  if (unitMatch != null) {
    return _QuantityGuess(
      value: _positiveInt(unitMatch.group(1), fallback: 1),
      unit: unitMatch.group(2),
      matchText: unitMatch.group(0),
    );
  }

  final xMatch = RegExp(r'(?:x|X|×|\*)\s*(\d+)').firstMatch(line);
  if (xMatch != null) {
    return _QuantityGuess(
      value: _positiveInt(xMatch.group(1), fallback: 1),
      matchText: xMatch.group(0),
    );
  }

  return const _QuantityGuess(value: 1);
}

String? _categoryForName(String name) {
  if (RegExp(r'纸|巾|洗|皂|牙膏|垃圾袋').hasMatch(name)) {
    return '日用品';
  }
  if (RegExp(r'药|片|胶囊|口罩|酒精|碘伏').hasMatch(name)) {
    return '药品';
  }
  if (RegExp(r'乳|霜|精华|面膜|洗面奶|口红').hasMatch(name)) {
    return '化妆品';
  }
  return '食品';
}

String? _merchant(List<String> lines) {
  for (final line in lines) {
    final match =
        RegExp(r'(?:商家|门店|merchant)\s*[:：]\s*(.+)', caseSensitive: false)
            .firstMatch(line);
    if (match != null) {
      return match.group(1)?.trim();
    }
  }
  return null;
}

String? _orderId(List<String> lines) {
  for (final line in lines) {
    final match = RegExp(
      r'(?:订单号|订单编号|order\s*id|order)\s*[:：#]?\s*([A-Za-z0-9_-]+)',
      caseSensitive: false,
    ).firstMatch(line);
    if (match != null) {
      return match.group(1)?.trim();
    }
  }
  return null;
}

DateTime? _firstDate(List<String> lines) {
  for (final line in lines) {
    final date = _parseDate(line);
    if (date != null) {
      return date;
    }
  }
  return null;
}

DateTime? _parseDate(String text) {
  final standard = _datePattern.firstMatch(text);
  if (standard != null) {
    final normalized = standard.group(0)!.replaceAll(RegExp(r'[/.]'), '-');
    return _safeDate(normalized.split('-'));
  }
  final chinese = _chineseDatePattern.firstMatch(text);
  if (chinese != null) {
    return _safeDate([
      chinese.group(1)!,
      chinese.group(2)!,
      chinese.group(3)!,
    ]);
  }
  return null;
}

DateTime? _safeDate(List<String> parts) {
  if (parts.length != 3) {
    return null;
  }
  final year = int.tryParse(parts[0]);
  final month = int.tryParse(parts[1]);
  final day = int.tryParse(parts[2]);
  if (year == null || month == null || day == null) {
    return null;
  }
  return DateTime(year, month, day);
}

int _positiveInt(String? value, {required int fallback}) {
  final parsed = int.tryParse(value ?? '');
  if (parsed == null || parsed < 1) {
    return fallback;
  }
  return parsed;
}

final _datePattern = RegExp(r'20\d{2}[-/.]\d{1,2}[-/.]\d{1,2}');
final _chineseDatePattern = RegExp(r'(20\d{2})年(\d{1,2})月(\d{1,2})日');
final _pricePattern = RegExp(r'(?:¥|￥)\s*\d+(?:\.\d+)?|\d+(?:\.\d+)?\s*元');

class _ParsedTextItem {
  const _ParsedTextItem({
    required this.name,
    required this.quantity,
    required this.confidence,
    this.unit,
    this.categoryName,
    this.notes,
  });

  final String name;
  final int quantity;
  final String? unit;
  final String? categoryName;
  final String? notes;
  final double confidence;
}

class _QuantityGuess {
  const _QuantityGuess({
    required this.value,
    this.unit,
    this.matchText,
  });

  final int value;
  final String? unit;
  final String? matchText;
}
