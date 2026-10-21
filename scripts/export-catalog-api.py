#!/usr/bin/env python3
"""Export Mac catalog.db → data/catalog.json for the React static build.

Shape matches maison fetchTree/fetchProducts (CategoryNode + Product).
Never writes 供货价/集采价. image_url → /images/<file> for GitHub Pages.
Also refreshes data/products.json + images/ (legacy thin site + simple list).
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sqlite3
from datetime import datetime, timezone
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


def tier_of(retail):
    if retail is None:
        return ""
    for cap, label in ((50, "≤50"), (100, "≤100"), (150, "≤150"), (200, "≤200"), (300, "≤300")):
        if retail <= cap:
            return label
    return "300+"


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

    cat_rows = list(conn.execute("SELECT * FROM categories ORDER BY sort_order, id"))
    counts = {
        r["category_id"]: r["n"]
        for r in conn.execute("SELECT category_id, COUNT(*) AS n FROM products GROUP BY category_id")
    }
    nodes = {r["id"]: {**dict(r), "children": []} for r in cat_rows}
    roots = []
    for node in nodes.values():
        parent = node["parent_id"]
        if parent and parent in nodes:
            nodes[parent]["children"].append(node)
        else:
            roots.append(node)

    def annotate(node):
        own = counts.get(node["id"], 0)
        below = own
        for child in node["children"]:
            below += annotate(child)
        node["direct_products"] = own
        node["product_count"] = below
        return below

    for root in roots:
        annotate(root)

    name_of = {r["id"]: r["name"] for r in cat_rows}
    field_meta = {
        r["id"]: (r["name"], r["category_id"])
        for r in conn.execute("SELECT id, name, category_id FROM fields")
    }

    src_img = db.parent / "product-images"
    dst_img = ROOT / "images"
    dst_img.mkdir(parents=True, exist_ok=True)
    keep = set()

    api_products = []
    simple_products = []

    for r in conn.execute(
        "SELECT id, category_id, name, created_at, image_path, image_width, image_height, link_url FROM products ORDER BY id"
    ):
        values = []
        vals_map = {}
        for pv in conn.execute(
            "SELECT field_id, value FROM product_values WHERE product_id = ?", (r["id"],)
        ):
            meta = field_meta.get(pv["field_id"])
            if not meta:
                continue
            fname, fcid = meta
            if fname in COST_FIELDS:
                continue
            val = (pv["value"] or "").strip()
            vals_map[fname] = val
            values.append(
                {
                    "name": fname,
                    "value": val,
                    "field_id": pv["field_id"],
                    "defined_on_id": fcid,
                    "defined_on_name": name_of.get(fcid, ""),
                    "level": None,
                }
            )

        img_name = (r["image_path"] or "").strip()
        image_url = None
        image_rel = None
        if img_name:
            s = src_img / Path(img_name).name
            if s.is_file():
                d = dst_img / s.name
                keep.add(s.name)
                if (
                    not d.exists()
                    or d.stat().st_mtime < s.stat().st_mtime
                    or d.stat().st_size != s.stat().st_size
                ):
                    shutil.copy2(s, d)
                image_url = f"images/{s.name}"
                image_rel = f"images/{s.name}"

        brand = vals_map.get("品牌", "")
        retail = price_num(vals_map.get("零售价") or vals_map.get("零售指导价") or vals_map.get("市场价") or "")
        tier = vals_map.get("价格档", "")
        if tier == "待定档":
            tier = ""
        if not tier and retail is not None:
            tier = tier_of(retail)
        model = vals_map.get("型号") or vals_map.get("料号") or ""
        spec = vals_map.get("规格", "")
        title = r["name"]
        if brand and title.startswith(brand):
            rest = title[len(brand) :].strip()
            if len(rest) >= 2:
                title = rest

        api_products.append(
            {
                "id": r["id"],
                "category_id": r["category_id"],
                "category_name": name_of.get(r["category_id"], ""),
                "name": r["name"],
                "created_at": r["created_at"] or "",
                "image_path": img_name,
                "image_url": image_url,
                "image_width": r["image_width"] or 0,
                "image_height": r["image_height"] or 0,
                "image_original_url": None,
                "image_detail_urls": [],
                "link_url": clean_link(r["link_url"] or ""),
                "values": values,
            }
        )
        simple_products.append(
            {
                "id": r["id"],
                "name": r["name"],
                "title": title,
                "brand": brand,
                "category": name_of.get(r["category_id"], ""),
                "category_id": r["category_id"],
                "retail": retail,
                "tier": tier,
                "model": model,
                "spec": spec,
                "image": image_rel,
                "link": clean_link(r["link_url"] or ""),
            }
        )

    # prune stale images
    for f in dst_img.iterdir():
        if f.is_file() and f.name not in keep and f.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
            f.unlink()

    data_dir = ROOT / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    catalog = {
        "exported_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "count": len(api_products),
        "tree": roots,
        "products": api_products,
    }
    (data_dir / "catalog.json").write_text(
        json.dumps(catalog, ensure_ascii=False, separators=(",", ":")), encoding="utf-8"
    )

    simple = {
        "brand": "华甄选",
        "company": "深圳市华甄选礼品有限公司",
        "exported_at": catalog["exported_at"],
        "count": len(simple_products),
        "categories": sorted({p["category"] for p in simple_products if p["category"]}),
        "tiers": ["≤50", "≤100", "≤150", "≤200", "≤300", "300+"],
        "products": simple_products,
    }
    (data_dir / "products.json").write_text(
        json.dumps(simple, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"exported {len(api_products)} products → data/catalog.json + data/products.json + images/ ({len(keep)} files)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", type=Path, default=DEFAULT_DB)
    args = ap.parse_args()
    export(args.db)
