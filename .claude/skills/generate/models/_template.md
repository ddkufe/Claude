# Model Name

One line on what this model is best at and when to pick it.

| Field | Value |
|---|---|
| Model ID | the-exact-model-id |
| Provider | Kie AI / fal.ai / WaveSpeed AI / Google AI Studio |
| Method | Sync (instant reply) or Async (submit, then poll) |
| Type | Image or Video |
| API key | `.env` → KEY_NAME |
| Docs | link to the provider's page for this model |
| Cost | rough price per image / per second |

## Endpoint

```
POST https://...
```

## Request format

(the exact JSON body from the docs, with prompt, aspect ratio, resolution,
reference image fields)

## Response handling

(where the image/video lives in the reply: base64 field, or a URL to
download. For async: the status endpoint and the field that says "done".)

## Notes

(gotchas: rate limits, max sizes, content rules, upload quirks)

---

Reminder on authentication shape per provider (fill in the right one above):

- **Google AI Studio** — key goes in the URL:
  `POST .../models/{model-id}:generateContent?key={GOOGLE_API_KEY}`
- **fal.ai** — header, the word "Key":
  `POST https://fal.run/{model-id}` with `Authorization: Key {FAL_KEY}`
- **Kie AI** — header, the word "Bearer":
  `POST api.kie.ai/api/v1/jobs/createTask` with
  `Authorization: Bearer {KIE_API_KEY}`
- **WaveSpeed AI** — check their docs page for the exact header shape when
  wiring this provider in for the first time.

Async pattern (most video models):

1. `POST` the job → reply contains a task id.
2. Poll the status URL every 5–10 seconds, patiently.
3. Status says complete → reply now contains a file URL.
4. Download immediately — result URLs often expire in hours.
5. Save into `generations/`, then write the sidecar log.
