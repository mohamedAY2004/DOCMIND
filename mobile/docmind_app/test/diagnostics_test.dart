import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:docmind_app/core/network/sanitized_diagnostics.dart';
import 'package:docmind_app/core/network/repository_call.dart';
import 'package:docmind_app/core/domain/failure.dart';

class ObservedErrorHandler extends ErrorInterceptorHandler {
  @override
  void next(DioException error) {}
}

void main() {
  test(
    'diagnostics contain only method, route template, status and timing',
    () {
      final logs = <String>[];
      final diagnostics = SanitizedDiagnostics(sink: logs.add);
      final options = RequestOptions(
        method: 'POST',
        path: '/api/chat/doc/conversations/private-id/messages?token=secret',
        headers: {'Authorization': 'Bearer secret'},
        data: {'message': 'private text'},
      );
      diagnostics.onRequest(options, RequestInterceptorHandler());
      diagnostics.onResponse(
        Response(
          requestOptions: options,
          statusCode: 200,
          data: 'private answer',
        ),
        ResponseInterceptorHandler(),
      );
      expect(
        logs.single,
        matches(r'^POST /api/chat/doc/conversations/:id/messages 200 \d+ms$'),
      );
      expect(logs.single, isNot(contains('private')));
      expect(logs.single, isNot(contains('secret')));
    },
  );
  test('disabled diagnostics emit nothing, including failures', () {
    final logs = <String>[];
    final diagnostics = SanitizedDiagnostics(sink: logs.add, enabled: false);
    final request = RequestOptions(path: '/auth/login');
    diagnostics.onError(
      DioException(requestOptions: request, message: 'secret'),
      ObservedErrorHandler(),
    );
    expect(logs, isEmpty);
  });
  test(
    'repository results distinguish authentication, readiness, validation and network failures',
    () async {
      Future<Failure> failure(int? status, [String? code]) async {
        final request = RequestOptions(path: '/');
        final result = await repositoryCall<void>(
          () async => throw DioException(
            requestOptions: request,
            response: status == null
                ? null
                : Response(
                    requestOptions: request,
                    statusCode: status,
                    data: {'code': code},
                  ),
          ),
        );
        return result.fold(
          (value) => value,
          (_) => throw StateError('Expected failure'),
        );
      }

      expect(await failure(401), isA<AuthenticationFailure>());
      expect(await failure(409, 'FILES_NOT_READY'), isA<ReadinessFailure>());
      expect(await failure(422), isA<ValidationFailure>());
      expect(await failure(null), isA<NetworkFailure>());
    },
  );
}
