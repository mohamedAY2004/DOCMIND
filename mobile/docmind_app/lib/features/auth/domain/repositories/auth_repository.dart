import 'package:fpdart/fpdart.dart';
import '../../../../core/domain/failure.dart';
import '../entities/auth_session.dart';

/// Auth repository contract.
abstract class AuthRepository {
  Future<Either<Failure, AuthSession>> login({
    required String username,
    required String password,
  });

  Future<Either<Failure, AuthSession?>> getSavedSession();

  Future<Either<Failure, void>> logout();
}
