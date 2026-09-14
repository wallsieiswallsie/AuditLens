# AuditLens — penjelasan Bahasa Indonesia

AuditLens adalah proyek portofolio pendidikan untuk mempelajari audit digital, pengendalian internal, risiko TI, analisis sistem dan rekayasa perangkat lunak dengan data sintetis. Proyek ini tidak menggunakan atau mengklaim metodologi milik PwC maupun organisasi lain.

Status terbaru: stabilisasi dan Local CLI Audit Framework sudah diimplementasikan dan diverifikasi lokal dengan PostgreSQL 17.5. Framework mengambil snapshot melalui pembaca terbatas, memvalidasi hash, lalu menyimpan run, provenance dan hasil lokal. Hanya framework.health tersedia; belum ada detektor bisnis atau autentikasi. Railway belum diverifikasi langsung. Tahap berikutnya Audit Policy + Detector SDK. Lihat [catatan verifikasi](VERIFICATION.md) dan [panduan framework](AUDIT-FRAMEWORK.md).

## Tujuan dan cara kerja
Bayangkan perusahaan latihan yang mencatat faktur dan pembayaran. Sistem bisnis menjalankan proses operasional. AuditLens bertindak sebagai meja pemeriksaan yang membaca data, mencari penyimpangan dan menyimpan hasil pemeriksaan secara terpisah.

Alur lokal saat ini: PostgreSQL → ekstraksi read-only → snapshot JSONL dan manifest/hash → validasi → konteks beku → framework.health → artefak hasil lokal. Kontrak bukti dan temuan tersedia untuk detektor masa depan. AuditLens tidak mengubah sumber dan detektor tidak memperoleh koneksi database.

## Komponen teknis
React 19 dan Vite menyediakan antarmuka. React Router mengatur halaman. Tailwind CSS dan DaisyUI menyediakan gaya dasar. Hapi pada Node.js menyediakan API. PostgreSQL menyimpan data, sedangkan Knex mengatur koneksi dan migrasi. Python, Pandas dan SQL akan menjalankan analisis tabel. JWT direncanakan untuk autentikasi; belum diimplementasikan.

Satu database bernama auditlens memiliki skema business dan audit. Skema business berisi rancangan pegawai, akun, peran, izin, pemasok, faktur, persetujuan, pembayaran dan log. Skema audit berisi rancangan identitas auditor, risiko, kontrol, pengujian, pelaksanaan, hasil, bukti dan temuan. Akun auditor berbeda dari akun pegawai yang diperiksa. Kredensial pembaca sumber harus hanya memiliki izin SELECT; kredensial migrasi tidak boleh digunakan sebagai akun aplikasi.

## Konsep penting
Risiko adalah kemungkinan sesuatu merugikan terjadi. Kontrol adalah tindakan untuk mengurangi risiko tersebut. Prosedur audit menjelaskan cara memeriksa kontrol. Exception adalah kondisi yang ditandai aturan dan masih perlu diperiksa. Bukti adalah informasi yang mendukung pengamatan. Finding atau temuan adalah kesimpulan yang telah ditelaah. Rekomendasi adalah usulan perbaikan.

Contoh: akun pegawai nonaktif masih aktif. Data pegawai dan akun menjadi bukti. Auditor memeriksa apakah ada alasan yang disetujui sebelum membuat temuan. Jumlah exception bukan bukti otomatis adanya kecurangan.

RBAC mengatur akses berdasarkan peran. Segregation of Duties atau pemisahan tugas mencegah satu orang menguasai langkah yang bertentangan, misalnya membuat sekaligus menyetujui pembayaran. Akun dormant tidak digunakan selama batas waktu tertentu. Batas waktu harus ditetapkan sebagai parameter kebijakan.

## Model data dan integritas
Status pegawai dipisahkan dari status akun agar akses pegawai nonaktif dapat diuji. Peran dan izin menggunakan tabel penghubung. Satu faktur dapat memiliki beberapa pembayaran parsial. Nilai uang memakai decimal, waktu memakai timestamptz. Bukti disimpan sebagai salinan dengan identitas sumber; tidak bergantung pada baris sumber yang dapat berubah. Hash membantu mendeteksi perubahan bila dibandingkan dengan nilai terpercaya, tetapi bukan jaminan terhadap administrator database.

## Siklus pemeriksaan
Pahami proses → identifikasi risiko → identifikasi kontrol → tentukan tujuan dan prosedur → ambil dan validasi data → jalankan pengujian → tinjau exception → dokumentasikan temuan → laporkan hasil. Data tidak lengkap harus menghasilkan status gagal atau tidak dapat disimpulkan, bukan lulus.

Temuan bergerak dari draft, in_review, open, remediated hingga closed. Pemilik proses menangani perbaikan dan penelaah memverifikasi penutupan.

## Kondisi saat ini dan langkah berikutnya
Phase 0 dan Phase 1 tetap terverifikasi. Acceptance PostgreSQL juga menjalankan CLI snapshot dua kali, membandingkan hash, menjalankan audit tanpa koneksi database, menolak snapshot yang diubah dan membuktikan sumber tetap sama. Framework memakai dependensi pg Node yang sudah tersedia melalui transport terbatas; Python memiliki kontrak dan eksekusi. Identitas operator eksplisit atau local, tanpa membaca nama pengguna mesin. Ground truth hanya untuk evaluasi, tidak dimuat runtime. Web/API tetap terpisah dan Railway belum diverifikasi. Tahap selanjutnya Audit Policy + Detector SDK; lihat [verifikasi](VERIFICATION.md) dan [roadmap](13-DEVELOPMENT-ROADMAP.md).

Pelajari [arsitektur](03-SYSTEM-ARCHITECTURE.md), [ERD](04-ERD.md), [kamus data](05-DATA-DICTIONARY.md), [katalog pengujian](08-AUDIT-TEST-CATALOG.md) dan [pertanyaan terbuka](OPEN-QUESTIONS.md). Petunjuk menjalankan aplikasi tersedia di [README](../README.md).
