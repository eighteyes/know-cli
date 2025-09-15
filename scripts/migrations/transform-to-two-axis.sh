#!/bin/bash

# Transform spec-graph.json to two-axis architecture
# This script implements the hierarchy fix plan

set -e

INPUT="spec-graph.json"
OUTPUT="spec-graph-transformed.json"

echo "Starting two-axis architecture transformation..."

# Step 1: Add functionality entities based on features and user needs
echo "Step 1: Creating functionality entities..."

jq '
# Define functionality entities based on features and user needs
.entities.functionality = {
  "robot-control": {
    "id": "robot-control",
    "type": "functionality",
    "name": "Robot Control",
    "description": "Core capability for controlling and operating robots remotely",
    "implements": ["teleoperation", "mission-execution", "emergency-intervention"]
  },
  "fleet-management": {
    "id": "fleet-management",
    "type": "functionality",
    "name": "Fleet Management",
    "description": "Capability to manage multiple robots as a coordinated fleet",
    "implements": ["multi-robot-coordination", "zone-management", "workload-distribution"]
  },
  "telemetry-monitoring": {
    "id": "telemetry-monitoring",
    "type": "functionality",
    "name": "Telemetry Monitoring",
    "description": "Real-time monitoring of robot status and performance data",
    "implements": ["live-tracking", "status-monitoring", "performance-metrics"]
  },
  "maintenance-management": {
    "id": "maintenance-management",
    "type": "functionality",
    "name": "Maintenance Management",
    "description": "Predictive and reactive maintenance capabilities",
    "implements": ["predictive-maintenance", "parts-ordering", "service-scheduling"]
  },
  "analytics-insights": {
    "id": "analytics-insights",
    "type": "functionality",
    "name": "Analytics & Insights",
    "description": "Data analysis and business intelligence capabilities",
    "implements": ["performance-analytics", "operational-insights", "reporting"]
  },
  "mission-planning": {
    "id": "mission-planning",
    "type": "functionality",
    "name": "Mission Planning",
    "description": "Autonomous and manual mission planning capabilities",
    "implements": ["route-optimization", "coverage-planning", "scheduling"]
  },
  "diagnostics": {
    "id": "diagnostics",
    "type": "functionality",
    "name": "Diagnostics",
    "description": "System and device diagnostic capabilities",
    "implements": ["health-monitoring", "troubleshooting", "error-detection"]
  },
  "user-management": {
    "id": "user-management",
    "type": "functionality",
    "name": "User Management",
    "description": "User access control and permissions management",
    "implements": ["authentication", "authorization", "multi-tenancy"]
  }
}
' $INPUT > temp1.json

# Step 2: Add user dependencies on functionalities
echo "Step 2: Adding user-to-functionality dependencies..."

jq '
# Map users to the functionalities they need
.graph["user:owner"].depends_on = [
  "functionality:fleet-management",
  "functionality:analytics-insights",
  "functionality:maintenance-management",
  "functionality:user-management"
] |
.graph["user:operator"].depends_on = [
  "functionality:robot-control",
  "functionality:telemetry-monitoring",
  "functionality:mission-planning"
] |
.graph["user:teleoperator"].depends_on = [
  "functionality:robot-control",
  "functionality:telemetry-monitoring",
  "functionality:diagnostics"
] |
.graph["user:fleet-teleoperator"].depends_on = [
  "functionality:fleet-management",
  "functionality:robot-control",
  "functionality:telemetry-monitoring"
] |
.graph["user:customer-service"].depends_on = [
  "functionality:diagnostics",
  "functionality:maintenance-management"
] |
.graph["user:operations-manager"].depends_on = [
  "functionality:fleet-management",
  "functionality:analytics-insights",
  "functionality:mission-planning"
] |
.graph["user:executive"].depends_on = [
  "functionality:analytics-insights",
  "functionality:user-management"
]
' temp1.json > temp2.json

# Step 3: Add functionality-to-feature dependencies
echo "Step 3: Mapping functionalities to implementing features..."

jq '
# Map functionalities to the features that implement them
.graph["functionality:robot-control"] = {
  "depends_on": [
    "feature:fleet-coordination",
    "feature:mission-automation",
    "requirement:low-latency-teleoperation"
  ]
} |
.graph["functionality:fleet-management"] = {
  "depends_on": [
    "feature:fleet-coordination",
    "requirement:fleet-scalability"
  ]
} |
.graph["functionality:telemetry-monitoring"] = {
  "depends_on": [
    "feature:real-time-telemetry",
    "requirement:near-real-time-data"
  ]
} |
.graph["functionality:maintenance-management"] = {
  "depends_on": [
    "feature:predictive-maintenance",
    "feature:parts-ordering-system",
    "feature:maintenance-alerts"
  ]
} |
.graph["functionality:analytics-insights"] = {
  "depends_on": [
    "feature:analytics",
    "feature:ai-anomaly-detection"
  ]
} |
.graph["functionality:mission-planning"] = {
  "depends_on": [
    "feature:mission-automation",
    "feature:natural-language-interface"
  ]
} |
.graph["functionality:diagnostics"] = {
  "depends_on": [
    "feature:ai-anomaly-detection",
    "requirement:system-reliability"
  ]
} |
.graph["functionality:user-management"] = {
  "depends_on": [
    "requirement:multi-tenant-security"
  ]
}
' temp2.json > temp3.json

# Step 4: Update screen dependencies to go through features instead of users
echo "Step 4: Updating screen dependencies..."

jq '
# Remove user dependencies from screens and add feature dependencies
.graph["screen:fleet-dashboard"] = {
  "depends_on": [
    "feature:real-time-telemetry",
    "feature:fleet-coordination",
    "feature:analytics"
  ]
} |
.graph["screen:mission-control"] = {
  "depends_on": [
    "feature:mission-automation",
    "feature:fleet-coordination"
  ]
} |
.graph["screen:device-diagnostics"] = {
  "depends_on": [
    "feature:ai-anomaly-detection",
    "feature:predictive-maintenance"
  ]
} |
.graph["screen:teleoperation-interface"] = {
  "depends_on": [
    "feature:fleet-coordination",
    "requirement:low-latency-teleoperation",
    "requirement:emergency-response"
  ]
} |
.graph["screen:business-intelligence"] = {
  "depends_on": [
    "feature:analytics"
  ]
}
' temp3.json > temp4.json

# Step 5: Add feature dependencies on components and platforms
echo "Step 5: Adding feature-to-component dependencies..."

jq '
# Map features to their implementing components and platforms
.graph["feature:real-time-telemetry"] = {
  "depends_on": [
    "platform:aws-infrastructure",
    "component:websocket-manager",
    "component:telemetry-processor"
  ]
} |
.graph["feature:fleet-coordination"] = {
  "depends_on": [
    "platform:aws-infrastructure",
    "component:fleet-controller",
    "component:conflict-resolver"
  ]
} |
.graph["feature:predictive-maintenance"] = {
  "depends_on": [
    "component:edge-ai-analyzer",
    "component:maintenance-scheduler"
  ]
} |
.graph["feature:mission-automation"] = {
  "depends_on": [
    "component:path-planner",
    "component:mission-scheduler"
  ]
} |
.graph["feature:analytics"] = {
  "depends_on": [
    "platform:aws-infrastructure",
    "component:data-pipeline",
    "component:report-generator"
  ]
} |
.graph["feature:parts-ordering-system"] = {
  "depends_on": [
    "component:inventory-manager",
    "component:supplier-integration"
  ]
} |
.graph["feature:maintenance-alerts"] = {
  "depends_on": [
    "component:alert-generator",
    "component:notification-service"
  ]
} |
.graph["feature:ai-anomaly-detection"] = {
  "depends_on": [
    "component:ml-detector",
    "component:anomaly-classifier"
  ]
} |
.graph["feature:natural-language-interface"] = {
  "depends_on": [
    "component:nlp-processor",
    "component:command-interpreter"
  ]
}
' temp4.json > temp5.json

# Step 6: Add component entities to complete the hierarchy
echo "Step 6: Adding component entities..."

jq '
# Add component entities
.entities.components = (.entities.components // {}) + {
  "websocket-manager": {
    "id": "websocket-manager",
    "type": "component",
    "name": "WebSocket Manager",
    "description": "Manages real-time websocket connections for telemetry"
  },
  "telemetry-processor": {
    "id": "telemetry-processor",
    "type": "component",
    "name": "Telemetry Processor",
    "description": "Processes incoming telemetry data streams"
  },
  "fleet-controller": {
    "id": "fleet-controller",
    "type": "component",
    "name": "Fleet Controller",
    "description": "Orchestrates fleet-wide operations"
  },
  "conflict-resolver": {
    "id": "conflict-resolver",
    "type": "component",
    "name": "Conflict Resolver",
    "description": "Resolves scheduling and resource conflicts"
  },
  "edge-ai-analyzer": {
    "id": "edge-ai-analyzer",
    "type": "component",
    "name": "Edge AI Analyzer",
    "description": "Performs AI analysis at the edge for maintenance predictions"
  },
  "maintenance-scheduler": {
    "id": "maintenance-scheduler",
    "type": "component",
    "name": "Maintenance Scheduler",
    "description": "Schedules maintenance tasks based on predictions"
  },
  "path-planner": {
    "id": "path-planner",
    "type": "component",
    "name": "Path Planner",
    "description": "Plans optimal paths for missions"
  },
  "mission-scheduler": {
    "id": "mission-scheduler",
    "type": "component",
    "name": "Mission Scheduler",
    "description": "Schedules and queues missions"
  },
  "data-pipeline": {
    "id": "data-pipeline",
    "type": "component",
    "name": "Data Pipeline",
    "description": "ETL pipeline for analytics data"
  },
  "report-generator": {
    "id": "report-generator",
    "type": "component",
    "name": "Report Generator",
    "description": "Generates analytical reports"
  },
  "inventory-manager": {
    "id": "inventory-manager",
    "type": "component",
    "name": "Inventory Manager",
    "description": "Manages parts inventory"
  },
  "supplier-integration": {
    "id": "supplier-integration",
    "type": "component",
    "name": "Supplier Integration",
    "description": "Integrates with supplier APIs"
  },
  "alert-generator": {
    "id": "alert-generator",
    "type": "component",
    "name": "Alert Generator",
    "description": "Generates maintenance and operational alerts"
  },
  "notification-service": {
    "id": "notification-service",
    "type": "component",
    "name": "Notification Service",
    "description": "Delivers notifications to users"
  },
  "ml-detector": {
    "id": "ml-detector",
    "type": "component",
    "name": "ML Detector",
    "description": "Machine learning anomaly detector"
  },
  "anomaly-classifier": {
    "id": "anomaly-classifier",
    "type": "component",
    "name": "Anomaly Classifier",
    "description": "Classifies detected anomalies"
  },
  "nlp-processor": {
    "id": "nlp-processor",
    "type": "component",
    "name": "NLP Processor",
    "description": "Natural language processing engine"
  },
  "command-interpreter": {
    "id": "command-interpreter",
    "type": "component",
    "name": "Command Interpreter",
    "description": "Interprets natural language commands"
  }
}
' temp5.json > $OUTPUT

# Clean up temp files
rm -f temp1.json temp2.json temp3.json temp4.json temp5.json

echo "Transformation complete! Output saved to $OUTPUT"

# Validate the result
echo -e "\nValidating transformed graph..."
echo "Checking for circular dependencies..."
./scripts/json-graph-query.sh cycles || true

echo -e "\nGraph statistics:"
./scripts/json-graph-query.sh stats || true