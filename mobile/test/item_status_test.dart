import 'package:flutter_test/flutter_test.dart';
import 'package:vibe_fridge/models/item_status.dart';

void main() {
  test('maps legacy status values to Dart enum values', () {
    expect(ItemStatus.fromDbValue('active'), ItemStatus.active);
    expect(ItemStatus.fromDbValue('expired'), ItemStatus.expired);
    expect(ItemStatus.fromDbValue('consumed'), ItemStatus.consumed);
    expect(ItemStatus.fromDbValue('wasted'), ItemStatus.wasted);
    expect(ItemStatus.fromDbValue('unknown'), ItemStatus.active);
  });
}
