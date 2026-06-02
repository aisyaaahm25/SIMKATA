import streamlit as st
import json
import time
import re
from openai import OpenAI

st.set_page_config(
    page_title="SimKata — Literasi Anak Disleksia",
    page_icon="📚",
    layout="centered"
)

try:
    api_key = st.secrets["OPENAI_API_KEY"]
except Exception:
    st.error("⚠️ API key belum dikonfigurasi.")
    st.stop()

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800;900&display=swap');

html, body, [class*="css"] {
    font-family: 'Nunito', sans-serif !important;
    background-color: #FFFBF5;
}

/* Hero Section */
.hero-wrap {
    background: linear-gradient(135deg, #FFF5E6 0%, #E8F4FD 100%);
    border-radius: 24px;
    padding: 40px 36px;
    margin-bottom: 32px;
    position: relative;
    overflow: hidden;
    border: 2px dashed #FFD580;
}
.hero-tag {
    font-size: 12px;
    font-weight: 800;
    letter-spacing: 2px;
    color: #F59E0B;
    text-transform: uppercase;
    margin-bottom: 8px;
}
.hero-title {
    font-size: 36px;
    font-weight: 900;
    color: #1A1A2E;
    line-height: 1.2;
    margin-bottom: 12px;
}
.hero-title span { color: #3B82F6; }
.hero-desc {
    font-size: 15px;
    color: #6B7280;
    line-height: 1.6;
    max-width: 480px;
}
.deco { position: absolute; font-size: 48px; opacity: 0.15; }
.deco-1 { top: 10px; right: 20px; }
.deco-2 { bottom: 10px; right: 80px; font-size: 32px; }
.deco-3 { top: 50%; right: 140px; font-size: 24px; }

/* Section title */
.sec-tag {
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 2px;
    color: #F59E0B;
    text-transform: uppercase;
    text-align: center;
    margin-bottom: 4px;
}
.sec-title {
    font-size: 26px;
    font-weight: 900;
    color: #1A1A2E;
    text-align: center;
    margin-bottom: 28px;
}

/* Input area */
.input-wrap {
    background: white;
    border-radius: 20px;
    padding: 28px;
    box-shadow: 0 4px 24px rgba(0,0,0,0.06);
    border: 2px solid #E5E7EB;
    margin-bottom: 24px;
}

/* Button */
.stButton > button {
    background: linear-gradient(135deg, #3B82F6, #6366F1) !important;
    color: white !important;
    border: none !important;
    border-radius: 50px !important;
    font-weight: 800 !important;
    font-size: 16px !important;
    padding: 12px 32px !important;
    font-family: 'Nunito', sans-serif !important;
    width: 100% !important;
    box-shadow: 0 4px 15px rgba(99,102,241,0.3) !important;
    transition: all 0.2s !important;
}
.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(99,102,241,0.4) !important;
}

/* Kata sulit card */
.kata-header {
    background: linear-gradient(135deg, #FEF3C7, #FDE68A);
    border: 2px solid #F59E0B;
    border-radius: 16px;
    padding: 14px 20px;
    margin: 16px 0 8px;
    display: flex;
    align-items: center;
    gap: 10px;
}
.kata-header-text {
    font-size: 18px;
    font-weight: 900;
    color: #92400E;
}
.kata-badge {
    background: #F59E0B;
    color: white;
    font-size: 11px;
    font-weight: 800;
    padding: 3px 12px;
    border-radius: 20px;
    letter-spacing: 1px;
}

/* Rekomendasi cards */
.rek-card {
    border-radius: 14px;
    padding: 14px 18px;
    margin: 6px 0;
    display: flex;
    align-items: center;
    gap: 12px;
    font-weight: 700;
    font-size: 15px;
}
.rek-1 { background: #EFF6FF; border: 2px solid #BFDBFE; color: #1D4ED8; }
.rek-2 { background: #F0FDF4; border: 2px solid #BBF7D0; color: #15803D; }
.rek-3 { background: #FDF4FF; border: 2px solid #E9D5FF; color: #7E22CE; }
.rek-num {
    width: 28px; height: 28px;
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 13px; font-weight: 900;
    flex-shrink: 0;
}
.num-1 { background: #DBEAFE; color: #1D4ED8; }
.num-2 { background: #DCFCE7; color: #15803D; }
.num-3 { background: #F3E8FF; color: #7E22CE; }
.alasan-box {
    background: #F8FAFC;
    border-left: 3px solid #CBD5E1;
    padding: 8px 14px;
    border-radius: 0 8px 8px 0;
    font-size: 13px;
    color: #64748B;
    margin: 4px 0 16px;
    font-style: italic;
}

/* Info cards */
.info-grid { display: flex; gap: 12px; margin: 20px 0; }
.info-card {
    flex: 1;
    border-radius: 16px;
    padding: 16px;
    text-align: center;
}
.info-card-1 { background: #FEF3C7; border: 2px solid #FDE68A; }
.info-card-2 { background: #EFF6FF; border: 2px solid #BFDBFE; }
.info-card-3 { background: #F0FDF4; border: 2px solid #BBF7D0; }
.info-icon { font-size: 28px; margin-bottom: 6px; }
.info-val { font-size: 24px; font-weight: 900; color: #1A1A2E; }
.info-lbl { font-size: 11px; color: #6B7280; font-weight: 600; margin-top: 2px; }

/* Success */
.success-box {
    background: linear-gradient(135deg, #F0FDF4, #DCFCE7);
    border: 2px solid #86EFAC;
    border-radius: 16px;
    padding: 20px;
    text-align: center;
    font-size: 16px;
    font-weight: 700;
    color: #15803D;
}

/* Footer */
.footer {
    text-align: center;
    padding: 24px 0 8px;
    font-size: 12px;
    color: #9CA3AF;
    font-weight: 600;
}

/* Textarea styling */
.stTextArea textarea {
    border-radius: 12px !important;
    border: 2px solid #E5E7EB !important;
    font-family: 'Nunito', sans-serif !important;
    font-size: 15px !important;
}
.stTextArea textarea:focus {
    border-color: #3B82F6 !important;
    box-shadow: 0 0 0 3px rgba(59,130,246,0.1) !important;
}
</style>
""", unsafe_allow_html=True)

# ── Hero ─────────────────────────────────────────────────
st.markdown("""
<div class="hero-wrap">
    <div class="deco deco-1">📚</div>
    <div class="deco deco-2">✨</div>
    <div class="deco deco-3">⭐</div>
    <div class="hero-tag">✦ Sistem Rekomendasi Kata ✦</div>
    <div class="hero-title">Kata Sulit? <span>Kami Bantu</span><br>Cari yang Lebih Mudah!</div>
    <div class="hero-desc">Masukkan kata atau kalimat, SimKata akan otomatis mendeteksi kata yang sulit dan memberikan rekomendasi kata pengganti yang lebih mudah dipahami.</div>
</div>
""", unsafe_allow_html=True)

# ── Konstanta fitur ──────────────────────────────────────
HURUF_BINGUNG     = set('bdpq')
KOMBINASI_BINGUNG = ['ng', 'ny']
POLA_FONEM        = ['str','kl','pr','kr','bl','gr','tr','dr','br','fr','sy','kh','gh','ts']
HURUF_RAWAN       = set('bdpqnumw')

def prediksi_kesulitan(kata):
    kata = kata.lower()
    f2   = len(kata)
    f3   = int(any(h in HURUF_BINGUNG for h in kata) or any(k in kata for k in KOMBINASI_BINGUNG))
    f4   = sum(1 for p in POLA_FONEM if p in kata)
    f5   = round(sum(1 for h in kata if h in HURUF_RAWAN) / len(kata), 4) if kata else 0
    skor = 0
    if f2 >= 7:      skor += 2
    elif f2 >= 5:    skor += 1
    if f3 == 1:      skor += 2
    if f4 >= 1:      skor += 1
    if f5 >= 0.4:    skor += 2
    elif f5 >= 0.25: skor += 1
    return 'sulit' if skor >= 3 else 'mudah'

def rekomendasikan_kata(kata, client, max_retry=3):
    prompt = f"""Kamu adalah ahli linguistik Bahasa Indonesia yang membantu 
menyederhanakan kosakata untuk anak disleksia usia 7-12 tahun.

Berikan 3 kata pengganti yang lebih sederhana untuk kata: "{kata}"

Kriteria:
- Lebih pendek atau sama panjangnya
- Lebih familiar dalam kehidupan sehari-hari anak
- Makna sama atau sangat mirip
- Mudah diucapkan dan dieja anak usia 7-12 tahun
- Hindari huruf b/d/p/q berlebihan dan gugus konsonan kompleks

Jawab HANYA dalam format JSON:
{{"kata_asli": "{kata}", "rekomendasi": ["kata1", "kata2", "kata3"], "alasan": "alasan singkat"}}"""

    for attempt in range(max_retry):
        try:
            response = client.chat.completions.create(
                model='gpt-3.5-turbo',
                messages=[
                    {'role': 'system', 'content': 'Kamu ahli linguistik Bahasa Indonesia. Jawab hanya dalam format JSON.'},
                    {'role': 'user',   'content': prompt}
                ],
                max_tokens=200,
                temperature=0.3
            )
            hasil_text = response.choices[0].message.content.strip()
            hasil_text = hasil_text.replace('```json','').replace('```','').strip()
            return json.loads(hasil_text)
        except:
            if attempt < max_retry - 1:
                time.sleep(2)
            else:
                return {'kata_asli': kata, 'rekomendasi': [], 'alasan': ''}

# ── Input Section ────────────────────────────────────────
st.markdown('<div class="sec-title">Masukkan Kata atau Kalimat</div>', unsafe_allow_html=True)

user_input = st.text_area(
    label="input",
    height=130,
    placeholder="Contoh: Budi berlari dengan tergesa-gesa menuju sekolah karena tidak ingin terlambat mengikuti pelajaran...",
    label_visibility="collapsed"
)

proses = st.button("🔍  Temukan Rekomendasi Kata")

# ── Proses ───────────────────────────────────────────────
if proses:
    if not user_input.strip():
        st.warning("⚠️ Masukkan kata atau kalimat terlebih dahulu ya!")
    else:
        semua_kata = re.findall(r'\b[a-zA-Z]+\b', user_input)
        kata_unik  = list(dict.fromkeys([k.lower() for k in semua_kata]))
        kata_sulit = [k for k in kata_unik if prediksi_kesulitan(k) == 'sulit']

        if not kata_sulit:
            st.markdown('<div class="success-box">Tidak ada kata sulit yang ditemukan, teks ini sudah ramah untuk anak disleksia!</div>', unsafe_allow_html=True)
        else:
            # Info cards
            st.markdown(f"""
            <div class="info-grid">
                <div class="info-card info-card-1">
                    <div class="info-icon">📝</div>
                    <div class="info-val">{len(kata_unik)}</div>
                    <div class="info-lbl">Total Kata</div>
                </div>
                <div class="info-card info-card-2">
                    <div class="info-icon">🔴</div>
                    <div class="info-val">{len(kata_sulit)}</div>
                    <div class="info-lbl">Kata Sulit</div>
                </div>
                <div class="info-card info-card-3">
                    <div class="info-icon">✅</div>
                    <div class="info-val">{len(kata_unik)-len(kata_sulit)}</div>
                    <div class="info-lbl">Kata Mudah</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown('<div class="sec-tag">✦ Hasil Rekomendasi</div>', unsafe_allow_html=True)
            st.markdown('<div class="sec-title">Kata Pengganti yang Lebih Mudah</div>', unsafe_allow_html=True)

            client_ai = OpenAI(api_key=api_key)
            progress  = st.progress(0, text='Sedang mencari rekomendasi...')

            for i, kata in enumerate(kata_sulit):
                hasil  = rekomendasikan_kata(kata, client_ai)
                rek    = hasil.get('rekomendasi', [])
                alasan = hasil.get('alasan', '')

                st.markdown(f"""
                <div class="kata-header">
                    <span style="font-size:20px">🔴</span>
                    <span class="kata-header-text">{kata}</span>
                    <span class="kata-badge">SULIT</span>
                </div>
                """, unsafe_allow_html=True)

                warna = [('rek-1','num-1','1️⃣'), ('rek-2','num-2','2️⃣'), ('rek-3','num-3','3️⃣')]
                if rek:
                    for j, k in enumerate(rek[:3]):
                        if k:
                            cls, num_cls, em = warna[j]
                            st.markdown(f"""
                            <div class="rek-card {cls}">
                                <div class="rek-num {num_cls}">{j+1}</div>
                                <span>{k}</span>
                            </div>
                            """, unsafe_allow_html=True)
                    if alasan:
                        st.markdown(f'<div class="alasan-box">💡 {alasan}</div>', unsafe_allow_html=True)

                progress.progress((i+1)/len(kata_sulit),
                                  text=f'Memproses {i+1}/{len(kata_sulit)} kata...')
                time.sleep(0.3)

            progress.empty()
            st.markdown('<div class="success-box">Selesai! Semua kata sulit sudah direkomendasikan.</div>', unsafe_allow_html=True)

# ── Footer ───────────────────────────────────────────────
st.markdown("""
<div class="footer">
    SimKata · UIN Sunan Gunung Djati Bandung · 2026
</div>
""", unsafe_allow_html=True)
