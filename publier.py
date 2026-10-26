"""Fabrique le dossier publication/ : le site seul, prêt à mettre en ligne, avec le référencement.

Usage :
    python publier.py https://linux.tneric.com [--goatcounter moncode] [--deployer]

--deployer met aussitôt le site en ligne sur Cloudflare (Worker « cours-linux », config deploiement/wrangler.toml).
Il lit deux fichiers privés, jamais copiés dans le projet ni affichés :
  %USERPROFILE%\.cloudflare_api_token   jeton API (permission « Compte · Workers Scripts : Modifier »)
  %USERPROFILE%\.cloudflare_account_id  identifiant du compte Cloudflare

Le dossier publication/ contient uniquement index.html, modules/ et assets/ (jamais CLAUDE.md,
PASSATION.md ni videos/), plus ce qui dépend de l'adresse finale du site :
  - balises canonical, Open Graph et Twitter Card (aperçus de partage) sur chaque page ;
  - données structurées JSON-LD : le cours, chaque module, chaque vidéo (VideoObject), fil d'Ariane ;
  - sitemap.xml, robots.txt, 404.html, _headers (cache et sécurité pour Netlify / Cloudflare Pages) ;
  - en option, la mesure d'audience GoatCounter (gratuite, sans cookie).
À relancer après chaque nouveau module ou nouvelle vidéo (avec --deployer, ou en glissant publication/ chez l'hébergeur).
"""
import argparse
import datetime as dt
import html
import json
import os
import re
import shutil
import subprocess

import imageio_ffmpeg

RACINE = os.path.dirname(os.path.abspath(__file__))
SORTIE = os.path.join(RACINE, "publication")
NOM_SITE = "Carnet Linux"
PROJET_CLOUDFLARE = "cours-linux"
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()


def texte(fragment):
    """Texte brut d'un fragment HTML."""
    return html.unescape(re.sub(r"<[^>]+>", "", fragment)).strip()


def duree_iso(chemin):
    sortie = subprocess.run([FFMPEG, "-hide_banner", "-i", chemin], capture_output=True, text=True).stderr
    m = re.search(r"Duration: (\d+):(\d+):(\d+)\.(\d+)", sortie)
    if not m:
        return None
    h, mi, s = int(m.group(1)), int(m.group(2)), int(m.group(3))
    return f"PT{h * 60 + mi}M{s}S"


def date_iso(chemin):
    return dt.datetime.fromtimestamp(os.path.getmtime(chemin), dt.timezone.utc).replace(microsecond=0).isoformat()


def videos_de(page_html, base):
    """Les vidéos rendues d'une page : (film, titre, description)."""
    res = []
    for bloc in re.findall(r'<figure class="video-card">(.*?)</figure>', page_html, re.S):
        m = re.search(r"assets/video/([\w-]+)\.mp4", bloc)
        if not m:
            continue                                   # vidéo pas encore rendue
        film = m.group(1)
        titre = texte(re.search(r"<strong>(.*?)</strong>", bloc, re.S).group(1))
        sous = texte(re.search(r"</strong><span>(.*?)</span>", bloc, re.S).group(1))
        mp4 = os.path.join(RACINE, "assets", "video", f"{film}.mp4")
        res.append({
            "@type": "VideoObject",
            "name": titre,
            "description": f"{titre} : {sous}. Vidéo de 90 secondes du cours {NOM_SITE}.",
            "thumbnailUrl": [f"{base}/assets/video/{film}.jpg"],
            "uploadDate": date_iso(mp4),
            "duration": duree_iso(mp4),
            "contentUrl": f"{base}/assets/video/{film}.mp4",
            "inLanguage": "fr",
        })
    return res


def balises(page, url, base, analytics):
    s = page["html"]
    titre = texte(re.search(r"<title>(.*?)</title>", s, re.S).group(1))
    desc = html.unescape(re.search(r'<meta name="description" content="(.*?)">', s).group(1))
    vids = videos_de(s, base)
    image = vids[0]["thumbnailUrl"][0] if vids else f"{base}/assets/img/og-image.png"
    larg, haut = (1920, 1080) if vids else (1200, 630)
    e = lambda v: html.escape(v, quote=True)
    lignes = [
        f'<link rel="canonical" href="{e(url)}">',
        # Auteur et dates : sans eux, l'inspecteur LinkedIn affiche « No author / publish date found ».
        f'<meta name="author" content="{NOM_SITE}">',
        f'<meta property="article:author" content="{NOM_SITE}">',
        f'<meta property="article:published_time" content="{page["modif"]}">',
        f'<meta property="article:modified_time" content="{page["modif"]}">',
        f'<meta property="og:site_name" content="{NOM_SITE}">',
        '<meta property="og:locale" content="fr_FR">',
        f'<meta property="og:type" content="{"website" if page["accueil"] else "article"}">',
        f'<meta property="og:title" content="{e(titre)}">',
        f'<meta property="og:description" content="{e(desc)}">',
        f'<meta property="og:url" content="{e(url)}">',
        f'<meta property="og:image" content="{e(image)}">',
        f'<meta property="og:image:width" content="{larg}">',
        f'<meta property="og:image:height" content="{haut}">',
        '<meta name="twitter:card" content="summary_large_image">',
        f'<meta name="twitter:title" content="{e(titre)}">',
        f'<meta name="twitter:description" content="{e(desc)}">',
        f'<meta name="twitter:image" content="{e(image)}">',
    ]
    cours = {
        "@type": "Course", "@id": f"{base}/#cours", "name": f"Cours Linux — {NOM_SITE}",
        "description": "Cours Linux complet et gratuit, en français : de l'installation d'Ubuntu à l'administration système.",
        "url": f"{base}/", "inLanguage": "fr", "isAccessibleForFree": True,
        "provider": {"@type": "Organization", "name": NOM_SITE, "url": f"{base}/"},
    }
    if page["accueil"]:
        graphe = [{"@type": "WebSite", "name": NOM_SITE, "url": f"{base}/", "inLanguage": "fr"}, cours]
    else:
        h1 = texte(re.search(r"<h1>(.*?)</h1>", s, re.S).group(1))
        ressource = {
            "@type": "LearningResource", "name": h1, "headline": titre, "description": desc, "url": url,
            "inLanguage": "fr", "isAccessibleForFree": True, "learningResourceType": "Cours",
            "isPartOf": {"@id": f"{base}/#cours"}, "dateModified": page["modif"],
        }
        if vids:
            ressource["video"] = vids
        graphe = [cours, ressource, {
            "@type": "BreadcrumbList", "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": NOM_SITE, "item": f"{base}/"},
                {"@type": "ListItem", "position": 2, "name": h1, "item": url}]}]
    lignes.append('<script type="application/ld+json">' +
                  json.dumps({"@context": "https://schema.org", "@graph": graphe}, ensure_ascii=False) + "</script>")
    if analytics:
        lignes.append(f'<script data-goatcounter="https://{analytics}.goatcounter.com/count" async src="//gc.zgo.at/count.js"></script>')
    return "  " + "\n  ".join(lignes) + "\n"


def page_404(base):
    return f"""<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Page introuvable | {NOM_SITE}</title>
  <meta name="robots" content="noindex">
  <link rel="icon" href="{base}/assets/img/tux.svg">
  <link rel="stylesheet" href="{base}/assets/css/style.css">
</head>
<body>
<section class="hero"><div class="hero-inner" style="grid-template-columns:1fr;text-align:center">
  <div><span class="eyebrow">erreur 404</span>
  <h1><span class="grad">cd</span> : aucun fichier ou dossier de ce nom</h1>
  <p class="lead" style="margin:0 auto">Cette page n'existe pas (ou plus). Pas de panique : <code>cd ~</code> te ramène à l'accueil.</p>
  <p style="margin-top:2rem"><a class="done-btn" href="{base}/">🏠 Retour au programme du cours</a></p></div>
</div></section>
</body>
</html>
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("adresse", help="adresse finale du site, ex. https://cours-linux.netlify.app")
    ap.add_argument("--goatcounter", help="code GoatCounter pour mesurer l'audience (optionnel)")
    ap.add_argument("--deployer", action="store_true", help="mettre en ligne sur Cloudflare Pages après la fabrication")
    a = ap.parse_args()
    base = a.adresse.rstrip("/")

    shutil.rmtree(SORTIE, ignore_errors=True)
    os.makedirs(SORTIE)
    shutil.copy2(os.path.join(RACINE, "index.html"), SORTIE)
    shutil.copytree(os.path.join(RACINE, "modules"), os.path.join(SORTIE, "modules"))
    shutil.copytree(os.path.join(RACINE, "assets"), os.path.join(SORTIE, "assets"))

    pages = [("index.html", f"{base}/")] + [
        (f"modules/{f}", f"{base}/modules/{f}") for f in sorted(os.listdir(os.path.join(SORTIE, "modules"))) if f.endswith(".html")]
    plan = []
    for rel, url in pages:
        chemin = os.path.join(SORTIE, rel)
        s = open(chemin, encoding="utf-8").read()
        modif = dt.date.fromtimestamp(os.path.getmtime(os.path.join(RACINE, rel))).isoformat()
        bloc = balises({"html": s, "accueil": rel == "index.html", "modif": modif}, url, base, a.goatcounter)
        s = s.replace("</head>", bloc + "</head>", 1)
        open(chemin, "w", encoding="utf-8").write(s)
        plan.append((url, modif, len(videos_de(s, base))))

    with open(os.path.join(SORTIE, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
        for url, modif, _ in plan:
            f.write(f"  <url><loc>{url}</loc><lastmod>{modif}</lastmod></url>\n")
        f.write("</urlset>\n")
    with open(os.path.join(SORTIE, "robots.txt"), "w", encoding="utf-8") as f:
        f.write(f"User-agent: *\nAllow: /\n\nSitemap: {base}/sitemap.xml\n")
    with open(os.path.join(SORTIE, "404.html"), "w", encoding="utf-8") as f:
        f.write(page_404(base))
    with open(os.path.join(SORTIE, "_headers"), "w", encoding="utf-8") as f:
        f.write("/*\n  X-Content-Type-Options: nosniff\n  Referrer-Policy: strict-origin-when-cross-origin\n\n"
                "/assets/*\n  Cache-Control: public, max-age=604800\n\n"
                "/assets/video/*\n  Cache-Control: public, max-age=2592000\n")

    taille = sum(os.path.getsize(os.path.join(d, x)) for d, _, fs in os.walk(SORTIE) for x in fs)
    print(f"publication/ prêt ({taille / 1e6:.0f} Mo) pour {base}")
    for url, modif, nv in plan:
        print(f"  {url}  ({nv} vidéo{'s' if nv > 1 else ''})")
    if a.deployer:
        deployer()


def deployer():
    """Envoie publication/ sur Cloudflare : le site est un Worker à fichiers statiques (deploiement/wrangler.toml)."""
    def secret(nom):
        chemin = os.path.expanduser(f"~/.{nom}")
        if not os.path.exists(chemin):
            raise SystemExit(f"Fichier manquant : {chemin} (voir l'aide en tête de publier.py)")
        return open(chemin, encoding="utf-8-sig").read().strip()

    env = dict(os.environ, CLOUDFLARE_API_TOKEN=secret("cloudflare_api_token"),
               CLOUDFLARE_ACCOUNT_ID=secret("cloudflare_account_id"))
    npx = shutil.which("npx") or shutil.which("npx.cmd")
    if not npx:
        raise SystemExit("npx introuvable : installe Node.js (https://nodejs.org).")
    print(f"Déploiement sur Cloudflare (Worker {PROJET_CLOUDFLARE})…")
    config = os.path.join(RACINE, "deploiement", "wrangler.toml")
    r = subprocess.run([npx, "--yes", "wrangler", "deploy", "--config", config], env=env, cwd=os.path.dirname(config))
    if r.returncode != 0:
        raise SystemExit("Échec du déploiement (voir les messages de Wrangler ci-dessus).")
    print("Site en ligne : https://linux.tneric.com")


if __name__ == "__main__":
    main()
