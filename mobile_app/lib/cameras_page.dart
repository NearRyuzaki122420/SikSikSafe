import 'package:flutter/material.dart';

class CamerasPage extends StatefulWidget {
  const CamerasPage({super.key});

  @override
  State<CamerasPage> createState() => _CamerasPageState();
}

class _CamerasPageState extends State<CamerasPage> {
  String selectedZone = "All Zones";

  final List<String> zones = ["All Zones", "Zone A", "Zone B", "Zone C"];

  final List<Map<String, dynamic>> cameras = [
    {
      "title": "Main Entrance",
      "zone": "Zone A",
      "image": "https://images.unsplash.com/photo-1500",
      "status": "MEDIUM",
      "crowd": 72,
    },
    {
      "title": "Cafeteria",
      "zone": "Zone B",
      "image": "https://images.unsplash.com/photo-1501",
      "status": "LOW",
      "crowd": 45,
    },
    {
      "title": "Auditorium Entrance",
      "zone": "Zone C",
      "image": "https://images.unsplash.com/photo-1502",
      "status": "HIGH",
      "crowd": 89,
    },
    {
      "title": "Parking Lot A",
      "zone": "Zone A",
      "image": "https://images.unsplash.com/photo-1503",
      "status": "LOW",
      "crowd": 34,
    },
    {
      "title": "Corridor 2F",
      "zone": "Zone A",
      "image": null,
      "status": "MAINTENANCE",
      "crowd": 0,
    },
    {
      "title": "Emergency Exit B",
      "zone": "Zone C",
      "image": "https://images.unsplash.com/photo-1504",
      "status": "CRITICAL",
      "crowd": 95,
    },
  ];

  Color getRiskColor(String status) {
    switch (status) {
      case "HIGH":
        return Colors.orange;
      case "MEDIUM":
        return Colors.amber;
      case "LOW":
        return Colors.green;
      case "CRITICAL":
        return Colors.red;
      default:
        return Colors.grey;
    }
  }

  List<Map<String, dynamic>> get filteredCameras {
    if (selectedZone == "All Zones") return cameras;
    return cameras.where((c) => c["zone"] == selectedZone).toList();
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(20),
      color: const Color(0xFFF6F7FB),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // HEADER
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: const [
                  Text(
                    "Camera Management",
                    style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold),
                  ),
                  SizedBox(height: 4),
                  Text(
                    "Configure cameras and monitoring zones",
                    style: TextStyle(color: Colors.grey),
                  ),
                ],
              ),

              ElevatedButton.icon(
                onPressed: () {},
                icon: const Icon(Icons.add),
                label: const Text("Add Camera"),
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.purple,
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(
                    horizontal: 16,
                    vertical: 12,
                  ),
                ),
              ),
            ],
          ),

          const SizedBox(height: 20),

          // ZONE FILTER
          Row(
            children: zones.map((z) {
              final active = selectedZone == z;
              return Padding(
                padding: const EdgeInsets.only(right: 10),
                child: ChoiceChip(
                  label: Text(z),
                  selected: active,
                  onSelected: (_) {
                    setState(() {
                      selectedZone = z;
                    });
                  },
                  selectedColor: Colors.purple,
                  labelStyle: TextStyle(
                    color: active ? Colors.white : Colors.black,
                  ),
                ),
              );
            }).toList(),
          ),

          const SizedBox(height: 20),

          // CAMERA GRID
          Expanded(
            child: GridView.builder(
              itemCount: filteredCameras.length,
              gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                crossAxisCount: 3,
                crossAxisSpacing: 16,
                mainAxisSpacing: 16,
                childAspectRatio: 1.2,
              ),
              itemBuilder: (context, index) {
                final cam = filteredCameras[index];

                return Container(
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(14),
                    boxShadow: [
                      BoxShadow(
                        color: Colors.grey.withOpacity(0.1),
                        blurRadius: 10,
                      ),
                    ],
                  ),
                  child: Column(
                    children: [
                      // IMAGE AREA
                      Expanded(
                        flex: 3,
                        child: Stack(
                          children: [
                            Container(
                              width: double.infinity,
                              decoration: BoxDecoration(
                                color: Colors.grey.shade200,
                                borderRadius: const BorderRadius.only(
                                  topLeft: Radius.circular(14),
                                  topRight: Radius.circular(14),
                                ),
                              ),
                              child: cam["status"] == "MAINTENANCE"
                                  ? const Center(
                                      child: Icon(
                                        Icons.warning,
                                        color: Colors.orange,
                                        size: 40,
                                      ),
                                    )
                                  : const Icon(
                                      Icons.videocam,
                                      size: 50,
                                      color: Colors.grey,
                                    ),
                            ),

                            // STATUS BADGE
                            Positioned(
                              top: 10,
                              right: 10,
                              child: Container(
                                padding: const EdgeInsets.symmetric(
                                  horizontal: 8,
                                  vertical: 4,
                                ),
                                decoration: BoxDecoration(
                                  color: getRiskColor(
                                    cam["status"],
                                  ).withOpacity(0.2),
                                  borderRadius: BorderRadius.circular(20),
                                ),
                                child: Text(
                                  cam["status"],
                                  style: TextStyle(
                                    fontSize: 10,
                                    color: getRiskColor(cam["status"]),
                                    fontWeight: FontWeight.bold,
                                  ),
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),

                      // INFO
                      Expanded(
                        flex: 2,
                        child: Padding(
                          padding: const EdgeInsets.all(10),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                cam["title"],
                                style: const TextStyle(
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                              Text(
                                cam["zone"],
                                style: const TextStyle(
                                  color: Colors.grey,
                                  fontSize: 12,
                                ),
                              ),

                              const Spacer(),

                              Row(
                                mainAxisAlignment:
                                    MainAxisAlignment.spaceBetween,
                                children: [
                                  const Text(
                                    "Crowd Density",
                                    style: TextStyle(fontSize: 12),
                                  ),
                                  Text(
                                    "${cam["crowd"]}%",
                                    style: TextStyle(
                                      color: getRiskColor(cam["status"]),
                                      fontWeight: FontWeight.bold,
                                    ),
                                  ),
                                ],
                              ),

                              const SizedBox(height: 6),

                              LinearProgressIndicator(
                                value: cam["crowd"] / 100,
                                minHeight: 6,
                                backgroundColor: Colors.grey.shade200,
                                valueColor: AlwaysStoppedAnimation(
                                  getRiskColor(cam["status"]),
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                    ],
                  ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}
