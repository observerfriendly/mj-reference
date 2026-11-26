"""Slim the keyword index for mobile delivery.

keywords.json is the readable archive. index.json is what the app ships:
short keys, categories deduped into a lookup, image paths stripped to the
suffix after the repo root so the base URL isn't repeated 4,951 times.
"""

import json
import os

DATA = "/home/claude/mjref/data"
PREFIX = "https://raw.githubusercontent.com/willwulfken/MidJourney-Styles-and-Keywords-Reference/main/"


def main():
    with open(os.path.join(DATA, "keywords.json"), encoding="utf-8") as fh:
        rows = json.load(fh)

    cats = sorted({r["category"] for r in rows})
    cat_ix = {c: i for i, c in enumerate(cats)}
    vers = sorted({r["version"] for r in rows})
    ver_ix = {v: i for i, v in enumerate(vers)}

    out = []
    for r in rows:
        img = r["image"]
        if img.startswith(PREFIX):
            img = img[len(PREFIX):]
        out.append([r["keyword"], cat_ix[r["category"]], img, ver_ix[r["version"]]])

    out.sort(key=lambda e: e[0].lower())

    payload = {"prefix": PREFIX, "cats": cats, "vers": vers, "rows": out}
    path = os.path.join(DATA, "index.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, separators=(",", ":"))

    before = os.path.getsize(os.path.join(DATA, "keywords.json"))
    after = os.path.getsize(path)
    print("keywords:   ", len(out))
    print("categories: ", len(cats))
    print("archive:     %6.0f KB" % (before / 1024))
    print("shipped:     %6.0f KB  (%.0f%% smaller)" % (after / 1024, 100 - after / before * 100))


if __name__ == "__main__":
    main()
