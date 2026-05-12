import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'package:shared_preferences/shared_preferences.dart';

class ThemeService extends GetxService {
  static const String _isDarkKey = 'is_dark_mode';
  final isDarkMode = true.obs;

  static Future<ThemeService> init() async {
    final prefs = await SharedPreferences.getInstance();
    final isDark = prefs.getBool(_isDarkKey) ?? true;
    return ThemeService()..isDarkMode.value = isDark;
  }

  Future<void> setDarkMode(bool value) async {
    // Apply framework theme mode immediately so all active routes refresh now.
    Get.changeThemeMode(value ? ThemeMode.dark : ThemeMode.light);
    isDarkMode.value = value;
    Get.forceAppUpdate();
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool(_isDarkKey, value);
  }
}
