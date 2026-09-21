# Biological Rules for a 3D Lymph Node Vaccine Simulator

## A literature-based manual for cell agents, spatial constraints, and state transitions

Version 1.0 • 21 September 2026

Prepared for Helder Nakaya

**Scope:** an adult human draining lymph node responding to vaccination, with explicit distinctions between human observations, experimental mechanisms established in other systems, and proposed simulation rules. The main scenario is a T-dependent response to protein antigens delivered by an inactivated or live-attenuated vaccine. This is a biological specification, not a calibrated predictive model or a clinical decision tool.

**Deliverables:** this manual defines cell identities, tissue compartments, signaling relationships, event prerequisites, prohibited transitions, quantitative evidence anchors, and validation requirements. Stable identifiers are provided for later conversion into JSON. Numerical parameters without a defensible measurement are left unresolved rather than presented as biological constants.

# 1. How to use this manual

The simulator should answer two different questions: what can a cell do in its present biological context, and how often does that event occur? The first can often be constrained from mechanism. The second usually requires a particular vaccine, tissue, species, assay, and time course. A reliable model must keep these questions separate.

A lymph node is not a container of interchangeable agents. Its stromal networks, vascular entry points, lymphatic routes, and antigen-retaining surfaces create different encounter opportunities. Human immune atlases identify many relevant populations, but an atlas alone does not establish transition rates or prove that one cluster becomes another. [R01–R03]

## 1.1 Evidence labels

**D — Direct mechanism:** a perturbation or functional experiment supports the stated biological relationship. The experimental system must still be specified.

**Q — Quantitative observation:** a time, proportion, distribution, or rate was measured in a defined experiment. It is not automatically a human parameter.

**A — Association or anatomical observation:** expression, localization, or population structure supports an annotation but does not establish causality.

**T — Transfer assumption:** a mechanism or number is being transferred between species, organs, vaccines, or experimental conditions.

**P — Proposed implementation:** a modeling choice introduced here. It may be useful and biologically consistent without having been measured in vivo.

A rule can carry several labels. For example, CXCR4-dependent germinal-center organization has experimental support, whereas a particular mathematical chemotaxis coefficient remains P until fitted. [R18]

## 1.2 Constraint classes

**Invariant:** a restriction imposed within the declared healthy-vaccination model, such as preserving B-cell versus T-cell lineage or preventing a committed apoptotic cell from dividing. It does not claim that experimental reprogramming or malignancy is impossible.

**Mechanistic gate:** a condition needed for a particular modeled route. Cognate peptide–HLA recognition is required for that TCR-dependent interaction, but alternative activation routes must be represented separately rather than silently excluded.

**Soft bias:** a tendency that changes an event rate or movement preference, not a compulsory fate. Follicular localization and helper-cell polarization belong here.

**Unresolved parameter:** a value that cannot yet be justified for the target human setting. It must be fitted, experimentally estimated, or varied in sensitivity analysis.

## 1.3 Default experimental boundary

The reference configuration is a peripheral draining node after parenteral vaccination in an immunocompetent adult. Age, prior infection, prior vaccination, HLA genotype, immune suppression, and route are configuration variables, not noise to ignore. An axillary node after intramuscular injection is not interchangeable with a tonsil or a mesenteric node.

Use the inactivated influenza study as direct evidence that human vaccine-specific germinal centers can contain both recalled and less-mutated B-cell clones. Use live-attenuated yellow-fever studies for platform-specific innate and systemic responses. Neither provides a complete human spatial kinetic model. [R39, R41–R43]

# 2. Spatial ontology and physical restrictions

## 2.1 Compartments

The compartment identifiers below are a proposed computational ontology (P). Their anatomical rationale comes from stromal organization, trafficking experiments, and human tissue observations. A zone is a region with characteristic interactions, not a box that changes cell identity. [R01–R07, R17–R20]

| ID | Region | Permitted interpretation and constraints |
|---|---|---|
| LN-S01 | Afferent lymphatic boundary | Entry route for lymph-borne antigen and tissue-derived migratory APCs. Represent the injection site as an upstream source, not as the whole LN. |
| LN-S02 | Subcapsular sinus | Lymph-facing space with antigen capture and relay. Separate the lumen, its lining, and the adjacent follicular tissue. |
| LN-S03 | Interfollicular region | Interface where incoming material and APCs can encounter lymphocytes. It is not equivalent to the entire T zone. |
| LN-S04 | Paracortex / T-cell zone | FRC-supported region for naive T-cell scanning and DC-mediated priming. Include connections to HEVs and follicular borders. |
| LN-S05 | B-cell follicle | CXCL13-associated B-cell territory with an FDC network. A primary follicle need not contain a GC. |
| LN-S06 | T–B border | Interface supporting cognate encounters between antigen-activated B cells and helper T cells. Defined spatially, not as a new cell lineage. |
| LN-S07 | GC dark-zone neighborhood | Region enriched for proliferating GC B cells and CXCL12-associated support. Develops only when a GC exists. |
| LN-S08 | GC light-zone neighborhood | Region supporting antigen acquisition from FDCs, Tfh encounters, selection, and removal of dying cells. |
| LN-S09 | Medullary cords | Candidate niche for antibody-secreting cells and associated stromal/myeloid support. |
| LN-S10 | Medullary / efferent lymphatic pathway | Exit route for lymph and eligible emigrating cells. Crossing requires an anatomical outlet. |
| LN-S11 | Blood vessel / HEV boundary | Controlled blood-to-node recruitment interface. The blood lumen is not freely accessible tissue. |
| LN-S12 | Capsule, trabeculae, and stromal matrix | Structural boundaries and migration scaffold. Tissue deformation can be modeled; unrestricted passage through a capsule cannot. |
| EXT-S01 | Blood reservoir | Supplies recirculating cells and receives downstream outputs. Not an unlimited local source. |
| EXT-S02 | Injection-site / peripheral-tissue reservoir | Supplies antigen, inflammatory signals, and emigrating APCs according to vaccine and route. |
| EXT-S03 | Bone-marrow / distal-tissue reservoir | Optional destination for plasma cells and effectors. Do not claim to simulate its survival niches unless modeled explicitly. |

**Topology rules (P):** afferent material enters LN-S02, with antigen-specific routing onward; HEV recruitment enters the paracortical tissue; activated B cells move between follicle and T–B border; GC B cells circulate between connected dark- and light-zone neighborhoods; exit occurs through connected lymphatic paths. Geometry and motility must make these routes possible without teleportation.

**Soft boundaries:** follicles, paracortex, and GC zones have graded interfaces. Use chemokine fields, receptor responsiveness, matrix access, and local contacts to generate enrichment. Do not kill a B cell merely because it crosses a follicular boundary. CXCR4/CXCR5 perturbations should change organization, not rename a lineage. [R17, R18]

**Physical boundaries:** vessel walls and capsule are barriers with defined crossing mechanisms. Stromal deformation may permit node expansion; dendritic-cell interactions with the FRC network can alter tissue tension in mice. A fixed-volume model should declare that it omits this response. [R03, R05]

## 2.2 Geometry, scale, and observation

**P:** define all positions in micrometers and all times in a single base unit, preferably minutes. Specify whether the simulated domain is a full node, one follicle with adjacent paracortex, or a representative tissue patch. A small visualization with a few hundred agents is not automatically a whole-node model.

**P:** record whether an agent represents one cell or a weighted population. Mixing individual-cell contact rules with large agent weights changes competition and encounter rates. If one agent represents many cells, branching, cytokine secretion, and antigen consumption require an explicit coarse-graining scheme.

**P:** do not prescribe universal compartment percentages or cell counts. Obtain them from the target tissue or treat them as calibration parameters. Section area, dissociated-cell frequency, and FNA frequency are different measurements. The observation model must reproduce the sampling process before comparison with data.

# 3. Cell identities and reversible states

Each entry has a stable identifier. Markers are examples for annotation, not sufficient diagnostic panels or mandatory Boolean gates. Human and mouse names are not interchangeable. The registry combines human immune data with functional studies and mouse stromal maps; species transfers are identified below. [R01, R02, R07, R15]

A cell record should preserve **lineage**, **functional state**, **activation history**, **location**, **cell-cycle phase**, and **viability** independently. A cycling Tfh remains a CD4 T cell. A migrating cDC2 remains cDC2. A B cell moving from dark to light zone does not become a different lineage.

## 3.1 B-cell lineage

### B-01 — Naive mature B cell

**Identity/location:** typically CD19/MS4A1-positive, with surface IgM and IgD; principally follicular. **Capabilities:** native-antigen recognition through its BCR, uptake, processing, and peptide–MHC-II display. **Allowed route:** B-02 after a qualified activation event; otherwise continued recirculation, survival, or death. **Constraint:** no vaccine-specific plasmablast program from proximity to antigen alone. A selected antigen must bind the modeled BCR; a T-dependent route also needs appropriate help. [R02, R13, R17, R28]

### B-02 — Antigen-activated, pre-GC B cell

**Location:** follicular perimeter, T–B border, and extrafollicular response sites. **State:** recent BCR engagement, processed antigen, and altered migration responsiveness. **Allowed routes:** extrafollicular plasmablast, GC-entry program, memory-like output where supported, or death. **Constraint:** GC entry is not compulsory. Class-switch recombination can begin before GC formation; never require GC membership as a universal CSR prerequisite. [R13, R17, R28, R33]

### B-03 — GC-entry / founder state

**Location:** an emerging GC within a follicle. **State:** sustained B-cell activation and a GC program, including BCL6-associated features. **Allowed routes:** proliferative GC state or loss from the response. **P:** encode entry as a timed program requiring a viable cell, suitable interactions, and an available follicular niche. Do not create a mature dark/light-zone architecture on the same frame as first BCR binding. [R21, R29, R39]

### B-04 — GC dark-zone-biased state

**Identity:** GC B cell with a proliferative program and relatively strong CXCR4 responsiveness. **Capabilities:** cell-cycle progression and AID-dependent diversification in the appropriate program. **Allowed routes:** daughter GC cells, light-zone-biased state, or apoptosis. **Constraint:** cycling and mutation must be scheduled processes; neither can be granted repeatedly by an unrestricted action choice. A damaging BCR mutation can reduce subsequent viability or selection. [R18, R29–R31, R34]

### B-05 — GC light-zone-biased state

**Location/function:** FDC-rich selection neighborhood. A cell acquires native antigen, processes it, and competes for cognate Tfh help. **Allowed routes:** selected state, continued search, output differentiation, or apoptosis. **Constraint:** affinity alone is not a deterministic survival command; antigen accessibility, receptor integrity, presentation, and helper availability also matter. [R11, R25, R29, R31, R52]

### B-06 — Positively selected GC B cell

**Definition:** a transient event-associated state, not a new lineage. **Allowed routes:** renewed proliferative program, memory differentiation, or antibody-secreting differentiation. **P:** represent help as a finite, decaying license that can change division propensity and cycling kinetics. Do not infer an unlimited division budget from one Tfh contact. [R29, R30, R35]

### B-07 — Memory B cell

**Identity:** antigen-experienced B cell; may be class-switched or unswitched, and CD27 is not a universal gate. **Location:** local or recirculating compartments, depending on subtype. **Allowed routes:** quiescence, recall activation, plasmablast differentiation, and context-dependent GC participation. **Constraint:** memory is not synonymous with constitutive antibody secretion. Initialize repertoire and prior antigen exposure explicitly. [R02, R27, R35, R39]

### B-08 — Plasmablast

**Identity:** differentiating antibody-secreting B-lineage cell, often proliferative, with IRF4/PRDM1 and secretory-program features. **Location:** extrafollicular and medullary response sites, with possible export. **Allowed routes:** finite proliferation while licensed, plasma-cell maturation, egress, or death. **Constraint:** antibody specificity derives from the cell's immunoglobulin sequence; the agent cannot invent a newly requested specificity. [R26, R27, R39, R40]

### B-09 — Plasma cell

**Identity:** mature antibody-secreting state with a sustained secretory program; CD138 and BCMA can support annotation but are not universal binary definitions. **Default:** no cell-cycle re-entry in the healthy mature-plasma module (P). **Allowed routes:** survival, secretion, migration where appropriate, or death. Local persistence does not prove bone-marrow longevity. BCMA must not be implemented as the only possible survival input: mouse studies disagree on its indispensability. [R37, R38]

## 3.2 T-cell lineage

### T-01 — Naive CD4 T cell

**Location:** paracortex after entry, with CCR7-associated recirculation. **Capabilities:** scanning APCs for cognate peptide–MHC-II. **Allowed routes:** activation, continued migration, egress, or death. **Constraint:** neither soluble intact protein nor high MHC-II abundance is sufficient to establish a cognate TCR interaction. Costimulation and signaling history affect productive priming. [R02, R12, R16, R19]

### T-02 — Activated CD4 T cell

**State:** antigen-experienced activation with time-dependent changes in retention, proliferation readiness, and helper programs. **Allowed routes:** Tfh-related, other helper-effector, or memory programs; failed expansion and apoptosis remain possible. **Constraint:** one cytokine does not deterministically assign a permanent lineage. Cell-cycle eligibility is separate from cytokine secretion. [R16, R20–R22, R36, R49, R51]

### T-03 — Pre-Tfh / border helper state

**Location:** between the T zone and follicular interface. **Function:** supports and is shaped by cognate B-cell encounters. **Allowed routes:** follicular Tfh development, other activated states, or loss. **Constraint:** expression of CXCR5 or BCL6 alone does not prove mature GC helper function. Human IL-12 can promote Tfh-like properties in culture, so a rigid mouse-only cytokine rule is inappropriate. [R21, R49]

### T-04 — Germinal-center Tfh

**Identity:** CD4 T cell with follicular localization and helper capacity, commonly associated with CXCR5, PD-1, ICOS, and BCL6. **Capabilities:** cognate B-cell recognition, contact-dependent help, and context-dependent IL-21/IL-4 production. **Allowed routes:** persistence, proliferation under suitable conditions, state change, memory-associated output, or death. **Constraint:** help is delivered through actual local encounters; it is not a GC-wide reward broadcast. [R21, R25, R29, R30]

### T-05 — Th1-like effector state

**Function:** a CD4 program associated with TBX21 and IFN-γ competence. Human IL-12 experiments support increased IFN-γ-producing capacity, but secretion still depends on stimulation and history. **Location:** T-zone/interfollicular regions and eventual tissue-directed egress. **Constraint:** live attenuation does not force every responding CD4 cell into this state. [R41, R51]

### T-06 — Th2-like effector state

**Function:** a CD4 program associated with GATA3 and type-2 cytokine competence. IL-4/STAT6 signaling has experimental support, including mouse loss-of-function evidence. **Constraint:** an inactivated vaccine is not automatically a Th2 perturbation. Implement the program only with platform- and species-appropriate evidence; do not transfer mouse immunoglobulin subclass rules to humans. [R02, R47]

### T-07 — Th17-like effector state

**Function:** a CD4 program associated with RORC and IL-17 competence. **Constraint:** human differentiation depends on the experimental starting population and cytokine context. Human studies have reported different requirements for TGF-β. Do not encode either culture result as a universal in vivo switch. This module requires separate calibration. [R48, R50]

### T-08 — Regulatory T cell

**Identity:** regulatory CD4 population with FOXP3-associated features; activated conventional human T cells can complicate marker-only calls. **Function:** contact-dependent and cytokine-dependent regulation. **Constraint:** suppression is an effect on specific partner interactions or signals, not automatic killing. CTLA-4-mediated removal of CD80/CD86 is a mechanistically supported option. [R02, R24]

### T-09 — Follicular regulatory T cell

**Identity:** follicularly localized regulatory CD4 state, associated with FOXP3 and BCL6. **Location:** follicular/GC environments. **Function:** regulation of GC reactions. **P:** allow development from a qualified regulatory precursor and modulate local helper access or costimulation. Do not convert a Tfh into a Tfr merely because IL-10 is detected. [R23, R24]

### T-10 — Memory CD4 T cell

**Identity:** antigen-experienced CD4 cell with recall potential. **Location:** depends on recirculating versus tissue-associated program. **Allowed routes:** maintenance, recall proliferation and effector/helper states, or death. **P:** model subtype and prior clonotype-specific experience separately; a single generic “memory multiplier” cannot represent all recall behavior. [R02]

### T-11 — Naive CD8 T cell

**Function:** recognizes cognate peptide–MHC-I. **Allowed routes:** priming by suitable APCs, continued recirculation, or loss. **Constraint:** no activation by peptide–MHC-II through the conventional CD8 pathway. Cross-presentation permits some exogenous antigens to enter MHC-I presentation; the APC need not itself be infected. [R14, R16]

### T-12 — Effector / memory CD8 states

**Function:** activated CD8 cells can proliferate, produce cytokines, and acquire cytotoxic capacity; memory cells require a separate persistence/recall state. **P:** cytotoxic killing requires a susceptible local target, cognate recognition for the antigen-specific route, and an execution delay. Do not kill every vaccine-antigen-containing cell. An inactivated vaccine can support cross-priming without productive infection. [R02, R14, R36, R41]

## 3.3 Antigen-presenting and innate cells

### D-01 — Conventional dendritic cell type 1

**Annotation:** XCR1/CLEC9A-associated cDC1; human CD141 can contribute to identification. **Function:** antigen presentation, with experimentally supported cross-presentation capacity. **Constraint:** cDC1 is not exclusively an MHC-I presenter; CD4 presentation is not forbidden. Separate lineage from residence, migration, maturation, and antigen load. [R09, R14, R15]

### D-02 — Conventional dendritic cell type 2

**Annotation:** CD1C/FCER1A-associated cDC2, with tissue heterogeneity. **Function:** uptake, MHC-II presentation, costimulation, and context-dependent cytokines. **Constraint:** do not classify every HLA-DRA-high inflammatory myeloid cell as cDC2. Monocyte-derived populations and human DC3-like populations require separate definitions when included. [R02, R09, R15]

### D-03 — Plasmacytoid dendritic cell

**Annotation:** CLEC4C/IL3RA/TCF4-associated human pDC identity. **Function:** type-I-interferon production under appropriate sensing conditions; antigen-presentation behavior is context dependent. **Constraint:** pDC presence does not force IFN release, and vaccine identity does not imply that all pDCs receive ligand. [R15, R41]

### D-04 — Migratory / mature DC state tag

**Definition:** an attribute applied to a qualified DC population, not a separate lineage. CCR7-dependent migration links peripheral tissue sensing to LN entry. **Allowed outcomes:** arrival, antigen presentation, altered secretion, and eventual loss. **Constraint:** migration must start upstream and consume travel time. Resident DCs may present arriving antigen before every tissue DC arrives. [R08, R09]

### D-05 — Inflammatory monocyte-derived APC / DC3-like optional populations

Keep these as distinct configurable populations rather than synonyms. Recruitment, differentiation, and presentation capacity depend on the inflammatory setting. **P:** a blood monocyte may enter an explicitly parameterized inflammatory-APC program; it must not spontaneously become an FDC or a conventional DC solely from an expression score. Human blood DC classifications do not supply human LN differentiation rates. [R02, R15]

### M-01 — Subcapsular sinus macrophage

**Location:** sinus-associated interface, commonly CD169-associated in experimental systems. **Function:** capture and relay of lymph-borne material; immune-complex relay can involve noncognate B cells. **Constraint:** antigen capture is not equivalent to destruction of all native epitopes or to universal naive T-cell priming. Species and cargo dependence must be retained. [R10]

### M-02 — Medullary macrophage

**Location:** medullary sinus/cord neighborhoods, according to subtype. **Function:** clearance and local myeloid support. **P:** model phagocytic capacity and cargo degradation separately from antigen presentation. Do not assign every macrophage the same cytokine profile or migration program. The exact human subtype composition requires tissue-specific annotation. [R01, R02]

### M-03 — Tingible body macrophage

**Location/function:** removal of apoptotic B-cell material in and around GCs. Mouse imaging supports local activation and clearance by pre-positioned cells and processes. **P:** maintain a finite capture/processing queue; clearance can be slower than death generation. Corpses should not disappear instantly or continue secreting as live cells. [R31, R32]

### I-01 — Recruited monocyte

**Function:** context-dependent inflammatory, phagocytic, and APC-related activity. **P:** use a blood-source recruitment rate and an explicit differentiation graph. No indefinite local self-replenishment is assumed. Human monocyte markers and DC-related signatures overlap; classification uncertainty should remain visible. [R02, R15]

### I-02 — Neutrophil

**Function/location:** a conditional inflammatory participant, not a compulsory major population in every vaccine-draining node. **P:** mature neutrophils do not proliferate in the default model; recruitment, antimicrobial activity, death, and clearance are separate events. NET release or tissue damage must remain disabled unless a vaccine-specific module is supported. [R02]

### I-03 — Natural killer cell

**Identity:** innate cytotoxic lymphocyte, distinct from CD8 T cells. **P:** cytokine responsiveness, inhibitory/activating receptor balance, contact requirements, and killing capacity must be represented separately. Do not assign a rearranged vaccine-specific TCR or allow spontaneous conversion to a T-cell lineage. Include only mechanisms needed by the chosen vaccine setting. [R02]

## 3.4 Stromal and vascular cells

### S-01 — T-zone fibroblastic reticular cell

**Location:** paracortical reticular network. **Function:** structural guidance and homeostatic support, including IL-7/chemokine-associated functions. **Constraint:** a fibroblast does not become an APC-equivalent cDC because it expresses an HLA-II transcript. **P:** movement is limited by the attached network; remodeling is slower than lymphocyte motility. [R01, R03–R05]

### S-02 — Marginal reticular cell

**Location:** follicular/sinus-adjacent stromal region. **Function:** niche support and chemokine production according to tissue. Human tonsil data identified BAFF expression in MRCs rather than FDCs. **Constraint:** BAFF source must be species/tissue-specific, not assigned to all FDCs by convention. [R01, R07]

### S-03 — Follicular dendritic cell

**Identity:** mesenchymal stromal cell, not a conventional dendritic cell. **Function:** retention and recycling of native immune complexes for B-cell access. **Location:** follicular network, including GC light-zone niches. Human FDCs can show HLA-DR and immunoregulatory features; this does not establish a default naive-CD4-priming role. **Constraint:** no acute cDC-to-FDC conversion. [R06, R07, R11]

### S-04 — Dark-zone reticular support cell

**Location/function:** CXCL12-associated GC support neighborhood. **P:** represent as a spatial source/scaffold linked to GC organization, using mouse-to-human transfer labels when necessary. Do not assume that every FDC and every dark-zone stromal cell are one homogeneous population. [R01, R18]

### S-05 — Medullary fibroblast

**Location:** medullary support structures. **Function:** matrix and niche-associated support, with subtype heterogeneity. **P:** possible survival-ligand production needs human tissue evidence; do not fill missing ligand measurements with arbitrary constitutive secretion. [R01, R45]

### S-06 — Lymphatic endothelial cell

**Location:** sinus and lymphatic boundaries. **Function:** barrier, routing, and stromal signaling context. **P:** model entry/exit gates and lymph flow separately from lymphocyte movement. Treat antigen archiving and tolerogenic presentation as optional extensions requiring their own evidence, not baseline assumptions. [R01–R03, R19]

### S-07 — Blood endothelial / HEV cell

**Location:** blood-to-LN interface. **Function:** regulated recruitment rather than unlimited cell creation. **P:** distinguish ordinary vasculature from specialized HEV segments and couple entry to reservoir composition, adhesion competence, and available crossing sites. [R03]

### S-08 — Perivascular and capsular structural cells

**Identity:** pericytes, vascular-support cells, and capsular fibroblasts must retain their own identities if represented as agents. Mouse lineage studies support perivascular origins of FDCs, but do not justify instant conversion of arbitrary adult pericytes during vaccination. **P:** structural remodeling can be an explicit optional program. [R01, R06]

## 3.5 Conditional populations and omissions

**O-01 mast cell; O-02 eosinophil; O-03 basophil; O-04 ILC1/ILC2/ILC3; O-05 γδ T cell; O-06 MAIT cell; O-07 invariant NKT cell; O-08 Langerhans cell.** These are distinct populations, not a generic “other immune cell.” Their abundance, location, and relevance depend on organ, route, and perturbation. Include them as annotated populations only when supported by the target data; do not invent response rules to populate the scene. [R02, R08, R15]

**P:** in the first calibrated vaccine model, these populations may be passive background or explicitly absent. Record that choice. Langerhans-cell migration is relevant to a skin-associated scenario, not an automatic consequence of an intramuscular injection. Nonclassical antigen-recognition modules must not be approximated by conventional peptide–MHC-II matching.

# 4. Vaccination as an upstream perturbation

## 4.1 Inputs that must be specified

**P:** a vaccine input record must include platform, antigen identities, dose units, route, administration time, formulation/adjuvant, antigen accessibility, degradation/retention behavior, and prior immune history. Dose injected into muscle is not dose arriving at a node. Separate delivery into the draining lymphatic system from the amount retained at the injection site.

For each antigen, distinguish native B-cell epitopes, possible processed T-cell peptides, peptide–HLA compatibility, and any physically linked carrier or particle. A multivalent vaccine requires separate antigen identities and may produce competing responses. Pre-existing antibodies and memory clonotypes must be initialized before vaccination rather than manufactured after an unexpectedly strong response. [R13, R39, R52]

**P:** the antigen source may be a measured time-varying boundary condition rather than explicit injection-site agents. This is acceptable if declared. A node-only simulation should not imply that it has predicted injection-site replication, muscle inflammation, or systemic reactogenicity.

## 4.2 Inactivated vaccine

An inactivated vaccine supplies nonreplicating antigen. Antigen can nevertheless persist through formulation-dependent delivery, tissue retention, or immune-complex storage. Native material can be available to B cells, while internalized proteins can supply MHC-II peptides. Some exogenous antigen can also enter cross-presentation pathways; lack of replication is not a universal prohibition on CD8 priming. [R11, R14, R39]

**Hard input restriction (P):** the source term for replication of the inactivated organism is zero. Movement between reservoirs, epitope unmasking, recycling, and fragmentation cannot be counted as new organism production. Innate stimulation must depend on the actual formulation and sensing mechanism; do not assume that all inactivated vaccines use the same adjuvant or induce the same helper profile.

## 4.3 Live-attenuated vaccine

A live-attenuated vaccine can generate antigen through biologically restricted replication, but the permissive tissue, cell type, kinetics, and immune-control mechanisms are organism-specific. Yellow-fever 17D experiments support activation of multiple DC subsets and several innate-sensing pathways; those findings do not mean that every live vaccine uses all the same receptors or infects every LN cell. [R41, R42]

**P:** represent replication only in explicitly permissive compartments or cells, with source depletion, immune containment, and calibrated kinetics. A generic “live = stronger” multiplier is not a mechanistic model. The node can receive additional antigen from upstream tissue without itself containing productively infected cells. An infection state must therefore be distinct from antigen carriage.

## 4.4 Overlapping phases, not a compulsory timetable

**Delivery and innate response:** soluble/particulate material reaches draining pathways; resident capture and presentation can overlap with later arrival of migratory DCs. The relative timing depends on route and cargo. [R08–R11]

**Priming and early expansion:** qualified T cells scan APCs, accumulate stimulation, alter retention, and eventually enter the cell cycle. B cells recognize native antigen and seek help. Extrafollicular antibody production can begin without every responding B cell entering a GC. [R13, R16, R20, R28, R39]

**GC establishment and selection:** some clones enter a follicular GC program, expand, diversify, acquire antigen, and compete for help. Their fate depends on repeated local interactions rather than vaccine time alone. [R18, R29–R35]

**Output and contraction:** memory and antibody-secreting outputs coexist with cell loss. A GC need not terminate on a fixed day. Human influenza-vaccine GCs were detected one week after immunization and persisted to nine weeks in some sampled participants. Human mRNA-vaccine studies provide another persistence example, not a directly interchangeable parameter set. [R39, R40]

# 5. Antigen transport, presentation, and productive recognition

## 5.1 Keep antigen species separate

**P:** use at least six distinct antigen pools: free native antigen; cell-associated native cargo; FDC-retained immune complexes; internalized degradable protein; processed peptide; and surface peptide–HLA complexes. Track source, epitope identity, molecular state, location, and age. A scalar “antigen level” cannot represent all six.

The same native antigen may supply several peptide species. Loss of a native conformational epitope need not eliminate all T-cell peptides. Conversely, persistent peptide–MHC display does not prove that intact BCR-recognizable antigen remains. FDC recycling preserves access to immune complexes, whereas conventional processing generates a different recognition substrate. [R11–R13]

**P:** antigen accounting must use compatible units. Fragmentation can increase particle number without increasing antigen mass; therefore preserve parent provenance or mass-equivalent units rather than demanding that every pool have the same molecule count. Model dissociation, uptake, degradation, and epitope masking separately.

## 5.2 Sinus capture and follicular delivery

SCS macrophages can relay immune complexes through noncognate B cells, providing one route into follicular antigen display. FDCs can internalize and recycle complexes for subsequent B-cell access. These routes should be available when the required complement/antibody/receptor context exists, not forced for every soluble vaccine protein. [R10, R11]

**P:** encode capture as a local encounter with finite binding/processing capacity. Uptake by one cell cannot simultaneously deliver the same indivisible antigen object to unlimited competitors. When using continuous antigen pools, consumption must be reserved and applied atomically. Retention and recycling require independent residence-time parameters.

## 5.3 The MHC class II route

A conventional protein-presentation sequence is: antigen uptake; endosomal processing; access to MHC-II peptide-loading compartments; removal of invariant-chain-derived CLIP; peptide exchange influenced by HLA-DM; surface delivery of peptide–HLA-II; and encounter with a matching CD4 TCR. The HLA-II molecules of interest include HLA-DR, -DP, and -DQ. HLA-DM-supported CLIP dissociation and loading are experimentally established. [R12]

**P:** separate uptake rate, processing delay, peptide yield, HLA compatibility, loading capacity, surface turnover, and partner recognition. These parameters need not be identical across DCs, B cells, and macrophages. Cross-species transfer must not replace the user's actual HLA setting.

**Recognition invariant:** HLA-DRA expression is not a peptide identity. Total MHC-II abundance is not the number of cognate complexes. A large HLA-II signal cannot rescue a TCR–peptide mismatch. For a given interaction, require the correct peptide/HLA pair and a TCR compatibility rule; allow cross-reactivity only when explicitly modeled.

## 5.4 What “MHC-II signaling” means here

For the default priming module, peptide–MHC-II is the recognition surface on the presenting cell; productive signaling is evaluated in the contacting CD4 T cell. Represent the TCR/CD3 signaling program separately from CD28-family costimulation, inhibitory inputs, and cytokine receptor signaling. Do not treat increased APC MHC-II expression as if it directly commanded T-cell proliferation. Functional human B–T experiments and temporally resolved DC–T experiments show why recognition and cellular response are distinct events. [R13, R16, R28]

**P:** a minimal internal abstraction can maintain four continuous program variables: recent cognate TCR stimulation, costimulatory support, inhibitory burden, and cytokine-conditioned differentiation competence. These are model states, not measured concentrations. Their update equations and decay constants must be documented; an LLM must not silently define them.

Insufficient stimulation may yield continued scanning or failed activation. Tolerance/anergy and exhaustion are different biological programs; do not assign either merely because an activation threshold was missed. Include such programs only with a separately specified perturbation and evidence base.

## 5.5 B-cell antigen recognition and linked help

A B cell binds native antigen through its BCR, internalizes associated material, and can present processed peptides to a helper T cell. The B-cell epitope and T-cell peptide need not be identical. The relevant condition is physical linkage within the captured antigen/carrier complex and cognate recognition of the resulting peptide–HLA display. [R13, R28]

**P:** require a traceable chain: native antigen object → B-cell uptake event → processed peptide → surface pMHC-II → cognate helper contact. An unrelated Tfh elsewhere in the follicle cannot provide antigen-specific help just because both cells are “activated.” CD40–CD40L and cytokine support modify outcomes after partner qualification; cytokine proximity alone does not establish linked recognition.

## 5.6 MHC-I and cross-presentation extension

The conventional CD8 route requires peptide–MHC-I rather than peptide–MHC-II. Endogenous antigen and cross-presented exogenous antigen need separate processing routes. Human cDC1-associated cross-presentation is experimentally supported, but presentation capacity is an enrichment, not permission to assume all antigen is efficiently cross-presented. [R14]

**P:** keep the MHC-I module optional in an initial GC-focused model. When enabled, define peptide–HLA-I compatibility, APC licensing/activation context, cytotoxic effector differentiation, and target susceptibility. Do not use GC B-cell death as a proxy for cytotoxic T-cell killing.

# 6. Germinal-center selection, differentiation, and antibody output

## 6.1 GC formation is an outcome

**P:** initialize primary follicles and stromal support, but create an active GC only after enough qualified B-cell activation, helper availability, and spatial organization have developed. A numerical founder threshold is a computational parameter, not a universal human constant. Multiple clones and multiple follicles should remain distinguishable.

GC organization depends on chemokine responsiveness and local support. CXCR4-associated dark-zone positioning and CXCR5-associated follicular/light-zone access should influence movement probabilities rather than enforce rectangular compartments. [R18]

## 6.2 A minimal selection cycle

A proliferative GC cell completes licensed divisions and may generate immunoglobulin variants. A viable descendant enters a selection-associated state, samples available native antigen, presents peptides, and may receive help. Selected cells can recycle or differentiate; unsuccessful cells can die. Experimental work links help to both expansion and cell-cycle speed, and distinguishes apoptotic selection pressures across GC microanatomy. [R29–R31]

**P:** implement this as several events rather than one “GC action.” Candidate events include finish division, update BCR variant, change migratory bias, acquire antigen, load pMHC, request local helper contact, receive help, renew cycling, commit to output, and initiate apoptosis. Do not require mutation at every time step or guarantee that each daughter improves affinity.

## 6.3 Affinity, competition, and mutation

**P:** represent BCR affinity against a named antigen/epitope, not against “the vaccine” as a single universal target. Accessibility, valency, antibody masking, and acquisition capacity can influence capture independently of affinity. A mutation kernel should include neutral, deleterious, and potentially beneficial outcomes; its parameters require sequence-based calibration.

AID is required for canonical somatic hypermutation and class-switch recombination, but these are different processes. Mouse AID deficiency does not mean that all GC structures fail to form. Antibody feedback can also modify antigen availability and GC selection; pre-existing or newly secreted antibody should not be ignored in a recall model. [R34, R52]

**Hard restriction (P):** immunoglobulin diversification must preserve clonal ancestry. No somatic-hypermutation event is applied to the TCR in this healthy vaccine model. Affinity scores must not be updated merely because the model's selection classifier becomes more confident.

## 6.4 Class-switch recombination

Class switching changes the immunoglobulin constant-region program, not the variable-region antigen specificity by itself. It can begin before GC entry; a model that permits it only in light-zone cells will exclude a documented route. IgM/IgD coexpression in naive cells should not be treated as evidence of conventional switch recombination. [R33, R34]

**P:** track isotype, switched allele history, AID competence, cytokine/contact context, and completion time independently of SHM. Switching is not a reversible color change: deleted upstream constant-region DNA is not restored by a later action. Human isotype/subclass choices require human rules; do not relabel mouse IgG1/IgG2a outputs as human subclasses.

A complete human subclass-specific switch matrix is outside the calibrated content of this version. Until one is supplied, use a coarse unswitched/switched state and record that loss of resolution rather than inventing precise subclass probabilities.

## 6.5 Memory versus antibody-secreting output

GC outputs vary across response time and cellular context; mouse fate studies support temporal biases rather than a universal day on which all cells switch fate. Human IL-21/STAT3 studies support B-cell differentiation programs with different requirements in naive and memory populations. [R26, R27, R35]

**P:** use competing output propensities conditioned on current state and history, with irreversible commitment only after a defined program completes. Do not let a cell simultaneously finish a plasma-cell commitment and return to the proliferating GC pool. A memory cell retains recall potential; a mature plasma cell is assigned a different default action set.

## 6.6 Antibody production and plasma-cell survival

**P:** antibodies inherit the clone's specificity and current isotype. Secretion consumes modeled cellular production capacity; antibody distribution and decay belong to an extracellular/reservoir model. Antibody concentration, neutralization, and protection are distinct outputs. Predicting protection requires additional validated relationships beyond LN cell dynamics.

Mouse studies have reached different conclusions about whether BCMA is indispensable for long-lived plasma-cell survival. The 2025 study tested two BCMA-deficient strains and found survival without BCMA under its conditions, contrasting with an earlier report. Retain both observations; use a contextual survival network rather than a universal BCMA-only death gate. [R37, R38]

# 7. Signaling and communication catalogue

The entries below are qualitative candidate mechanisms. They are not an instruction to simulate every cytokine at once. Sources must be activated, receptors must be functionally available, and local exposure must be integrated over time. A gene-expression score can support competence but is not a secretion rate or proof of receptor occupancy.

## 7.1 Positioning signals

| Signal / receptor | Main modeled relationship | Constraint / evidence |
|---|---|---|
| CCL19/CCL21 → CCR7 | T-zone access and DC/lymphocyte trafficking context | Separate chemotaxis, matrix association, and receptor responsiveness. No deterministic T-cell fate assignment. [R03, R04, R08, R17] |
| CXCL13 → CXCR5 | Follicular positioning of B cells and follicular T-cell programs | Local gradients and accessibility matter. CXCR5 expression alone is not proof of Tfh identity. [R07, R17, R18, R21] |
| CXCL12 → CXCR4 | GC dark-zone organization; optional downstream plasma-cell homing module | The GC evidence does not quantify bone-marrow entry or survival. [R18] |
| S1P → S1PR1 | Lymphocyte egress competence along accessible exit routes | Receptor state and tissue topology both matter. [R19] |
| Type-I IFN / CD69–S1PR1 relationship | Activation-associated retention can change egress | Retention is not proliferation; the mouse mechanism requires an explicit transfer label in a human model. [R20] |

## 7.2 Cytokines and survival signals

| Cue | Source/target interpretation | Required caution |
|---|---|---|
| IL-2 → IL-2 receptor / STAT5-associated program | Activated T-cell signal with context-dependent expansion and regulatory effects | More IL-2 is not always more Tfh or larger GCs; experimental IL-2 can restrict Tfh differentiation. [R22] |
| IL-7 → IL-7R-associated survival | FRC-supported naive T-cell homeostasis | A local survival resource, not an automatic vaccine-specific expansion signal. [R04] |
| IL-12 → IL-12R-associated program | Activated APC-to-T-cell signal; human IFN-γ competence and Tfh-like properties in particular experiments | IL-12p40 alone is not bioactive IL-12p70. Do not force Th1 and Tfh into mutually exclusive cytokine bins. [R41, R49, R51] |
| IFN-α/β → IFNAR-associated program | Antiviral sensing responses, including pDC-associated production in suitable settings | Platform, dose, source, and timing matter; an interferon signature is not proof of live infection. [R20, R41, R42] |
| IFN-γ → IFNGR-associated program | Effector feedback and activation context | Secretory competence is not continuous secretion; distinguish exposure from a Th1 identity label. [R51] |
| IL-4 → IL-4R / STAT6-associated program | Helper polarization and B-cell differentiation context | Use species-specific downstream rules. Not a universal consequence of an inactivated platform. [R47] |
| IL-21 → IL-21R / STAT3-associated program | T-cell help influencing GC B-cell maintenance and antibody-secreting differentiation | Effects depend on B-cell state and accompanying signals; human naive and memory cells differ. [R25–R27] |
| IL-6 and IL-1β | Inflammatory context that can influence helper programs | Do not map either cytokine alone to a fixed lineage. Mature IL-1β requires processing; transcript abundance is insufficient. [R41, R46, R48, R50] |
| IL-23 | Context-dependent support of human Th17-associated responses | Not an autonomous universal conversion signal for every naive CD4 cell. [R48, R50] |
| TGF-β | Regulatory and differentiation context | Track active versus latent signal if modeled. Human Th17 culture findings depend on conditions; preserve that uncertainty. [R48, R50] |
| IL-10 | Regulatory and B-cell differentiation context | Do not interpret it as a universal “turn all cells off” variable. The producing and receiving populations matter. [R27, R48] |
| BAFF / APRIL receptor network | B-lineage and antibody-secreting-cell survival context | Tissue-specific ligand sources and receptor redundancy matter. Human tonsil FDCs must not automatically be the BAFF source. [R07, R37, R38] |

**Optional modules:** IL-15 trans-presentation, TNF/lymphotoxin-dependent stromal maintenance, IL-17-driven recruitment, inflammatory chemokines such as CXCL9/10 and CCL2, complement activation, and adhesion mechanics can be added when required. This version does not assign their human kinetic constants or claim that transcript coexpression validates a signaling edge. Each extension needs its own source-backed rule card.

## 7.3 Contact-dependent communication

**Peptide–HLA / TCR:** determines cognate eligibility for the modeled conventional T-cell interaction. **CD80/CD86 / CD28:** costimulatory context must be available on the actual partner. **CD40 / CD40L:** a functional helper input for T-dependent B-cell responses; generic cytokine exposure is not a substitute. [R13, R16, R28]

**CTLA-4 / CD80-CD86:** can reduce available costimulatory ligands through trans-endocytosis. Model a change to partner ligand availability rather than an undefined “suppression score” that affects every cell. **PD-1 ligands:** human FDC observations justify considering local inhibitory interactions, but receptor expression alone does not quantify inhibition or establish T-cell exhaustion. [R07, R24]

**P:** contact events require distance, compatible surfaces, partner availability, sufficient encounter duration, and explicit release. A ligand-presenting surface has finite occupancy. Persistent contacts and secretion may overlap, but a single physical interface cannot be allocated incompatibly to unlimited partners.

# 8. Proliferation, apoptosis, and finite resources

## 8.1 Proliferation is a timed process

**P:** a cell has G0, activation/growth, G1, S, G2, and M states or a justified reduced equivalent. A choice to proliferate can initiate or continue an eligible program; it cannot instantly create a daughter. First-division delay and subsequent interdivision times need separate distributions. A cycling marker is an observation of state, not a completed division event.

T-cell priming experiments show temporally organized contact and division behavior, and GC experiments show that helper signals can alter proliferation and cell-cycle speed. These observations argue against a constant per-frame division chance for all lymphocytes. Their measured kinetics are not universal human defaults. [R16, R29, R30]

**P:** division completion requires viability, completion of the scheduled cycle, a valid license, sufficient biomass/resources, and spatial feasibility. It creates exactly two daughters from one parent. Store parent ID, clone ID, generation, timestamps, partitioned cargo, inherited state, and any separately executed mutation event.

## 8.2 The correct meaning of a proliferation limit

One original cell can produce 524,288 descendants after 19 perfectly surviving binary generations: 2^19 = 524,288. This is a mathematical lineage-tree result, not one cell undergoing 500,000 sequential divisions. Whether that population is plausible depends on time, survival, recruitment, available space, and the biological system.

**P:** avoid a single lifetime division cap shared by naive T cells, GC B cells, plasmablasts, and stromal cells. Instead constrain the current cycle, the number of divisions licensed by recent stimulation, license decay/renewal, differentiation exits, and death. A computational emergency population cap may prevent a crash, but any run that reaches it is flagged as numerically censored, not interpreted as immune homeostasis.

**P:** a help episode can carry a finite division allowance, but its human distribution is unresolved here. Division allowance and interdivision time are different quantities. Do not copy a proposed numerical allowance into the model as if it had been measured in a human LN.

## 8.3 Homeostasis is not population freezing

**P:** maintain inflow, egress, division, and death as separate fluxes. The number of cells in a compartment follows the accounting identity: change = incoming cells + completed net division gain − outgoing cells − deaths. A constant total may arise from balanced fluxes; it must not be enforced by deleting random cells after proliferation.

Space is a local constraint. Use cell volume, exclusion, compressibility assumptions, stromal access, and possible tissue expansion rather than an arbitrary whole-node cell count alone. If nutrient/oxygen metabolism is not explicitly modeled, label the resource constraint as a phenomenological capacity term, not a measured ATP budget. [R05]

## 8.4 Death, failed selection, and clearance

GC cell death can result from different local failures, including inadequate selection and damaging receptor diversification. Mouse reporter/imaging work found substantial GC turnover, with up to half the population lost over six hours under the examined conditions. This is not a universal human death probability or the fraction that should be visibly apoptotic in a snapshot. [R31]

Activated T-cell contraction also has intrinsic apoptotic mechanisms; Bim-dependent death has experimental support in a defined mouse activation model. Therefore, do not require a Fas-mediated killing contact for every contracting T cell. Conversely, do not infer inevitable apoptosis from one low cytokine measurement. [R36]

**P:** distinguish stressed, apoptosis-initiating, irreversibly committed apoptotic, corpse, and cleared states. Before commitment, recovery may be allowed by an explicit model. After commitment, disable movement programs requiring a live cell, new secretion, division, and differentiation. Retain physical debris until phagocytosis/clearance occurs.

Tingible body macrophage behavior supports local removal of apoptotic fragments. **P:** assign finite uptake and digestion capacity, record uncleared debris, and model secondary inflammatory effects only if separately justified. A death event and a clearance event must never be counted as two cell deaths. [R32]

# 9. Quantitative evidence and the parameter register

## 9.1 What is measured, and what is not

The literature anchors below constrain model behavior but do not form a complete human parameter set. The reported measurement, the model parameter, and a transferable prior are different objects. A human FNA frequency cannot be used directly as a whole-node cell count; an in vitro cytokine dose is not an in vivo interstitial concentration.

| Parameter / observation | Evidence anchor | How it can and cannot be used |
|---|---|---|
| Q-01: naive T-cell priming sequence | Mouse intravital work described serial encounters during the first approximately 8 h, more stable contacts in the following approximately 12 h, and proliferation on the second day. [R16] | Establishes ordering and heterogeneous contact behavior. Not a universal human CD4 clock; the experimental antigen delivery and T-cell system must be matched. |
| Q-02: GC proliferation response to help | Mouse GC experiments linked help to division/expansion and to altered cell-cycle speed. [R29, R30] | Supports separate help-dependent division allowance and cycle duration. This manual does not extract a universal numerical human allowance or minimum cycle time. |
| Q-03: GC death burden | Up to roughly half of GC B cells were lost over 6 h in the examined mouse system. [R31] | Use only as a mouse-context turnover anchor. A visible apoptotic fraction also depends on corpse-clearance time and detection. |
| Q-04: human inactivated influenza response | Vaccine-binding GC B cells appeared by week 1; sustained responses through week 9 occurred in 3 of 8 participants. [R39] | Supports heterogeneous, prolonged human GC activity. Does not imply all eight had identical earlier responses or that 9 weeks is a fixed endpoint. |
| Q-05: recall/new-clone mixture | In that influenza study, 12–88% of GC clones overlapped with early circulating plasmablast clones. [R39] | A repertoire/overlap observation, not a direct transition probability from plasmablast to GC cell. Do not reverse the inferred lineage direction. |
| Q-06: another human platform | Human mRNA-vaccine GCs and LN plasmablast responses persisted for at least 12 weeks after the second immunization in the reported study. [R40] | Comparator for possible response duration; not an inactivated/live-attenuated rate estimate. |
| Q-07: human B-cell differentiation | Human IL-21/STAT3 perturbation studies found state-dependent differentiation responses. [R26, R27] | Constrains pathway dependence and naive/memory differences. Culture concentrations and sampling days do not directly set LN exposure or cell-cycle constants. |
| Q-08: plasma-cell survival | Older and newer mouse BCMA experiments differ in the reported requirement for survival. [R37, R38] | Requires alternative contextual hypotheses. A single universal lethal knockout rule is not justified. |

**P, mathematical example only:** if 50% of a homogeneous population dies over 6 h and the hazard is assumed constant, the implied hazard is ln(2)/6 = 0.1155 h⁻¹. A 5-minute event probability would be 1 − exp(−0.1155 × 5/60), approximately 0.00958. This is a conversion demonstration, not a recommended human GC death parameter. The homogeneous constant-hazard assumption is stronger than the original observation.

## 9.2 Parameters requiring a target dataset

| Parameter family | Required unit / representation | Status in this version |
|---|---|---|
| Geometry and packing | μm, μm³, cell-size distribution, contact distance | Unresolved for the target node; derive from imaging or state a scaled domain. |
| Cell entry and exit | cells/min by population and boundary | Unresolved; must distinguish circulating abundance from tissue recruitment. |
| Motility | μm/min, persistence time, turning distribution | Unresolved human values; transfer from imaging only with a declared species/tissue label. |
| Cognate precursor abundance | cells/node or cells/defined domain by clonotype | Unresolved; avoid arbitrary repertoire enrichment without recording it. |
| Native antigen arrival | mass- or molecule-equivalent/min by antigen | Unresolved; injected dose is not LN arrival. |
| Retention and degradation | residence-time distributions or min⁻¹ | Separate injection-site, free, cell-associated, and FDC-retained pools. |
| Processing and pMHC display | delay distribution, complexes/cell, turnover min⁻¹ | Unresolved by cell type, peptide, and HLA allele. |
| Functional contact | min/contact; partner occupancy | Unresolved; distinguish physical contact from productive signaling. |
| First division | hours from a clearly defined activation event | Unresolved human distribution; not the same as subsequent cycling. |
| Subsequent division | hours/cycle, conditional on state and help | Unresolved human distribution; no per-frame daughter creation. |
| Division allowance | completed divisions per qualified stimulation episode | Unresolved; finite distribution and renewal rule are proposed structures, not fitted values. |
| Cytokine production | molecules/min/cell or declared concentration source | Unresolved; RNA abundance is not an absolute secretion rate. |
| Diffusion, binding, uptake | μm²/min; association/dissociation and sink rates | Unresolved; extracellular matrix binding may invalidate free-diffusion assumptions. |
| Selection, death, and differentiation | conditional hazards in min⁻¹ | Unresolved; separated by state and failure mechanism. |
| SHM / affinity change | mutation process per sequence/event; affinity units | Unresolved; sequence-calibrated kernel preferred over arbitrary affinity increases. |
| Antibody output and distribution | molecules/min/cell, transport and loss | Unresolved; serum measurements require a reservoir/observation model. |

**P:** store missing values as explicitly unresolved, not zero. For exploratory visualization, declared demonstration values may be used in a separate configuration, but outputs must be labeled uncalibrated. Sensitivity ranges chosen for debugging are not literature confidence intervals.

## 9.3 Time discretization and event probabilities

**P:** use biological time rather than screen frames. Movement, field diffusion, and long cellular programs can use different integration intervals, provided the coupling is consistent. A faster JEV call changes compute throughput, not the amount of biological time passed.

For an event with hazard λ(t), the probability over an interval is:

P(event in Δt) = 1 − exp[−∫ from t to t+Δt λ(u) du].

For constant λ, this becomes 1 − exp(−λΔt). Never keep an unchanged “10% per step” probability when changing step length. For mutually exclusive events, use competing hazards or an event scheduler. For compatible channels, such as movement and secretion, update them separately. Death and division cannot both complete for the same parent.

**P:** use a distribution of completion times where the biology supports staged processes. A fixed delay can be a deliberate simplification, but it should not be confused with a fitted exponential waiting time. Reducing Δt should not substantially change biological outputs after numerical convergence.

# 10. Atomic biological rule catalogue

Every rule below is a proposed implementation of the cited mechanism or of a stated model invariant. It is not a numerical parameterization. A rule is enabled only when its required fields, measurements, or declared assumptions are available.

## 10.1 Transport and antigen rules

**LN-R001 — Preserve lineage.** A state transition must follow the explicit lineage graph. B, T, myeloid, and stromal identities cannot be exchanged by an agent decision. Reference support: cell-identity and lineage studies; restriction scoped to healthy vaccination. [R02, R06, R15]

**LN-R002 — Enter through a valid boundary.** Recruitment requires a source reservoir, a compatible entry route, and an entry event. No spontaneous appearance in a follicle. [R03, R08]

**LN-R003 — Move continuously.** Position updates obey speed, geometry, and collision constraints. Chemokine responsiveness changes migration bias, not lineage. [R03, R17, R18]

**LN-R004 — Distinguish residence from maturation.** DC lineage is unchanged by acquiring antigen, CCR7-associated migration, or maturation. [R08, R09, R15]

**LN-R005 — Capture local antigen.** Uptake requires accessible antigen and a compatible uptake mechanism; consume or transfer an accounted amount. [R10, R11, R13]

**LN-R006 — Preserve antigen provenance.** A processed peptide or immune complex retains a link to its parent antigen. Recycling does not create replication. [R11, R12]

**LN-R007 — Complete processing before display.** Cognate pMHC-II appears only after a qualified processing/loading route or explicitly initialized display. HLA abundance alone cannot instantiate a peptide. [R12]

**LN-R008 — Match receptor and displayed ligand.** A conventional CD4 interaction requires compatible TCR and peptide–HLA-II; the CD8 branch requires peptide–HLA-I. [R12–R14]

## 10.2 Activation and differentiation rules

**LN-R009 — Qualify productive T-cell priming.** Integrate cognate recognition, partner costimulation, inhibition, and time. A transient collision alone does not complete priming. [R16, R24]

**LN-R010 — Separate retention from expansion.** An activation-associated egress change cannot itself create daughter cells or define helper fate. [R19, R20]

**LN-R011 — Require linked B–T help.** For the T-dependent route, match a B cell's displayed peptide to the helper cell and retain linkage to the BCR-captured material. [R13, R28]

**LN-R012 — Permit an extrafollicular branch.** Activated B cells can enter an antibody-secreting program without obligatory GC passage. [R26, R27, R39]

**LN-R013 — Gate GC entry.** A qualified B cell enters an existing/emerging GC program through a timed transition, not instant relocation. [R18, R29, R39]

**LN-R014 — Keep DZ/LZ switching reversible.** Change program and migration bias, preserving cell and clone ancestry. [R18, R29]

**LN-R015 — Make selection local and competitive.** Antigen access and available cognate helper interactions affect selection. No global affinity leaderboard directly saves every high-affinity cell. [R11, R29, R52]

**LN-R016 — Renew finite proliferative permission.** A qualified help event may alter a bounded episode-specific division allowance and cell-cycle kinetics. Renewing permission is not performing a division. [R29, R30]

**LN-R017 — Separate CSR and SHM.** AID competence does not mean the two events happen together. CSR is allowed before GC entry under the proper program. [R33, R34]

**LN-R018 — Preserve immunoglobulin history.** SHM and switching update explicit sequence/isotype states and clonal records; they cannot erase ancestry or restore deleted DNA by a state label. [R33, R34]

**LN-R019 — Make output choices compete.** Recycling, memory commitment, and plasma commitment have distinct prerequisites and cannot all complete simultaneously. [R27, R35]

**LN-R020 — Keep mature plasma cells out of default cycling.** Use a secretion/survival action set after terminal maturation; re-entry would require an explicitly different model. Survival is not a universal BCMA-only gate. [R37, R38]

## 10.3 Timing, viability, and control rules

**LN-R021 — Complete the cell cycle once.** A viable parent completing one scheduled cycle produces two daughters and is replaced, not retained as a third live cell. [R16, R30]

**LN-R022 — Reserve space and resources.** Failed physical placement or exhausted resource budgets prevent division completion or invoke a declared crowding response; they do not trigger silent deletion elsewhere. [R05]

**LN-R023 — Apply state-specific death mechanisms.** Failed GC selection, receptor damage, and T-cell contraction are distinct hazards. [R31, R36]

**LN-R024 — Make committed apoptosis absorbing.** Cancel pending division/differentiation events after commitment. Never resurrect a cleared agent through a delayed callback. Model invariant (P).

**LN-R025 — Clear corpses separately.** A macrophage uptake event transfers debris into a finite processing queue; it is not a second death event. [R32]

**LN-R026 — Require secretion competence and exposure.** Cytokine production requires a qualified source state; effects require receptor/pathway competence and local exposure. IL-1β processing is explicit if this cytokine is used. [R25–R27, R46]

**LN-R027 — Regulate specific interactions.** Treg/Tfr effects act on defined partners, ligands, or signals. Suppression is not a tissue-wide unconditional stop command. [R23, R24]

**LN-R028 — Exit through an available route.** Egress requires location and competence; exporting a cell removes it from local interactions and records its destination. [R19, R20]

**LN-R029 — Enforce platform-specific antigen generation.** Inactivated antigen has no replication source; live-vaccine production requires an explicitly permissive upstream or cellular module. [R39, R41]

**LN-R030 — Log uncertainty and rejected actions.** Every transition records evidence class, applicable parameters, agent proposal, validator result, and executed consequence. Never conceal an invalid action as a successful biological event. Model requirement (P).

# 11. Four worked rule cards

These examples show the granularity required for future JSON conversion. The biological relationship is source-backed; thresholds, functional forms, and rates remain P unless fitted.

## 11.1 RC-01 — Productive CD4 priming by a DC

**Actors:** viable T-01 and viable antigen-presenting D-01 or D-02, possibly carrying the D-04 tag. **Location:** reachable T-zone/interfollicular contact. **Required observation:** local contact, exact peptide–HLA-II identity/availability, TCR compatibility, costimulation, inhibitory context, and current stimulation history. [R09, R12, R16]

**Eligibility:** cognate display exists; contact is physically valid; neither actor is committed to apoptosis; the partner has remaining contact capacity. **Process:** accumulate stimulation over the contact history; qualify activation only when the declared activation model permits it. **Completion:** change T-01 to T-02, initialize growth/retention programs, and schedule any subsequent cycle-entry evaluation.

**Not allowed:** instant daughter creation; assignment of Tfh solely from high MHC-II; recognition of unrelated peptide; using the vaccine's name instead of peptide/HLA matching. **Unresolved parameters:** productive-contact distribution, signal decay, activation threshold, costimulatory dependence, first-division delay. **Validation:** peptide mismatch must block this cognate route; preserved pMHC with reduced costimulation should have a distinguishable effect from antigen absence.

## 11.2 RC-02 — B-cell capture and linked helper interaction

**Actors:** B-01/B-02 and a qualified activated/helper CD4 cell. **Location:** native-antigen capture site followed by an accessible T–B interface. **Required sequence:** BCR-compatible native antigen uptake → processing → cognate pMHC-II display → helper encounter → contact-dependent help. [R13, R17, R28]

**Eligibility:** adequate native antigen access, functional uptake, compatible HLA processing/display, and an available matching helper. **Completion:** update activation/help history and permit subsequent branch evaluation. **Resource accounting:** remove/transfer captured antigen, maintain processing queue, reserve helper contact, and update displayed complexes according to turnover.

**Not allowed:** generic IL-21 exposure establishing linked recognition; BCR recognition of arbitrary intracellular peptide; simultaneous allocation of one indivisible antigen object to many B cells. **Unresolved parameters:** capture kinetics, peptide yield, helper-contact duration, signal integration, branch probabilities.

## 11.3 RC-03 — GC recycling and a finite proliferative episode

**Actor:** B-05/B-06 with functional receptor state and completed selection-associated help. **Location:** light-zone neighborhood with a reachable proliferative region. **Evidence:** help can change GC expansion and cycling kinetics. [R29, R30]

**Eligibility:** viable cell, qualifying help event, no competing committed output program, and a valid episode-specific allowance. **Initiation:** update migratory/cycling program and schedule the next eligible cycle stage. **Completion of each division:** verify viability and space again, replace parent with two daughters, decrement the relevant allowance under the declared inheritance rule, and preserve clone ancestry.

**P inheritance requirement:** define whether allowance is a per-lineage remaining generation count or a shared clone-level resource. These interpretations have different growth consequences and must not be mixed. **Not allowed:** interpreting one allowance unit as unlimited daughters; cloning the parent without removing it; lowering the cycle duration because JEV answered faster. **Unresolved parameters:** allowance distribution, renewal rule, phase times, growth/resource requirements, and death hazards.

## 11.4 RC-04 — Failed selection, apoptosis, and clearance

**Actor:** GC B cell without adequate selection/survival support, or with a qualifying damaging receptor state. **Partner:** a reachable M-03 for subsequent clearance. **Evidence:** GC death mechanisms and local macrophage clearance are experimentally separable. [R31, R32]

**Eligibility:** the state-specific death model generates an initiation event. **Initiation:** enter apoptosis-initiating state; apply any explicitly modeled pre-commitment rescue window. **Commitment:** terminate live-cell programs and cancel pending mitosis/output events. **Clearance:** transfer corpse/debris to a macrophage only when contact and processing capacity permit.

**Not allowed:** treating each uncleared fragment as another live cell; counting macrophage uptake as another death; maintaining cytokine release indefinitely after commitment. **Unresolved parameters:** initiation/commitment timing, rescue conditions, fragment representation, capture radius, and processing time. **Observable:** live GC count, apoptotic burden, and uncleared material are separate outputs.

# 12. JEV decision layer and deterministic simulator contract

The division of responsibilities below is an architectural proposal. TypeSafe's official material describes bounded semantic decisions and separation from code-based execution; it does not validate this biological model, establish biological rates, or demonstrate predictive performance in a lymph node. [R53]

## 12.1 What a cell agent may observe

**P:** provide only its identity/state, receptor/effector competence, local geometry, nearby partners, accessible antigen species, locally sensed cues, internal cargo, recent contact history, and active clocks. Descriptive text can summarize these observations, but numerical variables, units, and provenance remain explicit.

Do not provide future outcomes, the whole tissue's hidden state, a target antibody titer, or other cells' private clonotype information unless a physical recognition event makes that information observable. An agent should not know that a neighbor has a “high-affinity” BCR by reading a global simulator label.

## 12.2 What it may choose

**P:** JEV may select among a small prevalidated set of context-appropriate actions, such as continue scanning, maintain an eligible contact, move toward an accessible gradient, initiate a permitted program, or defer. Eligibility is calculated before the choice. The agent cannot create a new lineage or add an unlisted cytokine simply because a narrative makes it sound useful.

Separate action channels: movement; contact allocation; secretion; state-program initiation; cell-cycle progression; and viability. Some channels coexist. Others conflict. Apoptotic commitment has priority over division completion and live secretion. The engine, not a natural-language rationale, resolves these conflicts.

## 12.3 What deterministic code must own

**P:** code owns clock advancement, distance and collision checks, diffusion/transport, antigen and cell accounting, contact reservations, stochastic event sampling, cycle completion, apoptosis commitment, and the mutation/affinity model. “Deterministic” here means fully specified and reproducible given state and random seed; it does not prohibit biologically stochastic events.

Use a synchronous update: immutable tissue snapshot → compute eligible actions → obtain bounded agent proposals → validate/reserve resources → resolve conflicts → apply events → update fields → record outcomes. This prevents later agents in an iteration from gaining an artificial advantage by reading already-updated neighbors.

A JEV score is not a hazard, a calibrated probability, a receptor occupancy, or a confidence interval. The scientific model must define and validate any mapping from a score to a biological effect. Benchmark JEV's incremental value against the same simulator using fixed rules or conventional classifiers; otherwise the model may merely reproduce the constraints imposed by its engine.

## 12.4 Failure behavior

**P:** invalid output is rejected and logged. A safe fallback can be no new discretionary action while mandatory clocks and viability continue. Repeated errors, systematic invalid actions, or population emergency caps invalidate the run for inference. Record model version, prompt/rule version, parameter set, random seed, and complete event provenance.

# 13. Field dictionary for later JSON conversion

This section defines a schema concept, not a JSON implementation. Biological records and executable numerical configurations should remain separate so a source correction does not silently change unrelated parameters.

| Record | Required fields |
|---|---|
| Cell identity | identity_id; lineage; species; tissue_scope; annotation_markers; marker_caveats; supported_functions; evidence_refs |
| Cell instance | cell_id; clone_id; parent_id; lineage; state_ids; position_um; compartment_id; age_min; activation_history; cycle_phase; viability; receptor_state; cargo; resource_state |
| Antigen | antigen_id; parent/source_id; platform; native_epitopes; processed_peptides; HLA_compatibility; molecular_state; amount; unit; location; timestamp |
| Spatial region | compartment_id; geometry; adjacency; boundary_type; transport_permissions; source/sink_fields; stromal_support |
| Biological rule | rule_id; version; actors; allowed_states; location_requirements; prerequisites; forbidden_conditions; initiation; completion; effects; competing_events; evidence_class; constraint_class; evidence_refs |
| Parameter | parameter_id; definition; value_or_unresolved; unit; distribution; applicability; experimental_system; source_locator; uncertainty; transfer_assumptions; calibration_status |
| Signal | signal_id; molecular_form; source_state; release_condition; receptor; competence_requirement; transport_model; uptake/decay; response_function |
| Event log | event_id; simulation_time; actor/partner_ids; rule_id; observation_snapshot; eligible_actions; proposal; validation; sampled_event; consumed_resources; completed_effect; rejection_reason |
| Experiment | vaccine/formulation; route; dose; host_history; HLA; species; sample_site; timepoints; measurements; observation_model; held_out_split |

**P:** exact source location should identify an abstract, result paragraph, figure, table, or supplement supporting the parameter or rule. A DOI alone identifies a paper, not the particular numerical value. If a number has not been extracted and checked, mark it unresolved.

**P:** keep biological null, not measured, not applicable, and model zero as different values. For example, zero replication for an inactivated source is a model invariant; unknown FDC antigen residence time is not zero. A missing gene in sparse single-cell data is not evidence that the receptor is functionally absent.

# 14. Validation, negative controls, and calibration

## 14.1 First gate: accounting and invariant tests

**P:** test that every division replaces one parent with two daughters; every live cell has one lineage; every pMHC has a valid origin; antigen transfer cannot double-spend cargo; inactivated sources cannot replicate; committed apoptotic cells cannot divide; all emigrating cells use an outlet; and clone ancestry survives mutation, switching, and differentiation.

Use adversarial agent proposals: a B cell requests a CD4 identity, a cDC requests FDC differentiation, a plasma cell requests immediate GC recycling, or a cell requests mitosis before S phase. The validator must reject each while maintaining a valid state and an informative event log.

## 14.2 Second gate: mechanism-specific perturbations

**Antigen/HLA mismatch:** block the relevant cognate interaction while preserving motility and nonspecific inflammation. It should not remove all cells from the node. [R12–R14]

**B-cell-specific loss of functional MHC-II presentation:** impair the modeled cognate B–T helper route without automatically deleting earlier DC-mediated priming. This is a model discrimination test, not a claim that all other B-cell pathways vanish. [R13, R28]

**CD40/CD40L interruption:** alter T-dependent B-cell output; do not equate it with absence of antigen capture. **AID loss:** remove canonical SHM/CSR while permitting GC formation/expansion where supported, rather than hardcoding no GC. [R28, R34]

**CXCR4/CXCR5 perturbation:** change GC/follicular organization and encounter opportunities without changing lineage. **S1PR1-related perturbation:** affect egress rather than instantly killing retained cells. [R18, R19]

**Changed IL-2 exposure:** test whether the implementation can reproduce reduced Tfh/GC behavior under a matched experimental context. This is not a claim of a universal monotonic dose effect in every human vaccine setting. [R22]

**Reduced helper availability:** modify selection, recycling, and output. **Slower corpse clearance:** increase visible debris without necessarily increasing the underlying death-initiation rate. **BCMA loss:** compare contextual survival-network hypotheses rather than requiring universal plasma-cell extinction. [R29–R32, R37, R38]

## 14.3 Third gate: observations at the correct scale

Compare spatial compartment enrichment, cell tracks/contact distributions, clone sizes, GC DZ/LZ-associated states, cycling fractions, apoptosis and debris, vaccine-specific B-cell frequencies, repertoire overlap, isotype/SHM profiles, and antibody-secreting outputs. No one endpoint is sufficient.

Human serial LN FNA provides a direct longitudinal reference for vaccine-specific GC activity. Blood transcriptomics or plasmablast measurements can complement it but cannot replace the LN measurement. Tonsil organoids and organotypic LN models support controlled perturbations, while omitting parts of intact-body trafficking and physiology. [R39, R40, R42–R45]

**P:** explicitly simulate each assay. Ki-67 positivity reports a cycling-associated state, not a completed-division count. FNA cell proportions depend on sampling/capture and denominator composition. Serum antibody additionally depends on distribution, secretion outside the modeled node, and clearance. Match uncertainty and missingness rather than fitting simulated absolute counts directly to all measured percentages.

## 14.4 Calibration and prediction

**P:** fit geometry/migration and antigen handling before allowing many cytokine coefficients to compensate for incorrect spatial encounters. Estimate only parameters identifiable from the available outputs; fix or marginalize the others transparently. Report parameter correlations and alternative fits, not only a single best run.

Hold out entire donors, vaccination experiments, or perturbations. Splitting cells from the same donor between training and testing does not establish independent predictive performance. A future-time forecast should use only information available before that time, with uncertainty bands derived from parameter and stochastic variation.

Compare three baselines using the same data and engine: constrained fixed rules; a conventional fitted statistical/classifier policy; and the JEV-mediated policy. Evaluate trajectory error, calibration, mechanism-perturbation responses, runtime, invalid-action frequency, and reproducibility. Biological plausibility alone does not demonstrate that JEV improves prediction.

## 14.5 Release criteria for the first model

**P:** release as a mechanistic exploratory simulator only after invariant tests, numerical convergence, and qualitative perturbation checks pass. Release as a calibrated simulator only with a complete parameter/provenance table and matched quantitative validation. Describe it as predictive only after successful held-out longitudinal or perturbation testing.

Before implementation, specify the first vaccine and route, target LN/domain scale, baseline repertoire and HLA model, primary outputs, available calibration data, and which optional modules are disabled. This manual provides the biological structure for those choices; it does not substitute missing measurements with an AI decision.

# 15. Evidence boundaries and unresolved biology

Most detailed spatial movies and mechanistic GC perturbations cited here were performed in mice; several human mechanistic experiments used blood cells or tonsils rather than vaccine-draining peripheral nodes. Direct human vaccine studies are therefore used to constrain response trajectories, while transferred mechanisms retain their original provenance.

The most consequential unresolved quantities are human first/subsequent division distributions by state, antigen arrival and FDC retention, pMHC generation/turnover, helper-contact efficacy, output/death hazards, and the relationship between an observed transcriptional program and functional competence. They cannot be inferred uniquely from one cross-sectional spatial transcriptomics sample.

Two source conflicts must remain explicit: human Th17 cytokine requirements differ across experimental conditions, and BCMA dependence of plasma-cell survival differs across mouse studies. The model should store competing contextual hypotheses rather than average incompatible findings into a single supposedly universal rule. [R37, R38, R48, R50]

The manual's fixed boundaries concern identity, accounting, timing, physical access, and mechanistic eligibility. Quantitative behavior belongs to a separately calibrated parameter set. That separation allows the eventual JSON rules and JEV policy to evolve without losing track of what was actually observed.


# 16. References and evidence provenance

The bibliography contains 52 primary research papers and one software-documentation record. Sources were selected through targeted literature searches and checks of primary article pages, accessible text, or abstracts. This is not a systematic review or a full-text methodological appraisal of every paper. Experimental numbers not extracted and verified for the target use remain unresolved. The annotation after each reference states the system and the principal limit on transfer.

**[R01] Rodda LB et al. (2018).** Single-Cell RNA Sequencing of Lymph Node Stromal Cells Reveals Niche-Associated Heterogeneity. Immunity 48:1014–1028.e6. DOI: 10.1016/j.immuni.2018.04.006.

Evidence scope: Mouse lymph-node stromal single-cell analysis. Supports niche heterogeneity, not human transition rates.

**[R02] Domínguez Conde C et al. (2022).** Cross-tissue immune cell analysis reveals tissue-specific features in humans. Science 376:eabl5197. DOI: 10.1126/science.abl5197.

Evidence scope: Human cross-tissue immune atlas. Used for population context and annotation, not causal differentiation or absolute node counts.

**[R03] Bajénoff M et al. (2006).** Stromal cell networks regulate lymphocyte entry, migration, and territoriality in lymph nodes. Immunity 25:989–1001. DOI: 10.1016/j.immuni.2006.10.011.

Evidence scope: Mouse imaging and stromal-network experiments. Supports spatial routing and cellular territories.

**[R04] Link A et al. (2007).** Fibroblastic reticular cells in lymph nodes regulate the homeostasis of naive T cells. Nature Immunology 8:1255–1265. DOI: 10.1038/ni1513.

Evidence scope: Mouse FRC and naive-T-cell homeostasis experiments; not a human IL-7 secretion-rate estimate.

**[R05] Acton SE et al. (2014).** Dendritic cells control fibroblastic reticular network tension and lymph node expansion. Nature 514:498–502. DOI: 10.1038/nature13814.

Evidence scope: Mouse DC–FRC mechanics and node expansion. Supports deformable architecture rather than fixed tissue capacity.

**[R06] Krautler NJ et al. (2012).** Follicular dendritic cells emerge from ubiquitous perivascular precursors. Cell 150:194–206. DOI: 10.1016/j.cell.2012.05.032.

Evidence scope: Mouse lineage/precursor experiments. Supports mesenchymal FDC origin, not instant adult-cell conversion.

**[R07] Heesters BA et al. (2021).** Characterization of human FDCs reveals regulation of T cells and antigen presentation to B cells. Journal of Experimental Medicine 218:e20210790. DOI: 10.1084/jem.20210790.

Evidence scope: Human tonsil FDC/stromal analysis and functional assays. Includes tissue-specific BAFF-source and immunoregulatory observations.

**[R08] Ohl L et al. (2004).** CCR7 governs skin dendritic cell migration under inflammatory and steady-state conditions. Immunity 21:279–288. DOI: 10.1016/j.immuni.2004.06.014.

Evidence scope: Mouse skin-to-node migration experiments. Route and tissue specificity must be retained.

**[R09] Itano AA et al. (2003).** Distinct dendritic cell populations sequentially present antigen to CD4 T cells and stimulate different aspects of cell-mediated immunity. Immunity 19:47–57. DOI: 10.1016/S1074-7613(03)00175-4.

Evidence scope: Mouse antigen-presentation experiments. Supports sequential contributions from DC populations.

**[R10] Phan TG et al. (2009).** Immune complex relay by subcapsular sinus macrophages and noncognate B cells drives antibody affinity maturation. Nature Immunology 10:786–793. DOI: 10.1038/ni.1745.

Evidence scope: Mouse antigen-relay and GC experiments. Cargo and immune-complex context matter.

**[R11] Heesters BA et al. (2013).** Endocytosis and recycling of immune complexes by follicular dendritic cells enhances B cell antigen binding and activation. Immunity 38:1164–1175. DOI: 10.1016/j.immuni.2013.02.023.

Evidence scope: Experimental FDC immune-complex cycling. Supports native-antigen retention and reacquisition.

**[R12] Denzin LK, Cresswell P. (1995).** HLA-DM induces CLIP dissociation from MHC class II αβ dimers and facilitates peptide loading. Cell 82:155–165. DOI: 10.1016/0092-8674(95)90061-6.

Evidence scope: Biochemical HLA-II loading experiments. Does not supply an in vivo human LN processing time.

**[R13] Lanzavecchia A. (1985).** Antigen-specific interaction between T and B cells. Nature 314:537–539. DOI: 10.1038/314537a0.

Evidence scope: Functional human B–T antigen-presentation experiments. Supports specificity and linked helper interactions.

**[R14] Bachem A et al. (2010).** Superior antigen cross-presentation and XCR1 expression define human CD11c+CD141+ cells as homologues of mouse CD8+ dendritic cells. Journal of Experimental Medicine 207:1273–1281. DOI: 10.1084/jem.20100348.

Evidence scope: Human DC functional experiments. Supports cross-presentation enrichment, not exclusivity of all DC functions.

**[R15] Villani AC et al. (2017).** Single-cell RNA-seq reveals new types of human blood dendritic cells, monocytes, and progenitors. Science 356:eaah4573. DOI: 10.1126/science.aah4573.

Evidence scope: Human blood single-cell/functional characterization. Not a vaccine-draining LN lineage-tracing dataset.

**[R16] Mempel TR, Henrickson SE, von Andrian UH. (2004).** T-cell priming by dendritic cells in lymph nodes occurs in three distinct phases. Nature 427:154–159. DOI: 10.1038/nature02238.

Evidence scope: Mouse intravital priming model. Timing anchors are experiment-specific, not universal human CD4 values.

**[R17] Reif K et al. (2002).** Balanced responsiveness to chemoattractants from adjacent zones determines B-cell position. Nature 416:94–99. DOI: 10.1038/416094a.

Evidence scope: Experimental B-cell positioning and chemokine responsiveness, principally mouse evidence.

**[R18] Allen CDC et al. (2004).** Germinal center dark and light zone organization is mediated by CXCR4 and CXCR5. Nature Immunology 5:943–952. DOI: 10.1038/ni1100.

Evidence scope: Mouse GC organization/chemokine-receptor perturbation. Does not define rigid geometric walls.

**[R19] Matloubian M et al. (2004).** Lymphocyte egress from thymus and peripheral lymphoid organs is dependent on S1P receptor 1. Nature 427:355–360. DOI: 10.1038/nature02284.

Evidence scope: Mouse receptor-dependent egress experiments. Provides mechanism, not a universal human exit rate.

**[R20] Shiow LR et al. (2006).** CD69 acts downstream of interferon-α/β to inhibit S1P1 and lymphocyte egress from lymphoid organs. Nature 440:540–544. DOI: 10.1038/nature04606.

Evidence scope: Mouse activation/retention mechanism. Egress and proliferation remain separate processes.

**[R21] Johnston RJ et al. (2009).** Bcl6 and Blimp-1 are reciprocal and antagonistic regulators of T follicular helper cell differentiation. Science 325:1006–1010. DOI: 10.1126/science.1175870.

Evidence scope: Experimental Tfh regulatory programs, predominantly mouse evidence.

**[R22] Ballesteros-Tato A et al. (2012).** Interleukin-2 inhibits germinal center formation by limiting T follicular helper cell differentiation. Immunity 36:847–856. DOI: 10.1016/j.immuni.2012.02.012.

Evidence scope: Mouse IL-2/Tfh perturbation. Context-dependent constraint against a generic pro-GC IL-2 multiplier.

**[R23] Chung Y et al. (2011).** Follicular regulatory T cells expressing Foxp3 and Bcl-6 suppress germinal center reactions. Nature Medicine 17:983–988. DOI: 10.1038/nm.2426.

Evidence scope: Mouse follicular regulatory-cell experiments. Supports a distinct regulatory state/module.

**[R24] Qureshi OS et al. (2011).** Trans-endocytosis of CD80 and CD86: a molecular basis for the cell-extrinsic function of CTLA-4. Science 332:600–603. DOI: 10.1126/science.1202947.

Evidence scope: Functional CTLA-4 ligand-removal experiments. Supports partner-specific costimulatory changes.

**[R25] Zotos D et al. (2010).** IL-21 regulates germinal center B cell differentiation and proliferation through a B cell-intrinsic mechanism. Journal of Experimental Medicine 207:365–378. DOI: 10.1084/jem.20091777.

Evidence scope: Mouse IL-21 perturbations. Human kinetic transfer is unresolved.

**[R26] Ettinger R et al. (2005).** IL-21 induces differentiation of human naive and memory B cells into antibody-secreting plasma cells. Journal of Immunology 175:7867–7879. DOI: 10.4049/jimmunol.175.12.7867.

Evidence scope: Human B-cell culture experiments. Functional differentiation evidence, not human LN concentration measurements.

**[R27] Deenick EK et al. (2013).** Naive and memory human B cells have distinct requirements for STAT3 activation to differentiate into antibody-secreting plasma cells. Journal of Experimental Medicine 210:2739–2753. DOI: 10.1084/jem.20130323.

Evidence scope: Human B-cell and genetic-deficiency experiments. Supports state-dependent signaling requirements.

**[R28] Nonoyama S et al. (1993).** B cell activation via CD40 is required for specific antibody production by antigen-stimulated human B cells. Journal of Experimental Medicine 178:1097–1102. DOI: 10.1084/jem.178.3.1097.

Evidence scope: Human antigen-driven B-cell functional experiments. Supports CD40-dependent helper routes.

**[R29] Gitlin AD, Shulman Z, Nussenzweig MC. (2014).** Clonal selection in the germinal centre by regulated proliferation and hypermutation. Nature 509:637–640. DOI: 10.1038/nature13300.

Evidence scope: Mouse GC selection experiments. Links help to expansion/diversification; human division budgets remain uncalibrated.

**[R30] Gitlin AD et al. (2015).** T cell help controls the speed of the cell cycle in germinal center B cells. Science 349:643–646. DOI: 10.1126/science.aac4919.

Evidence scope: Mouse GC cell-cycle experiments. Separates cycling kinetics from simple clone-size outcomes.

**[R31] Mayer CT et al. (2017).** The microanatomic segregation of selection by apoptosis in the germinal center. Science 358:eaao2602. DOI: 10.1126/science.aao2602.

Evidence scope: Mouse reporter/imaging study of GC apoptosis. High-turnover estimate is conditional on that system.

**[R32] Grootveld AK et al. (2023).** Apoptotic cell fragments locally activate tingible body macrophages in the germinal center. Cell 186:1144–1161.e18. DOI: 10.1016/j.cell.2023.02.004.

Evidence scope: Mouse imaging/functional study of local apoptotic-material clearance.

**[R33] Roco JA et al. (2019).** Class-Switch Recombination Occurs Infrequently in Germinal Centers. Immunity 51:337–350.e7. DOI: 10.1016/j.immuni.2019.07.001.

Evidence scope: Mouse temporal/lineage experiments supporting substantial pre-GC class switching.

**[R34] Muramatsu M et al. (2000).** Class switch recombination and hypermutation require activation-induced cytidine deaminase (AID), a potential RNA editing enzyme. Cell 102:553–563. DOI: 10.1016/S0092-8674(00)00078-7.

Evidence scope: Mouse AID-deficiency experiments. Historical title retained; it is not an endorsement of the early RNA-editing hypothesis.

**[R35] Weisel FJ et al. (2016).** A Temporal Switch in the Germinal Center Determines Differential Output of Memory B and Plasma Cells. Immunity 44:116–130. DOI: 10.1016/j.immuni.2015.12.004.

Evidence scope: Mouse fate-output study. Temporal biases are not a universal human calendar rule.

**[R36] Hildeman DA et al. (2002).** Activated T cell death in vivo mediated by proapoptotic Bcl-2 family member Bim. Immunity 16:759–767. DOI: 10.1016/S1074-7613(02)00322-9.

Evidence scope: Mouse activated-T-cell death model. Does not quantify all vaccine-induced T-cell contraction.

**[R37] O’Connor BP et al. (2004).** BCMA is essential for the survival of long-lived bone marrow plasma cells. Journal of Experimental Medicine 199:91–98. DOI: 10.1084/jem.20031330.

Evidence scope: Mouse BCMA/survival evidence. Interpret alongside the contrasting newer study R38.

**[R38] Menzel SR et al. (2025).** B cell maturation antigen (BCMA) is dispensable for the survival of long-lived plasma cells. Nature Communications 16:7106. DOI: 10.1038/s41467-025-62530-2.

Evidence scope: Mouse study using two BCMA-deficient strains. Challenges a universal BCMA-only survival rule.

**[R39] Turner JS et al. (2020).** Human germinal centres engage memory and naive B cells after influenza vaccination. Nature 586:127–132. DOI: 10.1038/s41586-020-2711-0.

Evidence scope: Human seasonal influenza vaccination with serial draining-LN sampling and repertoire analysis.

**[R40] Turner JS et al. (2021).** SARS-CoV-2 mRNA vaccines induce persistent human germinal centre responses. Nature 596:109–113. DOI: 10.1038/s41586-021-03738-2.

Evidence scope: Human mRNA vaccination and serial LN sampling. A platform comparator, not an inactivated/live-attenuated parameter set.

**[R41] Querec T et al. (2006).** Yellow fever vaccine YF-17D activates multiple dendritic cell subsets via TLR2, 7, 8, and 9 to stimulate polyvalent immunity. Journal of Experimental Medicine 203:413–424. DOI: 10.1084/jem.20051720.

Evidence scope: Human DC experiments plus mouse mechanistic studies; platform-specific innate evidence.

**[R42] Querec TD et al. (2009).** Systems biology approach predicts immunogenicity of the yellow fever vaccine in humans. Nature Immunology 10:116–125. DOI: 10.1038/ni.1688.

Evidence scope: Human vaccination and systemic measurements. Blood-based associations are not direct spatial LN rates.

**[R43] Nakaya HI et al. (2011).** Systems biology of vaccination for seasonal influenza in humans. Nature Immunology 12:786–795. DOI: 10.1038/ni.2067.

Evidence scope: Human influenza-vaccine systems study. Supports platform/systemic context, not a complete draining-node mechanism.

**[R44] Wagar LE et al. (2021).** Modeling human adaptive immune responses with tonsil organoids. Nature Medicine 27:125–135. DOI: 10.1038/s41591-020-01145-0.

Evidence scope: Human tonsil organoid experiments. Useful for perturbations but not identical to intact peripheral LN physiology.

**[R45] Morrison AI et al. (2025).** Functional organotypic human lymph node model with native immune cells benefits from fibroblastic reticular cell enrichment. Scientific Reports 15:12233. DOI: 10.1038/s41598-025-95031-9.

Evidence scope: Human ex vivo LN model. Supports testing stromal contributions under controlled culture conditions.

**[R46] Martinon F, Burns K, Tschopp J. (2002).** The inflammasome: a molecular platform triggering activation of inflammatory caspases and processing of proIL-β. Molecular Cell 10:417–426. DOI: 10.1016/S1097-2765(02)00599-3.

Evidence scope: Biochemical/cellular inflammasome work. Supports distinguishing precursor from processed IL-1β.

**[R47] Takeda K et al. (1996).** Essential role of Stat6 in IL-4 signalling. Nature 380:627–630. DOI: 10.1038/380627a0.

Evidence scope: Mouse STAT6 loss-of-function study. Supports pathway dependence, not human subclass-specific numerical rules.

**[R48] Volpe E et al. (2008).** A critical function for transforming growth factor-β, interleukin 23 and proinflammatory cytokines in driving and modulating human TH-17 responses. Nature Immunology 9:650–657. DOI: 10.1038/ni.1613.

Evidence scope: Human T-cell culture experiments. Interpret with R50 because starting populations and culture conditions matter.

**[R49] Schmitt N et al. (2009).** Human dendritic cells induce the differentiation of interleukin-21-producing T follicular helper-like cells through interleukin-12. Immunity 31:158–169. DOI: 10.1016/j.immuni.2009.04.016.

Evidence scope: Human DC–T-cell culture experiments. Tfh-like function in vitro is not a complete GC Tfh identity.

**[R50] Acosta-Rodriguez EV et al. (2007).** Interleukins 1β and 6 but not transforming growth factor-β are essential for the differentiation of interleukin 17-producing human T helper cells. Nature Immunology 8:942–949. DOI: 10.1038/ni1496.

Evidence scope: Human T-cell differentiation experiments. Contrasting TGF-β result relative to R48 must remain contextual.

**[R51] Manetti R et al. (1994).** Interleukin 12 induces stable priming for interferon gamma (IFN-gamma) production during differentiation of human T helper (Th) cells and transient IFN-gamma production in established Th2 cell clones. Journal of Experimental Medicine 179:1273–1283. DOI: 10.1084/jem.179.4.1273.

Evidence scope: Human T-cell culture experiments on cytokine competence and differentiation.

**[R52] Zhang Y et al. (2013).** Germinal center B cells govern their own fate via antibody feedback. Journal of Experimental Medicine 210:457–464. DOI: 10.1084/jem.20120150.

Evidence scope: Mouse GC experiments and modeling. Supports an antibody-feedback module affecting antigen access/selection.

**[R53] TypeSafe. (2026).** TypeSafe agent skill, official repository; Introducing System One Models and JEV, official technical introduction. Accessed 21 September 2026.

Evidence scope: Software documentation, not biological evidence. Repository: github.com/typesafe-ai/skills, skills/typesafe-ai/SKILL.md. Technical introduction: typesafe.ai/blog/introducing-system-one-models-and-jev.

