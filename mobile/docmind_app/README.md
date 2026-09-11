# DocMind mobile

Flutter client for DocMind's document chat and subject tutors.

## Current status

- Implemented surfaces include sign-in, the home shell, document selection/upload and file-status polling, and document and tutor conversations.
- Profile data comes from the saved authenticated session; subject tutors use the backend subjects API.
- Privacy and Help & Support navigation are not implemented (`TODO(nav)` in the profile controller).

The mobile app remains a work in progress. Passing local tests does not establish production readiness.

## Development

Use the Flutter version in [`.flutter-version`](.flutter-version). Run from this directory:

```sh
flutter pub get
flutter analyze
flutter test
flutter run
```

The Android emulator defaults to `http://10.0.2.2:8000/api`. For a physical device, use an API address it can reach:

```sh
flutter run --dart-define=API_BASE_URL=http://YOUR_HOST:8000/api
```

Dependencies are assembled in [`AppBinding`](lib/core/bindings/app_binding.dart). Controllers receive domain use cases; repositories return `Either<Failure, T>`. HTTP configuration and endpoints live in [`lib/core/network/`](lib/core/network/).

## Documentation

- [Repository guidance](../../AGENTS.md): current architecture and contribution rules.
- [Project analysis](PROJECT_ANALYSIS.md): background on features and data flow.
- [Feature development guide](FEATURE_DEVELOPMENT_GUIDE.md): implementation examples.
- [Maintenance guide](MAINTENANCE_GUIDE.md): debugging and release reference.

The three longer guides predate the current dependency-injection and error-handling refactor. Use repository guidance and the current implementation when their examples differ.
