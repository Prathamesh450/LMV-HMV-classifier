import 'package:flutter/material.dart';
import 'screens/login_screen.dart';

void main() {
  runApp(const SecuritySystemApp());
}

class SecuritySystemApp extends StatelessWidget {
  const SecuritySystemApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Security System',
      theme: ThemeData(
        primarySwatch: Colors.blue,
        visualDensity: VisualDensity.adaptivePlatformDensity,
      ),
      home: const LoginScreen(),
      debugShowCheckedModeBanner: false,
    );
  }
}
