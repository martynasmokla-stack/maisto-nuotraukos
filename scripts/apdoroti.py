"""Apdoroja restoranų nuotraukas: baltas fonas, šviesa, spalvos, prieš/po ir puslapis."""
import json, os, sys, io, urllib.request
from PIL import Image, ImageEnhance, ImageFilter, ImageOps, ImageDraw, ImageFont
from rembg import remove, new_session

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SIZE = 1200
session = new_session("isnet-general-use")

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    return Image.open(io.BytesIO(urllib.request.urlopen(req, timeout=60).read())).convert("RGB")

def square(im, n):
    return ImageOps.fit(im, (n, n), Image.LANCZOS)

def po(src):
    cut = remove(src, session=session, post_process_mask=True)
    bbox = cut.getchannel("A").point(lambda a: 255 if a > 20 else 0).getbbox()
    cut = cut.crop(bbox)
    rgb = cut.convert("RGB")
    rgb = ImageEnhance.Brightness(rgb).enhance(1.08)
    rgb = ImageEnhance.Contrast(rgb).enhance(1.10)
    rgb = ImageEnhance.Color(rgb).enhance(1.18)
    rgb = rgb.filter(ImageFilter.UnsharpMask(radius=2, percent=80, threshold=2))
    alpha = cut.getchannel("A")
    inner = int(SIZE * 0.82)
    scale = inner / max(rgb.size)
    w, h = int(rgb.width * scale), int(rgb.height * scale)
    rgb, alpha = rgb.resize((w, h), Image.LANCZOS), alpha.resize((w, h), Image.LANCZOS)
    canvas = Image.new("RGB", (SIZE, SIZE), (255, 255, 255))
    x, y = (SIZE - w) // 2, (SIZE - h) // 2
    shadow = Image.new("L", (SIZE, SIZE), 0)
    shadow.paste(alpha.point(lambda a: int(a * 0.28)), (x + 10, y + 22))
    shadow = shadow.filter(ImageFilter.GaussianBlur(28))
    canvas = Image.composite(Image.new("RGB", canvas.size, (200, 196, 190)), canvas, shadow)
    canvas.paste(rgb, (x, y), alpha)
    return canvas

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
        if os.path.exists(os.path.join(out, "po.jpg")) and not r.get("perdaryti"):
            continue
        try:
            src = fetch(r["nuotrauka"])
            os.makedirs(out, exist_ok=True)
            b, a = square(src, SIZE), po(src)
            b.save(os.path.join(out, "pries.jpg"), quality=88)
            a.save(os.path.join(out, "po.jpg"), quality=90)
            combo(src, a).save(os.path.join(out, "pries-po.jpg"), quality=85)
            subj = urllib.request.quote(r["pavadinimas"] + " – nuotraukos")
            html = tpl.replace("{{RESTORANAS}}", r["pavadinimas"]).replace("{{RESTORANAS_URL}}", subj)
            open(os.path.join(out, "index.html"), "w", encoding="utf-8").write(html)
            print("OK", r["slug"])
        except Exception as e:
            print("KLAIDA", r["slug"], e, file=sys.stderr)

if __name__ == "__main__":
    main()
