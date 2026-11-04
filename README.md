# Pemutar Musik Python Sederhana

Proyek ini adalah hasil **vibe coding** yang dibuat dengan tujuan **belajar**
pengembangan aplikasi desktop menggunakan Python. Kode dan fitur dikembangkan
secara eksperimen sambil mempelajari GUI, pemutaran audio, penyimpanan data,
serta pembuatan aplikasi executable untuk Windows.

## Tentang Aplikasi

Pemutar Musik adalah aplikasi desktop berbasis `tkinter` untuk memutar file
audio di Windows. Pemutaran audio menggunakan Windows MCI (`winmm.dll`) sehingga
proyek ini tidak memerlukan library pemutar audio pihak ketiga.

## Fitur

- Memilih satu atau beberapa file audio
- Menambahkan seluruh audio dari sebuah folder
- Playlist lagu
- Putar, jeda, lanjutkan, berhenti, dan navigasi lagu
- Acak playlist
- Ulang playlist atau satu lagu
- Atur volume dan posisi pemutaran
- Menampilkan durasi dan waktu berjalan lagu
- Menyimpan serta menghapus lirik untuk setiap lagu
- Menyimpan playlist, volume, dan lirik ke file JSON

Format yang didaftarkan oleh aplikasi:
`.mp3`, `.wav`, `.wma`, `.mid`, `.midi`, dan `.ogg`. Dukungan format akhir tetap
bergantung pada codec Windows yang tersedia di komputer.

## Teknologi

- Python 3
- `tkinter` untuk antarmuka desktop
- Windows MCI API melalui `winmm.dll`
- JSON untuk menyimpan konfigurasi dan data playlist
- PyInstaller untuk membuat aplikasi Windows executable

## Menjalankan dari Source

Aplikasi menggunakan modul bawaan Python. Pastikan Python dan Tkinter sudah
tersedia, lalu jalankan source `latpy.py`:

```bat
cd "C:\Users\hyang\OneDrive\Desktop\python learning\projek mandiri\projek-mp3-python-sederhana"
python latpy.py
```

> Proyek ini khusus dibuat untuk Windows karena bergantung pada `winmm.dll`.

## Menjalankan Versi Executable

Versi executable sudah tersedia pada:

```text
dist\PemutarMusik.exe
```

Jalankan langsung dengan mengeklik atau mengetik namanya melalui Command Prompt.

## Data Aplikasi

Playlist, volume, dan lirik disimpan secara otomatis ke file
`music_player_data.json`.

- Saat dijalankan sebagai source, file dibuat di folder source.
- Saat dijalankan sebagai executable, file dibuat di folder tempat
  `PemutarMusik.exe` berada.

## Build dengan PyInstaller

Konfigurasi PyInstaller tersedia pada `PemutarMusik.spec`.

```bat
cd "C:\Users\hyang\OneDrive\Desktop\python learning\projek mandiri\projek-mp3-python-sederhana"
pyinstaller PemutarMusik.spec
```

Hasil executable akan berada pada folder `dist`.

## Struktur Folder

```text
projek-mp3-python-sederhana/
├── README.md
├── PemutarMusik.spec        # Konfigurasi PyInstaller
├── latpy.py                 # Source utama aplikasi
├── build/                   # Berkas proses build PyInstaller
│   └── PemutarMusik/
└── dist/                    # Output aplikasi executable
    └── PemutarMusik.exe
```

## Tujuan Pembelajaran

Proyek sederhana ini dibuat untuk berlatih:

- Membuat GUI dengan Tkinter
- Mengelola state aplikasi
- Mengontrol perangkat audio Windows
- Membaca dan menulis file JSON
- Membuat playlist dan fitur pemutaran berulang
- Mengemas program Python menjadi executable

Kode masih dapat berkembang dan belum ditujukan sebagai pemutar musik produksi.
