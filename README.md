# Carnet Linux — cours Linux en français

**Site : [linux.tneric.com](https://linux.tneric.com)**

Un cours Linux complet et gratuit, en français : de l'installation d'Ubuntu dans une machine virtuelle jusqu'à
l'administration système. Chaque module combine théorie, schémas, une ou deux vidéos animées de 90 secondes,
un quiz et une mission pratique dont chaque étape affiche sa correction.

## Programme

| Phase | Modules | État |
|---|---|---|
| 1 · Fondations | 00 Linux et son installation · 01 Le bureau et le terminal · 02 Le système de fichiers · 03 Lire et éditer des fichiers · 04 Utilisateurs, groupes et permissions | ✅ |
| 2 · Maîtrise du shell | 05 Redirections, pipes et filtres · 06 Rechercher et expressions régulières · 07 Processus et tâches · 08 Gestion des logiciels · 09 Personnaliser son environnement | ✅ |
| 3 · Administration système | 10 Démarrage et systemd · 11 Disques · 12 Réseau · 13 SSH · 14 Planification et journaux · 15 Sauvegardes | à venir |
| 4 · Scripting | 16–17 Scripts Bash · 18 Git | à venir |
| 5 · Services et sécurité | 19 Sécurité · 20 Serveur web · 21 Conteneurs · 22 Performance et dépannage | à venir |
| 6 · Aller plus loin | 23 Le noyau · 24 Ansible · 25 Projet final et certifications | à venir |

## Lire le cours en local

Le site est fait de HTML, CSS et JavaScript, sans étape de compilation : ouvre simplement `index.html` dans un navigateur.

```
index.html          page d'accueil et programme
modules/            un fichier HTML par module
assets/             styles, scripts, images, vidéos finales (assets/video/)
publier.py          fabrique le site publiable (référencement) et le déploie
deploiement/        configuration du déploiement sur Cloudflare
videos/             sources des vidéos (animations, scripts de production)
```

## Publier

```bash
python publier.py https://linux.tneric.com              # fabrique publication/
python publier.py https://linux.tneric.com --deployer   # … et met en ligne sur Cloudflare
```

`publier.py` copie uniquement le site dans `publication/` et y ajoute ce qui dépend de l'adresse finale :
balises canonical et Open Graph, données structurées (cours, modules, vidéos), `sitemap.xml`, `robots.txt`,
page 404 et en-têtes de cache. Le déploiement utilise [Wrangler](https://developers.cloudflare.com/workers/wrangler/)
avec un jeton lu dans le dossier personnel de l'utilisateur, jamais dans le dépôt.

## Les vidéos

Chaque vidéo est une page HTML de 1920×1080 animée par une timeline [GSAP](https://gsap.com) en pause.
Le moteur de rendu (`videos/anim/render.mjs`) calcule chaque image avec Chrome headless puis l'encode avec ffmpeg :
le rendu est déterministe, sans saccade. La voix off et la musique sont générées par IA (Google Gemini TTS et Lyria),
et les sous-titres sont calés sur la voix au mot près grâce à Whisper (`videos/scripts/aligner.py`).

```bash
cd videos/anim && npm install
node render.mjs planche unix Charon 24        # planche-contact pour vérifier la mise en page
node render.mjs video unix Charon synthwave   # rendu final
```

Les voix, musiques et rendus intermédiaires ne sont pas versionnés (trop volumineux) ; les vidéos finales sont dans `assets/video/`.

## Crédits

- Tux : Larry Ewing (lewing@isc.tamu.edu) avec The GIMP.
- Photos via Wikimedia Commons : Linus Torvalds par Krd (CC BY-SA 4.0), Richard Stallman par Ruben Rodriguez (CC BY 4.0),
  Ken Thompson et Dennis Ritchie (domaine public), logo GNU par Aurelio A. Heckert (CC BY-SA 2.0).
- Polices : Inter, Space Grotesk, JetBrains Mono, Bricolage Grotesque, Instrument Sans (SIL Open Font License).
- Voix off et musiques des vidéos générées par IA.
