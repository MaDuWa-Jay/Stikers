#!/usr/bin/env python3
"""
Telegram sticker pack  ->  folder of WhatsApp-ready stickers + pack.json   (run on YOUR PC, not in the app)

Static (.webp)      -> 512x512 webp
Video  (.webm)      -> animated webp (512x512, <= 500 KB)     needs ffmpeg
Animated (.tgs)     -> animated webp (512x512, <= 500 KB)     needs ffmpeg + python-lottie  (pip install lottie[all])

Usage:
  python3 tg_pack_to_json.py --token 123:ABC --pack https://t.me/addstickers/PackName \
      --out ./packs/PackName --base-url https://yourdomain.com/packs/PackName

Then upload the whole folder to any web host / GitHub Pages, and put
  https://yourdomain.com/packs/PackName/pack.json
as the url in MyStickerPacks.kt.
"""
import argparse, json, os, re, shutil, subprocess, sys, tempfile, urllib.parse, urllib.request

MAX_ANIM_BYTES = 500_000
MAX_STATIC_BYTES = 100_000
# (fps, quality) tried in order until the file fits
ANIM_TRIES = [(15, 60), (12, 50), (10, 40), (8, 30), (6, 20)]
VF_BASE = ("scale=512:512:force_original_aspect_ratio=decrease,format=rgba,"
           "pad=512:512:(ow-iw)/2:(oh-ih)/2:color=0x00000000")


def api(token, method, **params):
    url = f"https://api.telegram.org/bot{token}/{method}?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=30) as r:
        data = json.load(r)
    if not data.get("ok"):
        raise RuntimeError(data.get("description", "Telegram error"))
    return data["result"]


def download(token, file_id, dest):
    path = api(token, "getFile", file_id=file_id)["file_path"]
    urllib.request.urlretrieve(f"https://api.telegram.org/file/bot{token}/{path}", dest)
    return path


def video_to_anim_webp(src, dst, decoder_hint=True):
    """webm (VP9 + alpha) or gif -> animated webp. Forcing libvpx-vp9 keeps the transparency."""
    for fps, q in ANIM_TRIES:
        cmd = ["ffmpeg", "-y", "-loglevel", "error"]
        if src.endswith(".webm") and decoder_hint:
            cmd += ["-c:v", "libvpx-vp9"]          # native vp9 decoder drops alpha
        cmd += ["-i", src, "-vf", f"fps={fps},{VF_BASE}", "-c:v", "libwebp", "-lossless", "0",
                "-q:v", str(q), "-loop", "0", "-an", "-vsync", "0", "-t", "10", dst]
        subprocess.run(cmd, check=True)
        if os.path.getsize(dst) <= MAX_ANIM_BYTES:
            return
    raise RuntimeError(f"{os.path.basename(src)}: can't get under 500 KB")


def tgs_to_anim_webp(src, dst):
    gif = dst + ".gif"
    subprocess.run(["lottie_convert.py", src, gif], check=True)
    video_to_anim_webp(gif, dst, decoder_hint=False)
    os.remove(gif)


def static_to_webp(src, dst):
    from PIL import Image
    im = Image.open(src).convert("RGBA")
    im.thumbnail((512, 512))
    canvas = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
    canvas.paste(im, ((512 - im.width) // 2, (512 - im.height) // 2), im)
    for q in (90, 80, 70, 60, 50, 40, 30):
        canvas.save(dst, "WEBP", quality=q)
        if os.path.getsize(dst) <= MAX_STATIC_BYTES:
            return


def convert_pack(token, pack, out, base_url=""):
    """Downloads + converts one Telegram pack into `out`. Returns the list of sticker URLs/paths for pack.json."""
    name = pack.strip().split("?")[0].rstrip("/").split("/")[-1]
    os.makedirs(out, exist_ok=True)
    stickers = api(token, "getStickerSet", name=name)["stickers"]
    files = []
    tmp = tempfile.mkdtemp()
    try:
        for i, s in enumerate(stickers, 1):
            raw = os.path.join(tmp, f"{i}.raw")
            path = download(token, s["file_id"], raw)
            ext = os.path.splitext(path)[1].lower()
            out_name = f"{len(files) + 1}.webp"
            dst = os.path.join(out, out_name)
            try:
                if ext == ".webm":
                    shutil.move(raw, raw + ".webm"); video_to_anim_webp(raw + ".webm", dst)
                elif ext == ".tgs":
                    shutil.move(raw, raw + ".tgs"); tgs_to_anim_webp(raw + ".tgs", dst)
                else:
                    static_to_webp(raw, dst)
            except Exception as e:
                print(f"  skip {i}: {e}", file=sys.stderr)
                continue
            files.append(out_name)
            print(f"  {i}/{len(stickers)} ok ({ext})")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    base = base_url.rstrip("/")
    return [f"{base}/{n}" if base else n for n in files]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--token", required=True)
    ap.add_argument("--pack", required=True, help="t.me/addstickers/Name or just Name")
    ap.add_argument("--out", required=True)
    ap.add_argument("--base-url", default="", help="public URL of the --out folder (no trailing slash)")
    a = ap.parse_args()
    urls = convert_pack(a.token, a.pack, a.out, a.base_url)
    with open(os.path.join(a.out, "pack.json"), "w", encoding="utf-8") as f:
        json.dump({"stickers": urls}, f, indent=1)
    print(f"done: {len(urls)} stickers -> {a.out}/pack.json")


if __name__ == "__main__":
    main()
