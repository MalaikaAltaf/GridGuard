import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'theme.dart';
import 'screens/login_screen.dart';

void main() {
  runApp(const ProviderScope(child: GridGuardApp()));
}

class GridGuardApp extends StatelessWidget {
  const GridGuardApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Grid-Guard AI',
      theme: AppTheme.themeData,
      debugShowCheckedModeBanner: false,
      home: const LoginScreen(),
    );
  }
}
