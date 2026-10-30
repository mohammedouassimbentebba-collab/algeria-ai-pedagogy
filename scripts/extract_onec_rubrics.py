# -*- coding: utf-8 -*-
"""
Real ONEC Scoring Rubric Extractor (2017-2026)
Parses all official ONEC Corrigés in BAC_Archives/bac_text_corpus.jsonl to extract
real quarter-point grading allocations (0.25, 0.50, 0.75, 1.00, 1.50, 2.00) alongside
their adjacent answer elements (عناصر الإجابة / Éléments de réponse).
"""

import os
import sys
import json
import re
from collections import Counter
from typing import Dict, Any, List

sys.stdout.reconfigure(encoding='utf-8')

MARK_REGEX = re.compile(
    r"(?:(\d)\s*[x×*]\s*)?\b(0[.,](?:25|50|5|75)|1[.,](?:00|0|25|50|5|75)|2[.,](?:00|0|50|5))\b"
)

HEADER_REGEX = re.compile(
    r"(الموضوع\s+(?:الأول|الثاني|1|2)|التمرين\s+(?:الأول|الثاني|الثالث|الرابع|الخامس|[12345])|المسألة|الجزء\s+(?:الأول|الثاني)|Exercice\s*\d+|Part\s*\w+|Topic\s*\w+)",
    re.IGNORECASE
)

def _parse_mark_value(match: re.Match) -> float:
    mult_str = match.group(1)
    val_str = match.group(2).replace(",", ".")
    val = float(val_str)
    mult = int(mult_str) if mult_str else 1
    total = round(mult * val, 2)
    # Round to nearest 0.25
    return round(total * 4) / 4.0

def _is_meaningful_step_line(line: str) -> bool:
    s = line.strip()
    if len(s) < 6 or len(s) > 220:
        return False
    # Ignore pure numbers/marks lines or page headers
    if re.fullmatch(r"[\d\s.,/+-x×*:()ننقطةنقاطptpts]+", s, re.IGNORECASE):
        return False
    if any(skip in s for skip in ["صفحة", "الديوان الوطني", "وزارة التربية", "امتحان بكالوريا", "الإجابة النموذجية", "مجزأة", "المجموع"]):
        return False
    return True

def extract_rubrics_from_corriges(
    corpus_path: str = "BAC_Archives/bac_text_corpus.jsonl",
    output_path: str = "BAC_Archives/onec_extracted_rubrics.json"
) -> Dict[str, Any]:
    corriges = []
    with open(corpus_path, "r", encoding="utf-8") as f:
        for line in f:
            doc = json.loads(line)
            if doc.get("type") == "Corrigé":
                corriges.append(doc)

    print(f"فحص {len(corriges)} تصحيح وزاري رسمي (Corrigé) لاستخراج سلالم التنقيط الحقيقية...")

    extracted_rubrics = []
    by_subject_counts = Counter()
    total_items_extracted = 0

    for doc in corriges:
        lines = [ln.strip() for ln in doc.get("text", "").splitlines() if ln.strip()]
        current_header = "عناصر الإجابة"
        doc_items = []
        used_step_lines = set()

        for idx, ln in enumerate(lines):
            h_match = HEADER_REGEX.search(ln)
            if h_match and len(ln) < 90:
                current_header = ln

            m_match = MARK_REGEX.search(ln)
            if not m_match:
                continue

            pts = _parse_mark_value(m_match)
            if pts <= 0 or pts > 6.0 or (pts * 4) % 1 != 0:
                continue

            # Check if the current line itself also contains the answer element text
            line_without_mark = MARK_REGEX.sub("", ln).strip(" :.-()نقطةنقاطptpts")
            step_text = ""
            if _is_meaningful_step_line(line_without_mark) and len(line_without_mark) >= 12:
                step_text = line_without_mark
                used_step_lines.add(idx)
            else:
                # Look at adjacent lines in the table (lines[idx-3 : idx+4])
                for offset in (-1, 1, -2, 2, -3, 3):
                    cand_idx = idx + offset
                    if 0 <= cand_idx < len(lines) and cand_idx not in used_step_lines:
                        cand = lines[cand_idx]
                        cand_clean = MARK_REGEX.sub("", cand).strip(" :.-()")
                        if _is_meaningful_step_line(cand_clean):
                            step_text = cand_clean
                            used_step_lines.add(cand_idx)
                            break

            if step_text:
                doc_items.append({
                    "exercise": current_header,
                    "step_criterion": step_text,
                    "points": pts,
                    "raw_mark_token": m_match.group(0)
                })
                if len(doc_items) >= 35:
                    break

        if doc_items:
            extracted_rubrics.append({
                "corrige_id": doc["id"],
                "file_path": doc["file_path"],
                "subject": doc["subject"],
                "stream": doc["stream"],
                "year": doc["year"],
                "session": doc.get("session", "عادية"),
                "text_source": doc.get("text_source", "digital"),
                "detected_topics": doc.get("detected_topics", []),
                "items_count": len(doc_items),
                "total_points_sampled": round(sum(i["points"] for i in doc_items), 2),
                "rubric_items": doc_items
            })
            by_subject_counts[doc["subject"]] += len(doc_items)
            total_items_extracted += len(doc_items)

    summary = {
        "total_corriges_processed": len(corriges),
        "corriges_with_structured_rubrics": len(extracted_rubrics),
        "total_rubric_steps_extracted": total_items_extracted,
        "steps_by_subject": dict(by_subject_counts),
        "rubrics": extracted_rubrics
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"✅ تم استخراج {total_items_extracted} عنصر تنقيط حقيقي من {len(extracted_rubrics)} تصحيح وزاري في {output_path}!")
    return summary

if __name__ == "__main__":
    extract_rubrics_from_corriges()
