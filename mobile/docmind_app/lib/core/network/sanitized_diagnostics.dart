import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';

/// Development diagnostics deliberately exclude headers, bodies, queries and IDs.
class SanitizedDiagnostics extends Interceptor {
  SanitizedDiagnostics({void Function(String)? sink, this.enabled = true})
    : _sink = sink ?? ((line) => debugPrint(line));

  final void Function(String) _sink;
  final bool enabled;
  static const _timerKey = 'docmind.diagnosticTimer';
  static const _routeSegments = {
    'api',
    'auth',
    'login',
    'logout',
    'me',
    'chat',
    'doc',
    'tutor',
    'conversations',
    'messages',
    'files',
    'feedback',
    'subjects',
    'student',
    'instructor',
    'semesters',
    'current',
    'status',
  };

  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    if (kDebugMode && enabled) options.extra[_timerKey] = Stopwatch()..start();
    handler.next(options);
  }

  void _record(RequestOptions options, int? status) {
    if (!kDebugMode || !enabled) return;
    final timer = options.extra.remove(_timerKey) as Stopwatch?;
    timer?.stop();
    final uri = Uri.tryParse(options.path);
    final path =
        '/${(uri?.pathSegments ?? const <String>[]).map((part) => _routeSegments.contains(part) ? part : ':id').join('/')}';
    final method = RegExp(r'^[A-Z]+$').hasMatch(options.method)
        ? options.method
        : 'HTTP';
    _sink(
      '$method $path ${status ?? '-'} ${timer?.elapsedMilliseconds ?? 0}ms',
    );
  }

  @override
  void onResponse(Response response, ResponseInterceptorHandler handler) {
    _record(response.requestOptions, response.statusCode);
    handler.next(response);
  }

  @override
  void onError(DioException err, ErrorInterceptorHandler handler) {
    _record(err.requestOptions, err.response?.statusCode);
    handler.next(err);
  }
}
