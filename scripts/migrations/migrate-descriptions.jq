#!/usr/bin/env jq -f

# Extract all references for easier access
.references as $refs |

# Process entities - replace description_ref with actual description
.entities |= with_entries(
  .value |= with_entries(
    .value |= (
      # If entity has description_ref, replace with actual description
      if .description_ref and $refs.descriptions[.description_ref] then
        . + {description: $refs.descriptions[.description_ref]} | del(.description_ref)
      # If entity already has a description field, keep it
      elif .description then
        .
      # For entities with description in references based on ID pattern
      elif $refs.descriptions[.id + "-desc"] then
        . + {description: $refs.descriptions[.id + "-desc"]}
      elif $refs.descriptions[.name + "-desc"] then
        . + {description: $refs.descriptions[.name + "-desc"]}
      else
        .
      end
    )
  )
) |

# Also update graph nodes with resolved_description if they reference descriptions
.graph |= with_entries(
  .value |= (
    if .resolved_description and (.resolved_description | endswith("-desc")) and $refs.descriptions[.resolved_description] then
      . + {resolved_description: $refs.descriptions[.resolved_description]}
    else
      .
    end
  )
) |

# Remove the references section entirely
del(.references)