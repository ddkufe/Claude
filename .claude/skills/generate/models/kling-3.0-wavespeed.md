# Kling 3.0 Pro (WaveSpeed AI)

Fallback route for Kling 3.0 when Kie AI is down or lacks capacity. General
video, good motion. Use only as a fallback — Kie AI is the default route
for Kling 3.0 (see models/kling-3.0.md); switch here only after confirming
Kie AI's `createTask` endpoint is actually failing, and say so before using
this route.

| Field | Value |
|---|---|
| Model ID | `kwaivgi/kling-v3.0-pro/text-to-video` |
| Provider | WaveSpeed AI |
| Method | Async (submit a job, then poll) |
| Type | Video |
| API key | `.env` → `WAVESPEED_API_KEY` |
| Docs | https://wavespeed.ai/docs/docs-api/kwaivgi/kwaivgi-kling-v3.0-pro-text-to-video |
| Cost | ~$0.112/sec without sound, ~$0.168/sec with sound (sound adds ~50%). Observed on the pricing page: 3s/no-sound $0.336, 5s/no-sound $0.56, 10s/no-sound $1.12, 15s/no-sound $1.68. Always quote before running (see SKILL.md rules). |

## Endpoint

```
POST https://api.wavespeed.ai/api/v3/kwaivgi/kling-v3.0-pro/text-to-video
Authorization: Bearer {WAVESPEED_API_KEY}
Content-Type: application/json
```

Status polling:

```
GET https://api.wavespeed.ai/api/v3/predictions/{id}/result
Authorization: Bearer {WAVESPEED_API_KEY}
```

Balance check (cheap sanity check before any run):

```
GET https://api.wavespeed.ai/api/v3/balance
Authorization: Bearer {WAVESPEED_API_KEY}
```

## Request format

Documented fields (from the provider's own model page, not verified
end-to-end yet by an actual successful run as of first use):

```json
{
  "prompt": "the full prompt text",
  "negative_prompt": "elements to exclude",
  "duration": 5,
  "aspect_ratio": "16:9",
  "cfg_scale": 0.5,
  "sound": false,
  "shot_type": "intelligent",
  "multi_prompt": []
}
```

- `duration` is an **integer** here (not a string like Kie AI's `"5"`),
  range 3–15 seconds.
- `sound: true` adds ~50% to cost — re-quote before enabling, same rule as
  the Kie AI recipe.
- `multi_prompt` is the multi-shot equivalent of Kie AI's `multi_prompt`
  array, but the exact per-item shape (whether it takes `{prompt,
  duration}` like Kie AI, or something else) is **not yet confirmed** —
  verify against the docs page above or with a tiny test shot before
  trusting the shape.
- **No `kling_elements` equivalent is documented.** WaveSpeed's Kling
  endpoints do not appear to expose a subject/product reference-lock
  feature the way Kie AI's wrapper does. If product-appearance consistency
  matters, the fallback approach is image-to-video (start-frame image) via
  a separate `kwaivgi/kling-v3.0-pro/image-to-video` endpoint, not
  `kling_elements` — this has not been tested this session.

## Response handling

1. `POST` the job → response is `{ "code": 200, "message": "success", "data": { "id": "...", "status": "..." } }` (exact shape not yet confirmed by a live call).
2. Poll `GET /predictions/{id}/result` every ~2 seconds, increasing the
   interval for longer jobs.
3. Status values: `completed`, `failed`, `cancelled`, `timeout`, `deleted`.
4. On `completed`, the video URL is in `data.outputs` (array).
5. Download immediately — result URLs likely expire, exact window not
   confirmed.
6. Save into `generations/`, then write the sidecar log.

## Notes

- This recipe was assembled from WaveSpeed's public docs pages during a
  Kie AI outage (Aug 2026) and has **not yet been verified against a real
  successful job** — run one small, cheap test first (short duration, no
  sound, no multi_prompt) before trusting the shape for a real build.
- Without `kling_elements`, the split-generation technique (separate
  no-product / product-locked jobs, concatenated) may not be enough on its
  own to keep the product visually consistent across shots — expect more
  manual verification of product appearance per shot than with the Kie AI
  route.

Sources: [Kling 3.0 Pro Text-to-Video - wavespeed.ai](https://wavespeed.ai/models/kwaivgi/kling-v3.0-pro/text-to-video), [API docs - wavespeed.ai](https://wavespeed.ai/docs/docs-api/kwaivgi/kwaivgi-kling-v3.0-pro-text-to-video), [Get Result - wavespeed.ai](https://wavespeed.ai/docs/get-result), [Balance API - wavespeed.ai](https://wavespeed.ai/docs/docs-common-api/balance)
