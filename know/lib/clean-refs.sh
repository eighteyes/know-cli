#!/bin/bash

# Clean up references to be granular, specific items
set -e

GRAPH_FILE="${1:-./.ai/spec-graph.json}"
TEMP_FILE="/tmp/clean_$$.json"

echo "🧹 Cleaning up references to be granular, specific items..."

jq '
# Extract specific granular references from nested structures
.references as $refs |

# Create new clean references
.references = {} |

# Keep these as-is (already properly structured)
.references.technical_architecture = $refs.technical_architecture |
.references.libraries = $refs.libraries |
.references.protocols = $refs.protocols |
.references.data_models = $refs.data_models |
.references.acceptance_criteria = $refs.acceptance_criteria |
.references.state_mutations = $refs.state_mutations |
.references.platforms = $refs.platforms |
.references.business_logic = $refs.business_logic |
.references.screens = $refs.screens |
.references.external = $refs.external |
.references.assets = $refs.assets |

# Extract specific labels from buttons structure
.references.labels = {
  "emergency-stop-btn": "EMERGENCY STOP",
  "assign-mission-btn": "Assign Mission",
  "start-teleoperation-btn": "Take Control",
  "approve-btn": "Approve",
  "export-report-btn": "Export Report",
  "cancel-btn": "Cancel",
  "save-draft-btn": "Save Draft",
  "view-details-btn": "View Details",
  "refresh-btn": "Refresh",
  "filter-btn": "Filter",
  "back-btn": "Back",
  "next-btn": "Next",
  "home-btn": "Dashboard",
  "settings-btn": "Settings",
  "help-btn": "Help",
  "status-online": "Online",
  "status-offline": "Offline",
  "status-maintenance": "Maintenance",
  "status-error": "Error",
  "status-operational": "Operational",
  "field-robot-id": "Robot ID",
  "field-battery": "Battery",
  "field-location": "Location",
  "field-mission-status": "Mission Status",
  "field-last-updated": "Last Updated",
  "section-fleet-overview": "Fleet Overview",
  "section-active-missions": "Active Missions",
  "section-maintenance-queue": "Maintenance Queue",
  "section-performance-metrics": "Performance Metrics",
  "section-system-alerts": "System Alerts"
} |

# Create specific style references
.references.styles = {
  "emergency-stop-btn": "background: #FF0000; color: white; font-weight: bold;",
  "primary-btn": "background: #0076FE; color: white;",
  "secondary-btn": "border: 1px solid rgba(255,255,255,0.2); background: transparent;",
  "glass-overlay": "background: rgba(18,18,20,0.80); backdrop-filter: blur(15px);",
  "dark-bg": "background: rgba(18,18,20,1);",
  "status-error": "color: #FF0000;",
  "status-ok": "color: #33E2FF;"
} |

# Keep colors but simplify
.references.colors = {
  "bg-dark": "rgba(18, 18, 20, 1)",
  "glass": "rgba(18, 18, 20, 0.80)",
  "white": "#fff",
  "white-10": "rgba(255, 255, 255, 0.1)",
  "white-20": "rgba(255, 255, 255, 0.2)",
  "error": "#FF0000",
  "primary": "#0076FE",
  "secondary": "#33E2FF",
  "black-50": "rgba(0, 0, 0, 0.5)",
  "black-90": "rgba(0, 0, 0, 0.9)"
} |

# Keep typography values as lists/objects (as requested)
.references.typography = {
  "font-stack": "-apple-system, BlinkMacSystemFont, \"Segoe UI\", Roboto, sans-serif",
  "sizes": ["12px", "14px", "16px", "20px"],
  "weights": [400, 500, 600, 700]
} |

# Keep spacing as simple array
.references.spacing = {
  "micro": ["2px", "4px", "8px", "12px", "16px"],
  "component": ["20px", "24px", "32px"],
  "layout": ["48px", "64px", "80px"]
} |

# Create specific layout references
.references.layouts = {
  "dashboard-grid": "display: grid; grid-template-columns: 250px 1fr; gap: 20px;",
  "card-grid": "display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 16px;",
  "form-stack": "display: flex; flex-direction: column; gap: 16px;",
  "button-row": "display: flex; gap: 12px; justify-content: flex-end;"
} |

# Create specific patterns
.references.patterns = {
  "modal-overlay": "position: fixed; inset: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center;",
  "card-shadow": "box-shadow: 0 4px 6px rgba(0,0,0,0.1);",
  "hover-lift": "transition: transform 0.2s; &:hover { transform: translateY(-2px); }",
  "focus-ring": "outline: 2px solid #0076FE; outline-offset: 2px;"
} |

# Remove the old nested structures we flattened
del(.references.buttons) |
del(.references.brand) |
del(.references["button-styles"]) |
del(.references["chart-styles"]) |
del(.references["status-indicators"]) |
del(.references.themes) |

# Update graph dependencies to remove references to deleted items
.graph |= with_entries(
  .value.depends_on |= map(
    select(
      . != "button-styles:id" and
      . != "chart-styles:id" and
      . != "status-indicators:id" and
      . != "button-styles:name" and
      . != "chart-styles:name" and
      . != "status-indicators:name" and
      . != "button-styles:description" and
      . != "chart-styles:description" and
      . != "status-indicators:description"
    )
  )
)
' "$GRAPH_FILE" > "$TEMP_FILE"

if [[ -s "$TEMP_FILE" ]]; then
    mv "$TEMP_FILE" "$GRAPH_FILE"
    echo "✅ References cleaned up successfully!"
    echo ""
    echo "📊 Summary:"
    echo "  - Created specific label references (emergency-stop-btn, etc.)"
    echo "  - Created specific style references (primary-btn, glass-overlay, etc.)"
    echo "  - Simplified colors to flat key-value pairs"
    echo "  - Kept typography.sizes and spacing as arrays (as requested)"
    echo "  - Created specific layout and pattern references"
    echo "  - Removed generic categories (buttons, button-styles, etc.)"
else
    echo "❌ Error: Transformation failed"
    rm -f "$TEMP_FILE"
    exit 1
fi