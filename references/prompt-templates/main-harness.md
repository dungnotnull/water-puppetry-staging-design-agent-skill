# Prompt Template: main harness (water-puppetry-staging-design)

Orchestrate the 5 sub-skills in declared order (see config/skill_registry.yaml).
Run Pre-Flight language detection. After synthesis, apply the 10 quality gates
(U1-U6 + G1-G4) with 2-retry auto-fix. Emit the final report per the Output
Format in skills/main.md. On degradation Level >= 1, prepend the LIMITATION
banner. On Level 4, emit DATA_UNAVAILABLE and do not fabricate.
