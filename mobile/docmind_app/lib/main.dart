import 'package:flutter/material.dart';
import 'package:get/get.dart';

import 'features/auth/data/datasources/auth_local_data_source.dart';

import 'core/routes/app_routes.dart';
import 'core/theme/app_theme.dart';
import 'core/theme/theme_service.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();

  final themeService = await ThemeService.init();
  Get.put(themeService);
  Get.changeThemeMode(
    themeService.isDarkMode.value ? ThemeMode.dark : ThemeMode.light,
  );

  final local = AuthLocalDataSource();
  final hasSession = await local.hasSession();

  runApp(DocMindApp(
    initialRoute: hasSession ? AppRoutes.home : AppRoutes.signIn,
  ));
}

class DocMindApp extends StatelessWidget {
  const DocMindApp({
    super.key,
    this.initialRoute = AppRoutes.signIn,
  });

  final String initialRoute;

  @override
  Widget build(BuildContext context) {
    final themeService = Get.find<ThemeService>();

    return Obx(() => GetMaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'DocMind',
      theme: AppTheme.light,
      darkTheme: AppTheme.dark,
      themeMode: themeService.isDarkMode.value
          ? ThemeMode.dark
          : ThemeMode.light,
      initialRoute: initialRoute,
      getPages: AppPages.pages,
    ));
  }
}
