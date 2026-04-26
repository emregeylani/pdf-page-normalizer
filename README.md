normalize_pdf
Normalizes PDFs with inconsistent page sizes to A4. Specific pages (e.g. A2) can be preserved as-is.
Installation
```bash
pip install pypdf
```
Usage
```bash
python3 normalize_pdf.py <input.pdf> [--keep "page,numbers"] [--output output.pdf]
```
Examples
```bash
# Normalize all pages to A4
python3 normalize_pdf.py document.pdf

# Keep pages 2 and 5 untouched
python3 normalize_pdf.py document.pdf --keep "2,5"

# Specify output filename
python3 normalize_pdf.py document.pdf --keep "2,5" --output result.pdf
```
Parameters
Parameter	Short	Description
`input`	—	Source PDF file
`--keep`	`-k`	Page numbers to leave untouched (comma-separated, quoted)
`--output`	`-o`	Output filename (default: `<input>_normalized.pdf`)
`--help`	`-h`	Show help message
Behavior
Pages in the `--keep` list are not modified.
Pages larger than A4 are scaled down to fit (aspect ratio preserved).
Pages smaller than A4 are not scaled up; they are centered on an A4 canvas.
Landscape pages are normalized to landscape A4 (297×210 mm).
