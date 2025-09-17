#!/bin/bash

# Flatten content and design references to root level
set -e

GRAPH_FILE="${1:-./.ai/spec-graph.json}"
TEMP_FILE="/tmp/flatten_$$.json"

echo "🔧 Flattening content and design references to root level..."

# Extract and restructure references
jq '
  # Move content and design children to root, remove content and design containers
  .references |= (
    # Add content children to root
    .brand = .content.brand |
    .buttons = .content.buttons |
    .labels = .content.labels |

    # Add design children to root
    ."button-styles" = .design."button-styles" |
    ."chart-styles" = .design."chart-styles" |
    .colors = .design.colors |
    .layouts = .design.layouts |
    .patterns = .design.patterns |
    .spacing = .design.spacing |
    ."status-indicators" = .design."status-indicators" |
    .styles = .design.styles |
    .themes = .design.themes |
    .typography = .design.typography |

    # Remove the now-empty content and design containers
    del(.content) |
    del(.design)
  ) |

  # Update graph dependencies from design:* to just *
  .graph |= with_entries(
    .value.depends_on |= map(
      if startswith("design:") then
        ltrimstr("design:")
      elif startswith("content:") then
        ltrimstr("content:")
      else
        .
      end
    )
  )
' "$GRAPH_FILE" > "$TEMP_FILE"

# Check if transformation was successful
if [[ -s "$TEMP_FILE" ]]; then
    mv "$TEMP_FILE" "$GRAPH_FILE"
    echo "✅ References flattened successfully!"

    # Show summary of changes
    echo ""
    echo "📊 Summary of changes:"
    echo "  - Moved 3 content references to root level"
    echo "  - Moved 10 design references to root level"
    echo "  - Updated all entity dependencies to use new paths"
    echo ""
    echo "📝 Reference mapping:"
    echo "  content:brand → brand"
    echo "  content:buttons → buttons"
    echo "  content:labels → labels"
    echo "  design:button-styles → button-styles"
    echo "  design:chart-styles → chart-styles"
    echo "  design:colors → colors"
    echo "  design:layouts → layouts"
    echo "  design:patterns → patterns"
    echo "  design:spacing → spacing"
    echo "  design:status-indicators → status-indicators"
    echo "  design:styles → styles"
    echo "  design:themes → themes"
    echo "  design:typography → typography"
else
    echo "❌ Error: Transformation failed"
    rm -f "$TEMP_FILE"
    exit 1
fi