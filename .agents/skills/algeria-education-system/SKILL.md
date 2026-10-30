---
name: algerian-education-system
description: "مرجع بيداغوجي شامل ومنهجية إجابة معتمدة رسمياً للتعليم الجزائري في طوري الثانوي (البكالوريا BAC) والجامعي (LMD)، يضبط لغة وسياق وشبكات التنقيط واستراتيجيات إيصال الفكرة وتلخيصها وتحفيظها للذكاء الاصطناعي لكافة المواد والشعب."
---

# نظام ومنهجية التعليم الجزائري (Algerian Education System & BAC Methodology)

هذا الدليل يحدد القواعد الصارمة والمنهجيات المعتمدة رسمياً من قبل وزارة التربية الوطنية الجزائرية (المفتشية العامة للبيداغوجيا والديوان الوطني للامتحانات والمسابقات ONEC)، بالإضافة إلى ضوابط التعليم العالي والبحث العلمي (نظام LMD) والمعايير الهندسية (CDIO Standards 3.0).

---

## 1. المبادئ العامة للرد على الطلاب والتلاميذ الجزائريين

1. **الالتزام بالمصطلحات الرسمية المبرمجة (إلزامية 100%):**
   - يُحظر استخدام أي مصطلحات مشرقية أو أنجلوساكسونية غير واردة في المنهاج الجزائري.
   - المرجع الشامل: [القاموس المصطلحي الوطني الموحد](./references/national_pedagogical_glossary.md).
2. **احترام شبكة التقويم وسلالم التنقيط الوزارية (ONEC Barème):**
   - في الامتحانات الرسمية، تُقسّم النقطة على مؤشرات دقيقة (0.25، 0.5، 0.75). يجب صياغة الجواب خطوة بخطوة مع توضيح هذه المؤشرات ليعتاد التلميذ عليها.
3. **التوجيه السقراطي والتدرج المعرفي:**
   - عدم إعطاء الحلول الجاهزة في أسئلة الفهم والتدرب، وتوجيه التلميذ عبر أسئلة متدرجة لاكتشاف الحل بنفسه، مع استثناء طلبات التصحيح المقارن الصريحة.
   - المرجع الشامل: [بروتوكول التفاعل المعرفي والسلوكي](./references/cognitive_interaction_protocol.md).
4. **التمايز الصارم بين الشعب:**
   - مراعاة المستوى العلمي المطلوب لكل شعبة (رياضيات وتقني رياضي vs علوم تجريبية vs تسيير واقتصاد vs آداب وفلسفة ولغات أجنبية).

---

## 2. الأدوات وقواعد البيانات الفعلية المتاحة للوكيل (Executable Data & Tools)

عند الإجابة عن أسئلة البكالوريا أو تصحيح إجابات التلميذ، استعمل الأدوات وقواعد البيانات المفهرسة كاملة (659 ملف PDF مفهرس نصياً بالكامل بعد معالجة الـ OCR وفك تشفير خطوط الديوان الوطني ONEC):

1. **البحث في مواضيع وتصحيحات البكالوريا الرسمية (2017–2026):**
   - `python scripts/query_bac.py --subject "الرياضيات" --stream "علوم تجريبية" --query "القيم المتوسطة"`
   - البحث النصي المعمق في 659 ملفاً: `python scripts/query_bac.py --deep "مبرهنة بيزو"`
2. **استرجاع مقتطفات سلالم التنقيط (استخراج آلي تقريبي — نحو 47% من العناصر مشوّهة وأغلب التصحيحات غير مكتملة؛ ارجع دائماً إلى ملف PDF الأصلي للتحقق قبل الاعتماد):**
   - قاعدة البيانات: `BAC_Archives/onec_extracted_rubrics.json`
   - محرك التنقيط وفحص المنهاج: `python scripts/bac_scoring_engine.py --subject "العلوم الفيزيائية" --stream "علوم تجريبية" --question "..." --answer "..."`
3. **حساب الارتيابات وتدقيق مذكرات التخرج الجامعية (LMD & CDIO):**
   - `python scripts/higher_ed_cdio_engine.py --demo`
4. **محرك الشرح (PCK) والتلخيص المعرفي وفحص النسخ الحرفي (3-gram Audit):**
   - `python scripts/instruction_summarization_engine.py --summarize "..."`

---

## 3. محرك استراتيجيات التعليم وإيصال الفكرة وتلخيصها وتحفيظها (المرحلة 6)

يرتبط هذا الدليل مباشرة بالمحرك البيداغوجي المتقدم:
👉 **[محرك إيصال الفكرة وتلخيصها وتحفيظها علمياً](./references/instruction_summarization_memorization_engine.md)**

ويشمل ثلاث ركائز عملية تلزم الذكاء الاصطناعي:
1. **محرك إيصال الفكرة والشرح الفائق:**
   - تطبيق المعرفة البيداغوجية بالمحتوى (*PCK - Shulman 1986*) عبر تقديم المفهوم بـ 3 مستويات: حسي واقعي، بياني صوري، ورمزي صارم.
   - الشرح الديناميكي وسداد الدَّين البحثي (*Distill & Bret Victor*) بتفكيك حركة المتغيرات.
   - تفعيل أثر التلمذة (*Protégé Effect - Chase et al. 2009*) بطلب شرح المفهوم من التلميذ للوكيل للتحقق من الفهم.
2. **محرك التلخيص المعرفي والتحليل الدلالي:**
   - تطبيق قواعد ماكرو الثلاث لاستيعاب الخطاب (*الحذف، التعميم، والبناء التركيبي - Kintsch & van Dijk 1983*).
   - بناء الخرائط المفاهيمية الهرمية مع قضايا وروابط الربط الصريحة (*Novak 2008 & Ausubel*).
   - الالتزام بنسبة الربع أو الثلث (20%–35%) في تلخيص نصوص العربية مع فحص التطابق اللفظي الثلاثي (منع النسخ الحرفي)، وهيكل الـ *Compte-rendu* في الفرنسية والإنجليزية.
3. **محرك التحفيظ العلمي وترسيخ الذاكرة بعيدة المدى:**
   - التكرار المتباعد التكيفي المقاوم لمنحنى النسيان (*Ebbinghaus 1885 & Dunlosky 2013*).
   - الترميز متعدد الوسائط وأثر الرسم اليدوي (*Fernandes et al. 2018*).
   - تقنية قصر الذاكرة والربط المكاني (*Krokos et al. 2019*: تحسن الاسترجاع بنسبة 8.8% في البيئات المكانية) لحفظ التواريخ والمصطلحات.
   - فترات الراحة اليقظة القصيرة (10 ثوانٍ - *Buch et al., Cell Reports 2021*) لتفعيل إعادة التشغيل العصبي السريع (20–30 مرة بانضغاط زمني 20 ضعفاً) والتنبيه على أهمية النوم لتثبيت المعارف (*Walker 2006*).

---

## 4. المراجع والأدلة المنهجية التخصصية حسب المواد

- **القاموس المصطلحي الوطني الموحد:** [national_pedagogical_glossary.md](./references/national_pedagogical_glossary.md)
- **بروتوكول شبكات التنقيط والتقويم الوزاري الرسمي (ONEC):** [onec_scoring_rubric_engine.md](./references/onec_scoring_rubric_engine.md)
- **مصفوفة التمايز الصارم بين الشعب:** [stream_differentiation_matrix.md](./references/stream_differentiation_matrix.md)
- **بروتوكول التفاعل المعرفي والسلوكي:** [cognitive_interaction_protocol.md](./references/cognitive_interaction_protocol.md)
- **دليل أجرأة الأسس المعرفية والبيداغوجية:** [cognitive_foundation_operationalizer.md](./references/cognitive_foundation_operationalizer.md)
- **محرك إيصال الفكرة وتلخيصها وتحفيظها:** [instruction_summarization_memorization_engine.md](./references/instruction_summarization_memorization_engine.md)
- **إطار التعليم الجامعي والمدارس العليا LMD & CDIO:** [higher_education_cdio_framework.md](./references/higher_education_cdio_framework.md)
- **دليل تقارير الأعمال المخبرية ومذكرات التخرج (TP & PFE):** [university_tp_pfe_methodology.md](./references/university_tp_pfe_methodology.md)
- **الرياضيات:** [mathematics_methodology.md](./references/mathematics_methodology.md)
- **اللغة العربية وآدابها:** [arabic_methodology.md](./references/arabic_methodology.md)
- **علوم الطبيعة والحياة:** [natural_sciences_methodology.md](./references/natural_sciences_methodology.md)
- **العلوم الفيزيائية:** [physics_chemistry_methodology.md](./references/physics_chemistry_methodology.md)
- **الفلسفة:** [philosophy_methodology.md](./references/philosophy_methodology.md)
- **اللغات الأجنبية (فرنسية، إنجليزية، ألمانية):** [foreign_languages_methodology.md](./references/foreign_languages_methodology.md)
- **التاريخ والجغرافيا:** [history_geography_methodology.md](./references/history_geography_methodology.md)
- **العلوم الإسلامية:** [islamic_sciences_methodology.md](./references/islamic_sciences_methodology.md)

---

## 4. مستودع الدراسات والأسس العلمية المحلية (31 مؤلفاً ودراسة)
👉 **[Pedagogical_Science_Foundations/README.md](../../../Pedagogical_Science_Foundations/README.md)**

---

## 5. التعليم الجامعي والمدارس العليا (Higher Education / LMD & CDIO)
- استخدام المصطلحات الثنائية (فرنسية/عربية) حسب التخصص (ST, SM, MI, SNV, Médecine, Droit, Économie).
- هيكلة الأعمال الموجهة (TD) والمخبرية (TP) وحساب الارتيابات وهامش الخطأ.
- معايير مذكرات التخرج (PFE) والتقارير التربصية وفق معايير وزارة التعليم العالي والبحث العلمي (MESRS) ومعايير CDIO العالمية.
