import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'services/auth_service.dart';
import 'screens/auth/login_screen.dart';
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
    // Listen to authentication state changes
    final authService = Provider.of<AuthService>(context);

    if (authService.isAuthenticated) {
      return const HomeScreenPlaceholder();
    } else {
      return const LoginScreen();
    }
  }
}

// Temporary Home Screen Placeholder until we build the Marketplace
class HomeScreenPlaceholder extends StatelessWidget {
  const HomeScreenPlaceholder({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('BorrowCircle Marketplace'),
        actions: [
          IconButton(
            icon: const Icon(Icons.logout),
            onPressed: () {
              Provider.of<AuthService>(context, listen: false).logout();
            },
          ),
        ],
      ),
      body: const Center(
        child: Text(
          'Welcome to BorrowCircle!\nYou are successfully logged in.',
          textAlign: TextAlign.center,
          style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
        ),
      ),
    );
  }
}