import '../../domain/entities/auth_user.dart';

/// Data model for authenticated user.
class AuthUserModel {
  const AuthUserModel({
    required this.id,
    required this.username,
    required this.name,
    required this.role,
  });

  final String id;
  final String username;
  final String name;
  final String role;

  factory AuthUserModel.fromJson(Map<String, dynamic> json) {
    return AuthUserModel(
      id: json['id'] as String? ?? '',
      username: json['username'] as String? ?? '',
      name: json['name'] as String? ?? '',
      role: json['role'] as String? ?? '',
    );
  }

  AuthUser toEntity() => AuthUser(
        id: id,
        username: username,
        name: name,
        role: role,
      );
}
