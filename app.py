import re
import bisect
import requests
from flask import Flask, jsonify, request
from youtube_transcript_api import YouTubeTranscriptApi

app = Flask(__name__, static_folder="static", static_url_path="")
LANGS = {"pt", "en", "es"}
NOISE = re.compile(r"^[\[\(♪♫\s]*(m[úu]sica|music|musica|applause|aplausos|instrumental)?[\]\)♪♫\s]*$", re.I)
UA = {"User-Agent": "LyricType/1.0 (https://github.com/local/lyrictype)"}
YT_CACHE, LRC_CACHE = {}, {}


class ApiErr(Exception):
    def __init__(self, msg, status=404):
        self.msg, self.status = msg, status


def video_id(u):
    m = re.search(r"(?:v=|youtu\.be/|shorts/|embed/)([\w-]{11})", u)
    if m:
        return m.group(1)
    return u if re.fullmatch(r"[\w-]{11}", u) else None


def clean(s):
    return re.sub(r"\s+", " ", s).strip()


def trim(cache):
    if len(cache) > 20:
        cache.clear()


# ---------- LRCLIB ----------
def yt_meta(v):
    r = requests.get("https://www.youtube.com/oembed", headers=UA, timeout=8,
                     params={"url": f"https://www.youtube.com/watch?v={v}", "format": "json"})
    j = r.json()
    return j["title"], j["author_name"]


def split_title(title, author):
    t = re.sub(r"[\(\[][^\)\]]*(official|video|v[ií]deo|lyric|audio|visuali[sz]er|clip|hd|4k|remaster|live|letra|legendado|tradu)[^\)\]]*[\)\]]", "", title, flags=re.I)
    t = re.sub(r"\s(feat\.?|ft\.?)\s.*$", "", t, flags=re.I)
    t = re.sub(r"\s*\|.*$", "", t)
    t = clean(t).strip(" -–—")
    a = clean(re.sub(r"\s*(-\s*topic|vevo|official)$", "", author, flags=re.I))
    parts = re.split(r"\s[-–—]\s", t, maxsplit=1)
    if len(parts) == 2:
        return clean(parts[0]), clean(parts[1])
    return a, t


def parse_lrc(s):
    out = []
    for ln in s.splitlines():
        m = re.match(r"^\s*((?:\[\d+:\d+(?:\.\d+)?\])+)\s*(.*)$", ln)
        if not m:
            continue
        for mm in re.finditer(r"\[(\d+):(\d+(?:\.\d+)?)\]", m.group(1)):
            out.append((int(mm.group(1)) * 60 + float(mm.group(2)), clean(m.group(2))))
    return sorted(out, key=lambda x: x[0])


def lrclib_search(**p):
    r = requests.get("https://lrclib.net/api/search", params=p, headers=UA, timeout=10)
    return r.json() if r.ok else []


STOP = {
    "en": "the and you i to a me my in it of is that on for with this be we are your but all so not love"
          " just like know oh baby no yeah what when".split(),
    "pt": "o a os as e é que de da do em um uma não eu você tu te me meu minha com para por se mas está"
          " amor coração vida nós ela ele quando já só".split(),
    "es": "el la los las y es que de del en un una no yo tú te me mi con para por se pero está amor"
          " corazón vida nosotros ella él cuando ya solo".split(),
}


def guess_lang(text):
    words = re.findall(r"[a-záéíóúâêôãõçñü']+", text.lower())
    score = {k: sum(w in set(v) for w in words) for k, v in STOP.items()}
    return max(score, key=score.get)


def get_lrc(v, dur):
    k = (v, dur)
    if k in LRC_CACHE:
        return LRC_CACHE[k]
    try:
        title, author = yt_meta(v)
        artist, track = split_title(title, author)
        res = (lrclib_search(track_name=track, artist_name=artist)
               or lrclib_search(q=f"{artist} {track}") or lrclib_search(q=title))
        res = [x for x in res if x.get("syncedLyrics")]
        if not res:
            return None
        if dur:
            res.sort(key=lambda x: abs((x.get("duration") or 0) - dur))
        stamps = parse_lrc(res[0]["syncedLyrics"])
    except Exception:
        return None
    lines = []
    for i, (st, text) in enumerate(stamps):
        if not text or NOISE.match(text):
            continue
        nxt = stamps[i + 1][0] if i + 1 < len(stamps) else st + 4
        lines.append({"s": round(st, 2), "e": round(max(min(nxt, st + 10), st + 0.8), 2), "t": text})
    if len(lines) < 3:
        return None
    orig = guess_lang(" ".join(l["t"] for l in lines))
    trim(LRC_CACHE)
    LRC_CACHE[k] = {"source": "lrclib", "orig": orig, "generated": False, "lines": lines, "tr": {}}
    return LRC_CACHE[k]


def translate_lrc(data, lang):
    if lang in data["tr"]:
        return data["tr"][lang]
    from deep_translator import GoogleTranslator
    texts = [l["t"] for l in data["lines"]]
    gt = GoogleTranslator(source="auto", target=lang)
    out = []
    for i in range(0, len(texts), 40):
        chunk = texts[i:i + 40]
        res = gt.translate_batch(chunk)
        out += [r or c for r, c in zip(res, chunk)]
    data["tr"][lang] = out
    return out


# ---------- Legenda do YouTube ----------
def load_yt(v):
    if v in YT_CACHE:
        return YT_CACHE[v]
    try:
        items = list(YouTubeTranscriptApi().list(v))
        # A legenda automática está sempre no idioma falado (o original).
        t = next((x for x in items if x.is_generated), None)
        if t is None:
            sup = [x for x in items if x.language_code[:2] in LANGS]
            t = (sup or items)[0]
        raw = [(clean(s.text), s.start, s.duration) for s in t.fetch()]
    except Exception:
        raise ApiErr("Este vídeo não tem legenda disponível e a LRCLIB não achou a letra. Tente outra versão da música.")
    lines = []
    for i, (text, start, dur) in enumerate(raw):
        if not text or NOISE.match(text):
            continue
        nxt = raw[i + 1][1] if i + 1 < len(raw) else start + dur
        end = min(start + dur, nxt) if nxt > start else start + dur
        lines.append({"s": round(start, 2), "e": round(max(end, start + 0.8), 2), "t": text, "i": i})
    if len(lines) < 3:
        raise ApiErr("Legenda curta demais para montar o jogo.", 422)
    trim(YT_CACHE)
    YT_CACHE[v] = {"source": "yt", "orig": t.language_code[:2], "generated": t.is_generated,
                   "lines": lines, "raw": raw, "t": t, "tr": {}}
    return YT_CACHE[v]


def translate_yt(data, lang):
    if lang in data["tr"]:
        return data["tr"][lang]
    t = data["t"]
    if not t.is_translatable:
        raise ValueError
    tr = [(clean(s.text), s.start) for s in t.translate(lang).fetch()]
    starts = [x[1] for x in tr]
    by_raw, used = {}, -1
    for i, (_, st, _) in enumerate(data["raw"]):
        j = bisect.bisect_left(starts, st - 0.05)
        cand = [k for k in (j - 1, j) if 0 <= k < len(tr)]
        k = min(cand, key=lambda c: abs(starts[c] - st))
        by_raw[i] = "" if k == used else tr[k][0]
        used = k
    out = [by_raw[l["i"]] for l in data["lines"]]
    data["tr"][lang] = out
    return out


@app.get("/")
def index():
    return app.send_static_file("index.html")


@app.get("/api/lyrics")
def lyrics():
    v = video_id(request.args.get("url", "").strip())
    if not v:
        return jsonify(error="Link inválido. Cole um link do YouTube."), 400
    lang = request.args.get("lang", "")[:2].lower()
    src = request.args.get("src", "auto")
    try:
        dur = int(request.args.get("dur", 0))
    except ValueError:
        dur = 0
    try:
        data = get_lrc(v, dur) if src in ("auto", "lrclib") else None
        if data is None and src == "lrclib":
            raise ApiErr("A LRCLIB não tem letra sincronizada para esta música. Use a legenda do YouTube.")
        if data is None:
            data = load_yt(v)
    except ApiErr as e:
        return jsonify(error=e.msg), e.status

    orig, texts = data["orig"], [l["t"] for l in data["lines"]]
    if lang in LANGS and lang != orig:
        try:
            texts = translate_lrc(data, lang) if data["source"] == "lrclib" else translate_yt(data, lang)
        except Exception:
            return jsonify(error="Não foi possível traduzir a letra para esse idioma. Use a letra original."), 422
    else:
        lang = orig
    lines = [{"s": l["s"], "e": l["e"], "t": t} for l, t in zip(data["lines"], texts)]
    return jsonify(id=v, lang=lang, orig=orig, generated=data["generated"], source=data["source"], lines=lines)


if __name__ == "__main__":
    app.run(host = "0.0.0.0", port=5000, debug=False)