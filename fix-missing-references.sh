#!/bin/bash

KNOWLEDGE_MAP="knowledge-map-structured.json"

echo "🔧 Adding missing content_library entries..."

# Add missing content_library entries
jq '.content_library += {
  "ai-preservation-req": "All existing AI capabilities must be preserved during v1 consolidation",
  "mobile-offline-req": "Mobile interface must support 30-minute offline operation with essential functions", 
  "multi-tenant-req": "System must support company-segmented data access with strict isolation"
}' "$KNOWLEDGE_MAP" > temp.json && mv temp.json "$KNOWLEDGE_MAP"

echo "🔧 Adding missing screen entities..."

# Add missing screens
jq '.entities.screens += {
  "robot-control": {
    "id": "robot-control",
    "type": "screen", 
    "name": "Robot Control",
    "description_ref": "robot-control-desc",
    "route": "/robot-control",
    "layout": "main-layout",
    "priority": "P0",
    "components": ["robot-control-panel", "status-indicator"],
    "features": ["robot-control", "manual-override"],
    "user_access": ["operator"],
    "requirements": ["teleoperation-latency"]
  },
  "diagnostics-dashboard": {
    "id": "diagnostics-dashboard", 
    "type": "screen",
    "name": "Diagnostics Dashboard",
    "description_ref": "diagnostics-dashboard-desc",
    "route": "/diagnostics",
    "layout": "main-layout", 
    "priority": "P1",
    "components": ["diagnostics-panel", "alert-panel"],
    "features": ["device-diagnostics", "health-monitoring"],
    "user_access": ["customer-service", "operations-manager"],
    "requirements": ["real-time-updates"]
  },
  "fleet-coordination": {
    "id": "fleet-coordination",
    "type": "screen",
    "name": "Fleet Coordination", 
    "description_ref": "fleet-coordination-desc",
    "route": "/fleet-coordination",
    "layout": "main-layout",
    "priority": "P0",
    "components": ["fleet-status-map", "zone-manager", "coordination-panel"],
    "features": ["fleet-coordination", "zone-management"],
    "user_access": ["fleet-teleoperator"],
    "requirements": ["real-time-updates"],
    "version_introduced": "v4"
  }
}' "$KNOWLEDGE_MAP" > temp.json && mv temp.json "$KNOWLEDGE_MAP"

echo "🔧 Adding missing component entities..."

# Add missing components
jq '.entities.components += {
  "quick-actions": {
    "id": "quick-actions",
    "type": "component",
    "name": "Quick Actions Panel", 
    "description_ref": "quick-actions-desc",
    "framework": "react",
    "file_path": "src/components/QuickActions/index.tsx",
    "used_by_screens": ["dashboard"],
    "used_by_features": ["emergency-controls", "quick-operations"]
  },
  "robot-assignment-panel": {
    "id": "robot-assignment-panel",
    "type": "component", 
    "name": "Robot Assignment Panel",
    "description_ref": "robot-assignment-panel-desc",
    "framework": "react", 
    "file_path": "src/components/RobotAssignmentPanel/index.tsx",
    "used_by_screens": ["fleet-management"],
    "used_by_features": ["robot-assignment"],
    "uses_models": ["robot", "user", "assignment"]
  },
  "status-indicator": {
    "id": "status-indicator",
    "type": "component",
    "name": "Status Indicator",
    "description_ref": "status-indicator-desc", 
    "framework": "react",
    "file_path": "src/components/StatusIndicator/index.tsx",
    "used_by_screens": ["dashboard", "robot-control"],
    "used_by_features": ["real-time-status"],
    "uses_models": ["robot", "status"]
  }
}' "$KNOWLEDGE_MAP" > temp.json && mv temp.json "$KNOWLEDGE_MAP"

echo "🔧 Adding missing feature entities..."

# Add missing features  
jq '.entities.features += {
  "robot-control": {
    "id": "robot-control",
    "type": "feature",
    "name": "Robot Control",
    "description_ref": "robot-control-desc", 
    "priority": "P0",
    "version_introduced": "v1",
    "components": ["robot-control-panel", "status-indicator"],
    "screens": ["robot-control", "mission-control"],
    "requirements": ["teleoperation-latency"],
    "models": ["robot", "command"]
  },
  "device-health-monitoring": {
    "id": "device-health-monitoring", 
    "type": "feature",
    "name": "Device Health Monitoring",
    "description_ref": "device-health-monitoring-desc",
    "priority": "P1",
    "version_introduced": "v1", 
    "components": ["diagnostics-panel", "alert-panel"],
    "screens": ["diagnostics-dashboard"],
    "requirements": ["real-time-updates"],
    "models": ["robot", "health-data", "telemetry"]
  },
  "alert-system": {
    "id": "alert-system",
    "type": "feature", 
    "name": "Alert System",
    "description_ref": "alert-system-desc",
    "priority": "P0",
    "version_introduced": "v1",
    "components": ["alert-panel"],
    "screens": ["dashboard", "diagnostics-dashboard"], 
    "requirements": ["real-time-updates"],
    "models": ["alert", "notification"]
  }
}' "$KNOWLEDGE_MAP" > temp.json && mv temp.json "$KNOWLEDGE_MAP"

echo "🔧 Adding missing model entities..."

# Add missing models
jq '.entities.models += {
  "status": {
    "id": "status",
    "type": "model",
    "name": "Robot Status",
    "description_ref": "status-model-desc", 
    "database_table": "robot_status",
    "fields": {
      "robot_id": {"type": "uuid", "foreign_key": "robots.id"},
      "status": {"type": "enum", "values": ["active", "maintenance", "offline", "error"]},
      "battery_level": {"type": "number"},
      "last_seen": {"type": "timestamp"},
      "location": {"type": "coordinates"}
    },
    "used_by_features": ["real-time-status"],
    "used_by_components": ["fleet-status-map", "status-indicator"]
  },
  "alert": {
    "id": "alert",
    "type": "model", 
    "name": "Alert",
    "description_ref": "alert-model-desc",
    "database_table": "alerts",
    "fields": {
      "id": {"type": "uuid", "required": true},
      "robot_id": {"type": "uuid", "foreign_key": "robots.id"},
      "alert_type": {"type": "enum", "values": ["maintenance", "emergency", "warning"]},
      "severity": {"type": "enum", "values": ["critical", "warning", "info"]},
      "message": {"type": "string", "required": true},
      "acknowledged": {"type": "boolean", "default": false}
    },
    "used_by_features": ["alert-system", "predictive-maintenance"],
    "used_by_components": ["alert-panel"]
  }
}' "$KNOWLEDGE_MAP" > temp.json && mv temp.json "$KNOWLEDGE_MAP"

echo "🔧 Adding missing content_library descriptions..."

# Add missing descriptions
jq '.content_library += {
  "robot-control-desc": "Direct robot operation interface with movement controls, mission execution, and emergency functions",
  "diagnostics-dashboard-desc": "Technical diagnostic interface with component health analysis and maintenance tools",
  "fleet-coordination-desc": "Advanced fleet coordination interface for managing multiple robots across zones",
  "quick-actions-desc": "Quick access panel for common operations and emergency functions",
  "robot-assignment-panel-desc": "Interface for owners to assign robots to operators with permission management",
  "status-indicator-desc": "Visual indicator showing current robot status with color coding and alerts",
  "device-health-monitoring-desc": "Continuous monitoring of robot component health with predictive maintenance alerts",
  "status-model-desc": "Real-time status data for robots including location, battery, and operational state",
  "robot-control-feat-desc": "Core robot control capabilities including movement, mission control, and emergency functions"
}' "$KNOWLEDGE_MAP" > temp.json && mv temp.json "$KNOWLEDGE_MAP"

echo "✅ Missing references have been added!"