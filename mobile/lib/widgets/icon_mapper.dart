import 'package:flutter/material.dart';

IconData iconForName(String? name) {
  switch (name) {
    case 'restaurant':
    case 'food-apple':
      return Icons.restaurant_outlined;
    case 'home':
      return Icons.home_outlined;
    case 'palette':
      return Icons.palette_outlined;
    case 'medical_services':
    case 'medical-bag':
    case 'medication':
      return Icons.medication_outlined;
    case 'local_drink':
      return Icons.local_drink_outlined;
    case 'egg_alt':
      return Icons.egg_alt_outlined;
    case 'bakery_dining':
      return Icons.bakery_dining_outlined;
    case 'clean_hands':
      return Icons.clean_hands_outlined;
    case 'category':
      return Icons.category_outlined;
    default:
      return Icons.inventory_2_outlined;
  }
}
