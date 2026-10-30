# -*- coding: utf-8 -*-
"""
Cognitive Learning & Pedagogy Operational Engine (Phase 3)
Implements practical cognitive foundations:
- Interleaved Practice Problem Generator (Rohrer & Taylor 2007)
- Deep Structure vs Surface Features Scaffold (Chi et al. 1981)
- Active Recall & Spaced Repetition Timetable (Dunlosky 2013 & Ebbinghaus 1885)
- Hierarchical Concept Mapping via Mermaid (Novak 2008 & Fernandes 2018)
"""

import os
import sys
import json
import random
import argparse
from typing import Dict, Any, List, Optional

sys.stdout.reconfigure(encoding='utf-8')

# Syllabus Unit Pools for Interleaving Practice
INTERLEAVED_POOLS = {
    "الرياضيات": [
        {"topic": "الدوال العددية وحساب النهايات", "deep_law": "المقارنة والتزايد المقارن", "sample": "احسب نهاية f(x) عند +∞ وبين وجود مستقيم مقارب مائل."},
        {"topic": "المتتاليات العددية والبرهان بالتراجع", "deep_law": "الاستدلال الاستقرائي ومبرهنة التقارب للمتتاليات الرتيبة والمحدودة", "sample": "برهن بالتراجع أن Un > 1 ثم ادرس اتجاه تغير المتتالية واستنتج تقاربها."},
        {"topic": "مبرهنة القيم المتوسطة", "deep_law": "الاتصال الموضعي والرتابة في المجالات المغلقة", "sample": "بيّن أن المعادلة f(x)=0 تقبل حلاً وحيداً α في المجال [1.2, 1.3]."},
        {"topic": "الاحتمالات والمتغيرات العشوائية", "deep_law": "قانون الاحتمال الكلي وتساوي الفرص", "sample": "احسب احتمال الحصول على كرتين من نفس اللون، وعرف قانون احتمال المتغير العشوائي X."},
        {"topic": "الأعداد المركبة والتحويلات النقطية", "deep_law": "التمثيل الهندسي للعمليات الجبرية في المستوي المركب", "sample": "اكتب العدد المركب z على الشكل الأسي، وحدد طبيعة التحويل النقطي وزاويته ونسبته."}
    ],
    "العلوم_الفيزيائية": [
        {"topic": "الميكانيك والسقوط الشاقولي", "deep_law": "القانون الثاني لنيوتن ومبدأ الفعل ورد الفعل", "sample": "بتطبيق القانون الثاني لنيوتن في مرجع عطالي جد المعادلة التفاضلية للسرعة."},
        {"topic": "الظواهر الكهربائية (ثنائي القطب RC)", "deep_law": "قانون جمع التوترات وانحفاظ الشحنة الكهربائية", "sample": "اكتب المعادلة التفاضلية لتوتر المكثفة uc(t) وأثبت عبارة ثابت الزمن τ بالتحليل البعدي."},
        {"topic": "تطور جملة كيميائية (أحماض وأسس)", "deep_law": "قانون التوازن الكيميائي والتبادل البروتوني (برونشتد)", "sample": "احسب النسبة النهائية للتقدم τf وحدد كسر التفاعل عند التوازن وثابت الحموضة pKa."},
        {"topic": "التحولات النووية والنشاط الإشعاعي", "deep_law": "قانونا الصودي لانحفاظ الشحنة والكتلة والتكافؤ طاقة-كتلة", "sample": "اكتب معادلة التفكك النووي واحسب طاقة الربط لكل نكليون للنواة الناتجة."}
    ],
    "علوم_الطبيعة_والحياة": [
        {"topic": "آليات تركيب البروتين", "deep_law": "التعبير المورثي وتدفق المعلومات الوراثية (ADN -> ARNm -> بروتين)", "sample": "اشرح في نص علمي مهيكل دور مختلف الجزيئات في مرحلتي الاستنساخ والترجمة."},
        {"topic": "النشاط الإنزيمي للبروتينات", "deep_law": "التحفيز الحيوي والتكامل البنيوي للموقع الفعال", "sample": "حلل منحنى تغيرات السرعة الابتدائية للتفاعل بدلالة تركيز مادة التفاعل وفسر التأثير التثبيطي."},
        {"topic": "المناعة والدفاع عن الذات", "deep_law": "التعرف النوعي والتكامل بين محدد المستضد والمستقبلات الغشائية", "sample": "استغل الوثيقة لتبيان آلية الانتقاء النسيلي للمفاويات B والتمايز إلى خلايا بلازمية مفرزة."}
    ]
}

DEEP_STRUCTURE_TEMPLATES = {
    "نيوتن": {
        "governing_law": "القانون الثاني لنيوتن في الميكانيك الكلاسيكي (ΣF_ext = m · a_G)",
        "assumptions": "مرجع سطحي أرضي نعتبره غاليلياً ومزوداً بمعلم شاقولي، كتلة الجملة ثابتة، القوى الخارجية: الثقل وقوة الاحتكاك المائع ومقاومة الهواء.",
        "algebraic_flow": "1. إسقاط العلاقة الشعاعية: P - f = m · (dv/dt)\n2. التعويض: m·g - k·v = m·(dv/dt)\n3. القسمة على m والترتيب: dv/dt + (k/m)v = g\n4. تحديد السرعة الحدية عند dv/dt = 0: v_lim = (m·g)/k"
    },
    "قيم متوسطة": {
        "governing_law": "مبرهنة القيم المتوسطة (Théorème des Valeurs Intermédiaires) للتحليل الرياضي",
        "assumptions": "دالة عددية معرفة ومستمرة ورتيبة تماماً على مجال مغلق [a, b] بحيث f(a) و f(b) من إشارتين مختلفتين.",
        "algebraic_flow": "1. التحقق من الاستمرارية على المجال المغلق.\n2. التحقق من الرتابة التامة (إشارة المشتقة ثابتة لا تنعدم على المجال).\n3. الحساب العددي الدقيق للصورة f(a) والصورة f(b).\n4. جداء الصورتين سالب: f(a) × f(b) < 0.\n5. النتيجة: المعادلة f(x)=0 تقبل حلاً وحيداً α في المجال ]a, b[."
    },
    "انحفاظ الطاقة": {
        "governing_law": "مبدأ انحفاظ الطاقة لجملة ميكانيكية معزولة أو غير معزولة (E_initial + E_reçue - E_cédée = E_finale)",
        "assumptions": "تحديد الجملة الميكانيكية بدقة (جسم، جسم + أرض، جسم + نابض) لتحديد ما إذا كانت طاقة الثقل أو المرونة طاقة كامنة داخلية أم عمل قوة خارجية.",
        "algebraic_flow": "1. كتابة الحصيلة الطاقوية بين الموضعين A و B.\n2. كتابة معادلة انحفاظ الطاقة الحرفية.\n3. تعويض عبارات الطاقة: Ec = 1/2 m·v² و Epp = m·g·h.\n4. استخراج المجهول حرفياً قبل الحساب العددي والتحقق من تجانس الوحدات."
    }
}

class CognitiveLearningEngine:
    """Core educational engine for Phase 3 cognitive operationalization."""

    @staticmethod
    def generate_interleaved_set(subject: str, stream: str, count: int = 4) -> Dict[str, Any]:
        """Generate an interleaved problem set forcing deep structure discrimination."""
        
        # Normalize subject key
        target_sub = "الرياضيات"
        if "فيزيا" in subject:
            target_sub = "العلوم_الفيزيائية"
        elif "طبيع" in subject or "علوم" in subject and "فيزيا" not in subject:
            target_sub = "علوم_الطبيعة_والحياة"
            
        pool = INTERLEAVED_POOLS.get(target_sub, INTERLEAVED_POOLS["الرياضيات"])
        selected = random.sample(pool, min(count, len(pool)))
        
        problems = []
        for i, item in enumerate(selected, 1):
            problems.append({
                "number": i,
                "topic": item["topic"],
                "deep_principle": item["deep_law"],
                "problem_text": item["sample"],
                "diagnostic_challenge": f"قبل البدء بالحساب: ما هو القانون الكلي الحاكم لمسألة التمرين {i} وما هي الشروط الأولية لتطبيقه؟"
            })
            
        return {
            "subject": target_sub,
            "stream": stream,
            "methodology": "التدريب المتشابك (Interleaved Practice - Rohrer & Taylor 2007)",
            "pedagogical_benefit": "خلط وحدات دراسية متباينة لمنع وهم الكفاءة وتدريب العقل على التشخيص التمييزي للقوانين الحاكمة.",
            "problems": problems
        }

    @staticmethod
    def build_deep_structure_scaffold(problem_keyword: str) -> Dict[str, Any]:
        """Build a 3-layer deep structure representation (Chi et al. 1981)."""
        key = "نيوتن"
        if "قيم" in problem_keyword or "توسط" in problem_keyword or "دال" in problem_keyword:
            key = "قيم متوسطة"
        elif "طاق" in problem_keyword or "انحفاظ" in problem_keyword:
            key = "انحفاظ الطاقة"
            
        data = DEEP_STRUCTURE_TEMPLATES.get(key, DEEP_STRUCTURE_TEMPLATES["نيوتن"])
        
        return {
            "keyword": problem_keyword,
            "concept_category": key,
            "cognitive_foundation": "تفكيك البنية العميقة مقابل المظاهر السطحية (Chi, Feltovich & Glaser 1981)",
            "layer_1_governing_principle": data["governing_law"],
            "layer_2_boundary_assumptions": data["assumptions"],
            "layer_3_algebraic_steps": data["algebraic_flow"]
        }

    @staticmethod
    def build_active_recall_challenge(concept_name: str, subject: str) -> Dict[str, Any]:
        """Construct an Active Recall & Spaced Repetition protocol."""
        return {
            "concept": concept_name,
            "subject": subject,
            "protocol": "أثر الاختبار والاسترجاع المجهد (Dunlosky 2013 & Roediger 2006)",
            "closed_recall_prompt": f"⚠️ توجيه بيداغوجي إلزامي: أغلق ورقة الدرس واصرف عينك عن الشاشة، واكتب الآن على ورقة بيضاء بيدك: ما هي الشروط الدقيقة والمؤشرات الثلاثة لتطبيق «{concept_name}»؟",
            "spaced_schedule": [
                {"interval": "بعد 20 دقيقة", "purpose": "تثبيت الذاكرة العاملة ومقاومة التلاشي اللحظي", "action": "إعادة استرجاع القانون غيباً"},
                {"interval": "بعد 24 ساعة (غداً صباحاً)", "purpose": "مقاومة أول انحدار حاد لمنحنى النسيان لإبنجهاوس", "action": "حل تمرين تطبيقي مصغر في 5 دقائق"},
                {"interval": "بعد 3 أيام (نهاية الأسبوع)", "purpose": "ترسيخ المسار العصبي عبر الاسترجاع المتباعد", "action": "شرح الفكرة لزميل (أثر التلمذة)"},
                {"interval": "بعد أسبوعين", "purpose": "النقل إلى الذاكرة طويلة المدى", "action": "إدراج السؤال ضمن حزمة تدريب متشابكة"}
            ]
        }

    @staticmethod
    def generate_concept_map_mermaid(topic: str, subject: str) -> str:
        """Generate a valid hierarchical concept map in Mermaid syntax (Novak 2008)."""
        clean_topic = topic.strip()
        
        if "دوال" in clean_topic or "رياضيات" in subject:
            return """```mermaid
graph TD
    A["دراسة الدالة العددية f(x)"] -->|"تتطلب تحديد"| B["مجموعة التعريف Df والامتداد"]
    A -->|"تستوجب حساب"| C["النهايات وسلوك الأطراف"]
    C -->|"تحدد هندسياً"| D["المستقيمات المقاربة (مائل/أفقي/عمودي)"]
    A -->|"تقتضي اشتقاق"| E["حساب المشتقة f'(x)"]
    E -->|"دراسة إشارتها تعطي"| F["اتجاه التغير والذروات"]
    F -->|"تُلخص في"| G["جدول التغيرات المعياري"]
    G -->|"تمكّن من تطبيق"| H["مبرهنة القيم المتوسطة وحصر الحلول"]
    H -->|"تتوج بالرسم في"| I["رسم المنحنى البياني (Cf) والمماسات"]
```"""
        elif "فيزيا" in subject or "نيوتن" in clean_topic:
            return """```mermaid
graph TD
    A["تطور جملة ميكانيكية"] -->|"تخضع حصراً لـ"| B["قوانين نيوتن الكلاسيكية"]
    B -->|"تتطلب تحديد"| C["الجملة المدروسة والمرجع العطالي"]
    B -->|"تقتضي جرد"| D["القوى الخارجية المؤثرة (الثقل، الاحتكاك، الرد)"]
    D -->|"تُطبق شعاعياً في"| E["القانون الثاني: ΣF_ext = m·a_G"]
    E -->|"تُسقط على المحور لتنتج"| F["المعادلة التفاضلية للحركة"]
    F -->|"بالتكامل والحل تعطي"| G["المعادلات الزمنية للسرعة والموضع"]
    G -->|"عند النظام الدائم تحدد"| H["السرعة الحدية v_lim وثابت الزمن"]
```"""
        else:
            return """```mermaid
graph TD
    A["المفهوم العلمي الأساسي"] -->|"ينبثق من"| B["المبدأ الكوني الحاكم"]
    A -->|"يتطلب شروطاً محددة"| C["الشروط التجريبية والحدية"]
    B -->|"يُترجم رياضياً إلى"| D["العلاقات والقوانين الوظيفية"]
    C -->|"تُختبر عبر"| E["المسعى العلمي واستغلال الوثائق"]
    D -->|"تُتوج بـ"| F["الاستنتاج والتركيب النهائي"]
```"""

def run_phase3_demo():
    print("=" * 75)
    print("🚀 تشغيل محرك الأسس المعرفية والبيداغوجية (Cognitive Learning Engine Demo)")
    print("=" * 75)
    
    engine = CognitiveLearningEngine()
    
    # 1. Interleaved Practice
    print("\n[المحطة 1: توليد حزمة تدريب متشابك - Rohrer & Taylor 2007]")
    inter = engine.generate_interleaved_set(subject="الرياضيات", stream="علوم تجريبية", count=3)
    print(f"المادة: {inter['subject']} | الفلسفة: {inter['methodology']}")
    print(f"الفائدة: {inter['pedagogical_benefit']}\n")
    for p in inter["problems"]:
        print(f"  • تمرين {p['number']}: {p['topic']}")
        print(f"    النص: {p['problem_text']}")
        print(f"    التحدي التشخيصي: {p['diagnostic_challenge']}\n")
        
    # 2. Deep Structure Scaffolding
    print("[المحطة 2: تفكيك البنية العميقة للمسألة - Chi et al. 1981]")
    deep = engine.build_deep_structure_scaffold("نيوتن والسقوط الشاقولي")
    print(f"المفهوم: {deep['concept_category']} | المرجع: {deep['cognitive_foundation']}")
    print(f"• الطبقة 1 (المبدأ الحاكم): {deep['layer_1_governing_principle']}")
    print(f"• الطبقة 2 (الشروط والافتراضات): {deep['layer_2_boundary_assumptions']}")
    print(f"• الطبقة 3 (المسار الجبري والحسابي):\n{deep['layer_3_algebraic_steps']}\n")
    
    # 3. Active Recall & Spaced Repetition
    print("[المحطة 3: بروتوكول الاسترجاع النشط والتكرار المتباعد - Dunlosky & Ebbinghaus]")
    recall = engine.build_active_recall_challenge("مبرهنة القيم المتوسطة", "الرياضيات")
    print(recall["closed_recall_prompt"])
    print("\n📅 جدول التكرار المتباعد المبرمج:")
    for step in recall["spaced_schedule"]:
        print(f"  - {step['interval']}: {step['purpose']} 👈 {step['action']}")
        
    # 4. Concept Map
    print("\n[المحطة 4: الخريطة المفاهيمية الهرمية مع كلمات الربط - Novak 2008]")
    cmap = engine.generate_concept_map_mermaid("دراسة الدوال", "الرياضيات")
    print(cmap)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="محرك الأسس المعرفية والبيداغوجية")
    parser.add_argument("--demo", action="store_true", help="تشغيل العرض العملي لكافة الركائز")
    parser.add_argument("--interleave", action="store_true", help="توليد تدريب متشابك")
    parser.add_argument("--deep", type=str, help="تفكيك البنية العميقة لمسألة")
    parser.add_argument("--recall", type=str, help="توليد تحدي استرجاع نشط وجدول مراجعة")
    parser.add_argument("--map", type=str, help="توليد خريطة مفاهيمية هرمية")
    parser.add_argument("--subject", type=str, default="الرياضيات", help="المادة")
    parser.add_argument("--stream", type=str, default="علوم تجريبية", help="الشعبة")
    
    args = parser.parse_args()
    
    engine = CognitiveLearningEngine()
    
    if args.demo or len(sys.argv) == 1:
        run_phase3_demo()
    elif args.interleave:
        res = engine.generate_interleaved_set(args.subject, args.stream)
        print(json.dumps(res, ensure_ascii=False, indent=2))
    elif args.deep:
        res = engine.build_deep_structure_scaffold(args.deep)
        print(json.dumps(res, ensure_ascii=False, indent=2))
    elif args.recall:
        res = engine.build_active_recall_challenge(args.recall, args.subject)
        print(json.dumps(res, ensure_ascii=False, indent=2))
    elif args.map:
        res = engine.generate_concept_map_mermaid(args.map, args.subject)
        print(res)
