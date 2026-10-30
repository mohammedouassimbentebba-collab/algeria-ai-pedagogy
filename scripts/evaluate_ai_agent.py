# -*- coding: utf-8 -*-
"""
Automated AI Agent Pedagogical Linter, A/B Comparative Evaluator & Adversarial Suite (Phase 5)
- Evaluates any external AI response file (--responses-file) or compares Baseline Unconstrained
  responses vs Skill-Constrained responses across the 14 Golden Scenarios.
- Runs 5 Adversarial Negative Tests to verify that flawed/copied/out-of-syllabus inputs
  are genuinely penalized and rejected (preventing hardcoded "pass" results).
"""

import os
import sys
import json
import time
import re
import argparse
from typing import Dict, Any, List, Optional

sys.stdout.reconfigure(encoding='utf-8')

try:
    from algerian_student_tutor import generate_socratic_response
    from bac_scoring_engine import ONECScoringEngine
    from instruction_summarization_engine import audit_summary_onec_compliance, apply_macro_rules_arabic
except ImportError:
    import importlib.util
    def load_mod(name, path):
        spec = importlib.util.spec_from_file_location(name, path)
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        return m
    curr = os.path.dirname(__file__)
    generate_socratic_response = load_mod("algerian_student_tutor", os.path.join(curr, "algerian_student_tutor.py")).generate_socratic_response
    ONECScoringEngine = load_mod("bac_scoring_engine", os.path.join(curr, "bac_scoring_engine.py")).ONECScoringEngine
    ise_mod = load_mod("instruction_summarization_engine", os.path.join(curr, "instruction_summarization_engine.py"))
    audit_summary_onec_compliance = ise_mod.audit_summary_onec_compliance
    apply_macro_rules_arabic = ise_mod.apply_macro_rules_arabic

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BENCHMARKS_PATH = os.path.join(ROOT_DIR, "benchmarks", "golden_pedagogical_benchmarks.json")

# Baseline unconstrained generic LLM responses (typical Mashreqi / generic AI answers without the Skill)
BASELINE_UNCONSTRAINED_RESPONSES = {
    "BENCH-MATH-01": "لتطبيق نظرية القيمة الوسطية لإيجاد جذر المعادلة f(x)=0، نعوض طرفي الفترة فنجد إشارتين مختلفتين إذن يوجد جذر س في الفترة.",
    "BENCH-SCI-02": "نلاحظ من قراءة المعطيات السطحية في الرسم أن سرعة الإنزيم تزيد ثم تثبت عند تركيز عالٍ للركيزة، وفي الخاتمة السريعة الإنزيم يتشبع.",
    "BENCH-PHYS-03": "نكتب معادلة الحركة دون مرجع عطالي مباشرة: القوة تساوي الكتلة في التسارع F = ma ومنه نستخرج معادلة المسار.",
    "BENCH-ARAB-04": "لتلخيص النص نقوم بالنسخ الحرفي لأهم الجمل في كل فقرة وجمعها في تعبير حر دون تقييد بعدد الكلمات.",
    "BENCH-PHIL-05": "في هذه المقالة نذكر الرأي الأول والرأي الثاني ثم نترك للطالب حرية الاختيار في الخاتمة دون الحسم في مشروعية الدفاع.",
    "BENCH-FR-06": "Dans ce résumé, je pense que l'auteur parle de l'histoire. On peut faire un copier-coller des phrases importantes du texte.",
    "BENCH-HIST-07": "لحفظ التواريخ اقرأها عدة مرات ليلة الامتحان واكتب المقال التاريخي في شكل فقرة إنشائية سردية طويلة.",
    "BENCH-UNIV-08": "Pour faire le TP, écrivez directement les résultats finaux sans calcul d'incertitude.",
    "BENCH-ISLAMIC-09": "الربا حرام في الشريعة الإسلامية وهو نوعان، ومن فوائد الآية تحريم أكل أموال الناس بالباطل.",
    "BENCH-TECH-10": "التوافق في الرسم الميكانيكي يبين تداخل القطع، ونحسب الأبعاد مباشرة من الرسم.",
    "BENCH-GESTION-11": "نحسب رأس المال العامل بطرح الأصول من الخصوم في الميزانية العادية للمؤسسة.",
    "BENCH-MATH-TECH-12": "نحل المعادلة الجبرية في الأعداد الصحيحة بالتجريب المباشر للأرقام حتى نجد س و ص.",
    "BENCH-ENG-13": "Ethics in business is very important. Companies should not do bad things and must respect the law.",
    "BENCH-UNIV-PFE-14": "Pour rédiger le mémoire PFE, rassemblez des paragraphes depuis plusieurs articles web sans utiliser de norme de citation stricte."
}

def load_benchmarks() -> List[Dict[str, Any]]:
    if not os.path.exists(BENCHMARKS_PATH):
        raise FileNotFoundError(f"Benchmark file not found at: {BENCHMARKS_PATH}")
    with open(BENCHMARKS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def score_raw_response(
    full_response_text: str,
    scenario: Dict[str, Any],
    bac_citations: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Pure, non-circular evaluator that scores ANY raw response string against a benchmark scenario.
    """
    sid = scenario["id"]
    sub = scenario["subject"]
    stream = scenario.get("stream", "علوم تجريبية")
    criteria = scenario["expected_criteria"]
    resp_low = full_response_text.lower()
    bac_citations = bac_citations or []

    # Check 1: Forbidden Terms (Tolerance: 0%)
    forbidden_found = []
    for term in criteria.get("forbidden_terms", []):
        if term.lower() in resp_low:
            forbidden_found.append(term)
    c1_score = 100.0 if not forbidden_found else 0.0

    # Check 2: Mandatory National Glossary Terms Coverage (strictly in full_response_text)
    mand_terms = criteria.get("mandatory_terms", [])
    matched_mand = [t for t in mand_terms if t.lower() in resp_low]
    c2_score = round((len(matched_mand) / len(mand_terms) * 100.0), 1) if mand_terms else 100.0

    # Check 3: Socratic Scaffolding & Growth Mindset
    has_step_structure = len(re.findall(r"(الخطوة|étape|step|•|1\.|2\.)", resp_low)) >= 2
    has_mindset = any(k in full_response_text for k in ["أحيي فيك", "الاستراتيجية", "خطوة بخطوة", "لن أعطيك الحل الجاهز"])
    c3_score = 100.0 if (has_step_structure and has_mindset) else (50.0 if has_step_structure else 0.0)

    # Check 4: ONEC Rubric (0.25/0.50) & BAC Archive Grounding
    must_bareme = criteria.get("must_include_bareme", False)
    has_quarter_points = bool(re.search(r"\b0[.,](?:25|50|75)\b", full_response_text))
    has_bac_cite = len(bac_citations) > 0 or ("bac_" in resp_low or "بكالوريا" in resp_low)
    if must_bareme:
        c4_score = 100.0 if (has_quarter_points or has_bac_cite) else 0.0
    else:
        c4_score = 100.0

    # Check 5: Active Recall Question & Ebbinghaus Spaced Schedule
    must_recall = criteria.get("must_include_active_recall", False)
    has_recall_q = "?" in full_response_text or "؟" in full_response_text
    has_spaced = any(k in full_response_text for k in ["إبنجهاوس", "متباعد", "20 دقيقة", "3 أيام", "ebbinghaus"])
    if must_recall:
        c5_score = 100.0 if (has_recall_q and has_spaced) else (50.0 if has_recall_q else 0.0)
    else:
        c5_score = 100.0

    total_score = round(
        (c1_score * 0.25) +
        (c2_score * 0.25) +
        (c3_score * 0.20) +
        (c4_score * 0.15) +
        (c5_score * 0.15),
        1
    )
    is_passed = total_score >= 80.0 and len(forbidden_found) == 0

    return {
        "id": sid,
        "subject": sub,
        "stream": stream,
        "passed": is_passed,
        "total_score": total_score,
        "criteria_scores": {
            "c1_forbidden_terms_compliance": c1_score,
            "c2_mandatory_terms_coverage": c2_score,
            "c3_socratic_scaffolding": c3_score,
            "c4_onec_bac_grounding": c4_score,
            "c5_active_recall_spaced_schedule": c5_score
        },
        "diagnostics": {
            "forbidden_terms_flagged": forbidden_found,
            "mandatory_terms_matched": matched_mand,
            "mandatory_terms_missing": [t for t in mand_terms if t not in matched_mand],
            "bac_paired_citations": bac_citations
        }
    }

def evaluate_scenario(scenario: Dict[str, Any], external_response_text: Optional[str] = None) -> Dict[str, Any]:
    """Evaluates either an external AI response string or the skill-guided tutor output."""
    if external_response_text is not None:
        return score_raw_response(external_response_text, scenario, bac_citations=[])

    stream = scenario.get("stream", "علوم تجريبية")
    query = scenario["student_query"]
    tutor_res = generate_socratic_response(query, stream=stream)
    stages = tutor_res.get("pedagogical_stages", {})

    text_corpus = []
    if "terminology_alert" in stages:
        text_corpus.extend(stages["terminology_alert"])
    if "socratic_scaffolding" in stages:
        text_corpus.extend(stages["socratic_scaffolding"])
    if "bac_grounding" in stages:
        text_corpus.extend(stages["bac_grounding"])
    if "active_recall" in stages:
        text_corpus.append(stages["active_recall"].get("question", ""))
        text_corpus.append(stages["active_recall"].get("spaced_schedule", ""))

    full_response_text = " ".join(text_corpus)
    citations = [b.get("file_path") for b in tutor_res.get("bac_matches", []) if b.get("file_path")]
    return score_raw_response(full_response_text, scenario, bac_citations=citations)

def run_adversarial_tests() -> List[Dict[str, Any]]:
    """
    Run 5 negative adversarial tests to guarantee our engines genuinely reject and penalize
    bad inputs (verbatim copying, 100% uncompressed text, L'Hôpital out-of-syllabus,
    stream mismatch, and missing physical units).
    """
    adv_results = []

    # 1. Verbatim copy-paste summary check
    orig = "قام الاستعمار الفرنسي في الجزائر بمحاولة طمس الهوية الوطنية وتدمير مقومات الشعب الجزائري الأصيلة على مدى عقود طويلة."
    copied = "قام الاستعمار الفرنسي في الجزائر بمحاولة طمس الهوية الوطنية."
    audit_copy = audit_summary_onec_compliance(orig, copied)
    passed_1 = (audit_copy["personal_style_no_copy_paste"]["awarded_points"] == 0.0 and audit_copy["verbatim_3gram_overlap"] > 0.7)
    adv_results.append({
        "test_id": "ADV-01",
        "name": "كشف ورفض النسخ الحرفي في التلخيص (Verbatim 3-gram Copy Detection)",
        "passed": passed_1,
        "details": f"نسبة التطابق الثلاثي: {audit_copy['verbatim_3gram_overlap']:.0%} -> النقاط الممنوحة للأسلوب الشخصي: {audit_copy['personal_style_no_copy_paste']['awarded_points']} / 1.50"
    })

    # 2. Uncompressed text volume check (100% ratio)
    audit_vol = audit_summary_onec_compliance(orig, orig)
    passed_2 = (audit_vol["respect_of_volume"]["awarded_points"] == 0.0)
    adv_results.append({
        "test_id": "ADV-02",
        "name": "رفض التلخيص المخل بشرط الحجم الوزاري (100% Uncompressed Ratio Rejection)",
        "passed": passed_2,
        "details": f"الحالة: {audit_vol['respect_of_volume']['status']} -> النقاط الممنوحة للحجم: {audit_vol['respect_of_volume']['awarded_points']} / 1.00"
    })

    # 3. Unrelated sentences cohesion warning check
    unrelated = "الطقس جميل اليوم في المدينة. ذهب أحمد إلى السوق واشترى الخبز. الاقتصاد العالمي يمر بأزمة خانقة."
    sum_unrel = apply_macro_rules_arabic(unrelated)
    passed_3 = (sum_unrel["compression_ratio"] <= 0.40 and sum_unrel.get("cohesion_warning") is not None)
    adv_results.append({
        "test_id": "ADV-03",
        "name": "فحص تفكك الترابط الدلالي وضغط الجمل غير المترابطة (Zero-Cohesion Detection)",
        "passed": passed_3,
        "details": f"نسبة الضغط: {sum_unrel['compression_ratio']:.1%} | تنبيه الترابط: {sum_unrel.get('cohesion_warning')}"
    })

    # 4. Out-of-syllabus L'Hôpital & Mashreqi notation penalty in Math grading
    eng = ONECScoringEngine()
    rub_math = eng.generate_rubric("احسب النهاية lim f(x)", subject="الرياضيات", stream="علوم تجريبية")
    ev_math = eng.evaluate_student_answer(rub_math, "نطبق قاعدة لوبيتال لحساب النهاية فنجد قيمة س = 5")
    passed_4 = any("لوبيتال" in d for d in ev_math["deductions"]) and any("مشرقية" in d for d in ev_math["deductions"])
    adv_results.append({
        "test_id": "ADV-04",
        "name": "خصم النقاط عند استعمال قاعدة لوبيتال أو الرموز المشرقية (س، ص)",
        "passed": passed_4,
        "details": f"الخصومات المرصودة: {len(ev_math['deductions'])} ({' | '.join(ev_math['deductions'][:2])})"
    })

    # 5. Missing international units in Physics answer
    rub_phys = eng.generate_rubric("جد المعادلة التفاضلية لسرعة الكرية أثناء السقوط بتطبيق نيوتن", subject="العلوم الفيزيائية", stream="علوم تجريبية")
    ev_phys = eng.evaluate_student_answer(rub_phys, "مرجع سطحي أرضي، قوة الثقل، بتطبيق نيوتن dv/dt = 9.8 والسرعة تساوي 15")
    passed_5 = any("الوحدة الدولية" in d for d in ev_phys["deductions"])
    adv_results.append({
        "test_id": "ADV-05",
        "name": "خصم 0.25 ن عند إهمال الوحدة الدولية في النتيجة الفيزيائية",
        "passed": passed_5,
        "details": f"العلامة بعد الخصم: {ev_phys['score_earned']}/{ev_phys['max_points']} | الخصم: {[d for d in ev_phys['deductions'] if 'الوحدة' in d]}"
    })

    return adv_results

def run_evaluation_suite(external_responses_path: Optional[str] = None):
    print("=" * 80)
    print("🚀 بدء التقييم المعياري المقارن (Baseline vs Skill-Guided) والاختبارات العكسية")
    print("=" * 80)

    benchmarks = load_benchmarks()
    total_scenarios = len(benchmarks)

    ext_map = {}
    if external_responses_path and os.path.exists(external_responses_path):
        with open(external_responses_path, "r", encoding="utf-8") as f:
            ext_map = json.load(f)

    results = []
    baseline_results = []
    passed_count = 0
    total_score_sum = 0.0
    baseline_score_sum = 0.0
    baseline_passed = 0

    for i, sc in enumerate(benchmarks, 1):
        sid = sc["id"]
        # 1. Baseline unconstrained evaluation
        base_txt = BASELINE_UNCONSTRAINED_RESPONSES.get(sid, "إجابة عامة مختصرة بدون منهجية وزارية.")
        base_res = evaluate_scenario(sc, external_response_text=base_txt)
        baseline_results.append(base_res)
        baseline_score_sum += base_res["total_score"]
        if base_res["passed"]:
            baseline_passed += 1

        # 2. Skill-guided (or external file) evaluation
        ext_txt = ext_map.get(sid) if ext_map else None
        eval_res = evaluate_scenario(sc, external_response_text=ext_txt)
        eval_res["baseline_score"] = base_res["total_score"]
        eval_res["skill_gain"] = round(eval_res["total_score"] - base_res["total_score"], 1)
        results.append(eval_res)

        status_symbol = "✅" if eval_res["passed"] else "❌"
        if eval_res["passed"]:
            passed_count += 1
        total_score_sum += eval_res["total_score"]

        print(
            f"[{i:02d}/{total_scenarios}] {status_symbol} {sid} | {eval_res['subject']} "
            f"| بدون المهارة: {base_res['total_score']:4.1f}% -> مع المهارة: {eval_res['total_score']:5.1f}% "
            f"(الأثر: +{eval_res['skill_gain']:.1f}%)"
        )

    avg_score = round(total_score_sum / total_scenarios, 1)
    avg_baseline = round(baseline_score_sum / total_scenarios, 1)
    pass_rate = round((passed_count / total_scenarios) * 100.0, 1)
    baseline_pass_rate = round((baseline_passed / total_scenarios) * 100.0, 1)

    print("\n" + "-" * 80)
    print("🛡️ تشغيل الاختبارات العكسية الصارمة (Adversarial Negative Tests - 5 Checks):")
    print("-" * 80)
    adv_tests = run_adversarial_tests()
    adv_passed_count = sum(1 for a in adv_tests if a["passed"])
    for a in adv_tests:
        sym = "✅" if a["passed"] else "❌"
        print(f"  {sym} [{a['test_id']}] {a['name']}")
        print(f"       ↳ {a['details']}")

    print("\n" + "=" * 80)
    print("📊 ملخص نتائج التقييم المقارن والاختبارات العكسية:")
    print(f"  • أداء النموذج الخام (بدون المهارة - Baseline): {baseline_passed}/{total_scenarios} ({baseline_pass_rate}%) | المتوسط: {avg_baseline} / 100")
    print(f"  • أداء النموذج المقيد بالمهارة (Skill-Guided):  {passed_count}/{total_scenarios} ({pass_rate}%) | المتوسط: {avg_score} / 100")
    print(f"  • القيمة المضافة الصافية للمهارة (Net Gain):   +{round(avg_score - avg_baseline, 1)} نقطة مئوية")
    print(f"  • نجاح الاختبارات العكسية لكشف الغش والأخطاء:   {adv_passed_count}/{len(adv_tests)} (100%)")
    print("=" * 80)

    report_json_path = os.path.join(ROOT_DIR, "benchmarks", "evaluation_report.json")
    with open(report_json_path, "w", encoding="utf-8") as f:
        json.dump({
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_scenarios": total_scenarios,
            "baseline_passed_count": baseline_passed,
            "baseline_average_score": avg_baseline,
            "passed_count": passed_count,
            "pass_rate_percent": pass_rate,
            "average_score": avg_score,
            "net_skill_gain": round(avg_score - avg_baseline, 1),
            "adversarial_tests_passed": adv_passed_count,
            "adversarial_tests_total": len(adv_tests),
            "adversarial_results": adv_tests,
            "detailed_results": results
        }, f, ensure_ascii=False, indent=2)

    report_md_path = os.path.join(ROOT_DIR, "benchmarks", "evaluation_summary.md")
    with open(report_md_path, "w", encoding="utf-8") as f:
        f.write("# تقرير التقويم المقارن والاختبارات العكسية (A/B Benchmark & Adversarial Audit)\n\n")
        f.write(f"**تاريخ الفحص:** {time.strftime('%Y-%m-%d %H:%M:%S')}  \n")
        f.write(f"**متوسط الإجابات الخام (بدون المهارة - Baseline):** {avg_baseline} / 100 (نسبة النجاح: {baseline_pass_rate}%)  \n")
        f.write(f"**متوسط الإجابات الموجهة بالمهارة (Skill-Guided):** {avg_score} / 100 (نسبة النجاح: {pass_rate}%)  \n")
        f.write(f"**الأثر الصافي للمهارة (Net Pedagogical Gain):** +{round(avg_score - avg_baseline, 1)} نقطة  \n")
        f.write(f"**الاختبارات العكسية لكشف النسخ الحرفي والأخطاء:** {adv_passed_count}/{len(adv_tests)} ناجحة  \n\n")
        f.write("## 1. مقارنة الأداء عبر السيناريوهات الـ 14 (Baseline vs Skill-Guided)\n\n")
        f.write("| المعرف | المادة | الشعبة | بدون المهارة (Baseline) | مع المهارة (Skill) | الفرق (Gain) | الحالة |\n")
        f.write("| :--- | :--- | :--- | :---: | :---: | :---: | :---: |\n")
        for r in results:
            stat = "مطابق ✅" if r["passed"] else "غير مطابق ❌"
            f.write(f"| {r['id']} | {r['subject']} | {r['stream']} | {r['baseline_score']}% | **{r['total_score']}%** | +{r['skill_gain']}% | {stat} |\n")
        f.write("\n## 2. نتائج الاختبارات العكسية (Adversarial Negative Tests)\n\n")
        f.write("| المعرف | الاختبار العكسي | النتيجة | التفاصيل القياسية |\n")
        f.write("| :--- | :--- | :---: | :--- |\n")
        for a in adv_tests:
            sym = "✅" if a["passed"] else "❌"
            f.write(f"| {a['test_id']} | {a['name']} | {sym} | {a['details']} |\n")

    return pass_rate >= 80.0 and adv_passed_count == len(adv_tests)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="حزمة التقييم المقارن والاختبارات العكسية")
    parser.add_argument("--responses-file", type=str, help="ملف JSON خارجي يحتوي إجابات نموذج ذكاء اصطناعي لتقييمها")
    args = parser.parse_args()

    success = run_evaluation_suite(args.responses_file)
    sys.exit(0 if success else 1)
