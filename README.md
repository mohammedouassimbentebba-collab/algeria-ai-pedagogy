# 🇩🇿 BAC-Guardian: Algerian National AI Pedagogy & BAC Governance Skill
### إطار الحوكمة البيداغوجية والذكاء الاصطناعي للمنهاج والتعليم الجزائري

[![Project Name](https://img.shields.io/badge/Project-BAC--Guardian-1f883d.svg?style=flat-square&logo=github)](https://github.com/mohammedouassimbentebba-collab/algeria-ai-pedagogy)
[![BAC Archives](https://img.shields.io/badge/BAC%20Archives-2017--2026%20(659%20PDFs)-006233.svg?style=flat-square)](./BAC_Archives)
[![OCR Status](https://img.shields.io/badge/OCR%20Indexed-100%25%20Complete-D52B1E.svg?style=flat-square)](./BAC_Archives/bac_text_corpus.jsonl)
[![ONEC Compliance](https://img.shields.io/badge/ONEC%20Rubrics-2%2C589%20Criteria-gold.svg?style=flat-square)](./BAC_Archives/onec_extracted_rubrics.json)
[![Pedagogical Foundations](https://img.shields.io/badge/Cognitive%20Science-31%20Peer--Reviewed%20Papers-blue.svg?style=flat-square)](./Pedagogical_Science_Foundations)
[![License](https://img.shields.io/badge/License-MIT-lightgrey.svg?style=flat-square)](LICENSE)

**BAC-Guardian** is an enterprise-grade pedagogical alignment framework and AI Agent Skill that constrains Large Language Models (LLMs) and autonomous agents to strictly adhere to official **Algerian Ministry of National Education (MEN)** and **National Examinations and Contests Office (ONEC)** curricula, scoring rubrics, standardized terminology, and cognitive science foundations.

---

## 🌟 Key Features

1. **Official National Pedagogical Terminology (100% MEN Compliance):**
   - Strictly prohibits non-curriculum, Mashreqi, or informal terms (e.g., enforces *الدالة المشتقة* instead of *المشتقة الأولى*, *مجموعة التعريف* instead of *مجال الدالة*, *مستقيم مقارب* instead of *خط تقارب*).
   - Zero tolerance for non-curriculum analytical shortcuts (e.g., strictly bans L'Hôpital's rule in limits).

2. **Official ONEC Scoring Rubric Engine:**
   - Decomposes problem solving into quarter-point increments (0.25, 0.5, 0.75) following official exam correction sheets.
   - Enforces intermediate mathematical proofs, literal formulas prior to numerical substitution, and mandatory SI units in physics.

3. **Complete BAC National Corpus (2017–2026):**
   - **659 official exam papers & answer keys** fully OCR-processed and indexed.
   - 100% scanned PDF coverage with font-glyph decoding (17 custom ONEC ligatures normalized).
   - Instant search and semantic query tools across all secondary streams (Mathematics, Experimental Sciences, Mathematical Technical, Management & Economics, Literature & Philosophy, Foreign Languages).

4. **Rigorous Cognitive & Learning Science Foundations:**
   - **PCK (Shulman 1986):** 3-tier multimodal conceptualization (Concrete, Visual/Graphical, Formal Symbolic).
   - **Discourse Macro-rules (Kintsch & van Dijk 1983):** Deletion, generalization, and construction for text summarization with strict anti-verbatim copy penalties.
   - **Active Retrieval & Spaced Repetition (Dunlosky 2013, Roediger & Karpicke 2006).**
   - **Spatial Memory & Fast Replay (Krokos 2019, Buch et al./Cell Reports 2021).**

5. **Higher Education (LMD & CDIO Standards 3.0):**
   - University-level laboratory reports (TP), graduation theses (PFE), uncertainty propagation, and engineering lifecycle alignment.

---

## 📁 Repository Structure

```tree
├── .agents/skills/algeria-education-system/  # Core Agent Skill definition & guidelines
│   ├── SKILL.md                              # Main agent entry point & directives
│   └── references/                           # Subject-specific pedagogical guides
│       ├── national_pedagogical_glossary.md  # Official MEN/ONEC terminology
│       ├── onec_scoring_rubric_engine.md     # Official grading mechanics
│       ├── stream_differentiation_matrix.md  # Strict academic stream divergence
│       ├── mathematics_methodology.md        # Mathematics BAC methodology
│       ├── physics_chemistry_methodology.md  # Physics & Chemistry methodology
│       ├── natural_sciences_methodology.md   # Biology / Natural Sciences methodology
│       ├── arabic_methodology.md             # Arabic literature & summarization
│       ├── philosophy_methodology.md         # Philosophy official canevas
│       ├── foreign_languages_methodology.md  # French & English Compte-rendu
│       ├── history_geography_methodology.md  # History & Geography methodology
│       ├── islamic_sciences_methodology.md   # Islamic Studies methodology
│       └── higher_education_cdio_framework.md# University LMD & CDIO framework
├── BAC_Archives/                             # Official 2017–2026 Exam Archives (659 files)
│   ├── bac_catalog_index.json                # Structured metadata index
│   ├── bac_text_corpus.jsonl                 # Full OCR text corpus
│   ├── onec_extracted_rubrics.json           # 2,589 extracted scoring criteria
│   └── [Subject Folders]                     # Organized by stream & academic subject
├── Pedagogical_Science_Foundations/          # 31 local peer-reviewed foundational papers
├── eval_pack/                                # 20 Real BAC Exam Evaluation Directories (A/B testing)
│   ├── Q01 ... Q20                           # Question PNGs, Task specs, & Official Corrigés
│   ├── PROMPT_A_BASELINE.txt                 # Baseline prompt (unconstrained model)
│   ├── PROMPT_B_SKILL.txt                    # Skill-guided prompt (ONEC compliant)
│   └── scoring_sheet.csv                     # A/B evaluation scoring template
└── scripts/                                  # Auditing, OCR, and Scoring toolchain
    ├── audit_pedagogical_compliance.py       # Full compliance verification suite
    ├── evaluate_ai_agent.py                  # A/B evaluation & adversarial testing engine
    ├── bac_scoring_engine.py                 # ONEC rubric grading engine
    ├── instruction_summarization_engine.py   # Macro-rules summarization & copy auditor
    └── query_bac.py                          # Fast deep-search CLI across all 659 exams
```

---

## 🚀 Quick Start & CLI Tools

### 1. Search the BAC Corpus
Search through 659 official exam papers and answers:
```bash
# Query by stream and topic
python scripts/query_bac.py --subject "الرياضيات" --stream "علوم تجريبية" --query "القيم المتوسطة"

# Deep keyword search across all indexed OCR texts
python scripts/query_bac.py --deep "مبرهنة بيزو"
```

### 2. Verify Pedagogical Compliance
Run the comprehensive 9-suite pedagogical compliance audit:
```bash
python scripts/audit_pedagogical_compliance.py
```

### 3. Evaluate AI Agent Responses (A/B & Adversarial Testing)
```bash
python scripts/evaluate_ai_agent.py
```

---

## 🧪 Real-World A/B Evaluation Pack

To empirically verify the value of this skill on your own models (GPT-4o, Claude 3.5 Sonnet, Gemini 1.5 Pro, etc.):
1. Navigate to [`eval_pack/`](./eval_pack).
2. For each question (`Q01` to `Q20`), provide the model with `question_page1.png` and test:
   - **Condition A (Baseline):** Using [`eval_pack/PROMPT_A_BASELINE.txt`](./eval_pack/PROMPT_A_BASELINE.txt)
   - **Condition B (Skill-Guided):** Using [`eval_pack/PROMPT_B_SKILL.txt`](./eval_pack/PROMPT_B_SKILL.txt)
3. Compare both outputs against the included official answer key (`ANSWER_KEY_official_corrige.pdf`) and record scores in [`scoring_sheet.csv`](./eval_pack/scoring_sheet.csv).

---

## 📜 Official Pedagogical References
- **Ministry of National Education (MEN Algeria)** — General Inspectorate of Pedagogy.
- **National Examinations and Contests Office (ONEC)** — Official BAC Barèmes & Corrigés (2017–2026).
- **Ministry of Higher Education and Scientific Research (MESRS)** — LMD Directives.
- **CDIO Initiative** — Standards 3.0 for Engineering Education.

---

## ⚖️ License
Released under the [MIT License](LICENSE).
Exam subjects and answer keys remain the intellectual property of the National Examinations and Contests Office (ONEC), Republic of Algeria.
