import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'api_service.dart';

class AuthService with ChangeNotifier {
  static final _storage = const FlutterSecureStorage();

  bool _isAuthenticated = false;
  bool get isAuthenticated => _isAuthenticated;

  // Key names for local storage
  static const String _accessTokenKey = 'access_token';
  static const String _refreshTokenKey = 'refresh_token';

  AuthService() {
    _checkAuthStatus();
  }

  // Verify if a token is already saved when the app starts
  Future<void> _checkAuthStatus() async {
    try {
      String? token = await _storage.read(
        key: _accessTokenKey,
        aOptions: const AndroidOptions(encryptedSharedPreferences: true),
      );
      _isAuthenticated = token != null;
    } catch (e) {
      _isAuthenticated = false;
    }
    notifyListeners();
  }

  // Register a new account
  Future<Map<String, dynamic>> register(Map<String, dynamic> data) async {
    final response = await ApiService.post('auth/register/', data);

    if (response['statusCode'] == 201) {
      await _saveTokens(response['body']['access'], response['body']['refresh']);
      _isAuthenticated = true;
      notifyListeners();
    }
    return response;
  }

  // Log in to an existing account
  Future<Map<String, dynamic>> login(String email, String password) async {
    final response = await ApiService.post('auth/login/', {
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

  // Log out of the account
  Future<void> logout() async {
    String? refresh = await _storage.read(
      key: _refreshTokenKey,
      aOptions: const AndroidOptions(encryptedSharedPreferences: true),
    );

    if (refresh != null) {
      try {
        await http.post(
          Uri.parse('${ApiService.baseUrl}/auth/logout/'),
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode({'refresh': refresh}),
        );
      } catch (e) {
        // Silently fail if server is down during logout
      }
    }

    await _storage.delete(key: _accessTokenKey, aOptions: const AndroidOptions(encryptedSharedPreferences: true));
    await _storage.delete(key: _refreshTokenKey, aOptions: const AndroidOptions(encryptedSharedPreferences: true));
    _isAuthenticated = false;
    notifyListeners();
  }

  Future<void> _saveTokens(String access, String refresh) async {
    await _storage.write(
      key: _accessTokenKey,
      value: access,
      aOptions: const AndroidOptions(encryptedSharedPreferences: true),
    );
    await _storage.write(
      key: _refreshTokenKey,
      value: refresh,
      aOptions: const AndroidOptions(encryptedSharedPreferences: true),
    );
  }
} 