import 'package:dio/dio.dart';
import 'package:fpdart/fpdart.dart';
import '../domain/failure.dart';

Future<Either<Failure, T>> repositoryCall<T>(
  Future<T> Function() action,
) async {
  try {
    return Right(await action());
  } catch (error) {
    return Left(mapFailure(error));
  }
}

Failure mapFailure(Object error) {
  if (error is Failure) return error;
  if (error is DioException) {
    if (error.error is Failure) return error.error! as Failure;
    final data = error.response?.data;
    final body = data is Map ? data : const {};
    final code = body['code'];
    final message = body['message'] is String
        ? body['message'] as String
        : null;
    final status = error.response?.statusCode;
    if (status == 401) {
      return AuthenticationFailure(message ?? 'Please sign in again.');
    }
    if (code == 'FILES_NOT_READY' ||
        code == 'SUBJECT_NOT_READY' ||
        (body['details'] is Map && body['details']['semesterState'] != null)) {
      return ReadinessFailure(message ?? 'The source is not ready for chat.');
    }
    if (status == 403) {
      return PermissionFailure(message ?? 'You do not have access.');
    }
    if (status == 400 ||
        status == 409 ||
        status == 413 ||
        status == 415 ||
        status == 422) {
      return ValidationFailure(
        message ?? 'Please check the request and try again.',
      );
    }
    if (error.response == null) return const NetworkFailure();
  }
  return const UnexpectedFailure();
}
