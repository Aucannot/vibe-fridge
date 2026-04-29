import 'package:intl/intl.dart';

String formatDate(DateTime? date) {
  if (date == null) {
    return '未设置';
  }
  return DateFormat('yyyy-MM-dd').format(date);
}
