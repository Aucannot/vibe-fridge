import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  test('screen and widget copy avoids internal engineering terms', () {
    final scannedFiles = [
      ..._dartFilesIn('lib/screens'),
      ..._dartFilesIn('lib/widgets'),
    ];
    final violations = <String>[];

    for (final file in scannedFiles) {
      final source = file.readAsStringSync();
      final literals = _stringLiterals(source);
      for (final literal in literals) {
        final visibleText = _withoutInterpolations(literal);
        for (final bannedTerm in _bannedUserFacingTerms) {
          if (visibleText.contains(bannedTerm)) {
            violations.add('${file.path}: "$bannedTerm" in "$literal"');
          }
        }
      }
    }

    expect(
      violations,
      isEmpty,
      reason: 'User-facing UI copy should not expose internal terminology.',
    );
  });
}

const _bannedUserFacingTerms = [
  '应用自检',
  '运行自检',
  '核心闭环',
  '数据库',
  'SQLite',
  '迁移状态',
  'legacy',
  'Wiki',
  'ISO-8601',
  'payload',
];

List<File> _dartFilesIn(String path) {
  return Directory(path)
      .listSync(recursive: true)
      .whereType<File>()
      .where((file) => file.path.endsWith('.dart'))
      .toList()
    ..sort((a, b) => a.path.compareTo(b.path));
}

List<String> _stringLiterals(String source) {
  final literals = <String>[];
  var index = 0;
  while (index < source.length) {
    final char = source[index];
    final next = index + 1 < source.length ? source[index + 1] : '';

    if (char == '/' && next == '/') {
      index = source.indexOf('\n', index + 2);
      if (index == -1) {
        break;
      }
      continue;
    }
    if (char == '/' && next == '*') {
      final end = source.indexOf('*/', index + 2);
      index = end == -1 ? source.length : end + 2;
      continue;
    }

    var raw = false;
    var quoteIndex = index;
    if ((char == 'r' || char == 'R') && _isQuote(next)) {
      raw = true;
      quoteIndex = index + 1;
    }

    if (!_isQuote(source[quoteIndex])) {
      index += 1;
      continue;
    }

    final parsed = _readStringLiteral(source, quoteIndex, raw: raw);
    if (parsed == null) {
      index += 1;
      continue;
    }
    literals.add(parsed.value);
    index = parsed.end;
  }
  return literals;
}

_ParsedString? _readStringLiteral(
  String source,
  int quoteIndex, {
  required bool raw,
}) {
  final quote = source[quoteIndex];
  final triple = quoteIndex + 2 < source.length &&
      source[quoteIndex + 1] == quote &&
      source[quoteIndex + 2] == quote;
  final buffer = StringBuffer();
  var index = quoteIndex + (triple ? 3 : 1);

  while (index < source.length) {
    if (triple) {
      if (index + 2 < source.length &&
          source[index] == quote &&
          source[index + 1] == quote &&
          source[index + 2] == quote) {
        return _ParsedString(buffer.toString(), index + 3);
      }
    } else if (source[index] == quote) {
      return _ParsedString(buffer.toString(), index + 1);
    }

    if (!raw && source[index] == r'\') {
      if (index + 1 < source.length) {
        buffer.write(source[index + 1]);
        index += 2;
        continue;
      }
    }

    buffer.write(source[index]);
    index += 1;
  }

  return null;
}

bool _isQuote(String char) => char == "'" || char == '"';

String _withoutInterpolations(String value) {
  return value
      .replaceAll(RegExp(r'\$\{[^{}]*\}'), '')
      .replaceAll(RegExp(r'\$[A-Za-z_][A-Za-z0-9_]*'), '');
}

class _ParsedString {
  const _ParsedString(this.value, this.end);

  final String value;
  final int end;
}
