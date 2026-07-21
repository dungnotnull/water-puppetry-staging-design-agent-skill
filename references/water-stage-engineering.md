# Water-Stage Engineering Reference

> Reference for the `estimate_pool_volume` tool and the `sub-core-analysis`
> skill. Grounded in SECOND-KNOWLEDGE-BRAIN.md Section 1.1.3.

## Standard Repertoire Pool

- Minimum surface: 8 m x 8 m.
- Depth: 0.8-1.2 m (waist-deep for operators / phu+o+ng).
- Water temperature: 18-28 deg C for operator comfort.
- Filtration required to maintain clarity for reflection effects.

## Puppet Mechanisms

1. **Rudder/pole mechanism** - long bamboo poles (5-7 m) controlled from behind
   the split-bamboo screen (thu.y ddi`nh).
2. **Bucephalous mechanism** - puppets mounted on floating platforms with hidden
   articulation.
3. **Buoyancy control** - carved fig wood (Ficus racemosa) treated with son
   lacquer for water resistance.
4. **Modern automated** - submerged linear actuators / waterproof servos (IP68).

## Volume & Mass Calculations

For a rectangular pool:
- Volume (m^3) = length_m * width_m * depth_m
- Volume (L) = volume_m^3 * 1000
- Mass (kg) ~= volume_m^3 * 1000 (water density ~1000 kg/m^3)
- Surface area (m^2) = length_m * width_m

Structural loading must account for the water mass plus puppet/operator dynamic
loads; engage a structural engineer for non-standard venues.
