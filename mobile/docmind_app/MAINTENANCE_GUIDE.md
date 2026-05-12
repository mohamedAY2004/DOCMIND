# 🔧 DocMind Maintenance & Updates Guide

## Daily Development Checklist

### Before Starting Work
- [ ] Pull latest code: `git pull origin main`
- [ ] Run `flutter pub get` to sync dependencies
- [ ] Run `flutter analyze` to catch lint issues
- [ ] Check if any new migrations or configs needed

### During Development
- [ ] Follow the architecture layers strictly
- [ ] Run `flutter format .` before committing
- [ ] Add error handling for all async operations
- [ ] Test on both Android and iOS simulators
- [ ] Test light and dark themes
- [ ] Check logs: `flutter run -v` (verbose mode)

### Before Committing
- [ ] Run `flutter analyze` (0 errors, few warnings OK)
- [ ] Format code: `flutter format .`
- [ ] Test the feature manually
- [ ] Write descriptive commit message
- [ ] Verify no hardcoded URLs or secrets

### Before Deployment
- [ ] Increment version in `pubspec.yaml`
- [ ] Run full test suite (if exists)
- [ ] Test on real device (not just simulator)
- [ ] Verify production API endpoints
- [ ] Check network connectivity handling
- [ ] Test with poor network (throttle to 3G)
- [ ] Verify app signing/certificates

---

## Debugging Common Issues

### 1. **API Calls Not Working**
```
Symptoms: Network requests fail silently or show generic error

Steps:
1. Check PrettyDioLogger output in console
   └─ Look for request/response details
2. Verify API endpoint in ApiConstants
   └─ Match with backend documentation
3. Check token is included (for authenticated endpoints)
   └─ Use AuthLocalDataSource.getToken()
4. Verify request body format matches API spec
   └─ Use response.data to see raw JSON
5. Check for DioException type
   └─ ConnectionException = network issue
   └─ TimeoutException = slow network
   └─ BadResponse = HTTP error (401, 500, etc.)

Solution Code:
catch (e) {
  if (e is DioException) {
    print('DioError type: ${e.type}');
    print('Response status: ${e.response?.statusCode}');
    print('Response data: ${e.response?.data}');
  }
}
```

### 2. **Session Not Persisting**
```
Symptoms: User has to login every time app restarts

Steps:
1. Verify SharedPreferences is saving
   └─ Check AuthLocalDataSource.saveSession() is called
2. Check JSON serialization is correct
   └─ Verify toJson() method in AuthSessionModel
3. Verify hasSession() returns true after login
   └─ Add debug print: print('Has session: ${await local.hasSession()}');
4. Check key name is consistent
   └─ Always use: static const String _sessionKey = 'auth_session';

Solution:
// In AuthRepositoryImpl.login()
await _local.saveSession(model);
final hasSession = await _local.hasSession(); // Should be true
```

### 3. **UI Not Updating After State Change**
```
Symptoms: Changed isLoading.value but UI didn't rebuild

Steps:
1. Check if using Obx() or GetBuilder()
   ❌ Wrong:  Text(controller.isLoading.toString())
   ✅ Right: Obx(() => Text(controller.isLoading.toString()))

2. Check if observable is defined with .obs
   ❌ Wrong:  var isLoading = false;
   ✅ Right: final isLoading = false.obs;

3. Check if GetBuilder/Obx wrapper is correct
   ✅ GetBuilder<MyController>(
        init: MyController(),
        builder: (controller) => ...
      )

4. Check if GetxController is extended
   ❌ Wrong:  class MyController extends GetxController {}
   ✅ Right: class MyController extends GetxController {}
```

### 4. **Navigation Not Working**
```
Symptoms: Get.toNamed() doesn't navigate

Steps:
1. Verify route is registered in AppPages
2. Check route name matches exactly (case-sensitive)
3. Verify controller is GetxController
4. Check for duplicate route definitions
5. Look for route guards blocking navigation

Debug:
Get.toNamed(
  AppRoutes.myRoute,
  arguments: {'key': 'value'}, // Optional: pass data
);
print('Navigated to: ${Get.currentRoute}'); // Check current route
```

### 5. **Memory Leaks / App Crashes**
```
Symptoms: App uses too much memory, eventually crashes

Steps:
1. Override onClose() in all GetxControllers
   Override void onClose() {
     super.onClose();
     // Dispose: timers, streams, subscriptions
   }

2. Cancel StreamSubscriptions
   _subscription?.cancel();

3. Close TextEditingControllers
   usernameController.dispose();

4. Clear large lists
   items.clear();

5. Profile with DevTools
   flutter run --profile
```

---

## Updating Dependencies

### Check for Updates
```bash
flutter pub outdated
```

### Update Specific Package
```bash
flutter pub upgrade package_name
flutter pub upgrade  # Update all
```

### After Updating
```bash
flutter clean
flutter pub get
flutter analyze
flutter test  # If tests exist
```

### Common Dependency Issues

**Issue**: GetX version incompatible with Flutter
```bash
# Solution: Update both
flutter upgrade  # Latest Flutter
flutter pub upgrade get  # Latest GetX
```

**Issue**: Dio causing SSL certificate errors
```dart
// Solution: In DioClient
_dio.httpClientAdapter = HttpClientAdapter()
  ..onHttpClientCreate = (HttpClient client) {
    client.badCertificateCallback = (X509Certificate cert, String host, int port) => true;
    return client;
  };
```

---

## Performance Optimization

### 1. **Lazy Load Images**
```dart
Image.network(
  url,
  cacheHeight: 300,
  cacheWidth: 300,
  errorBuilder: (_, __, ___) => const Icon(Icons.error),
  loadingBuilder: (context, child, progress) => progress == null
    ? child
    : const CircularProgressIndicator(),
)
```

### 2. **Pagination for Large Lists**
```dart
class ListController extends GetxController {
  final items = <Item>[].obs;
  int currentPage = 1;
  bool isLastPage = false;

  Future<void> loadMoreItems() async {
    if (isLastPage) return;
    
    final newItems = await repository.getItems(page: currentPage);
    if (newItems.isEmpty) {
      isLastPage = true;
    } else {
      items.addAll(newItems);
      currentPage++;
    }
  }
}

// In UI:
ListView.builder(
  itemCount: items.length + 1,
  itemBuilder: (context, index) {
    if (index == items.length) {
      controller.loadMoreItems();
      return const CircularProgressIndicator();
    }
    return ItemTile(item: items[index]);
  },
)
```

### 3. **Debounce Search**
```dart
class SearchController extends GetxController {
  final searchTerm = ''.obs;
  Timer? _searchTimer;

  @override
  void onInit() {
    super.onInit();
    
    // Debounce search after 500ms
    searchTerm.listen((_) {
      _searchTimer?.cancel();
      _searchTimer = Timer(
        const Duration(milliseconds: 500),
        () => _performSearch(),
      );
    });
  }

  Future<void> _performSearch() async {
    final results = await repository.search(searchTerm.value);
    // Update UI
  }

  @override
  void onClose() {
    _searchTimer?.cancel();
    super.onClose();
  }
}
```

### 4. **Minimize Rebuilds**
```dart
// ❌ Rebuilds entire widget tree
Obx(() => Column(
  children: [
    Text('Count: ${controller.count}'),
    Text('Name: ${controller.name}'),
  ],
))

// ✅ Only rebuild what changed
Obx(() => Text('Count: ${controller.count}')),
Obx(() => Text('Name: ${controller.name}')),
```

---

## Testing & QA

### Widget Testing Example
```dart
void main() {
  group('SignInPage', () {
    testWidgets('Shows email and password fields', (tester) async {
      await tester.pumpWidget(const DocMindApp());
      
      expect(find.byType(TextField), findsWidgets);
      expect(find.byType(ElevatedButton), findsOneWidget);
    });

    testWidgets('Shows error on invalid email', (tester) async {
      await tester.pumpWidget(const DocMindApp());
      
      await tester.enterText(find.byType(TextField).first, 'invalid');
      await tester.tap(find.byType(ElevatedButton));
      await tester.pumpAndSettle();
      
      expect(find.text('Invalid email'), findsOneWidget);
    });
  });
}
```

### Unit Testing Example
```dart
void main() {
  group('LoginUseCase', () {
    test('Returns AuthSession on successful login', () async {
      final mockRepo = MockAuthRepository();
      final useCase = LoginUseCase(mockRepo);
      
      final session = await useCase(
        username: 'user@example.com',
        password: 'password123',
      );
      
      expect(session.token, isNotEmpty);
      expect(session.user.id, isNotEmpty);
    });

    test('Throws AuthFailure on invalid credentials', () async {
      final mockRepo = MockAuthRepository();
      when(mockRepo.login(...)).thenThrow(const AuthFailure('Invalid credentials'));
      
      final useCase = LoginUseCase(mockRepo);
      
      expect(
        () => useCase(username: 'user', password: 'wrong'),
        throwsA(isA<AuthFailure>()),
      );
    });
  });
}
```

### Manual Testing Checklist
- [ ] Login with correct credentials
- [ ] Login with incorrect credentials
- [ ] Session persists after app restart
- [ ] Logout clears session
- [ ] All routes navigate correctly
- [ ] Back button works everywhere
- [ ] Dark theme toggles correctly
- [ ] Images load properly
- [ ] Forms validate input
- [ ] Error messages display
- [ ] Loading indicators show
- [ ] Network errors handled gracefully

---

## Git Workflow

### Branch Naming Convention
```
feature/user-authentication     # New feature
bugfix/login-session-error      # Bug fix
hotfix/critical-crash           # Production hotfix
refactor/improve-performance    # Code refactoring
```

### Commit Message Format
```
[TYPE] Brief description

Optional detailed explanation here...

Fixes #123  # Reference issue if applicable
```

**Types**: `feat`, `fix`, `docs`, `refactor`, `perf`, `test`

### Example Workflow
```bash
# Create feature branch
git checkout -b feature/add-document-upload

# Make changes and commit
git add .
git commit -m "[feat] Add document upload functionality"

# Push to remote
git push origin feature/add-document-upload

# Create Pull Request on GitHub
# Review → Merge to main
```

---

## Production Deployment

### Pre-Release Checklist
- [ ] Version bumped in `pubspec.yaml`
- [ ] Changelog updated
- [ ] All tests passing
- [ ] Code reviewed
- [ ] No debug prints remaining
- [ ] API endpoints are production URLs
- [ ] Error tracking configured
- [ ] Analytics events working
- [ ] No known bugs

### Android Release Build
```bash
# Create signed APK
flutter build apk --release

# Create signed App Bundle (for Play Store)
flutter build appbundle --release

# Location: build/app/outputs/
```

### iOS Release Build
```bash
# Create release build
flutter build ios --release

# Open in Xcode to upload to App Store
open ios/Runner.xcworkspace
```

### Version Numbering
```
version: MAJOR.MINOR.PATCH+BUILD

Examples:
1.0.0+1    # Initial release, build 1
1.1.0+2    # Minor update, build 2
1.0.1+3    # Patch, build 3
2.0.0+1    # Major release, build resets
```

---

## Monitoring & Analytics

### Add Crash Reporting (Firebase)
```dart
void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  // Initialize Firebase
  await Firebase.initializeApp();
  
  // Catch all errors
  FlutterError.onError = (errorDetails) {
    FirebaseCrashlytics.instance.recordFlutterError(errorDetails);
  };
  
  runApp(const DocMindApp());
}
```

### Log Important Events
```dart
// In controllers:
logger.d('User logged in: ${user.email}');
logger.w('API retry attempt 3');
logger.e('Failed to upload document', error: exception);

// Use logger from: logger: ^2.6.0
```

### Monitor Performance
```bash
# Profile app performance
flutter run --profile

# Use DevTools
flutter pub global activate devtools
devtools

# Check frame rates, memory usage, etc.
```

---

## Rollback Procedure

### If Deployment Goes Wrong
```bash
# 1. Identify last good version
git log --oneline | head -5

# 2. Revert to previous tag
git checkout v1.0.0

# 3. Rebuild and redeploy
flutter clean
flutter pub get
flutter build apk --release

# 4. Upload to Play Store

# 5. After verified working, create release notes
git tag -a v1.0.1 -m "Hotfix: revert problematic change"
git push origin v1.0.1
```

---

## Emergency Fixes (Hotfixes)

### Critical Bug Found in Production
```bash
# 1. Create hotfix branch from main
git checkout -b hotfix/critical-bug main

# 2. Fix the bug
# ... make changes ...

# 3. Test thoroughly
flutter test

# 4. Bump patch version
# In pubspec.yaml: 1.0.1+4 → 1.0.2+5

# 5. Merge back
git commit -am "[fix] Critical bug fix"
git push origin hotfix/critical-bug

# 6. Create PR and merge to main
# 7. Tag as release
git tag v1.0.2
git push origin v1.0.2

# 8. Rebuild and deploy
flutter build apk --release
```

---

## Useful Commands Reference

```bash
# Development
flutter run                    # Run in debug mode
flutter run -v                 # Verbose logging
flutter run --profile          # Profile mode (performance)
flutter format .               # Format all Dart files
flutter analyze                # Static analysis
flutter clean                  # Clean build artifacts

# Testing
flutter test                   # Run all tests
flutter test --coverage        # Generate coverage report
flutter test -v                # Verbose test output

# Build
flutter build apk --release    # Build Android APK
flutter build appbundle        # Build Android App Bundle
flutter build ios --release    # Build iOS

# Pub
flutter pub get                # Get dependencies
flutter pub upgrade            # Upgrade dependencies
flutter pub outdated           # Show outdated packages
flutter pub publish            # Publish to pub.dev

# Debug
flutter logs                   # Show device logs
flutter devices                # List connected devices
flutter emulators              # Manage emulators
```

---

## Resources & Support

### Official Documentation
- [Flutter Docs](https://flutter.dev/docs)
- [Dart Docs](https://dart.dev/guides)
- [GetX Documentation](https://github.com/jonataslaw/getx/wiki)
- [Dio Library](https://pub.dev/packages/dio)

### Useful Tools
- **VS Code Extensions**: Dart, Flutter, GetX
- **DevTools**: Built-in Flutter profiler
- **Android Studio**: Alternative IDE with emulator
- **Xcode**: Required for iOS development

### Getting Help
1. Check error message in console
2. Search existing GitHub issues
3. Read related documentation
4. Ask in Flutter Discord/Slack
5. Create GitHub issue if bug is new

---

**Last Updated**: May 10, 2026  
**Maintained By**: Development Team
