# -*- coding: utf-8 -*-
"""
Higher Education & CDIO Engineering Engine (Phase 4)
Implements:
- Bilingual TP Lab Report Generator (Canevas Algérien)
- CDIO Standards 3.0 Project Structuring (Conceive - Design - Implement - Operate)
- Automated Logarithmic Uncertainty Calculation (Calcul d'incertitudes)
- PFE & Master Thesis Structure Auditor (MESRS Arrêté 1082 Compliant)
"""

import os
import sys
import json
import math
import argparse
from typing import Dict, Any, List, Optional, Tuple

sys.stdout.reconfigure(encoding='utf-8')

class HigherEdCDIOEngine:
    """Core computational and methodological engine for Algerian higher education."""

    @staticmethod
    def calculate_uncertainty_quotient(
        a: float, delta_a: float,
        b: float, delta_b: float,
        power_a: float = 1.0, power_b: float = 1.0
    ) -> Dict[str, Any]:
        """
        Calculates absolute and relative uncertainty for Y = (A^n) / (B^m)
        using logarithmic differentiation: delta_Y / Y = n * (delta_A / A) + m * (delta_B / B)
        """
        if b == 0:
            raise ValueError("Division by zero in uncertainty calculation.")
            
        y_val = (math.pow(a, power_a)) / (math.pow(b, power_b))
        rel_uncertainty = (power_a * (delta_a / abs(a))) + (power_b * (delta_b / abs(b)))
        abs_uncertainty = abs(y_val) * rel_uncertainty
        
        return {
            "formula": f"Y = (A^{power_a}) / (B^{power_b})",
            "y_value": round(y_val, 4),
            "absolute_uncertainty": round(abs_uncertainty, 4),
            "relative_uncertainty_percent": round(rel_uncertainty * 100, 2),
            "formatted_result": f"Y = ({round(y_val, 4)} ± {round(abs_uncertainty, 4)})",
            "differentiation_rule": "ΔY/Y = |n|(ΔA/A) + |m|(ΔB/B) (Différentiation logarithmique)"
        }

    @staticmethod
    def generate_tp_report_template(tp_title: str, field: str = "ST / Physique") -> str:
        """Generates a complete Algerian university TP report structure in French/Arabic."""
        template = rf"""# Compte-Rendu de Travaux Pratiques (TP)
**Domaine:** {field} | **Module:** Travaux Pratiques de Physique / Chimie
**Titre du TP:** {tp_title}

---

## 1. But du TP (الهدف من التجربة)
- Déterminer expérimentalement les grandeurs caractéristiques de la manipulation.
- Vérifier la validité des lois théoriques régissant le phénomène physique étudié.
- Maîtriser les instruments de mesure et évaluer les incertitudes expérimentales.

---

## 2. Rappel Théorique (الأساس النظري)
- Énoncer les lois physiques régissant le système (ex. Loi d'Ohm, Principe fondamental de la dynamique).
- Définir clairement les variables, paramètres, constantes et leurs unités dans le Système International (SI).

---

## 3. Matériel et Schéma de Montage (العتاد والتركيب التجريبي)
- **Liste du matériel:** (Générateur, Oscilloscope, Multimètre, Résistance étalon, Capteurs...).
- **Schéma du montage:**

```mermaid
graph LR
    G["Générateur E"] -->|"Courant I"| R["Composant R"]
    R -->|"Tension U"| A["Ampèremètre"]
    A -->|"Fermeture"| G
```

---

## 4. Mode Opératoire (طريقة العمل)
1. Réaliser le câblage selon le schéma sans mettre sous tension.
2. Faire vérifier le montage par l'enseignant encadrant.
3. Varier les paramètres d'entrée et relever les grandeurs correspondantes.

---

## 5. Mesures et Tableau de Résultats (النتائج والقياسات)

| N° Mesure | Grandeur d'entrée $X$ | Grandeur de sortie $Y$ | Incertitude $\Delta Y$ |
| :---: | :---: | :---: | :---: |
| 1 | ... | ... | ... |
| 2 | ... | ... | ... |
| 3 | ... | ... | ... |

---

## 6. Calcul d'Incertitudes (حساب الارتيابات الإلزامي)
- **Incertitude absolue:** $\Delta Y$ déterminée par calcul d'erreur ou tolérance d'appareil.
- **Incertitude relative:** $\frac{{\Delta Y}}{{Y}} \times 100\%$.
- **Résultat final normalisé:**
  $$Y = (Y_{{\text{{exp}}}} \pm \Delta Y) \, [\text{{Unité}}]$$

---

## 7. Exploitation Graphique et Interprétation (الرسم والمناقشة)
- Tracer $Y = f(X)$ sur papier millimétré en plaçant les croix d'incertitude.
- Déterminer la pente expérimentale $a = \frac{{\Delta Y}}{{\Delta X}}$.
- Déduire la valeur de la constante physique recherchée.

---

## 8. Conclusion et Écart Relatif (الخاتمة وحساب التباعد)
- Calcul de l'écart relatif avec la valeur théorique tabulée:
  $$\text{{Écart}} = \frac{{|Y_{{\text{{exp}}}} - Y_{{\text{{théo}}}}|}}{{Y_{{\text{{théo}}}}}} \times 100\%$$
- Discussion des sources d'erreurs (résistance interne des appareils, imprécision de lecture...).
"""
        return template

    @staticmethod
    def structure_cdio_project(project_title: str, domain: str = "Génie Mécanique / Électrique") -> Dict[str, Any]:
        """Structures an engineering project into CDIO 3.0 stages."""
        return {
            "project_title": project_title,
            "domain": domain,
            "framework": "Worldwide CDIO Standards 3.0 (Conceive - Design - Implement - Operate)",
            "stages": [
                {
                    "stage": "1. Conceive (التصور وتحديد دفتر الشروط)",
                    "tasks": [
                        "Identification des besoins clients et de l'état de l'art",
                        "Rédaction du Cahier des Charges Fonctionnel (CDCF)",
                        "Étude de faisabilité technico-économique et contraintes normatives"
                    ],
                    "deliverable": "Cahier des charges validé (Specifications Document)"
                },
                {
                    "stage": "2. Design (التصميم والنمذجة الهندسية)",
                    "tasks": [
                        "Modélisation mathématique et cinématique/dynamique",
                        "Schémas d'architecture globale et diagrammes UML/SysML",
                        "Dimensionnement des composants et simulations préliminaires (CAD/SolidWorks/MATLAB)"
                    ],
                    "deliverable": "Dossier de conception détaillée (Detailed Design Document)"
                },
                {
                    "stage": "3. Implement (التنفيذ العملي والبرمجي)",
                    "tasks": [
                        "Développement des algorithmes et écriture du code embarqué (C/C++, Python)",
                        "Routage et réalisation des circuits imprimés (PCB) et usinage mécanique",
                        "Intégration matériel-logiciel et prototypage fonctionnel"
                    ],
                    "deliverable": "Prototype fonctionnel ou banc d'essai opérationnel"
                },
                {
                    "stage": "4. Operate (التشغيل والتحقق والصيانة)",
                    "tasks": [
                        "Protocoles de tests, de métrologie et validation des performances",
                        "Analyse des défaillances et calcul de fiabilité (AMDEC / FMEA)",
                        "Rédaction du manuel d'utilisation et bilan de fin de projet"
                    ],
                    "deliverable": "Rapport de qualification et notice de maintenance"
                }
            ]
        }

    @staticmethod
    def audit_pfe_structure(sections_present: List[str], citation_style: str = "IEEE") -> Dict[str, Any]:
        """Audits PFE report compliance against MESRS Canevas and Arrêté 1082."""
        mandatory_sections = [
            "Page de garde",
            "Résumés trilingues (Ar, Fr, En) et mots-clés",
            "Introduction Générale",
            "État de l'art / Revue bibliographique",
            "Matériel et Méthodes / Conception",
            "Résultats et Discussion",
            "Conclusion Générale et Perspectives",
            "Références Bibliographiques"
        ]
        
        missing = [sec for sec in mandatory_sections if not any(sec.lower() in p.lower() for p in sections_present)]
        
        plagiarism_checklist = [
            "Taux de similarité global inférieur à 10% (Arrêté ministériel 1082)",
            f"Respect strict de la norme de citation {citation_style}",
            "Absence totale de copier-coller sans guillemets et référence explicite",
            "Reformulation académique (Paraphrase) des concepts théoriques"
        ]
        
        is_compliant = len(missing) == 0
        
        return {
            "canevas_status": "Conforme" if is_compliant else "Non conforme (Sections manquantes)",
            "missing_sections": missing,
            "citation_style_verified": citation_style,
            "anti_plagiarism_rules": plagiarism_checklist,
            "recommendation": "Valide pour soumission à la commission de soutenance" if is_compliant else "Compléter les sections obligatoires avant validation"
        }

def run_phase4_demo():
    print("=" * 75)
    print("🚀 تشغيل محرك التعليم الجامعي والمدارس العليا LMD & CDIO (Phase 4 Demo)")
    print("=" * 75)
    
    engine = HigherEdCDIOEngine()
    
    # 1. Uncertainty Calculation Demo
    print("\n[المحطة 1: حساب الارتيابات بالتفاضل اللوغاريتمي - Calcul d'Incertitudes]")
    # Y = A / B, e.g. Resistance R = U / I where U = (12.0 ± 0.2) V, I = (2.00 ± 0.05) A
    u_res = engine.calculate_uncertainty_quotient(a=12.0, delta_a=0.2, b=2.00, delta_b=0.05)
    print(f"الصيغة الفيزيائية: R = U / I")
    print(f"القاعدة المطبقة: {u_res['differentiation_rule']}")
    print(f"قيمة المقاومة: {u_res['y_value']} Ω")
    print(f"الارتياب المطلق ΔR: ± {u_res['absolute_uncertainty']} Ω")
    print(f"الارتياب النسبي: {u_res['relative_uncertainty_percent']} %")
    print(f"النتيجة المعيارية: {u_res['formatted_result']} Ω\n")
    
    # 2. CDIO Project Structuring Demo
    print("[المحطة 2: نمذجة مشروع هندسي وفق معايير CDIO 3.0 العالمية]")
    cdio_proj = engine.structure_cdio_project("Conception et Réalisation d'un Bras Robotisé Autonome")
    print(f"المشروع: {cdio_proj['project_title']}")
    print(f"الإطار المعتمد: {cdio_proj['framework']}\n")
    for st in cdio_proj["stages"]:
        print(f"  • {st['stage']}:")
        print(f"    - المخرجات: {st['deliverable']}")
        for t in st["tasks"][:2]:
            print(f"      * {t}")
        print()
        
    # 3. PFE Canevas & Anti-Plagiarism Audit Demo
    print("[المحطة 3: تدقيق هيكل مذكرة التخرج PFE ومكافحة الانتحال (القرار الوزاري 1082)]")
    student_sections = [
        "Page de garde",
        "Résumés trilingues (Ar, Fr, En) et mots-clés",
        "Introduction Générale",
        "État de l'art / Revue bibliographique",
        "Matériel et Méthodes / Conception",
        "Résultats et Discussion",
        "Conclusion Générale et Perspectives",
        "Références Bibliographiques"
    ]
    pfe_audit = engine.audit_pfe_structure(student_sections, citation_style="IEEE")
    print(f"حالة المطابقة مع معايير MESRS: {pfe_audit['canevas_status']}")
    print(f"التوصية الأكاديمية: {pfe_audit['recommendation']}")
    print(f"قواعد مكافحة الانتحال العلمي (Arrêté 1082):")
    for r in pfe_audit["anti_plagiarism_rules"]:
        print(f"  - {r}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="محرك التعليم الجامعي والمدارس العليا LMD وCDIO")
    parser.add_argument("--demo", action="store_true", help="تشغيل العرض العملي لكافة المكونات")
    parser.add_argument("--tp", type=str, help="توليد قالب تقرير TP كامل")
    parser.add_argument("--cdio", type=str, help="نمذجة مشروع هندسي وفق CDIO")
    parser.add_argument("--uncertainty", action="store_true", help="حساب ارتياب نموذجي")
    
    args = parser.parse_args()
    engine = HigherEdCDIOEngine()
    
    if args.demo or len(sys.argv) == 1:
        run_phase4_demo()
    elif args.tp:
        print(engine.generate_tp_report_template(args.tp))
    elif args.cdio:
        res = engine.structure_cdio_project(args.cdio)
        print(json.dumps(res, ensure_ascii=False, indent=2))
    elif args.uncertainty:
        res = engine.calculate_uncertainty_quotient(10.0, 0.1, 2.0, 0.05)
        print(json.dumps(res, ensure_ascii=False, indent=2))
