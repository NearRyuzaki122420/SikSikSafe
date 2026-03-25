import 'package:flutter/material.dart';

class ZoneCard extends StatelessWidget {
  final dynamic zone;

  const ZoneCard({super.key, required this.zone});

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
    final String risk = zone["risk_level"] ?? "LOW";

    return Card(
      margin: const EdgeInsets.symmetric(vertical: 8),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(14),
      ),
      child: ListTile(
        contentPadding: const EdgeInsets.all(14),
        title: Text(
          zone["zone"] ?? "Unknown Zone",
          style: const TextStyle(fontWeight: FontWeight.bold),
        ),
        subtitle: Padding(
          padding: const EdgeInsets.only(top: 6),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text("People Count: ${zone["person_count"]}"),
              const SizedBox(height: 4),
              Text("Prediction: ${zone["prediction"]}"),
            ],
          ),
        ),
        trailing: Container(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
          decoration: BoxDecoration(
            color: getRiskColor(risk),
            borderRadius: BorderRadius.circular(10),
          ),
          child: Text(
            risk,
            style: const TextStyle(
              color: Colors.white,
              fontWeight: FontWeight.bold,
            ),
          ),
        ),
      ),
    );
  }
}