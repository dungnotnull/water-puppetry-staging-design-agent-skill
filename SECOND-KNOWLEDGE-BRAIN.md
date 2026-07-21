# SECOND-KNOWLEDGE-BRAIN.md — Skill 167: water-puppetry-staging-design

> **Living Knowledge Base** — updated by `tools/knowledge_updater.py` on a weekly
> schedule. All entries date-stamped; new entries appended at the bottom.
> Evidence hierarchy: Systematic Review > Meta-Analysis > Guideline/RCT > Cohort > Expert Consensus > News.

---

## 1. Core Concepts & Frameworks

### 1.1 Traditional Performing Arts Staging & Production Design — Foundational Methods

#### 1.1.1 Heritage
Vietnamese water puppetry (mua roi nuoc) originated in the Red River Delta circa 11th century CE during the Ly Dynasty. Performances take place on a water surface serving as both stage and concealment mechanism. Puppet mechanisms include:
- **Bucephalous mechanism** — puppets mounted on floating platforms with hidden articulation
- **Rudder/pole mechanism** — long bamboo poles (5-7 m) controlled from behind a bamboo screen (thuy dinh)
- **Buoyancy control** — carved fig wood (Ficus racemosa) treated with son lacquer for water resistance

Traditional performance spaces use waist-deep water (~1 m depth), with operators (phuong) standing behind the screen. The water surface creates natural reflections, masks mechanism lines, and provides acoustic enhancement.

#### 1.1.2 Repertoire
The traditional repertoire includes 30+ standardized scenes (tich tro) across categories:
- **Teu (Chu Teu)** — comic narrator figure, introduces scenes and provides social commentary
- **Agricultural cycle** — rice planting, buffalo fighting, fishing, duck herding
- **Mythological** — dragon dance, phoenix display, unicorn play, the four sacred animals
- **Historical legends** — Le Loi returns the sword, Tran Hung Dao defeats the Mongols
- **Fox hunt / clown scenes** — comedic interludes with acrobatic puppet work

Scene structure typically follows an episodic format: 3-5 minute segments linked by Chu Teu narration with live cheo/chau van musical accompaniment.

#### 1.1.3 Water-Stage Engineering
- **Pool specifications:** minimum 8 m x 8 m surface area, 0.8-1.2 m depth
- **Water treatment:** filtration to maintain clarity for reflection effects; temperature 18-28 deg C for operator comfort
- **Mechanism access:** operators positioned behind split-bamboo screen (2-3 m height) with waist-deep water access
- **Puppet storage:** submerged racks between scenes; quick-change mechanisms under 30 seconds
- **Modern additions:** submerged linear actuators for automated puppet trajectories; waterproof servo control

#### 1.1.4 Lighting & Effects
- **Fixture requirements:** IP65+ (water-jet resistant) minimum; IP67/IP68 preferred for submerged placement
- **Angle strategy:** low-angle (15-30 degrees from water surface) to minimize glare while revealing puppet detail
- **Color temperature:** 3000-4000 K for traditional warmth; 5600 K for modern documentation/video
- **Control protocol:** DMX512-A (ANSI E1.11) with sACN (ANSI E1.31) for networked fixtures
- **Reflection management:** water surface treated as secondary light source; Fresnel equations inform angle selection
- **Effects integration:** low-lying fog/haze (water-glycol), projection mapping on water surface with ripple compensation, LED matrices submerged for underwater illumination
- **Electrical safety near water:** RCD/GFCI protection (30 mA trip, <=40 ms) per IEC 60364-7-702; all circuits isolated; IP-rated junction boxes

#### 1.1.5 Safety & Accessibility
- **Operator safety:** non-slip surfaces at operator station; water quality monitoring (bacterial, chemical); maximum 4-hour continuous operation in water; emergency egress plan
- **Electrical safety:** all circuits within 3 m of water require RCD; annual PAT testing; emergency power cutoff accessible to stage manager
- **Audience safety:** barrier at minimum distance from water edge; fire exits unobstructed; fog density monitored
- **Accessibility:** wheelchair-accessible viewing positions; audio description capability; tactile tour options

### 1.2 Evidence Hierarchy (this domain)
- **Tier 1:** Systematic review / meta-analysis / official standard (ISO, UNESCO ICH, IEC, ESTA/ANSI, PLASA)
- **Tier 2:** Peer-reviewed academic paper / RCT (Theatre Journal, Asian Theatre Journal, Lighting Research & Technology)
- **Tier 3:** Industry report / professional association guideline (OISTAT, USITT, PLASA technical reports)
- **Tier 4:** News / blog / vendor material / practitioner accounts

---

## 2. Key Research Papers & Standards

| Title | Authors | Year | Venue | DOI/URL | Tier |
|------|---------|------|-------|---------|------|
| DMX512-A — Asynchronous Serial Digital Data Transmission Standard for Controlling Lighting Equipment and Accessories | USITT/ESTA | 2004 (rev 2018) | ANSI E1.11 | tsf.esta.org/tsp/documents/published-docs | 1 |
| Entertainment Technology — Recommended Practice for DMX512 | ESTA | 2011 | ANSI E1.11 | tsf.esta.org/tsp/documents/published-docs | 1 |
| Entertainment lighting safety — Electrical safety for stage lighting near water | ESTA/PLASA | current | ANSI E1.x | plasa.org/technical | 1 |
| IEC 60364-7-702: Electrical installations in swimming pools and fountains | IEC | 2010 | International Standard | iec.ch | 1 |
| Water Puppetry of Vietnam: A Living Tradition | Norton, Barley | 2001 | Asian Theatre Journal, 18(1), 135-158 | 10.1353/atj.2001.0013 | 2 |
| Stage Lighting Design: The Art, the Craft, the Life | Pilbrow, Richard | 2008 | Drama Publishers | 10.4324/9780203938630 | 2 |
| The Automated Lighting Programmer's Handbook | Brad Schiller | 2021 | Routledge | 10.4324/9781003155330 | 2 |
| Vietnamese Traditional Water Puppetry: Preservation and Innovation | Pham, Thi Thu Ha | 2019 | International Journal of Heritage Studies, 25(8), 842-856 | 10.1080/13527258.2018.1557251 | 2 |
| Digital Projection Mapping on Water Surfaces for Theatrical Performance | Chen, L., Zhang, W. | 2022 | Entertainment Computing, 41, 100471 | 10.1016/j.entcom.2022.100471 | 2 |
| LED Lighting for Theatrical Applications: Color Rendering and Thermal Management | Uchida, T., et al. | 2020 | Lighting Research & Technology, 52(6), 723-738 | 10.1177/1477153520907425 | 2 |
| Practical DMX: Control Solutions for Stage and Studio | Huntington, John | 2020 | PLASA Media | plasa.org/publications | 3 |
| UNESCO Intangible Cultural Heritage: Vietnamese Water Puppetry Nomination Dossier | Vietnam Ministry of Culture | 2023 | UNESCO ICH | ich.unesco.org | 1 |
| OISTAT Technical Standards for Theatre Design and Technology | OISTAT TC | 2022 | OISTAT | oistat.org | 3 |

Authoritative sources registered:
- Theatre Journal — Johns Hopkins UP
- Performance Research — Taylor & Francis
- Journal of Theatre and Performance Design — Taylor & Francis
- Lighting Research & Technology — SAGE
- Entertainment Computing — Elsevier
- Asian Theatre Journal — Project MUSE
- International Journal of Heritage Studies — Taylor & Francis

---

## 3. State-of-the-Art Methods & Tools

**Current state of the art (2025-2026):**
- LED matrix underwater arrays with individually addressable pixels for water-column illumination
- Projection mapping on water surfaces using real-time ripple-compensation algorithms (OpenCV-based)
- DMX/sACN networked control with Art-Net bridging for legacy fixture integration
- Water-safe robotics for automated puppet articulation (submerged servo actuators, IP68-rated)
- Immersive multimedia integration: spatial audio (Ambisonics), holographic projection on mist screens
- Real-time audience interaction via mobile device synchronized effects
- Heritage documentation via UNESCO ICH digital archiving standards
- Sustainable practices: solar-powered lighting rigs, water recycling systems

**Crawl targets:** Theatre Journal, Lighting Research & Technology, Entertainment Computing, Performance Research, Asian Theatre Journal, IJHS.

---

## 4. Authoritative Data Sources

### 4.1 Domain authoritative sources
- **UNESCO ICH** — Vietnamese water puppetry (ich.unesco.org)
- **OISTAT** — International Association of Theatre Designers and Technicians (oistat.org)
- **USITT** — United States Institute for Theatre Technology (usitt.org)
- **ESTA/ANSI E1** — Stage lighting and control standards
- **PLASA** — Professional Lighting and Sound Association (plasa.org)
- **IEC** — International Electrotechnical Commission (iec.ch)
- **Vietnam National Puppet Theatre** — Primary practitioner organization, Hanoi
- **Thang Long Water Puppet Theatre** — Major performance venue, Hanoi
- **Vietnam Museum of Ethnology** — Heritage research and documentation

### 4.2 Academic & research sources
- **Theatre Journal** — Johns Hopkins University Press
- **Performance Research** — Taylor & Francis
- **Journal of Theatre and Performance Design** — Taylor & Francis
- **Lighting Research & Technology** — SAGE Publications
- **Entertainment Computing** — Elsevier
- **Asian Theatre Journal** — Project MUSE / University of Hawaii Press
- **International Journal of Heritage Studies** — Taylor & Francis
- **TDR: The Drama Review** — MIT Press / Cambridge University Press

---

## 5. Analytical Frameworks

Knowledge categories covered:
- Water-puppetry heritage (origins, puppet mechanisms, water-stage construction)
- Storytelling & folk-tale repertoire (30+ tich tro catalogued)
- Stage & water-engineering (pool specifications, rudder/pole mechanics, buoyancy calculations)
- Lighting design (angle optimization, color temperature selection, water-safe IP-rated fixtures, DMX addressing)
- Physical/visual effects (fog density, projection mapping with ripple compensation, LED matrices, water reflections)
- Safety & accessibility (IEC 60364-7-702 electrical, operator safety protocols, audience egress, accessibility compliance)

**Scenario design framework (sub-core-analysis):**
1. Folk tale selection from repertoire with scene breakdown
2. Puppet mechanism specification per scene (pole/rudder/buoyancy/automated)
3. Water-stage engineering plan (pool dimensions, operator positions, mechanism access)
4. Lighting design (cue sheet with DMX channels, IP-rated fixture placement, angle/color decisions)
5. Effects plan (fog timing, projection content, reflection management)
6. Safety plan (electrical isolation, operator limits, emergency procedures)
7. Multi-scenario production plan (best case / base case / worst case)

**Evidence synthesis framework (sub-advisor):**
1. Conclusion category assignment (Production-Ready / Feasible with Refinements / High-Risk / Inconclusive)
2. Risk identification (min 3) with probability x impact matrix
3. Evidence chain construction (claim -> source -> tier)
4. Mandatory disclosure preceding recommendation
5. Remediation actions with priority ordering

Cross-reference the sub-skill workflows in `skills/*.md` for the domain methods applied at each step. The fixed bookends (requirements -> evidence -> knowledge -> synthesis -> quality gate) are mandatory; the core analysis sub-skills implement the domain-specific methods.

---

## 6. Self-Update Protocol

- **Crawl pipeline:** `tools/knowledge_updater.py`
- **Schedule:** weekly academic (Mondays 08:00) + daily news (07:00); documented in `CLAUDE.md`
- **Dedup:** SHA256 of DOI/URL (case/whitespace-insensitive)
- **Scoring:** composite 0-10 = recency(0.4) + keyword_relevance(0.4) + citation_count(0.2)
- **Crawl targets:** ArXiv (configured categories), Semantic Scholar (keyword clusters), RSS feeds
- **Gap-fill:** `sub-knowledge-updater` flags missing values as crawl queries during analysis
- **Append rule:** new entries appended under Section 7 with date stamp, source tag, and relevance score
- **Rate limiting:** 429 responses handled with Retry-After header parsing + exponential backoff
- **Logging:** structured logging to stdout (colored) and optional file via `--log-file`

---

## 7. Knowledge Update Log

_(Appended automatically by the crawl pipeline. Baseline seeded with the references in Section 2.)_

### 2026-07-10 [crawl] T
- **Authors:** Unknown
- **Year:** 
- **Venue:** Unknown
- **DOI/URL:** https://x.com
- **Relevance Score:** 0.0/10
- **Key Finding:** No abstract available.
