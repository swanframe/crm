import json
import os
from flask import g, request, session

# Direktori tempat file terjemahan JSON disimpan
TRANSLATIONS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'translations')
# Bahasa default jika tidak ada preferensi yang ditemukan
DEFAULT_LANG = 'en'
# Bahasa yang didukung
SUPPORTED_LANGS = ['en', 'id', 'zh']

def load_translations(lang_code):
    """
    Memuat terjemahan dari file JSON yang sesuai dengan kode bahasa.
    Mengembalikan kamus terjemahan.
    """
    filepath = os.path.join(TRANSLATIONS_DIR, f'{lang_code}.json')
    if not os.path.exists(filepath):
        # Jika file bahasa tidak ditemukan, kembali ke bahasa default
        print(f"Warning: Translation file not found for {lang_code}, falling back to {DEFAULT_LANG}.")
        filepath = os.path.join(TRANSLATIONS_DIR, f'{DEFAULT_LANG}.json')

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading translation file {filepath}: {e}")
        return {} # Mengembalikan kamus kosong jika ada kesalahan

def get_locale():
    """
    Menentukan bahasa yang akan digunakan berdasarkan:
    1. Parameter 'lang' di URL
    2. Preferensi 'lang' di sesi
    3. Header Accept-Language dari browser
    4. Bahasa default
    """
    # 1. Cek parameter 'lang' di URL
    if 'lang' in request.args and request.args['lang'] in SUPPORTED_LANGS:
        session['lang'] = request.args['lang'] # Simpan di sesi untuk persistensi
        return request.args['lang']

    # 2. Cek preferensi 'lang' di sesi
    if 'lang' in session and session['lang'] in SUPPORTED_LANGS:
        return session['lang']

    # 3. Cek header Accept-Language dari browser (opsional, bisa lebih kompleks)
    # Untuk kesederhanaan, kita hanya akan mengambil yang pertama jika ada
    # if request.accept_languages:
    #     for lang in request.accept_languages.values():
    #         if lang in SUPPORTED_LANGS:
    #             session['lang'] = lang
    #             return lang

    # 4. Kembali ke bahasa default
    session['lang'] = DEFAULT_LANG # Simpan default di sesi
    return DEFAULT_LANG

def get_translation(key, **kwargs):
    """
    Mengambil string terjemahan berdasarkan kunci.
    Mendukung placeholder (misalnya, "Hello {name}").
    """
    # Pastikan terjemahan sudah dimuat ke g.translations
    if not hasattr(g, 'translations') or not g.translations:
        # Jika belum dimuat (misalnya, pada skenario error atau akses langsung tanpa before_request),
        # coba muat bahasa default. Ini adalah fallback, bukan cara utama.
        g.translations = load_translations(DEFAULT_LANG)
        print("Warning: g.translations not loaded, falling back to default.")

    parts = key.split('.')
    current_dict = g.translations
    for part in parts:
        if isinstance(current_dict, dict) and part in current_dict:
            current_dict = current_dict[part]
        else:
            # Jika kunci tidak ditemukan, kembalikan kunci itu sendiri atau pesan error
            print(f"Warning: Translation key '{key}' not found.")
            return f"Missing translation for: {key}"

    # Jika nilai adalah string, format dengan kwargs
    if isinstance(current_dict, str):
        try:
            return current_dict.format(**kwargs)
        except KeyError as e:
            print(f"Warning: Missing placeholder '{e}' in translation for key '{key}'.")
            return current_dict # Kembalikan string tanpa format jika placeholder tidak cocok
    return current_dict # Mengembalikan nilai jika bukan string (misalnya, sub-dict)

def init_app_localization(app):
    """
    Menginisialisasi pengaturan lokalisasi untuk aplikasi Flask.
    Menambahkan fungsi get_translation sebagai global context dan filter Jinja2.
    """
    @app.before_request
    def before_request_localization():
        # Dapatkan kode bahasa yang akan digunakan untuk permintaan saat ini
        lang_code = get_locale()
        # Muat terjemahan ke objek global 'g'
        g.translations = load_translations(lang_code)
        # Simpan kode bahasa saat ini di g agar bisa diakses di template
        g.lang = lang_code

    @app.context_processor
    def inject_translations():
        """
        Membuat fungsi '_' tersedia di semua template Jinja2.
        """
        def _(key, **kwargs):
            return get_translation(key, **kwargs)
        return dict(_=_)

    # Tambahkan filter Jinja2 untuk terjemahan
    app.jinja_env.filters['_'] = get_translation

    # Tambahkan daftar bahasa yang didukung ke context processor agar bisa diakses di template
    @app.context_processor
    def inject_supported_languages():
        return dict(supported_languages=SUPPORTED_LANGS)