import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter/foundation.dart'; // Add this!
import 'package:http/http.dart' as http;
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'api_service.dart';

class AuthService with ChangeNotifier {
  static final _storage = const FlutterSecureStorage();

  bool _isAuthenticated = false;
  bool get isAuthenticated => _isAuthenticated;

  static const String _accessTokenKey = 'access_token';
  static const String _refreshTokenKey = 'refresh_token';

  AuthService() {
    _checkAuthStatus();
  }

  // Helper to get platform-specific options
  dynamic get _storageOptions => kIsWeb ? null : const AndroidOptions(encryptedSharedPreferences: true);

  Future<void> _checkAuthStatus() async {
    try {
      String? token = await _storage.read(
        key: _accessTokenKey,
        aOptions: _storageOptions, // Use the dynamic option
      );
      _isAuthenticated = token != null;
    } catch (e) {
      _isAuthenticated = false;
    }
    notifyListeners();
  }

  Future<Map<String, dynamic>> register(Map<String, dynamic> data) async {
    final response = await ApiService.post('auth/register/', data);
    if (response['statusCode'] == 201) {
      await _saveTokens(response['body']['access'], response['body']['refresh']);
      _isAuthenticated = true;
      notifyListeners();
    }
    return response;
  }

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

  Future<void> logout() async {
    String? refresh = await _storage.read(
      key: _refreshTokenKey,
      aOptions: _storageOptions,
    );
    if (refresh != null) {
      try {
        await http.post(
          Uri.parse('${ApiService.baseUrl}/auth/logout/'),
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode({'refresh': refresh}),
        );
      } catch (e) {}
    }
    await _storage.delete(key: _accessTokenKey, aOptions: _storageOptions);
    await _storage.delete(key: _refreshTokenKey, aOptions: _storageOptions);
    _isAuthenticated = false;
    notifyListeners();
  }

  Future<void> _saveTokens(String access, String refresh) async {
    await _storage.write(key: _accessTokenKey, value: access, aOptions: _storageOptions);
    await _storage.write(key: _refreshTokenKey, value: refresh, aOptions: _storageOptions);
  }
}