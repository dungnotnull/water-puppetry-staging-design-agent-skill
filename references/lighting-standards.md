# Lighting Standards Reference

> Reference for the `validate_ip_rating`, `compute_dmx_address`, and
> `lighting_angle_check` tools and the `sub-core-analysis` skill (Quality Gate G2).
> Tier-1 standards per SECOND-KNOWLEDGE-BRAIN.md Section 2.

## Ingress Protection (IEC 60529)

The IP code is `IP` + two digits: the first digit (0-8) rates solid-particle
ingress; the second digit (0-9) rates liquid ingress.

| Environment | Minimum IP | Notes |
|-------------|-----------|-------|
| Indoor dry (stage) | IP20 | Basic solid protection |
| Near water (<=3 m from pool) | IP65 | Water-jet resistant |
| Splash zone | IP66 | Powerful water jets |
| Submerged fixtures | IP68 | Continuous submersion |

## DMX512-A Addressing (ANSI E1.11)

- One DMX universe = 512 slots, addressed 1-512.
- A fixture consumes `channel_footprint` consecutive slots starting at `start_address`.
- `start_address + channel_footprint - 1` must not exceed 512; otherwise move to the next universe.
- Networked control via sACN (ANSI E1.31); Art-Net bridges legacy fixtures.

## Lighting Angles for Water Stages

Measured as the angle from the water surface (0 = grazing, 90 = top-down).

| Angle range | Zone | Glare risk |
|-------------|------|-----------|
| 0-14 | below-repertoire | low puppet detail; raise to 15-30 |
| 15-30 | optimal | low glare; reveals puppet detail |
| 31-45 | acceptable | moderate glare; use polarizing/flagging |
| 46-60 | high-glare | strong surface reflection; avoid for front audience |
| 61-90 | unsafe-glare | direct audience glare; do not use |

## Color Temperature Guidance

- 3000-4000 K: traditional warmth (heritage scenes).
- 5600 K: modern documentation / video capture.
