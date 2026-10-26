class Item {
  final String id;
  final String title;
  final String description;
  final double dailyRate;
  final double? securityDeposit;
  final String location;
  final String condition;
  final bool isAvailable;
  final String? imageUrl;
  final String ownerName;

  Item({
    required this.id,
    required this.title,
    required this.description,
    required this.dailyRate,
    this.securityDeposit,
    required this.location,
    required this.condition,
    required this.isAvailable,
    this.imageUrl,
    required this.ownerName,
  });

  factory Item.fromJson(Map<String, dynamic> json) {
    // Extract primary photo if available
    String? photoUrl;
    if (json['photos'] != null && (json['photos'] as List).isNotEmpty) {
      photoUrl = json['photos'][0]['image'];
    }

    return Item(
      id: json['id'].toString(),
      title: json['title'] ?? '',
      description: json['description'] ?? '',
      dailyRate: double.tryParse(json['daily_rate'].toString()) ?? 0.0,
      securityDeposit: json['security_deposit'] != null 
          ? double.tryParse(json['security_deposit'].toString()) 
          : null,
      location: json['location'] ?? 'Local',
      condition: json['condition'] ?? 'Good',
      isAvailable: json['is_available'] ?? true,
      imageUrl: photoUrl ?? json['image_url'],
      ownerName: json['owner_username'] ?? json['owner']?['username'] ?? 'Community Member',
    );
  }
}   