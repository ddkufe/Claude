# Bytedance Seedance 2.5

Video with strong realism, especially for human motion/actors. Supports
first/last-frame anchoring AND up to 30 reference images for subject/product
consistency (more flexible than Kling's kling_elements). Try this when Kling
output reads as obviously AI (faces, hands, actor interaction) and Veo 3 is
unavailable.

| Field | Value |
|---|---|
| Model ID | `bytedance/seedance-2-5` |
| Provider | Kie AI |
| Method | Async (submit a job, then poll) |
| Type | Video |
| API key | `.env` → `KIE_API_KEY` |
| Docs | https://docs.kie.ai/market/bytedance/seedance-2-5 |
| Cost | Not published on the model's doc page as of first use — check `common-api/get-account-credits` balance before/after a small test to discover actual cost, per SKILL.md's quote-before-video rule. |

## Endpoint

```
POST https://api.kie.ai/api/v1/jobs/createTask
Authorization: Bearer {KIE_API_KEY}
Content-Type: application/json
```

Status polling (same unified pattern as Kling/Nano Banana):

```
GET https://api.kie.ai/api/v1/jobs/recordInfo?taskId={taskId}
Authorization: Bearer {KIE_API_KEY}
```

## Request format

Verified against Kie AI's live docs (not yet verified end-to-end by an
actual successful run as of first use):

```json
{
  "model": "bytedance/seedance-2-5",
  "input": {
    "prompt": "the full prompt text (max 30,000 chars)",
    "first_frame_url": "https://.../start.jpg",
    "last_frame_url": "https://.../end.jpg",
    "reference_image_urls": ["https://.../ref1.jpg"],
    "resolution": "1080p",
    "aspect_ratio": "9:16",
    "duration": 5,
    "output_format": "mp4",
    "generate_audio": false,
    "nsfw_checker": false
  }
}
```

- `last_frame_url` requires `first_frame_url` to also be set.
- `reference_image_urls` supports up to 30 images combined with frame
  fields — use this for locking a product/subject's appearance, more
  generous than Kling's 2-4 image `kling_elements` limit.
- `reference_video_urls` / `reference_audio_urls` also exist (max 10 each,
  ≤30s total) — not needed for a typical hook-shot job.
- `resolution`: `480p`, `720p`, or `1080p` (default `720p`).
- `aspect_ratio`: `1:1`, `4:3`, `3:4`, `16:9`, `9:16`, `21:9`, `adaptive`.
- `duration`: 4-30 seconds, or `-1` for automatic (default 5).
- `generate_audio` defaults to **true** — set `false` explicitly to keep
  cost down and match a silent-hero-clip style, and re-quote if enabling it
  (same rule as every other video model in this skill).

## Response handling

Same as Kling 3.0 / Nano Banana 2 Lite:

1. `POST createTask` → `{ "code": 200, "data": { "taskId": "..." } }`.
2. Poll `recordInfo?taskId=...` every 5-10s.
3. `state: "success"` → `data.resultJson` is a JSON string; parse it for
   `resultUrls`.
4. Download immediately — result URLs typically expire.
5. Save into `generations/`, write the sidecar log.

## Notes

- Pricing was not visible on the model's own doc page — before committing
  to a real render, run the smallest/cheapest test (short duration, 720p,
  no audio) and diff the account balance
  (`GET https://api.kie.ai/api/v1/chat/credit`) before/after to discover
  the actual per-job cost, then quote the real run from that number.
- If Kie AI lacks capacity or rejects the job, no fallback provider for
  this model has been verified yet — check fal.ai/WaveSpeed docs fresh
  before assuming they host it.

Sources: [Bytedance Seedance 2.5 - docs.kie.ai](https://docs.kie.ai/market/bytedance/seedance-2-5)
