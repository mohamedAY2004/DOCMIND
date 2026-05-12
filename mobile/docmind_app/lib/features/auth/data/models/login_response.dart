import 'auth_user_model.dart';

class LoginResponse {
  const LoginResponse({
    required this.token,
    required this.user,
    this.redirect,
    this.welcomeMessage,
  });

  final String token;
  final AuthUserModel user;
  final String? redirect;
  final String? welcomeMessage;

  factory LoginResponse.fromJson(Map<String, dynamic> json) {
    return LoginResponse(
      token: json['token'] as String? ?? '',
      user: AuthUserModel.fromJson(json['user'] as Map<String, dynamic>? ?? {}),
      redirect: json['redirect'] as String?,
      welcomeMessage: json['welcomeMessage'] as String?,
    );
  }
}
