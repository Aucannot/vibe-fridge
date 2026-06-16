import 'dart:io' as io;
import 'dart:typed_data';

import 'package:path/path.dart' as p;
import 'package:path_provider/path_provider.dart';

class LocalImageStore {
  static Future<String> saveImage({
    required Uint8List bytes,
    required String folderName,
    required String originalName,
    required String mimeType,
  }) async {
    final documents = await getApplicationDocumentsDirectory();
    final directory = io.Directory(
      p.join(documents.path, 'attachments', folderName),
    );
    await directory.create(recursive: true);

    final timestamp = DateTime.now().microsecondsSinceEpoch;
    final extension = _extensionForImage(
      originalName: originalName,
      mimeType: mimeType,
    );
    final file = io.File(
      p.join(directory.path, '$folderName-$timestamp$extension'),
    );
    await file.writeAsBytes(bytes, flush: true);
    return file.path;
  }

  static String _extensionForImage({
    required String originalName,
    required String mimeType,
  }) {
    final extension = p.extension(originalName).toLowerCase();
    if (extension == '.png' ||
        extension == '.jpg' ||
        extension == '.jpeg' ||
        extension == '.webp' ||
        extension == '.heic' ||
        extension == '.heif') {
      return extension;
    }
    switch (mimeType) {
      case 'image/png':
        return '.png';
      case 'image/webp':
        return '.webp';
      case 'image/heic':
        return '.heic';
      case 'image/heif':
        return '.heif';
      default:
        return '.jpg';
    }
  }
}
