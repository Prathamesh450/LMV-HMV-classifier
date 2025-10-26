import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:security_system/main.dart';

void main() {
  testWidgets('App builds and shows login', (WidgetTester tester) async {
    await tester.pumpWidget(const SecuritySystemApp());
    expect(find.byType(MaterialApp), findsOneWidget);
  });
}
