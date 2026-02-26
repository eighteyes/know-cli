"""Shared color theme for graph visualizations."""

# Entity type → visual properties
ENTITY_COLORS = {
    # Spec graph types
    "project":    {"fill": "#e3f2fd", "stroke": "#1565c0", "rich_style": "bold blue",        "text_color": "#000"},
    "user":       {"fill": "#e8f5e9", "stroke": "#388e3c", "rich_style": "bold green",       "text_color": "#000"},
    "objective":  {"fill": "#fff3e0", "stroke": "#e65100", "rich_style": "bold dark_orange",  "text_color": "#000"},
    "feature":    {"fill": "#e1f5ff", "stroke": "#0288d1", "rich_style": "bold cyan",         "text_color": "#000"},
    "action":     {"fill": "#fff9c4", "stroke": "#f57f17", "rich_style": "bold yellow",       "text_color": "#000"},
    "component":  {"fill": "#f3e5f5", "stroke": "#7b1fa2", "rich_style": "bold magenta",      "text_color": "#000"},
    "operation":  {"fill": "#f1f8e9", "stroke": "#558b2f", "rich_style": "bold bright_green",  "text_color": "#000"},
    # Code graph types
    "module":     {"fill": "#e8eaf6", "stroke": "#283593", "rich_style": "bold blue",         "text_color": "#000"},
    "package":    {"fill": "#fce4ec", "stroke": "#c62828", "rich_style": "bold red",           "text_color": "#000"},
    "class":      {"fill": "#f3e5f5", "stroke": "#6a1b9a", "rich_style": "bold magenta",      "text_color": "#000"},
    "function":   {"fill": "#e0f7fa", "stroke": "#00838f", "rich_style": "bold bright_cyan",   "text_color": "#000"},
    "interface":  {"fill": "#e0f2f1", "stroke": "#00695c", "rich_style": "bold bright_green",  "text_color": "#000"},
    "layer":      {"fill": "#efebe9", "stroke": "#4e342e", "rich_style": "bold bright_black",  "text_color": "#000"},
    "namespace":  {"fill": "#fbe9e7", "stroke": "#bf360c", "rich_style": "bold dark_orange",   "text_color": "#000"},
    "external-dep": {"fill": "#eceff1", "stroke": "#546e7a", "rich_style": "dim",             "text_color": "#000"},
    # Fallback for references
    "_reference": {"fill": "#f5f5f5", "stroke": "#9e9e9e", "rich_style": "dim",               "text_color": "#666"},
}

# Graphviz node shapes by entity type
DOT_SHAPES = {
    "project": "house", "user": "oval", "objective": "hexagon",
    "feature": "box", "action": "parallelogram", "component": "component",
    "operation": "cds",
    "module": "box3d", "package": "folder", "class": "record",
    "function": "ellipse", "interface": "diamond", "layer": "tab",
    "namespace": "folder", "_reference": "note",
}


def get_color(entity_type):
    """Return color dict for an entity type, falling back to _reference."""
    return ENTITY_COLORS.get(entity_type, ENTITY_COLORS["_reference"])


def get_node_shape_dot(entity_type):
    """Return Graphviz node shape for an entity type."""
    return DOT_SHAPES.get(entity_type, "box")
