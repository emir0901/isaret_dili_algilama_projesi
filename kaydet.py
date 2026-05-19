"""
Otomatik Veri Kaydedici
=======================
Arduino'dan seri port üzerinden veri okur, veriokuma.csv'ye yazar.
400 satır dolunca otomatik durur.

Kullanım:
    python3 kaydet.py A        → A harfi, oturarak (posture=0)
    python3 kaydet.py B 1      → B harfi, ayakta (posture=1)
"""

import serial
import sys
import time
import csv
import os

# ─── AYARLAR ───────────────────────────────────────────
PORT      = '/dev/cu.usbserial-0001'
BAUD      = 115200
HEDEF     = 400
CSV_PATH  = 'isaret_dili_izleme/veriokumayeni.csv'
# ───────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print("Kullanım: python3 kaydet.py <HARF> [posture=0]")
        print("Örnek:    python3 kaydet.py A")
        print("Örnek:    python3 kaydet.py B 1   (ayakta)")
        sys.exit(1)

    label   = sys.argv[1].strip().upper()
    posture = int(sys.argv[2]) if len(sys.argv) > 2 else 0

    print(f"\n{'='*45}")
    print(f"  HARF    : {label}")
    print(f"  DURUŞ   : {'Ayakta' if posture else 'Oturarak'}")
    print(f"  HEDEF   : {HEDEF} satır")
    print(f"  DOSYA   : {CSV_PATH}")
    print(f"{'='*45}")
    print("  Arduino'yu yükle, sonra ENTER'a bas...")
    input()

    # Seri porta bağlan
    try:
        ser = serial.Serial(PORT, BAUD, timeout=2)
        print(f"  ✔ Bağlandı: {PORT}")
    except Exception as e:
        print(f"  ✘ Port hatası: {e}")
        sys.exit(1)

    time.sleep(1.5)  # Arduino reset bekle
    ser.reset_input_buffer()

    kayit = 0
    csv_exists = os.path.isfile(CSV_PATH) and os.path.getsize(CSV_PATH) > 5

    with open(CSV_PATH, 'a', newline='') as f:
        writer = csv.writer(f)
        if not csv_exists:
            writer.writerow(['f1','f2','f3','f4','f5','ax','ay','az','posture','label'])

        print(f"\n  Kayıt başladı...\n")
        start = time.time()

        while kayit < HEDEF:
            try:
                raw = ser.readline().decode('utf-8', errors='ignore').strip()
            except:
                continue

            if not raw or raw.startswith('#'):
                continue  # yorum satırları atla

            parts = raw.split(',')

            # Arduino 8 sütun gönderiyor: f1,f2,f3,f4,f5,ax,ay,az
            if len(parts) == 8:
                try:
                    vals = [float(x) for x in parts[:8]]
                    writer.writerow(vals + [posture, label])
                    kayit += 1
                except:
                    continue
            else:
                continue  # Beklenmedik format, atla

            # İlerleme göster
            if kayit % 50 == 0 or kayit == HEDEF:
                pct  = int(kayit / HEDEF * 100)
                bar  = '█' * (pct // 5) + '░' * (20 - pct // 5)
                sure = time.time() - start
                print(f"  [{bar}] %{pct:3d}  ({kayit}/{HEDEF})  {sure:.1f}s")
                f.flush()

    ser.close()
    print(f"\n  ✔ TAMAMLANDI! '{label}' için {HEDEF} satır kaydedildi.")
    print(f"  Toplam süre: {time.time()-start:.1f} saniye\n")

if __name__ == '__main__':
    main()
