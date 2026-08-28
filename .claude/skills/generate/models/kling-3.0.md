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
- `kling_elements` (named subject references, e.g. `@element_dog` in the
  prompt tied to reference image URLs) is available for advanced
  character-consistency jobs — see the docs page if a request needs it.
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
