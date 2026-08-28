---
name: generate
description: Generate images and videos via AI model APIs (Kie AI, fal.ai, WaveSpeed AI, Google AI Studio). Routes every request to the cheapest capable model, quotes cost before any paid video run, and files every output flat into one generations folder. Triggers on /generate, generate image, generate video, create image, thumbnail, animate.
---

# /generate

## Models

| Task | Default model | Recipe |
|---|---|---|
| Image (default) | Nano Banana 2 Lite | models/nano-banana-2-lite.md |
| Video (default) | Kling 3.0 | models/kling-3.0.md |

Read the recipe file before every generation. Do not guess request shapes or
endpoints from memory — the recipe file (or, if a field is still marked TODO
in it, the provider's live docs) is the source of truth, since model ids and
schemas change often.

To add a model later: copy `models/_template.md`, fill it in from the
provider's docs (ten minutes), add a row to the table above. Nothing else
changes.

## Provider routing

1. Both starter models (Nano Banana 2 Lite, Kling 3.0) run entirely on Kie
   AI through the same unified job API (`createTask` / `recordInfo`) — if
   only `KIE_API_KEY` is set, that's the whole route, no fallback needed
   for normal use.
2. Otherwise, default to the LOWEST COST provider that runs the model well
   (check Kie AI, fal.ai, WaveSpeed AI, and Google AI Studio in that order
   of setup simplicity — prefer whichever already has a key in `.env`).
3. If the cheapest route lacks the model, fails auth, or errors, fall back
   to the next provider that offers it.
4. Never hide a provider swap. Say which route ran and why before showing
   the result.

## API keys

Read keys from `.env` in the project root. Never paste a key into a prompt,
a script, or a chat message, and never write one into a log file.

| Provider | Key name in `.env` |
|---|---|
| Kie AI | `KIE_API_KEY` — required; covers both starter models |
| fal.ai | `FAL_KEY` — optional, fallback only |
| WaveSpeed AI | `WAVESPEED_API_KEY` — optional, fallback only |
| Google AI Studio | `GOOGLE_API_KEY` — optional, only if a recipe routes there directly |

If a key needed for the chosen route is missing, stop and ask for it rather
than trying another provider silently — that would violate the "never hide
a provider swap" rule above.

## Output

- Save every file FLAT into the generations folder: `generations/` (project
  root). No subfolders.
- Reference images (logos, faces, style shots) live in `generations/refs/`.
- Naming: `{project}_{description}_{timestamp}.{ext}`
- If `generations/` or `generations/refs/` don't exist yet, create them.

## Rules

- **Quote before video.** State the model, duration, resolution, and
  expected dollar cost, then wait for explicit go-ahead before any paid
  video run. Quoting is not approval — one approval covers exactly one run.
- **Draft cheap, finish pretty.** Iterate on the cheap image model first.
  Only rerun the same prompt on a quality/pro model once a favourite draft
  is picked.
- **Real refs, never described.** Never describe a logo or face in text —
  pass the real image file from `generations/refs/` as a reference. If the
  file isn't there, stop and ask for it instead of guessing.
- **One at a time.** Run multiple generations sequentially, not in
  parallel, to avoid rate limits.
- **Log every save.** After every save, write the sidecar log (see
  Logging below).

## Logging

After saving a generated file, write a small JSON sidecar next to it: same
basename, `.json` extension.

`hero_thumbnail_1774912000.jpg` → `hero_thumbnail_1774912000.json`

```json
{
  "model": "nano-banana-2-lite",
  "prompt": "the full text prompt that was sent to the API",
  "refs": ["refs/logo.png", "refs/headshot.jpg"],
  "params": { "aspect": "16:9", "size": "2K" },
  "created": "2026-08-20T09:41:00Z"
}
```

Same basename plus `.json` is the whole contract — it lets any future tool
(including the gallery page in `references/gallery-prompt.md`) or a plain
folder search recover exactly how any file in the library was made.

## Maintenance

Model ids change when providers ship new versions. If a call returns
"model not found," open that provider's model page, copy the id fresh, and
update the recipe file. That's the only upkeep this system needs.
