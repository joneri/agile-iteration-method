# Discover AIM

This is the public product guide for Agile Iteration Method.

Start here when you want to understand AIM before reading its detailed workflow or reference documentation.

For a two-minute inventory, read the [feature guide](features.md).

To see User Stories from different Epics move through planning, implementation,
review, validation and acceptance, run `/aim ui` from chat and explore [AIM
UI Beta](aim-ui.md).

For advice reused during planning, review and diagnosis, read
[shared learning during delivery](../workflow/reflection.md).

## The Short Version

AIM is a structured AI delivery system. **Ship** is the default: finish the
complete agreed product before final acceptance. Choose **Loop** for useful
Done Increments with recurring owner feedback. Both use the same engineering,
review and verification discipline.

Use **Graph engineering** to connect the goal, dependencies, assignments and
proof. **AIM UI** is the local control room: follow the current Increment,
explore User Stories and inspect Graph. An explicitly delegated agent owner can
provide feedback within a human-approved mandate; Epic closure remains human-owned.

You describe the outcome you want.
PO owns Epics and product priority. TDO creates and owns Stories and criteria, then plans a coherent increment that can cross Epic boundaries. AIM checks the first working core before expanding it, reviews and validates the delivered behavior, and returns acceptance to you. The working result is an increment; a Sprint is an optional timebox.

Quality goals are agreed before implementation. A separate reviewer challenges
the core with an independent example; runnable user journeys and retained raw
results support the final decision. Project knowledge, compact checkpoints and
relevant shared lessons help later sessions reuse work that still applies.

The [retained Enigma M3 results](../features/aim-enigma-evaluation.md) compare
GPT-6 Luna with AIM (**96.5/100** in the latest assessment) and
[GPT-6 Luna without AIM](../features/aim-3.2-enigma-m3-case.md) (**49.8/100**).
The earlier AIM result was **93.5/100**. The model, high reasoning effort,
brief and scoring weights match; the runs took place on different dates under
different delivery conditions. This is a historical comparison, not a fresh
paired experiment or a general quality or cost guarantee. The latest version
of AIM includes later changes that have not received this application score;
the assessed native delivery remained unfinished.

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
2. describing the desired product intent
3. automatic preparation of missing or stale knowledge and role skills
4. Epics, User Stories and AIM UI
5. the first prioritized delivery selection
6. Story acceptance and separate Epic closure

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
