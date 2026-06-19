"""
main.py - orkestrator: jalankan semua proses analisis & regenerasi aset paper.

Arsitektur (DRY - satu sumber kebenaran di common.py):
  common.py           mesin perhitungan bersama (data, statistik, CAPM, GMVP,
                      frontier, out-of-sample). Diunduh sekali lalu di-cache.
  sector_analysis.py  Tabel 1 - kinerja 11 sektor BEI (universum berbeda)
  figures.py          semua figur paper (Gambar 1-6) -> outputs/
  calculation.py      cetak seluruh angka kunci paper (bukti perhitungan)

Catatan:
  - Paper dikompilasi di Overleaf, jadi TIDAK ada langkah pdflatex di sini.

Jalankan dari dalam folder proyek:  python main.py
Hasil: folder 'outputs/' (figur paper + tabel sektor).
"""
import subprocess
import sys

SCRIPTS = [
    ("sector_analysis.py", "Tabel 1 - kinerja 11 sektor BEI"),
    ("figures.py",         "Gambar 1-6 - semua figur paper -> outputs/"),
    ("calculation.py",     "Cetak seluruh angka kunci paper"),
]


def main():
    for script, desc in SCRIPTS:
        print(f"\n=== {script}  ({desc}) ===", flush=True)
        subprocess.run([sys.executable, script], check=True)
    print("\n[SELESAI] Semua proses analisis & figur paper diperbarui.")
    print("Figur paper & tabel sektor ada di 'outputs/'.")


if __name__ == "__main__":
    main()
