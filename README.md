# KNOW CLI
An opinionated graph knowledgebase for product driven software development.

Intended primarily for automated access.

## Why? 
spec.md is a brittle approach to defining projects for LLM understanding. For months, I've used, built and rebuilt approaches to making spec files and I'm never truly happy with the results. They are brittle, prone to hallucination, resistant to change, and never internally consistent. Despite how "production-ready" and "Perfect!" they are. 

Introducing **SPEC GRAPHS**

## Spec Graphs solve for brittle specs. 
Every piece of information lives in one place, and is referenced by others. Functionally, this approach uses a simple graph with a single relationship type "depends_on" to map the connection between a User, their Objectives, into how they Act on software Components. 

These components serve as the link to a second graph in the same vein, one which describes the software architecture and how components link together. In this way, we can map from a user objective and determine all the software pieces involved in making that happen. It's an exciting vision.

Especially when you add AI, reinforced with tooling, to help you make these graphs. 

## Pure Alpha
This is a work in progress. There are two primary intents with `know`:
1) Provide a surface area for LLMs to understand the product and codebase without conducting token-wasting, repetitive manual analysis. 
2) Output current spec files for "traditional" spec-driven development.
 
Generally speaking, this is not designed for human use, as the ergonomics are somewhere between `tar` and `aws-cli`. That being said, a skill is provided for use `.claude/skills/know-tool/marketplace.json`, give it a spin. 
