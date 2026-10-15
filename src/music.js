import { createAudioPlayer } from 'expo-audio';
import { File, Paths } from 'expo-file-system';

// Plays the reader's mood music with the app's own audio player, in the same audio session as the narrator,
// so CarPlay and Bluetooth carry both at once. The reader renders each mood into a seamless loop the first
// time it's needed; the loops are kept on the phone so later sessions start instantly.
const VERSION = 1;
const FADE = 5;      // seconds to crossfade between moods
const STEP = 0.1;    // seconds between volume steps
const REF = 0.4;     // the loudness the loops were rendered at

export function createMusic({ requestRender, status }) {
  let level = 0.25, playing = false, mood = null, timer = null;
  const layers = {};       // mood -> { player, gain }
  const rendering = new Set();

  const fileFor = (m) => new File(Paths.cache, `undertone-music-${VERSION}-${m}.wav`);
  const out = () => Math.min(1, level / REF);

  function layer(m) {
    if (layers[m]) return layers[m];
    const f = fileFor(m);
    if (!f.exists) {
      if (!rendering.has(m)) { rendering.add(m); status?.(`preparing ${m} music`); requestRender(m); }
      return null;
    }
    const player = createAudioPlayer({ uri: f.uri });
    player.loop = true;
    player.volume = 0;
    return (layers[m] = { player, gain: 0, on: false });
  }

  function tick() {
    let busy = false;
    for (const [m, L] of Object.entries(layers)) {
      const target = playing && m === mood ? 1 : 0;
      if (L.gain !== target) {
        L.gain = target > L.gain ? Math.min(1, L.gain + STEP / FADE) : Math.max(0, L.gain - STEP / FADE);
        busy = true;
      }
      L.player.volume = L.gain * out();
      if (L.gain > 0 && playing && !L.on) { L.player.play(); L.on = true; }
      if (L.gain === 0 && L.on) { L.player.pause(); L.on = false; }
      if (L.gain === 0 && m !== mood) { L.player.remove(); delete layers[m]; }
    }
    if (!busy) { clearInterval(timer); timer = null; }
  }
  const run = () => { if (!timer) timer = setInterval(tick, STEP * 1000); tick(); };

  return {
    start(vol) { level = vol ?? level; playing = true; if (mood) layer(mood); run(); },
    pause() {
      playing = false;
      for (const L of Object.values(layers)) { L.gain = 0; if (L.on) { L.player.pause(); L.on = false; } }
      run();
    },
    volume(vol) { level = vol; for (const L of Object.values(layers)) L.player.volume = L.gain * out(); },
    mood(m) { mood = m || null; if (mood) layer(mood); run(); },
    // The reader finished rendering a mood: keep it, and fade it in if it's still the one wanted.
    data(m, base64) {
      rendering.delete(m);
      try {
        const f = fileFor(m);
        if (f.exists) f.delete();
        f.create();
        f.write(base64, { encoding: 'base64' });
      } catch (e) { status?.(`music: couldn't save ${m} (${e?.message || e})`); return; }
      if (m === mood) { layer(m); run(); status?.(`music ready (${m})`); }
    },
  };
}
