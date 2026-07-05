import 'package:flutter/material.dart';

class Sidebar extends StatelessWidget {
  final int selectedIndex;
  final Function(int) onTap;

  const Sidebar({
    super.key,
    required this.selectedIndex,
    required this.onTap,
  });

  Widget item({
    required IconData icon,
    required String title,
    required bool active,
    required VoidCallback onPressed,
  }) {
    return InkWell(
      onTap: onPressed,
      borderRadius: BorderRadius.circular(10),
      child: Container(
        margin: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: active ? const Color(0xFFF3ECFF) : Colors.transparent,
          borderRadius: BorderRadius.circular(10),
        ),
        child: Row(
          children: [
            Icon(
              icon,
              color: active ? Colors.purple : Colors.grey,
            ),
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

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 240,
      color: Colors.white,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const SizedBox(height: 30),

          const Center(
            child: Text(
              "SikSikSafe Admin",
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.bold,
              ),
            ),
          ),

          const SizedBox(height: 30),

          item(
            icon: Icons.dashboard,
            title: "Dashboard",
            active: selectedIndex == 0,
            onPressed: () => onTap(0),
          ),

          item(
            icon: Icons.camera_alt,
            title: "Cameras",
            active: selectedIndex == 1,
            onPressed: () => onTap(1),
          ),

          item(
            icon: Icons.rss_feed,
            title: "Live Feed",
            active: selectedIndex == 2,
            onPressed: () => onTap(2),
          ),

          item(
            icon: Icons.person,
            title: "Profile",
            active: selectedIndex == 3,
            onPressed: () => onTap(3),
          ),

          const Spacer(),

          const Padding(
            padding: EdgeInsets.all(20),
            child: Row(
              children: [
                Icon(Icons.logout, color: Colors.red),
                SizedBox(width: 10),
                Text(
                  "Logout",
                  style: TextStyle(color: Colors.red),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}