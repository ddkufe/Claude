# EasyGrip Kitchen Co. — 4-clip ad sequence

Product: under-cabinet jar opener. Mounts once, grips every lid.
Audience: arthritis / weak grip, seniors, and the caregivers buying for them.

Model: `kling-3.0/video` (Kie AI) · duration `"5"` · `sound: true`
`aspect_ratio: "9:16"` (vertical) · `mode: "std"` (720p)

**Spend approved.** The store owner was quoted ~$4–$7 for all four clips at
5s / 9:16 / std and gave explicit go-ahead. Proceed without re-quoting; quote
again only if something changes (longer clips, `pro` mode, or reruns).

Run these ONE AT A TIME, in order. Save flat to `generations/` with the
sidecar `.json` log per SKILL.md.

---

## Clip 1 — Discovery on the shelf

Filename stem: `easygrip_clip1-shelf-discovery`

> Warm bright supermarket kitchen-gadget aisle. A woman in her early sixties
> with silver-streaked hair pushes a cart slowly, scanning shelves. She stops,
> spots a boxed under-cabinet jar opener at eye level, and her face lifts into
> genuine surprised delight. She picks up the box with both hands and turns it
> over, reading the front, eyebrows raised, a small smile breaking. Handheld
> documentary camera, slow push-in from medium to close on her face. Natural
> retail lighting, shallow depth of field, warm and hopeful tone, photorealistic.

## Clip 2 — Showcasing it at home

Filename stem: `easygrip_clip2-home-showcase`

> Sunlit modern kitchen, morning light through a window. The same
> silver-haired woman stands at the counter holding the small under-cabinet
> jar opener up in one hand, showing it to camera with quiet pride, then turns
> and holds it beneath the edge of an upper cabinet to test the placement.
> Clean white cabinets, wood countertop, a bowl of lemons nearby. Smooth slow
> camera arc around her, soft natural light, airy and optimistic,
> photorealistic lifestyle commercial look.

## Clip 3 — The one-handed open (the money shot)

Filename stem: `easygrip_clip3-the-open`

> Close-up in a bright kitchen. An older woman's hands raise a stubborn
> pickle jar up into a jar opener mounted under the cabinet above. The lid
> presses into the grip and locks. She turns the jar with her open palm, no
> squeezing, and the lid breaks free with a visible give. Her shoulders drop
> in relief. Tight macro on the hands and lid, then a quick cut wider to her
> face lighting up. Crisp natural light, shallow depth of field, tactile and
> satisfying, photorealistic.

## Clip 4 — Enjoying the result

Filename stem: `easygrip_clip4-enjoying`

> A silver-haired woman sits at a sunlit kitchen table, relaxed, eating from
> the jar she just opened — a simple lunch plated in front of her. She looks
> content and independent, glances up and smiles softly. Behind her, the jar
> opener is visible mounted under the cabinet. Warm golden natural light,
> gentle slow push-in, calm and heartfelt, photorealistic lifestyle
> commercial tone.

---

## Continuity note

Kling does not carry a character between separate jobs on its own. To keep
the same woman across all four, generate one still of her with Nano Banana 2
Lite first (~$0.04), save it to `generations/refs/`, upload for a public URL,
then pass that URL in `image_urls` on each of the four video jobs.
