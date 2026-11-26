"""Build the parameter/codes reference.

Descriptions are written fresh here rather than copied from Midjourney's
documentation, so the app ships facts (flags, ranges, defaults) plus our own
wording, and links out to docs.midjourney.com for the full prose.

`note` is populated only where sources genuinely conflict or a flag is
version-restricted. No note means the value was consistent across sources.
"""

import json
import os

OUT = "/home/claude/mjref/data"

OFFICIAL = "https://docs.midjourney.com/hc/en-us/articles/32859204029709-Parameter-List"

P = [
    # ---------------- the look ----------------
    dict(group="Look", name="Aspect ratio", flag="--ar", alias="--aspect",
         values="Whole-number ratios, up to 14:1", default="1:1",
         desc="Sets the shape of the frame. Both numbers must be integers.",
         example="brutalist stairwell --ar 4:5",
         note="HD output caps the ratio at 4:1."),
    dict(group="Look", name="Stylize", flag="--s", alias="--stylize",
         values="0-1000", default="100",
         desc="How much of Midjourney's own aesthetic gets applied over your literal prompt. Low stays faithful, high prettifies.",
         example="type specimen poster --s 250"),
    dict(group="Look", name="Chaos", flag="--c", alias="--chaos",
         values="0-100", default="0",
         desc="How much the images in one grid differ from each other. Raise it when you want range, not polish.",
         example="editorial grid system --c 35"),
    dict(group="Look", name="Weird", flag="--w", alias="--weird",
         values="0-3000", default="0",
         desc="Pushes toward unconventional, off-kilter results. Stacks oddly with high stylize.",
         example="swiss poster, melting grid --w 800"),
    dict(group="Look", name="Raw mode", flag="--raw", alias=None,
         values="Flag, no value", default="Off",
         desc="Turns down the automatic beautification. Closer to what you literally asked for.",
         example="studio photo of a letterpress tray --raw"),
    dict(group="Look", name="Experimental", flag="--exp", alias=None,
         values="0-100", default="0",
         desc="Adds depth, dynamics and a tone-mapped richness. Subtle low, heavy-handed high.",
         example="neon night market in rain --exp 15",
         note="V7 and V8 only. Above roughly 25 it starts overriding --s and personalization, so pull one down when combining."),
    dict(group="Look", name="Negative prompt", flag="--no", alias=None,
         values="Words, comma-separated", default=None,
         desc="Names what you don't want in the frame.",
         example="still life with fruit --no bananas, text"),
    dict(group="Look", name="Tile", flag="--tile", alias=None,
         values="Flag, no value", default="Off",
         desc="Makes the result a seamless repeating tile. The one to reach for on pattern work.",
         example="victorian damask, scheele's green --tile",
         note="Not usable with the Edit model."),
    dict(group="Look", name="Seed", flag="--seed", alias=None,
         values="0-4294967295", default="Random",
         desc="Fixes the starting noise so you can change one word and compare like for like.",
         example="art nouveau lockup --seed 1312"),

    # ---------------- references ----------------
    dict(group="References", name="Style reference", flag="--sref", alias=None,
         values="Image URL, style code, or `random`", default=None,
         desc="Match the look and feel of another image. `random` returns a reusable numeric code.",
         example="boutique hotel lobby --sref 2474514122"),
    dict(group="References", name="Style weight", flag="--sw", alias=None,
         values="0-1000", default="100",
         desc="How hard the style reference pulls.",
         example="boutique hotel lobby --sref URL --sw 250",
         note="Requires --sref."),
    dict(group="References", name="Omni reference", flag="--oref", alias=None,
         values="Image URL", default=None,
         desc="Carries a specific person, character or object into a new scene.",
         example="a duckling holding a wand --oref URL",
         note="V7. Midjourney's own parameter list marks it replaced by the Edit model in V8.x, though some third-party V8.1 guides still document it. Treat as V7-era."),
    dict(group="References", name="Omni weight", flag="--ow", alias=None,
         values="1-1000", default="100",
         desc="How hard the omni reference pulls.",
         example="portrait, studio light --oref URL --ow 200",
         note="Requires --oref. Same V7/V8 caveat as --oref."),
    dict(group="References", name="Character reference", flag="--cref", alias=None,
         values="Image URL", default=None,
         desc="The earlier way to keep a character consistent.",
         example="a knight at dawn --cref URL",
         note="Superseded by --oref in V7."),
    dict(group="References", name="Character weight", flag="--cw", alias=None,
         values="0-100", default="100",
         desc="Low keeps the face only, high carries clothing and framing too.",
         example="a knight at dawn --cref URL --cw 20",
         note="Pairs with the legacy --cref."),
    dict(group="References", name="Personalization", flag="--p", alias="--profile",
         values="Bare flag for your default, or a profile / moodboard ID", default=None,
         desc="Applies the taste profile built from the image pairs you rated.",
         example="a cosy reading nook, rain on the window --p"),
    dict(group="References", name="Image weight", flag="--iw", alias=None,
         values="0-3", default="1",
         desc="How much an attached image prompt counts against your text.",
         example="URL a cathedral of circuitry --iw 2",
         note="Requires an image prompt. Niji 7 caps at 2."),

    # ---------------- model and output ----------------
    dict(group="Model", name="Version", flag="--v", alias="--version",
         values="8.2, 8.1, 7, 6.1, 6, and older", default="8.2",
         desc="Picks the model. Prompts written for one version rarely behave the same on another.",
         example="a lighthouse in fog --v 7",
         note="V8.2 became the default around 24 July 2026. Midjourney's older GitBook docs still say V7 is the default, so that page is stale."),
    dict(group="Model", name="Niji", flag="--niji", alias=None,
         values="7 or 6", default=None,
         desc="The anime and illustration model.",
         example="a girl and her cat on a train --niji 7"),
    dict(group="Model", name="HD", flag="--hd", alias=None,
         values="Flag, no value", default=None,
         desc="Renders at 2048px natively instead of upscaling.",
         example="packaging mockup, soft light --hd",
         note="Costs more GPU time and caps aspect ratio at 4:1. One API reseller's guide claims --hd does nothing in a prompt, but that describes their API, not the Midjourney app."),
    dict(group="Model", name="SD", flag="--sd", alias=None,
         values="Flag, no value", default=None,
         desc="Renders at 1024px for less GPU time.",
         example="thumbnail sketches of a logo --sd"),
    dict(group="Model", name="Draft", flag="--draft", alias=None,
         values="Flag, no value", default="Off",
         desc="Fires off a batch of small rough images cheaply. The right tool for finding a direction before committing.",
         example="24 ideas for a record sleeve --draft",
         note="Website only. Produces 24 images around 512px. Cannot be combined with an image prompt, --sref, --oref or HD."),
    dict(group="Model", name="Quality", flag="--q", alias="--quality",
         values="Contested", default="1",
         desc="Trades render time against detail.",
         example="a ceramic vessel --q 2",
         note="Sources disagree. One current cheat sheet says V8.1 and V8.2 dropped --q entirely and that V7 takes 1, 2 or 4; an API guide says V8.1 takes 1 or 4; Midjourney's legacy docs list .25, .5 and 1 for the V6 era. Check against your own version before relying on it."),
    dict(group="Model", name="Stop", flag="--stop", alias=None,
         values="10-100", default="100",
         desc="Halts the render early for a softer, less resolved image.",
         example="a figure in mist --stop 70",
         note="V6 and earlier. Reported unavailable in V8."),
    dict(group="Model", name="Repeat", flag="--r", alias="--repeat",
         values="Up to 4, 10 or 40 depending on plan", default=None,
         desc="Runs the same prompt several times in one go.",
         example="a grid of wax seals --r 4"),
    dict(group="Model", name="Video", flag="--video", alias=None,
         values="Flag, no value", default=None,
         desc="Saves a progress video of the initial grid being built.",
         example="an unfurling fern --video"),

    # ---------------- session ----------------
    dict(group="Session", name="Fast mode", flag="--fast", alias=None,
         values="Flag, no value", default=None,
         desc="Runs this one job at full speed against your fast hours.",
         example="a brass compass --fast"),
    dict(group="Session", name="Relax mode", flag="--relax", alias=None,
         values="Flag, no value", default=None,
         desc="Runs this one job in the queue instead of burning fast hours.",
         example="a brass compass --relax"),
    dict(group="Session", name="Turbo mode", flag="--turbo", alias=None,
         values="Flag, no value", default=None,
         desc="Runs this one job on the fastest tier.",
         example="a brass compass --turbo",
         note="Reported unavailable in V8."),
    dict(group="Session", name="Stealth mode", flag="--stealth", alias=None,
         values="Flag, no value", default=None,
         desc="Keeps this job off your public profile. Pro and Mega plans.",
         example="client concept, unreleased --stealth"),
    dict(group="Session", name="Public mode", flag="--public", alias=None,
         values="Flag, no value", default=None,
         desc="Forces this job public even on a stealth-capable plan.",
         example="a study in blue --public"),
]


def main():
    os.makedirs(OUT, exist_ok=True)
    for i, p in enumerate(P):
        p.setdefault("note", None)
        p["id"] = p["flag"].lstrip("-")
        p["order"] = i
    payload = {
        "source": OFFICIAL,
        "current_default_version": "8.2",
        "parameters": P,
    }
    with open(os.path.join(OUT, "params.json"), "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=1)

    groups = {}
    for p in P:
        groups.setdefault(p["group"], 0)
        groups[p["group"]] += 1
    flagged = [p for p in P if p["note"]]
    print("parameters:", len(P))
    for g, c in groups.items():
        print("  %-12s %2d" % (g, c))
    print("with a version or conflict note:", len(flagged))
    for p in flagged:
        print("  %-10s %s" % (p["flag"], p["note"][:88]))


if __name__ == "__main__":
    main()
