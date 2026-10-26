"""Assemble les images d'une planche-contact en mosaïques lisibles.

Usage : python mosaique.py <dossier> [colonnes] [par_feuille]
Produit <dossier>/../<nom>-feuilleN.png, chaque vignette annotée de son instant.
"""
import os
import sys

from PIL import Image, ImageDraw

dossier = sys.argv[1]
cols = int(sys.argv[2]) if len(sys.argv) > 2 else 3
par = int(sys.argv[3]) if len(sys.argv) > 3 else 9
W, H = 640, 360
images = sorted(f for f in os.listdir(dossier) if f.endswith(".png"))
for k in range(0, len(images), par):
    lot = images[k:k + par]
    rows = (len(lot) + cols - 1) // cols
    m = Image.new("RGB", (cols * W, rows * H), "black")
    d = ImageDraw.Draw(m)
    for i, f in enumerate(lot):
        im = Image.open(os.path.join(dossier, f)).convert("RGB").resize((W, H))
        x, y = (i % cols) * W, (i // cols) * H
        m.paste(im, (x, y))
        d.rectangle([x, y, x + 90, y + 22], fill="black")
        d.text((x + 4, y + 4), f.split("_", 1)[1].replace(".png", " s"), fill="yellow")
    sortie = f"{dossier}-feuille{k // par + 1}.png"
    m.save(sortie)
    print(sortie)
