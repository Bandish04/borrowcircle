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
      final List<dynamic> body = jsonDecode(response.body);
      return body.map((item) => Item.fromJson(item)).toList();
    } else {
      throw Exception('Failed to load items');
    }
  }
}