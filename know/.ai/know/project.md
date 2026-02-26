# Know-CLI Project Overview

## Purpose
Product knowledge graph CLI for AI-driven software development. Replaces flat spec files with structured dependency graphs linking product intent (spec-graph) to code implementation (code-graph).

## Users & Core Objectives
- **solo-developer**: Solo technical leads doing rapid prototyping with AI assistance
- **ai-agent**: AI agents consuming graph context for code generation  
- **know-maintainer**: Contributors maintaining the tool

See spec-graph for full user→objective→feature chains.

## Key Features (10 total)
- graph-management, graph-validation, spec-generation
- feature-lifecycle, graph-visualization, search-discovery
- cross-graph-linking, code-analysis, impact-analysis
- **git-pr-graph-compare** (compare graphs between git refs)

## Architecture
**4 Packages**: know-core, know-advanced, know-viz, know-cli
**11 Modules**: graph, cache, entities, dependencies, validation, generators, diff, contract-manager, feature-tracker, semantic-search, cli

**Tech Stack**: Python 3.8+, Click, NetworkX, Rich, Pydantic, PyYAML

## Graphs
- **Spec Graph**: 3 users, 9 objectives, 10 features ✓
- **Code Graph**: 4 packages, 11 modules, 6 external deps ✓

Use `/know:list`, `/know:connect`, `/know:build` for interactive workflows.
