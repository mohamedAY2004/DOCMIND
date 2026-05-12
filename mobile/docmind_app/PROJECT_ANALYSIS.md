# 📚 DocMind App - Complete Project Analysis

## Executive Summary

**DocMind** is a Flutter-based educational AI assistant platform designed to help students learn through:
- 🔐 **Authentication** - User login with persistent sessions
- 📚 **Document Chat** - Upload documents and chat with them (RAG)
- 💬 **Live Chat** - Real-time messaging
- 👨‍🏫 **Subject Tutors** - Subject-specific tutoring
- 👤 **Profile Management** - User settings

The project follows **Clean Architecture** with proper separation of concerns across Domain, Data, and Presentation layers using **GetX** for state management and routing.

---

## 🏗️ Architecture Overview

### Three-Layer Structure

```
┌─────────────────────────────────────────┐
│  PRESENTATION LAYER (UI & State)        │
│  ├─ Pages (Stateless widgets)           │
│  ├─ Controllers (GetX state mgmt)       │
│  └─ Widgets (Reusable components)       │
├─────────────────────────────────────────┤
│  DOMAIN LAYER (Business Logic)          │
│  ├─ Entities (core objects)             │
│  ├─ Use Cases (business rules)          │
│  ├─ Repository Interfaces (contracts)   │
│  └─ Custom Failures (error types)       │
├─────────────────────────────────────────┤
│  DATA LAYER (API & Storage)             │
│  ├─ Models (JSON ↔ Entity mapping)      │
│  ├─ Repository Implementations          │
│  ├─ Remote DataSource (Dio API calls)   │
│  └─ Local DataSource (SharedPrefs)      │
├─────────────────────────────────────────┤
│  CORE LAYER (App Infrastructure)        │
│  ├─ Routes (GetX routing)               │
│  ├─ Theme (Light/Dark modes)            │
│  ├─ Constants (colors, assets)          │
│  └─ Network (DioClient, API config)     │
└─────────────────────────────────────────┘
```

### Key Dependencies
- **GetX** 4.6.6 → State management, routing, DI
- **Dio** 5.9.2 → HTTP client with interceptors
- **SharedPreferences** 2.3.2 → Local persistence
- **Flutter SVG** 2.0 → Icon/image rendering
- **Flutter Native Splash** 2.4.7 → Splash screen

---

## 📱 Data Flow Example: User Login

```
1. User enters email & password in SignInPage
                        ↓
2. Taps "Sign In" button → SignInController.login()
                        ↓
3. Controller validates form & calls LoginUseCase
                        ↓
4. UseCase calls AuthRepositoryImpl.login()
                        ↓
5. Repository sends POST /auth/login via AuthRemoteDataSource
                        ↓
6. Backend returns {token, user, redirect, message}
                        ↓
7. Repository saves session to SharedPreferences via AuthLocalDataSource
                        ↓
8. Controller catches success → Sets errorMessage = null
                        ↓
9. Controller navigates to /home (Get.toNamed)
                        ↓
10. HomePage displays with user data from session
```

### Session Persistence Flow
```
App Start
    ↓
main() → Check AuthLocalDataSource.hasSession()
    ├─ If true  → Load session from SharedPreferences → Route to /home
    └─ If false → Route to /sign-in
    
On Login Success
    ├─ Save session JSON to SharedPreferences
    └─ Route to /home
    
On Logout
    ├─ Clear session from SharedPreferences
    └─ Route to /sign-in
```

---

## 🗂️ Project Directory Structure

```
lib/
├── main.dart                          # App entry point
│
├── core/                              # App-wide infrastructure
│   ├── constants/
│   │   ├── app_colors.dart           # Color palette
│   │   ├── app_assets.dart           # Asset paths
│   │   └── app_texts.dart            # String constants
│   │
│   ├── network/
│   │   ├── dio_client.dart           # Singleton Dio instance
│   │   └── api_constants.dart        # Base URL, endpoints
│   │
│   ├── routes/
│   │   └── app_routes.dart           # GetX routes & pages
│   │
│   └── theme/
│       ├── app_theme.dart            # Light/Dark themes
│       └── theme_service.dart        # Theme persistence
│
├── features/                          # Feature modules (isolated)
│   ├── auth/                          # Authentication module
│   │   ├── data/
│   │   │   ├── datasources/
│   │   │   │   ├── auth_remote_data_source.dart
│   │   │   │   └── auth_local_data_source.dart
│   │   │   ├── models/
│   │   │   │   ├── auth_session_model.dart
│   │   │   │   ├── login_request.dart
│   │   │   │   ├── login_response.dart
│   │   │   │   └── auth_user_model.dart
│   │   │   └── repositories/
│   │   │       └── auth_repository_impl.dart
│   │   │
│   │   ├── domain/
│   │   │   ├── entities/
│   │   │   │   ├── auth_session.dart
│   │   │   │   └── auth_user.dart
│   │   │   ├── errors/
│   │   │   │   └── auth_failure.dart
│   │   │   ├── repositories/
│   │   │   │   └── auth_repository.dart (interface)
│   │   │   └── usecases/
│   │   │       └── login_usecase.dart
│   │   │
│   │   └── presentation/
│   │       ├── controllers/
│   │       │   └── sign_in_controller.dart
│   │       ├── pages/
│   │       │   └── sign_in_page.dart
│   │       └── widgets/
│   │           ├── auth_button.dart
│   │           ├── auth_text_field.dart
│   │           └── auth_card.dart
│   │
│   ├── chat_with_documents/          # Document chat module
│   │   ├── data/ ... (similar structure)
│   │   ├── domain/ ...
│   │   └── presentation/ ...
│   │
│   ├── home/                         # Home/Dashboard
│   ├── live_chat/                    # Live messaging
│   ├── profile/                      # User profile
│   └── subject_tutors/               # Tutoring system
│
└── test/
    └── widget_test.dart
```

---

## 🔑 Key Components Explained

### 1. **GetX Routing System** (`app_routes.dart`)
```dart
abstract final class AppRoutes {
  static const String signIn = '/sign-in';
  static const String home = '/home';
  static const String myFeature = '/my-feature';
}

abstract final class AppPages {
  static final List<GetPage> pages = [
    GetPage(name: AppRoutes.signIn, page: () => SignInPage()),
    GetPage(name: AppRoutes.home, page: () => HomePage()),
    // ...
  ];
}

// Navigation (from anywhere):
Get.toNamed(AppRoutes.home);
Get.back();
```

### 2. **State Management Pattern** (GetX Controllers)
```dart
class MyController extends GetxController {
  // Observable state
  final items = <Item>[].obs;
  final isLoading = false.obs;
  final error = RxnString();  // Nullable string
  
  // Build methods react automatically to changes
  Future<void> loadItems() async {
    isLoading.value = true;
    try {
      items.value = await useCase();
    } catch (e) {
      error.value = e.toString();
    } finally {
      isLoading.value = false;
    }
  }
}

// UI automatically rebuilds:
// - GetBuilder (reactive updates)
// - Obx (observable updates)
```

### 3. **Repository Pattern** (Clean Architecture)
```dart
// Domain: Interface/Contract
abstract class AuthRepository {
  Future<AuthSession> login({required String username, password});
}

// Data: Implementation
class AuthRepositoryImpl implements AuthRepository {
  @override
  Future<AuthSession> login({...}) async {
    // Call remote datasource
    // Save to local datasource
    // Return entity
  }
}

// Presentation: Use via UseCase
class SignInController {
  void login() async {
    session = await LoginUseCase(AuthRepositoryImpl()).call(...);
  }
}
```

### 4. **API Communication** (Dio Client)
```dart
// Centralized Dio instance with:
// ✅ Base URL configuration
// ✅ Timeout settings (30s connect, 45s receive)
// ✅ Automatic logging (PrettyDioLogger)
// ✅ Content-Type headers

class DioClient {
  static final Dio _dio = Dio(BaseOptions(...))
    ..interceptors.add(PrettyDioLogger());
  
  static Dio get instance => _dio;
}

// Usage in datasources:
final response = await DioClient.instance.post(
  '/auth/login',
  data: request.toJson(),
);
```

### 5. **Local Storage** (SharedPreferences)
```dart
class AuthLocalDataSource {
  static const String _sessionKey = 'auth_session';
  
  Future<void> saveSession(AuthSessionModel session) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_sessionKey, jsonEncode(session.toJson()));
  }
  
  Future<AuthSessionModel?> getSession() async {
    final prefs = await SharedPreferences.getInstance();
    final jsonString = prefs.getString(_sessionKey);
    return jsonString != null 
      ? AuthSessionModel.fromJson(jsonDecode(jsonString))
      : null;
  }
}
```

---

## 🚀 How to Add a New Feature

### Quick 5-Step Process

**Step 1: Create Folder Structure**
```bash
lib/features/new_feature/{data,domain,presentation}/
```

**Step 2: Build Domain Layer** (Business Logic)
- Define `Entity` (core data object)
- Create `Repository` interface
- Implement `UseCase` classes

**Step 3: Build Data Layer** (API & Storage)
- Create `Model` (JSON mapping)
- Implement `Repository` (uses models)
- Implement `DataSources` (Dio, SharedPrefs)

**Step 4: Build Presentation Layer** (UI)
- Create `Controller` (GetxController)
- Create `Page` (Stateless widget + GetBuilder)
- Create `Widgets` (reusable components)

**Step 5: Register Route**
- Add route name to `AppRoutes`
- Add page to `AppPages.pages`
- Add to home screen `HomeController`

**See `FEATURE_DEVELOPMENT_GUIDE.md` for complete code examples!**

---

## 🎨 Theme System

```dart
// ThemeService handles theme persistence
class ThemeService {
  static Future<ThemeService> init() async {
    final isDarkMode = await _loadPreference();
    return ThemeService(isDarkMode: isDarkMode);
  }
  
  final isDarkMode = true.obs;
  
  void toggleTheme() {
    isDarkMode.value = !isDarkMode.value;
    _savePreference(isDarkMode.value);
  }
}

// App applies theme:
GetMaterialApp(
  themeMode: themeService.isDarkMode.value ? ThemeMode.dark : ThemeMode.light,
  theme: AppTheme.light,
  darkTheme: AppTheme.dark,
)
```

---

## ⚙️ Configuration Files

### `pubspec.yaml` - Dependencies
```yaml
dependencies:
  flutter: sdk: flutter
  get: ^4.6.6               # State management & routing
  dio: ^5.9.2               # HTTP client
  shared_preferences: ^2.3.2 # Local storage
  flutter_svg: ^2.0.10+1    # SVG support
  file_picker: ^8.1.7       # File selection

dev_dependencies:
  flutter_launcher_icons: ^0.14.3  # App icon generation
  flutter_native_splash: ^2.4.7     # Splash screen
```

### `analysis_options.yaml` - Linting Rules
```yaml
include: package:flutter_lints/flutter.yaml
linter:
  rules:
    - avoid_empty_else
    - avoid_print
    - prefer_const_constructors
```

### `.env` (if using):
```
API_BASE_URL=https://api.docmind.com
API_TIMEOUT=30000
```

---

## 📋 Maintenance & Deployment

### Code Quality Checklist
- [ ] Run `flutter analyze` (no warnings/errors)
- [ ] Run `flutter format .` (consistent formatting)
- [ ] Check for unused imports
- [ ] Verify error handling in all paths
- [ ] Test on both light & dark themes
- [ ] Test with slow network conditions

### Before Release
- [ ] Update `version` in `pubspec.yaml`
- [ ] Test all features on real device
- [ ] Verify API endpoints (production URLs)
- [ ] Check session persistence works
- [ ] Test token refresh (if applicable)
- [ ] Clear debug prints and logs
- [ ] Verify splash screen displays correctly

### Debugging Tips
```bash
# Analyze code for issues
flutter analyze

# Format code
flutter format .

# Run with verbose logging
flutter run -v

# Check for memory leaks
flutter run --profile

# View network logs in console
# (Auto-logged via PrettyDioLogger)
```

---

## 🛠️ Common Development Tasks

### Task 1: Add New API Endpoint
1. Add endpoint path to `ApiConstants`
2. Create `DataSource` method with Dio call
3. Handle `DioException` → Custom `Failure`
4. Map response model → entity
5. Call from `Repository.method()`

### Task 2: Add New Screen
1. Create `Entity` & `Repository` interface
2. Create `UseCase`
3. Create `Controller` with `.obs` state
4. Create `Page` with `GetBuilder`
5. Register route in `app_routes.dart`

### Task 3: Fix API Error
1. Check error logs in console (PrettyDioLogger)
2. Verify API response structure
3. Update model if needed
4. Verify endpoint URL
5. Check DioException mapping

### Task 4: Persist New Data
1. Create `Model` with `fromJson`/`toJson`
2. Add to `AuthLocalDataSource` or new datasource
3. JSON encode before saving to SharedPrefs
4. JSON decode after loading
5. Test persistence across app restarts

---

## 📊 Architecture Quality Metrics

| Metric | Score | Status |
|--------|-------|--------|
| Clean Architecture compliance | 8/10 | ✅ Good |
| Code reusability | 7/10 | ✅ Good |
| Testability | 7/10 | ✅ Good |
| Scalability | 7/10 | ✅ Good |
| Documentation | 9/10 | ✅ Excellent |

**Strengths:**
- ✅ Clear separation of concerns (Domain/Data/Presentation)
- ✅ Centralized routing and configuration
- ✅ Proper error handling with custom failures
- ✅ Session persistence pattern established
- ✅ Theme management built-in

**Areas for Improvement:**
- 🔄 Add unit/widget tests
- 🔄 Implement GetX Bindings for DI
- 🔄 Add request/response interceptors
- 🔄 Implement token refresh logic
- 🔄 Add analytics tracking

---

## 📚 Resources & References

### Key Files
- **Entry Point**: `lib/main.dart`
- **Routing**: `lib/core/routes/app_routes.dart`
- **Network**: `lib/core/network/dio_client.dart`
- **Theme**: `lib/core/theme/app_theme.dart`
- **Auth Example**: `lib/features/auth/` (complete pattern)

### Documentation Links
- [Flutter Official Docs](https://flutter.dev)
- [GetX Documentation](https://github.com/jonataslaw/getx)
- [Dio Package](https://pub.dev/packages/dio)
- [Clean Architecture](https://blog.cleancoder.com)

### Development Guides
- **Feature Development**: See `FEATURE_DEVELOPMENT_GUIDE.md`
- **Architecture Notes**: See `/memories/repo/docmind_architecture.md`

---

## 🤔 FAQ

**Q: How do I add a new feature?**
A: Follow the 5-step process in the "Add a New Feature" section or refer to `FEATURE_DEVELOPMENT_GUIDE.md`.

**Q: Where do I put API calls?**
A: In `DataSource` classes (e.g., `AuthRemoteDataSource`), not in Controllers.

**Q: How do I handle errors?**
A: Create custom `Failure` classes in domain layer, catch them in repository, expose via controller's `errorMessage` observable.

**Q: How is session data stored?**
A: JSON serialized in SharedPreferences under key `'auth_session'` via `AuthLocalDataSource`.

**Q: How do I switch themes?**
A: Call `ThemeService.toggleTheme()` which updates `.obs` and rebuilds app with new theme.

**Q: What's the GetX pattern?**
A: Use `Obx()` or `GetBuilder()` to wrap UI that should react to observable changes. Controllers extend `GetxController`.

**Q: How do I navigate?**
A: Use `Get.toNamed(AppRoutes.routeName)` or `Get.back()` from anywhere (no BuildContext needed).

---

## 🎯 Next Steps

1. **Explore the codebase**: Start with `main.dart` then follow to auth feature
2. **Run the app**: `flutter run` to see it in action
3. **Add a feature**: Follow the guide to implement a new module
4. **Test thoroughly**: Use the testing checklist before deployment
5. **Maintain quality**: Run analysis and formatting regularly

---

**Generated**: May 10, 2026  
**Version**: 1.0.0  
**Maintainer**: Development Team
