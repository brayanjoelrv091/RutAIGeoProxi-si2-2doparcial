import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';

class SavedAccount {
  final String email;
  final String password;

  SavedAccount({required this.email, required this.password});

  Map<String, dynamic> toJson() => {'email': email, 'password': password};

  factory SavedAccount.fromJson(Map<String, dynamic> json) =>
      SavedAccount(email: json['email'], password: json['password']);
}

class SavedAccountsManager {
  static const _key = 'saved_accounts';

  static Future<List<SavedAccount>> getSavedAccounts() async {
    final prefs = await SharedPreferences.getInstance();
    final data = prefs.getStringList(_key);
    if (data == null) return [];
    return data
        .map((e) => SavedAccount.fromJson(jsonDecode(e) as Map<String, dynamic>))
        .toList();
  }

  static Future<void> saveAccount(String email, String password) async {
    final accounts = await getSavedAccounts();
    accounts.removeWhere((acc) => acc.email.toLowerCase() == email.toLowerCase());
    accounts.add(SavedAccount(email: email, password: password));
    
    final prefs = await SharedPreferences.getInstance();
    await prefs.setStringList(_key, accounts.map((a) => jsonEncode(a.toJson())).toList());
  }

  static Future<void> removeAccount(String email) async {
    final accounts = await getSavedAccounts();
    accounts.removeWhere((acc) => acc.email.toLowerCase() == email.toLowerCase());
    
    final prefs = await SharedPreferences.getInstance();
    await prefs.setStringList(_key, accounts.map((a) => jsonEncode(a.toJson())).toList());
  }
}
