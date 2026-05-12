import '../../domain/entities/auth_session.dart';
import '../../domain/errors/auth_failure.dart';
import '../../domain/repositories/auth_repository.dart';
import '../datasources/auth_local_data_source.dart';
import '../datasources/auth_remote_data_source.dart';
import '../models/auth_session_model.dart';
import '../models/login_request.dart';

/// Auth repository implementation.
class AuthRepositoryImpl implements AuthRepository {
  AuthRepositoryImpl({
    AuthRemoteDataSource? remoteDataSource,
    AuthLocalDataSource? localDataSource,
  })  : _remote = remoteDataSource ?? AuthRemoteDataSource(),
        _local = localDataSource ?? AuthLocalDataSource();

  final AuthRemoteDataSource _remote;
  final AuthLocalDataSource _local;

  @override
  Future<AuthSession> login({
    required String username,
    required String password,
  }) async {
    if (username.trim().isEmpty || password.trim().isEmpty) {
      throw const AuthFailure('Username and password are required.');
    }

    final response = await _remote.login(
      LoginRequest(username: username, password: password),
    );

    final session = AuthSession(
      token: response.token,
      user: response.user.toEntity(),
      redirect: response.redirect,
      welcomeMessage: response.welcomeMessage,
    );

    await _local.saveSession(
      AuthSessionModel(
        token: session.token,
        user: response.user,
        redirect: session.redirect,
        welcomeMessage: session.welcomeMessage,
      ),
    );

    return session;
  }

  @override
  Future<AuthSession?> getSavedSession() async {
    final stored = await _local.getSession();
    return stored?.toEntity();
  }

  @override
  Future<void> clearSession() => _local.clearSession();

  @override
  Future<void> logout() async {
    final token = await _local.getToken();
    if (token != null && token.isNotEmpty) {
      await _remote.logout(token: token);
    }
    await _local.clearSession();
  }
}
