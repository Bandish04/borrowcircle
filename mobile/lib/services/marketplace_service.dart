import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/item.dart';
import 'api_service.dart';

class MarketplaceService {
  static Future<List<Item>> fetchItems({String? location, String? category}) async {
    // Build query parameters
    final Map<String, String> queryParams = {};
    if (location != null) queryParams['location'] = location;
    if (category != null) queryParams['category'] = category;

    final uri = Uri.parse('${ApiService.baseUrl}/items/').replace(queryParameters: queryParams);

    final response = await http.get(uri);

    if (response.statusCode == 200) {
      final decoded = jsonDecode(response.body);
      List<dynamic> list;

      // Handle DRF Pagination (if results key exists, use it)
      if (decoded is Map && decoded.containsKey('results')) {
        list = decoded['results'];
      } else {
        list = decoded as List<dynamic>;
      }

      return list.map((item) => Item.fromJson(item)).toList();
    } else {
      throw Exception('Failed to load items');
    }
  }

  static Future<List<dynamic>> fetchCategories() async {
    final response = await http.get(Uri.parse('${ApiService.baseUrl}/items/categories/'));

    if (response.statusCode == 200) {
      final decoded = jsonDecode(response.body);

      // DEEP DEFENSIVE PARSING
      if (decoded is Map) {
        if (decoded.containsKey('results')) {
          return decoded['results'] as List<dynamic>;
        }
        return [decoded];
      }

      return decoded as List<dynamic>;
    } else {
      throw Exception('Failed to load categories: ${response.statusCode}');
    }
  }
}
