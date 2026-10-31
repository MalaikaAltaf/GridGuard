class User {
  final String id;
  final String name;
  final String role;
  final String email;

  User({
    required this.id,
    required this.name,
    required this.role,
    required this.email,
  });

  factory User.fromJson(Map<String, dynamic> json) {
    return User(
      id: json['id'],
      name: json['name'],
      role: json['role'],
      email: json['email'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name': name,
      'role': role,
      'email': email,
    };
  }
}
