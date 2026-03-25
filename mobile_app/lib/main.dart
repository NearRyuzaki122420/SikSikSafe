import 'package:flutter/material.dart';
import 'login_page.dart';

void main() {
  runApp(const SiksikSafeApp());
}

class SiksikSafeApp extends StatelessWidget {
  const SiksikSafeApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'SiksikSafe',
      theme: ThemeData(primarySwatch: Colors.red),
      home: const LoginPage(),
    );
  }
}
