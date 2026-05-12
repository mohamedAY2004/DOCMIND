import '../entities/auth_session.dart';

/// Auth repository contract.
abstract class AuthRepository {
  Future<AuthSession> login({
    required String username,
    required String password,
  });

  Future<AuthSession?> getSavedSession();

  Future<void> clearSession();

  Future<void> logout();
}
