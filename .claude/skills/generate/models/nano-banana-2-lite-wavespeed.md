# Nano Banana 2 Lite (WaveSpeed AI)

Same model as `nano-banana-2-lite.md` (Kie AI), routed through WaveSpeed AI
instead. Use this when Kie AI's image-generation credits are unavailable but
WaveSpeed has balance — confirmed working (Kie AI returned 402 insufficient
credits on nano-banana-2-lite mid-session, Sept 2026, while WaveSpeed still
had balance).

| Field | Value |
|---|---|
| Model ID | `google/nano-banana-2-lite/edit` (image-editing/reference variant) |
| Provider | WaveSpeed AI |
| Method | Async (submit a job, then poll) |
| Type | Image |
| API key | `.env` → `WAVESPEED_API_KEY` |
| Docs | https://wavespeed.ai/docs/docs-api/google/google-nano-banana-2-lite-edit |
| Cost | $0.04 per output image (same as the Kie AI route). |

## Endpoint

```
POST https://api.wavespeed.ai/api/v3/google/nano-banana-2-lite/edit
Authorization: Bearer {WAVESPEED_API_KEY}
Content-Type: application/json
```

Status polling (same pattern as every other WaveSpeed model):

```
GET https://api.wavespeed.ai/api/v3/predictions/{id}/result
Authorization: Bearer {WAVESPEED_API_KEY}
```

## Request format

```json
{
  "images": ["https://.../ref1.jpg", "https://.../ref2.jpg"],
  "prompt": "the full prompt text",
  "output_format": "jpeg"
}
```

- `images` (required): array of reference image URLs — this is the
  edit/reference variant, so at least one image is expected (unlike Kie
  AI's `nano-banana-2-lite` where `image_urls` is optional for pure
  text-to-image). For text-to-image with no references, use
  `google/nano-banana-2-lite/text-to-image` instead (not yet used this
  session — verify its request shape fresh before trusting it).
- `output_format`: `png` (default) or `jpeg`.
- `enable_sync_mode` (default false): set true to wait for completion
  synchronously instead of polling, if a short timeout is acceptable.
- `enable_base64_output` (default false): return base64 instead of a URL.
- No `aspect_ratio` control was exercised this session — the output
  followed the input reference image's aspect ratio in practice.

## Response handling

1. `POST` the job → response has `data.id`.
2. Poll `GET /predictions/{id}/result` every ~5s (image jobs are fast,
   typically done in 1-3 polls).
3. `status: "completed"` → `data.outputs` is an array with the image URL.
4. Download immediately.
5. Save into `generations/`, write the sidecar log.

## Notes

- Same underlying model as Kie AI's `nano-banana-2-lite` — prefer the Kie
  AI route (`nano-banana-2-lite.md`) when its credits are available, since
  that's the skill's documented default; use this only as the funded
  fallback.

Sources: [Nano Banana 2 Lite Edit - wavespeed.ai](https://wavespeed.ai/models/google/nano-banana-2-lite/edit), [API docs - wavespeed.ai](https://wavespeed.ai/docs/docs-api/google/google-nano-banana-2-lite-edit)
