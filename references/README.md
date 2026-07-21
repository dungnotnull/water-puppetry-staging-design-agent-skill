# references/

Domain knowledge, prompt base-templates, and raw context guidelines used for
RAG / agent grounding. Loaded by the sub-skills and the tool registry.

## Contents

| File | Purpose | Used by |
|------|---------|---------|
| `folk-tale-repertoire.md` | 30+ tich tro catalog | `score_folktale_repertoire`, G1 |
| `lighting-standards.md` | IP ratings, DMX512-A, angle zones | `validate_ip_rating`, `compute_dmx_address`, `lighting_angle_check`, G2 |
| `water-stage-engineering.md` | Pool specs, puppet mechanisms, volume math | `estimate_pool_volume` |
| `safety-protocols.md` | IEC 60364-7-702, operator/audience safety | `electrical_safety_check`, G3 |
| `domain-glossary.md` | Bilingual (vi/en) glossary + labels | language detection (U4), Vietnamese output |
| `prompt-templates/` | Base prompt templates per sub-agent | sub-skills (markdown prompt source of truth) |

These references are the human-curated ground truth. The automated crawl
pipeline (`tools/knowledge_updater.py`) appends machine-discovered entries to
SECOND-KNOWLEDGE-BRAIN.md; references here remain the authoritative baseline.
