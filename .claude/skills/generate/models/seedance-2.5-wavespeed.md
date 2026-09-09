# Bytedance Seedance 2.5 (WaveSpeed AI)

Video with strong realism, especially human motion/actors. Use this route
when Kie AI's Seedance/Veo video credits are unavailable but WaveSpeed has
balance — confirmed working (WaveSpeed balance check succeeded when Kie AI's
media-generation credits were exhausted at every tier, Sept 2026).

| Field | Value |
|---|---|
| Model ID | `bytedance/seedance-2.5` (image-to-video variant) |
| Provider | WaveSpeed AI |
| Method | Async (submit a job, then poll) |
| Type | Video |
| API key | `.env` → `WAVESPEED_API_KEY` |
| Docs | https://wavespeed.ai/docs/docs-api/bytedance/bytedance-seedance-2.5-image-to-video |
| Cost | $0.36/sec at 720p, $0.90/sec at 1080p (audio included by default, disable via `generate_audio: false`). Observed: 5s/720p = $1.80, 8s/720p = $2.88, 5s/1080p = $4.50, 8s/1080p = $7.20. Always quote before running. |

## Endpoint

```
POST https://api.wavespeed.ai/api/v3/bytedance/seedance-2.5/image-to-video
Authorization: Bearer {WAVESPEED_API_KEY}
Content-Type: application/json
```

Status polling (same as Kling on WaveSpeed):

```
GET https://api.wavespeed.ai/api/v3/predictions/{id}/result
Authorization: Bearer {WAVESPEED_API_KEY}
```

Balance check:

```
GET https://api.wavespeed.ai/api/v3/balance
Authorization: Bearer {WAVESPEED_API_KEY}
```

## Request format

```json
{
  "prompt": "the full prompt text",
  "image": "https://.../start-frame.jpg",
  "last_image": "https://.../end-frame.jpg",
  "resolution": "720p",
  "duration": 5,
  "generate_audio": false
}
```

- `image` (start frame) is required; `last_image` (end frame) is optional
  but gives the same two-frame anchoring technique used for Kling on
  WaveSpeed — very effective for locking a product's exact appearance in
  the final frame when the model has no dedicated reference-image/element
  feature.
- **Aspect ratio follows the `image` (start frame) automatically** — there
  is no explicit `aspect_ratio` field. If `last_image` has a different
  aspect ratio than `image`, pad or crop it to match first (e.g. with
  ffmpeg, blur-fill the letterbox rather than hard-cropping the subject) —
  mismatched frames risk unexpected cropping/distortion.
- `resolution`: `480p`, `720p` (default), `1080p`, or `4k`.
- `duration`: 4-30 seconds (default 5).
- `generate_audio` defaults to **true** — set `false` explicitly to match
  a silent-hero-clip style and to avoid the audio cost premium; re-quote if
  enabling it.

## Response handling

Same pattern as Kling on WaveSpeed:

1. `POST` the job → response has `data.id`.
2. Poll `GET /predictions/{id}/result` every ~8s.
3. `status: "completed"` → `data.outputs` is an array of video URLs.
4. Download immediately.
5. Save into `generations/`, write the sidecar log.

## Notes

- No `kling_elements`-equivalent reference-image-array feature confirmed
  for this WaveSpeed endpoint — stick to the two-frame (`image`/
  `last_image`) technique for subject/product locking, same as the Kling
  WaveSpeed route.
- Kie AI also hosts `bytedance/seedance-2-5` (see `seedance-2.5.md`) with a
  richer feature set (up to 30 reference images, first+last frame together,
  more resolution/duration options) — prefer that route when Kie AI credits
  are available, since it's more flexible than this WaveSpeed variant.

Sources: [Seedance 2.5 Image-to-Video - wavespeed.ai](https://wavespeed.ai/models/bytedance/seedance-2.5/image-to-video), [API docs - wavespeed.ai](https://wavespeed.ai/docs/docs-api/bytedance/bytedance-seedance-2.5-image-to-video)
