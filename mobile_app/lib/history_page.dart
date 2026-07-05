import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

class HistoryPage extends StatefulWidget {
  const HistoryPage({super.key});

  @override
  State<HistoryPage> createState() => _HistoryPageState();
}

class _HistoryPageState extends State<HistoryPage> {
  List history = [];
  final String url = "http://192.168.100.6:5000/api/crowd-data";

  @override
  void initState() {
    super.initState();
    fetchHistory();
  }

  Future<void> fetchHistory() async {
    final response = await http.get(Uri.parse(url));
    if (response.statusCode == 200) {
      setState(() {
        history = jsonDecode(response.body);
      });
    }
  }

  Color getRiskColor(String risk) {
    switch (risk) {
      case "HIGH":
        return Colors.red;
      case "MEDIUM":
        return Colors.orange;
      default:
        return Colors.green;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("Crowd History"),
      ),
      body: RefreshIndicator(
        onRefresh: fetchHistory,
        child: ListView.builder(
          padding: const EdgeInsets.all(12),
          itemCount: history.length,
          itemBuilder: (context, index) {
            final item = history[index];
            return Card(
              child: ListTile(
                title: Text(item["zone"] ?? "Unknown Zone"),
                subtitle: Text(
                  "People: ${item["person_count"]} | Prediction: ${item["prediction"]}",
                ),
                trailing: Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 10,
                    vertical: 6,
                  ),
                  decoration: BoxDecoration(
                    color: getRiskColor(item["risk_level"]),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Text(
                    item["risk_level"],
                    style: const TextStyle(color: Colors.white),
                  ),
                ),
              ),
            );
          },
        ),
      ),
    );
  }
}