# Discover AIM 2.2

This is the public product guide for Agile Iteration Method.

Start here when you want to understand AIM before reading its detailed workflow or reference documentation.

For a two-minute inventory, read the [feature guide](features.md).

## The Short Version

AIM is a structured AI delivery system.

You describe the outcome you want.
AIM turns that outcome into one useful increment at a time, implements it, reviews it, validates it, corrects problems when evidence requires it, and returns meaningful decisions to you.

AIM is designed for real repositories and real delivery constraints:

- quality matters
- goals can drift
- context is limited
- repositories have their own rules
- humans need to understand what they are approving

## Choose Your Path

### I am evaluating AIM

Read [What AIM is and why it is different](what-is-aim.md).

You will learn:

- what AIM solves
- what AIM does not replace
- how quality and correction work
- how AIM respects context and tokens
- where humans remain in control

### I want to start using AIM

Follow the [First-time journey](getting-started.md).

It takes you through:

1. choosing the portable public Agent Skill or adaptive installer
2. repository calibration
3. the first Epic
4. Gate A
5. the first increment
6. acceptance

### I need to choose a setup

Read [Platforms and project agents](platforms-and-adoption.md).

It explains:

- the complete public Agent Skill available through the standard skills CLI
- the adaptive installer with explicit storage and sharing policy
- Codex, Claude, and GitHub Copilot
- project-specific PO, TDO, Dev, and Reviewer specialists
- what stays shared and what uses supplier-native configuration

## Documentation Layers

| Layer | Audience | Purpose |
| --- | --- | --- |
| Product docs | newcomers and evaluators | understand AIM and decide how to adopt it |
| Installation docs | new operators | install and configure AIM safely |
| Workflow docs | active AIM users | understand canonical behavior and operating rules |
| Reference docs | advanced users | investigate cost, adapters, troubleshooting, and detailed models |
| Maintainer docs | AIM contributors | maintain and release AIM itself |

Product docs explain the experience.
Canonical behavior remains under `docs/workflow/`.

## Website Foundation

The content in `docs/product/` is written to be reusable for GitHub Pages, launch material, tutorials, and demonstrations.

Website artwork is staged under:

```text
github-pages/assets/images/
```
