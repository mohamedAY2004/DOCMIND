import '../entities/auth_session.dart';
import '../repositories/auth_repository.dart';

/// Login use case.
class LoginUseCase {
  const LoginUseCase(this._repository);

  final AuthRepository _repository;

  Future<AuthSession> call({
    required String username,
    required String password,
  }) {
    return _repository.login(username: username, password: password);
  }
}
