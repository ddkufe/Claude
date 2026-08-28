# Nano Banana 2 Lite

Everyday images. Cheap, fast, strong with reference images (logos, faces,
style shots). Default choice for drafts and most one-off image requests.

| Field | Value |
|---|---|
| Model ID | `nano-banana-2-lite` |
| Provider | Kie AI (also on fal.ai / Google AI Studio as fallbacks — see Notes) |
| Method | Async (submit a job, then poll — see below) |
| Type | Image |
| API key | `.env` → `KIE_API_KEY` |
| Docs | https://docs.kie.ai/market/google/nano-banana-2-lite |
| Cost | from ~$0.04 per image |

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
  "model": "nano-banana-2-lite",
  "callBackUrl": "https://your-domain.com/api/callback",
  "input": {
    "prompt": "the full prompt text",
    "aspect_ratio": "16:9",
    "image_urls": ["https://.../refs/logo.png"]
  }
}
```

- `callBackUrl` is optional — omit it and just poll `recordInfo` instead if
  there's no webhook receiver set up.
- `aspect_ratio` accepts values like `"1:1"`, `"16:9"`, or `"auto"` (default).
- `image_urls` is how a real logo or face gets passed in — per the skill's
  rules, never describe these in text; omit the field entirely for
  pure text-to-image. Local files in `generations/refs/` need a public URL
  first (Kie AI's file-upload endpoint, or any quick host, works).

## Response handling

1. `POST createTask` → response is `{ "code": 200, "data": { "taskId": "..." } }`.
2. Poll `GET recordInfo?taskId=...` every 5–10 seconds.
3. When `data.state` is `"success"`, `data.resultJson` is a JSON *string* —
   parse it; it contains `resultUrls`, an array of image URLs.
4. Download immediately — result URLs typically expire after 24 hours.
5. Save the file flat into `generations/`, then write the sidecar log.

`state` values seen in the wild: `waiting`, `queuing`, `generating`,
`success`, `fail`.

## Notes

- Same unified job pattern (`createTask` / `recordInfo`) is shared across
  every model Kie AI hosts, including Kling 3.0 — one auth header, one
  polling loop, works for both starter models.
- Fallback route via fal.ai: `POST https://fal.run/{model-id}` with
  `Authorization: Key {FAL_KEY}` — use only if Kie AI lacks capacity or
  errors; confirm the exact fal.ai model slug on its docs page first, since
  it may differ from the Kie AI id above.
- Fallback route via Google AI Studio direct: key goes in the URL
  (`?key={GOOGLE_API_KEY}`), not a header — needs a key not otherwise
  required by this skill's default (Kie-only) setup.
- Content policy: some prompts (real people, certain brand marks) may be
  rejected — if so, fall back per the skill's provider-routing rule rather
  than retrying the same call blindly.

Sources: [Google - Nano Banana 2 Lite - docs.kie.ai](https://docs.kie.ai/market/google/nano-banana-2-lite), [Get Task Details - docs.kie.ai](https://docs.kie.ai/market/common/get-task-detail)
