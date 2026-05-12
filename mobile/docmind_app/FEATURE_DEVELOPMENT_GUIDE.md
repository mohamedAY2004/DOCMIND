# DocMind Feature Development Guide

## Quick Reference: Adding a New Feature

### Step-by-Step Checklist

#### 1️⃣ **Create Feature Folder Structure**
```bash
lib/features/my_feature/
├── data/
│   ├── datasources/
│   │   ├── my_feature_remote_data_source.dart
│   │   └── my_feature_local_data_source.dart  # if needed
│   ├── models/
│   │   ├── my_model.dart
│   │   └── my_response.dart
│   └── repositories/
│       └── my_feature_repository_impl.dart
├── domain/
│   ├── entities/
│   │   └── my_entity.dart
│   ├── errors/
│   │   └── my_feature_failure.dart  # if custom error needed
│   ├── repositories/
│   │   └── my_feature_repository.dart  # Interface/Abstract class
│   └── usecases/
│       └── my_usecase.dart
└── presentation/
    ├── controllers/
    │   └── my_feature_controller.dart
    ├── pages/
    │   └── my_feature_page.dart
    └── widgets/
        ├── my_feature_widget.dart
        └── my_card.dart  # Reusable components
```

---

## Implementation Layers (Bottom-Up)

### 📦 LAYER 1: Domain (Business Logic)

#### 1.1 Create Entity
**File**: `lib/features/my_feature/domain/entities/my_entity.dart`
```dart
class MyEntity {
  final String id;
  final String title;
  final DateTime createdAt;

  const MyEntity({
    required this.id,
    required this.title,
    required this.createdAt,
  });
}
```

#### 1.2 Create Custom Failure (Optional)
**File**: `lib/features/my_feature/domain/errors/my_feature_failure.dart`
```dart
class MyFeatureFailure implements Exception {
  final String message;

  const MyFeatureFailure(this.message);

  @override
  String toString() => message;
}
```

#### 1.3 Create Repository Interface
**File**: `lib/features/my_feature/domain/repositories/my_feature_repository.dart`
```dart
abstract class MyFeatureRepository {
  Future<List<MyEntity>> fetchItems();
  Future<MyEntity> createItem({required String title});
  Future<void> deleteItem({required String id});
}
```

#### 1.4 Create Use Cases
**File**: `lib/features/my_feature/domain/usecases/fetch_items_usecase.dart`
```dart
import '../entities/my_entity.dart';
import '../repositories/my_feature_repository.dart';

class FetchItemsUseCase {
  const FetchItemsUseCase(this._repository);

  final MyFeatureRepository _repository;

  Future<List<MyEntity>> call() {
    return _repository.fetchItems();
  }
}
```

---

### 💾 LAYER 2: Data (API & Storage)

#### 2.1 Create Model (JSON ↔ Entity mapping)
**File**: `lib/features/my_feature/data/models/my_model.dart`
```dart
import '../../domain/entities/my_entity.dart';

class MyModel extends MyEntity {
  const MyModel({
    required super.id,
    required super.title,
    required super.createdAt,
  });

  factory MyModel.fromJson(Map<String, dynamic> json) {
    return MyModel(
      id: json['id'] as String,
      title: json['title'] as String,
      createdAt: DateTime.parse(json['createdAt'] as String),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'title': title,
      'createdAt': createdAt.toIso8601String(),
    };
  }

  MyEntity toEntity() {
    return MyEntity(
      id: id,
      title: title,
      createdAt: createdAt,
    );
  }
}
```

#### 2.2 Create Remote Data Source
**File**: `lib/features/my_feature/data/datasources/my_feature_remote_data_source.dart`
```dart
import 'package:dio/dio.dart';
import '../../../../core/network/dio_client.dart';
import '../models/my_model.dart';

class MyFeatureRemoteDataSource {
  MyFeatureRemoteDataSource({Dio? dio})
      : _dio = dio ?? DioClient.instance;

  final Dio _dio;

  Future<List<MyModel>> fetchItems() async {
    try {
      final response = await _dio.get('/my-feature/items');
      
      if (response.data is List) {
        return (response.data as List)
            .map((item) => MyModel.fromJson(item as Map<String, dynamic>))
            .toList();
      }
      
      throw Exception('Unexpected response format');
    } on DioException catch (e) {
      throw Exception('Failed to fetch items: ${e.message}');
    }
  }

  Future<MyModel> createItem({required String title}) async {
    try {
      final response = await _dio.post(
        '/my-feature/items',
        data: {'title': title},
      );
      return MyModel.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw Exception('Failed to create item: ${e.message}');
    }
  }
}
```

#### 2.3 Create Repository Implementation
**File**: `lib/features/my_feature/data/repositories/my_feature_repository_impl.dart`
```dart
import '../../domain/entities/my_entity.dart';
import '../../domain/errors/my_feature_failure.dart';
import '../../domain/repositories/my_feature_repository.dart';
import '../datasources/my_feature_remote_data_source.dart';
import '../models/my_model.dart';

class MyFeatureRepositoryImpl implements MyFeatureRepository {
  MyFeatureRepositoryImpl({
    MyFeatureRemoteDataSource? remoteDataSource,
  }) : _remote = remoteDataSource ?? MyFeatureRemoteDataSource();

  final MyFeatureRemoteDataSource _remote;

  @override
  Future<List<MyEntity>> fetchItems() async {
    try {
      final models = await _remote.fetchItems();
      return models.map((m) => m.toEntity()).toList();
    } catch (e) {
      throw MyFeatureFailure('Unable to fetch items: $e');
    }
  }

  @override
  Future<MyEntity> createItem({required String title}) async {
    if (title.trim().isEmpty) {
      throw const MyFeatureFailure('Title cannot be empty');
    }
    
    try {
      final model = await _remote.createItem(title: title);
      return model.toEntity();
    } catch (e) {
      throw MyFeatureFailure('Unable to create item: $e');
    }
  }

  @override
  Future<void> deleteItem({required String id}) async {
    try {
      // Implement delete logic
    } catch (e) {
      throw MyFeatureFailure('Unable to delete item: $e');
    }
  }
}
```

---

### 🎨 LAYER 3: Presentation (UI & State Management)

#### 3.1 Create Controller
**File**: `lib/features/my_feature/presentation/controllers/my_feature_controller.dart`
```dart
import 'package:get/get.dart';

import '../../domain/entities/my_entity.dart';
import '../../domain/errors/my_feature_failure.dart';
import '../../domain/repositories/my_feature_repository.dart';
import '../../domain/usecases/fetch_items_usecase.dart';
import '../../data/repositories/my_feature_repository_impl.dart';

class MyFeatureController extends GetxController {
  // ── Observables ─────────────────────────────────────────────
  final items = <MyEntity>[].obs;
  final isLoading = false.obs;
  final errorMessage = RxnString();
  
  // ── Private fields ──────────────────────────────────────────
  late final FetchItemsUseCase _fetchItemsUseCase;

  @override
  void onInit() {
    super.onInit();
    _initializeDependencies();
    _loadItems();
  }

  void _initializeDependencies() {
    final repository = MyFeatureRepositoryImpl();
    _fetchItemsUseCase = FetchItemsUseCase(repository);
  }

  // ── Public methods ──────────────────────────────────────────
  Future<void> _loadItems() async {
    isLoading.value = true;
    errorMessage.value = null;

    try {
      final fetchedItems = await _fetchItemsUseCase();
      items.value = fetchedItems;
    } on MyFeatureFailure catch (e) {
      errorMessage.value = e.message;
    } catch (e) {
      errorMessage.value = 'An unexpected error occurred';
    } finally {
      isLoading.value = false;
    }
  }

  Future<void> refreshItems() => _loadItems();

  @override
  void onClose() {
    super.onClose();
    // Cleanup: close controllers, cancel timers, etc.
  }
}
```

#### 3.2 Create Page (UI)
**File**: `lib/features/my_feature/presentation/pages/my_feature_page.dart`
```dart
import 'package:flutter/material.dart';
import 'package:get/get.dart';

import '../../../../core/constants/app_colors.dart';
import '../controllers/my_feature_controller.dart';
import '../widgets/my_feature_widget.dart';

class MyFeaturePage extends StatelessWidget {
  const MyFeaturePage({super.key});

  @override
  Widget build(BuildContext context) {
    return GetBuilder<MyFeatureController>(
      init: MyFeatureController(),
      builder: (controller) {
        return Scaffold(
          appBar: AppBar(
            title: const Text('My Feature'),
            centerTitle: true,
          ),
          body: Obx(() {
            if (controller.isLoading.value) {
              return const Center(child: CircularProgressIndicator());
            }

            if (controller.errorMessage.value != null) {
              return Center(
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Text(
                      'Error: ${controller.errorMessage.value}',
                      textAlign: TextAlign.center,
                    ),
                    const SizedBox(height: 16),
                    ElevatedButton(
                      onPressed: controller.refreshItems,
                      child: const Text('Retry'),
                    ),
                  ],
                ),
              );
            }

            if (controller.items.isEmpty) {
              return const Center(child: Text('No items found'));
            }

            return RefreshIndicator(
              onRefresh: () => controller.refreshItems(),
              child: ListView.builder(
                itemCount: controller.items.length,
                itemBuilder: (context, index) {
                  final item = controller.items[index];
                  return MyCard(item: item);
                },
              ),
            );
          }),
        );
      },
    );
  }
}
```

#### 3.3 Create Widgets
**File**: `lib/features/my_feature/presentation/widgets/my_card.dart`
```dart
import 'package:flutter/material.dart';

import '../../domain/entities/my_entity.dart';

class MyCard extends StatelessWidget {
  const MyCard({super.key, required this.item});

  final MyEntity item;

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.all(12),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              item.title,
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 8),
            Text(
              'Created: ${item.createdAt}',
              style: Theme.of(context).textTheme.bodySmall,
            ),
          ],
        ),
      ),
    );
  }
}
```

---

### 🛣️ STEP 4: Register Routes

**File**: `lib/core/routes/app_routes.dart`

Add your route:
```dart
abstract final class AppRoutes {
  // ... existing routes ...
  
  // ── My Feature ──
  static const String myFeature = '/my-feature';
}

abstract final class AppPages {
  static final List<GetPage<dynamic>> pages = [
    // ... existing pages ...
    
    GetPage(
      name: AppRoutes.myFeature,
      page: () => const MyFeaturePage(),
    ),
  ];
}
```

---

### 🏠 STEP 5: Add to Home Screen

**File**: `lib/features/home/presentation/controllers/home_controller.dart`

Add your feature to the home options:
```dart
final homeOptions = [
  // ... existing options ...
  HomeOption(
    title: 'My Feature',
    icon: AppAssets.myFeatureIcon,
    route: AppRoutes.myFeature,
  ),
];
```

---

## Common Patterns

### Pattern 1: Pagination
```dart
class PaginatedResponse {
  final List<MyEntity> items;
  final int totalPages;
  final int currentPage;

  PaginatedResponse({
    required this.items,
    required this.totalPages,
    required this.currentPage,
  });
}
```

### Pattern 2: Search/Filter
```dart
Future<List<MyEntity>> searchItems({required String query}) {
  return _repository.searchItems(query: query);
}
```

### Pattern 3: Update/Edit
```dart
Future<MyEntity> updateItem({
  required String id,
  required Map<String, dynamic> updates,
}) async {
  // Validate updates
  // Call repository
  // Refresh local list
}
```

---

## Testing Checklist

- [ ] Controller initializes successfully
- [ ] API call returns correct data
- [ ] Error cases handled properly
- [ ] Loading states displayed
- [ ] Empty state shown when no data
- [ ] Navigation works
- [ ] Back button works
- [ ] Session token included in requests

---

## Performance Tips

1. **Lazy load images**: Use `Image.network` with caching
2. **Pagination**: Implement `FutureBuilder` with pagination
3. **Debounce search**: Use `Timer.run()` or `Rx.debounce()`
4. **Memory cleanup**: Override `onClose()` to dispose resources

---

## Common Mistakes to Avoid

❌ **DON'T**: Put HTTP calls directly in Controllers
✅ **DO**: Use UseCases and Repositories

❌ **DON'T**: Hardcode API endpoints
✅ **DO**: Use `ApiConstants`

❌ **DON'T**: Ignore error states
✅ **DO**: Always handle and display errors

❌ **DON'T**: Create controller instances in multiple places
✅ **DO**: Use GetX Bindings or single `init:`

❌ **DON'T**: Mix business logic with UI logic
✅ **DO**: Keep Controllers focused on state, not computation

---

## Troubleshooting

### Q: Page not showing?
- Check route is registered in `AppPages`
- Verify controller is initialized with `init: MyFeatureController()`
- Check for typos in route names

### Q: API calls not working?
- Verify endpoint in `ApiConstants`
- Check Dio configuration in `DioClient`
- Look at network logs (PrettyDioLogger)

### Q: State not updating?
- Ensure using `.obs` for observables
- Check `Obx()` wrapper in UI
- Verify controller is `GetBuilder` or `Obx`

### Q: Memory leaks?
- Override `onClose()` to dispose resources
- Cancel streams/listeners
- Clear timers

---

## API Conventions

### Request Format
```json
{
  "username": "user@example.com",
  "password": "password123"
}
```

### Response Format (Success)
```json
{
  "success": true,
  "data": { ... },
  "message": "Operation successful"
}
```

### Response Format (Error)
```json
{
  "success": false,
  "error": "Invalid credentials",
  "code": 401
}
```

---

## Deployment Checklist

Before pushing to production:
- [ ] Run `flutter analyze` (no warnings)
- [ ] Remove debug prints
- [ ] Test all error scenarios
- [ ] Verify API endpoints are live
- [ ] Update version in `pubspec.yaml`
- [ ] Test on real device
- [ ] Test on slow network
- [ ] Verify session persistence
- [ ] Check token refresh logic (if applicable)
