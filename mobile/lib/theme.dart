import 'package:flutter/material.dart';

class BorrowCircleTheme {
  static const Color primary = Color(0xFF5E60CE); // Slate Blue
  static const Color secondary = Color(0xFFFF9F1C); // Warm Amber
  static const Color background = Color(0xFFF7F5F2); // Warm Off-White
  static const Color surface = Color(0xFFFFFFFF);
  static const Color textDark = Color(0xFF2B2D42);

  static ThemeData get lightTheme {
    return ThemeData(
      useMaterial3: true,
      scaffoldBackgroundColor: background,
      colorScheme: ColorScheme.fromSeed(
        seedColor: primary,
        primary: primary,
        secondary: secondary,
        surface: surface,
      ),
      appBarTheme: const AppBarTheme(
        backgroundColor: surface,
        elevation: 0,
        foregroundColor: textDark,
        centerTitle: true,
      ),
    );
  }
}