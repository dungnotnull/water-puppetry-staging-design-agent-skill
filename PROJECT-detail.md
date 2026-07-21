# PROJECT-detail.md — Skill 167: water-puppetry-staging-design

## Executive Summary

`water-puppetry-staging-design` is a professional-grade harness for Claude Code targeting the
**Traditional Performing Arts Staging & Production Design** domain. It transforms Claude into a domain-expert that delivers
structured, evidence-backed outputs by combining real-time data aggregation,
recognized domain methods, and academic research into a single orchestrated
workflow ending in a risk/limitation-disclosed recommendation.

---

## Problem Statement

Practitioners in this domain face three structural gaps:
1. **Data fragmentation**: authoritative data scattered across sources.
2. **Methodology gaps**: most advice lacks systematic, evidence-graded methods.
3. **No self-improvement**: static tools don't learn from new research.

This skill addresses all three via real-time aggregation, professional
frameworks, and a continuously-updated knowledge crawl pipeline.

---

## Target Users & Use Cases

| User | Trigger Example | Skill Response |
|------|----------------|----------------|
| Practitioner | "Analyze Traditional Performing Arts Staging & Production Design case X" | Full evidenced report |
| Researcher | "What methods apply to Y?" | Method-grounded guidance with citations |
| Decision-maker | "Assess risk/feasibility of Z" | Risk-disclosed assessment with scenarios |
| Learner | "Explain method M in this domain" | Educational framing with evidence |

---

## Harness Architecture

```
USER INPUT
    │
    ▼
[main.md — water-puppetry-staging-design]
    │
    ├─► sub-gather-requirements.md  → Clarify the object of analysis, constraints, timeframe, available inputs, target audience, and language before any data fetching.
    ├─► sub-evidence-collector.md  → Fetch authoritative real-time and reference data for the object: current status/parameters, authoritative documents/standards, and recent developments from domain and academic sources.
    ├─► sub-core-analysis.md  → Analyze and design a water-puppetry scenario integrating traditional folk storytelling with modern lighting and physical effects, grounded in heritage and safety.
    ├─► sub-knowledge-updater.md  → Query SECOND-KNOWLEDGE-BRAIN.md for authoritative academic and professional evidence; surface citations with tier labels and flag gaps for the crawl pipeline.
    ├─► sub-advisor.md  → Synthesize all prior analysis into a risk-disclosed conclusion with a full evidence chain and recommended actions.

    └─► [QUALITY GATE — main.md]
            ✓ Claims cited to sources
            ✓ Disclosure included
            ✓ Evidence hierarchy respected
            ✓ Output formatted per template
```

---

## Full Sub-Skill Catalog

### 1. `sub-gather-requirements.md`
- **Purpose:** Clarify the object of analysis, constraints, timeframe, available inputs, target audience, and language before any data fetching.
- **Role:** intake specialist for a Traditional Performing Arts Staging & Production Design engagement
- **Inputs:** Raw user message + any provided materials/inputs.
- **Outputs:** Structured requirements: {object, scope, timeframe, available_inputs, target_audience, language, analysis_type}.
- **Tools:** - Conversation only (no external tools)
- **Quality Gate:** At least one object of analysis confirmed before proceeding.

### 2. `sub-evidence-collector.md`
- **Purpose:** Fetch authoritative real-time and reference data for the object: current status/parameters, authoritative documents/standards, and recent developments from domain and academic sources.
- **Role:** Traditional Performing Arts Staging & Production Design data librarian
- **Inputs:** Requirements object from Step 1.
- **Outputs:** Evidence bundle: {current_data, authoritative_docs, recent_news, reference_benchmarks} with source + date per item.
- **Tools:** - WebSearch, WebFetch (domain + academic sources)
- Read (SECOND-KNOWLEDGE-BRAIN.md for cached benchmarks)
- **Quality Gate:** At least current data + 1 authoritative document retrieved, or a limitation flag if unavailable.

### 3. `sub-core-analysis.md`
- **Purpose:** Analyze and design a water-puppetry scenario integrating traditional folk storytelling with modern lighting and physical effects, grounded in heritage and safety.
- **Role:** traditional-performing-arts production designer
- **Inputs:** Requested theme/folk tale, venue, available equipment, audience, language.
- **Outputs:** Scenario structure + puppet/stage engineering + lighting plan + effects + safety plan + scenarios.
- **Tools:** - Read (SECOND-KNOWLEDGE-BRAIN.md)
- WebSearch, WebFetch (UNESCO ICH, OISTAT, USITT, PLASA)
- Reasoning / design
- **Quality Gate:** Scenario grounded in a documented folk-tale repertoire; lighting specifies IP-rated/water-safe fixtures per IEC/ESTA; safety plan present before effects.

### 4. `sub-knowledge-updater.md`
- **Purpose:** Query SECOND-KNOWLEDGE-BRAIN.md for authoritative academic and professional evidence; surface citations with tier labels and flag gaps for the crawl pipeline.
- **Role:** research librarian for Traditional Performing Arts Staging & Production Design
- **Inputs:** Topic keywords from the current analysis.
- **Outputs:** 3-5 knowledge-base citations with Tier labels + flagged gaps.
- **Tools:** - Read (SECOND-KNOWLEDGE-BRAIN.md)
- WebSearch (gap-fill, max 2 queries)
- **Quality Gate:** At least 1 academic/authoritative source surfaced; coverage rating provided.

### 5. `sub-advisor.md`
- **Purpose:** Synthesize all prior analysis into a risk-disclosed conclusion with a full evidence chain and recommended actions.
- **Role:** senior Traditional Performing Arts Staging & Production Design advisor
- **Inputs:** Core analysis scorecard + evidence bundle + knowledge-base evidence.
- **Outputs:** Conclusion (one of N declared categories) + scenarios + key risks + evidence chain + remediation + mandatory disclosure.
- **Tools:** - Reasoning / synthesis
- Skill('sub-knowledge-updater') optional
- **Quality Gate:** Conclusion is exactly one of: Production-Ready Design / Feasible with Refinements / High-Risk Production / Inconclusive; disclosure appears before the conclusion.


---

## Skill File Format Specification

```markdown
---
name: {skill-name}
description: {one-line summary}
---
## Role & Persona
## Workflow (Harness Flow)
## Sub-skills Available   (main.md only)
## Tools
## Output Format
## Quality Gates
```

---

## E2E Execution Flow

```
1. User invokes /water-puppetry-staging-design [query]
2. main.md → sub-gather-requirements → structured requirements
3. sub-evidence-collector → data bundle
4. core analysis sub-skills → scorecard / signal set
5. sub-knowledge-updater → academic evidence entries
6. sub-advisor/synthesizer → final draft
7. main.md Quality Gate → verify, auto-fix, deliver
```

**Error handling:** primary sources fail → fallback chain → knowledge base →
explicit limitation flag; never silently proceed with stale data.

---

## SECOND-KNOWLEDGE-BRAIN Integration

- **Sources crawled:** academic databases + domain RSS + standards docs
- **Crawl config:** `KNOWLEDGE_CONFIG` in `tools/knowledge_updater.py`
- **Dedup:** SHA256 of DOI/URL
- **Scoring:** recency + keyword relevance + citation count

---

## Quality Gates Definition

Universal gates U1–U6 (see library SKILL-STANDARD.md) plus the domain gates
defined in `skills/main.md`: G1, G2, G3, G4

---

## Test Scenarios

See `tests/test-scenarios.md` for 5+ concrete scenario tests.

---

## Key Design Decisions

1. Domain sub-skills kept separate (distinct methods/data).
2. Authoritative domain sources as primary; global fallback secondary.
3. Disclosure enforced at the quality-gate level, not optional.
4. SECOND-KNOWLEDGE-BRAIN as living memory updated by crawl pipeline.
5. Graceful degradation to knowledge base with explicit limitation flags.

---

## Idea (Vietnamese)

> Tạo skill tự động hóa quy trình phân tích và đề xuất kịch bản múa rối nước truyền thống kết hợp công nghệ ánh sáng và hiệu ứng vật lý hiện đại, dựa trên các tích trò cổ và liên tục cập nhật xu hướng nghệ thuật trình diễn đa phương tiện trên thế giới.
