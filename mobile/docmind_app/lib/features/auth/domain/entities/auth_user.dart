/// Authenticated user entity.
///
/// Pure Dart — no framework dependencies.
class AuthUser {
  const AuthUser({
    required this.id,
    required this.username,
    required this.name,
    required this.role,
  });

  final String id;
  final String username;
  final String name;
  final String role;
}
