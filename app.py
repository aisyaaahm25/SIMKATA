import streamlit as st
import json
import time
import re
from openai import OpenAI

# ── Konfigurasi halaman ──────────────────────────────────
st.set_page_config(
    page_title="SimKata — Simplifikasi Kosakata Disleksia",
    page_icon="📚",
    layout="centered"
)

# ── CSS ──────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    .judul {
        font-size: 32px;
        font-weight: 700;
        color: #1A1A2E;
        margin-bottom: 4px;
    }
    .subjudul {
        font-size: 14px;
        color: #6B7280;
        margin-bottom: 24px;
    }
    .kartu-mudah {
        background: #F0FDF4;
        border: 1px solid #86EFAC;
        border-left: 4px solid #22C55E;
        padding: 12px 16px;
        border-radius: 10px;
        margin: 6px 0;
    }
    .kartu-sulit {
        background: #FFF1F2;
        border: 1px solid #FECDD3;
        border-left: 4px solid #F43F5E;
        padding: 12px 16px;
        border-radius: 10px;
        margin: 6px 0;
    }
    .kartu-rek {
        background: #EFF6FF;
        border: 1px solid #BFDBFE;
        border-left: 4px solid #3B82F6;
        padding: 10px 16px;
        border-radius: 10px;
        margin: 4px 0;
        font-size: 15px;
    }
    .badge {
        display: inline-block;
        padding: 2px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
    }
    .badge-mudah { background: #DCFCE7; color: #15803D; }
    .badge-sulit { background: #FFE4E6; color: #BE123C; }
    .fitur-box {
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 10px 14px;
        text-align: center;
    }
    .fitur-val { font-size: 20px; font-weight: 700; color: #1A1A2E; }
    .fitur-lbl { font-size: 11px; color: #94A3B8; margin-top: 2px; }
    .teks-box {
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 14px;
        font-size: 14px;
        line-height: 1.7;
        min-height: 80px;
    }
    .teks-hasil {
        background: #F0FDF4;
        border: 1px solid #86EFAC;
        border-radius: 10px;
        padding: 14px;
        font-size: 14px;
        line-height: 1.7;
        min-height: 80px;
    }
    .stButton > button {
        background: #3B82F6;
        color: white;
        border: none;
        border-radius: 10px;
        padding: 10px 20px;
        font-weight: 600;
        font-family: 'Plus Jakarta Sans', sans-serif;
        width: 100%;
        transition: background 0.2s;
    }
    .stButton > button:hover { background: #2563EB; }
    .divider { border-top: 1px solid #E2E8F0; margin: 20px 0; }
</style>
""", unsafe_allow_html=True)

# ── Header ───────────────────────────────────────────────
st.markdown('<div class="judul">📚 SimKata</div>', unsafe_allow_html=True)
st.markdown('<div class="subjudul">Sistem Rekomendasi Kata Pengganti untuk Mendukung Literasi Baca Anak Disleksia · UIN Sunan Gunung Djati Bandung</div>', unsafe_allow_html=True)

# ── Sidebar ──────────────────────────────────────────────
with st.sidebar:
    st.divider()
    st.markdown("### 📖 Tentang SimKata")
    st.markdown("""
    SimKata adalah sistem rekomendasi kata pengganti berbasis:
    - **K-Means Clustering** untuk identifikasi kosakata sulit
    - **GPT-3.5-turbo** untuk menghasilkan rekomendasi kata yang lebih sederhana
    
    Dikembangkan untuk mendukung literasi baca anak disleksia usia 7–12 tahun.
    """)
    st.divider()
    st.caption("Aisyah Muthmainnah · 1227050012 · Teknik Informatika · 2026")

# ── Ambil API key dari Streamlit Secrets ─────────────────
try:
    api_key = st.secrets["OPENAI_API_KEY"]
except Exception:
    st.error("⚠️ API key belum dikonfigurasi. Hubungi administrator.")
    st.stop()

# ── Konstanta fitur ──────────────────────────────────────
HURUF_BINGUNG     = set('bdpq')
KOMBINASI_BINGUNG = ['ng', 'ny']
POLA_FONEM        = ['str','kl','pr','kr','bl','gr','tr','dr','br','fr','sy','kh','gh','ts']
HURUF_RAWAN       = set('bdpqnumw')

# ── Fungsi fitur ─────────────────────────────────────────
def ekstrak_fitur(kata):
    kata = kata.lower()
    f2 = len(kata)
    f3 = int(any(h in HURUF_BINGUNG for h in kata) or
             any(k in kata for k in KOMBINASI_BINGUNG))
    f4 = sum(1 for p in POLA_FONEM if p in kata)
    f5 = round(sum(1 for h in kata if h in HURUF_RAWAN) / len(kata), 4) if kata else 0
    return f2, f3, f4, f5

def prediksi_kesulitan(kata):
    f2, f3, f4, f5 = ekstrak_fitur(kata)
    skor = 0
    if f2 >= 7:      skor += 2
    elif f2 >= 5:    skor += 1
    if f3 == 1:      skor += 2
    if f4 >= 1:      skor += 1
    if f5 >= 0.4:    skor += 2
    elif f5 >= 0.25: skor += 1
    return ('sulit' if skor >= 3 else 'mudah'), skor

def rekomendasikan_kata(kata, client, max_retry=3):
    prompt = f"""Kamu adalah ahli linguistik Bahasa Indonesia yang membantu 
menyederhanakan kosakata untuk anak disleksia usia 7-12 tahun.

Tugasmu: berikan 3 kata pengganti yang lebih sederhana untuk kata berikut.

Kriteria kata pengganti:
- Lebih pendek atau sama panjangnya
- Lebih sering digunakan dalam kehidupan sehari-hari anak
- Makna sama atau sangat mirip
- Mudah diucapkan dan dieja anak usia 7-12 tahun
- Hindari huruf b/d/p/q yang terlalu banyak
- Hindari gugus konsonan kompleks (str, kl, pr, kr, dll)

Kata: "{kata}"

Jawab HANYA dalam format JSON berikut, tanpa penjelasan tambahan:
{{"kata_asli": "{kata}", "rekomendasi": ["kata1", "kata2", "kata3"], "alasan": "alasan singkat 1 kalimat"}}"""

    for attempt in range(max_retry):
        try:
            response = client.chat.completions.create(
                model='gpt-3.5-turbo',
                messages=[
                    {
                        'role': 'system',
                        'content': 'Kamu adalah ahli linguistik Bahasa Indonesia. Selalu jawab dalam format JSON yang diminta, tanpa tambahan apapun.'
                    },
                    {'role': 'user', 'content': prompt}
                ],
                max_tokens=200,
                temperature=0.3
            )
            hasil_text = response.choices[0].message.content.strip()
            hasil_text = hasil_text.replace('```json','').replace('```','').strip()
            return json.loads(hasil_text)

        except json.JSONDecodeError:
            return {'kata_asli': kata, 'rekomendasi': ['[error]','',''], 'alasan': ''}
        except Exception as e:
            if attempt < max_retry - 1:
                time.sleep(2)
            else:
                return {'kata_asli': kata, 'rekomendasi': ['[error]','',''], 'alasan': str(e)}

def proses_teks(teks, client):
    kata_list = re.findall(r'\b[a-zA-Z]+\b', teks)
    kata_unik  = list(dict.fromkeys(kata_list))
    hasil_map  = {}
    teks_baru  = teks

    progress = st.progress(0, text='Menganalisis teks...')
    for i, kata in enumerate(kata_unik):
        label, _ = prediksi_kesulitan(kata.lower())
        if label == 'sulit':
            hasil = rekomendasikan_kata(kata.lower(), client)
            rek   = hasil.get('rekomendasi', [])
            if rek and rek[0] not in ['[error]', '']:
                hasil_map[kata] = rek[0]
                teks_baru = re.sub(
                    r'\b' + re.escape(kata) + r'\b',
                    f'**{rek[0]}**',
                    teks_baru
                )
        progress.progress(
            (i + 1) / len(kata_unik),
            text=f'Memproses kata {i+1}/{len(kata_unik)}...'
        )
        time.sleep(0.3)

    progress.empty()
    return teks_baru, hasil_map

# ── Tab UI ───────────────────────────────────────────────
tab1, tab2 = st.tabs(["🔤  Cek Kata", "📄  Sederhanakan Teks"])

# ════════════════════════════════════
# TAB 1 — Cek Kata
# ════════════════════════════════════
with tab1:
    st.markdown("#### Cek & Rekomendasikan Kata Pengganti")
    st.caption("Masukkan satu kata untuk dicek tingkat kesulitannya dan mendapatkan rekomendasi kata yang lebih sederhana.")

    kata_input = st.text_input(
        "Kata yang ingin dicek:",
        placeholder="contoh: tersenyum, memberikan, menyelesaikan...",
        label_visibility="collapsed"
    )

    cari = st.button("🔍  Cari Rekomendasi", key="btn_cari")

    if cari:
        if not kata_input.strip():
            st.warning("Masukkan kata terlebih dahulu.")
        else:
            kata_bersih = kata_input.strip().lower()
            label, skor = prediksi_kesulitan(kata_bersih)
            f2, f3, f4, f5 = ekstrak_fitur(kata_bersih)

            # Tampilkan fitur
            st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.markdown(f'<div class="fitur-box"><div class="fitur-val">{f2}</div><div class="fitur-lbl">Panjang Kata</div></div>', unsafe_allow_html=True)
            with col2:
                st.markdown(f'<div class="fitur-box"><div class="fitur-val">{"Ada" if f3 else "Tidak"}</div><div class="fitur-lbl">Huruf Bingung</div></div>', unsafe_allow_html=True)
            with col3:
                st.markdown(f'<div class="fitur-box"><div class="fitur-val">{f4}</div><div class="fitur-lbl">Fonem Kompleks</div></div>', unsafe_allow_html=True)
            with col4:
                st.markdown(f'<div class="fitur-box"><div class="fitur-val">{f5:.2f}</div><div class="fitur-lbl">Rasio Visual</div></div>', unsafe_allow_html=True)

            st.markdown("")

            if label == 'mudah':
                st.markdown(f'<div class="kartu-mudah">✅ Kata <b>"{kata_bersih}"</b> termasuk <span class="badge badge-mudah">MUDAH</span> — tidak perlu diganti.</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="kartu-sulit">⚠️ Kata <b>"{kata_bersih}"</b> termasuk <span class="badge badge-sulit">SULIT</span> — mencari rekomendasi...</div>', unsafe_allow_html=True)
                st.markdown("")

                with st.spinner('Menghubungi OpenAI...'):
                    client_ai = OpenAI(api_key=api_key)
                    hasil     = rekomendasikan_kata(kata_bersih, client_ai)

                rek    = hasil.get('rekomendasi', [])
                alasan = hasil.get('alasan', '')

                st.markdown("**✨ Rekomendasi kata pengganti:**")
                emoji = ['🥇', '🥈', '🥉']
                for i, k in enumerate(rek):
                    if k and k not in ['[error]', '']:
                        st.markdown(f'<div class="kartu-rek">{emoji[i]} <b>{k}</b></div>', unsafe_allow_html=True)

                if alasan:
                    st.markdown("")
                    st.caption(f"💡 {alasan}")

# ════════════════════════════════════
# TAB 2 — Sederhanakan Teks
# ════════════════════════════════════
with tab2:
    st.markdown("#### Sederhanakan Paragraf Teks")
    st.caption("Masukkan paragraf teks cerita anak. Sistem akan otomatis mendeteksi kata sulit dan menggantinya dengan kata yang lebih sederhana.")

    teks_input = st.text_area(
        "Teks cerita:",
        height=140,
        placeholder="Contoh: Budi berlari menuju sekolah dengan tergesa-gesa karena tidak ingin terlambat mengikuti pelajaran yang menyenangkan hari ini...",
        label_visibility="collapsed"
    )

    sederhanakan = st.button("✨  Sederhanakan Teks", key="btn_teks")

    if sederhanakan:
        if not teks_input.strip():
            st.warning("Masukkan teks terlebih dahulu.")
        else:
            client_ai          = OpenAI(api_key=api_key)
            teks_baru, hasil_map = proses_teks(teks_input, client_ai)

            st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**📄 Teks Asli**")
                st.markdown(f'<div class="teks-box">{teks_input}</div>', unsafe_allow_html=True)
            with col2:
                st.markdown("**✅ Teks Disederhanakan**")
                st.markdown(f'<div class="teks-hasil">{teks_baru}</div>', unsafe_allow_html=True)

            st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

            if hasil_map:
                st.markdown("**📋 Daftar kata yang diganti:**")
                cols = st.columns(3)
                for idx, (asli, ganti) in enumerate(hasil_map.items()):
                    with cols[idx % 3]:
                        st.markdown(f'<div class="kartu-rek">~~{asli}~~ → <b>{ganti}</b></div>', unsafe_allow_html=True)
                st.markdown("")
                st.success(f"✅ {len(hasil_map)} kata berhasil disederhanakan!")
            else:
                st.info("ℹ️ Tidak ada kata sulit yang ditemukan dalam teks ini.")
