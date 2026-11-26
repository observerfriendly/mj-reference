"""Inline everything into one HTML file.

The multi-file build is what deploys to Pages. This is the fallback: no
relative fetches, no service worker, no separate requests — so it renders
anywhere that can open an HTML page at all.
"""

import json
import os
import re

ROOT = "/home/claude/mjref"
OUT = os.path.join(ROOT, "dist", "mj-reference-single.html")


def read(p):
    with open(os.path.join(ROOT, p), encoding="utf-8") as fh:
        return fh.read()


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)

    html = read("index.html")
    css = read("app.css")
    js = read("app.js")
    index_json = read("data/index.json")
    params_json = read("data/params.json")

    # swap the network boot for an inline one
    js = js.replace(
        """Promise.all([
  fetch('data/index.json').then(function (r) { return r.json(); }),
  fetch('data/params.json').then(function (r) { return r.json(); })
]).then(function (res) {
  DB = res[0];
  PARAMS = res[1];""",
        """(function () {
  var res = [
    JSON.parse(document.getElementById('d-index').textContent),
    JSON.parse(document.getElementById('d-params').textContent)
  ];
  DB = res[0];
  PARAMS = res[1];""",
    )
    js = js.replace(
        """}).catch(function () {
  el.count.textContent = 'Could not load the reference data.';
});""",
        """}());""",
    )
    # no service worker in the single file
    js = re.sub(
        r"if \('serviceWorker' in navigator\) \{.*?\n\}\n", "", js, flags=re.S
    )

    html = html.replace(
        '<link rel="stylesheet" href="app.css">',
        "<style>\n" + css + "\n</style>",
    )
    html = html.replace('<link rel="manifest" href="manifest.webmanifest">', "")
    html = html.replace('<link rel="apple-touch-icon" href="icons/apple-touch-icon.png">', "")
    html = html.replace('<link rel="icon" href="icons/icon-192.png">', "")
    html = html.replace(
        '<script src="app.js"></script>',
        '<script id="d-index" type="application/json">' + index_json + "</script>\n"
        + '<script id="d-params" type="application/json">' + params_json + "</script>\n"
        + "<script>\n" + js + "\n</script>",
    )

    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(html)

    size = os.path.getsize(OUT)
    print("wrote", OUT)
    print("size: %.0f KB" % (size / 1024))
    # sanity: the boot swap actually applied
    body = read(os.path.join("dist", "mj-reference-single.html"))
    for probe, label in [
        ("d-index", "inline index data"),
        ("d-params", "inline params data"),
        ("getElementById('d-index')", "inline boot"),
    ]:
        print("  %-20s %s" % (label, "ok" if probe in body else "MISSING"))
    print("  %-20s %s" % ("no fetch() left", "ok" if "fetch('data/" not in body else "MISSING"))
    print("  %-20s %s" % ("no serviceWorker", "ok" if "serviceWorker" not in body else "MISSING"))


if __name__ == "__main__":
    main()
