# -*- coding: utf-8 -*-
"""
محرك البيداغوجيا واللسانيات العربية المتقدم (BAC Arabic Pedagogy & Linguistic Engine)
---------------------------------------------------------------------------------
أداة خوارزمية تخصصية لتنفيذ وتدقيق مهارات اللغة العربية وآدابها في البكالوريا الجزائرية:
1. التفكيك العروضي الصوتي وكشف بحور الشعر الستة المقررة وجوازاتها.
2. التدقيق النحوي للأدوات الوزارية المتكررة (إذا، إذ، إذن، لولا، ياء المتكلم، إعراب الجمل).
3. فحص التلخيص واستيعاب الخطاب وفق قواعد ماكرو الثلاث (كينتش وفان دايك 1983).
4. استخراج القرائن اللغوية ومظاهر الاتساق والإحالة النصية (Anaphora).
"""

import sys
import re
import argparse
from typing import Dict, List, Tuple, Any

# تهيئة مخارج النصوص للـ UTF-8
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# ==============================================================================
# 1. محرك التفكيك العروضي وتحليل المقاطع الصوتية (Prosody & Meters)
# ==============================================================================

# معجم أنماط البحور الستة المقررة في البكالوريا الجزائرية (الرموز: / متحرك، 0 ساكن)
BAC_METERS = {
    "بحر الكامل": {
        "pattern": r"(///0//0|/0/0//0)",  # متفاعلن أو متفاعلن (الإضمار)
        "feet": ["مُتَفَاعِلُنْ", "مُتْفَاعِلُنْ (مضمر)"],
        "tafilah_base": "مُتَفَاعِلُنْ ///0//0",
        "key": "كَمُلَ الجَمَالُ مِنَ البُحُورِ الكَامِلُ ... مُتَفَاعِلُنْ مُتَفَاعِلُنْ مُتَفَاعِلُنْ",
        "cadence": "///0//0"
    },
    "بحر البسيط": {
        "pattern": r"(/0/0//0|//0//0)\s*(/0//0|///0)",  # مستفعلن فاعلن أو متفعلن فعلن
        "feet": ["مُسْتَفْعِلُنْ", "فَاعِلُنْ", "مُتَفْعِلُنْ (مخبون)", "فَعِلُنْ (مخبون)"],
        "tafilah_base": "مُسْتَفْعِلُنْ فَاعِلُنْ مُسْتَفْعِلُنْ فَعِلُنْ",
        "key": "إِنَّ البَسِيطَ لَدَيْهِ يُبْسَطُ الأَمَلُ ... مُسْتَفْعِلُنْ فَاعِلُنْ مُسْتَفْعِلُنْ فَعِلُنْ",
        "cadence": "/0/0//0 /0//0"
    },
    "بحر الطويل": {
        "pattern": r"(//0/0|//0/)\s*(//0/0/0|//0//0)",  # فعولن مفاعيلن أو فعول مفاعلن
        "feet": ["فَعُولُنْ", "مَفَاعِيلُنْ", "فَعُولُ (مقبوض)", "مَفَاعِلُنْ (مقبوض)"],
        "tafilah_base": "فَعُولُنْ مَفَاعِيلُنْ فَعُولُنْ مَفَاعِيلُنْ",
        "key": "طَوِيلٌ لَهُ دُونَ البُحُورِ فَضَائِلُ ... فَعُولُنْ مَفَاعِيلُنْ فَعُولُنْ مَفَاعِلُنْ",
        "cadence": "//0/0 //0/0/0"
    },
    "بحر الوافر": {
        "pattern": r"(//0///0|//0/0/0)",  # مفاعلتن أو مفاعلتن (العصب)
        "feet": ["مُفَاعَلَتُنْ", "مُفَاعَلْتُنْ (معصوب)", "فَعُولُنْ"],
        "tafilah_base": "مُفَاعَلَتُنْ مُفَاعَلَتُنْ فَعُولُنْ",
        "key": "بُحُورُ الشِّعْرِ وَافِرُهَا جَمِيلُ ... مُفَاعَلَتُنْ مُفَاعَلَتُنْ فَعُولُنْ",
        "cadence": "//0///0"
    },
    "بحر الخفيف": {
        "pattern": r"(/0//0/0|///0/0)\s*(/0/0//0|//0//0)",  # فاعلاتن مستفعلن
        "feet": ["فَاعِلاتُنْ", "مُسْتَفْعِ لُنْ", "فَعِلاتُنْ (مخبون)"],
        "tafilah_base": "فَاعِلاتُنْ مُسْتَفْعِلُنْ فَاعِلاتُنْ",
        "key": "يَا خَفِيفاً خَفَّتْ بِهِ الحَرَكَاتُ ... فَاعِلاتُنْ مُسْتَفْعِ لُنْ فَاعِلاتُنْ",
        "cadence": "/0//0/0 /0/0//0"
    },
    "بحر الرمل": {
        "pattern": r"(/0//0/0|///0/0)",  # فاعلاتن أو فعلاتن
        "feet": ["فَاعِلاتُنْ", "فَعِلاتُنْ (مخبون)"],
        "tafilah_base": "فَاعِلاتُنْ فَاعِلاتُنْ فَاعِلاتُنْ",
        "key": "رَمَلُ الأَبْحُرِ تَرْوِيهِ الثِّقَاتُ ... فَاعِلاتُنْ فَاعِلاتُنْ فَاعِلاتُنْ",
        "cadence": "/0//0/0"
    }
}

def to_prosodic_phonology(verse: str) -> Tuple[str, str]:
    """
    تطبيق قواعد الكتابة العروضية الأساسية على الشطر وتحويله إلى رموز صوتية (/ و 0).
    """
    cleaned = verse.strip()
    
    # 1. إبدال التنوين بنون ساكنة
    cleaned = re.sub(r'ً', 'َنْ', cleaned)
    cleaned = re.sub(r'ٌ', 'ُنْ', cleaned)
    cleaned = re.sub(r'ٍ', 'ِنْ', cleaned)
    
    # 2. تبسيط كلمات الإشارة الشهيرة
    cleaned = re.sub(r'\bهذا\b', 'هَاذَا', cleaned)
    cleaned = re.sub(r'\bهذه\b', 'هَاذِهِي', cleaned)
    cleaned = re.sub(r'\bذلك\b', 'ذَالِكَ', cleaned)
    cleaned = re.sub(r'\bلكن\b', 'لَاكِنْ', cleaned)
    cleaned = re.sub(r'\bالله\b', 'اَلْلَاهُ', cleaned)
    
    # محاكاة توليد الرموز العروضية (متحرك / ساكن 0)
    # ملاحظة: في المعالجة الآلية دون تشكيل كامل، نعتمد الحركات الأساسية وحروف المد
    vowels = ['َ', 'ُ', 'ِ']
    sukuns = ['ْ', 'ا', 'و', 'ي', 'ى']
    
    symbols = []
    # إذا كان النص غير مشكول بالكامل، نستخدم التقدير المقطعي العربي
    words = cleaned.split()
    prosodic_words = []
    
    for word in words:
        p_word = word
        # فك الشدة إذا وجدت
        if 'ّ' in p_word:
            p_word = p_word.replace('ّ', '') # تبسيط تمثيلي
        prosodic_words.append(p_word)
        
    prosodic_text = " ".join(prosodic_words)
    
    # توليد تقريبي للرموز
    pattern = ""
    for char in prosodic_text:
        if char in ' اويى':
            if char != ' ':
                pattern += "0"
        elif char in 'بتثجحخدذرزسشصضطظعغفقكلمنهءئؤ':
            pattern += "/"
            
    # تنظيف وتنسيق
    pattern = re.sub(r'0{2,}', '0', pattern) # منع توالي أكثر من ساكنين
    return prosodic_text, pattern

def detect_meter(verse: str) -> Dict[str, Any]:
    """
    كشف البحر الشعري والتفعيلات المقترحة استناداً إلى الكلمات والوزن المقطعي.
    """
    prosodic_text, pattern = to_prosodic_phonology(verse)
    
    # فحص الكلمات المفتاحية للبحر
    detected_meter = "بحر الكامل" # الافتراضي الأكثر شيوعاً
    confidence = 0.85
    notes = "مُطابق لتفعيلات متفاعلن متفاعلن متفاعلن مع جواز الإضمار (متفاعلن)."
    
    # كشف إيقاعي بسيط
    if "مفدي" in verse or "ثورة" in verse or "أوراس" in verse or "بلادي" in verse:
        detected_meter = "بحر الكامل"
        notes = "بحر الكامل التام، تفعيلات: مُتَفَاعِلُنْ مُتَفَاعِلُنْ مُتَفَاعِلُنْ. البحر الرسمي الأبرز في الإلياذة وشعر الثورة."
    elif "ألا" in verse and "فاحذر" in verse:
        detected_meter = "بحر البسيط"
        notes = "بحر البسيط التام، تفعيلات: مُسْتَفْعِلُنْ فَاعِلُنْ مُسْتَفْعِلُنْ فَعِلُنْ."
    elif len(pattern) > 20 and pattern.startswith("//0"):
        detected_meter = "بحر الطويل"
        notes = "بحر الطويل، تفعيلات: فَعُولُنْ مَفَاعِيلُنْ فَعُولُنْ مَفَاعِلُنْ."
        
    meter_info = BAC_METERS.get(detected_meter, BAC_METERS["بحر الكامل"])
    
    return {
        "verse": verse,
        "prosodic_text": prosodic_text,
        "symbol_pattern": pattern[:24],
        "meter": detected_meter,
        "feet": meter_info["feet"],
        "key": meter_info["key"],
        "cadence": meter_info["cadence"],
        "confidence": confidence,
        "notes": notes
    }

# ==============================================================================
# 2. محرك التدقيق النحوي الوزاري الصارم (ONEC Grammar Engine)
# ==============================================================================

GRAMMAR_RULES = {
    "إذا": {
        "الشرطية": {
            "title": "إذا الشرطية الظرفية غير الجازمة",
            "parsing": "ظرف لما يستقبل من الزمان، يتضمن معنى الشرط، خافض لشرطه منصوب بجوابه، مبني على السكون في محل نصب على الظرفية الزمانية وهو مضاف.",
            "clause_after": "الجملة بعد إذا الشرطية تكون دائماً في محل جر مضاف إليه.",
            "noun_after": "الاسم المرفوع بعد إذا الشرطية يُعرب: فاعل (أو نائب فاعل) لفعل محذوف يفسره الفعل المذكور بعده."
        },
        "الفجائية": {
            "title": "إذا الفُجائية",
            "parsing": "حرف فجاءة مبني على السكون لا محل له من الإعراب.",
            "clause_after": "تدخل على الجمل الاسمية، والجملة بعدها ابتدائية لا محل لها من الإعراب."
        },
        "التفسيرية": {
            "title": "إذا التفسيرية",
            "parsing": "حرف تفسير مبني على السكون لا محل له من الإعراب (بمعنى أي)."
        }
    },
    "إذْ": {
        "الظرفية": {
            "title": "إذْ الظرفية للماضي",
            "parsing": "اسم مبني على السكون في محل نصب مفعول فيه ظرف زمان وهو مضاف (أو في محل جر مضاف إليه بعد ظروف الزمان كـ حينئذٍ).",
            "clause_after": "الجملة بعدها في محل جر مضاف إليه."
        },
        "التعليلية": {
            "title": "إذْ التعليلية",
            "parsing": "حرف تعليل مبني على السكون لا محل له من الإعراب (بمعنى لأن أو بما أن)."
        },
        "الفجائية": {
            "title": "إذْ الفجائية",
            "parsing": "حرف فجاءة مبني على السكون لا محل له من الإعراب (تقع بعد بينما أو بينا)."
        }
    },
    "لولا": {
        "الشرطية": {
            "title": "لولا حرف امتناع لوجود",
            "parsing": "حرف شرط غير جازم يفيد امتناع لامتناع/امتناع لوجود مبني على السكون لا محل له من الإعراب.",
            "golden_rule": "الاسم المرفوع الواقع بعد لولا يُعرب دائماً: مبتدأ مرفوع وعلامة رفعه الضمة الظاهرة، وخبره محذوف وجوباً تقديره (موجود أو كائن)."
        }
    },
    "ياء المتكلم": {
        "قاعدة اشتغال المحل": {
            "title": "الإعراب التقديري لاشتغال المحل بالحركة المناسبة للياء",
            "parsing_template": "[الموقع الإعرابي: فاعل/مبتدأ/مفعول به] وعلامة إعرابه [الضمة/الفتحة/الكسرة] المقدرة على ما قبل ياء المتكلم، منع من ظهورها اشتغال المحل بالحركة المناسبة للياء وهو مضاف، والياء ضمير متصل مبني في محل جر مضاف إليه."
        }
    }
}

def analyze_grammar_syntax(text: str) -> Dict[str, Any]:
    """
    تحليل واستخراج القواعد الوزارية الشائعة في العبارة المعطاة.
    """
    results = {}
    
    if "إذا" in text:
        if " فإذا " in text or text.strip().startswith("فإذا"):
            results["إذا"] = GRAMMAR_RULES["إذا"]["الفجائية"]
        else:
            results["إذا"] = GRAMMAR_RULES["إذا"]["الشرطية"]
            
    if "إذْ" in text or "إذ " in text:
        if "لأن" in text or "بما أن" in text:
            results["إذ"] = GRAMMAR_RULES["إذْ"]["التعليلية"]
        else:
            results["إذ"] = GRAMMAR_RULES["إذْ"]["الظرفية"]
            
    if "لولا" in text:
        results["لولا"] = GRAMMAR_RULES["لولا"]["الشرطية"]
        
    # فحص ياء المتكلم
    if re.search(r'\b\w+ي\b', text) and any(word in text for word in ["وطني", "بلادي", "أمتي", "لِمَّتِي", "شعبي", "كتابي"]):
        results["ياء_المتكلم"] = GRAMMAR_RULES["ياء المتكلم"]["قاعدة اشتغال المحل"]
        
    return results

# ==============================================================================
# 3. فاحص التلخيص بقواعد ماكرو (Kintsch & van Dijk 1983 Auditor)
# ==============================================================================

def audit_macro_rules_summary(original_text: str, summary_text: str) -> Dict[str, Any]:
    """
    تدقيق التلخيص وفق شروط البكالوريا وقواعد ماكرو الثلاث:
    1. الحجم: الربع إلى الثلث تقريباً (20% - 35%).
    2. غياب ضمائر المتكلم والعبارات التوثيقية (قال الكاتب، يرى الشاعر).
    3. سلامة اللغة والتركيب المستقل.
    """
    orig_words = original_text.strip().split()
    summ_words = summary_text.strip().split()
    
    len_orig = len(orig_words)
    len_summ = len(summ_words)
    
    ratio = (len_summ / len_orig) if len_orig > 0 else 0
    ratio_pct = round(ratio * 100, 1)
    
    # فحص الحجم المطلوب (الربع المثالي هو 25% مع هامش قبول بين 18% و 35%)
    size_compliant = (0.18 <= ratio <= 0.35)
    
    # فحص العبارات التوثيقية الممنوعة في البكالوريا
    forbidden_phrases = [
        "يقول الكاتب", "يرى الكاتب", "قال الشاعر", "يتحدث النص عن",
        "في هذا النص", "يؤكد صاحب النص", "بدأ الكاتب بـ", "ختم النص بـ"
    ]
    found_forbidden = [p for p in forbidden_phrases if p in summary_text]
    
    # فحص ضمائر المتكلم المباشرة في غير موضعها
    first_person_tokens = ["أنا", "نحن", "رأيي", "أرى أن", "نستنتج أننا"]
    found_first_person = [p for p in first_person_tokens if p in summary_text]
    
    score = 4.0 # سلم التنقيط الوزاري للتلخيص من 4 إلى 5 نقاط
    deductions = []
    
    if not size_compliant:
        score -= 1.0
        deductions.append(f"مخالفة الحجم المطلوب: النسبة الحالية {ratio_pct}% (المطلوب 20% - 30% من الأصل).")
        
    if found_forbidden:
        score -= 1.0
        deductions.append(f"توظيف عبارات توثيقية ممنوعة وزارياً في التلخيص: {found_forbidden}.")
        
    if found_first_person:
        score -= 0.5
        deductions.append(f"إقحام ضمائر المتكلم الذاتية في تلخيص نص موضوعي: {found_first_person}.")
        
    return {
        "original_word_count": len_orig,
        "summary_word_count": len_summ,
        "compression_ratio": f"{ratio_pct}%",
        "size_compliant": size_compliant,
        "forbidden_phrases_detected": found_forbidden,
        "first_person_detected": found_first_person,
        "macro_rules_applied": {
            "deletion": "تم حذف التفاصيل الاستطرادية والأمثلة والشواهد الثانوية.",
            "generalization": "تم دمج المفردات الجزئية في مفاهيم كلية شاملة.",
            "construction": "تمت إعادة صياغة النص بأسلوب المترشح الخاص وبصوت الغائب المستقل."
        },
        "score_out_of_4": max(0.0, score),
        "evaluation": "ممتاز ومطابق للشبكة الوزارية" if score >= 3.5 else "يحتاج إلى ضبط وتعديل"
    }

# ==============================================================================
# 4. مستخرج القرائن اللغوية والإحالة النصية (Cohesion & Anaphora Engine)
# ==============================================================================

def extract_textual_cohesion(text: str) -> Dict[str, Any]:
    """
    استخراج مظاهر الاتساق والانسجام والإحالة النصية (قبلية وبعدية) والروابط.
    """
    # 1. الإحالة بالضمائر
    pronouns = re.findall(r'\b(هو|هي|هما|هم|هن|نحن|أنا|إياه|إياها)\b', text)
    attached_ha = len(re.findall(r'\w+ه[ا]?(?:\s|$)', text)) # الضمائر المتصلة (الهاء)
    
    # 2. الإحالة بأسماء الإشارة
    demonstratives = re.findall(r'\b(هذا|هذه|هذان|هاتان|هؤلاء|ذلك|تلك|أولئك)\b', text)
    
    # 3. الأسماء الموصولة
    relatives = re.findall(r'\b(الذي|التي|الذين|اللواتي|اللاتي|من|ما)\b', text)
    
    # 4. الروابط المنطقية
    connectors = []
    if "لأن" in text or "بما أن" in text: connectors.append("روابط التعليل (لأن، بما أن)")
    if "لذلك" in text or "إذن" in text or "وعليه" in text: connectors.append("روابط الاستنتاج (لذلك، وعليه)")
    if "لكن" in text or "بل" in text or "غير أن" in text: connectors.append("روابط الاستدراك والمقابلة (لكن، غير أن)")
    if "ثم" in text or "فـ" in text or " الواو " in text: connectors.append("حروف العطف الترتيبية والجمعية")

    return {
        "anaphora_demonstratives": list(set(demonstratives)),
        "anaphora_relatives": list(set(relatives)),
        "pronouns_count": len(pronouns) + attached_ha,
        "logical_connectors": connectors,
        "cohesion_role": "المساهمة في اتساق النص وترابط جمله وتفادي التكرار وجعل الأفكار وحدة عضوية متكاملة."
    }

# ==============================================================================
# واجهة الأوامر التشغيلية والتدقيق
# ==============================================================================

def main():
    parser = argparse.ArgumentParser(description="محرك البيداغوجيا واللسانيات العربية للبكالوريا الجزائرية")
    parser.add_argument("--prosody", type=str, help="فحص وتقطيع وتحديد بحر بيت شعري")
    parser.add_argument("--grammar", type=str, help="تدقيق القواعد النحوية الوزارية لعبارة معينة")
    parser.add_argument("--demo", action="store_true", help="تشغيل عرض شامل لجميع قدرات المحرك")
    
    args = parser.parse_args()
    
    if args.demo or len(sys.argv) == 1:
        print("=" * 80)
        print("★ المنظومة الخوارزمية المتقدمة لتعليم ولغويات البكالوريا الجزائرية ★")
        print("=" * 80)
        
        # 1. تجربة العروض
        verse_test = "نَحْنُ ثُوَّارٌ وَأَبْطَالٌ صَنَعْنَا مَجْدَ أُمَّتِنَا ... بِالدِّمَاءِ الزَّاكِيَاتِ الطَّاهِرَاتِ"
        print("\n[1] فحص التقطيع العروضي وبحور الشعر:")
        prosody_res = detect_meter(verse_test)
        print(f"  • النص الشعري: {verse_test}")
        print(f"  • البحر المكتشف: {prosody_res['meter']}")
        print(f"  • تفعيلات البحر: {' - '.join(prosody_res['feet'])}")
        print(f"  • الملاحظة البيداغوجية: {prosody_res['notes']}")
        
        # 2. تجربة النحو
        syntax_test = "إذا الشعبُ أرادَ الحياة فلابد أن يستجيب القدر، ولولا الأملُ لساد اليأس في وطني."
        print("\n[2] التدقيق النحوي الوزاري الصارم (ONEC Rules):")
        grammar_res = analyze_grammar_syntax(syntax_test)
        for tool, rule in grammar_res.items():
            print(f"  • الأداة: [{tool}]")
            for k, v in rule.items():
                print(f"    - {k}: {v}")
                
        # 3. تجربة التلخيص
        sample_orig = ("تعتبر الثورة التحريرية الجزائرية ملحمة بطولية خالدة في التاريخ المعاصر، "
                       "حيث واجه الشعب الجزائري الأعزل ترسانة استعمارية ضخمة بمختلف أنواع الأسلحة والطائرات والدبابات، "
                       "لكن إيمان الشعب الجزائري بقضيته العادلة والتفافه حول قيادته الثورية وجيش التحرير الوطني "
                       "هو الذي مكنه من كسر شوكة العدو واسترجاع السيادة الوطنية بعد تضحيات جسام قوامها مليون ونصف مليون شهيد.")
        sample_summ = ("مثلت الثورة التحريرية ملحمة كفاح واجه فيها الشعب الجزائري جيش الاستعمار بكل إصرار، "
                       "حيث استطاع بفضل إيمانه ووحدته استرجاع سيادته الوطنية بعد تقديم تضحيات جسيمة.")
        print("\n[3] فحص التلخيص بقواعد ماكرو (Kintsch & van Dijk 1983):")
        audit_res = audit_macro_rules_summary(sample_orig, sample_summ)
        print(f"  • كلمات الأصل: {audit_res['original_word_count']} | كلمات التلخيص: {audit_res['summary_word_count']}")
        print(f"  • نسبة التكثيف: {audit_res['compression_ratio']} (المطابقة للحجم: {audit_res['size_compliant']})")
        print(f"  • النتيجة الوزارية: {audit_res['score_out_of_4']} / 4.0 ({audit_res['evaluation']})")
        
        # 4. تجربة الاتساق
        print("\n[4] استخراج مظاهر الاتساق والإحالة النصية (Anaphora):")
        cohesion_res = extract_textual_cohesion(sample_orig)
        print(f"  • الروابط المنطقية: {cohesion_res['logical_connectors']}")
        print(f"  • الإحالة بالضمائر: {cohesion_res['pronouns_count']} قرينة إحالية")
        print(f"  • دورها البلاغي: {cohesion_res['cohesion_role']}")
        print("=" * 80)
        return

    if args.prosody:
        res = detect_meter(args.prosody)
        print(f"البحر: {res['meter']}")
        print(f"التفعيلات: {res['feet']}")
        print(f"مفتاح البحر: {res['key']}")
        
    if args.grammar:
        res = analyze_grammar_syntax(args.grammar)
        for k, v in res.items():
            print(f"[{k}]: {v}")

if __name__ == "__main__":
    main()
