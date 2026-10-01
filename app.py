import os
import time
import html
import re
import uuid
import requests
from functools import wraps
from flask import Flask, request, render_template_string, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET", "change-this-secret")
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
DEFAULT_CHAT_ID = os.getenv("TARGET_CHAT_ID", "").strip()
PANEL_USER = os.getenv("PANEL_USER", "admin")
PANEL_PASSWORD = os.getenv("PANEL_PASSWORD", "admin123")

history = []

HTML = r"""
<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Disparador Telegram</title>
<style>
:root{--bg:#080b12;--panel:#101521;--panel2:#151b29;--text:#f5f7fb;--muted:#8e98aa;--line:#232b3b;--accent:#5b8cff;--accent2:#7c5cff;--ok:#25d366;--danger:#ff5f6d}
*{box-sizing:border-box}body{margin:0;background:radial-gradient(circle at top,#17213a 0,#080b12 45%);color:var(--text);font-family:Inter,system-ui,-apple-system,Segoe UI,Roboto,Arial,sans-serif}
.wrap{max-width:1080px;margin:0 auto;padding:28px 16px 48px}.top{display:flex;align-items:center;justify-content:space-between;gap:16px;margin-bottom:24px}
.brand{display:flex;align-items:center;gap:12px}.logo{width:44px;height:44px;border-radius:14px;background:linear-gradient(135deg,var(--accent),var(--accent2));display:grid;place-items:center;font-size:22px;font-weight:800;box-shadow:0 10px 30px #0005}.brand h1{font-size:21px;margin:0}.brand p{margin:3px 0 0;color:var(--muted);font-size:13px}
.status{padding:9px 12px;border:1px solid #254b37;background:#102318;border-radius:999px;color:#8df0ae;font-size:12px}
.grid{display:grid;grid-template-columns:1.1fr .9fr;gap:18px}.card{background:rgba(16,21,33,.92);border:1px solid var(--line);border-radius:20px;padding:20px;box-shadow:0 20px 50px #0003}.card h2{font-size:16px;margin:0 0 16px}.sub{color:var(--muted);font-size:12px;margin:-8px 0 16px}
label{display:block;font-size:12px;color:#b9c1cf;margin:0 0 7px}.field{margin-bottom:15px}input,textarea{width:100%;border:1px solid var(--line);background:#0b0f18;color:var(--text);border-radius:12px;padding:12px 13px;font:inherit;outline:none}input:focus,textarea:focus{border-color:#4f76d8;box-shadow:0 0 0 3px #5b8cff18}textarea{min-height:190px;resize:vertical;line-height:1.5}
.row{display:grid;grid-template-columns:1fr 1fr;gap:12px}.drop{border:1px dashed #364158;background:#0b0f18;border-radius:14px;padding:16px;text-align:center}.drop input{border:0;padding:0;background:transparent}.hint{color:var(--muted);font-size:11px;margin-top:7px}
.preview{background:#0b0f18;border:1px solid var(--line);border-radius:16px;overflow:hidden}.preview-head{padding:11px 13px;border-bottom:1px solid var(--line);font-size:12px;color:var(--muted)}.preview-media{display:grid;grid-template-columns:repeat(2,1fr);gap:2px;background:#000}.preview-media img{width:100%;aspect-ratio:1/1;object-fit:cover;display:block}.preview-body{padding:14px;white-space:pre-wrap;font-size:13px;line-height:1.5}.button-preview{display:inline-block;margin-top:10px;background:#2f7df6;color:white;padding:9px 13px;border-radius:9px;text-decoration:none;font-size:12px}
.actions{display:flex;gap:10px;margin-top:15px}.btn{border:0;border-radius:12px;padding:13px 18px;font-weight:700;cursor:pointer;font-size:14px}.primary{background:linear-gradient(135deg,var(--accent),var(--accent2));color:#fff;flex:1}.secondary{background:#1b2231;color:#dbe1ec}.btn:disabled{opacity:.55;cursor:not-allowed}
.flash{padding:11px 13px;border-radius:12px;margin-bottom:12px;font-size:13px;background:#172238;border:1px solid #2c3b58}.flash.ok{background:#10261a;border-color:#245337;color:#9cf3b4}.flash.err{background:#2a1519;border-color:#5b292f;color:#ffb0b7}
.hist{display:flex;flex-direction:column;gap:10px}.item{border:1px solid var(--line);background:#0b0f18;border-radius:13px;padding:12px}.item-top{display:flex;justify-content:space-between;gap:10px}.pill{font-size:10px;padding:4px 7px;border-radius:999px;background:#13241a;color:#8ee9a7}.time{font-size:10px;color:var(--muted)}.item-text{font-size:12px;color:#cfd5df;margin-top:7px;white-space:pre-wrap;max-height:70px;overflow:hidden}
@media(max-width:820px){.grid{grid-template-columns:1fr}.wrap{padding-top:18px}.row{grid-template-columns:1fr}.top{align-items:flex-start}.status{display:none}}
</style>
</head>
<body>
<div class="wrap">
  <div class="top">
    <div class="brand"><div class="logo">➤</div><div><h1>Disparador Telegram</h1><p>Monte sua mensagem e publique em poucos segundos.</p></div></div>
    <div class="status">● BOT ONLINE</div>
  </div>

  {% with messages = get_flashed_messages(with_categories=true) %}
    {% for category, msg in messages %}
      <div class="flash {{ 'ok' if category=='ok' else 'err' }}">{{ msg }}</div>
    {% endfor %}
  {% endwith %}

  <div class="grid">
    <section class="card">
      <h2>Nova publicação</h2>
      <p class="sub">Adicione texto, fotos e um botão. Depois toque em Disparar.</p>
      <form method="post" action="{{ url_for('send') }}" enctype="multipart/form-data" id="sendForm">
        <div class="field">
          <label>Canal / grupo de destino</label>
          <input name="chat_id" value="{{ default_chat }}" placeholder="-1001234567890 ou @seucanal">
          <div class="hint">O bot precisa estar no canal/grupo e ter permissão para publicar.</div>
        </div>

        <div class="field">
          <label>Texto da mensagem</label>
          <textarea name="caption" id="caption" placeholder="Digite aqui a legenda...

Exemplo de texto clicável:
[ENTRA AQUI AGORA!](https://t.me/seulink)"></textarea>
        </div>

        <div class="field">
          <label>Fotos / vídeos</label>
          <div class="drop">
            <input type="file" name="media" id="media" accept="image/*,video/*" multiple>
            <div class="hint">Você pode selecionar várias fotos para enviar como álbum. Para texto clicável, use: [texto](https://link)</div>
          </div>
        </div>

        <div class="row">
          <div class="field">
            <label>Texto do botão</label>
            <input name="button_text" id="button_text" value="ENTRAR" placeholder="ENTRAR">
          </div>
          <div class="field">
            <label>Link do botão</label>
            <input name="button_url" id="button_url" placeholder="https://t.me/...">
          </div>
        </div>

        <div class="actions">
          <button class="btn secondary" type="button" id="clearBtn">Limpar</button>
          <button class="btn primary" type="submit" id="sendBtn">🚀 DISPARAR</button>
        </div>
      </form>
    </section>

    <aside class="card">
      <h2>Prévia</h2>
      <p class="sub">Assim ficará visualmente parecido no Telegram.</p>
      <div class="preview">
        <div class="preview-head">Prévia da publicação</div>
        <div class="preview-media" id="previewMedia"></div>
        <div class="preview-body"><span id="previewText">Seu texto aparecerá aqui...</span><br><a class="button-preview" id="previewButton" href="#" target="_blank" style="display:none">ENTRAR</a></div>
      </div>
      <div style="height:18px"></div>
      <h2>Últimos disparos</h2>
      <div class="hist">
        {% if history %}
          {% for item in history %}
            <div class="item">
              <div class="item-top"><span class="pill">ENVIADO</span><span class="time">{{ item.time }}</span></div>
              <div class="item-text">{{ item.caption }}</div>
            </div>
          {% endfor %}
        {% else %}
          <div class="item"><div class="item-text">Nenhum disparo ainda.</div></div>
        {% endif %}
      </div>
    </aside>
  </div>
</div>
<script>
const caption=document.getElementById('caption');
const buttonText=document.getElementById('button_text');
const buttonUrl=document.getElementById('button_url');
const media=document.getElementById('media');
const previewText=document.getElementById('previewText');
const previewButton=document.getElementById('previewButton');
const previewMedia=document.getElementById('previewMedia');
const form=document.getElementById('sendForm');
const sendBtn=document.getElementById('sendBtn');

function updatePreview(){
  previewText.textContent=caption.value || 'Seu texto aparecerá aqui...';
  const txt=buttonText.value.trim();
  const url=buttonUrl.value.trim();
  if(txt && url){ previewButton.style.display='inline-block'; previewButton.textContent=txt; previewButton.href=url; }
  else previewButton.style.display='none';
}
function renderMedia(){
  previewMedia.innerHTML='';
  const files=[...media.files].slice(0,10);
  files.forEach(f=>{
    if(f.type.startsWith('image/')){
      const img=document.createElement('img');
      img.alt='Prévia da foto';
      img.src=URL.createObjectURL(f);
      previewMedia.appendChild(img);
    }
  });
}
caption.addEventListener('input',updatePreview);
buttonText.addEventListener('input',updatePreview);
buttonUrl.addEventListener('input',updatePreview);
media.addEventListener('change',renderMedia);
document.getElementById('clearBtn').addEventListener('click',()=>{
  caption.value=''; buttonUrl.value=''; buttonText.value='ENTRAR'; media.value=''; renderMedia(); updatePreview();
});
form.addEventListener('submit',()=>{sendBtn.disabled=true;sendBtn.textContent='⏳ ENVIANDO...';});
updatePreview();
</script>
</body>
</html>
"""

def auth_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        auth = request.authorization
        if not auth or auth.username != PANEL_USER or auth.password != PANEL_PASSWORD:
            return ("Autenticação necessária", 401, {"WWW-Authenticate": 'Basic realm="Disparador Telegram"'})
        return fn(*args, **kwargs)
    return wrapper

def api_url(method):
    return f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"

def telegram(method, **data):
    r = requests.post(api_url(method), data=data, timeout=60)
    try:
        payload = r.json()
    except Exception:
        payload = {"ok": False, "description": r.text}
    if not r.ok or not payload.get("ok"):
        raise RuntimeError(payload.get("description", "Erro na API do Telegram"))
    return payload["result"]

def format_caption(caption):
    """Converte [texto](https://link) em hyperlink HTML do Telegram.
    O restante do texto é escapado para não quebrar o parse do Telegram.
    """
    if not caption:
        return ""
    pattern = re.compile(r"\[([^\]\n]+)\]\((https?://[^)\s]+|tg://[^)\s]+)\)")
    parts = []
    pos = 0
    for match in pattern.finditer(caption):
        parts.append(html.escape(caption[pos:match.start()]))
        label = html.escape(match.group(1))
        url = html.escape(match.group(2), quote=True)
        parts.append(f'<a href="{url}">{label}</a>')
        pos = match.end()
    parts.append(html.escape(caption[pos:]))
    return "".join(parts)

def send_one(chat_id, file_storage, caption, button_text, button_url):
    file_storage.stream.seek(0)
    filename = file_storage.filename or "arquivo"
    mime = file_storage.mimetype or ""
    if mime.startswith("image/"):
        method = "sendPhoto"
        field = "photo"
    elif mime.startswith("video/"):
        method = "sendVideo"
        field = "video"
    else:
        method = "sendDocument"
        field = "document"

    data = {"chat_id": chat_id}
    if caption:
        data["caption"] = format_caption(caption)
        data["parse_mode"] = "HTML"
    if button_text and button_url:
        data["reply_markup"] = __import__("json").dumps({
            "inline_keyboard": [[{"text": button_text, "url": button_url}]]
        })
    files = {field: (filename, file_storage.stream, mime or "application/octet-stream")}
    r = requests.post(api_url(method), data=data, files=files, timeout=120)
    try:
        payload = r.json()
    except Exception:
        payload = {"ok": False, "description": r.text}
    if not r.ok or not payload.get("ok"):
        raise RuntimeError(payload.get("description", "Erro ao enviar mídia"))
    return payload["result"]

def send_album(chat_id, files, caption, button_text, button_url):
    # Bot API sendMediaGroup supports up to 10 photos/videos.
    # Inline keyboard cannot be attached directly to individual album items,
    # so when a button is requested we send the album first and then a button message.
    media_specs=[]
    open_files=[]
    try:
        for i, fs in enumerate(files[:10]):
            fs.stream.seek(0)
            filename=fs.filename or f"media_{i}"
            mime=fs.mimetype or ""
            if mime.startswith("image/"):
                kind="photo"
            elif mime.startswith("video/"):
                kind="video"
            else:
                raise RuntimeError("Álbuns aceitam apenas fotos e vídeos.")
            attach=f"file{i}"
            item={"type":kind,"media":f"attach://{attach}"}
            if i==0 and caption:
                item["caption"]=format_caption(caption)
                item["parse_mode"]="HTML"
            media_specs.append(item)
            open_files.append((attach, filename, fs.stream, mime or "application/octet-stream"))
        data={"chat_id":chat_id, "media":__import__("json").dumps(media_specs, ensure_ascii=False)}
        multipart={k:(fn,stream,mime) for k,fn,stream,mime in open_files}
        r=requests.post(api_url("sendMediaGroup"), data=data, files=multipart, timeout=180)
        try: payload=r.json()
        except Exception: payload={"ok":False,"description":r.text}
        if not r.ok or not payload.get("ok"):
            raise RuntimeError(payload.get("description","Erro ao enviar álbum"))
        if button_text and button_url:
            telegram("sendMessage", chat_id=chat_id, text="👇 Acesse aqui:", reply_markup=__import__("json").dumps({
                "inline_keyboard":[[{"text":button_text,"url":button_url}]]
            }))
        return payload["result"]
    finally:
        for _,_,stream,_ in open_files:
            try: stream.close()
            except Exception: pass

@app.get("/health")
def health():
    if not BOT_TOKEN:
        return {"ok": False, "telegram": False, "error": "BOT_TOKEN não configurado"}, 500
    try:
        me=telegram("getMe")
        return {"ok": True, "telegram": True, "bot": me.get("username")}
    except Exception as e:
        return {"ok": False, "telegram": False, "error": str(e)}, 500

@app.route("/", methods=["GET"])
@auth_required
def index():
    return render_template_string(HTML, history=history[:12], default_chat=DEFAULT_CHAT_ID)

@app.post("/send")
@auth_required
def send():
    if not BOT_TOKEN:
        flash("BOT_TOKEN não configurado no Render.", "err")
        return redirect(url_for("index"))
    chat_id=(request.form.get("chat_id") or DEFAULT_CHAT_ID).strip()
    caption=request.form.get("caption","").strip()
    button_text=request.form.get("button_text","").strip()
    button_url=request.form.get("button_url","").strip()
    files=[f for f in request.files.getlist("media") if f and f.filename]
    if not chat_id:
        flash("Informe o canal/grupo de destino.", "err")
        return redirect(url_for("index"))
    if not caption and not files:
        flash("Coloque um texto ou pelo menos uma foto/vídeo.", "err")
        return redirect(url_for("index"))
    if button_url and not (button_url.startswith("http://") or button_url.startswith("https://") or button_url.startswith("tg://")):
        flash("O link do botão precisa começar com http://, https:// ou tg://.", "err")
        return redirect(url_for("index"))
    try:
        if len(files)>1:
            send_album(chat_id, files, caption, button_text, button_url)
        elif len(files)==1:
            send_one(chat_id, files[0], caption, button_text, button_url)
        else:
            markup=None
            if button_text and button_url:
                markup=__import__("json").dumps({"inline_keyboard":[[{"text":button_text,"url":button_url}]]})
            telegram("sendMessage", chat_id=chat_id, text=format_caption(caption), parse_mode="HTML", reply_markup=markup)
        history.insert(0, {"time": time.strftime("%d/%m %H:%M"), "caption": caption or "[mídia]", "chat_id": chat_id})
        del history[12:]
        flash("Mensagem disparada com sucesso! 🚀", "ok")
    except Exception as e:
        flash(f"Não foi possível enviar: {e}", "err")
    return redirect(url_for("index"))

@app.errorhandler(413)
def too_large(e):
    flash("Arquivo muito grande. O limite do painel é 50 MB.", "err")
    return redirect(url_for("index"))

if __name__ == "__main__":
    port=int(os.getenv("PORT","10000"))
    app.run(host="0.0.0.0", port=port)
