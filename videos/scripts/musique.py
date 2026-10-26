"""Fond musical avec Lyria RealTime (flux PCM 48 kHz stéréo 16 bits).

Usage : python musique.py <style> [secondes] [nom]   → ../musique/fond-<nom ou style>.wav
Enregistrement en temps réel : 92 s de musique prennent 92 s.
Structure : intro douce, groove sous la voix, petite montée finale.
"""
import asyncio
import os
import sys
import wave

from google import genai
from google.genai import types

CLE = open(os.path.expanduser("~/.gemini_api_key"), encoding="utf-8-sig").read().strip()
RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAUX, CANAUX = 48000, 2

STYLES = {
    "synthwave": {
        "bpm": 100,
        "base": "Retro synthwave, warm analog synths, bright arpeggios, steady drum machine, nostalgic 1980s computer lab vibe, curious tech documentary, instrumental",
        "intro": "soft analog pad and a slow blinking arpeggio, mysterious and curious",
        "final": "uplifting bright lift, triumphant synth lead",
    },
    "lofi": {
        "bpm": 86,
        "base": "Chill lo-fi hip hop, mellow electric piano, soft vinyl crackle, laid-back boom bap drums, warm round bass, studious and focused, instrumental",
        "intro": "lone electric piano chords with vinyl crackle, calm",
        "final": "warm satisfying ending, a bit brighter",
    },
    "electro": {
        "bpm": 112,
        "base": "Bright upbeat electro-pop, plucky synths, airy pads, soft punchy kick, claps, curious and optimistic tech documentary, instrumental",
        "intro": "soft airy pads and a single curious synth pluck, gentle build",
        "final": "uplifting euphoric lift, energetic",
    },
}


async def enregistrer(style: str, secondes: float) -> bytes:
    s = STYLES[style]
    client = genai.Client(api_key=CLE, http_options={"api_version": "v1alpha"})
    tampon = bytearray()
    cible = int(secondes * TAUX * CANAUX * 2)

    async with client.aio.live.music.connect(model="models/lyria-realtime-exp") as session:
        async def phase(prompts):
            await session.set_weighted_prompts(prompts=[types.WeightedPrompt(text=t, weight=w) for t, w in prompts])

        async def config(densite, eclat):
            await session.set_music_generation_config(
                config=types.LiveMusicGenerationConfig(bpm=s["bpm"], temperature=1.0, density=densite, brightness=eclat))

        await phase([(s["base"], 1.0), (s["intro"], 1.5)])
        await config(0.3, 0.65)
        await session.play()

        faites = set()
        async for msg in session.receive():
            if msg.server_content and msg.server_content.audio_chunks:
                for ch in msg.server_content.audio_chunks:
                    tampon.extend(ch.data)
            t = len(tampon) / (TAUX * CANAUX * 2)
            # Consignes envoyées ~1,2 s en avance (latence de Lyria).
            if t > 5 and "groove" not in faites:
                faites.add("groove")
                await phase([(s["base"], 1.0)])
                await config(0.55, 0.72)
            if t > secondes - 16 and "final" not in faites:
                faites.add("final")
                await phase([(s["base"], 1.0), (s["final"], 1.2)])
                await config(0.65, 0.8)
            if len(tampon) >= cible:
                break
        await session.stop()
    return bytes(tampon[:cible])


if __name__ == "__main__":
    style = sys.argv[1]
    secondes = float(sys.argv[2]) if len(sys.argv) > 2 else 94
    pcm = asyncio.run(enregistrer(style, secondes))
    nom = sys.argv[3] if len(sys.argv) > 3 else style   # ex. synthwave2 : une autre prise du même style
    sortie = f"{RACINE}/musique/fond-{nom}.wav"
    with wave.open(sortie, "wb") as w:
        w.setnchannels(CANAUX)
        w.setsampwidth(2)
        w.setframerate(TAUX)
        w.writeframes(pcm)
    print(f"{sortie}: {len(pcm) / (TAUX * CANAUX * 2):.1f} s")
