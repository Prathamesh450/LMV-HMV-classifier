import 'package:flutter/material.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  int _currentNavIndex = 0;
  bool _isDetectionActive = false;

  final List<Map<String, dynamic>> _stats = [
    {'title': 'Violations', 'value': '12', 'icon': Icons.warning_amber},
    {'title': 'Images', 'value': '47', 'icon': Icons.photo_library},
    {'title': 'Alerts', 'value': '3', 'icon': Icons.notifications},
  ];

  void _toggleDetection(bool value) {
    setState(() {
      _isDetectionActive = value;
    });

    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(
          value ? 'Detection system activated' : 'Detection system deactivated',
        ),
        backgroundColor: value ? Colors.green : Colors.orange,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFf8f9fa),
      appBar: _buildAppBar(),
      body: _buildBody(),
      bottomNavigationBar: _buildBottomNavigationBar(),
    );
  }

  AppBar _buildAppBar() {
    return AppBar(
      backgroundColor: Colors.white,
      elevation: 0,
      title: const Text(
        'Security Dashboard',
        style: TextStyle(
          color: Color(0xFF333333),
          fontWeight: FontWeight.bold,
        ),
      ),
      actions: [
        IconButton(
          icon: const Icon(Icons.notifications_none, color: Color(0xFF333333)),
          onPressed: _showNotifications,
        ),
        IconButton(
          icon: const Icon(Icons.account_circle, color: Color(0xFF333333)),
          onPressed: _showProfile,
        ),
      ],
    );
  }

  Widget _buildBody() {
    return Padding(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _buildHeader(),
          const SizedBox(height: 30),
          _buildFeaturesGrid(),
          const SizedBox(height: 20),
          _buildStatsSection(),
        ],
      ),
    );
  }

  Widget _buildHeader() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'Security Controls',
          style: TextStyle(
            fontSize: 24,
            fontWeight: FontWeight.bold,
            color: Color(0xFF333333),
          ),
        ),
        const SizedBox(height: 8),
        Text(
          'Manage your security system',
          style: TextStyle(
            fontSize: 16,
            color: Colors.grey[600],
          ),
        ),
      ],
    );
  }

  Widget _buildFeaturesGrid() {
    return Expanded(
      child: GridView.count(
        crossAxisCount: 2,
        crossAxisSpacing: 20,
        mainAxisSpacing: 20,
        children: [
          _buildFeatureCard(
            title: 'Start Detection',
            icon: Icons.radar,
            isActive: _isDetectionActive,
            hasSwitch: true,
            onToggle: _toggleDetection,
          ),
          _buildFeatureCard(
            title: 'Upload Image',
            icon: Icons.cloud_upload,
            isActive: true,
            hasSwitch: false,
            onToggle: null,
          ),
          _buildFeatureCard(
            title: 'Violation Logs',
            icon: Icons.list_alt,
            isActive: true,
            hasSwitch: false,
            onToggle: null,
          ),
          _buildFeatureCard(
            title: 'Live Feed',
            icon: Icons.videocam,
            isActive: false,
            hasSwitch: false,
            onToggle: null,
          ),
        ],
      ),
    );
  }

  Widget _buildFeatureCard({
    required String title,
    required IconData icon,
    required bool isActive,
    required bool hasSwitch,
    required Function(bool)? onToggle,
  }) {
    return Card(
      elevation: 4,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
      ),
      child: InkWell(
        onTap: hasSwitch && onToggle != null ? () => onToggle(!isActive) : null,
        borderRadius: BorderRadius.circular(16),
        child: Container(
          padding: const EdgeInsets.all(20),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              // Icon
              Container(
                width: 60,
                height: 60,
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    colors: isActive
                        ? [const Color(0xFF667eea), const Color(0xFF764ba2)]
                        : [Colors.grey[300]!, Colors.grey[400]!],
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                  ),
                  shape: BoxShape.circle,
                ),
                child: Icon(
                  icon,
                  color: Colors.white,
                  size: 30,
                ),
              ),
              const SizedBox(height: 16),
              // Title
              Text(
                title,
                style: const TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.w600,
                  color: Color(0xFF333333),
                ),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 8),
              // Status indicator
              if (hasSwitch)
                Transform.scale(
                  scale: 1.2,
                  child: Switch(
                    value: isActive,
                    onChanged: onToggle,
                    activeColor: const Color(0xFF667eea),
                  ),
                )
              else
                Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                  decoration: BoxDecoration(
                    color: isActive ? Colors.green[50] : Colors.grey[200],
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Text(
                    isActive ? 'Active' : 'Inactive',
                    style: TextStyle(
                      color: isActive ? Colors.green : Colors.grey[600],
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildStatsSection() {
    return Card(
      elevation: 4,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
      ),
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              "Today's Stats",
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.bold,
                color: Color(0xFF333333),
              ),
            ),
            const SizedBox(height: 16),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceAround,
              children: _stats.map((stat) => _buildStatItem(stat)).toList(),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildStatItem(Map<String, dynamic> stat) {
    return Column(
      children: [
        Container(
          width: 50,
          height: 50,
          decoration: BoxDecoration(
            color: const Color(0xFF667eea).withOpacity(0.1),
            shape: BoxShape.circle,
          ),
          child: Icon(
            stat['icon'],
            color: const Color(0xFF667eea),
            size: 24,
          ),
        ),
        const SizedBox(height: 8),
        Text(
          stat['value'],
          style: const TextStyle(
            fontSize: 20,
            fontWeight: FontWeight.bold,
            color: Color(0xFF333333),
          ),
        ),
        Text(
          stat['title'],
          style: TextStyle(
            color: Colors.grey[600],
            fontSize: 12,
          ),
        ),
      ],
    );
  }

  BottomNavigationBar _buildBottomNavigationBar() {
    return BottomNavigationBar(
      currentIndex: _currentNavIndex,
      onTap: (index) => setState(() => _currentNavIndex = index),
      type: BottomNavigationBarType.fixed,
      selectedItemColor: const Color(0xFF667eea),
      unselectedItemColor: Colors.grey[600],
      items: const [
        BottomNavigationBarItem(
          icon: Icon(Icons.dashboard),
          label: 'Dashboard',
        ),
        BottomNavigationBarItem(
          icon: Icon(Icons.photo_library),
          label: 'Gallery',
        ),
        BottomNavigationBarItem(
          icon: Icon(Icons.analytics),
          label: 'Analytics',
        ),
        BottomNavigationBarItem(
          icon: Icon(Icons.settings),
          label: 'Settings',
        ),
      ],
    );
  }

  void _showNotifications() {
    // Implement notifications screen
  }

  void _showProfile() {
    // Implement profile screen
  }
}
