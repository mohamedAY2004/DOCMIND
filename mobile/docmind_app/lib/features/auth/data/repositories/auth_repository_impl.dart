import 'package:fpdart/fpdart.dart';
import '../../../../core/domain/failure.dart';
import '../../../../core/network/repository_call.dart';
import '../../domain/entities/auth_session.dart';
import '../../domain/repositories/auth_repository.dart';
import '../datasources/auth_local_data_source.dart';
import '../datasources/auth_remote_data_source.dart';
import '../models/auth_session_model.dart';
import '../models/login_request.dart';

/// Auth repository implementation.
class AuthRepositoryImpl implements AuthRepository {
  const AuthRepositoryImpl(this._remote, this._local);

  final AuthRemoteDataSource _remote;
  final AuthLocalDataSource _local;

  @override
  Future<Either<Failure, AuthSession>> login({
    required String username,
    required String password,
  }) => repositoryCall(() async {
    if (username.trim().isEmpty || password.trim().isEmpty) {
      throw const ValidationFailure('Username and password are required.');
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
  });

  @override
  Future<Either<Failure, AuthSession?>> getSavedSession() =>
      repositoryCall(() async {
        final stored = await _local.getSession();
        return stored?.toEntity();
      });

  @override
  Future<Either<Failure, void>> logout() => repositoryCall(() async {
    final token = await _local.getToken();
    if (token != null && token.isNotEmpty) {
      await _remote.logout();
    }
    await _local.clearSession();
  });
}
