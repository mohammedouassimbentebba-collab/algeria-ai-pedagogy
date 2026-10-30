# -*- coding: utf-8 -*-
"""
BAC Archive Fast Query and Search Engine
Enables searching and retrieving BAC exam topics, questions, and official solutions
by subject, stream, year, topic, or keyword.
"""

import os
import sys
import json
import re
import argparse
from typing import List, Dict, Any, Optional

sys.stdout.reconfigure(encoding='utf-8')

CATALOG_PATH = "BAC_Archives/bac_catalog_index.json"
CORPUS_PATH = "BAC_Archives/bac_text_corpus.jsonl"

def load_catalog() -> Dict[str, Any]:
    if not os.path.exists(CATALOG_PATH):
        print(f"Error: Catalog not found at {CATALOG_PATH}. Please run scripts/build_bac_indexer.py first.")
        sys.exit(1)
    with open(CATALOG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def normalize_text(text: str) -> str:
    if not text:
        return ""
    t = re.sub(r"[إأآا]", "ا", text)
    t = re.sub(r"ة", "ه", t)
    t = re.sub(r"ى", "ي", t)
    t = re.sub(r"[\u064B-\u065F\u0670]", "", t)
    return t.lower()

def search_bac(
    subject: Optional[str] = None,
    stream: Optional[str] = None,
    year: Optional[int] = None,
    doc_type: Optional[str] = None,
    topic: Optional[str] = None,
    query: Optional[str] = None,
    limit: int = 5
) -> List[Dict[str, Any]]:
    catalog_data = load_catalog()
    items = catalog_data.get("catalog", [])
    
    results = []
    norm_query = normalize_text(query) if query else None
    
    for item in items:
        # Filter Subject
        if subject and normalize_text(subject) not in normalize_text(item["subject"]):
            continue
            
        # Filter Stream
        if stream and normalize_text(stream) not in normalize_text(item["stream"]):
            continue
            
        # Filter Year
        if year and item["year"] != year:
            continue
            
        # Filter Type (Sujet vs Corrigé)
        if doc_type:
            dt_norm = normalize_text(doc_type)
            if dt_norm == "sujet" and item["type"] != "Sujet":
                continue
            elif (dt_norm in ["corrige", "تصحيح", "حل"]) and item["type"] != "Corrigé":
                continue
                
        # Filter Topic
        if topic:
            topic_norm = normalize_text(topic)
            item_topics_norm = [normalize_text(t) for t in item.get("detected_topics", [])]
            if not any(topic_norm in t for t in item_topics_norm):
                continue
                
        # Filter Query in text
        match_score = 0
        snippet = ""
        if norm_query:
            prev_norm = normalize_text(item.get("preview_text", ""))
            if norm_query in prev_norm:
                match_score += 2
                idx = prev_norm.find(norm_query)
                start = max(0, idx - 80)
                end = min(len(item["preview_text"]), idx + len(norm_query) + 120)
                snippet = item["preview_text"][start:end].strip()
            else:
                # If query not in preview, check detected topics or filename
                if any(norm_query in normalize_text(t) for t in item.get("detected_topics", [])):
                    match_score += 1
                elif norm_query in normalize_text(item["filename"]):
                    match_score += 1
                else:
                    continue
        else:
            match_score = 1
            
        item_copy = dict(item)
        item_copy["snippet"] = snippet
        item_copy["score"] = match_score
        results.append(item_copy)
        
    # Sort by year descending and score
    results.sort(key=lambda x: (x.get("score", 0), x.get("year") or 0), reverse=True)
    return results[:limit]

def find_paired_file(item: Dict[str, Any]) -> Optional[str]:
    """Given a Sujet, find its Corrigé, and vice versa."""
    catalog_data = load_catalog()
    target_type = "Corrigé" if item.get("type") == "Sujet" else "Sujet"
    item_session = item.get("session", "عادية")
    
    for other in catalog_data.get("catalog", []):
        if (other.get("subject") == item.get("subject") and
            other.get("stream") == item.get("stream") and
            other.get("year") == item.get("year") and
            other.get("session", "عادية") == item_session and
            other.get("type") == target_type):
            return other.get("file_path")
    return None

def deep_text_search(query: str, subject: Optional[str] = None, limit: int = 5) -> List[Dict[str, Any]]:
    """Deep full-text search inside the text corpus."""
    if not os.path.exists(CORPUS_PATH):
        return []
        
    norm_query = normalize_text(query)
    results = []
    
    with open(CORPUS_PATH, "r", encoding="utf-8") as f:
        for line in f:
            entry = json.loads(line)
            if subject and normalize_text(subject) not in normalize_text(entry["subject"]):
                continue
                
            norm_full = normalize_text(entry["text"])
            if norm_query in norm_full:
                count = norm_full.count(norm_query)
                idx = norm_full.find(norm_query)
                start = max(0, idx - 100)
                end = min(len(entry["text"]), idx + len(norm_query) + 200)
                snippet = entry["text"][start:end].replace("\n", " ").strip()
                
                results.append({
                    "id": entry["id"],
                    "file_path": entry["file_path"],
                    "subject": entry["subject"],
                    "stream": entry["stream"],
                    "year": entry["year"],
                    "type": entry["type"],
                    "count": count,
                    "snippet": f"...{snippet}..."
                })
                
    results.sort(key=lambda x: (x["count"], x["year"] or 0), reverse=True)
    return results[:limit]

def main():
    parser = argparse.ArgumentParser(description="محرك الاسترجاع الذكي لأرشيف البكالوريا الجزائري")
    parser.add_argument("--subject", "-s", type=str, help="المادة (مثال: الرياضيات، العلوم الفيزيائية، التاريخ والجغرافيا...)")
    parser.add_argument("--stream", "-b", type=str, help="الشعبة (مثال: علوم تجريبية، رياضيات، تقني رياضي، تسيير واقتصاد، آداب وفلسفة...)")
    parser.add_argument("--year", "-y", type=int, help="سنة البكالوريا (2017 إلى 2026)")
    parser.add_argument("--type", "-t", type=str, choices=["Sujet", "Corrigé", "sujet", "corrige"], help="النوع: Sujet أو Corrigé")
    parser.add_argument("--topic", type=str, help="الوحدة أو الموضوع الدراسي (مثال: المتتاليات، الميكانيك، المناعة، الحرب الباردة...)")
    parser.add_argument("--query", "-q", type=str, help="بحث نصي معمق في محتوى الأسئلة والحلول")
    parser.add_argument("--deep", action="store_true", help="تفعيل البحث المعمق داخل النصوص الكاملة للـ 519 ملف")
    parser.add_argument("--limit", "-n", type=int, default=5, help="الحد الأقصى للنتائج")
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("🔍 محرك البحث والاسترجاع المنهجي لأرشيف البكالوريا الجزائري (ONEC)")
    print("=" * 70)
    
    if args.deep and args.query:
        print(f"🔎 جاري البحث المعمق عن: '{args.query}' في النصوص الكاملة...")
        results = deep_text_search(args.query, subject=args.subject, limit=args.limit)
    else:
        results = search_bac(
            subject=args.subject,
            stream=args.stream,
            year=args.year,
            doc_type=args.type,
            topic=args.topic,
            query=args.query,
            limit=args.limit
        )
        
    print(f"📊 عدد النتائج المطابقة: {len(results)}\n")
    
    for i, r in enumerate(results, 1):
        print(f"[{i}] {r['subject']} | {r['stream']} | دورة {r['year']} ({r.get('session', 'عادية')}) | النوع: {r['type']}")
        print(f"    📄 الملف: {r['file_path']}")
        
        # Check paired file
        paired = find_paired_file(r)
        if paired:
            pair_label = "التصحيح وسلم التنقيط" if r['type'] == "Sujet" else "الموضوع الأصلي"
            print(f"    🔗 {pair_label}: {paired}")
            
        topics = r.get("detected_topics", [])
        if topics:
            print(f"    🏷️ الوحدات المكتشفة: {', '.join(topics)}")
            
        headers = r.get("exercise_headers", [])
        if headers:
            print(f"    📌 هيكل التمارين: {' | '.join(headers[:4])}")
            
        if r.get("snippet"):
            print(f"    📝 مقتطف من النص: \"{r['snippet']}\"")
        print("-" * 70)

if __name__ == "__main__":
    main()
