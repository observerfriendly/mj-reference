import json
import os
import re
import sys
from collections import Counter

REPO = "/home/claude/willwulfken/mj-ref-tree"
PAGES = os.path.join(REPO, "Pages")
OUT = "/home/claude/build/out"

RAW = "https://raw.githubusercontent.com/willwulfken/MidJourney-Styles-and-Keywords-Reference/main"

IMG_RE = re.compile(r'<img[^>]+src="([^"]+)"', re.I)
SUMMARY_RE = re.compile(r"<summary>(.*?)</summary>", re.I | re.S)
H2_RE = re.compile(r"<h2>(.*?)</h2>", re.I | re.S)
TAG_RE = re.compile(r"<[^>]+>")
ALIGN_RE = re.compile(r"^\|[\s:\-|]+\|$")

# strip emoji / pictographs / variation selectors
EMOJI_RE = re.compile(
    "["
    "\U0001f000-\U0001faff"
    "\u2190-\u21ff"
    "\u2300-\u27bf"
    "\u2b00-\u2bff"
    "\ufe00-\ufe0f"
    "\u200d"
    "]+"
)

VERSION_ORDER = {
    "MJ_V1": 1,
    "MJ_V2": 2,
    "MJ_V3": 3,
    "MJ_V4": 4,
    "MJ_V5": 5,
}


def clean(text):
    text = TAG_RE.sub(" ", text)
    text = EMOJI_RE.sub(" ", text)
    text = text.replace("&amp;", "&").replace("&nbsp;", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip(" .*_|")


def split_row(line):
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    return line.split("|")


def version_of(path, img_src):
    for key in VERSION_ORDER:
        if "/" + key + "/" in img_src or "/" + key + "/" in path:
            return key
    if "Niji" in img_src or "Niji" in path:
        return "Niji"
    return "Other"


def image_url(src):
    src = src.split("?")[0]
    if src.startswith("http"):
        return src
    if not src.startswith("/"):
        src = "/" + src
    return RAW + src


def parse_file(relpath):
    """Yield dicts of keyword entries found in one markdown page."""
    full = os.path.join(PAGES, relpath)
    with open(full, "r", encoding="utf-8", errors="replace") as fh:
        lines = fh.read().split("\n")

    category = os.path.splitext(os.path.basename(relpath))[0].replace("_", " ")
    page_title = None
    section = None
    entries = []

    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]

        if page_title is None:
            m = H2_RE.search(line)
            if m:
                page_title = clean(m.group(1))

        for m in SUMMARY_RE.finditer(line):
            section = clean(m.group(1)) or None

        stripped = line.strip()
        is_row = stripped.startswith("|") and stripped.count("|") >= 2

        # A header row: table row with no images, followed by an alignment row.
        if is_row and "<img" not in stripped and i + 1 < n and ALIGN_RE.match(lines[i + 1].strip()):
            headers = [clean(c) for c in split_row(stripped)]
            j = i + 2
            # collect the image rows belonging to this header
            while j < n:
                body = lines[j].strip()
                if not body.startswith("|"):
                    break
                if ALIGN_RE.match(body):
                    j += 1
                    continue
                if "<img" not in body:
                    break
                cells = split_row(body)
                for col, cell in enumerate(cells):
                    if col >= len(headers):
                        break
                    kw = headers[col]
                    if not kw or len(kw) > 80:
                        continue
                    im = IMG_RE.search(cell)
                    if not im:
                        continue
                    src = im.group(1)
                    if "/Repo_Parts/" in src or "/Sponsor_Images/" in src:
                        continue
                    entries.append(
                        {
                            "keyword": kw,
                            "category": category,
                            "section": section,
                            "page": page_title or category,
                            "version": version_of(relpath, src),
                            "image": image_url(src),
                        }
                    )
                j += 1
            i = j
            continue

        i += 1

    return entries


def main():
    os.makedirs(OUT, exist_ok=True)

    all_entries = []
    files = []
    for root, _dirs, names in os.walk(PAGES):
        for name in names:
            if name.endswith(".md"):
                files.append(os.path.relpath(os.path.join(root, name), PAGES))
    files.sort()

    for rel in files:
        all_entries.extend(parse_file(rel))

    # Flatten to one vocabulary: keep the newest version's render per keyword.
    best = {}
    for e in all_entries:
        if e["version"] == "Other":
            continue
        key = e["keyword"].lower()
        rank = VERSION_ORDER.get(e["version"], 0)
        prev = best.get(key)
        if prev is None or rank > prev["_rank"]:
            rec = dict(e)
            rec["_rank"] = rank
            best[key] = rec

    flat = []
    for rec in best.values():
        rec.pop("_rank", None)
        flat.append(rec)
    flat.sort(key=lambda r: (r["category"].lower(), r["keyword"].lower()))

    with open(os.path.join(OUT, "keywords.json"), "w", encoding="utf-8") as fh:
        json.dump(flat, fh, ensure_ascii=False, indent=0)

    print("pages parsed:      ", len(files))
    print("raw pairs found:   ", len(all_entries))
    print("unique keywords:   ", len(flat))
    print()
    print("by source version:")
    for v, c in Counter(r["version"] for r in flat).most_common():
        print("  %-6s %5d" % (v, c))
    print()
    print("top categories:")
    for c, k in Counter(r["category"] for r in flat).most_common(18):
        print("  %-28s %5d" % (c, k))
    print()
    print("total categories:  ", len(set(r["category"] for r in flat)))
    print()
    print("sample:")
    for r in flat[:6]:
        print("  %-26s | %-18s | %s" % (r["keyword"][:26], r["category"][:18], r["image"][-52:]))


if __name__ == "__main__":
    main()
