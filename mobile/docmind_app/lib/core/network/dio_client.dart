import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import '../domain/failure.dart';
import 'api_constants.dart';
import 'sanitized_diagnostics.dart';

/// The composition root provides token storage; network code owns attachment.
abstract final class DioClient {
  static Dio create({required Future<String?> Function() tokenProvider}) {
    final dio = Dio(
      BaseOptions(
        baseUrl: ApiConstants.baseUrl,
        connectTimeout: const Duration(seconds: 30),
        receiveTimeout: const Duration(minutes: 3),
        headers: {'Content-Type': 'application/json'},
      ),
    );
    dio.interceptors.add(
      InterceptorsWrapper(
        onRequest: (options, handler) async {
          if (options.path == ApiConstants.login) {
            handler.next(options);
            return;
          }
          try {
            final token = await tokenProvider();
            if (token == null || token.isEmpty) {
              handler.reject(
                DioException(
                  requestOptions: options,
                  error: const AuthenticationFailure(),
                ),
              );
              return;
            }
            options.headers['Authorization'] = 'Bearer $token';
            handler.next(options);
          } catch (_) {
            handler.reject(
              DioException(
                requestOptions: options,
                error: const UnexpectedFailure(),
              ),
            );
          }
        },
      ),
    );
    if (kDebugMode) dio.interceptors.add(SanitizedDiagnostics());
    return dio;
  }
}
