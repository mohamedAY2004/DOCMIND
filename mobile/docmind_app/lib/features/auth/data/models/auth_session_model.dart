import '../../domain/entities/auth_session.dart';
import 'auth_user_model.dart';

class AuthSessionModel {
  const AuthSessionModel({
    required this.token,
    required this.user,
    this.redirect,
    this.welcomeMessage,
  });

  final String token;
  final AuthUserModel user;
  final String? redirect;
  final String? welcomeMessage;

  Map<String, dynamic> toJson() => {
        'token': token,
        'user': {
          'id': user.id,
          'username': user.username,
          'name': user.name,
          'role': user.role,
        },
        'redirect': redirect,
        'welcomeMessage': welcomeMessage,
      };

  factory AuthSessionModel.fromJson(Map<String, dynamic> json) {
    return AuthSessionModel(
      token: json['token'] as String? ?? '',
      user: AuthUserModel.fromJson(json['user'] as Map<String, dynamic>? ?? {}),
      redirect: json['redirect'] as String?,
      welcomeMessage: json['welcomeMessage'] as String?,
    );
  }

  AuthSession toEntity() => AuthSession(
        token: token,
        user: user.toEntity(),
        redirect: redirect,
        welcomeMessage: welcomeMessage,
      );
}
