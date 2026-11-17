"""Cale le vrai texte de la voix off sur l'audio, mot à mot (Whisper local).

Usage : python aligner.py <clé> <voix> [<voix>…]    ex. python aligner.py unix Charon Zephyr
Sortie : ../reperes/<clé>-<voix>.json
  mots   : [{w, t0, t1}]   chaque mot du vrai texte (avec sa ponctuation)
  lignes : [{t0, t1, i0, i1}]   groupes de mots pour les sous-titres
  cues   : {nom: t}   début des expressions clés (REPERES)
Les temps sont ceux de la voix seule, sans le décalage du mixage.
Whisper déforme parfois les mots ; on aligne donc le vrai texte sur la
transcription (difflib) et on interpole les mots non reconnus.
"""
import difflib
import json
import os
import re
import sys
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tts import TEXTES  # noqa: E402

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

REPERES = {
    "unix": [
        ("an1969", "en 1969"), ("bell", "dans les laboratoires"), ("chercheurs", "deux chercheurs"),
        ("ken", "ken thompson"), ("unix", "unix leur"), ("idee", "leur idee"), ("outils", "des petits outils"),
        ("seule", "une seule chose"), ("bien", "la font bien"), ("briques", "et qu on assemble"),
        ("fichier", "autre idee"), ("toutfichier", "tout est fichier"), ("disque", "un disque"),
        ("clavier", "un clavier"), ("programme", "un programme"), ("memefacon", "tout se manipule"),
        ("universites", "unix conquiert"), ("probleme", "seul probleme"), ("att", "il appartient"),
        ("licence", "et sa licence"), ("an1983", "en 1983"), ("stallman", "richard stallman"),
        ("gnu", "le projet gnu"), ("libre", "un unix entierement"), ("utiliser", "de l utiliser"),
        ("etudier", "de l etudier"), ("modifier", "de le modifier"), ("partager", "de le partager"),
        ("libertes", "ce sont les quatre"), ("ecrit", "en quelques annees"), ("compilateur", "le compilateur"),
        ("shell", "le shell"), ("commandes", "les commandes"), ("manque", "il ne manque"),
        ("difficile", "la plus difficile"), ("noyau", "le noyau en"), ("an1991", "en 1991"),
        ("helsinki", "a helsinki"), ("etudiant", "un etudiant"), ("linus", "linus torvalds"),
        ("message", "poste un message"), ("jefais", "je fais"), ("hobby", "juste un hobby"),
        ("gros", "ca ne sera"), ("spoiler", "spoiler"), ("tort", "il avait tort"),
        ("emboitent", "le noyau de linus"), ("ne", "linux est ne"), ("devs", "des milliers"),
        ("mascotte", "et la mascotte"), ("tux", "un manchot"), ("aujourdhui", "aujourd hui"),
        ("android", "android"), ("cloud", "le cloud"), ("box", "les box"), ("cent", "et cent pour"),
        ("supercalc", "des supercalculateurs"), ("pasmal", "pas mal"),
    ],
    "vm": [
        ("intro", "tu veux apprendre"), ("windows", "sans toucher"), ("solution", "la solution"),
        ("deuxlettres", "deux lettres"), ("machine", "une machine virtuelle"), ("imagine", "imagine"),
        ("dansordi", "dans ton ordinateur"), ("hote", "ton vrai pc"), ("hote2", "c est l hote"),
        ("invite", "le systeme qui"), ("invite2", "c est l invite"), ("entre", "et entre les deux"),
        ("hyperviseur", "l hyperviseur"), ("vbox", "chez toi"), ("autres", "il en existe"),
        ("principe", "mais le principe"), ("prete", "virtualbox prete"), ("cpu", "un peu de processeur"),
        ("ram", "un peu de memoire"), ("disque", "et un disque"), ("fichier", "qu un gros fichier"),
        ("feu", "ubuntu lui"), ("vraie", "il croit"), ("rapide", "et c est rapide"),
        ("instructions", "des instructions"), ("vtx", "vt x"), ("amdv", "amd v"), ("bios", "pense juste"),
        ("regle", "la regle d or"), ("moitie", "jamais plus"), ("processeurs", "ni de tes"),
        ("huit", "avec huit"), ("quatre", "tu en donnes"), ("pasplus", "pas plus"), ("rament", "sinon les deux"),
        ("super", "et le super"), ("instantane", "l instantane"), ("photo", "une photo"),
        ("casses", "tu casses tout"), ("clic", "un clic"), ("arriere", "et tu reviens"),
        ("prends", "prends en un"), ("sauvegarde", "c est ton point"), ("jeu", "comme dans un jeu"),
        ("vasy", "alors vas y"), ("teste", "teste"), ("casse", "casse recommence"),
        ("recommence", "recommence"), ("apprend", "c est comme ca"),
    ],
    "shell": [
        ("ls1", "tu tapes deux"), ("entree", "tu appuies"), ("liste", "et la liste"), ("voyage", "en coulisses"),
        ("terminal", "premiere etape"), ("fenetre", "c est la fenetre"), ("travail", "son seul travail"),
        ("annees", "son nom vient"), ("geant", "quand on se connectait"), ("terminaux", "des terminaux"),
        ("teletype", "et avant eux"), ("papier", "qui imprimaient"), ("tty", "d ou l abreviation"),
        ("shell", "deuxieme etape"), ("bash", "sur ubuntu"), ("interprete", "c est lui l interprete"),
        ("decoupe", "il decoupe"), ("cherche", "cherche le programme"), ("demande", "et demande au noyau"),
        ("noyau", "troisieme etape"), ("cpu", "il donne au programme"), ("memoire", "de la memoire"),
        ("disque", "et l acces au disque"), ("inverse", "puis le resultat"), ("ecrit", "le programme ecrit"),
        ("affiche", "le terminal l affiche"), ("main", "et le shell te rend"), ("invite", "cette invite"),
        ("nom", "ton nom d utilisateur"), ("arobase", "arobase"), ("machine", "le nom de la machine"),
        ("deuxpoints", "deux points le dossier"), ("dollar", "et a la fin"), ("normal", "tu es un utilisateur normal"),
        ("diese", "si tu vois un diese"), ("root", "tu es root"), ("trois", "terminal shell noyau trois"),
        ("ouvre", "ouvre un terminal"), ("ctrl", "controle alt t"),
    ],
    "aide": [
        ("phrase", "une commande linux"), ("verbe", "d abord le verbe"), ("ls", "ls par exemple"),
        ("options", "ensuite les options"), ("tiret", "elles commencent"), ("tl", "tiret l pour"),
        ("ta", "tiret a pour"), ("coller", "et on peut les coller"), ("argument", "enfin l argument"),
        ("etc", "slash etc"), ("longue", "les options ont souvent"), ("all", "tiret tiret all"),
        ("lisible", "plus long a taper"), ("casse", "attention linux"), ("majuscule", "ls avec un l"),
        ("notfound", "command not found"), ("personne", "et personne ne"), ("secret", "le secret"),
        ("help", "premier reflexe"), ("resume", "un resume"), ("man", "deuxieme reflexe"),
        ("fleches", "on navigue"), ("cherchemot", "on cherche un mot"), ("q", "et on quitte"),
        ("tldr", "troisieme reflexe"), ("exemples", "pas de roman"), ("tab", "et pour taper moins"),
        ("complete", "deux ou trois lettres"), ("haut", "fleche du haut"), ("ctrlr", "controle r"),
        ("emballe", "et si une commande"), ("ctrlc", "controle c"), ("urgence", "le bouton d arret"),
        ("recap", "commande options argument"), ("portes", "et trois portes"), ("final", "avec ca aucune"),
    ],
    "arbo": [
        ("windows", "sous windows"), ("seul", "sous linux il n y a"), ("racine", "la racine"),
        ("slash", "un simple slash"), ("tout", "tout absolument tout"), ("role", "et chaque dossier"),
        ("home", "slash home les"), ("root", "slash root la"), ("etc", "slash etc la"),
        ("panneau", "c est le panneau"), ("usr", "slash usr et"), ("lsbin", "quand tu tapes ls"),
        ("var", "slash var les"), ("tmp", "slash tmp les"), ("boot", "slash boot le"),
        ("dev", "slash dev les"), ("sda", "ton disque c est"), ("fichier", "eh oui"),
        ("proc", "slash proc un"), ("media", "et enfin slash media"), ("retiens", "retiens les principaux"),
        ("t_home", "home pour toi"), ("t_etc", "etc pour la configuration"), ("t_var", "var pour les journaux"),
        ("final", "avec ces trois la"),
    ],
    "chemins": [
        ("intro", "pour designer"), ("deux", "et il existe"), ("absolu", "le chemin absolu"),
        ("racine", "il part de la racine"), ("exabs", "slash home slash user"), ("postale", "c est une adresse"),
        ("relatif", "le chemin relatif"), ("ici", "si tu es deja"), ("exrel", "documents slash rapport point txt suffit"),
        ("porte", "c est comme dire"), ("pwd", "pour savoir ou"), ("print", "print working"),
        ("cd", "pour te deplacer"), ("cddoc", "cd documents"), ("raccourcis", "et trois raccourcis"),
        ("point", "le point le dossier"), ("pointpoint", "le point point le"), ("cdpp", "cd point point"),
        ("tilde", "et le tilde"), ("astuces", "encore deux astuces"), ("cdseul", "cd tout seul"),
        ("cdtiret", "et cd tiret"), ("navigateur", "comme le bouton"), ("choix", "alors absolu"),
        ("scripts", "absolu dans les scripts"), ("quotidien", "relatif au quotidien"), ("tab", "et n oublie pas"),
        ("existe", "si elle ne propose"), ("recap", "slash pour la racine"), ("final", "avec ces quatre"),
    ],
    "lire": [
        ("texte", "sous linux presque"), ("indispensable", "savoir lire"), ("outil", "et il y a un outil"),
        ("cat", "cat affiche"), ("hostname", "comme slash etc"), ("dixmille", "mais sur un fichier"), ("defile", "tout defile"),
        ("less", "pour les gros fichiers"), ("page", "il affiche une page"), ("espace", "espace pour avancer"),
        ("b", "b pour reculer"), ("slash", "slash pour chercher"), ("q", "et q pour quitter"), ("man", "le meme fonctionnement"),
        ("head", "tu veux juste le debut"), ("dix", "par defaut les dix"), ("n3", "head tiret n trois"),
        ("tail", "et la fin"), ("journaux", "tres utile pour"), ("tailf", "mais le vrai super"), ("follow", "f comme follow"),
        ("direct", "le fichier reste ouvert"), ("admins", "les administrateurs"), ("ctrlc", "controle c pour"),
        ("wc", "et pour compter"), ("lignes", "le nombre de lignes"), ("recap", "recapitulons"),
        ("r_cat", "cat pour tout voir"), ("r_less", "less pour lire"), ("r_head", "head pour le debut"),
        ("r_tail", "tail pour la fin"), ("r_tailf", "tail tiret f pour le direct"), ("r_wc", "et wc pour compter"),
        ("final", "six commandes"),
    ],
    "vim": [
        ("intro", "un jour ca t arrivera"), ("ouvres", "tu ouvres un fichier"), ("vim", "et tu te retrouves"),
        ("tapes", "tu tapes rien"), ("quitter", "tu essaies de quitter"), ("millions", "rassure toi"),
        ("modes", "le secret de vim"), ("normal", "quand tu l ouvres"), ("commandes", "ici les touches"),
        ("d", "d supprime"), ("y", "y copie"), ("p", "p colle"), ("u", "u annule"), ("ecrire", "pour ecrire"),
        ("i", "appuie sur i"), ("insertion", "en bas le mot"), ("taper", "maintenant tu peux"), ("revenir", "pour revenir"),
        ("echap", "echap toujours"), ("doute", "en cas de doute"), ("quitte2", "et pour quitter"),
        ("w", "deux points w pour"), ("q", "deux points q pour quitter"), ("wq", "deux points w q"),
        ("qbang", "et deux points q point"), ("panique", "pour quitter sans enregistrer"), ("pourquoi", "pourquoi tant"),
        ("rapide", "parce qu une fois"), ("dd", "d d supprime"), ("yy", "y y la copie"), ("cherche", "slash pour chercher"),
        ("clavier", "tout ca sans"), ("serveurs", "et surtout vim"), ("nano", "si tu debutes"),
        ("formule", "mais retiens au moins"), ("final", "grave la"),
    ],
    "droits": [
        ("intro", "sous linux chaque fichier"), ("regles", "et des regles"), ("lsl", "pour les voir"),
        ("suite", "au debut de chaque"), ("lettres", "tiret r w x"), ("type", "le premier caractere"),
        ("fichier", "un tiret pour un fichier"), ("dossier", "un d pour un dossier"), ("trois", "ensuite trois groupes"),
        ("proprio", "le premier pour"), ("groupe", "le deuxieme pour"), ("autres", "le troisieme pour"),
        ("ordre", "et dans chaque trio"), ("r", "r read"), ("w", "w write"), ("x", "x execute"),
        ("refuse", "un tiret a la place"), ("dossierx", "sur un dossier"), ("chmod", "pour changer les droits"),
        ("uplusx", "chmod u plus x"), ("omoinsr", "chmod o moins r"), ("chiffres", "les administrateurs eux"),
        ("quatre", "lire vaut quatre"), ("deux", "ecrire deux"), ("un", "executer un"), ("sept", "on additionne"),
        ("six", "six lire et"), ("cinq", "cinq lire et"), ("c755", "chmod sept cent"), ("c644", "six cent quarante"),
        ("recap", "proprietaire groupe autres lire"), ("neuf", "neuf petites lettres"), ("securite", "et toute la securite"),
    ],
    "sudo": [
        ("root", "sur un systeme linux"), ("pasautres", "pas comme les autres"), ("zero", "son numero d identifiant"),
        ("tous", "et il a tous"), ("lire", "lire n importe"), ("detruire", "y compris detruire"), ("jamais", "c est pourquoi"),
        ("normal", "on utilise un compte"), ("moindre", "c est le principe"), ("besoin", "chacun n a que"),
        ("erreur", "une erreur un virus"), ("limites", "les degats"), ("installer", "mais alors"), ("sudo", "avec sudo"),
        ("ponctuelle", "sudo c est demander"), ("une", "executer une seule"), ("apt", "sudo apt update"),
        ("mdp", "le systeme te demande"), ("verifie", "verifie que tu"), ("execute", "puis execute"),
        ("journal", "et tout est note"), ("qui", "qui a le droit"), ("groupesudo", "les membres du groupe"),
        ("groupes", "car sous linux"), ("admins", "un groupe pour les administrateurs"), ("ajouter", "ajouter quelqu un"),
        ("whoami", "pour savoir qui"), ("id", "pour voir tes groupes"), ("passwd", "et tous les comptes"),
        ("regle", "retiens la regle"), ("necessaire", "sudo seulement quand"), ("comprends", "et seulement si"),
        ("pouvoir", "car avec un grand"),
    ],
    "flux": [
        ("trois", "chaque programme linux"), ("flux", "on les appelle"), ("stdin", "l entree standard"),
        ("clavier", "par defaut ton clavier"), ("stdout", "la sortie standard"), ("ecran", "par defaut ton ecran"),
        ("stderr", "et la sortie d erreur"), ("separe", "elle aussi s affiche"), ("tout", "et ca change tout"),
        ("rediriger", "car ces flux"), ("chevron", "avec le chevron"), ("exls", "ls superieur liste"),
        ("ecrase", "attention le fichier"), ("ajouter", "pour ajouter a la fin"), ("journal", "parfait pour tenir"),
        ("erreurs", "et les erreurs"), ("deux", "pour les capturer"), ("separes", "les erreurs partent"),
        ("tout2", "tu veux tout rassembler"), ("rejoignent", "les erreurs rejoignent"), ("taire", "et pour faire taire"),
        ("null", "slash dev slash null"), ("trounoir", "le trou noir"), ("disparait", "tout ce qu on y envoie"),
        ("inferieur", "enfin le chevron inverse"), ("recap", "zero l entree"), ("final", "trois numeros"),
    ],
    "pipes": [
        ("puissance", "sous linux la vraie"), ("combinaison", "mais de leur combinaison"), ("trait", "et l outil magique"),
        ("pipe", "le pipe branche"), ("tuyaux", "comme des tuyaux"), ("coulent", "pas de fichier"),
        ("probleme", "prenons un vrai"), ("serveur", "un serveur web"), ("question", "question quelles"),
        ("e1", "etape un"), ("e2", "etape deux"), ("e3", "etape trois"), ("e4", "etape quatre"),
        ("e5", "etape cinq"), ("e6", "etape six"), ("voila", "et voila"), ("ligne", "six petites commandes"),
        ("millions", "et la reponse tombe"), ("grep", "ajoute grep"), ("wc", "wc tiret l"), ("boite", "et tu tiens"),
        ("philo", "c est toute la philosophie"), ("outils", "des petits outils"), ("assembler", "et un pipe pour"),
    ],
    "find": [
        ("perdu", "un fichier perdu"), ("panique", "pas de panique"), ("grammaire", "sa grammaire"),
        ("ou", "d abord ou chercher"), ("quoi", "ensuite quoi chercher"), ("exname", "find slash etc tiret name"),
        ("conf", "etoile point conf"), ("sous", "tous les fichiers de configuration"), ("combinent", "les criteres se combinent"),
        ("typef", "tiret type f"), ("typed", "tiret type d"), ("size", "tiret size plus"), ("traquer", "parfait pour traquer"),
        ("mtime", "tiret mtime moins"), ("user", "et tiret user"), ("agit", "mais find ne se contente"),
        ("exec", "avec tiret exec"), ("delete", "et tiret delete"), ("verifie", "alors verifie"),
        ("parcourt", "find est puissant"), ("locate", "pour aller plus vite"), ("base", "il interroge"),
        ("which", "et pour savoir ou"), ("python", "which python"), ("trois", "ou chercher quoi chercher quoi en faire"),
        ("final", "avec ces trois questions"),
    ],
    "regex": [
        ("motif", "une expression reguliere"), ("forme", "pas un mot precis"), ("grep", "et avec grep"),
        ("ancres", "commencons par les ancres"), ("circ", "l accent circonflexe"), ("dollar", "le dollar"),
        ("exroot", "grep circonflexe root"), ("point", "le point remplace"), ("etoile", "l etoile repete"),
        ("pointetoile", "point etoile"), ("crochets", "les crochets definissent"), ("chiffre", "crochets zero tiret neuf"),
        ("lettre", "crochets a tiret z"), ("etendu", "avec grep tiret e"), ("plus", "le plus une fois"),
        ("interro", "le point d interrogation"), ("accolades", "les accolades"), ("barre", "et la barre verticale"),
        ("assemble", "assemble les pieces"), ("ip", "et tu reconnais"), ("piege", "le piege"),
        ("jokers", "le point et l etoile n ont"), ("apostrophes", "et pense aux apostrophes"), ("peur", "les regex font peur"),
        ("heures", "mais une fois apprivoisees"), ("langages", "et presque tous"),
    ],
    "processus": [
        ("chaque", "chaque programme qui"), ("exemples", "ton navigateur"), ("pid", "chaque processus recoit"),
        ("ancetre", "et tous descendent"), ("systemd", "le processus numero un"), ("arbre", "c est un veritable"),
        ("ps", "pour voir ceux"), ("psseul", "ps tout seul"), ("aux", "ps aux les montre"), ("top", "pour une vue en direct"),
        ("trie", "la liste se rafraichit"), ("chauffer", "ideal pour reperer"), ("htop", "et sa version moderne"),
        ("charge", "en haut de top"), ("coeurs", "si elle depasse"), ("nice", "enfin chaque processus a une priorite"),
        ("gentil", "plus la valeur"), ("recap", "un pid un parent"), ("final", "voila la carte"),
    ],
    "signaux": [
        ("comment", "comment arreter"), ("signal", "en lui envoyant"), ("ctrlc", "le plus courant"),
        ("sigint", "il envoie le signal"), ("kill", "pour un programme qui tourne ailleurs"), ("trompeur", "son nom est trompeur"),
        ("sigterm", "par defaut c est sigterm"), ("range", "le programme range"), ("repond", "et s il ne repond"),
        ("kill9", "kill tiret neuf"), ("immediat", "le noyau supprime"), ("dernier", "a utiliser en dernier"),
        ("pkill", "plus pratiques"), ("pause", "les signaux servent aussi"), ("ctrlz", "controle z suspend"),
        ("jobs", "la commande jobs"), ("fg", "fg le ramene"), ("bg", "bg le relance"), ("esperluette", "et une esperluette"),
        ("survive", "enfin pour qu une tache"), ("tmux", "nohup ou mieux"), ("recap", "demander avec sigterm"),
        ("final", "tu tiens maintenant"),
    ],
    "apt": [
        ("windows", "sous windows on"), ("mieux", "sous linux on a mieux"), ("paquet", "un paquet c est"),
        ("depots", "et tous ces paquets"), ("signes", "verifies et signes"), ("soixante", "plus de soixante"),
        ("apt", "sur ubuntu l outil"), ("update", "premiere etape"), ("catalogue", "le systeme telecharge"),
        ("rien", "rien n est installe"), ("install", "ensuite sudo apt install"), ("dependances", "apt trouve le logiciel"),
        ("une", "en une seule"), ("upgrade", "pour mettre a jour tout"), ("search", "tu cherches un logiciel"),
        ("show", "tu veux en savoir"), ("remove", "tu veux le retirer"), ("purge", "et pour supprimer aussi"),
        ("dpkg", "sous le capot"), ("quotidien", "mais au quotidien"), ("garantie", "les depots officiels"),
        ("conseil", "avant de telecharger"),
    ],
    "snap": [
        ("trois", "sur ubuntu il existe"), ("philo", "et chacune a"), ("deb", "les paquets deb"),
        ("partagent", "ils partagent"), ("figee", "mais leur version"), ("snap", "les snaps crees"),
        ("embarquent", "embarquent tout"), ("isoles", "ils sont isoles"), ("firefox", "firefox sur ubuntu"),
        ("contrepartie", "en contrepartie"), ("flatpak", "flatpak suit"), ("flathub", "son catalogue"),
        ("sources", "et il reste une"), ("controle", "le maximum de controle"), ("choisir", "alors que choisir"),
        ("c_apt", "d abord apt"), ("c_snap", "un snap ou un flatpak"), ("c_src", "et les sources"), ("regle", "trois formats"),
    ],
    "variables": [
        ("intro", "ton shell garde"), ("variables", "ce sont des variables"), ("def", "une variable c est"),
        ("dollar", "pour la lire"), ("home", "echo dollar home"), ("user", "echo dollar user"), ("creer", "pour creer la tienne"),
        ("espaces", "sans espaces"), ("env", "certaines variables sont"), ("export", "avec le mot export"),
        ("envcmd", "la commande env"), ("path", "et parmi elles"), ("cherche", "quand tu tapes ls"), ("fouille", "il fouille"),
        ("gagne", "le premier qui contient"), ("bin", "tu as ecrit tes propres"), ("ajoute", "ajoute le au path"),
        ("disparait", "attention une variable"), ("fichier", "pour la garder"), ("recap", "un dollar pour lire"),
        ("final", "et path pour trouver"),
    ],
    "bashrc": [
        ("intro", "ton terminal peut"), ("fichier", "et tout se passe"), ("lit", "a chaque ouverture"),
        ("permanents", "c est la qu on range"), ("alias", "premier reflexe"), ("ll", "alias ll egal"), ("maj", "alias maj egal"),
        ("tapes", "tu tapes maj"), ("variables", "deuxieme reflexe"), ("invite", "troisieme reflexe"), ("ps1", "la variable ps1"),
        ("perso", "tout est personnalisable"), ("source", "apres avoir modifie"), ("srccmd", "source point bashrc"),
        ("zsh", "et si tu veux aller"), ("ohmy", "zsh avec le celebre"), ("conseil", "un conseil"),
        ("commentaire", "et ajoute un commentaire"), ("final", "dans six mois"),
    ],
    "demarrage": [
        ("power", "tu appuies sur"), ("bureau", "quelques secondes plus tard"), ("relais", "mais entre les deux"),
        ("uefi", "premier coureur"), ("verifie", "il verifie le materiel"), ("grub", "deuxieme coureur"), ("menu", "c est lui qui affiche"),
        ("charge", "son travail"), ("noyau", "troisieme coureur"), ("controle", "il prend le controle"), ("initramfs", "pour trouver le vrai disque"),
        ("racine", "une fois la partition racine"), ("pid1", "celui qui porte"), ("systemd", "quatrieme coureur"), ("services", "systemd demarre tous"),
        ("login", "et enfin l ecran"), ("mdp", "tu entres ton mot"), ("analyze", "pour savoir combien"), ("blame", "et avec systemd analyze blame"),
        ("panne", "si un jour"), ("recap", "uefi grub noyau systemd quatre"), ("final", "quatre relais"),
    ],
    "systemd": [
        ("intro", "sur ton systeme"), ("services", "ce sont des services"), ("gouverne", "et c est systemd"), ("systemctl", "pour leur parler"),
        ("status", "systemctl status suivi"), ("actif", "est il actif"), ("vert", "le petit point vert"), ("start", "pour demarrer un service"),
        ("stop", "pour l arreter"), ("restart", "et apres avoir change"), ("piege", "attention piege"), ("enable", "pour qu il demarre"),
        ("disable", "et disable"), ("maintenant", "start c est pour maintenant"), ("toujours", "enable c est pour toujours"),
        ("unite", "chaque service est decrit"), ("tiennes", "tu peux meme"), ("panne", "et quand un service refuse"),
        ("journalctl", "journalctl affiche"), ("u", "avec tiret u"), ("f", "et avec tiret f"), ("reflexe", "un service en panne"),
        ("final", "la reponse est"),
    ],
    "disques": [
        ("neuf", "un disque neuf"), ("trois", "en trois etapes"), ("inventaire", "d abord l inventaire"), ("lsblk", "la commande lsblk"),
        ("noms", "sous linux les disques"), ("vda", "et dans une machine"), ("partitions", "les partitions ajoutent"), ("partitionner", "etape un"),
        ("terrain", "comme on divise"), ("formater", "etape deux"), ("ext4", "sous linux le grand"), ("monter", "etape trois"),
        ("lettre", "sous linux pas de lettre"), ("point", "sur un dossier vide"), ("mount", "avec la commande mount"), ("reboot", "mais au redemarrage"),
        ("fstab", "pour le rendre permanent"), ("uuid", "avec l uuid"), ("attention", "attention une erreur"), ("verifie", "apres chaque modification"),
        ("recap", "partitionner formater monter trois"), ("final", "et n importe quel"),
    ],
    "espace": [
        ("erreur", "message d erreur"), ("enquete", "pas de panique"), ("df", "premier indice"), ("h", "avec tiret h"), ("colonnes", "df affiche chaque"),
        ("pourcent", "au dessus de"), ("du", "deuxieme indice"), ("qui", "df te dit quel"), ("dush", "du tiret s h"), ("sort", "combine avec sort"),
        ("coupables", "les coupables habituels"), ("ncdu", "pour une enquete plus"), ("swap", "et il existe un espace"), ("pleine", "quand la memoire vive"),
        ("lent", "pratique mais"), ("free", "la commande free"), ("menage", "pour faire le menage"), ("clean", "puis sudo apt clean"),
        ("recap", "df pour voir"), ("final", "et ensuite"),
    ],
    "reseau": [
        ("intro", "tu tapes une adresse"), ("coulisses", "mais que s est il passe"), ("ip", "d abord ta machine"), ("postale", "comme une adresse postale"),
        ("ipa", "la commande ip a"), ("exemple", "par exemple dix"), ("dhcp", "elle t a ete attribuee"), ("nom", "deuxieme probleme"),
        ("chiffres", "or les ordinateurs"), ("dns", "c est le role du dns"), ("traduit", "il traduit un nom"), ("dig", "la commande dig"),
        ("passerelle", "ta demande part alors"), ("route", "la commande ip route"), ("port", "enfin sur le serveur"), ("numero", "pour savoir a qui"),
        ("p443", "quatre cent quarante trois"), ("p22", "vingt deux pour ssh"), ("ss", "la commande ss"), ("panne", "quand quelque chose"),
        ("ping", "ping verifie"), ("pingnom", "ping vers une adresse"), ("coupable", "le coupable c est"), ("recap", "adresse nom passerelle"),
        ("final", "quatre questions"),
    ],
    "ufw": [
        ("intro", "ta machine est branchee"), ("parefeu", "c est le travail"), ("vigile", "imagine un vigile"), ("porte", "chaque connexion qui arrive"),
        ("liste", "le vigile consulte"), ("autorise", "autorise il ouvre"), ("refuse", "pas sur la liste"), ("netfilter", "sous linux le vrai"),
        ("complexes", "mais ses regles"), ("ufw", "alors ubuntu fournit"), ("status", "au depart il est"), ("strategie", "la bonne strategie"),
        ("ouvrir", "puis n ouvrir que"), ("allowssh", "pour autoriser ssh"), ("allow80", "pour un site web"), ("piege", "attention piege"),
        ("dehors", "sinon tu fermes"), ("enable", "ensuite seulement"), ("verbose", "sudo ufw status verbose"), ("delete", "pour en retirer"),
        ("nmap", "et pour verifier depuis"), ("tiennes", "uniquement sur"), ("recap", "tout fermer puis"), ("final", "c est la regle d or"),
    ],
    "ssh": [
        ("intro", "un serveur c est souvent"), ("comment", "alors comment"), ("ssh", "ssh c est un terminal"), ("tapes", "tu tapes des commandes"),
        ("chiffre", "tout le trajet"), ("serveur", "cote serveur"), ("install", "sur ubuntu il s installe"), ("client", "cote client"),
        ("arobase", "d une arobase"), ("windows", "elle existe aussi"), ("empreinte", "a la premiere connexion"), ("yes", "tu reponds yes"),
        ("change", "si un jour cette"), ("usurpe", "ou quelqu un"), ("mdp", "ensuite ton mot de passe"), ("invite", "et l invite change"),
        ("exit", "pour revenir"), ("vm", "et pour une machine"), ("nat", "dans virtualbox"), ("redir", "le port deux mille deux"),
        ("p2222", "puis ssh tiret p"), ("scp", "pour copier des fichiers"), ("recap", "un terminal n importe"), ("final", "c est ca ssh"),
    ],
    "cles": [
        ("intro", "taper ton mot de passe"), ("deviner", "et surtout risque"), ("mieux", "heureusement il existe"), ("paire", "le principe est simple"),
        ("publique", "une cle publique"), ("privee", "et une cle privee"), ("keygen", "pour creer ta paire"), ("fichiers", "deux fichiers apparaissent"),
        ("prive", "la cle privee id"), ("jamais", "elle ne quitte jamais"), ("pub", "et la cle publique qui"), ("donner", "celle la tu peux"),
        ("copyid", "tu poses ensuite"), ("authorized", "ta cle publique rejoint"), ("defi", "a la connexion suivante"), ("reussi", "defi reussi"),
        ("aucun", "et aucun mot de passe"), ("phrase", "protege ta cle"), ("vol", "si on te la vole"), ("derniere", "derniere etape"),
        ("config", "dans le fichier sshd"), ("verifie", "mais avant verifie"), ("dehors", "sinon tu restes"), ("recap", "un cadenas sur le serveur"),
        ("final", "plus sur et plus"),
    ],
}


def norm(s):
    s = s.replace("’", "'")
    s = unicodedata.normalize("NFD", s.lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", " ", s).split()


def mots_du_texte(texte):
    texte = texte.replace("<short pause>", " ")
    mots, attente = [], ""
    for w in texte.split():
        if norm(w):
            mots.append(attente + w)
            attente = ""
        elif w in "«(" or not mots:      # ponctuation ouvrante : rattachée au mot suivant
            attente += w + " "
        else:                            # « : », « ? », « … » : rattachés au mot précédent
            mots[-1] += " " + w
    return mots


def grouper(mots):
    """Lignes de sous-titres : coupure sur la ponctuation forte, ou à ~7 mots."""
    lignes, debut = [], 0
    for i, m in enumerate(mots):
        n = i - debut + 1
        fin_forte = re.search(r"[.?!…:»]$", m["w"])
        fin_faible = re.search(r"[,;]$", m["w"]) and n >= 4
        if fin_forte or fin_faible or n >= 7 or i == len(mots) - 1:
            lignes.append({"i0": debut, "i1": i, "t0": mots[debut]["t0"], "t1": m["t1"]})
            debut = i + 1
    return lignes


def aligner(modele, cle, voix):
    wav = f"{RACINE}/voix/{cle}-{voix}.wav"
    segments, _ = modele.transcribe(wav, language="fr", word_timestamps=True, vad_filter=False, beam_size=5)
    entendus = []
    for seg in segments:
        for w in seg.words:
            for part in norm(w.word):
                entendus.append((part, w.start, w.end))

    vrais = mots_du_texte(TEXTES[cle])
    jetons, proprio = [], []          # jetons normalisés du vrai texte → indice du mot
    for i, w in enumerate(vrais):
        for part in norm(w):
            jetons.append(part)
            proprio.append(i)

    temps = [None] * len(jetons)
    sm = difflib.SequenceMatcher(None, jetons, [e[0] for e in entendus], autojunk=False)
    for a, b, n in sm.get_matching_blocks():
        for k in range(n):
            temps[a + k] = (entendus[b + k][1], entendus[b + k][2])
    reconnus = sum(t is not None for t in temps)

    # Interpolation linéaire des jetons non reconnus.
    fin_audio = entendus[-1][2] if entendus else 0
    for i in range(len(temps)):
        if temps[i] is None:
            g = next((j for j in range(i - 1, -1, -1) if temps[j]), None)
            d = next((j for j in range(i + 1, len(temps)) if temps[j]), None)
            tg = temps[g][1] if g is not None else 0.0
            td = temps[d][0] if d is not None else fin_audio
            ng, nd = (g if g is not None else -1), (d if d is not None else len(temps))
            pas = (td - tg) / (nd - ng)
            temps[i] = (tg + pas * (i - ng), tg + pas * (i - ng + 1))

    mots = []
    for i, w in enumerate(vrais):
        ts = [temps[k] for k in range(len(jetons)) if proprio[k] == i]
        mots.append({"w": w, "t0": round(min(t[0] for t in ts), 3), "t1": round(max(t[1] for t in ts), 3)})

    cues, curseur = {}, 0
    for nom, expr in REPERES[cle]:
        cible = norm(expr)
        pos = next((i for i in range(curseur, len(jetons) - len(cible) + 1)
                    if jetons[i:i + len(cible)] == cible), None)
        if pos is None:
            print(f"  ! repère introuvable dans le texte : {nom} ({expr})")
            continue
        cues[nom] = round(temps[pos][0], 3)
        curseur = pos + 1

    res = {"mots": mots, "lignes": grouper(mots), "cues": cues, "fin": round(fin_audio, 3)}
    print(f"{cle}-{voix}: {reconnus}/{len(jetons)} jetons reconnus, fin {fin_audio:.1f} s, {len(cues)} repères")
    return res


if __name__ == "__main__":
    os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
    from faster_whisper import WhisperModel
    modele = WhisperModel("small", device="cpu", compute_type="int8")
    cle = sys.argv[1]
    os.makedirs(f"{RACINE}/reperes", exist_ok=True)
    for voix in sys.argv[2:]:
        r = aligner(modele, cle, voix)
        with open(f"{RACINE}/reperes/{cle}-{voix}.json", "w", encoding="utf-8") as f:
            json.dump(r, f, ensure_ascii=False, indent=1)
