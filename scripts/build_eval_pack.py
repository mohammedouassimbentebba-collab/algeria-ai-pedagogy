# -*- coding: utf-8 -*-
"""
Build a 20-question evaluation pack from REAL official BAC subjects.
Each question = pages 1-2 of an official Sujet (Topic 1 / Exercise 1) rendered as PNG
(no lossy text extraction), plus the official Corrigé PDF kept separately as the answer key.
"""
import os, sys, json, shutil
from collections import defaultdict
try:
    import pymupdf as fitz
except ImportError:
    import fitz
fitz.TOOLS.mupdf_display_errors(False)
sys.stdout.reconfigure(encoding='utf-8')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "eval_pack")

# (subject, stream substring, year, what to answer inside "الموضوع الأول")
PLAN = [
    ("الرياضيات", "علوم تجريبية", 2022, "التمرين الأول"),
    ("الرياضيات", "علوم تجريبية", 2023, "التمرين الأول"),
    ("الرياضيات", "رياضيات", 2020, "التمرين الأول"),
    ("الرياضيات", "تسيير", 2021, "التمرين الأول"),
    ("العلوم الفيزيائية", "علوم تجريبية", 2022, "التمرين الأول"),
    ("العلوم الفيزيائية", "علوم تجريبية", 2023, "التمرين الأول"),
    ("العلوم الفيزيائية", "علوم تجريبية", 2021, "التمرين الأول"),
    ("علوم الطبيعة والحياة", "علوم تجريبية", 2022, "التمرين الأول"),
    ("علوم الطبيعة والحياة", "علوم تجريبية", 2023, "التمرين الأول"),
    ("علوم الطبيعة والحياة", "علوم تجريبية", 2021, "التمرين الأول"),
    ("اللغة العربية", "آداب", 2022, "كل أسئلة الموضوع الأول (البناء الفكري، البناء اللغوي، التقويم النقدي)"),
    ("اللغة العربية", "آداب", 2023, "كل أسئلة الموضوع الأول (البناء الفكري، البناء اللغوي، التقويم النقدي)"),
    ("الفلسفة", "آداب", 2022, "مقالة الموضوع الأول (اختر أحد السؤالين/النصين حسب الصيغة وأجب كتلميذ)"),
    ("الفلسفة", "", 2021, "مقالة الموضوع الأول (اختر أحد السؤالين/النصين حسب الصيغة وأجب كتلميذ)"),
    ("التاريخ والجغرافيا", "علمية", 2022, "كل أسئلة الموضوع الأول"),
    ("التاريخ والجغرافيا", "علمية", 2023, "كل أسئلة الموضوع الأول"),
    ("العلوم الإسلامية", "", 2022, "كل أسئلة الموضوع الأول"),
    ("اللغة الفرنسية", "", 2022, "كل أسئلة الموضوع الأول (Sujet 1)"),
    ("اللغة الفرنسية", "", 2023, "كل أسئلة الموضوع الأول (Sujet 1)"),
    ("اللغة الإنجليزية", "", 2022, "كل أسئلة الموضوع الأول (Topic 1)"),
]

def render(pdf_path, pages, out_dir, prefix):
    doc = fitz.open(pdf_path)
    names = []
    for p in pages:
        if p < len(doc):
            name = f"{prefix}_page{p+1}.png"
            doc[p].get_pixmap(dpi=110).save(os.path.join(out_dir, name))
            names.append(name)
    doc.close()
    return names

def main():
    docs = [json.loads(l) for l in open(os.path.join(ROOT, "BAC_Archives", "bac_text_corpus.jsonl"), encoding="utf-8")]
    pairs = defaultdict(dict)
    for d in docs:
        if d["type"] in ("Sujet", "Corrigé") and d.get("text_source") == "digital":
            pairs[(d["subject"], d["stream"], d["year"], d.get("session", "عادية"))][d["type"]] = d

    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)
    used = set()
    csv = ["id,subject,stream,year,task,max_score,score_without_skill,score_with_skill,notes"]
    readme = ["# حزمة اختبار الـ Skill (20 سؤالاً حقيقياً من البكالوريا)\n",
              "## طريقة الاختبار\n",
              "1. لكل مجلد `Qxx`: أعطِ النموذج صور `question_*.png` فقط مع الطلب المذكور في `TASK.txt`. **لا تعطه ملف التصحيح.**\n",
              "2. أجرِ التجربة مرتين بنفس النموذج: (أ) بدون Skill، (ب) مع طلب قراءة `.agents/skills/algeria-education-system/SKILL.md` أولاً.\n",
              "3. صحّح كلتا الإجابتين بمقارنتهما مع `ANSWER_KEY_official_corrige.pdf` وسلم التنقيط فيه، وسجّل العلامتين في `scoring_sheet.csv` (من 20 أو من علامة التمرين).\n",
              "4. قارن المتوسطين. إن لم يتحسن المتوسط بوضوح (أكثر من نقطة تقريباً على 20)، فالـ Skill لا تضيف قيمة.\n",
              "\n## الأسئلة\n"]
    qid = 0
    for subj, hint, year, task in PLAN:
        cands = [(k, v) for k, v in pairs.items()
                 if k[0] == subj and hint in k[1] and k[3] == "عادية" and "Sujet" in v and "Corrigé" in v and k not in used]
        cands.sort(key=lambda kv: (kv[0][2] != year, abs(kv[0][2] - year)))
        if not cands:
            print("NO CANDIDATE", subj, hint, year); continue
        k, v = cands[0]
        used.add(k)
        qid += 1
        d = os.path.join(OUT, f"Q{qid:02d}")
        os.makedirs(d)
        names = render(v["Sujet"]["file_path"], list(range(8)), d, "question")
        shutil.copy(v["Corrigé"]["file_path"], os.path.join(d, "ANSWER_KEY_official_corrige.pdf"))
        open(os.path.join(d, "TASK.txt"), "w", encoding="utf-8").write(
            f"المادة: {k[0]} | الشعبة: {k[1]} | بكالوريا {k[2]}\n"
            f"المطلوب: أجب عن «{task}» من «الموضوع الأول» كما يجيب تلميذ في الامتحان الرسمي (بالتفصيل وبحسب سلم التنقيط).\n"
            f"المصدر الأصلي: {v['Sujet']['file_path']}\n")
        readme.append(f"- **Q{qid:02d}** — {k[0]} | {k[1]} | {k[2]} — المطلوب: {task}\n")
        csv.append(f"Q{qid:02d},{k[0]},{k[1]},{k[2]},{task},,,,")
    open(os.path.join(OUT, "README.md"), "w", encoding="utf-8").write("".join(readme))
    open(os.path.join(OUT, "scoring_sheet.csv"), "w", encoding="utf-8-sig").write("\n".join(csv))
    print("questions:", qid)

if __name__ == "__main__":
    main()

