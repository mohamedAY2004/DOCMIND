/// Failures cross repository boundaries without exposing transport exceptions.
sealed class Failure implements Exception {
  const Failure(this.message);
  final String message;
  @override
  String toString() => message;
}

class AuthenticationFailure extends Failure {
  const AuthenticationFailure([super.message = 'Please sign in again.']);
}

class ValidationFailure extends Failure {
  const ValidationFailure(super.message);
}

class ReadinessFailure extends Failure {
  const ReadinessFailure(super.message);
}

class PermissionFailure extends Failure {
  const PermissionFailure(super.message);
}

class NetworkFailure extends Failure {
  const NetworkFailure([
    super.message = 'Check your connection and try again.',
  ]);
}

class UnexpectedFailure extends Failure {
  const UnexpectedFailure([
    super.message = 'Something went wrong. Please try again.',
  ]);
}
