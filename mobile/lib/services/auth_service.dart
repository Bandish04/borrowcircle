
import 'dart:convert';

import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:http/http.dart' as http;

import 'api_service.dart';

class AuthService with ChangeNotifier {
  static const _storage = FlutterSecureStorage();

  bool _isAuthenticated = false;
  bool _isVerified = false;
  String _currentEmail = '';

  bool get isAuthenticated => _isAuthenticated;
  bool get isVerified => _isVerified;
  String get currentEmail => _currentEmail;

  static const String _accessTokenKey = 'access_token';
  static const String _refreshTokenKey = 'refresh_token';
  static const String _isVerifiedKey = 'is_verified';
  static const String _emailKey = 'current_email';

  AuthService() {
    _checkAuthStatus();
  }

  dynamic get _storageOptions =>
      kIsWeb ? null : const AndroidOptions(
        encryptedSharedPreferences: true,
      );

  Future<void> _checkAuthStatus() async {
    try {
      final token = await _storage.read(
        key: _accessTokenKey,
        aOptions: _storageOptions,
      );

      final verifiedStr = await _storage.read(
        key: _isVerifiedKey,
        aOptions: _storageOptions,
      );

      final email = await _storage.read(
        key: _emailKey,
        aOptions: _storageOptions,
      );

      _isAuthenticated = token != null && token.isNotEmpty;
      _isVerified = verifiedStr == 'true';
      _currentEmail = email ?? '';
    } catch (e) {
      _isAuthenticated = false;
      _isVerified = false;
      _currentEmail = '';
    }

    notifyListeners();
  }

  Future<Map<String, dynamic>> _post(
    String endpoint,
    Map<String, dynamic> data, {
    String? accessToken,
  }) async {
    try {
      final headers = <String, String>{
        'Content-Type': 'application/json',
      };

      if (accessToken != null) {
        headers['Authorization'] = 'Bearer $accessToken';
      }

      final response = await http.post(
        Uri.parse('${ApiService.baseUrl}/$endpoint'),
        headers: headers,
        body: jsonEncode(data),
      );

      dynamic body;

      try {
        body = response.body.isNotEmpty
            ? jsonDecode(response.body)
            : <String, dynamic>{};
      } catch (_) {
        body = {
          'error':
              'Server returned an invalid response '
              '(Status: ${response.statusCode}).',
        };
      }

      return {
        'statusCode': response.statusCode,
        'body': body,
      };
    } catch (e) {
      return {
        'statusCode': 500,
        'body': {'error': 'Unable to connect to the server: $e'},
      };
    }
  }

  Future<void> _saveTokens(String access, String refresh) async {
    await _storage.write(
      key: _accessTokenKey,
      value: access,
      aOptions: _storageOptions,
    );

    await _storage.write(
      key: _refreshTokenKey,
      value: refresh,
      aOptions: _storageOptions,
    );
  }

  Future<void> _clearTokens() async {
    await _storage.delete(
      key: _accessTokenKey,
      aOptions: _storageOptions,
    );

    await _storage.delete(
      key: _refreshTokenKey,
      aOptions: _storageOptions,
    );
  }

  Future<void> _saveEmail(String email) async {
    _currentEmail = email;

    await _storage.write(
      key: _emailKey,
      value: email,
      aOptions: _storageOptions,
    );
  }

  Future<Map<String, dynamic>?> getUserProfile() async {
    try {
      final token = await _storage.read(
        key: _accessTokenKey,
        aOptions: _storageOptions,
      );

      if (token == null) return null;

      final response = await http.get(
        Uri.parse('${ApiService.baseUrl}/auth/me/'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $token',
        },
      );

      if (response.statusCode == 200) {
        return jsonDecode(response.body) as Map<String, dynamic>;
      }
    } catch (_) {
      // Profile retrieval failure is handled by the caller.
    }

    return null;
  }

  // Registration creates an unverified account.
  // It does not authenticate the user or save JWT tokens.
  Future<Map<String, dynamic>> register(
    Map<String, dynamic> data,
  ) async {
    final email = (data['email'] as String?)?.trim() ?? '';

    final response = await _post(
      'auth/register/',
      data,
    );

    if (response['statusCode'] == 201) {
      await _clearTokens();
      await _saveEmail(email);

      _isAuthenticated = false;
      _isVerified = false;

      await _storage.write(
        key: _isVerifiedKey,
        value: 'false',
        aOptions: _storageOptions,
      );

      notifyListeners();
    }

    return response;
  }

  // Email verification is public and requires email + OTP.
  Future<Map<String, dynamic>> verifyEmail(String code) async {
    final email = await _storage.read(
      key: _emailKey,
      aOptions: _storageOptions,
    );

    if (email == null || email.isEmpty) {
      return {
        'statusCode': 400,
        'body': {'error': 'Please register or enter your email address again.'},
      };
    }

    final response = await _post(
      'auth/verify-email/',
      {
        'email': email,
        'code': code.trim(),
      },
    );

    if (response['statusCode'] == 200) {
      await _storage.write(
        key: _isVerifiedKey,
        value: 'true',
        aOptions: _storageOptions,
      );

      _isVerified = true;
      _isAuthenticated = false;

      notifyListeners();
    }

    return response;
  }

  Future<void> markVerified() async {
    await _storage.write(
      key: _isVerifiedKey,
      value: 'true',
      aOptions: _storageOptions,
    );

    _isVerified = true;
    _isAuthenticated = false;

    notifyListeners();
  }

  // Resend OTP is public and requires the registered email.
  Future<Map<String, dynamic>> resendOTP() async {
    final email = await _storage.read(
      key: _emailKey,
      aOptions: _storageOptions,
    );

    if (email == null || email.isEmpty) {
      return {
        'statusCode': 400,
        'body': {'error': 'Email address is missing.'},
      };
    }

    return _post(
      'auth/resend-otp/',
      {'email': email},
    );
  }

  Future<Map<String, dynamic>> forgotPassword(String email) async {
    return _post(
      'auth/forgot-password/',
      {'email': email.trim()},
    );
  }

  Future<Map<String, dynamic>> verifyResetCode(
    String email,
    String code,
  ) async {
    return _post(
      'auth/verify-reset-code/',
      {
        'email': email.trim(),
        'code': code.trim(),
      },
    );
  }

  Future<Map<String, dynamic>> resetPassword(
    String email,
    String code,
    String newPassword,
  ) async {
    return _post(
      'auth/reset-password/',
      {
        'email': email.trim(),
        'code': code.trim(),
        'new_password': newPassword,
      },
    );
  }

  Future<Map<String, dynamic>> login(
    String email,
    String password,
  ) async {
    final response = await _post(
      'auth/login/',
      {
        'email': email.trim(),
        'password': password,
      },
    );

    if (response['statusCode'] == 200) {
      final body = response['body'];

      if (body is! Map ||
          body['access'] == null ||
          body['refresh'] == null) {
        return {
          'statusCode': 500,
          'body': {'error': 'The server did not return valid login tokens.'},
        };
      }

      await _saveTokens(
        body['access'].toString(),
        body['refresh'].toString(),
      );

      await _saveEmail(email.trim());

      _isAuthenticated = true;
      _isVerified = true;

      await _storage.write(
        key: _isVerifiedKey,
        value: 'true',
        aOptions: _storageOptions,
      );

      notifyListeners();
    }

    return response;
  }

  Future<void> logout() async {
    final access = await _storage.read(
      key: _accessTokenKey,
      aOptions: _storageOptions,
    );

    final refresh = await _storage.read(
      key: _refreshTokenKey,
      aOptions: _storageOptions,
    );

    if (access != null && refresh != null) {
      await _post(
        'auth/logout/',
        {'refresh': refresh},
        accessToken: access,
      );
    }

    await _clearTokens();

    await _storage.delete(
      key: _isVerifiedKey,
      aOptions: _storageOptions,
    );

    await _storage.delete(
      key: _emailKey,
      aOptions: _storageOptions,
    );

    _isAuthenticated = false;
    _isVerified = false;
    _currentEmail = '';

    notifyListeners();
  }
}
