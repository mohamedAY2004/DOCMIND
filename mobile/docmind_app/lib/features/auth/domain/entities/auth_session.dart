import 'auth_user.dart';

/// Successful authentication result.
class AuthSession {
  const AuthSession({
    required this.token,
    required this.user,
    this.redirect,
    this.welcomeMessage,
  });

  final String token;
  final AuthUser user;
  final String? redirect;
  final String? welcomeMessage;
}
