"""Mixe une voix off avec un ou plusieurs fonds musicaux.

Usage : python mixer.py <film> <voix> <style> [<style>…]   → ../mixes/<film>-<voix>-<style>.m4a
La musique s'efface sous la voix (compression en sidechain) et revient entre
les phrases et sur la carte de fin ; le tout est normalisé à -14 LUFS.
La durée est la même que celle de l'animation (commun.js) : voix + 1,5 s avant + 3,5 s après.
"""
import json
import os
import subprocess
import sys

import imageio_ffmpeg

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEBUT_VOIX = 1.5
APRES_VOIX = 3.5

film, voix, styles = sys.argv[1], sys.argv[2], sys.argv[3:]
fin = json.load(open(f"{RACINE}/reperes/{film}-{voix}.json", encoding="utf-8"))["fin"]
DUREE = round(fin + DEBUT_VOIX + APRES_VOIX, 1)
ms = int(DEBUT_VOIX * 1000)

filtre = (
    f"[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay={ms}|{ms},asplit=2[v][sc0];"
    # Voix prolongée de silence : sinon le compresseur, donc la musique, s'arrêterait avec elle.
    f"[sc0]apad=whole_dur={DUREE + 2}[sc];"
    "[0:a]volume=0.5[m];"
    "[m][sc]sidechaincompress=threshold=0.02:ratio=6:attack=15:release=450[md];"
    "[md][v]amix=inputs=2:duration=first:normalize=0,"
    f"afade=t=in:d=0.4,afade=t=out:st={DUREE - 2.2}:d=2.2,atrim=0:{DUREE},"
    "loudnorm=I=-14:TP=-1.5:LRA=11[out]"
)

os.makedirs(f"{RACINE}/mixes", exist_ok=True)
for style in styles:
    sortie = f"{RACINE}/mixes/{film}-{voix}-{style}.m4a"
    subprocess.run([
        FFMPEG, "-y", "-loglevel", "error",
        "-i", f"{RACINE}/musique/fond-{style}.wav", "-i", f"{RACINE}/voix/{film}-{voix}.wav",
        "-filter_complex", filtre, "-map", "[out]", "-ar", "48000", "-c:a", "aac", "-b:a", "192k", sortie,
    ], check=True)
    print(f"{sortie} ({DUREE} s)")
