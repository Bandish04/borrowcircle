import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'api_service.dart';

class AuthService with ChangeNotifier {
  static final _storage = const FlutterSecureStorage();

  bool _isAuthenticated = false;
  bool get isAuthenticated => _isAuthenticated;

  // Key names for storage
  static const String _accessTokenKey = 'access_token';
  static const String _refreshTokenKey = 'refresh_token';

  // Initialize: check if user is logged in
  AuthService() {
    _checkAuthStatus();
  }

  Future<void> _checkAuthStatus() async {
    String? token = await _storage.read(key: _accessTokenKey);
    _isAuthenticated = token != null;
    notifyListeners();
  }

  // Register
  Future<Map<String, dynamic>> register(Map<String, dynamic> data) async {
    final response = await ApiService.post('accounts/register/', data);

    if (response['statusCode'] == 201) {
      await _saveTokens(response['body']['access'], response['body']['refresh']);
      _isAuthenticated = true;
      notifyListeners();
    }
    return response;
  }

  // Login
  Future<Map<String, dynamic>> login(String email, String password) async {
    final response = await ApiService.post('accounts/login/', {
      'email': email,
      'password': password,
    });

    if (response['statusCode'] == 200) {
      await _saveTokens(response['body']['access'], response['body']['refresh']);
      _isAuthenticated = true;
      notifyListeners();
    }
    return response;
  }

  // Logout
  Future<void> logout() async {
    String? refresh = await _storage.read(key: _refreshTokenKey);

    // Attempt to blacklist token on server
    if (refresh != null) {
      try {
        await http.post(
          Uri.parse('${ApiService.baseUrl}/accounts/logout/'),
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode({'refresh': refresh}),
        );
      } catch (e) {
        // Silently fail if network issue during logout
      }
    }

    await _storage.delete(key: _accessTokenKey);
    await _storage.delete(key: _refreshTokenKey);
    _isAuthenticated = false;
    notifyListeners();
  }

  Future<void> _saveTokens(String access, String refresh) async {
    await _storage.write(key: _accessTokenKey, value: access);
    await _storage.write(key: _refreshTokenKey, value: refresh);
  }
}
