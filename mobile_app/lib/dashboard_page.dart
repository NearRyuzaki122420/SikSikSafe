import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:socket_io_client/socket_io_client.dart' as io;

import 'history_page.dart';
import 'chart_page.dart';
import 'widgets/stat_card.dart';
import 'widgets/zone_card.dart';

class DashboardPage extends StatefulWidget {
  final String userName;

  const DashboardPage({super.key, required this.userName});

  @override
  State<DashboardPage> createState() => _DashboardPageState();
}

class _DashboardPageState extends State<DashboardPage> {
  List zones = [];
  String alertMessage = "No active alerts";
  int totalZones = 0;
  int totalPeople = 0;
  int highRiskCount = 0;

  late io.Socket socket;

  final String baseUrl = "http://192.168.1.16:5000";

  @override
  void initState() {
    super.initState();
    fetchZones();
    fetchSummary();
    connectSocket();
  }

  Future<void> fetchZones() async {
    final response = await http.get(
      Uri.parse("$baseUrl/api/crowd-data/zones/latest"),
    );

    if (response.statusCode == 200) {
      setState(() {
        zones = jsonDecode(response.body);
      });
    }
  }

  Future<void> fetchSummary() async {
    final response = await http.get(
      Uri.parse("$baseUrl/api/stats/summary"),
    );

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);

      setState(() {
        totalZones = data["total_zones"] ?? 0;
        totalPeople = data["total_people"] ?? 0;
        highRiskCount = data["high_risk_count"] ?? 0;

        if (data["latest_alert"] != null) {
          alertMessage =
              "${data["latest_alert"]["zone"]} - ${data["latest_alert"]["prediction"]}";
        }
      });
    }
  }

  void connectSocket() {
    socket = io.io(
      baseUrl,
      io.OptionBuilder().setTransports(['websocket']).build(),
    );

    socket.onConnect((_) {
      debugPrint("Socket connected");
    });

    socket.on("crowdUpdate", (_) {
      fetchZones();
      fetchSummary();
    });

    socket.on("alert", (data) {
      setState(() {
        alertMessage = data["message"] ?? "New alert received";
      });
    });
  }

  @override
  void dispose() {
    socket.dispose();
    super.dispose();
  }

  Future<void> refreshAll() async {
    await fetchZones();
    await fetchSummary();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("SikSikSafe Dashboard"),
        actions: [
          IconButton(
            icon: const Icon(Icons.pie_chart),
            onPressed: () {
              Navigator.push(
                context,
                MaterialPageRoute(builder: (_) => const ChartPage()),
              );
            },
          ),
          IconButton(
            icon: const Icon(Icons.history),
            onPressed: () {
              Navigator.push(
                context,
                MaterialPageRoute(builder: (_) => const HistoryPage()),
              );
            },
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: refreshAll,
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            Text(
              "Welcome, ${widget.userName}",
              style: const TextStyle(
                fontSize: 22,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 14),
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.red.shade100,
                borderRadius: BorderRadius.circular(14),
              ),
              child: Row(
                children: [
                  const Icon(Icons.warning_amber_rounded, color: Colors.red),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Text(
                      alertMessage,
                      style: const TextStyle(
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 18),
            Row(
              children: [
                StatCard(
                  title: "Zones",
                  value: totalZones.toString(),
                  icon: Icons.map,
                  color: Colors.blue,
                ),
                StatCard(
                  title: "People",
                  value: totalPeople.toString(),
                  icon: Icons.people,
                  color: Colors.green,
                ),
                StatCard(
                  title: "High Risk",
                  value: highRiskCount.toString(),
                  icon: Icons.report,
                  color: Colors.red,
                ),
              ],
            ),
            const SizedBox(height: 22),
            const Text(
              "Live Zone Overview",
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 10),
            ...zones.map((zone) => ZoneCard(zone: zone)),
          ],
        ),
      ),
    );
  }
}