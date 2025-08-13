# app.py (Hata Düzeltilmiş Son Versiyon)

import os
import sqlite3
import json
import sys
import traceback
from flask import Flask, render_template_string, request, jsonify, Response
from gold_club_bot import GoldClubBot

# --- Ayarlar ve Konfigürasyon ---
project_path = os.getcwd() 
DATA_DIR = os.path.join(project_path, 'data')
DATABASE = os.path.join(DATA_DIR, 'goldclub_data.db')
PLAYLISTS_DIR = os.path.join(DATA_DIR, 'playlists')
CONFIG_FILE = os.path.join(project_path, 'config.json') 
config = {}

if 'GOLD_CLUB_EMAIL' in os.environ and 'GOLD_CLUB_PASSWORD' in os.environ:
    print("Ortam değişkenleri (Render) kullanılıyor.")
    config['email'] = os.environ.get('GOLD_CLUB_EMAIL')
    config['password'] = os.environ.get('GOLD_CLUB_PASSWORD')
else:
    print("Yerel config.json dosyası kullanılıyor.")
    try:
        with open(CONFIG_FILE, 'r') as f: config = json.load(f)
    except FileNotFoundError:
        sys.exit(f"HATA: Ne ortam değişkenleri ne de {CONFIG_FILE} dosyası bulundu.")

def get_db_connection():
    conn = sqlite3.connect(DATABASE); conn.row_factory = sqlite3.Row; return conn

def init_app():
    if not os.path.exists(DATA_DIR): os.makedirs(DATA_DIR)
    if not os.path.exists(PLAYLISTS_DIR): os.makedirs(PLAYLISTS_DIR)
    if not os.path.exists(DATABASE):
        conn = get_db_connection()
        conn.execute("CREATE TABLE generated_links (id INTEGER PRIMARY KEY, m3u_url TEXT NOT NULL, expiry_date TEXT NOT NULL, channel_count INTEGER, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);")
        conn.commit(); conn.close()
        print("Veritabanı oluşturuldu.")

# --- Flask Uygulaması ---
app = Flask(__name__)
app.config['SECRET_KEY'] = 'render-icin-super-gizli-anahtar!'

# --- HTML TEMPLATE'LER ---
HOME_TEMPLATE = """
<!DOCTYPE html><html lang="tr"><head><meta charset="UTF-8"><title>Playlist Yönetim Paneli</title><meta name="viewport" content="width=device-width, initial-scale=1.0"><script src="https://cdn.jsdelivr.net/npm/feather-icons/dist/feather.min.js"></script><link href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&display=swap" rel="stylesheet"><style>:root { --bg-dark: #101014; --bg-card: rgba(30, 30, 35, 0.5); --border-color: rgba(255, 255, 255, 0.1); --text-primary: #f0f0f0; --text-secondary: #a0a0a0; --accent-grad: linear-gradient(90deg, #8A2387, #E94057, #F27121); --success-color: #1ed760; --error-color: #f44336; }@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }* { box-sizing: border-box; margin: 0; padding: 0; }body { font-family: 'Manrope', sans-serif; background: var(--bg-dark); color: var(--text-primary); }body::before { content: ''; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: radial-gradient(circle at 15% 25%, #8a238744, transparent 30%), radial-gradient(circle at 85% 75%, #f2712133, transparent 40%); z-index: -1; } .container { max-width: 900px; margin: 3rem auto; padding: 0 2rem; }.shell { background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 16px; padding: 2rem; backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px); box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2); }h1, h2 { font-weight: 800; }.btn { display: flex; align-items: center; justify-content: center; gap: 0.75rem; width: 100%; padding: 0.9rem; background: var(--accent-grad); color: white; border: none; border-radius: 8px; font-size: 1.1rem; cursor: pointer; transition: all 0.2s; font-weight: 700; margin-top: 1.5rem; }.btn:hover:not(:disabled) { transform: translateY(-3px); box-shadow: 0 4px 20px rgba(233, 64, 87, 0.3); }.btn:disabled { background: #333; cursor: not-allowed; opacity: 0.6; }.history-table { width: 100%; border-collapse: collapse; margin-top: 1rem; }.history-table th, .history-table td { padding: 1rem; border-bottom: 1px solid var(--border-color); text-align: left; vertical-align: middle; }.btn-details { background: var(--success-color); color: white; padding: 0.4rem 1rem; border-radius: 20px; text-decoration: none; font-size: 0.9rem; font-weight: 500; }.notification { padding: 1rem; border-radius: 8px; margin-top: 1.5rem; display: none; text-align: center; font-weight: 500; }.notification.success { background: var(--success-color); color: white; }.notification.error { background: var(--error-color); color: white; }</style></head>
<body><div class="container"><div class="shell"><h1 style="text-align: center;">Playlist Yönetim Paneli</h1><form id="control-form" method="POST" action="{{ url_for('handle_start_process') }}"><label for="target_group" style="color:var(--text-secondary); margin-top:1.5rem;">Filtrelenecek Kanal Grubu</label><input type="text" id="target_group" name="target_group" value="TURKISH" style="background-color: rgba(0,0,0,0.2);"><button type="submit" id="start-btn" class="btn"><i data-feather="play-circle"></i><span>Link Üret ve Analiz Et</span></button></form><div id="notification-area">{% if message %}<div class="notification {{ 'success' if success else 'error' }}" style="display:flex; align-items:center; justify-content:center; gap: 0.5rem;"><i data-feather="{{ 'check-circle' if success else 'alert-triangle' }}"></i> <span>{{ message }}</span></div>{% endif %}</div><h2 style="margin-top:2.5rem; border-top: 1px solid var(--border-color); padding-top: 2rem;">Geçmiş İşlemler</h2><div style="max-height: 550px; overflow-y: auto;"><table class="history-table"><thead><tr><th>Üretim Zamanı</th><th>Son Kullanma</th><th>Kanal Sayısı</th><th>İşlem</th></tr></thead><tbody>{% for item in history %}<tr><td>{{ item.created_at.split('.')[0] }}</td><td>{{ item.expiry_date }}</td><td>{{ item.channel_count }}</td><td><a href="{{ url_for('playlist_details', link_id=item.id) }}" class="btn-details">Detaylar</a></td></tr>{% endfor %}</tbody></table></div></div></div>
<script>feather.replace();document.getElementById('control-form').addEventListener('submit', () => { const btn = document.getElementById('start-btn'); btn.disabled = true; btn.innerHTML = '<i data-feather="loader" class="spinner"></i><span>İşlem Yürütülüyor... Bu işlem 1-2 dakika sürebilir.</span>'; feather.replace(); });</script></body></html>"""
PLAYLIST_DETAILS_HTML = """
<!DOCTYPE html><html lang="tr"><head><meta charset="UTF-8"><title>Playlist Detayları</title><meta name="viewport" content="width=device-width, initial-scale=1.0"><script src="https://cdn.jsdelivr.net/npm/feather-icons/dist/feather.min.js"></script><link href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&display=swap" rel="stylesheet"><style>:root { --bg-dark: #101014; --bg-card: rgba(30, 30, 35, 0.5); --border-color: rgba(255, 255, 255, 0.1); --text-primary: #f0f0f0; --text-secondary: #a0a0a0; --accent-grad: linear-gradient(90deg, #8A2387, #E94057, #F27121); }body { font-family: 'Manrope', sans-serif; background: var(--bg-dark); color: var(--text-primary); }body::before { content: ''; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: radial-gradient(circle at 15% 85%, #8a238722, transparent 30%), radial-gradient(circle at 85% 25%, #f2712122, transparent 40%); z-index: -1; }.container { max-width: 1400px; margin: 3rem auto; padding: 2rem; background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 16px; backdrop-filter: blur(20px); }h1 { display: flex; align-items: center; gap: 1rem; font-weight: 800; }.controls { display: flex; flex-wrap: wrap; gap: 1rem; margin: 2rem 0; }.search-wrapper { flex-grow: 1; position: relative; }#search-box { width: 100%; padding: 0.8rem 1rem; padding-left: 3rem; background-color: rgba(0,0,0,0.2); border: 1px solid var(--border-color); border-radius: 8px; color: var(--text-primary); font-size: 1rem; }.search-wrapper i { position: absolute; left: 1rem; top: 50%; transform: translateY(-50%); color: var(--text-secondary); }.btn { display: flex; align-items: center; justify-content: center; gap: 0.5rem; padding: 0.8rem 1.5rem; color: white; border: none; border-radius: 8px; cursor: pointer; text-decoration: none; font-weight: 600;}.btn-download { background-image: var(--accent-grad); } .btn-back { background-color: #444; }.table-container { max-height: 70vh; overflow-y: auto; border: 1px solid var(--border-color); border-radius: 8px; }table { width: 100%; border-collapse: collapse; }th, td { padding: 0.8rem 1rem; text-align: left; border-bottom: 1px solid var(--border-color); }thead th { background-color: rgba(0,0,0,0.3); position: sticky; top: 0; z-index: 10; }.actions-cell { position: relative; text-align: right !important; }.btn-actions { background: none; border: 1px solid var(--border-color); color: var(--text-secondary); padding: 0.3rem; border-radius: 5px; cursor: pointer; }.copy-menu { display: none; position: absolute; background-color: #2a2a2a; border: 1px solid var(--border-color); border-radius: 6px; z-index: 100; padding: 0.5rem; right: 1rem; top: 100%; min-width: 180px; box-shadow: 0 8px 24px rgba(0,0,0,0.4);}.copy-option { display: flex; align-items: center; gap: 0.5rem; width: 100%; background: none; border: none; color: var(--text-primary); padding: 0.5rem; text-align: left; border-radius: 4px; cursor: pointer;}.copy-option:hover { background-image: var(--accent-grad); color: white;}</style></head>
<body><div class="container"><h1><i data-feather="list"></i><span>Playlist Detayları (<span id="channel-count">0</span> Kanal)</span><a href="/" class="btn btn-back" style="margin-left: auto;"><i data-feather="arrow-left"></i><span>Ana Sayfa</span></a></h1><div class="controls"><div class="search-wrapper"><i data-feather="search"></i><input type="text" id="search-box" placeholder="Kanal adında veya grupta ara..."></div><button id="download-selected-btn" class="btn btn-download"><i data-feather="download"></i><span>Seçilenleri İndir</span></button></div><div class="table-container"><table id="channels-table"><thead><tr><th><input type="checkbox" id="select-all"></th><th>Grup</th><th>Kanal Adı</th><th style="text-align: right;">Aksiyonlar</th></tr></thead><tbody>{% for channel in channels %}<tr data-url="{{ channel.url }}"><td><input type="checkbox" class="channel-checkbox"></td><td>{{ channel.group }}</td><td>{{ channel.name }}</td><td class="actions-cell"><button class="btn-actions" title="Aksiyonlar"><i data-feather="more-vertical"></i></button><div class="copy-menu"><button class="copy-option" data-format="ts"><i data-feather="film"></i><span>TS Olarak Kopyala</span></button><button class="copy-option" data-format="m3u8"><i data-feather="list"></i><span>M3U8 Kopyala</span></button><button class="copy-option" data-format="original"><i data-feather="link"></i><span>Orijinal Kopyala</span></button></div></td></tr>{% endfor %}</tbody></table></div></div>
<script>feather.replace(); const linkId = {{ link_id }}; const tableBody = document.querySelector("#channels-table tbody"); document.getElementById("channel-count").textContent = tableBody.rows.length;document.getElementById("search-box").addEventListener("keyup", e => { const q = e.target.value.toLowerCase(); tableBody.querySelectorAll("tr").forEach(r => r.style.display = r.textContent.toLowerCase().includes(q) ? "" : "none"); });document.getElementById("select-all").addEventListener("change", e => { document.querySelectorAll(".channel-checkbox").forEach(cb => { if(cb.closest('tr').style.display !== 'none') cb.checked = e.target.checked; }); });tableBody.addEventListener('click', e => { const actionButton = e.target.closest('.btn-actions'); if (actionButton) { const currentMenu = actionButton.nextElementSibling; document.querySelectorAll('.copy-menu').forEach(m => { if (m !== currentMenu) m.style.display = 'none'; }); currentMenu.style.display = currentMenu.style.display === 'block' ? 'none' : 'block'; return; } if (e.target.closest('.copy-option')) { const button = e.target.closest('.copy-option'); const format = button.dataset.format; const baseUrl = button.closest('tr').dataset.url; let finalUrl = baseUrl; if (format !== 'original') { const urlParts = baseUrl.split('/'); const streamId = urlParts.pop(); const userInfo = urlParts.slice(3).join('/'); finalUrl = `http://${urlParts[2]}/live/${userInfo}/${streamId}.${format}`; } navigator.clipboard.writeText(finalUrl).then(() => { const originalHtml = button.innerHTML; button.innerHTML = '<i data-feather="check"></i><span>Kopyalandı!</span>'; feather.replace(); setTimeout(() => { button.innerHTML = originalHtml; feather.replace(); }, 1500); }); document.querySelectorAll('.copy-menu').forEach(m => m.style.display = 'none'); }});document.addEventListener('click', e => { if (!e.target.closest('.actions-cell')) document.querySelectorAll('.copy-menu').forEach(m => m.style.display = 'none'); });document.getElementById("download-selected-btn").addEventListener("click", () => { const selected = Array.from(document.querySelectorAll(".channel-checkbox:checked")).map(cb => { const r = cb.closest("tr"); return { group: r.cells[1].textContent, name: r.cells[2].textContent, url: r.dataset.url }; }); if (selected.length === 0) return alert("Lütfen en az bir kanal seçin."); fetch('/generate_custom_playlist', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ channels: selected }) }).then(res => res.blob()).then(blob => { const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = `playlist_${linkId}.m3u`; document.body.appendChild(a); a.click(); a.remove(); }); });</script></body></html>"""

# --- Flask Yolları (Routes) ---
@app.route('/', methods=['GET'])
def index():
    conn = get_db_connection(); history_data = conn.execute('SELECT * FROM generated_links ORDER BY id DESC LIMIT 20').fetchall(); conn.close()
    return render_template_string(HOME_TEMPLATE, history=[dict(row) for row in history_data])

@app.route('/start_process', methods=['POST'])
def handle_start_process():
    target_group = request.form.get('target_group')
    message, success = "", False
    try:
        # project_path'i bot'a iletiyoruz, böylece ekran görüntüsünü doğru yere kaydedebilir
        bot = GoldClubBot(email=config['email'], password=config['password'], target_group=target_group, project_path=project_path)
        result_data = bot.run_full_process()
        if result_data and "url" in result_data:
            conn = get_db_connection(); cursor = conn.cursor()
            cursor.execute('INSERT INTO generated_links (m3u_url, expiry_date, channel_count) VALUES (?, ?, ?)', (result_data['url'], result_data['expiry'], len(result_data.get('channels', []))))
            new_id = cursor.lastrowid; conn.commit(); conn.close()
            with open(os.path.join(PLAYLISTS_DIR, f"{new_id}.json"), 'w', encoding='utf-8') as f: json.dump(result_data['channels'], f, ensure_ascii=False, indent=4)
            message = f"İşlem başarılı! {len(result_data['channels'])} kanal bulundu ve kaydedildi."
            success = True
        else:
            message = "Bot çalıştı ancak geçerli bir sonuç döndürmedi. Sunucu loglarını ve 'error_screenshot.png' dosyasını kontrol edin."
    except Exception as e:
        traceback.print_exc()
        message = f"Kritik bir hata oluştu. Sunucu loglarını ve 'error_screenshot.png' dosyasını kontrol edin. Hata: {e}"
        success = False

    conn = get_db_connection(); history_data = conn.execute('SELECT * FROM generated_links ORDER BY id DESC LIMIT 20').fetchall(); conn.close()
    return render_template_string(HOME_TEMPLATE, history=[dict(row) for row in history_data], message=message, success=success)

@app.route('/playlist/<int:link_id>')
def playlist_details(link_id):
    playlist_path = os.path.join(PLAYLISTS_DIR, f"{link_id}.json");
    if not os.path.exists(playlist_path): return "Playlist bulunamadı.", 404
    with open(playlist_path, 'r', encoding='utf-8') as f: channels = json.load(f)
    return render_template_string(PLAYLIST_DETAILS_HTML, channels=channels, link_id=link_id)

@app.route('/generate_custom_playlist', methods=['POST'])
def generate_custom_playlist():
    data = request.json; channels = data.get('channels', []);
    if not channels: return "Kanal seçilmedi.", 400
    content = "#EXTM3U\n"
    for ch in channels: content += f'#EXTINF:-1 group-title="{ch["group"]}",{ch["name"]}\n{ch["url"]}\n'
    return Response(content, mimetype="audio/x-mpegurl", headers={"Content-disposition": "attachment; filename=custom_playlist.m3u"})

# Uygulama başlangıcında veritabanını ve klasörleri kontrol et
init_app()

if __name__ == "__main__":
    # Bu blok sadece yerel makinede çalıştırıldığında kullanılır.
    # Render, gunicorn komutunu kullanacağı için bu bloğu çalıştırmaz.
    app.run(host='0.0.0.0', port=9999)
