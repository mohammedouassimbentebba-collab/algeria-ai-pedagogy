# -*- coding: utf-8 -*-
"""
Algerian Student AI Pedagogical Tutor & Interactive Simulator
An interactive runner implementing the 6-Phase Algerian Pedagogical Engine:
- Socratic Scaffolding (Mollick 2023)
- Ministerial Terminology Enforcement (ONEC/National Glossary)
- BAC Question & Scoring Rubric Retrieval (2017-2026 Archive)
- Growth Mindset Feedback (Dweck & Ericsson)
- Active Recall & Spaced Repetition (Dunlosky & Ebbinghaus)
"""

import os
import sys
import json
import re
import argparse
from typing import Dict, Any, List, Optional, Tuple

sys.stdout.reconfigure(encoding='utf-8')

# Import query functions from query_bac
try:
    from query_bac import search_bac, deep_text_search, find_paired_file
except ImportError:
    # Fallback to local import
    import importlib.util
    spec = importlib.util.spec_from_file_location("query_bac", os.path.join(os.path.dirname(__file__), "query_bac.py"))
    qb = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(qb)
    search_bac = qb.search_bac
    deep_text_search = qb.deep_text_search
    find_paired_file = qb.find_paired_file

# Import Phase 6 Instruction, Summarization & Retention Engine
try:
    from instruction_summarization_engine import (
        explain_concept_pck,
        apply_macro_rules_arabic,
        generate_compte_rendu_critique,
        generate_memory_palace,
        build_concept_map_mermaid
    )
except ImportError:
    import importlib.util
    spec_p6 = importlib.util.spec_from_file_location("instruction_summarization_engine", os.path.join(os.path.dirname(__file__), "instruction_summarization_engine.py"))
    ise = importlib.util.module_from_spec(spec_p6)
    spec_p6.loader.exec_module(ise)
    explain_concept_pck = ise.explain_concept_pck
    apply_macro_rules_arabic = ise.apply_macro_rules_arabic
    generate_compte_rendu_critique = ise.generate_compte_rendu_critique
    generate_memory_palace = ise.generate_memory_palace
    build_concept_map_mermaid = ise.build_concept_map_mermaid

# Mapping forbidden terms to official Algerian replacements
FORBIDDEN_TERMS_MAP = {
    r"نظرية\s+القيمة\s+الوسطية": "مبرهنة القيم المتوسطة (Théorème des valeurs intermédiaires)",
    r"نظرية\s+القيمة\s+الوسطى": "مبرهنة القيم المتوسطة (M.Q.M)",
    r"المشتق\b": "الدالة المشتقة (Fonction dérivée) أو العدد المشتق",
    r"الدوال\s+المثلثية\s+العكسية": "غير مبرمجة في البكالوريا الجزائرية (يُمنع استخدامها)",
    r"المصفوفات": "غير مبرمجة في البكالوريا (مبرمجة في السنة الأولى جامعي LMD)",
    r"المحددات": "غير مبرمجة في البكالوريا (خاصة بالتعليم الجامعي)",
    r"المعادلات\s+التفاضلية\s+من\s+الدرجة\s+الثانية": "غير مبرمجة في البكالوريا للطور الثانوي",
    r"تكامل\s+بالكسور\s+الجزئية": "تفكيك الكسور إلى عناصر بسيطة (Décomposition en éléments simples)",
    r"التكامل\s+بالتعويض": "المكاملة بالتجزئة أو وضع متغير مساعد وفق المنهاج",
    r"حساب\s+المثلثات": "التحويلات النقطية أو الحساب الشعاعي والأعداد المركبة",
    r"الرقم\s+الهيدروجيني": "درجة الـ pH أو الـ pH (المصطلح الرسمي)",
    r"(أوجد|احسب|حساب|إيجاد|قيمة)\s+ص\b": "جد قيمة y أو f(x) (الترميز اللاتيني الصارم y بدلاً من ص)",
    r"(أوجد|احسب|حساب|إيجاد|قيمة)\s+س\b": "جد قيمة x (الترميز اللاتيني الصارم x بدلاً من س)",
    r"المتجهات": "الأشعة (Les vecteurs) أو الحساب الشعاعي"
}

def check_forbidden_terms(text: str) -> List[Tuple[str, str]]:
    """Scan student text for non-Algerian terms and suggest official replacements."""
    flagged = []
    for pattern, replacement in FORBIDDEN_TERMS_MAP.items():
        if re.search(pattern, text):
            match = re.search(pattern, text).group(0)
            flagged.append((match, replacement))
    return flagged

def identify_subject_and_topic(text: str) -> Tuple[Optional[str], Optional[str]]:
    """Detect the relevant subject and topic from student input with domain priority."""
    clean_t = text.lower()
    
    # Check specific high-priority domains first
    if any(k in clean_t for k in ["cdio", "compte-rendu tp", "incertitude", "pfe", "1082", "turnitin", "mesrs", "canevas"]):
        return "التعليم الجامعي والمدارس العليا", "تعليم جامعي"
    if any(k in clean_t for k in ["sadt", "توافق", "h7/g6", "خلوص", "تفاوت", "رسم التعاريف"]):
        return "الهندسة الميكانيكية", "تحليل وظيفي وتوافقات"
    if any(k in clean_t for k in ["ميزانية وظيفية", "frng", "bfr", "tn", "scf", "اهتلاك", "تسيير محاسبي"]):
        return "تسيير محاسبي ومالي", "ميزانية وظيفية"
    if any(k in clean_t for k in ["مقاصد", "ربا", "ربا الفضل", "ربا النسيئة", "أحكام وفوائد", "إسلامية", "شريعة"]):
        return "العلوم الإسلامية", "مقاصد ومعاملات"
    if any(k in clean_t for k in ["ethics in business", "counterfeiting", "guided essay", "topic 1", "english", "corruption"]):
        return "اللغة الإنجليزية", "guided essay"
    if any(k in clean_t for k in ["compte-rendu", "amorce", "texte d'histoire", "visée communicative"]):
        return "اللغة الفرنسية", "compte-rendu"
    if any(k in clean_t for k in ["استقصاء", "جدلية", "أطروحة", "فلسف", "سؤال علمي", "فرضية"]):
        return "الفلسفة", "استقصاء وجدل"
    if any(k in clean_t for k in ["حرب باردة", "مؤتمر", "صومام", "ثورة", "استعمار", "مقال تاريخي", "شخصية", "عالم متقدم", "تواريخ"]):
        return "التاريخ_والجغرافيا", "تاريخ وجغرافيا"
    if any(k in clean_t for k in ["شعر", "قصيدة", "إعراب", "صورة بيانية", "استعارة", "تلخيص", "بناء فكري", "بناء لغوي", "اتساق"]):
        return "اللغة العربية", "بناء فكري ولغوي"
        
    # High priority for natural sciences
    if any(k in clean_t for k in ["وثيقة", "ركيزة", "إنزيم", "بروتين", "مسعى علمي", "استدلال", "مناعة", "مشبك", "استنساخ", "ترجمة", "بلعمة", "adn", "arn"]):
        return "علوم_الطبيعة_والحياة", "مسعى علمي واستغلال وثائق"
        
    # High priority for physics mechanics and circuits
    if any(k in clean_t for k in ["قذيفة", "نيوتن", "سقوط", "دارة", "مكثفة", "وشيعة", "حقل الجاذبية", "ناقلية", "معايرة", "نووي", "أسترة", "ميكانيك"]):
        return "العلوم_الفيزيائية", "ميكانيك ودارات"
        
    # Math analysis and algebra
    if any(k in clean_t for k in ["قيم متوسطة", "قيمة وسط", "مماس", "انعطاف", "تراجع", "f(x)", "موافقات", "بيزو", "غوص", "pgcd", "دالة", "متتالية", "تكامل", "نهاية", "مشتق", "مركب", "احتمال"]):
        return "الرياضيات", "تحليل وجبر"
        
    return None, None

def generate_socratic_response(student_prompt: str, stream: str = "علوم تجريبية") -> Dict[str, Any]:
    """Process student input and generate an official pedagogical response."""
    
    # 1. Terminology Interception
    flagged_terms = check_forbidden_terms(student_prompt)
    
    # 2. Identify Subject & Topic
    subject, topic = identify_subject_and_topic(student_prompt)
    
    # 3. BAC Archive Retrieval
    bac_references = []
    if subject:
        # Search for matching BAC questions
        bac_references = search_bac(
            subject=subject.replace("_", " "),
            stream=stream,
            query=topic or student_prompt,
            limit=2
        )
        if not bac_references and topic:
            # Fallback to topic search
            bac_references = deep_text_search(topic, limit=2)

    # 4. Synthesize Socratic Dialogue
    response = {
        "student_input": student_prompt,
        "stream": stream,
        "subject_detected": subject,
        "topic_detected": topic,
        "terminology_flags": flagged_terms,
        "bac_matches": bac_references,
        "pedagogical_stages": {}
    }
    
    # Stage 1: Terminology Alert (if any)
    if flagged_terms:
        term_alerts = []
        for wrong, right in flagged_terms:
            term_alerts.append(f"تنبيه بيداغوجي وزاري: مصطلح «{wrong}» غير معتمد في المنهاج الجزائري وبكالوريا (ONEC). المصطلح الوطني الرسمي الإلزامي هو: «{right}».")
        response["pedagogical_stages"]["terminology_alert"] = term_alerts
        
    # Stage 2: Socratic Guidance (Mollick Protocol)
    # Never dump full answers; provide guidance, strategy praise, and intermediate steps
    guidance = []
    guidance.append("مرحباً بك يا بني/بنيتي في رحاب التميز البيداغوجي الجزائري.")
    guidance.append("أحيي فيك هذه المبادرة والسعي لفهم البنية العميقة للسؤال، فهذا هو مسار التفوق في شهادة البكالوريا وبناء العضلات الفكرية ومهارات الاستدلال.")
    guidance.append("لن أعطيك الحل الجاهز لأن الحل السريع يمنع بناء الملكة العلمية، بل سأقودك خطوة بخطوة وفق شبكة التقييم الوزارية:")
    
    q_low = student_prompt.lower()
    
    if subject == "الرياضيات":
        if "قيم متوسطة" in q_low or "f(x)" in q_low or "حلا" in q_low:
            guidance.append("• الخطوة الأولى (0.25 ن): طبق مبرهنة القيم المتوسطة (م.ق.م) واذكر صراحة أن الدالة مستمرة ورتيبة تماماً على المجال المحدد.")
            guidance.append("• الخطوة الثانية (0.25 ن): احسب الصورتين f(a) و f(b) وتأكد من أن جداءهما سالب f(a) × f(b) < 0.")
            guidance.append("• الخطوة الثالثة (0.25 ن): صغ الاستنتاج الرسمي والتفسير البياني: المنحنى (Cf) يقطع محور الفواصل في نقطة وحيدة فاصلتها محصورة في المجال.")
        elif "بيزو" in q_low or "غوص" in q_low or "z" in q_low or "pgcd" in q_low:
            guidance.append("• الخطوة الأولى (0.50 ن): احسب القاسم المشترك الأكبر PGCD باستعمال خوارزمية إقليدس للقسمة الإقليدية.")
            guidance.append("• الخطوة الثانية (0.50 ن): بيّن وجود حلول للمعادلة في Z بتطبيق مبرهنة بيزو ثم استخرج حلاً خاصاً.")
            guidance.append("• الخطوة الثالثة (0.50 ن): طبق مبرهنة غوص لإيجاد الحل العام بدلالة العدد الصحيح k والموافقات في Z.")
        else:
            guidance.append("• الخطوة المنهجية: فكك المسألة الرياضية إلى شروط المبرهنة، وحساب العبارات الجبرية، والتحقق من النتيجة النهائية.")
            
    elif subject == "علوم_الطبيعة_والحياة":
        guidance.append("• الخطوة الأولى (المسعى العلمي واستغلال الوثيقة): ابدأ بالتعريف الدقيق بالوثيقة («تمثل الوثيقة... حيث نلاحظ...»).")
        guidance.append("• الخطوة الثانية (التحليل بالمؤشرات): قسّم المعطيات إلى شروط تجريبية ودلالتها الحيوية («مما يدل على...»).")
        guidance.append("• الخطوة الثالثة (الاستنتاج الجزئي): استخرج المعلومة المستهدفة مباشرة وبصياغة مركزة تفيد التركيب النهائي.")
        
    elif subject == "العلوم_الفيزيائية":
        guidance.append("• الخطوة الأولى (التأسيس الفيزيائي): حدد بدقة الجملة المدروسة والمرجع العطالي السطحي الأرضي.")
        guidance.append("• الخطوة الثانية (القوى وقوانين الحركة): اذكر الشروط الابتدائية ثم طبق القانون الثاني لنيوتن بالإسقاط على المحاور.")
        guidance.append("• الخطوة الثالثة (المعادلة التفاضلية): استخرج المعادلة التفاضلية للحركة ورتبها بدلالة المتغير الفيزيائي المطلوب.")
        
    elif subject == "اللغة العربية":
        guidance.append("• الخطوة الأولى (البناء الفكري وقواعد التلخيص): التزم بالقواعد الثلاث للتلخيص المعرفي: الحذف للزوائد، والتعميم للأمثلة، وإعادة البناء التركيبي.")
        guidance.append("• الخطوة الثانية (حجم التلخيص): اضبط حجم الملخص في حدود ربع النص أو ثلث النص تقريباً بأسلوبك الشخصي مع تجنب النقل السطحي للأفكار.")
        
    elif subject == "الفلسفة":
        guidance.append("• الخطوة الأولى (طرح المشكلة): صغ مدخلاً وظيفياً للموضوع، ثم اعرض فكرة شائعة ونقيضها وضبط المشكلة بصيغة الدفاع (استقصاء بالوضع).")
        guidance.append("• الخطوة الثانية (محاولة حل المشكلة): اعرض أولاً منطق الأطروحة ومسلماتها، ثم ادعمها بالدفاع عنها بحجج شخصية ومذاهب فلسفية، وانقد خصوم الأطروحة نقد منطق وحجة.")
        guidance.append("• الخطوة الثالثة (حل المشكلة): أكد في الخاتمة على مشروعية الدفاع وصحة الأطروحة ووجوب الأخذ بها.")
        
    elif subject == "اللغة الفرنسية":
        guidance.append("• Étape 1 (L'Amorce): Rédigez l'accroche complète (Titre, auteur, source, date, thème et visée communicative) pour réussir le compte-rendu objectif.")
        guidance.append("• Étape 2 (Résumé des idées): Condensez les idées principales au discours indirect en utilisant des verbes introducteurs avec une reformulation personnelle rigoureuse.")
        
    elif subject == "اللغة الإنجليزية":
        guidance.append("• Step 1 (Topic sentence): State clearly the central claim for Topic 1 Guided essay regarding Ethics in Business and combating counterfeiting.")
        guidance.append("• Step 2 (Body & Connectors): Expand the given bullet points using logical connectors and conclude with a concise synthesis.")
        
    elif subject == "التاريخ_والجغرافيا":
        guidance.append("• المنهجية المعرفية للتثبيت: طبّق استراتيجية التكرار المتباعد لمقاومة منحنى النسيان لإبنجهاوس، مع توظيف تقنية قصر الذاكرة والربط المكاني وأثر الرسم وفترات الراحة المصغرة.")
        guidance.append("• في ورقة الامتحان: المقال التاريخي يُحرر بإلزامية في شكل عوارض (مطّات) مركزة وليس فقرة إنشائية سردية.")
        
    elif subject == "العلوم الإسلامية":
        guidance.append("• الخطوة الأولى (المقاصد الضرورية): حدد نوع المقصد (حفظ الدين، حفظ النفس، حفظ العقل، حفظ النسل، حفظ المال) ومرتبته التشريعية.")
        guidance.append("• الخطوة الثانية (المعاملات المالية): فرّق بدقة بين ربا الفضل (الزيادة دون تأجيل في المتجانسين) وربا النسيئة (الزيادة المشروطة مقابل التأخير).")
        guidance.append("• الخطوة الثالثة (الأحكام والفوائد): صغ الحكم الشرعي مبدوءاً بـ (وجوب/تحريم) والفائدة بجملة اسمية مفيدة.")
        
    elif subject == "الهندسة الميكانيكية":
        guidance.append("• الخطوة الأولى (التحليل الوظيفي SADT): حدد علبة النشاط الوظيفي A-0 مع بيان المادة الأولية والقيمة المضافة ومعطيات التحكم.")
        guidance.append("• الخطوة الثانية (التوافقات): حدد نظام التوافق H7/g6 واستخرج الانحرافات العلوية والسفلية لحساب الخلوص الأقصى والخلوص الأدنى ونوع التوافق.")
        
    elif subject == "تسيير محاسبي ومالي":
        guidance.append("• الخطوة الأولى (الميزانية الوظيفية): رتب كتل الميزانية وفق النظام المحاسبي المالي SCF إلى موارد ثابتة واستخدامات ثابتة وأصول وخصوم متداولة.")
        guidance.append("• الخطوة الثانية (مؤشرات التوازن المالي): احسب رأس المال العامل الصافي الإجمالي FRNG = الموارد الثابتة - الاستخدامات الثابتة، واحتياج رأس المال BFR، والخزينة الصافية TN = FRNG - BFR.")
        
    elif subject == "التعليم الجامعي والمدارس العليا":
        if "1082" in q_low or "انتحال" in q_low or "pfe" in q_low:
            guidance.append("• الخطوة التنظيمية: راجع نصوص القرار الوزاري 1082 الصادر عن وزارة التعليم العالي والبحث العلمي (MESRS) لمكافحة السرقة العلمية.")
            guidance.append("• المعايير الإلزامية: يجب أن تكون نسبة التشابه أقل من 10%، والاعتماد الصارم على إعادة الصياغة Paraphrase مع التوثيق المرجعي بنمط IEEE أو APA.")
        else:
            guidance.append("• المنهجية الهندسية CDIO: قسّم المشروع إلى مراحله الأربع: Conceive (التصور ودفتر الشروط Cahier des charges)، و Design (التصميم والنمذجة)، و Implement (التنفيذ البرمجي والمادي)، و Operate (التشغيل والتحقق).")
            guidance.append("• في تقرير العمل المخبري (Compte-rendu TP): التزم بحساب الارتيابات بالتفاضل اللوغاريتمي ومقارنة التباعد النسبي مع الثوابت النظرية.")
    else:
        guidance.append("• الخطوة المنهجية: فكك السؤال إلى أركانه الأساسية وفق التدرج المعتمد في المنهاج الجزائري الرسمي وشبكات تقييم الامتحانات الوطنية.")
        
    response["pedagogical_stages"]["socratic_scaffolding"] = guidance
    
    # Stage 3: BAC Official Grounding
    bac_grounding = []
    if bac_references:
        bac_grounding.append("📌 هذا النمط من الأسئلة ورد حرفياً في مواضيع البكالوريا الرسمية السابقة:")
        for b in bac_references:
            bac_grounding.append(f"   • {b.get('subject')} | دورة {b.get('year')} ({b.get('stream')}) - الملف: {b.get('file_path')}")
            paired = find_paired_file(b)
            if paired:
                bac_grounding.append(f"     🔗 التصحيح وسلم التنقيط الرسمي (ONEC): {paired}")
    response["pedagogical_stages"]["bac_grounding"] = bac_grounding
    
    # Stage 4: Active Recall Question (Dunlosky & Karpicke)
    active_recall = {
        "question": f"سؤال التثبيت والاسترجاع النشط الفوري: ما هي الخطوة الصارمة التي إذا نسيتها في ورقة إجابتك تفقد 0.5 نقطة في سلم تنقيط {subject or 'البكالوريا'}؟",
        "spaced_schedule": "راجع إجابة هذا المفهوم بعد: 20 دقيقة، ثم غداً صباحاً (اليوم 1)، ثم بعد 3 أيام لمقاومة منحنى النسيان لإبنجهاوس."
    }
    response["pedagogical_stages"]["active_recall"] = active_recall

    # Stage 5: Phase 6 Specialized Modules (PCK Transmission, Macro-Summarization, Memory Palace)
    # Check for concept transmission triggers
    if any(k in q_low for k in ["اشرح", "مكثفة", "قيم متوسطة", "إنزيم", "دارة", "شحن"]):
        c_key = "شحن_المكثفة" if ("مكثفة" in q_low or "دارة" in q_low) else ("مبرهنة_القيم_المتوسطة" if "قيم متوسطة" in q_low else ("النشاط_الإنزيمي" if "إنزيم" in q_low else student_prompt))
        response["pedagogical_stages"]["pck_explanation"] = explain_concept_pck(c_key, custom_name=student_prompt)
        
    # Check for text summarization triggers
    if any(k in q_low for k in ["تلخيص", "لخص", "résumé"]):
        sample_txt = "قام الاستعمار بتدمير القرى، ومصادرة الأراضي، وفرض الضرائب، وممارسة شتى أنواع التنكيل. غير أن الشعب الجزائري التف حول ثورته وقدم التضحيات حتى حقق النصر المبين."
        response["pedagogical_stages"]["discourse_summarization"] = apply_macro_rules_arabic(sample_txt)
    elif "compte-rendu" in q_low or "compte rendu" in q_low:
        sample_fr = "Le peuple algérien s'est soulevé contre la colonisation pour recouvrer sa pleine liberté et son indépendance nationale."
        response["pedagogical_stages"]["compte_rendu"] = generate_compte_rendu_critique(sample_fr, author="Historien", source="Archives Nationales")

    # Check for memory palace and retention triggers
    if any(k in q_low for k in ["حفظ", "تواريخ", "قصر ذاكرة", "نسيان", "تثبيت", "تاريخ"]):
        response["pedagogical_stages"]["memory_palace"] = generate_memory_palace()
    
    return response

def print_tutor_interaction(res: Dict[str, Any]):
    print("\n" + "=" * 75)
    print("🎓 المحاكي البيداغوجي الذكي للتلميذ الجزائري (Algerian AI Pedagogical Mentor)")
    print("=" * 75)
    print(f"👤 سؤال التلميذ: \"{res['student_input']}\" (الشعبة: {res['stream']})")
    print("-" * 75)
    
    stages = res.get("pedagogical_stages", {})
    
    # 1. Terminology
    if "terminology_alert" in stages:
        print("\n⚠️  [المحطة 1: ضبط المصطلحات الوطنية الرسمية]")
        for alert in stages["terminology_alert"]:
            print(f"   {alert}")
            
    # 2. Socratic Scaffolding
    if "socratic_scaffolding" in stages:
        print("\n🧭 [المحطة 2: التوجيه السقراطي وعقلية النمو (Mollick & Dweck)]")
        for line in stages["socratic_scaffolding"]:
            print(f"   {line}")
            
    # 3. BAC Grounding
    if "bac_grounding" in stages and stages["bac_grounding"]:
        print("\n🏛️  [المحطة 3: الربط بالأرشيف الوزاري الرسمي وشبكة التنقيط (ONEC)]")
        for line in stages["bac_grounding"]:
            print(f"   {line}")
            
    # 4. Active Recall
    if "active_recall" in stages:
        print("\n🧠 [المحطة 4: الاسترجاع النشط والتكرار المتباعد (Dunlosky & Ebbinghaus)]")
        print(f"   ❓ {stages['active_recall']['question']}")
        print(f"   ⏳ {stages['active_recall']['spaced_schedule']}")
        
    # 5. Phase 6: PCK Explanation
    if "pck_explanation" in stages:
        pck = stages["pck_explanation"]
        print("\n🔬 [المحطة 5: الشرح الفائق ومستويات PCK الثلاثة (Shulman 1986)]")
        print(f"   📌 المفهوم: {pck.get('concept_name')}")
        print(f"   1️⃣ التشبيه الحسي: {pck.get('analogical_anchor')}")
        print(f"   2️⃣ الصياغة الرمزية الصارمة: {pck.get('formal_symbolic')}")
        print(f"   🎓 تحدي التلمذة (Protégé): {pck.get('protege_challenge')}")

    # 6. Phase 6: Summarization
    if "discourse_summarization" in stages:
        ds = stages["discourse_summarization"]
        print("\n✍️ [المحطة 6: التلخيص الدلالي وفق قواعد ماكرو (Kintsch 1978)]")
        print(f"   📝 النص الملخص: {ds.get('summary_text')}")
        print(f"   📊 نسبة الضغط: {ds.get('compression_ratio'):.1%}")

    if "compte_rendu" in stages:
        cr = stages["compte_rendu"]
        print("\n🇫🇷 [المحطة 6-ب: Le Compte-Rendu Critique (ONEC)]")
        print(f"   {cr.get('accroche')}")
        print(f"   {cr.get('resume_analytique')}")

    # 7. Phase 6: Memory Palace
    if "memory_palace" in stages:
        mp = stages["memory_palace"]
        print("\n🏰 [المحطة 7: قصر الذاكرة المكاني وأثر الرسم وإعادة التشغيل (Krokos 2019 & NIH)]")
        print(f"   📍 القصر: {mp.get('palace_name')} ({mp.get('stations_count')} محطات)")
        print(f"   🧠 وقفة الـ 20 ثانية (Waking Replay): {mp['waking_replay_protocol']['student_action']}")
        
    print("=" * 75 + "\n")

def run_demo():
    print("\n" + "=" * 75)
    print("🚀 بدء العرض التجريبي للمحاكي البيداغوجي عبر 3 سيناريوهات واقعية للطلاب")
    print("=" * 75)
    
    demo_queries = [
        {
            "query": "كيف أطبق نظرية القيمة الوسطية لحساب حل المعادلة f(x)=0؟",
            "stream": "علوم تجريبية"
        },
        {
            "query": "كيف أحلل الوثيقة في مادة علوم الطبيعة والحياة لاختبار تركيب البروتين؟",
            "stream": "علوم تجريبية"
        },
        {
            "query": "أريد حل تمرين السقوط الشاقولي وقوانين نيوتن وحساب ص والسرعة الحدية",
            "stream": "رياضيات وتقني رياضي"
        }
    ]
    
    for dq in demo_queries:
        res = generate_socratic_response(dq["query"], stream=dq["stream"])
        print_tutor_interaction(res)

def main():
    parser = argparse.ArgumentParser(description="المحاكي البيداغوجي الذكي للتلميذ الجزائري")
    parser.add_argument("--demo", action="store_true", help="تشغيل عرض تجريبي حي للسيناريوهات")
    parser.add_argument("--query", "-q", type=str, help="سؤال التلميذ")
    parser.add_argument("--stream", "-s", type=str, default="علوم تجريبية", help="الشعبة")
    
    args = parser.parse_args()
    
    if args.demo:
        run_demo()
    elif args.query:
        res = generate_socratic_response(args.query, stream=args.stream)
        print_tutor_interaction(res)
    else:
        # Interactive mode
        print("\n" + "=" * 70)
        print("أهلاً بك في المحاكي البيداغوجي الجزائري. اكتب سؤالك، أو اكتب 'exit' للخروج:")
        print("=" * 70)
        while True:
            try:
                inp = input("\n📝 سؤالك: ").strip()
                if not inp or inp.lower() in ["exit", "quit", "خروج"]:
                    break
                res = generate_socratic_response(inp)
                print_tutor_interaction(res)
            except (KeyboardInterrupt, EOFError):
                break

if __name__ == "__main__":
    main()
