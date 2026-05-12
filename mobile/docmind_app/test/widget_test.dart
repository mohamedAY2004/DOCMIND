// This is a basic Flutter widget test.
//
// To perform an interaction with a widget in your test, use the WidgetTester
// utility in the flutter_test package. For example, you can send tap and scroll
// gestures. You can also use WidgetTester to find child widgets in the widget
// tree, read text, and verify that the values of widget properties are correct.

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:get/get.dart';

import 'package:docmind_app/main.dart';
import 'package:docmind_app/core/theme/theme_service.dart';

void main() {
  setUp(() {
    Get.testMode = true;
    Get.put(ThemeService()..isDarkMode.value = false);
  });

  tearDown(() {
    Get.reset();
  });

  testWidgets('App builds smoke test', (WidgetTester tester) async {
    await tester.pumpWidget(const DocMindApp());
    await tester.pumpAndSettle();

    expect(find.byType(Scaffold), findsWidgets);
  });
}
