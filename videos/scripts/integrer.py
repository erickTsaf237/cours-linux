"""Remplace les « Vidéo en préparation » des modules par le vrai lecteur,
pour chaque vidéo déjà rendue (assets/video/<film>.mp4 et .jpg présents).

Usage : python integrer.py
"""
import glob
import os
import re

SITE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MOTIF = re.compile(r'<div class="video-attente" data-video="([\w-]+)">.*?</div>')


def lecteur(film):
    return (f'<video controls preload="none" playsinline poster="../assets/video/{film}.jpg">'
            f'<source src="../assets/video/{film}.mp4" type="video/mp4">'
            f'Ton navigateur ne lit pas la vidéo : <a href="../assets/video/{film}.mp4">télécharge-la ici</a>.</video>')


for page in sorted(glob.glob(os.path.join(SITE, "modules", "*.html"))):
    s = open(page, encoding="utf-8").read()
    faits = []

    def remplace(m):
        film = m.group(1)
        if all(os.path.exists(os.path.join(SITE, "assets", "video", f"{film}.{ext}")) for ext in ("mp4", "jpg")):
            faits.append(film)
            return lecteur(film)
        return m.group(0)

    neuf = MOTIF.sub(remplace, s)
    if faits:
        open(page, "w", encoding="utf-8").write(neuf)
        print(os.path.basename(page), "->", ", ".join(faits))
