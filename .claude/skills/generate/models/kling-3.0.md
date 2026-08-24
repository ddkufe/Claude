# Kling 3.0

General video. The sensible default: good motion, fair price. Use this
before reaching for a pricier/slower model like Veo.

| Field | Value |
|---|---|
| Model ID | `kling-3.0/video` |
| Provider | Kie AI |
| Method | Async (submit a job, then poll) |
| Type | Video |
| API key | `.env` → `KIE_API_KEY` |
| Docs | https://docs.kie.ai/market/kling/kling-3-0 |
| Cost | ~$0.20–$0.35 per second. `std` = 720p, `pro` = 1080p. 3–15 second clips. A 10s clip is roughly $2–$3.50 — always quote this and get explicit go-ahead first (see SKILL.md rules). |

## Endpoint

```
POST https://api.kie.ai/api/v1/jobs/createTask
Authorization: Bearer {KIE_API_KEY}
Content-Type: application/json
```

Status polling:

```
GET https://api.kie.ai/api/v1/jobs/recordInfo?taskId={taskId}
Authorization: Bearer {KIE_API_KEY}
```

## Request format

Verified against Kie AI's live docs:

```json
{
  "model": "kling-3.0/video",
  "callBackUrl": "https://your-domain.com/api/callback",
  "input": {
    "prompt": "the full prompt text",
    "image_urls": ["https://.../refs/style-frame.jpg"],
    "sound": true,
    "duration": "5",
    "aspect_ratio": "16:9",
    "mode": "std",
    "multi_shots": false
  }
}
```

- `callBackUrl` is optional — omit it and poll `recordInfo` instead if
  there's no webhook receiver set up.
- `image_urls` is optional — include it for image-to-video / start-frame
  jobs (array, even for one image); omit entirely for pure text-to-video.
- `duration` is a string, e.g. `"5"`; `mode` is `"std"` (720p) or `"pro"`
  (1080p) per the cost table above.
- `sound: true` on a single-shot job costs noticeably more than `sound:
  false` — observed 81 credits vs. 54 credits for the same 3s/pro/9:16
  request (a ~50% premium), not documented on Kie AI's pricing page.
  Re-quote before enabling sound rather than assuming it's free relative to
  a silent quote already given.
- Multi-shot: set `multi_shots: true` and pass `multi_prompt`, an array of
  `{prompt, duration}`. Each shot prompt is capped at **500 characters** —
  longer prompts are rejected outright, so validate before submitting.
  Observed: per-shot `duration` values are effectively normalised to ~2s
  each, and the clip runs ~2s x number of shots regardless of the top-level
  `duration` (4 shots -> 8.04s, 3 shots -> 6.04s, both with `duration: "8"`).
  Budget shots, not seconds. Note also that `sound` DEFAULTS TO ON in
  multi-shot mode — set `sound: false` explicitly for silent output.
- `kling_elements` (named subject references) locks the appearance of a
  specific subject — use it whenever the product/character must match real
  reference photos, especially when the start frame does not show the
  subject. Verified shape:

  ```json
  "kling_elements": [
    { "name": "element_opener",
      "description": "short descriptor",
      "element_input_urls": ["https://...a.jpg", "https://...b.jpg"] }
  ]
  ```

  Reference it in the prompt as `@element_opener` (the array `name` omits
  the `@`). 2–4 image URLs per element, max 10MB each, max 3 elements per
  task, and each `@element` costs 37 characters of prompt budget.
- Local reference images need a public URL first (Kie AI's file-upload
  endpoint works for this).

## Response handling

1. `POST createTask` → response is `{ "code": 200, "data": { "taskId": "..." } }`.
2. Poll `GET recordInfo?taskId=...` every 5–10 seconds, patiently — video
   jobs take longer than image jobs.
3. When `data.state` is `"success"`, `data.resultJson` is a JSON *string* —
   parse it; it contains `resultUrls`, an array with the video URL.
4. Download immediately — result URLs typically expire after 24 hours.
5. Save the file flat into `generations/`, then write the sidecar log.

`state` values seen in the wild: `waiting`, `queuing`, `generating`,
`success`, `fail`.

## Notes

- Getting sync/async backwards is the single most common reason a first
  attempt on a video model appears to "hang" — Kling is always async, never
  expect an instant reply.
- Same unified job pattern (`createTask` / `recordInfo`) is shared with
  Nano Banana 2 Lite and every other model Kie AI hosts — one auth header,
  one polling loop, works for both starter models.
- If Kie AI rejects the job or lacks capacity, fall back to WaveSpeed AI or
  fal.ai per the skill's provider-routing rule, and say so before retrying.
- Always restate the quote (model, duration, resolution, ~$ cost) and get
  explicit approval before running — this is a hard rule in SKILL.md, not
  optional here just because it's the "default" model.

Sources: [Kling 3.0 - docs.kie.ai](https://docs.kie.ai/market/kling/kling-3-0), [Get Task Details - docs.kie.ai](https://docs.kie.ai/market/common/get-task-detail)
