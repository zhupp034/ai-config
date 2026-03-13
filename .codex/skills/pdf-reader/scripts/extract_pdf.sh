#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: extract_pdf.sh <input.pdf> [--output <file>] [--pages <first-last>] [--layout] [--markdown] [--per-page] [--ocr] [--auto-ocr] [--ocr-lang <lang>]

Options:
  --output <file>       Write extracted text to a file instead of stdout.
  --pages <first-last>  Extract only the inclusive page range, for example 2-5.
  --layout              Preserve physical layout for tables or multi-column content.
  --markdown            Wrap output as simple Markdown.
  --per-page            Extract each page separately with page markers.
  --ocr                 Force OCR with ocrmypdf before extracting text.
  --auto-ocr            Run normal extraction first, then OCR if the text is empty.
  --ocr-lang <lang>     Tesseract language code for OCR. Default: eng.
  -h, --help            Show this help.
USAGE
}

cleanup() {
  if [ -n "${tmpdir:-}" ] && [ -d "${tmpdir:-}" ]; then
    rm -rf "$tmpdir"
  fi
}

is_effectively_empty() {
  local file="$1"
  if [ ! -s "$file" ]; then
    return 0
  fi
  if tr -d '[:space:]' < "$file" | wc -c | awk '{exit ($1 == 0 ? 0 : 1)}'; then
    return 0
  fi
  return 1
}

if ! command -v pdftotext >/dev/null 2>&1; then
  echo "pdftotext is not installed. Install poppler first: brew install poppler" >&2
  exit 1
fi

if ! command -v pdfinfo >/dev/null 2>&1; then
  echo "pdfinfo is not installed. Install poppler first: brew install poppler" >&2
  exit 1
fi

if [ "$#" -lt 1 ]; then
  usage >&2
  exit 1
fi

input=""
output=""
page_range=""
layout=0
markdown=0
per_page=0
ocr=0
auto_ocr=0
ocr_lang="eng"

while [ "$#" -gt 0 ]; do
  case "$1" in
    --output)
      [ "$#" -ge 2 ] || { echo "Missing value for --output" >&2; exit 1; }
      output="$2"
      shift 2
      ;;
    --pages)
      [ "$#" -ge 2 ] || { echo "Missing value for --pages" >&2; exit 1; }
      page_range="$2"
      shift 2
      ;;
    --layout)
      layout=1
      shift
      ;;
    --markdown)
      markdown=1
      shift
      ;;
    --per-page)
      per_page=1
      shift
      ;;
    --ocr)
      ocr=1
      shift
      ;;
    --auto-ocr)
      auto_ocr=1
      shift
      ;;
    --ocr-lang)
      [ "$#" -ge 2 ] || { echo "Missing value for --ocr-lang" >&2; exit 1; }
      ocr_lang="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    -*)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 1
      ;;
    *)
      if [ -n "$input" ]; then
        echo "Only one input PDF is supported." >&2
        exit 1
      fi
      input="$1"
      shift
      ;;
  esac
done

if [ -z "$input" ]; then
  echo "Input PDF is required." >&2
  usage >&2
  exit 1
fi

if [ ! -f "$input" ]; then
  echo "Input PDF not found: $input" >&2
  exit 1
fi

if [ "$ocr" -eq 1 ] && [ "$auto_ocr" -eq 1 ]; then
  echo "Use either --ocr or --auto-ocr, not both." >&2
  exit 1
fi

tmpdir="$(mktemp -d)"
trap cleanup EXIT

args=()
if [ "$layout" -eq 1 ]; then
  args+=("-layout")
fi

page_start=""
page_end=""
if [ -n "$page_range" ]; then
  if [[ "$page_range" =~ ^([0-9]+)-([0-9]+)$ ]]; then
    page_start="${BASH_REMATCH[1]}"
    page_end="${BASH_REMATCH[2]}"
    if [ "$page_start" -gt "$page_end" ]; then
      echo "Invalid --pages range: $page_range" >&2
      exit 1
    fi
  else
    echo "Invalid --pages format: $page_range (expected first-last)" >&2
    exit 1
  fi
fi

if [ -z "$page_end" ]; then
  page_end="$(pdfinfo "$input" | awk -F': *' '/^Pages:/ {print $2; exit}')"
fi

if [ -z "$page_end" ]; then
  echo "Could not determine PDF page count: $input" >&2
  exit 1
fi

if [ -z "$page_start" ]; then
  page_start=1
fi

if [ "$page_start" -gt "$page_end" ]; then
  echo "Requested page range starts after the end of the document." >&2
  exit 1
fi

ocr_input="$input"

run_ocr() {
  if ! command -v ocrmypdf >/dev/null 2>&1; then
    echo "ocrmypdf is not installed. Install it first: brew install ocrmypdf" >&2
    exit 1
  fi
  if ! command -v tesseract >/dev/null 2>&1; then
    echo "tesseract is not installed. Install it first: brew install tesseract" >&2
    exit 1
  fi

  local ocr_pdf="$tmpdir/ocr.pdf"
  ocrmypdf --skip-text --language "$ocr_lang" "$input" "$ocr_pdf" >/dev/null
  ocr_input="$ocr_pdf"
}

render_single_stream() {
  local raw_file="$tmpdir/raw.txt"
  pdftotext "${args[@]}" -f "$page_start" -l "$page_end" "$ocr_input" "$raw_file"

  if [ "$markdown" -eq 1 ]; then
    printf '# %s\n\n' "$(basename "$input")"
  fi
  cat "$raw_file"

  if is_effectively_empty "$raw_file"; then
    echo "Warning: extracted text is empty or whitespace-only. The PDF may be image-based and require OCR." >&2
  fi
}

render_per_page() {
  local combined="$tmpdir/combined.txt"
  local page raw_file

  : > "$combined"
  for ((page=page_start; page<=page_end; page++)); do
    raw_file="$tmpdir/page-$page.txt"
    pdftotext "${args[@]}" -f "$page" -l "$page" "$ocr_input" "$raw_file"

    if [ "$markdown" -eq 1 ]; then
      {
        printf '## Page %s\n\n' "$page"
        cat "$raw_file"
        printf '\n\n'
      } >> "$combined"
    else
      {
        printf '===== Page %s =====\n' "$page"
        cat "$raw_file"
        printf '\n\n'
      } >> "$combined"
    fi
  done

  cat "$combined"

  if is_effectively_empty "$combined"; then
    echo "Warning: extracted text is empty or whitespace-only. The PDF may be image-based and require OCR." >&2
  fi
}

result_file="$tmpdir/result.txt"
if [ "$ocr" -eq 1 ]; then
  run_ocr
fi

render_output() {
  if [ "$per_page" -eq 1 ]; then
    render_per_page
  else
    render_single_stream
  fi
}

render_output > "$result_file"

if [ "$auto_ocr" -eq 1 ] && is_effectively_empty "$result_file"; then
  echo "Info: normal extraction was empty; retrying with OCR." >&2
  run_ocr
  render_output > "$result_file"
fi

if [ -n "$output" ]; then
  mkdir -p "$(dirname "$output")"
  cp "$result_file" "$output"
  echo "Wrote text to $output"
  exit 0
fi

cat "$result_file"
