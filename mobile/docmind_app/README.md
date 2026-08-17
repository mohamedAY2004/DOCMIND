# docmind_app

A new Flutter project.

## Current status

- Working surfaces include sign-in, the home shell, document selection/upload and processing progress, document and tutor conversation screens, and live-chat API models.
- The profile feature still serves static user data (`TODO(backend)` in `lib/features/profile/presentation/controllers/profile_controller.dart`).
- Subject tutors still use a fake datasource (`TODO(backend)` in `lib/features/subject_tutors/domain/usecases/get_subjects_usecase.dart`).
- Privacy and Help & Support navigation are not implemented (`TODO(nav)` in the profile controller).

The backend and web frontend are production-grade; the mobile app is a work in progress that currently lags the backend API.

## Getting Started

This project is a starting point for a Flutter application.

A few resources to get you started if this is your first Flutter project:

- [Lab: Write your first Flutter app](https://docs.flutter.dev/get-started/codelab)
- [Cookbook: Useful Flutter samples](https://docs.flutter.dev/cookbook)

For help getting started with Flutter development, view the
[online documentation](https://docs.flutter.dev/), which offers tutorials,
samples, guidance on mobile development, and a full API reference.
