import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:fl_chart/fl_chart.dart';
import 'cameras_page.dart';
import 'live_feed_page.dart';
import 'profile_page.dart';

class DashboardPage extends StatefulWidget {
  final String userName;

  const DashboardPage({super.key, required this.userName});

  @override
  State<DashboardPage> createState() => _DashboardPageState();
}

class _DashboardPageState extends State<DashboardPage> {
  int selectedIndex = 0;

  int activeCameras = 5;
  int activeIncidents = 3;
  int pendingAlerts = 2;
  int avgCrowdDensity = 56;

  final String baseUrl = "http://192.168.1.5:5000";

  List<double> crowdTrend = [20, 40, 65, 70, 85, 75];

  List criticalCameras = [
    {
      "name": "Auditorium Entrance",
      "location": "Building C - Hall 1",
      "risk": 89,
    },
    {
      "name": "Emergency Exit B",
      "location": "Building C - Left Side",
      "risk": 95,
    },
  ];

  @override
  void initState() {
    super.initState();
    fetchSummary();
  }

  Future<void> fetchSummary() async {
    final response = await http.get(Uri.parse("$baseUrl/api/stats/summary"));

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);

      setState(() {
        activeCameras = data["total_zones"] ?? 5;
        activeIncidents = data["high_risk_count"] ?? 3;
        pendingAlerts = data["pending_alerts"] ?? 2;
        avgCrowdDensity = data["avg_density"] ?? 56;
      });
    }
  }

  // ================= SIDEBAR =================
  Widget buildSidebar() {
    return Container(
      width: 240,
      color: Colors.white,
      child: Column(
        children: [
          const SizedBox(height: 30),
          const Text(
            "SikSikSafe Admin",
            style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 30),

          sidebarItem(Icons.dashboard, "Dashboard", 0),
          sidebarItem(Icons.camera_alt, "Cameras", 1),
          sidebarItem(Icons.rss_feed, "Live Feed", 2),
          sidebarItem(Icons.person, "Profile", 3),

          const Spacer(),

          const Padding(
            padding: EdgeInsets.all(20),
            child: Row(
              children: [
                Icon(Icons.logout, color: Colors.red),
                SizedBox(width: 10),
                Text("Logout", style: TextStyle(color: Colors.red)),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget sidebarItem(IconData icon, String title, int index) {
    bool active = selectedIndex == index;

    return GestureDetector(
      onTap: () {
        setState(() {
          selectedIndex = index;
        });
      },
      child: Container(
        margin: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: active ? const Color(0xFFF3ECFF) : Colors.transparent,
          borderRadius: BorderRadius.circular(10),
        ),
        child: Row(
          children: [
            Icon(icon, color: active ? Colors.purple : Colors.grey),
            const SizedBox(width: 10),
            Text(
              title,
              style: TextStyle(
                color: active ? Colors.purple : Colors.grey,
                fontWeight: active ? FontWeight.bold : FontWeight.normal,
              ),
            ),
          ],
        ),
      ),
    );
  }

  // ================= STAT CARD =================
  Widget statCard(String title, String value, IconData icon, Color color) {
    return Expanded(
      child: Container(
        margin: const EdgeInsets.all(8),
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(12),
        ),
        child: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: color.withOpacity(0.15),
                borderRadius: BorderRadius.circular(10),
              ),
              child: Icon(icon, color: color),
            ),
            const SizedBox(width: 10),
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  value,
                  style: const TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                Text(title, style: const TextStyle(color: Colors.grey)),
              ],
            ),
          ],
        ),
      ),
    );
  }

  // ================= LINE CHART =================
  Widget buildLineChart() {
    return LineChart(
      LineChartData(
        gridData: const FlGridData(show: false),
        titlesData: const FlTitlesData(show: false),
        borderData: FlBorderData(show: false),
        lineBarsData: [
          LineChartBarData(
            spots: crowdTrend
                .asMap()
                .entries
                .map((e) => FlSpot(e.key.toDouble(), e.value))
                .toList(),
            isCurved: true,
            color: Colors.purple,
            barWidth: 3,
            dotData: const FlDotData(show: true),
          ),
        ],
      ),
    );
  }

  // ================= CRITICAL CARD =================
  Widget buildCriticalCard(Map data) {
    return Container(
      margin: const EdgeInsets.symmetric(vertical: 6),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: const Color(0xFFFFF1F1),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                data["name"],
                style: const TextStyle(fontWeight: FontWeight.bold),
              ),
              Text(
                data["location"],
                style: const TextStyle(color: Colors.grey),
              ),
            ],
          ),
          Text(
            "${data["risk"]}%",
            style: const TextStyle(
              color: Colors.red,
              fontWeight: FontWeight.bold,
            ),
          ),
        ],
      ),
    );
  }

  // ================= PAGES =================
  Widget dashboardContent() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          "Dashboard Overview",
          style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold),
        ),
        const Text(
          "Real-time crowd monitoring analytics",
          style: TextStyle(color: Colors.grey),
        ),

        const SizedBox(height: 20),

        Row(
          children: [
            statCard(
              "Active Cameras",
              "$activeCameras",
              Icons.videocam,
              Colors.blue,
            ),
            statCard(
              "Active Incidents",
              "$activeIncidents",
              Icons.warning,
              Colors.red,
            ),
            statCard(
              "Pending Alerts",
              "$pendingAlerts",
              Icons.notifications,
              Colors.orange,
            ),
            statCard(
              "Avg Crowd Density",
              "$avgCrowdDensity%",
              Icons.groups,
              Colors.green,
            ),
          ],
        ),

        const SizedBox(height: 20),

        Expanded(
          child: Row(
            children: [
              Expanded(
                flex: 2,
                child: Container(
                  padding: const EdgeInsets.all(16),
                  color: Colors.white,
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        "Crowd Density Trend",
                        style: TextStyle(fontWeight: FontWeight.bold),
                      ),
                      const SizedBox(height: 20),
                      Expanded(child: buildLineChart()),
                    ],
                  ),
                ),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Container(
                  padding: const EdgeInsets.all(16),
                  color: Colors.white,
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        "Critical Cameras",
                        style: TextStyle(fontWeight: FontWeight.bold),
                      ),
                      const SizedBox(height: 10),
                      ...criticalCameras
                          .map((e) => buildCriticalCard(e))
                          .toList(),
                    ],
                  ),
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }

  Widget camerasPage() {
  return Container(
    padding: const EdgeInsets.all(20),
    child: GridView.builder(
      itemCount: 6,
      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: 3,
        crossAxisSpacing: 15,
        mainAxisSpacing: 15,
        childAspectRatio: 1.2,
      ),
      itemBuilder: (context, index) {
        return Container(
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(14),
            boxShadow: [
              BoxShadow(
                color: Colors.grey.withOpacity(0.1),
                blurRadius: 10,
              )
            ],
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 10,
                      vertical: 5,
                    ),
                    decoration: BoxDecoration(
                      color: Colors.green.withOpacity(0.15),
                      borderRadius: BorderRadius.circular(20),
                    ),
                    child: const Text(
                      "LIVE",
                      style: TextStyle(
                        color: Colors.green,
                        fontWeight: FontWeight.bold,
                        fontSize: 12,
                      ),
                    ),
                  ),
                  const Icon(Icons.videocam, color: Colors.blue),
                ],
              ),

              const SizedBox(height: 15),

              Text(
                "Camera ${index + 1}",
                style: const TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                ),
              ),

              const SizedBox(height: 5),

              const Text(
                "Building Area Monitoring",
                style: TextStyle(color: Colors.grey, fontSize: 12),
              ),

              const Spacer(),

              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  const Text("Risk Level"),
                  Text(
                    "${30 + index * 10}%",
                    style: const TextStyle(
                      color: Colors.red,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ],
              ),

              const SizedBox(height: 6),

              ClipRRect(
                borderRadius: BorderRadius.circular(10),
                child: LinearProgressIndicator(
                  value: (30 + index * 10) / 100,
                  minHeight: 8,
                  backgroundColor: Colors.grey.shade200,
                  valueColor: const AlwaysStoppedAnimation(Colors.red),
                ),
              ),
            ],
          ),
        );
      },
    ),
  );
}

  Widget liveFeedPage() {
    return const Center(child: Text("📡 Live Feed Page"));
  }

  Widget profilePage() {
    return const Center(child: Text("👤 Profile Page"));
  }

  Widget getCurrentPage() {
    switch (selectedIndex) {
      case 1:
        return camerasPage();
      case 2:
        return liveFeedPage();
      case 3:
        return profilePage();
      default:
        return dashboardContent();
    }
  }

  // ================= MAIN BUILD =================
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF6F7FB),
      body: Row(
        children: [
          buildSidebar(),
          Expanded(
            child: Padding(
              padding: const EdgeInsets.all(20),
              child: getCurrentPage(),
            ),
          ),
        ],
      ),
    );
  }
}
