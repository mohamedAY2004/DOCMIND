import 'package:fpdart/fpdart.dart';
import '../../../../core/domain/failure.dart';
import '../entities/auth_session.dart';
import '../repositories/auth_repository.dart';

class GetSavedSessionUseCase {
  const GetSavedSessionUseCase(this._repository);

  final AuthRepository _repository;

  Future<Either<Failure, AuthSession?>> call() => _repository.getSavedSession();
}
