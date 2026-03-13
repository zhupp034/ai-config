---
name: pdf-reader
description: Read and inspect PDF files with pdftotext and pdfinfo. Use when Codex needs to extract text from a PDF, inspect PDF metadata or page count, summarize PDF contents, search inside a PDF after conversion, or prepare PDF text for downstream processing.
---

# PDF Reader

Use `pdfinfo` for a fast structural check, then use the bundled script to extract text with `pdftotext`.
Prefer this skill over ad hoc PDF guessing whenever the task depends on the actual contents of a `.pdf` file.
When extraction is empty or the PDF is a scan, use the OCR path backed by `ocrmypdf` and `tesseract`.

## Prerequisite check

Verify the required CLI tools are available:

```bash
command -v pdfinfo
command -v pdftotext
command -v ocrmypdf
command -v tesseract
```

If the text-extraction commands are missing on macOS with Homebrew, install Poppler:

```bash
brew install poppler
```

If OCR commands are missing, install OCR tooling:

```bash
brew install tesseract ocrmypdf
```

## Skill path

```bash
export CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
export PDF_READER="$CODEX_HOME/skills/pdf-reader/scripts/extract_pdf.sh"
```

## Core workflow

1. Run `pdfinfo <file.pdf>` to confirm the file is readable and check page count, title, author, and encryption status.
2. Run the bundled extraction script to get plain text, page-separated text, or Markdown.
3. If the output is empty or nearly empty, rerun with `--ocr` or `--auto-ocr`.
4. Summarize, search, or transform the extracted text based on the user task.
5. When text quality is still poor after OCR, state the limitation explicitly.

## Quick start

Extract text to stdout:

```bash
"$PDF_READER" /absolute/path/file.pdf
```

Extract text to a file:

```bash
"$PDF_READER" /absolute/path/file.pdf --output /tmp/file.txt
```

Extract a page range:

```bash
"$PDF_READER" /absolute/path/file.pdf --pages 1-3
```

Preserve layout when tables or aligned columns matter:

```bash
"$PDF_READER" /absolute/path/file.pdf --layout
```

Extract per-page Markdown:

```bash
"$PDF_READER" /absolute/path/file.pdf --per-page --markdown
```

Force OCR for a scanned PDF:

```bash
"$PDF_READER" /absolute/path/file.pdf --ocr
```

Auto-fallback to OCR when normal extraction is empty:

```bash
"$PDF_READER" /absolute/path/file.pdf --auto-ocr
```

## Recommended patterns

### Read and summarize a PDF

```bash
pdfinfo /absolute/path/file.pdf
"$PDF_READER" /absolute/path/file.pdf > /tmp/file.txt
```

Then read `/tmp/file.txt`, cite page-aware observations when possible, and mention extraction limitations.

### Produce page-aware notes

```bash
"$PDF_READER" /absolute/path/file.pdf --per-page --markdown > /tmp/file.md
```

Use this when the user wants citations, page-by-page notes, or easier downstream parsing.

### OCR a scanned PDF

```bash
"$PDF_READER" /absolute/path/file.pdf --ocr --ocr-lang eng
```

Use this when `pdftotext` yields little or no text.

### Search for a term in a PDF

```bash
"$PDF_READER" /absolute/path/file.pdf | rg "keyword"
```

### Inspect only metadata

```bash
pdfinfo /absolute/path/file.pdf
```

Use this first when the user asks about page count, title, producer, or encryption.

## Guardrails

- Use absolute paths for PDF inputs and outputs.
- Inspect with `pdfinfo` before assuming a damaged or empty extraction.
- If the output is empty or garbled, report that the document may require OCR; do not pretend the PDF had extractable text.
- Use `--layout` for tables, invoices, and columnar documents.
- Use `--per-page --markdown` when page boundaries matter.
- Use `--auto-ocr` for mixed-quality PDFs when you want the script to decide based on output emptiness.
- Default OCR language is `eng`. Homebrew's default Tesseract install on this machine currently includes `eng`, `osd`, and `snum`; install `tesseract-lang` if other languages are needed.
- Keep extracted artifacts in `/tmp` or the working repo unless the user requests another location.
- Do not claim page-accurate citations unless you actually extracted the relevant page range or inspected the source carefully.
- If the script warns that the PDF may require OCR, say that explicitly and avoid overconfident summaries.
