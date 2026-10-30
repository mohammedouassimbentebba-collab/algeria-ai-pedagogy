# -*- coding: utf-8 -*-
"""
BAC Archive Indexer and Structured Catalog Generator
Scans all Algerian BAC official PDFs (2017-2026), extracts metadata,
detects syllabus topics, classifies Sujet vs Corrigé, and builds a fast queryable database.
"""

import os
import sys
import json
import glob
import re
import time
import unicodedata
from typing import Dict, Any, List

# Suppress PyMuPDF deprecation and syntax errors
try:
    import pymupdf as fitz
    fitz.TOOLS.mupdf_display_errors(False)
except ImportError:
    try:
        import fitz
        fitz.TOOLS.mupdf_display_errors(False)
    except ImportError:
        fitz = None

sys.stdout.reconfigure(encoding='utf-8')

# Topic taxonomy dictionaries for national Algerian syllabi
SYLLABUS_TOPICS = {
    "الرياضيات": {
        "المتتاليات": [r"متتالية", r"متتاليات", r"حسابية", r"هندسية", r"تراجعية", r"البرهان بالتراجع", r"u_\{?n\}?", r"u_n", r"v_n"],
        "الدوال العددية والاشتقاقية": [r"الدالة", r"f\(x\)", r"المشتقة", r"جدول التغيرات", r"المستقيم المقارب", r"نقطة الانعطاف", r"مركز التناظر", r"محور التناظر"],
        "مبرهنة القيم المتوسطة": [r"القيم المتوسطة", r"تقبل حلا وحيدا", r"تقبل حلا", r"f\(x\)\s*=\s*0", r"حصر.*العدد", r"المجال\s*\[\s*α"],
        "الدوال الأسية واللوغاريتمية": [r"الأسية", r"e\^", r"exp", r"اللوغاريتم", r"اللوغاريتمية", r"ln\("],
        "التكامل وحساب المساحات": [r"التكامل", r"الدالة الأصلية", r"الدوال الأصلية", r"مساحة الحيز", r"∫"],
        "الأعداد المركبة والتحويلات النقطية": [r"المركب", r"الأعداد المركبة", r"العمدة", r"الطويلة", r"الشكل المثلثي", r"الشكل الأسي", r"التحاكي", r"الدوران", r"الانسحاب", r"التشابه المباشر"],
        "الهندسة في الفضاء": [r"الفضاء", r"المستوي", r"الجملة الخطية", r"معادلة ديكارتية", r"المستقيم في الفضاء", r"المسافة بين نقطة ومستو", r"سطح كرة", r"الجداء السلمي"],
        "الاحتمالات والإحصاء": [r"احتمال", r"الاحتمالات", r"المتغير العشوائي", r"الأمل الرياضياتي", r"التباين", r"الانحراف المعياري", r"سحب في آن واحد", r"على التوالي"],
        "القسمة والموافقات في Z": [r"الموافقات", r"القسمة الإقليدية", r"القاسم المشترك الأكبر", r"PGCD", r"بيزو", r"غوص", r"نظام التعداد", r"Z\s*×\s*Z"]
    },
    "العلوم_الفيزيائية": {
        "المتابعة الزمنية لتحول كيميائي": [r"المتابعة الزمنية", r"السرعة الحجمية", r"زمن نصف التفاعل", r"t_{?1/2}?", r"المعايرة", r"الناقلية", r"جدول التقدم", r"المتفاعل المحد", r"المؤكسد", r"المرجع"],
        "التحولات النووية": [r"النشاط الإشعاعي", r"التناقص الإشعاعي", r"طاقة الربط", r"الانشطار", r"الاندماج", r"ألفا", r"بيتا", r"غاما", r"عمر النصف", r"نظير", r"النواة"],
        "الظواهر الكهربائية (RC, RL, RLC)": [r"الدارة\s*RC", r"الدارة\s*RL", r"الدارة\s*RLC", r"المكثفة", r"الوشيعة", r"ثابت الزمن", r"τ", r"شحن المكثفة", r"تفريغ المكثفة", r"الذاتية", r"القوة المحركة"],
        "تطور جملة كيميائية نحو حالة التوازن (أحماض وأسس)": [r"حمض", r"أساس", r"pH", r"الـ pH", r"ثابت التوازن", r"pKa", r"النسبة النهائية للتقدم", r"τ_f", r"المعايرة الـ pH", r"نقطة التكافؤ", r"الكاشف الملون"],
        "تطور جملة ميكانيكية (الميكانيك)": [r"قوانين نيوتن", r"السقوط الشاقولي", r"السقوط الحر", r"دافعة أرخميدس", r"الاحتكاك", r"القذيفة", r"حركة الأقمار", r"حركة الكواكب", r"المستوى المائل", r"المستوى الأفقي", r"الطاقة الحركية"],
        "مراقبة تطور جملة كيميائية (الأسترة)": [r"الأسترة", r"الإماهة", r"إستر", r"حمض كربوكسيلي", r"كحول", r"مردود الأسترة", r"التصبن", r"مراقبة التفاعل"]
    },
    "علوم_الطبيعة_والحياة": {
        "تركيب البروتين": [r"تركيب البروتين", r"الاستنساخ", r"الترجمة", r"ARN", r"ARNm", r"ARNt", r"الريبوزوم", r"الاستطالة", r"البداية", r"النهاية", r"الشفرة الوراثية"],
        "العلاقة بين بنية ووظيفة البروتين": [r"بنية البروتين", r"البنية الأولية", r"البنية الثانوية", r"البنية الثالثية", r"البنية الرابعة", r"الروابط الهيدروجينية", r"الجسور الكبريتية", r"سلوك الأحماض الأمينية", r"الهجرة الكهربائية"],
        "النشاط الإنزيمي للبروتينات": [r"الإنزيم", r"النشاط الإنزيمي", r"الموقع الفعال", r"التكامل المحفز", r"السرعة الابتدائية", r"درجة الحرارة", r"تأثير الـ pH", r"المثبطات"],
        "دور البروتينات في الدفاع عن الذات (المناعة)": [r"المناعة", r"الذات واللاذات", r"محدد المستضد", r"الجسم المضاد", r"اللمفاويات", r"LB", r"LT", r"LT4", r"LT8", r"البالعات", r"البلعمة", r"المعقد المناعي", r"الخلطية", r"الخلوية", r"HLA", r"CMH", r"السيتوكينات", r"الإنترلوكين"],
        "دور البروتينات في الاتصال العصبي": [r"الاتصال العصبي", r"كمون الراحة", r"كمون العمل", r"المشبك", r"مشبك تنبيهي", r"مشبك تثبيطي", r"الأستيل كولين", r"القنوات الغشائية", r"مضخة الصوديوم", r"PPSE", r"PPSI", r"الإدماج العصبي"],
        "آليات تحويل الطاقة الضوئية (التركيب الضوئي)": [r"التركيب الضوئي", r"المرحلة الكيميوضوئية", r"المرحلة الكيميوحيوية", r"التيلاكويد", r"الحشوة", r"حلقة كالفن", r"اليخضور", r"التركيب الحيوي"],
        "التنفس والتخمر": [r"التنفس الخلوي", r"التخمر", r"التحلل السكري", r"الميتوكوندري", r"حلقة كريبس", r"الفسفرة التأكسدية", r"ATP"]
    },
    "اللغة العربية": {
        "عصر الضعف والانحطاط": [r"المديح النبوي", r"الزهد", r"البوصيري", r"ابن نباتة", r"ابن عربي", r"التضمين", r"البديع", r"الضعف والانحطاط"],
        "عصر النهضة وشعر المنفى": [r"الإحياء والبعث", r"المنفى", r"الشوقيات", r"محمود سامي البارودي", r"أحمد شوقي", r"التقليد والتجديد"],
        "الشعر المهجري والرابطة القلمية": [r"المهجر", r"الرابطة القلمية", r"العصبة الأندلسية", r"إيليا أبو ماضي", r"ميخائيل نعيمة", r"جبران", r"التفاؤل", r"الإنسانية", r"الطبيعة"],
        "شعر الثورة التحريرية الجزائرية": [r"الثورة الجزائرية", r"مفدي زكريا", r"أول نوفمبر", r"الأوراس", r"الجهاد", r"التحرر", r"الاستعمار", r"نزار قباني", r"محمود درويش"],
        "القضية الفلسطينية وظاهرة الالتزام": [r"فلسطين", r"القدس", r"القضية الفلسطينية", r"الالتزام", r"الأدب الملتزم", r"المقاومة"],
        "ظاهرة الحزن والألم والشعر الحر": [r"الحزن والألم", r"نازك الملائكة", r"بدر شاكر السياب", r"شعر التفعيلة", r"الشعر الحر", r"الرمز والأسطورة"],
        "النثر العلمي والنثر العلمي المتأدب": [r"النثر العلمي", r"النثر العلمي المتأدب", r"ابن خلدون", r"القزويني", r"المصطلحات العلمية", r"الإجمال والتفصيل"],
        "فن المقال": [r"المقال", r"البشير الإبراهيمي", r"جمعية العلماء", r"طه حسين", r"المقال الاجتماعي", r"المقال النقدي", r"المقال السياسي", r"النزعة الإصلاحية"]
    },
    "الفلسفة": {
        "السؤال والمشكلة والإشكالية": [r"السؤال العلمي", r"السؤال الفلسفي", r"المشكلة والإشكالية", r"المفارقة"],
        "فلسفة الرياضيات والمطلقية": [r"أصل المفاهيم الرياضية", r"العقل والتجربة في الرياضيات", r"اليقين الرياضي", r"الأكسيوماتيك", r"الهندسات اللاإقليدية"],
        "فلسفة علوم المادة الحية (البيولوجيا)": [r"المادة الحية", r"الحتمية في البيولوجيا", r"الغائية", r"التجريب في البيولوجيا", r"كلود برنار"],
        "فلسفة العلوم الإنسانية": [r"العلوم الإنسانية", r"علم التاريخ", r"علم النفس", r"علم الاجتماع", r"الذاتية والموضوعية في دراسة الإنسان"],
        "الشعور واللاشعور": [r"الشعور", r"اللاشعور", r"فرويد", r"التحليل النفسي", r"الكبت", r"الأنا والهو"],
        "الحرية والمسؤولية": [r"الحرية", r"المسؤولية", r"الحتمية والجبرية", r"سارتر", r"كانط", r"العقاب والجزاء"],
        "اللغة والفكر": [r"اللغة والفكر", r"الدال والمدلول", r"العلاقة بين الدال والمدلول", r"اعتباطية الإشارة", r"عجز اللغة"],
        "الأخلاق والعدالة والأنظمة السياسية": [r"الأخلاق", r"المنفعة والواجب", r"العدالة الاجتماعية", r"الحق والواجب", r"الأنظمة السياسية", r"الديمقراطية", r"الدولة"]
    },
    "التاريخ_والجغرافيا": {
        "بروز الصراع وتشكل العالم (الحرب الباردة)": [r"الحرب الباردة", r"الثنائية القطبية", r"مشروع مارشال", r"مبدأ ترومان", r"حلف وارسو", r"حلف الشمال الأطلسي", r"الستار الحديدي", r"الاستقطاب"],
        "مساعي الانفراج الدولي والتعايش السلمي": [r"التعايش السلمي", r"الانفراج الدولي", r"حركة عدم الانحياز", r"مؤتمر باندونغ", r"مؤتمر بلغراد", r"نزع السلاح"],
        "الثورة التحريرية الجزائرية (1954-1962)": [r"الثورة التحريرية", r"بيان أول نوفمبر", r"هجمات الشمال القسنطيني", r"مؤتمر الصومام", r"لجنة التنسيق والتنفيذ", r"الحكومة المؤقتة", r"مفاوضات إيفيان", r"مظاهرات 11 ديسمبر"],
        "العالم المتقدم والعالم المتخلف": [r"الشمال والجنوب", r"العالم المتقدم", r"العالم المتخلف", r"مؤشر التنمية البشرية", r"البترول والغاز", r"حركة رؤوس الأموال", r"الاحتكارات"],
        "القوى الاقتصادية الكبرى (أمريكا، أوروبا، آسيا)": [r"الولايات المتحدة الأمريكية", r"الاتحاد الأوروبي", r"القطب الاقتصادي", r"منطقة شرق وجنوب شرق آسيا", r"التنينات والنمور", r"التبادل التجاري", r"الهيمنة المالية"]
    },
    "العلوم_الإسلامية": {
        "العقيدة الإسلامية وأثرها": [r"العقيدة الإسلامية", r"وسائل تثبيت العقيدة", r"التذكير بقدرة الله", r"رسم الصور المحببة", r"إثارة الوجدان"],
        "مقاصد الشريعة الإسلامية": [r"مقاصد الشريعة", r"الضروريات", r"الحاجيات", r"التحسينيات", r"حفظ الدين", r"حفظ النفس", r"حفظ العقل", r"حفظ النسل", r"حفظ المال"],
        "العقل في القرآن الكريم": [r"العقل", r"دور العقل", r"حدود العقل", r"الحث على النظر والتفكر"],
        "المعاملات المالية والربا": [r"الربا", r"ربا الفضل", r"ربا النسيئة", r"القرض", r"المرابحة", r"بيع التقسيط"],
        "أحكام الأسرة (الميراث، النسب، التبني)": [r"الميراث", r"الورثة", r"التركة", r"أسباب الإرث", r"موانع الإرث", r"النسب", r"التبني", r"الكفالة"]
    }
}

# Mapping for ONEC PDFs with broken ToUnicode ligature glyphs
ONEC_GLYPH_MAP = {
    "\u01fd": "ي",  # ǽ
    "\u01fc": "ب",  # Ǽ
    "\u0204": "ي",  # Ȅ
    "\u01fb": "ي",  # ǻ
    "\u02ae": "يا", # ʮ
    "\u02ad": "نا", # ʭ
    "\u0202": "ي",  # Ȃ
    "\u01fa": "ب",  # Ǻ
    "\u0203": "ب",  # ȃ
    "\u021e": "ك",  # Ȟ
    "\u020f": "ي",  # ȏ
    "\u0211": "ي",  # ȑ
    "\u0201": "ب",  # ȁ
    "\u0218": "ق",  # Ș
    "\u0216": "ق",  # Ȗ
    "\u0114": "نه", # Ĕ
    "\u010e": "ً",  # Ď
}

def decode_onec_font_glyphs(text: str, is_arabic_subject: bool = True) -> str:
    """Decode presentation forms (NFKC) and repair ONEC PDF custom font glyphs."""
    if not text:
        return ""
    t = unicodedata.normalize("NFKC", text)
    if is_arabic_subject:
        for bad_ch, ar_repl in ONEC_GLYPH_MAP.items():
            if bad_ch in t:
                t = t.replace(bad_ch, ar_repl)
    return t

def clean_arabic_text(text: str) -> str:
    """Normalize Arabic text for reliable regex searching."""
    if not text:
        return ""
    t = decode_onec_font_glyphs(text, is_arabic_subject=True)
    # Normalize alefs and letters
    t = re.sub(r"[إأآا]", "ا", t)
    t = re.sub(r"ة", "ه", t)
    t = re.sub(r"ى", "ي", t)
    t = re.sub(r"[\u064B-\u065F\u0670]", "", t) # diacritics
    return t

def extract_pdf_data(pdf_path: str, is_arabic_subject: bool = True, ocr_pages: List[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Extract page count, text, structure, and topics from a PDF (with OCR fallback)."""
    result = {
        "num_pages": 0,
        "has_text": False,
        "text_source": "none",
        "char_count": 0,
        "pages_text": [],
        "exercise_headers": [],
        "detected_topics": []
    }
    
    if not fitz or not os.path.exists(pdf_path):
        return result

    try:
        doc = fitz.open(pdf_path)
        result["num_pages"] = len(doc)
        total_text = []
        
        for i, page in enumerate(doc):
            ptext = page.get_text() or ""
            ptext_clean = decode_onec_font_glyphs(ptext.strip(), is_arabic_subject=is_arabic_subject)
            if ptext_clean:
                total_text.append(ptext_clean)
                result["pages_text"].append({
                    "page_num": i + 1,
                    "text": ptext_clean
                })
        
        full_doc_text = "\n\n".join(total_text)
        # Check if digital text is actually unreadable Mojibake
        is_mojibake = is_arabic_subject and len(re.findall(r"[\u0150-\u01BF]", full_doc_text)) > 20
        
        if (len(full_doc_text) <= 80 or is_mojibake) and ocr_pages:
            result["pages_text"] = ocr_pages
            full_doc_text = "\n\n".join([p["text"] for p in ocr_pages if p.get("text")])
            result["text_source"] = "ocr_winrt" if len(full_doc_text) > 40 else "none"
        else:
            result["text_source"] = "digital" if len(full_doc_text) > 80 else "none"

        result["char_count"] = len(full_doc_text)
        result["has_text"] = len(full_doc_text) > 40
        
        # Extract Exercise Headers
        headers = []
        for line in full_doc_text.splitlines():
            line_str = line.strip()
            if re.search(r"(الموضوع\s+(الأول|الثاني|1|2)|التمرين\s+(الأول|الثاني|الثالث|الرابع|الخامس|[12345])|المسألة|الجزء\s+(الأول|الثاني))", line_str):
                if len(line_str) < 80:
                    headers.append(line_str)
        result["exercise_headers"] = list(dict.fromkeys(headers))[:12] # deduplicate
        
    except Exception as e:
        result["error"] = str(e)
        
    return result

def parse_filename_metadata(rel_path: str) -> Dict[str, Any]:
    """Parse subject, stream, year, session, and type from the relative path."""
    parts = rel_path.replace("\\", "/").split("/")
    filename = parts[-1]
    
    meta = {
        "file_path": rel_path.replace("\\", "/"),
        "filename": filename,
        "subject_folder": parts[1] if len(parts) > 1 else "Unknown",
        "stream_folder": parts[2] if len(parts) > 2 else "Unknown",
        "year": None,
        "session": "عادية",
        "type": "غير محدد",
        "standard_subject": "",
        "standard_stream": ""
    }
    
    # Check type: Sujet vs Corrigé
    if "Corrigé" in filename or "Corrig" in filename or "corrig" in filename or "حل" in filename or "تصحيح" in filename:
        meta["type"] = "Corrigé"
    elif "Sujet" in filename or "sujet" in filename or "موضوع" in filename:
        meta["type"] = "Sujet"
    elif "annale" in filename:
        meta["type"] = "Annale"
        
    # Check year & session
    # e.g., BAC_2017-2 or BAC_2023 or bac-2022
    year_match = re.search(r"BAC[_\-]?(\d{4})(-2)?", filename, re.IGNORECASE)
    if not year_match:
        year_match = re.search(r"(\d{4})", filename)
        
    if year_match:
        meta["year"] = int(year_match.group(1))
        if year_match.lastindex and year_match.lastindex >= 2 and year_match.group(2) == "-2":
            meta["session"] = "استثنائية"
            
    # Standardize Subject
    sub_map = {
        "الرياضيات": "الرياضيات",
        "العلوم_الفيزيائية": "العلوم الفيزيائية",
        "علوم_الطبيعة_والحياة": "علوم الطبيعة والحياة",
        "اللغة العربية": "اللغة العربية",
        "الفلسفة": "الفلسفة",
        "التاريخ_والجغرافيا": "التاريخ والجغرافيا",
        "العلوم_الإسلامية": "العلوم الإسلامية",
        "اللغة_الفرنسية": "اللغة الفرنسية",
        "اللغة_الإنجليزية": "اللغة الإنجليزية",
        "اللغة_الألمانية": "اللغة الألمانية",
        "اللغة_الإسبانية": "اللغة الإسبانية",
        "اللغة_الإيطالية": "اللغة الإيطالية",
        "اللغة_الأمازيغية": "اللغة الأمازيغية",
        "هندسة_ميكانيكية": "الهندسة الميكانيكية",
        "هندسة_كهربائية": "الهندسة الكهربائية",
        "هندسة_مدنية": "الهندسة المدنية",
        "هندسة_الطرائق": "هندسة الطرائق",
        "اقتصاد_ومناجمنت": "اقتصاد ومناجمنت",
        "القانون": "القانون",
        "تسيير_محاسبي_ومالي": "تسيير محاسبي ومالي",
        "dzexams_user_downloads": "حوليات مجمعة"
    }
    meta["standard_subject"] = sub_map.get(meta["subject_folder"], meta["subject_folder"])
    
    # Standardize Stream
    stream_map = {
        "شعبة_علوم_تجريبية": "علوم تجريبية",
        "شعبة_رياضيات": "رياضيات",
        "شعبة_تقني_رياضي": "تقني رياضي",
        "شعبة_رياضيات_وتقني_رياضي": "رياضيات وتقني رياضي",
        "شعبة_تسيير_واقتصاد": "تسيير واقتصاد",
        "شعبة_آداب_وفلسفة": "آداب وفلسفة",
        "شعبة_لغات_أجنبية": "لغات أجنبية",
        "شعبة_آداب_وفلسفة_ولغات": "آداب وفلسفة ولغات أجنبية",
        "الشعب_العلمية_والتقنية_المشتركة": "الشعب العلمية والتقنية المشتركة",
        "جميع_الشعب_المشتركة": "جميع الشعب المشتركة",
        "عام": "جميع الشعب"
    }
    if meta["subject_folder"] == "dzexams_user_downloads":
        fn_low = filename.lower()
        if "mathematiques" in fn_low:
            meta["standard_subject"] = "الرياضيات"
            meta["subject_folder"] = "الرياضيات"
        elif "arabe" in fn_low:
            meta["standard_subject"] = "اللغة العربية"
            meta["subject_folder"] = "اللغة العربية"
        meta["standard_stream"] = "جميع الشعب"
    else:
        meta["standard_stream"] = stream_map.get(meta["stream_folder"], meta["stream_folder"])
    
    return meta

def detect_topics(subject: str, full_text: str) -> List[str]:
    """Detect presence of official syllabus topics in extracted text."""
    if not full_text or subject not in SYLLABUS_TOPICS:
        return []
    
    clean_text = clean_arabic_text(full_text)
    detected = []
    
    for topic, patterns in SYLLABUS_TOPICS[subject].items():
        score = 0
        for pat in patterns:
            pat_clean = clean_arabic_text(pat)
            if re.search(pat_clean, clean_text, re.IGNORECASE):
                score += 1
        if score >= 1:
            detected.append(topic)
            
    return detected

def build_bac_catalog(archive_dir: str = "BAC_Archives", output_json: str = "BAC_Archives/bac_catalog_index.json"):
    print("=" * 70)
    print("بدء بناء المحرك الفهرسي الشامل لأرشيف البكالوريا الجزائري (2017-2026)")
    print("=" * 70)
    
    pdf_files = glob.glob(os.path.join(archive_dir, "**/*.pdf"), recursive=True)
    total_files = len(pdf_files)
    print(f"إجمالي ملفات PDF المكتشفة: {total_files}")
    
    ocr_cache = {}
    ocr_cache_path = os.path.join(archive_dir, "ocr_cache.json")
    if os.path.exists(ocr_cache_path):
        try:
            with open(ocr_cache_path, "r", encoding="utf-8") as f:
                ocr_cache = json.load(f)
            print(f"تم تحميل ذاكرة OCR لـ {len(ocr_cache)} ملف ممسوح ضوئياً.")
        except Exception as e:
            print(f"تنبيه: تعذر قراءة ocr_cache.json: {e}")

    latin_subjects = {
        "اللغة الفرنسية", "اللغة الإنجليزية", "اللغة الألمانية",
        "اللغة الإسبانية", "اللغة الإيطالية", "اللغة الأمازيغية"
    }

    catalog = []
    stats = {
        "total": total_files,
        "subjects": {},
        "streams": {},
        "years": {},
        "types": {"Sujet": 0, "Corrigé": 0, "Annale": 0, "Other": 0},
        "text_based": 0,
        "digital_text": 0,
        "ocr_recovered": 0,
        "image_scanned": 0
    }
    
    corpus_entries = []
    start_time = time.time()
    
    for idx, pdf_path in enumerate(pdf_files):
        rel_path = os.path.relpath(pdf_path, ".")
        meta = parse_filename_metadata(rel_path)
        is_arabic = meta["standard_subject"] not in latin_subjects
        ocr_pages = ocr_cache.get(meta["file_path"])
        pdf_data = extract_pdf_data(pdf_path, is_arabic_subject=is_arabic, ocr_pages=ocr_pages)
        
        # Combine text for topic detection
        full_text = "\n\n".join([p["text"] for p in pdf_data["pages_text"]])
        detected_topics = detect_topics(meta["subject_folder"], full_text)
        
        entry = {
            "id": f"BAC_{meta['year'] or 'X'}_{meta['standard_subject']}_{meta['standard_stream']}_{meta['type']}_{idx}",
            "file_path": meta["file_path"],
            "filename": meta["filename"],
            "subject": meta["standard_subject"],
            "stream": meta["standard_stream"],
            "year": meta["year"],
            "session": meta["session"],
            "type": meta["type"],
            "num_pages": pdf_data["num_pages"],
            "has_text": pdf_data["has_text"],
            "text_source": pdf_data.get("text_source", "digital"),
            "char_count": pdf_data["char_count"],
            "exercise_headers": pdf_data["exercise_headers"],
            "detected_topics": detected_topics,
            "preview_text": full_text[:400].strip() if full_text else ""
        }
        
        catalog.append(entry)
        
        # Save corpus entry if text exists
        if pdf_data["has_text"]:
            corpus_entries.append({
                "id": entry["id"],
                "file_path": entry["file_path"],
                "subject": entry["subject"],
                "stream": entry["stream"],
                "year": entry["year"],
                "session": entry["session"],
                "type": entry["type"],
                "text_source": entry["text_source"],
                "detected_topics": detected_topics,
                "text": full_text
            })
            stats["text_based"] += 1
            if entry["text_source"] == "ocr_winrt":
                stats["ocr_recovered"] += 1
            else:
                stats["digital_text"] += 1
        else:
            stats["image_scanned"] += 1
            
        # Update Stats
        sub = meta["standard_subject"]
        stats["subjects"][sub] = stats["subjects"].get(sub, 0) + 1
        
        stream = meta["standard_stream"]
        stats["streams"][stream] = stats["streams"].get(stream, 0) + 1
        
        yr = str(meta["year"]) if meta["year"] else "Unknown"
        stats["years"][yr] = stats["years"].get(yr, 0) + 1
        
        tp = meta["type"]
        if tp in stats["types"]:
            stats["types"][tp] += 1
        else:
            stats["types"]["Other"] += 1
            
        if (idx + 1) % 50 == 0 or (idx + 1) == total_files:
            elapsed = time.time() - start_time
            print(f"[{idx + 1}/{total_files}] تمت معالجة الملفات... الوقت المنقضي: {elapsed:.1f}s")
            
    # Write JSON Catalog
    print("\nحفظ فهرس الكتالوج الشامل في:", output_json)
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump({
            "version": "1.0.0",
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "stats": stats,
            "catalog": catalog
        }, f, ensure_ascii=False, indent=2)
        
    # Write Corpus JSONL for fast retrieval
    corpus_jsonl = "BAC_Archives/bac_text_corpus.jsonl"
    print("حفظ قاعدة النصوص المستخرجة للبحث المعمق في:", corpus_jsonl)
    with open(corpus_jsonl, "w", encoding="utf-8") as f:
        for centry in corpus_entries:
            f.write(json.dumps(centry, ensure_ascii=False) + "\n")
            
    print("\n" + "=" * 70)
    print("اكتمل بناء الفهرس بنجاح تام!")
    print(f"إجمالي الملفات المفهرسة: {len(catalog)}")
    print(f"الملفات ذات النصوص الرقمية المستخرجة: {stats['text_based']}")
    print(f"الملفات المصورة (Scanned): {stats['image_scanned']}")
    print(f"المواضيع (Sujet): {stats['types']['Sujet']}")
    print(f"التصحيحات وسلالم التنقيط (Corrigé): {stats['types']['Corrigé']}")
    print("=" * 70)

if __name__ == "__main__":
    build_bac_catalog()
