#!/usr/bin/env python3
"""Export Mac catalog.db → data/products.json + images/ for this static site.

Default DB: ../huazhen-catalog/data/catalog.db (sibling of this repo).
Never writes 供货价/集采价.

Usage (from repo root):
  python3 scripts/export-from-db.py
  python3 scripts/export-from-db.py --db /path/to/catalog.db
  python3 scripts/export-from-db.py && git add data images && git commit -m "refresh catalog" && git push
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT.parent / "huazhen-catalog" / "data" / "catalog.db"
COST_FIELDS = {"供货价", "集采价"}


def price_num(raw: str):
    m = re.search(r"\d+(?:\.\d+)?", str(raw or "").replace(",", "").replace("，", ""))
    if not m:
        return None
    n = float(m.group(0))
    return n if n > 0 else None


def clean_link(link: str) -> str:
    link = (link or "").strip()
    if "item.jd.com" in link:
        m = re.search(r"(https?://item\.jd\.com/\d+\.html)", link)
        if m:
            return m.group(1)
    return link


def export(db: Path) -> None:
    if not db.is_file():
        raise SystemExit(f"DB not found: {db}")

    conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    cats = {r["id"]: r["name"] for r in conn.execute("SELECT id, name FROM categories")}
    rows = conn.execute(
        "SELECT id, name, category_id, image_path, link_url FROM products ORDER BY id"
    ).fetchall()

    def fields(pid: int) -> dict:
        out = {}
        for r in conn.execute(
            """
            SELECT f.name, pv.value FROM product_values pv
            JOIN fields f ON f.id = pv.field_id WHERE pv.product_id = ?
            """,
            (pid,),
        ):
            if r["name"] in COST_FIELDS:
                continue
            out[r["name"]] = (r["value"] or "").strip()
        return out

    products = []
    src_img = db.parent / "product-images"
    dst_img = ROOT / "images"
    dst_img.mkdir(parents=True, exist_ok=True)
    keep = set()

    for r in rows:
        vals = fields(r["id"])
        brand = vals.get("品牌", "")
        retail = price_num(vals.get("零售价") or vals.get("零售指导价") or vals.get("市场价") or "")
        tier = vals.get("价格档", "")
        if tier == "待定档":
            tier = ""
        model = vals.get("型号") or vals.get("料号") or ""
        spec = vals.get("规格", "")
        img_name = (r["image_path"] or "").strip()
        image = None
        if img_name:
            s = src_img / Path(img_name).name
            if s.is_file():
                d = dst_img / s.name
                keep.add(s.name)
                if not d.exists() or d.stat().st_mtime < s.stat().st_mtime or d.stat().st_size != s.stat().st_size:
                    shutil.copy2(s, d)
                image = f"images/{s.name}"
        title = r["name"]
        if brand and title.startswith(brand):
            rest = title[len(brand) :].strip()
            if len(rest) >= 2:
                title = rest
        products.append(
            {
                "id": r["id"],
                "name": r["name"],
                "title": title,
                "brand": brand,
                "category": cats.get(r["category_id"], ""),
                "category_id": r["category_id"],
                "retail": retail,
                "tier": tier,
                "model": model,
                "spec": spec[:240] if spec else "",
                "image": image,
                "link": clean_link(r["link_url"] or ""),
            }
        )

    # prune stale images not in export
    for orphan in dst_img.iterdir():
        if orphan.is_file() and orphan.name not in keep:
            orphan.unlink()

    payload = {
        "brand": "华甄选",
        "company": "深圳市华甄选礼品有限公司",
        "exported_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "count": len(products),
        "categories": sorted({p["category"] for p in products if p["category"]}),
        "tiers": ["≤50", "≤100", "≤150", "≤200", "≤300", "300+"],
        "products": products,
    }
    out = ROOT / "data" / "products.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    if "供货价" in text or "集采价" in text:
        raise SystemExit("refusing to write: wholesale fields leaked")
    out.write_text(text, encoding="utf-8")
    print(f"exported {len(products)} products → {out.relative_to(ROOT)}")
    print(f"images kept: {len(keep)} under images/")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", type=Path, default=DEFAULT_DB)
    args = ap.parse_args()
    export(args.db.resolve())


if __name__ == "__main__":
    main()
