"""Iš restorano nuotraukos ir AI versijos (po.jpg) sukuria prieš/po paveikslėlį ir puslapį."""
import json, os, sys, io, urllib.request
from PIL import Image, ImageEnhance, ImageFilter, ImageOps, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SIZE = 1200

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    return Image.open(io.BytesIO(urllib.request.urlopen(req, timeout=60).read())).convert("RGB")

def square(im, n):
    return ImageOps.fit(im, (n, n), Image.LANCZOS)

def combo(b, a):
    n, pad, top = 700, 24, 70
    c = Image.new("RGB", (n * 2 + pad * 3, n + top + pad), "white")
    c.paste(square(b, n), (pad, top)); c.paste(a.resize((n, n), Image.LANCZOS), (pad * 2 + n, top))
    d = ImageDraw.Draw(c)
    try: f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 30)
    except OSError: f = ImageFont.load_default()
    for x, t in [(pad, "PRIEŠ"), (pad * 2 + n, "PO")]:
        d.text((x + (n - d.textlength(t, font=f)) / 2, 20), t, fill=(40, 40, 40), font=f)
    return c

def main():
    tpl = open(os.path.join(ROOT, "sablonai/pavyzdys.html"), encoding="utf-8").read()
    for r in json.load(open(os.path.join(ROOT, "restoranai.json"), encoding="utf-8")):
        out = os.path.join(ROOT, "pavyzdziai", r["slug"])
        po_path = os.path.join(out, "po.jpg")
        if not os.path.exists(po_path) or (os.path.exists(os.path.join(out, "index.html")) and not r.get("perdaryti")):
            continue
        try:
            src = fetch(r["nuotrauka"])
            a = Image.open(po_path).convert("RGB")
            square(src, SIZE).save(os.path.join(out, "pries.jpg"), quality=88)
            combo(src, a).save(os.path.join(out, "pries-po.jpg"), quality=85)
            subj = urllib.request.quote(r["pavadinimas"] + " – nuotraukos")
            html = tpl.replace("{{RESTORANAS}}", r["pavadinimas"]).replace("{{RESTORANAS_URL}}", subj)
            open(os.path.join(out, "index.html"), "w", encoding="utf-8").write(html)
            print("OK", r["slug"])
        except Exception as e:
            print("KLAIDA", r["slug"], e, file=sys.stderr)

if __name__ == "__main__":
    main()
