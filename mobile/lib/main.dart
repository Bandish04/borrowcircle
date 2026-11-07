import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'services/auth_service.dart';
import 'screens/auth/login_screen.dart';
import 'screens/auth/verify_email_screen.dart';
import 'screens/marketplace/home_screen.dart';
import 'theme.dart';

void main() {
  runApp(const BorrowCircleApp());
}

class BorrowCircleApp extends StatelessWidget {
  const BorrowCircleApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => AuthService()),
      ],
      child: MaterialApp(
        title: 'BorrowCircle',
        theme: BorrowCircleTheme.lightTheme,
        debugShowCheckedModeBanner: false,
        home: const AuthWrapper(),
      ),
    );
  }
}

class AuthWrapper extends StatelessWidget {
  const AuthWrapper({super.key});

  @override
  Widget build(BuildContext context) {
    final authService = Provider.of<AuthService>(context);

    if (!authService.isAuthenticated) {
      // Not logged in → show login
      return const LoginScreen();
    }

    if (!authService.isVerified) {
      // Logged in but email not verified → show verify screen
      // Pass the stored email so the screen can display it
      return VerifyEmailScreen(email: authService.currentEmail);
    }

    // Logged in and verified → go to app
    return const HomeScreen();
  }
}
