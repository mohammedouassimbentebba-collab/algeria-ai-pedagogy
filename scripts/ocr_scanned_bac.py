# -*- coding: utf-8 -*-
"""
Parallel Batch OCR Engine for Scanned & Mojibake Algerian BAC PDFs (2017-2026)
Uses PyMuPDF page rendering + 8 Parallel Windows Native WinRT OCR Workers
(Windows.Media.Ocr.OcrEngine) for fast multi-core Arabic/French OCR.
"""

import os
import sys
import json
import time
import shutil
import subprocess
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    import pymupdf as fitz
    fitz.TOOLS.mupdf_display_errors(False)
except ImportError:
    import fitz
    fitz.TOOLS.mupdf_display_errors(False)

sys.stdout.reconfigure(encoding='utf-8')

LATIN_SUBJECTS = {
    "اللغة الفرنسية", "اللغة الإنجليزية", "اللغة الألمانية",
    "اللغة الإسبانية", "اللغة الإيطالية", "اللغة الأمازيغية"
}

POWERSHELL_OCR_SCRIPT = r"""
param([string]$JobsJsonPath, [string]$OutJsonPath)
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Add-Type -AssemblyName System.Runtime.WindowsRuntime
$null = [Windows.Storage.StorageFile, Windows.Storage, ContentType = WindowsRuntime]
$null = [Windows.Media.Ocr.OcrEngine, Windows.Foundation, ContentType = WindowsRuntime]
$null = [Windows.Foundation.IAsyncOperation`1, Windows.Foundation, ContentType = WindowsRuntime]
$null = [Windows.Graphics.Imaging.BitmapDecoder, Windows.Foundation, ContentType = WindowsRuntime]
$null = [Windows.Globalization.Language, Windows.Globalization, ContentType = WindowsRuntime]

$asTaskGeneric = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {
    $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1'
})[0]

Function Await($WinRtTask, $ResultType) {
    $asTask = $asTaskGeneric.MakeGenericMethod($ResultType)
    $netTask = $asTask.Invoke($null, @($WinRtTask))
    $netTask.Wait(-1) | Out-Null
    $netTask.Result
}

$langAr = New-Object Windows.Globalization.Language('ar-SA')
$engineAr = [Windows.Media.Ocr.OcrEngine]::TryCreateFromLanguage($langAr)

$langFr = New-Object Windows.Globalization.Language('fr-FR')
$engineFr = [Windows.Media.Ocr.OcrEngine]::TryCreateFromLanguage($langFr)

$jobs = Get-Content -Path $JobsJsonPath -Raw -Encoding UTF8 | ConvertFrom-Json
$results = @{}

foreach ($job in $jobs) {
    $imgPath = $job.img_path
    $isRtl = $job.is_rtl
    $key = $job.key
    try {
        $file = Await ([Windows.Storage.StorageFile]::GetFileFromPathAsync($imgPath)) ([Windows.Storage.StorageFile])
        $stream = Await ($file.OpenAsync([Windows.Storage.FileAccessMode]::Read)) ([Windows.Storage.Streams.IRandomAccessStream])
        $decoder = Await ([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($stream)) ([Windows.Graphics.Imaging.BitmapDecoder])
        $bitmap = Await ($decoder.GetSoftwareBitmapAsync()) ([Windows.Graphics.Imaging.SoftwareBitmap])
        $engine = if ($isRtl) { $engineAr } else { $engineFr }
        $res = Await ($engine.RecognizeAsync($bitmap)) ([Windows.Media.Ocr.OcrResult])
        $stream.Dispose()

        $lines = foreach ($line in $res.Lines) {
            if ($isRtl) {
                $w = $line.Text -split ' '
                [Array]::Reverse($w)
                $w -join ' '
            } else {
                $line.Text
            }
        }
        $results[$key] = ($lines -join "`n")
    } catch {
        $results[$key] = ""
    }
}

$jsonOut = $results | ConvertTo-Json -Depth 5 -Compress
[System.IO.File]::WriteAllText($OutJsonPath, $jsonOut, [System.Text.Encoding]::UTF8)
"""

def _run_worker(worker_id: int, chunk: list, ps1_path: str, tmp_dir: str) -> dict:
    jobs_json = os.path.join(tmp_dir, f"jobs_{worker_id}.json")
    out_json = os.path.join(tmp_dir, f"out_{worker_id}.json")
    with open(jobs_json, "w", encoding="utf-8") as f:
        json.dump(chunk, f, ensure_ascii=False)
    subprocess.run([
        "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
        "-File", ps1_path, "-JobsJsonPath", jobs_json, "-OutJsonPath", out_json
    ], check=True)
    with open(out_json, "r", encoding="utf-8-sig") as f:
        return json.load(f)

def run_batch_ocr(num_workers: int = 8):
    catalog_path = "BAC_Archives/bac_catalog_index.json"
    corpus_path = "BAC_Archives/bac_text_corpus.jsonl"
    ocr_cache_path = "BAC_Archives/ocr_cache.json"

    with open(catalog_path, "r", encoding="utf-8") as f:
        cat_data = json.load(f)

    mojibake_paths = set()
    if os.path.exists(corpus_path):
        with open(corpus_path, "r", encoding="utf-8") as f:
            for line in f:
                d = json.loads(line)
                if len(re.findall(r'[\u0150-\u01BF]', d.get("text", ""))) > 20:
                    mojibake_paths.add(d["file_path"])

    ocr_cache = {}
    if os.path.exists(ocr_cache_path):
        try:
            with open(ocr_cache_path, "r", encoding="utf-8") as f:
                ocr_cache = json.load(f)
        except Exception:
            ocr_cache = {}

    target_entries = [
        c for c in cat_data["catalog"]
        if (not c.get("has_text") or c["file_path"] in mojibake_paths)
        and c["file_path"] not in ocr_cache
    ]

    print(f"إجمالي الملفات التي تحتاج OCR: {len(target_entries)} ملف")
    if not target_entries:
        return ocr_cache

    tmp_dir = os.path.abspath("BAC_Archives/_ocr_tmp")
    os.makedirs(tmp_dir, exist_ok=True)

    jobs = []
    file_page_keys = {}
    start_render = time.time()

    for idx, entry in enumerate(target_entries):
        pdf_path = entry["file_path"]
        is_rtl = entry["subject"] not in LATIN_SUBJECTS
        page_keys = []
        try:
            doc = fitz.open(pdf_path)
            for pno in range(len(doc)):
                key = f"{idx}_{pno}"
                img_path = os.path.join(tmp_dir, f"page_{key}.png")
                if not os.path.exists(img_path):
                    pix = doc[pno].get_pixmap(dpi=130)
                    pix.save(img_path)
                jobs.append({
                    "key": key,
                    "img_path": img_path,
                    "is_rtl": is_rtl
                })
                page_keys.append(key)
            doc.close()
        except Exception as e:
            print(f"خطأ في تحويل {pdf_path}: {e}")
        file_page_keys[pdf_path] = page_keys

    print(f"تم تجهيز {len(jobs)} صفحة في {time.time() - start_render:.1f}s. بدء {num_workers} معالجات متوازية...")

    ps1_path = os.path.join(tmp_dir, "run_ocr.ps1")
    with open(ps1_path, "w", encoding="utf-8-sig") as f:
        f.write(POWERSHELL_OCR_SCRIPT)

    chunk_size = max(1, (len(jobs) + num_workers - 1) // num_workers)
    chunks = [jobs[i:i + chunk_size] for i in range(0, len(jobs), chunk_size)]

    raw_page_results = {}
    t_ocr = time.time()
    with ThreadPoolExecutor(max_workers=num_workers) as ex:
        futures = {ex.submit(_run_worker, wid, ch, ps1_path, tmp_dir): wid for wid, ch in enumerate(chunks)}
        for fut in as_completed(futures):
            wid = futures[fut]
            part = fut.result()
            raw_page_results.update(part)
            print(f"  [Worker {wid}] اكتمل ({len(part)} صفحة) - الوقت: {time.time() - t_ocr:.1f}s")

    for pdf_path, keys in file_page_keys.items():
        pages_text = []
        for pno, k in enumerate(keys):
            txt = raw_page_results.get(k, "").strip()
            if txt:
                pages_text.append({"page_num": pno + 1, "text": txt})
        ocr_cache[pdf_path] = pages_text

    with open(ocr_cache_path, "w", encoding="utf-8") as f:
        json.dump(ocr_cache, f, ensure_ascii=False, indent=2)

    shutil.rmtree(tmp_dir, ignore_errors=True)
    print(f"✅ اكتمل الـ OCR المتوازي في {time.time() - t_ocr:.1f}s وحُفظ في {ocr_cache_path} ({len(ocr_cache)} ملف)!")
    return ocr_cache

if __name__ == "__main__":
    run_batch_ocr(8)
