import 'dart:convert';
import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

class ChartPage extends StatefulWidget {
  const ChartPage({super.key});

  @override
  State<ChartPage> createState() => _ChartPageState();
}

class _ChartPageState extends State<ChartPage> {
  Map<String, dynamic> riskCounts = {
    "LOW": 0,
    "MEDIUM": 0,
    "HIGH": 0,
  };

  final String url = "http://192.168.1.5:5000/api/stats/risk-counts";

  @override
  void initState() {
    super.initState();
    fetchRiskCounts();
  }

  Future<void> fetchRiskCounts() async {
    final response = await http.get(Uri.parse(url));
    if (response.statusCode == 200) {
      setState(() {
        riskCounts = jsonDecode(response.body);
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final low = (riskCounts["LOW"] ?? 0).toDouble();
    final medium = (riskCounts["MEDIUM"] ?? 0).toDouble();
    final high = (riskCounts["HIGH"] ?? 0).toDouble();

    return Scaffold(
      appBar: AppBar(
        title: const Text("Risk Statistics"),
      ),
      body: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          children: [
            const SizedBox(height: 20),
            const Text(
              "Crowd Risk Level Distribution",
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 30),
            SizedBox(
              height: 250,
              child: PieChart(
                PieChartData(
                  sectionsSpace: 3,
                  centerSpaceRadius: 50,
                  sections: [
                    PieChartSectionData(
                      value: low,
                      title: "Low\n${low.toInt()}",
                      color: Colors.green,
                      radius: 60,
                    ),
                    PieChartSectionData(
                      value: medium,
                      title: "Med\n${medium.toInt()}",
                      color: Colors.orange,
                      radius: 60,
                    ),
                    PieChartSectionData(
                      value: high,
                      title: "High\n${high.toInt()}",
                      color: Colors.red,
                      radius: 60,
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}