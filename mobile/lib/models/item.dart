class Item {
  final String id;
  final String title;
  final String description;
  final double depositAmount;
  final int maxLoanDays;
  final String location;
  final String condition;
  final bool isAvailable;
  final String? imageUrl;
  final String ownerName;

  Item({
    required this.id,
    required this.title,
    required this.description,
    required this.depositAmount,
    required this.maxLoanDays,
    required this.location,
    required this.condition,
    required this.isAvailable,
    this.imageUrl,
    required this.ownerName,
  });

  factory Item.fromJson(Map<String, dynamic> json) {
    // Extract cover photo if available
    String? photoUrl;
    if (json['photos'] != null && (json['photos'] as List).isNotEmpty) {
      photoUrl = json['photos'][0]['image'];
    }

    return Item(
      id: json['id'].toString(),
      title: json['title'] ?? '',
      description: json['description'] ?? '',
      depositAmount: double.tryParse(json['deposit_amount'].toString()) ?? 0.0,
      maxLoanDays: json['max_loan_days'] ?? 14,
      location: json['pickup_area'] ?? 'Local',
      condition: json['condition'] ?? 'Good',
      isAvailable: json['status'] == 'active',
      imageUrl: photoUrl ?? json['image_url'],
      ownerName: json['owner_username'] ?? 'Community Member',
    );
  }
}