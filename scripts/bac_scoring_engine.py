# -*- coding: utf-8 -*-
"""
BAC Scoring and Evaluation Engine (ONEC Ministerial Standard)
Part of Phase 2: BAC Grounding & Scoring Rubric Engine.
Provides automated rubric generation, itemized 0.25/0.50 grading,
and stream-specific syllabus compatibility checking.
"""

import os
import sys
import json
import re
import argparse
from typing import Dict, Any, List, Optional, Tuple

sys.stdout.reconfigure(encoding='utf-8')

# Stream Syllabus Topic Restrictions (Out-of-syllabus detection)
OUT_OF_SYLLABUS_MAP = {
    "علوم تجريبية": {
        "topics_forbidden": [
            r"القسمة\s+في\s+z", r"الموافقات\b", r"مبرهنة\s+بيزو", r"مبرهنة\s+غوص",
            r"نظام\s+التعداد", r"التشابه\s+المباشر", r"الاهتزازات\s+الميكانيكية"
        ],
        "message": "هذا المحور خاص فقط بشعبتي (رياضيات) و(تقني رياضي) وغير مبرمج لطلبة شعبة العلوم التجريبية في شهادة البكالوريا."
    },
    "تسيير واقتصاد": {
        "topics_forbidden": [
            r"الأعداد\s+المركبة", r"الهندسة\s+في\s+الفضاء", r"التكامل\s+وحساب\s+الحجوم",
            r"الدوال\s+المثلثية", r"القسمة\s+في\s+z", r"المسعى\s+العلمي"
        ],
        "message": "هذا المحور مجرد/علمي وغير مبرمج لشعبة تسيير واقتصاد؛ حيث يقتصر برنامجكم في الرياضيات على الدوال، المتتاليات، والإحصاء والاحتمالات."
    },
    "آداب وفلسفة": {
        "topics_forbidden": [
            r"الأعداد\s+المركبة", r"الهندسة\s+في\s+الفضاء", r"التكامل", r"الدوال\s+الأسية",
            r"الدوال\s+اللوغاريتمية", r"قوانين\s+نيوتن", r"التركيب\s+الضوئي", r"المناعة"
        ],
        "message": "هذا المحور علمي صرف ولا يُدرس في شعبة آداب وفلسفة؛ برنامجكم في الرياضيات مقتصر على الموافقات والمتتاليات والدوال كثيرات الحدود من الدرجة الثالثة."
    },
    "لغات أجنبية": {
        "topics_forbidden": [
            r"الأعداد\s+المركبة", r"الهندسة\s+في\s+الفضاء", r"التكامل", r"الفيزياء", r"العلوم\s+الطبيعية"
        ],
        "message": "هذا المحور غير مبرمج لشعبة لغات أجنبية."
    }
}

class ONECScoringEngine:
    """Core engine for retrieving real extracted ONEC rubrics and evaluating student answers."""

    _extracted_db = None

    @classmethod
    def _load_extracted_rubrics(cls) -> List[Dict[str, Any]]:
        if cls._extracted_db is not None:
            return cls._extracted_db
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        db_path = os.path.join(root_dir, "BAC_Archives", "onec_extracted_rubrics.json")
        if os.path.exists(db_path):
            try:
                with open(db_path, "r", encoding="utf-8") as f:
                    cls._extracted_db = json.load(f).get("rubrics", [])
            except Exception:
                cls._extracted_db = []
        else:
            cls._extracted_db = []
        return cls._extracted_db

    @classmethod
    def retrieve_official_onec_rubrics(cls, subject: str, stream: Optional[str] = None, query: str = "", limit: int = 2) -> List[Dict[str, Any]]:
        """Search the 2,589 real ONEC corrigé rubric items extracted from BAC_Archives."""
        rubrics = cls._load_extracted_rubrics()
        if not rubrics:
            return []

        sub_clean = subject.replace("_", " ").strip()
        q_tokens = [w for w in re.split(r"\W+", query.lower()) if len(w) >= 3]

        scored = []
        for r in rubrics:
            if sub_clean and sub_clean not in r.get("subject", "") and r.get("subject", "") not in sub_clean:
                continue
            score = 1.0
            if stream and (stream in r.get("stream", "") or r.get("stream", "") in stream):
                score += 2.0
            # Match query tokens against detected topics and rubric step criteria
            blob = " ".join(r.get("detected_topics", [])) + " " + " ".join(i.get("step_criterion", "") for i in r.get("rubric_items", []))
            blob_low = blob.lower()
            for qt in q_tokens:
                if qt in blob_low:
                    score += 1.5
            scored.append((score, r.get("year") or 0, r))

        scored.sort(key=lambda x: (x[0], x[1]), reverse=True)
        results = []
        for sc, yr, r in scored[:limit]:
            # Filter best matching items inside that corrigé
            items = r.get("rubric_items", [])
            if q_tokens:
                matched_items = [i for i in items if any(qt in i.get("step_criterion", "").lower() for qt in q_tokens)]
                selected_items = (matched_items + [i for i in items if i not in matched_items])[:6]
            else:
                selected_items = items[:6]
            results.append({
                "corrige_id": r["corrige_id"],
                "file_path": r["file_path"],
                "subject": r["subject"],
                "stream": r["stream"],
                "year": r["year"],
                "session": r.get("session", "عادية"),
                "sampled_steps": selected_items
            })
        return results
    
    @staticmethod
    def verify_stream_compatibility(stream: str, query_text: str) -> Optional[str]:
        """Check if the student is asking about an out-of-syllabus topic for their stream."""
        stream_norm = stream.strip()
        if stream_norm in OUT_OF_SYLLABUS_MAP:
            for pattern in OUT_OF_SYLLABUS_MAP[stream_norm]["topics_forbidden"]:
                if re.search(pattern, query_text, re.IGNORECASE):
                    return OUT_OF_SYLLABUS_MAP[stream_norm]["message"]
        return None

    @staticmethod
    def generate_rubric(question_text: str, subject: str, stream: str, max_points: float = 3.5) -> Dict[str, Any]:
        """Deconstruct an exam question into official ONEC sub-steps and attach real archive corrigé rubrics."""
        
        # Check compatibility first
        compat_warning = ONECScoringEngine.verify_stream_compatibility(stream, question_text)
        official_samples = ONECScoringEngine.retrieve_official_onec_rubrics(subject, stream=stream, query=question_text, limit=2)
        
        sub_indicators = []
        q_lower = question_text.lower()
        
        if "فيزيا" in subject or "physics" in subject.lower():
            if "نيوتن" in q_lower or "سقوط" in q_lower or "ميكانيك" in q_lower or "قذيفة" in q_lower:
                sub_indicators = [
                    {"step": "تحديد الجملة المدروسة والمرجع العطالي السطحي الأرضي", "points": 0.50, "required_keyword": "مرجع"},
                    {"step": "إحصاء وتمثيل القوى الخارجية المؤثرة", "points": 0.25, "required_keyword": "قوة"},
                    {"step": "كتابة القانون الثاني لنيوتن والإسقاط على المحور الموجه", "points": 0.50, "required_keyword": "نيوتن"},
                    {"step": "استخراج المعادلة التفاضلية وترتيبها بدقة", "points": 0.50, "required_keyword": "dv/dt"},
                    {"step": "كتابة الوحدات الفيزيائية الصحيحة للثوابت والسرعة", "points": 0.25, "required_keyword": "m/s"}
                ]
            elif "دارة" in q_lower or "مكثفة" in q_lower or "rc" in q_lower or "rl" in q_lower:
                sub_indicators = [
                    {"step": "قانون جمع التوترات وتحديد جهة التيار والتوترات", "points": 0.25, "required_keyword": "توتر"},
                    {"step": "كتابة المعادلة التفاضلية للتوتر أو الشحنة", "points": 0.50, "required_keyword": "معادلة"},
                    {"step": "إثبات عبارة ثابت الزمن والتحليل البعدي", "points": 0.50, "required_keyword": "ثابت الزمن"}
                ]
            else:
                sub_indicators = [
                    {"step": "التأسيس الفيزيائي والقانون الرياضي المعتمد", "points": 0.50, "required_keyword": ""},
                    {"step": "التطبيق العددي ومراعاة الوحدات الدولية", "points": 0.50, "required_keyword": ""}
                ]

        elif "رياضيات" in subject or "math" in subject.lower():
            if "قيم متوسطة" in q_lower or "f(x)=0" in q_lower or "حلا وحيدا" in q_lower:
                sub_indicators = [
                    {"step": "الاستمرارية والرتابة التامة على المجال المحدد", "points": 0.25, "required_keyword": "مستمرة ورتيبة"},
                    {"step": "حساب الصورتين وبيان اختلاف إشارتهما f(a) × f(b) < 0", "points": 0.25, "required_keyword": "f("},
                    {"step": "الاستنتاج الرسمي وصياغة الحصر: تقبل حلا وحيدا α", "points": 0.25, "required_keyword": "حسب مبرهنة القيم المتوسطة"}
                ]
            elif "بيزو" in q_lower or "غوص" in q_lower or "pgcd" in q_lower or "موافقات" in q_lower:
                sub_indicators = [
                    {"step": "حساب القاسم المشترك الأكبر PGCD بخوارزمية إقليدس", "points": 0.50, "required_keyword": "pgcd"},
                    {"step": "تطبيق مبرهنة بيزو أو غوص مع ذكر شرط الأولية فيما بينهما", "points": 0.50, "required_keyword": "أوليان"},
                    {"step": "كتابة مجموعة الحلول في Z بدلالة الوسيط الصحيح k", "points": 0.50, "required_keyword": "k"}
                ]
            elif "نهاية" in q_lower or "نهايات" in q_lower or "lim" in q_lower:
                sub_indicators = [
                    {"step": "حساب النهاية الأولى مع التبرير الرياضي (تزايد مقارن أو نهاية شهيرة)", "points": 0.50, "required_keyword": "lim"},
                    {"step": "حساب النهاية الثانية مع التبرير الرياضي والتفسير البياني للمستقيم المقارب", "points": 0.50, "required_keyword": "مقارب"}
                ]
            elif "مشتق" in q_lower or "تغيرات" in q_lower:
                sub_indicators = [
                    {"step": "ذكر قابلية الاشتقاق وحساب الدالة المشتقة f'(x)", "points": 0.50, "required_keyword": "قابلة للاشتقاق"},
                    {"step": "دراسة إشارة المشتقة وتحديد اتجاه التغير", "points": 0.50, "required_keyword": "متزايدة"},
                    {"step": "رسم جدول التغيرات بأسطره الثلاثة مع النهايات وقيم الذروة", "points": 0.50, "required_keyword": "جدول"}
                ]
            else:
                sub_indicators = [
                    {"step": "التأسيس النظري وكتابة القانون / المبرهنة", "points": 0.25, "required_keyword": ""},
                    {"step": "التطبيق الجبري المنطقي المتدرج", "points": 0.50, "required_keyword": ""},
                    {"step": "النتيجة النهائية الدقيقة", "points": 0.25, "required_keyword": ""}
                ]

        elif "طبيعة" in subject or "علوم طبيعية" in subject or "snv" in subject.lower() or "nature" in subject.lower():
            sub_indicators = [
                {"step": "التعريف بالوثيقة والسند التجريبي بدقة", "points": 0.25, "required_keyword": "تمثل الوثيقة"},
                {"step": "تحليل المعطيات بمؤشرات المقارنة والدلالة (حيث نلاحظ... مما يدل على)", "points": 0.50, "required_keyword": "نلاحظ"},
                {"step": "الاستنتاج الجزئي المركز والمباشر", "points": 0.50, "required_keyword": "نستنتج"}
            ]
        else:
            # If we have extracted real steps from the archive for this subject, surface their structure
            sub_indicators = [
                {"step": "المقدمة وضبط الإشكالية بدقة", "points": 0.50, "required_keyword": ""},
                {"step": "العرض وتفكيك المؤشرات العلمية/الفلسفية/التاريخية", "points": 1.50, "required_keyword": ""},
                {"step": "الخاتمة والحوصلة التركيبية المنسجمة", "points": 0.50, "required_keyword": ""}
            ]
            
        total_p = sum(ind["points"] for ind in sub_indicators)
        
        return {
            "question": question_text,
            "subject": subject,
            "stream": stream,
            "total_points": total_p,
            "compatibility_warning": compat_warning,
            "indicators": sub_indicators,
            "official_archive_rubrics": official_samples
        }

    @staticmethod
    def evaluate_student_answer(rubric: Dict[str, Any], student_answer: str) -> Dict[str, Any]:
        """Grade a student's answer against each indicator in the ONEC rubric with quarter-point accuracy."""
        
        results = []
        earned_total = 0.0
        deductions = []
        clean_ans = student_answer.lower()
        
        for ind in rubric.get("indicators", []):
            req = ind.get("required_keyword", "").lower()
            pts = ind["points"]
            
            # Simple keyword heuristic for automated audit demo
            matched = True
            if req and req not in clean_ans:
                matched = False
                
            if matched:
                earned = pts
                results.append({
                    "step": ind["step"],
                    "points_allocated": pts,
                    "points_earned": earned,
                    "status": "مكتملة ومستوفاة"
                })
                earned_total += earned
            else:
                earned = 0.0
                results.append({
                    "step": ind["step"],
                    "points_allocated": pts,
                    "points_earned": 0.0,
                    "status": f"ناقصة (يُشترط ذكر: {req})"
                })
                deductions.append(f"خصم {pts} ن: لعدم استيفاء «{ind['step']}».")
                
        # Deduct for missing international units after numerical values in physics
        if "فيزيا" in rubric.get("subject", ""):
            num_matches = re.findall(r"(?:=|\bيساوي|\bتساوي)\s*[-+]?\d+(?:[.,]\d+)?([^\n.,؛;]*)", clean_ans)
            for trailing in num_matches:
                if not re.search(r"\b(m/s|m\.s|s|v|a|kg|g|mol|j|ev|mev|w|hz|rad|c|Ω|ohm|ω|μf|mf|nf|f|h|n|pa)\b", trailing.strip(), re.IGNORECASE):
                    deductions.append("خصم 0.25 ن وزاري: إهمال كتابة الوحدة الدولية بعد القيمة العددية في النتيجة الفيزيائية.")
                    earned_total = max(0.0, earned_total - 0.25)
                    break

        # Deduct for out-of-syllabus methods (e.g., L'Hôpital's rule in BAC Math) or Mashreqi notation
        if re.search(r"(لوبيتال|h[oô]pital)", clean_ans, re.IGNORECASE):
            deductions.append("رفض وزاري (خصم 0.50 ن): قاعدة لوبيتال (L'Hôpital) خارج المنهاج الثانوي الجزائري ولا تُقبل في تصحيح البكالوريا.")
            earned_total = max(0.0, earned_total - 0.50)

        if re.search(r"(نظرية\s+القيمة\s+الوسط|حساب\s+[سص]\b|\b[سص]\s*=)", clean_ans):
            deductions.append("تنبيه مصطلحي وزاري (خصم 0.25 ن): استخدام مصطلحات أو رموز مشرقية غير معتمدة في المنهاج الجزائري.")
            earned_total = max(0.0, earned_total - 0.25)
                    
        return {
            "question": rubric["question"],
            "subject": rubric["subject"],
            "stream": rubric["stream"],
            "max_points": rubric["total_points"],
            "score_earned": round(earned_total, 2),
            "percentage": round((earned_total / rubric["total_points"]) * 100, 1) if rubric["total_points"] > 0 else 0,
            "itemized_steps": results,
            "deductions": deductions,
            "compatibility_warning": rubric.get("compatibility_warning"),
            "official_archive_rubrics": rubric.get("official_archive_rubrics", [])
        }

    @staticmethod
    def format_rubric_table(eval_result: Dict[str, Any]) -> str:
        """Format the evaluation as an official ONEC markdown rubric table."""
        out = []
        out.append(f"### 📋 شبكة التقييم وسلم التنقيط المعتمد رسمياً (ONEC)")
        out.append(f"**المادة:** {eval_result['subject']} | **الشعبة:** {eval_result['stream']}")
        out.append(f"**السؤال:** {eval_result['question']}\n")
        
        if eval_result.get("compatibility_warning"):
            out.append(f"> [!WARNING]\n> {eval_result['compatibility_warning']}\n")
            
        out.append("| المؤشر البيداغوجي وعناصر الإجابة الوزارية | العلامة المجزأة | العلامة الممنوحة | الملاحظة والتقييم |")
        out.append("| :--- | :---: | :---: | :--- |")
        
        for step in eval_result.get("itemized_steps", []):
            out.append(f"| {step['step']} | {step['points_allocated']:.2f} ن | **{step['points_earned']:.2f} ن** | {step['status']} |")
            
        out.append(f"| **المجموع النهائي للفرع** | **{eval_result['max_points']:.2f} ن** | **{eval_result['score_earned']:.2f} ن** | **النسبة: {eval_result['percentage']}%** |\n")
        
        if eval_result.get("deductions"):
            out.append("#### ⚠️ أسباب خصم النقاط والتوجيه البيداغوجي للتلميذ:")
            for d in eval_result["deductions"]:
                out.append(f"- {d}")
        else:
            out.append("✨ **إجابة نموذجية ممتازة استوفت كافة مؤشرات الديوان الوطني للامتحانات (علامة كاملة).**")

        if eval_result.get("official_archive_rubrics"):
            out.append("\n#### 🏛️ مقتطفات سلم التنقيط الحقيقي المستخرجة من أرشيف التصحيحات الرسمية (ONEC Corrigés):")
            for arch in eval_result["official_archive_rubrics"]:
                out.append(f"- **{arch['subject']} ({arch['stream']}) - دورة {arch['year']}** [`{arch['file_path']}`]:")
                for st in arch.get("sampled_steps", [])[:4]:
                    out.append(f"  - `{st['points']:.2f} ن`: {st['step_criterion']}")
            
        return "\n".join(out)

def run_phase2_demo():
    print("=" * 75)
    print("🚀 تشغيل محرك شبكات التنقيط والتمايز البيداغوجي (ONEC Scoring Engine Demo)")
    print("=" * 75)
    
    engine = ONECScoringEngine()
    
    # Test 1: Out-of-syllabus check (Experimental science asking about Z arithmetic)
    print("\n[الاختبار 1: فحص التمايز بين الشعب ومنع المحاور الخارجة عن المنهاج]")
    warn = engine.verify_stream_compatibility("علوم تجريبية", "أريد حل معادلة باستعمال مبرهنة غوص والقسمة في Z")
    print(f"الشعبة: علوم تجريبية | السؤال: القسمة في Z")
    print(f"النتيجة: {warn}")
    
    # Test 2: Rubric Generation & Grading for Mathematics
    print("\n[الاختبار 2: توليد شبكة تنقيط وتقييم إجابة تلميذ في الرياضيات]")
    q_math = "أثبت أن المعادلة f(x)=0 تقبل حلا وحيدا في المجال [1, 2]"
    rubric_math = engine.generate_rubric(q_math, subject="الرياضيات", stream="علوم تجريبية")
    
    student_ans_incomplete = "حسبت الصور ووجدت f(1) موجبة و f(2) سالبة إذن المعادلة تقبل حلا"
    eval_res = engine.evaluate_student_answer(rubric_math, student_ans_incomplete)
    print(engine.format_rubric_table(eval_res))
    
    # Test 3: Rubric Generation & Complete Grading for Physics
    print("\n[الاختبار 3: تقييم إجابة مستوفاة في العلوم الفيزيائية]")
    q_phys = "بتطبيق القانون الثاني لنيوتن جد المعادلة التفاضلية لسرعة الكرية أثناء السقوط"
    rubric_phys = engine.generate_rubric(q_phys, subject="العلوم الفيزيائية", stream="علوم تجريبية")
    
    student_ans_complete = "الجملة الكرية، المرجع سطحي أرضي عطالي، القوى المؤثرة قوة الثقل وقوة الاحتكاك. بتطبيق القانون الثاني لنيوتن والإسقاط نجد dv/dt + k/m v = g ووحدة السرعة هي m/s"
    eval_phys = engine.evaluate_student_answer(rubric_phys, student_ans_complete)
    print(engine.format_rubric_table(eval_phys))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="محرك شبكات التنقيط والتقويم الوزاري (ONEC)")
    parser.add_argument("--demo", action="store_true", help="تشغيل العرض العملي للمحرك")
    parser.add_argument("--subject", "-sub", type=str, default="الرياضيات", help="المادة")
    parser.add_argument("--stream", "-str", type=str, default="علوم تجريبية", help="الشعبة")
    parser.add_argument("--question", "-q", type=str, help="نص السؤال")
    parser.add_argument("--answer", "-a", type=str, help="إجابة التلميذ المراد تقييمها")
    
    args = parser.parse_args()
    
    if args.demo or not args.question:
        run_phase2_demo()
    else:
        eng = ONECScoringEngine()
        rub = eng.generate_rubric(args.question, subject=args.subject, stream=args.stream)
        ans = args.answer or ""
        ev = eng.evaluate_student_answer(rub, ans)
        print(eng.format_rubric_table(ev))
