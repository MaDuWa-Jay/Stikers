#!/usr/bin/env python3
"""Reads packs.txt, converts every Telegram pack, writes site/catalog.json (this is the app's CATALOG_URL)."""
import argparse, json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tg_pack_to_json as t


def parse(path):
    packs = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = [p.strip() for p in line.split("|")]
            if len(parts) == 1:
                name, link, ver = None, parts[0], 1
            else:
                name, link = parts[0], parts[1]
                ver = int(parts[2]) if len(parts) > 2 and parts[2] else 1
            tg_name = link.split("?")[0].rstrip("/").split("/")[-1]
            packs.append((name or tg_name, link, ver))
    return packs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--packs", default="packs.txt")
    ap.add_argument("--out", default="site")
    ap.add_argument("--base-url", required=True, help="e.g. https://user.github.io/repo")
    ap.add_argument("--publisher", default="NovaKey")
    a = ap.parse_args()
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        sys.exit("TELEGRAM_BOT_TOKEN secret eka set karala naha.")

    base = a.base_url.rstrip("/")
    catalog, failed = [], []
    for name, link, ver in parse(a.packs):
        pid = re.sub(r"[^A-Za-z0-9_]", "_", name)[:60]
        print(f"== {name}  ({link})")
        try:
            urls = t.convert_pack(token, link, os.path.join(a.out, "packs", pid), f"{base}/packs/{pid}")
        except Exception as e:
            print(f"  FAILED: {e}", file=sys.stderr)
            failed.append(name)
            continue
        if not urls:
            failed.append(name)
            continue
        catalog.append({"id": pid, "name": name, "publisher": a.publisher, "version": ver, "stickers": urls})

    os.makedirs(a.out, exist_ok=True)
    with open(os.path.join(a.out, "catalog.json"), "w", encoding="utf-8") as f:
        json.dump({"packs": catalog}, f, ensure_ascii=False, indent=1)
    with open(os.path.join(a.out, "index.html"), "w", encoding="utf-8") as f:
        f.write("<!doctype html><meta charset=utf-8><title>Stickers</title><p>OK</p>")
    print(f"\n{len(catalog)} packs published" + (f", FAILED: {', '.join(failed)}" if failed else ""))
    if not catalog:
        sys.exit(1)


if __name__ == "__main__":
    main()
