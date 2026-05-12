import 'dart:convert';

import 'package:shared_preferences/shared_preferences.dart';

import '../models/auth_session_model.dart';

class AuthLocalDataSource {
  static const String _sessionKey = 'auth_session';

  Future<void> saveSession(AuthSessionModel session) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_sessionKey, jsonEncode(session.toJson()));
  }

  Future<AuthSessionModel?> getSession() async {
    final prefs = await SharedPreferences.getInstance();
    final jsonString = prefs.getString(_sessionKey);
    if (jsonString == null || jsonString.isEmpty) return null;

    try {
      final map = jsonDecode(jsonString) as Map<String, dynamic>;
      return AuthSessionModel.fromJson(map);
    } catch (_) {
      return null;
    }
  }

  Future<String?> getToken() async {
    final session = await getSession();
    return session?.token;
  }

  Future<void> clearSession() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_sessionKey);
  }

  Future<bool> hasSession() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.containsKey(_sessionKey);
  }
}
