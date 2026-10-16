import { createAudioPlayer } from 'expo-audio';

// Plays one sentence from an online voice (ElevenLabs, Speechify) with the app's audio player, in the same
// audio session as the music, so it reaches CarPlay and Bluetooth the same way. Only one plays at a time.
let current = null;
export function stop() {
  if (current) { try { current.remove(); } catch {} current = null; }
}
// Resolves true when the sentence finished, false when stop() cut it short. `rate` changes the pace
// without changing the pitch (used where the service itself has no speed setting).
export function play(file, rate, onStart) {
  stop();
  return new Promise((resolve) => {
    const player = createAudioPlayer({ uri: file.uri });
    current = player;
    let started = false;
    player.addListener('playbackStatusUpdate', (st) => {
      if (!started && st.playing) { started = true; onStart?.(); }
      if (st.didJustFinish) { if (current === player) stop(); resolve(true); }
    });
    // A stop() before the end removes the player; settle so nothing waits forever.
    const check = setInterval(() => { if (current !== player) { clearInterval(check); resolve(false); } }, 250);
    if (rate && Math.abs(rate - 1) > 0.01) { try { player.setPlaybackRate(Math.min(2, Math.max(0.5, rate)), 'high'); } catch {} }
    player.play();
  });
}
