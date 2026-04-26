#!/usr/bin/env python3
"""
normalize_pdf.py — Sayfa boyutlarını A4'e normalize eder.

Kullanım:
  python3 normalize_pdf.py input.pdf
  python3 normalize_pdf.py input.pdf --keep "1,3,5"
  python3 normalize_pdf.py input.pdf --keep "2,4" --output custom_output.pdf

Argümanlar:
  input           : Kaynak PDF dosyası
  --keep          : Dokunulmayacak sayfa numaraları (1'den başlar), virgülle ayrılmış, tırnak içinde
  --output / -o   : Çıktı dosyası adı (varsayılan: <input>_normalized.pdf)

Davranış:
  - --keep listesindeki sayfalar olduğu gibi kalır (örn. A2 sayfalar).
  - Diğer sayfalar A4'e sığdırılır:
      * Büyük sayfalar küçültülür (en-boy oranı korunur).
      * Küçük sayfalar büyütülmez; ortaya hizalanarak A4 mediabox içine alınır.
  - Sayfa yönü (portre/yatay) otomatik algılanır.
"""

import argparse
import sys
from pathlib import Path

try:
    from pypdf import PdfReader, PdfWriter
    from pypdf.generic import RectangleObject
except ImportError:
    sys.exit("Hata: pypdf bulunamadı. Lütfen kurun: pip install pypdf")


# --- Sayfa boyutları (puan / pt cinsinden, 1 pt = 1/72 inç) ---
A4_W = 595.276   # 210 mm
A4_H = 841.890   # 297 mm


def parse_keep_pages(raw: str) -> set[int]:
    """'1,3,5' gibi bir string'i 0-tabanlı indeks setine çevirir."""
    pages = set()
    for token in raw.split(","):
        token = token.strip()
        if not token:
            continue
        if not token.isdigit():
            sys.exit(f"Hata: Geçersiz sayfa numarası: '{token}'. Sadece pozitif tam sayı girin.")
        n = int(token)
        if n < 1:
            sys.exit(f"Hata: Sayfa numaraları 1'den başlamalıdır, '{n}' geçersiz.")
        pages.add(n - 1)   # 0-tabanlı indekse çevir
    return pages


def fit_to_a4(page) -> None:
    """
    Sayfayı yerinde A4'e normalize eder.
    - Büyükse: A4'e sığacak şekilde küçültülür (en-boy oranı korunur).
    - Küçükse: Büyütülmez; A4 tuval içinde ortalanır.
    """
    mb = page.mediabox
    pw = float(mb.width)
    ph = float(mb.height)

    # Sayfa yönüne göre hedef A4 boyutunu seç
    if pw > ph:           # yatay sayfa → yatay A4
        target_w, target_h = A4_H, A4_W
    else:                 # portre veya kare → portre A4
        target_w, target_h = A4_W, A4_H

    scale = min(target_w / pw, target_h / ph)

    if scale < 1.0:
        # İçeriği küçült
        page.scale_by(scale)
        # Mediabox'ı da küçültülmüş boyuta ayarla, sonra A4'e genişlet
        new_w = pw * scale
        new_h = ph * scale
    else:
        # Küçük sayfa: içerik olduğu gibi kalır, sadece tuval A4 yapılır
        new_w = pw
        new_h = ph

    # İçeriği A4 tuvalinde ortala
    offset_x = (target_w - new_w) / 2
    offset_y = (target_h - new_h) / 2

    if offset_x != 0 or offset_y != 0:
        # Mevcut content stream'e translate uygula
        page.add_transformation(
            [1, 0, 0, 1, offset_x, offset_y],
            expand=False
        )

    # Mediabox'ı tam A4 yap
    page.mediabox = RectangleObject([0, 0, target_w, target_h])

    # CropBox varsa sıfırla
    if "/CropBox" in page:
        page.cropbox = RectangleObject([0, 0, target_w, target_h])


def normalize_pdf(input_path: str, keep_pages: set[int], output_path: str) -> None:
    reader = PdfReader(input_path)
    writer = PdfWriter()
    total = len(reader.pages)

    print(f"Kaynak: {input_path}  ({total} sayfa)")
    if keep_pages:
        human_readable = sorted(p + 1 for p in keep_pages)
        print(f"Dokunulmayacak sayfalar: {human_readable}")

    for i, page in enumerate(reader.pages):
        page_num = i + 1
        mb = page.mediabox
        orig_w = float(mb.width)
        orig_h = float(mb.height)

        if i in keep_pages:
            writer.add_page(page)
            print(f"  Sayfa {page_num:>4}: ATLAIDI  ({orig_w:.1f} x {orig_h:.1f} pt)")
        else:
            fit_to_a4(page)
            writer.add_page(page)
            new_mb = page.mediabox
            print(
                f"  Sayfa {page_num:>4}: "
                f"{orig_w:.1f} x {orig_h:.1f} pt  →  "
                f"{float(new_mb.width):.1f} x {float(new_mb.height):.1f} pt"
            )

    with open(output_path, "wb") as f:
        writer.write(f)

    print(f"\nKaydedildi: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="PDF sayfalarını A4'e normalize eder; seçili sayfaları olduğu gibi bırakır."
    )
    parser.add_argument("input", help="Kaynak PDF dosyası")
    parser.add_argument(
        "--keep", "-k",
        default="",
        metavar='"1,3,5"',
        help="Dokunulmayacak sayfa numaraları (virgülle ayrılmış, tırnak içinde)"
    )
    parser.add_argument(
        "--output", "-o",
        default="",
        help="Çıktı dosyası (varsayılan: <girdi>_normalized.pdf)"
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        sys.exit(f"Hata: Dosya bulunamadı: {args.input}")
    if input_path.suffix.lower() != ".pdf":
        sys.exit("Hata: Girdi dosyası .pdf uzantılı olmalıdır.")

    keep_pages = parse_keep_pages(args.keep) if args.keep.strip() else set()

    output_path = args.output if args.output else str(input_path.with_stem(input_path.stem + "_normalized"))

    # Girdi ile aynı yere yazmayı engelle
    if Path(output_path).resolve() == input_path.resolve():
        sys.exit("Hata: Çıktı dosyası girdi dosyasıyla aynı olamaz.")

    normalize_pdf(str(input_path), keep_pages, output_path)


if __name__ == "__main__":
    main()
