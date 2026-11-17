"""Voix off des vidéos du carnet Linux, avec Gemini TTS (API Interactions).

Usage : python tts.py <clé> <voix> [sortie.wav]
  clé : unix | vm
Sortie par défaut : ../voix/<clé>-<voix>.wav

Quota gratuit : 10 requêtes par jour, 3 par minute.
"""
import base64
import io
import json
import os
import sys
import urllib.error
import urllib.request
import wave

CLE = open(os.path.expanduser("~/.gemini_api_key"), encoding="utf-8-sig").read().strip()
MODELE = "gemini-3.8-flash-tts"
RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

STYLE = (
    "Dynamic, clear native French documentary narrator, in the style of a popular YouTube "
    "science-popularisation channel: lively rhythm, curious and warm, a hint of playful humour "
    "on the punchlines, confident, never shouting. Short natural pauses between ideas. "
    "Standard French pronunciation. 'Unix' is pronounced 'u-nix', 'GNU' is pronounced 'gnou', "
    "'Linux' is pronounced 'li-nux', 'Ubuntu' is pronounced 'ou-boun-tou'. "
    "Linux command names are read letter by letter in French: 'ls' = 'èl-èss', 'cd' = 'cé-dé', "
    "'pwd' = 'pé-doublevé-dé', 'tldr' = 'té-èl-dé-èr', 'wc' = 'doublevé-cé', 'TTY' = 'té-té-i grec'. "
    "'cat', 'less', 'head', 'tail', 'man', 'help', 'Bash', 'Vim', 'nano', 'root', 'home' are read as English words. "
    "'etc' is read 'ètsé', 'usr' is read 'user', 'tmp' is read 'temp', 'dev', 'var', 'proc', 'boot', 'bin' as written. "
    "'chmod' is read 'tché-mod', 'chown' is read 'tché-own', 'sudo' is read 'sou-dou', 'apt' is read 'apte', 'id' is read 'i-dé', "
    "'passwd' is read 'password', 'stdin' is read 'standard in', 'stdout' is read 'standard out', 'stderr' is read 'standard error', "
    "'grep', 'cut', 'sort', 'uniq', 'pipe', 'null', 'read', 'write', 'execute' are read as English words. "
    "'find', 'locate', 'which', 'exec', 'delete', 'name', 'type', 'size', 'top', 'nice', 'kill', 'killall', 'jobs' are read as English words. "
    "'mtime' is read 'em-time', 'regex' is read 'ré-gex', 'ps' is read 'pé-èss', 'aux' is read 'a-u-ix', 'htop' is read 'ache-top', "
    "'PID' is read 'pid', 'systemd' is read 'system-dé', 'SIGINT' is read 'sig-int', 'SIGTERM' is read 'sig-term', 'SIGKILL' is read 'sig-kill', "
    "'pkill' is read 'pé-kill', 'fg' is read 'èf-gé', 'bg' is read 'bé-gé', 'nohup' is read 'no-heup', 'tmux' is read 'té-mux'. "
    "'dpkg' is read 'dé-pé-ka-gé', 'deb' is read 'dèb', 'snap', 'snaps', 'flatpak', 'Flathub', 'update', 'upgrade', 'install', 'remove', 'purge', "
    "'search', 'show', 'export', 'source', 'HOME', 'USER', 'PATH' are read as English words. 'env' is read 'env', 'echo' is read 'écho', "
    "'bashrc' is read 'bash-ré-cé', 'll' is read 'èl-èl', 'PS1' is read 'pé-èss-un', 'Zsh' is read 'zède-shell', 'Oh My Zsh' is read 'oh my zède-shell', "
    "'maj' is read 'maj'. "
    "'UEFI' is read letter by letter 'u-e-èf-i', 'GRUB' is read 'grub', 'initramfs' is read 'init-ram-èf-èss', 'Power' as English, "
    "'systemd-analyze' is read 'system-dé analyze', 'blame' as English, 'systemctl' is read 'system-cé-té-èl', 'journalctl' is read 'journal-cé-té-èl', "
    "'status', 'start', 'stop', 'restart', 'enable', 'disable' are read as English words. "
    "'lsblk' is read 'èl-èss-bé-èl-ka', 'sda' is read 'èss-dé-a', 'sdb' is read 'èss-dé-bé', 'vda' is read 'vé-dé-a', 'sda1' is read 'èss-dé-a un', "
    "'sda2' is read 'èss-dé-a deux', 'fdisk' is read 'èf-disk', 'parted' is read 'part-ed', 'mkfs' is read 'èm-ka-èf-èss', 'ext4' is read 'ext quatre', "
    "'mount' as English, 'mnt' is read 'èm-èn-té', 'fstab' is read 'èf-èss-tab', 'UUID' is read 'u-u-i-dé', "
    "'df' is read 'dé-èf', 'du' is read 'dé-u', 'ncdu' is read 'èn-cé-dé-u', 'free', 'swap', 'autoremove', 'clean', 'log' as English, 'RAM' is read 'ram'. "
    "'IP' is read 'i-pé', 'ip a' is read 'i-pé a', 'ip route' is read 'i-pé route', 'DHCP' is read 'dé-ache-cé-pé', 'DNS' is read 'dé-èn-èss', "
    "'dig', 'ping', 'route', 'allow', 'deny', 'delete', 'verbose', 'yes', 'exit', 'localhost' are read as English words, "
    "'ss' is read 'èss-èss', 'ufw' is read 'u-èf-doublevé', 'tcp' is read 'té-cé-pé', 'netfilter' as English, 'nmap' is read 'èn-map', "
    "'SSH' is read 'èss-èss-ache', 'sshd' is read 'èss-èss-ache-dé', 'openssh-server' is read 'open-èss-èss-ache server', "
    "'scp' is read 'èss-cé-pé', 'rsync' is read 'èr-sync', 'NAT' is read 'nat', 'PowerShell' as English, "
    "'ssh-keygen' is read 'èss-èss-ache key-gen', 'ed25519' is read 'é-dé deux-cinq-cinq-un-neuf', 'id' in 'id ed25519' is read 'i-dé', "
    "'ssh-copy-id' is read 'èss-èss-ache copy i-dé', 'pub' is read 'pub', 'authorized keys' as English, 'sshd config' is read 'èss-èss-ache-dé config', "
    "'PasswordAuthentication' is read 'password authentication' in English, 'no' is read as English."
)

TEXTES = {
    "unix": """En 1969, dans les laboratoires Bell, aux États-Unis, deux chercheurs, Ken Thompson et Dennis Ritchie, créent un système d'exploitation : Unix.
Leur idée ? Des petits outils, qui font une seule chose… mais qui la font bien. Et qu'on assemble, comme des briques. Autre idée géniale : tout est fichier. Un disque, un clavier, un programme… tout se manipule de la même façon.
Unix conquiert les universités. Seul problème : il appartient à AT&T… et sa licence coûte de plus en plus cher.
En 1983, Richard Stallman lance le projet GNU : un Unix entièrement libre. Libre de l'utiliser, de l'étudier, de le modifier, de le partager. Ce sont les quatre libertés du logiciel libre.
En quelques années, GNU écrit presque tout : le compilateur, le shell, les commandes… Il ne manque qu'une pièce. La plus difficile : le noyau.
En 1991, à Helsinki, un étudiant de vingt et un ans, Linus Torvalds, poste un message : « Je fais un système d'exploitation libre. Juste un hobby. Ça ne sera pas gros, ni professionnel. »
<short pause> Spoiler : il avait tort.
Le noyau de Linus et les outils de GNU s'emboîtent parfaitement. Linux est né. Des milliers de développeurs, partout dans le monde, rejoignent l'aventure. Et la mascotte ? Un manchot : Tux.
Aujourd'hui, il fait tourner Android, le cloud, les box internet… et cent pour cent des supercalculateurs les plus puissants du monde.
<short pause> Pas mal, pour un hobby.""",

    "vm": """Tu veux apprendre Linux… sans toucher à ton Windows ? La solution tient en deux lettres : V.M. Une machine virtuelle.
Imagine un ordinateur… dans ton ordinateur. Ton vrai PC, c'est l'hôte. Le système qui tourne dans la fenêtre, Ubuntu, c'est l'invité. Et entre les deux, le chef d'orchestre : l'hyperviseur. Chez toi, c'est VirtualBox. Il en existe d'autres, comme VMware ou Hyper-V, mais le principe reste le même.
VirtualBox prête à Ubuntu une partie de ton matériel : un peu de processeur, un peu de mémoire… et un disque dur, qui n'est en réalité qu'un gros fichier sur ton disque Windows.
Ubuntu, lui, n'y voit que du feu : il croit tourner sur une vraie machine. Et c'est rapide, parce que ton processeur a des instructions spéciales pour ça : VT-x chez Intel, AMD-V chez AMD. Pense juste à les activer dans le BIOS.
La règle d'or : jamais plus de la moitié de ta mémoire, ni de tes processeurs. Avec huit gigas de RAM, tu en donnes quatre. Pas plus. Sinon, les deux systèmes rament.
Et le super-pouvoir de la VM ? L'instantané. Une photo complète de ta machine, à un moment précis. Tu casses tout ? Un clic… et tu reviens en arrière. Prends-en un juste après l'installation : c'est ton point de sauvegarde, comme dans un jeu vidéo.
<short pause> Alors vas-y : teste, casse, recommence. C'est comme ça qu'on apprend Linux.""",
    "shell": """Tu tapes deux lettres : ls. Tu appuies sur Entrée… et la liste de tes fichiers apparaît. En coulisses, ta commande vient de faire un sacré voyage.
Première étape : le terminal. C'est la fenêtre. Son seul travail : afficher du texte et transmettre ce que tu tapes. Son nom vient des années soixante-dix, quand on se connectait à un ordinateur géant depuis un simple écran et un clavier : des terminaux. Et avant eux, des téléscripteurs, qui imprimaient sur du papier. D'où l'abréviation TTY, qu'on retrouve encore partout dans Linux.
Deuxième étape : le shell. Sur Ubuntu, il s'appelle Bash. C'est lui l'interprète. Il découpe ta ligne en morceaux, cherche le programme ls sur le disque, et demande au noyau de le lancer.
Troisième étape : le noyau. Il donne au programme du temps de processeur, de la mémoire, et l'accès au disque pour lire le contenu du dossier.
Puis le résultat fait le chemin inverse. Le programme écrit sa réponse, le terminal l'affiche… et le shell te rend la main, avec l'invite.
Cette invite, justement, elle te parle. Ton nom d'utilisateur, arobase, le nom de la machine, deux-points, le dossier où tu te trouves. Et à la fin, un dollar : tu es un utilisateur normal. Si tu vois un dièse, attention : tu es root, l'administrateur, celui qui peut tout casser.
Terminal, shell, noyau : trois rôles, une seule ligne de commande. Et maintenant que tu sais qui fait quoi… ouvre un terminal : Contrôle, Alt, T.""",

    "aide": """Une commande Linux, ça se lit comme une phrase. D'abord, le verbe : la commande. ls, par exemple : lister. Ensuite, les options, qui disent comment le faire. Elles commencent par un tiret. Tiret l, pour un affichage détaillé. Tiret a, pour voir aussi les fichiers cachés. Et on peut les coller : tiret l a. Enfin, l'argument : sur quoi agir. Slash etc, le dossier de configuration.
Les options ont souvent une version longue, avec deux tirets : tiret tiret all. Plus long à taper, mais beaucoup plus lisible.
Attention, Linux est pointilleux : majuscules et minuscules comptent. ls avec un L majuscule ? Command not found.
Et personne ne connaît toutes les options par cœur. Le secret, c'est de savoir où chercher. Premier réflexe : tiret tiret help. Un résumé de toutes les options, en un éclair. Deuxième réflexe : man. Le manuel complet. On navigue avec les flèches, on cherche un mot avec slash… et on quitte avec Q. Troisième réflexe : tldr. Pas de roman, juste les exemples les plus utiles.
Et pour taper moins, utilise Tab. Deux ou trois lettres, Tab… et le shell complète à ta place. Flèche du haut pour retrouver une ancienne commande. Contrôle R pour la chercher dans l'historique. Et si une commande s'emballe ? Contrôle C. Le bouton d'arrêt d'urgence.
Commande, options, argument. Et trois portes de sortie : help, man, tldr. Avec ça, aucune commande ne te résiste.""",

    "arbo": """Sous Windows, il y a C deux-points, D deux-points… Sous Linux, il n'y a qu'un seul point de départ : la racine. Un simple slash.
Tout, absolument tout, est rangé sous cette racine, dans une arborescence. Et chaque dossier a un rôle précis, le même sur toutes les distributions.
Slash home : les dossiers personnels. Tes documents, tes images, ta configuration. Chaque utilisateur a le sien.
Slash root : la maison de l'administrateur.
Slash etc : la configuration du système. Des fichiers texte, qu'on peut lire et modifier. C'est le panneau de contrôle de Linux.
Slash usr et slash bin : les programmes. Quand tu tapes ls, c'est slash usr slash bin slash ls qui s'exécute.
Slash var : les données qui varient. Les journaux du système, les bases de données, les sites web.
Slash tmp : les fichiers temporaires, effacés au redémarrage.
Slash boot : le noyau et le chargeur de démarrage. Mieux vaut ne pas y toucher.
Slash dev : les périphériques. Ton disque, c'est slash dev slash sda. Eh oui : sous Linux, tout est fichier.
Slash proc : un dossier magique, qui n'existe pas sur le disque. Le noyau y expose en direct les processus et l'état du système.
Et enfin slash media et slash mnt : c'est là qu'apparaissent les clés USB et les disques montés.
Retiens les principaux : home pour toi, etc pour la configuration, var pour les journaux. Avec ces trois-là, tu sais déjà où chercher dans la plupart des cas.""",

    "chemins": """Pour désigner un fichier, il faut donner son chemin. Et il existe deux façons de le faire.
Le chemin absolu commence toujours par un slash : il part de la racine. Slash home, slash user, slash Documents, slash rapport point txt. C'est une adresse complète, comme une adresse postale : elle fonctionne de n'importe où.
Le chemin relatif, lui, part de l'endroit où tu te trouves. Si tu es déjà dans ton dossier personnel, Documents slash rapport point txt suffit. C'est comme dire : deuxième porte à gauche.
Pour savoir où tu es, une commande : pwd. Print working directory.
Pour te déplacer : cd. cd Documents, et tu entres dans le dossier.
Et trois raccourcis à connaître par cœur. Le point : le dossier où tu es. Le point point : le dossier parent, un étage au-dessus. cd point point, et tu remontes. Et le tilde : ton dossier personnel, où que tu sois.
Encore deux astuces. cd tout seul te ramène chez toi. Et cd tiret te renvoie au dossier précédent, comme le bouton retour d'un navigateur.
Alors, absolu ou relatif ? Absolu dans les scripts et la configuration, pour ne jamais se tromper. Relatif au quotidien, pour aller vite.
Et n'oublie pas la touche Tab : elle complète les chemins pour toi. Si elle ne propose rien… c'est que le chemin n'existe pas.
Slash pour la racine, point pour ici, point point pour remonter, tilde pour la maison. Avec ces quatre symboles, tu ne te perdras plus jamais.""",

    "lire": """Sous Linux, presque tout est du texte : la configuration, les journaux, les scripts. Savoir lire un fichier, c'est donc indispensable. Et il y a un outil pour chaque situation.
cat affiche tout le fichier d'un coup. Parfait pour un petit fichier, comme slash etc slash hostname. Mais sur un fichier de dix mille lignes ? Tout défile, et tu ne vois que la fin.
Pour les gros fichiers, il y a less. Il affiche une page à la fois. Espace pour avancer, B pour reculer, slash pour chercher un mot, et Q pour quitter. Le même fonctionnement que man : tu le connais déjà.
Tu veux juste le début ? head. Par défaut, les dix premières lignes. head tiret n trois, et tu n'en vois que trois.
Et la fin ? tail. Les dix dernières lignes. Très utile pour les journaux, où les événements les plus récents sont en bas.
Mais le vrai super-pouvoir, c'est tail tiret f. F comme follow : suivre. Le fichier reste ouvert, et chaque nouvelle ligne s'affiche en direct. Les administrateurs l'utilisent pour surveiller un serveur en temps réel. Contrôle C pour arrêter.
Et pour compter ? wc. Le nombre de lignes, de mots et de caractères.
Récapitulons. cat pour tout voir. less pour lire tranquillement. head pour le début, tail pour la fin, tail tiret f pour le direct. Et wc pour compter. Six commandes, et plus aucun fichier ne te résiste.""",

    "vim": """Un jour, ça t'arrivera. Tu ouvres un fichier… et tu te retrouves dans Vim. Tu tapes, rien ne marche. Tu essaies de quitter… impossible. Rassure-toi : des millions de développeurs sont passés par là.
Le secret de Vim, ce sont les modes. Quand tu l'ouvres, tu es en mode normal. Ici, les touches ne tapent pas de texte : ce sont des commandes. D supprime, Y copie, P colle, U annule.
Pour écrire, il faut passer en mode insertion : appuie sur I. En bas, le mot INSERTION apparaît. Maintenant, tu peux taper normalement.
Pour revenir au mode normal ? Échap. Toujours Échap. En cas de doute, appuie sur Échap.
Et pour quitter, on passe en mode commande, avec deux-points. Deux-points W pour enregistrer. Deux-points Q pour quitter. Deux-points W Q pour faire les deux. Et deux-points Q point d'exclamation… pour quitter sans enregistrer, en cas de panique.
Pourquoi tant de complications ? Parce qu'une fois les modes maîtrisés, Vim est d'une rapidité redoutable. D D supprime une ligne entière. Y Y la copie. Slash pour chercher. Tout ça sans jamais lâcher le clavier. Et surtout, Vim est installé sur presque tous les serveurs du monde.
Si tu débutes, préfère nano : ses raccourcis sont écrits en bas de l'écran. Mais retiens au moins la formule magique de Vim : Échap, deux-points, Q, point d'exclamation, Entrée. Grave-la dans ta mémoire.""",
    "droits": """Sous Linux, chaque fichier a un propriétaire… et des règles. Pour les voir : ls tiret l. Au début de chaque ligne, une étrange suite de lettres : tiret, r, w, x, r, tiret, x, r, tiret, tiret.
Le premier caractère indique le type. Un tiret pour un fichier, un d pour un dossier.
Ensuite, trois groupes de trois lettres. Le premier pour le propriétaire du fichier, le deuxième pour son groupe, le troisième pour tous les autres.
Et dans chaque trio, toujours le même ordre. R, read : lire. W, write : modifier. X, execute : exécuter. Un tiret à la place d'une lettre ? Ce droit est refusé.
Sur un dossier, x permet… d'y entrer.
Pour changer les droits, une commande : chmod. chmod u plus x : on ajoute l'exécution pour le propriétaire. chmod o moins r : on retire la lecture aux autres.
Les administrateurs, eux, parlent en chiffres. Lire vaut quatre, écrire deux, exécuter un. On additionne : sept, tous les droits. Six, lire et écrire. Cinq, lire et exécuter. chmod sept cent cinquante-cinq : tout pour le propriétaire, lire et exécuter pour les autres. Six cent quarante-quatre : le réglage classique d'un document.
Propriétaire, groupe, autres. Lire, écrire, exécuter. Neuf petites lettres… et toute la sécurité de Linux tient dedans.""",

    "sudo": """Sur un système Linux, il existe un utilisateur pas comme les autres : root. Son numéro d'identifiant est zéro, et il a tous les droits. Lire n'importe quel fichier, installer, supprimer, tout modifier… y compris détruire le système en une seule commande.
C'est pourquoi on ne travaille jamais en root au quotidien. On utilise un compte normal, aux droits limités. C'est le principe du moindre privilège : chacun n'a que les droits dont il a besoin, rien de plus. Une erreur, un virus, un script mal écrit ? Les dégâts restent limités à ton dossier personnel.
Mais alors, comment installer un logiciel ? Avec sudo. sudo, c'est demander une autorisation ponctuelle : exécuter une seule commande avec les droits de root. sudo apt update : le système te demande ton propre mot de passe, vérifie que tu en as le droit… puis exécute la commande. Et tout est noté dans un journal.
Qui a le droit d'utiliser sudo ? Les membres du groupe sudo. Car sous Linux, les utilisateurs sont rangés dans des groupes. Un groupe pour les administrateurs, un pour l'audio, un pour les journaux… Ajouter quelqu'un à un groupe, c'est lui donner d'un coup tous les droits de ce groupe.
Pour savoir qui tu es : whoami. Pour voir tes groupes : id. Et tous les comptes du système sont listés dans le fichier slash etc slash passwd.
Retiens la règle d'or : sudo seulement quand c'est nécessaire, et seulement si tu comprends la commande. Car avec un grand pouvoir… vient une grande responsabilité.""",

    "flux": """Chaque programme Linux est relié au monde par trois canaux. On les appelle des flux.
L'entrée standard, stdin, numéro zéro : ce que le programme lit. Par défaut, ton clavier.
La sortie standard, stdout, numéro un : ce qu'il affiche. Par défaut, ton écran.
Et la sortie d'erreur, stderr, numéro deux : ses messages d'erreur. Elle aussi s'affiche à l'écran… mais c'est un canal séparé. Et ça change tout.
Car ces flux, on peut les rediriger. Avec le chevron, supérieur, la sortie part dans un fichier au lieu de l'écran. ls supérieur liste point txt : le résultat est enregistré. Attention : le fichier est écrasé à chaque fois.
Pour ajouter à la fin sans rien effacer : deux chevrons. Parfait pour tenir un journal.
Et les erreurs ? Elles ne suivent pas le chevron. Pour les capturer, on précise leur numéro : deux, chevron. Les erreurs partent dans un fichier, les résultats restent à l'écran.
Tu veux tout rassembler ? Deux, chevron, et commercial, un : les erreurs rejoignent la sortie standard.
Et pour faire taire une commande, il existe un endroit magique : slash dev slash null. Le trou noir de Linux. Tout ce qu'on y envoie disparaît à jamais.
Enfin, le chevron inverse, inférieur, alimente l'entrée standard avec le contenu d'un fichier.
Zéro, l'entrée. Un, la sortie. Deux, les erreurs. Trois numéros, quelques chevrons… et c'est toi qui décides où va chaque information.""",

    "pipes": """Sous Linux, la vraie puissance ne vient pas d'une commande… mais de leur combinaison. Et l'outil magique pour ça, c'est un simple trait vertical : le pipe.
Le pipe branche la sortie d'une commande directement sur l'entrée de la suivante. Comme des tuyaux. Pas de fichier intermédiaire : les données coulent d'un programme à l'autre.
Prenons un vrai problème. Un serveur web a reçu des milliers de visites, toutes notées dans un journal. Question : quelles adresses IP l'ont le plus visité ?
Étape un : cat, pour lire le journal. Des milliers de lignes défilent.
Étape deux : cut, pour ne garder que la première colonne : l'adresse IP.
Étape trois : sort, pour trier les adresses. Les identiques se retrouvent côte à côte.
Étape quatre : uniq tiret c, qui fusionne les doublons et compte combien de fois chacun apparaît.
Étape cinq : sort tiret n r, pour trier ces nombres du plus grand au plus petit.
Étape six : head, pour ne garder que les cinq premiers.
Et voilà ! Six petites commandes, une seule ligne… et la réponse tombe en une fraction de seconde, même sur des millions de lignes.
Ajoute grep pour filtrer les lignes qui contiennent un mot, wc tiret l pour compter, et tu tiens une boîte à outils redoutable.
C'est toute la philosophie Unix, depuis 1973 : des petits outils qui font une seule chose, et la font bien. Et un pipe pour les assembler.""",
    "find": """Un fichier perdu quelque part, dans les milliers de dossiers du système ? Pas de panique : find le retrouve.
Sa grammaire est simple. D'abord, où chercher : un dossier de départ. Ensuite, quoi chercher : des critères. find slash etc tiret name, et entre guillemets, étoile point conf : tous les fichiers de configuration, dans tous les sous-dossiers.
Les critères se combinent à volonté. tiret type f pour les fichiers, tiret type d pour les dossiers. tiret size plus cent M pour ceux qui dépassent cent mégaoctets : parfait pour traquer ce qui remplit ton disque. tiret mtime moins sept, pour ceux modifiés cette semaine. Et tiret user, pour ceux d'un utilisateur précis.
Mais find ne se contente pas de trouver. Avec tiret exec, il agit sur chaque résultat : compresser, copier, changer les droits. Et tiret delete supprime… alors vérifie toujours la liste avant !
find est puissant, mais il parcourt réellement le disque. Pour aller plus vite, il y a locate : il interroge une base de données, et répond instantanément.
Et pour savoir où se cache une commande ? which. which python, et tu obtiens son chemin exact.
Où chercher, quoi chercher, quoi en faire. Avec ces trois questions, aucun fichier ne peut plus t'échapper.""",

    "regex": """Une expression régulière, c'est un motif qui décrit du texte. Pas un mot précis : une forme. Et avec grep, ça devient un détecteur surpuissant.
Commençons par les ancres. L'accent circonflexe : le début de la ligne. Le dollar : la fin. grep circonflexe root trouve les lignes qui commencent par root, et seulement celles-là.
Le point remplace n'importe quel caractère. L'étoile répète ce qui la précède, zéro fois ou plus. Point étoile : n'importe quoi, de n'importe quelle longueur.
Les crochets définissent une liste. Crochets zéro tiret neuf : un chiffre. Crochets a tiret z : une lettre minuscule.
Avec grep tiret E, le mode étendu, on ajoute des quantificateurs. Le plus : une fois ou plus. Le point d'interrogation : zéro ou une fois. Les accolades : un nombre précis de répétitions. Et la barre verticale : ceci, ou cela.
Assemble les pièces : un à trois chiffres, un point, le tout répété quatre fois… et tu reconnais une adresse IP dans un journal de dix mille lignes.
Le piège ? Le point et l'étoile n'ont pas le même sens que dans les jokers du shell. Et pense aux apostrophes autour du motif, pour que le shell n'y touche pas.
Les regex font peur au début. Mais une fois apprivoisées, elles te font gagner des heures, dans grep, sed, awk… et presque tous les langages de programmation.""",

    "processus": """Chaque programme qui tourne sur ta machine est un processus. Ton navigateur, ton terminal, le serveur web… et même les commandes que tu tapes, le temps de leur exécution.
Chaque processus reçoit un numéro unique : son PID. Et tous descendent d'un ancêtre commun, le processus numéro un : systemd, lancé par le noyau au démarrage. C'est un véritable arbre généalogique : chaque processus a un parent, et peut avoir des enfants.
Pour voir ceux qui tournent, une commande : ps. ps tout seul n'affiche que ceux de ton terminal. ps aux les montre tous, avec leur propriétaire, leur consommation de processeur et de mémoire.
Pour une vue en direct, il y a top. La liste se rafraîchit en permanence, triée par consommation : idéal pour repérer le programme qui fait chauffer la machine. Et sa version moderne, htop, ajoute des couleurs, des barres de charge, et se pilote à la souris.
En haut de top, trois nombres : la charge moyenne, sur une, cinq et quinze minutes. Si elle dépasse le nombre de cœurs de ton processeur, la machine est surchargée.
Enfin, chaque processus a une priorité, réglable avec nice. Plus la valeur est haute, plus le processus est gentil… et laisse passer les autres.
Un PID, un parent, une priorité. Voilà la carte d'identité de tout ce qui vit dans ton système.""",

    "signaux": """Comment arrêter un programme sous Linux ? En lui envoyant un signal : un petit message du noyau, qui lui dit quoi faire.
Le plus courant, tu le connais déjà : Contrôle C. Il envoie le signal SIGINT, interruption : le programme s'arrête proprement.
Pour un programme qui tourne ailleurs, il y a la commande kill. Son nom est trompeur : elle envoie un signal, pas forcément mortel. Par défaut, c'est SIGTERM, numéro quinze : une demande polie de terminer. Le programme range ses affaires, enregistre, puis s'arrête.
Et s'il ne répond plus ? kill tiret neuf : SIGKILL. Là, ce n'est plus une demande. Le noyau supprime le processus immédiatement, sans lui laisser le temps de rien. À utiliser en dernier recours.
Plus pratiques, pkill et killall visent un programme par son nom, plutôt que par son PID.
Les signaux servent aussi à mettre en pause. Contrôle Z suspend le programme en cours. La commande jobs liste ce qui est en attente. fg le ramène au premier plan, bg le relance en arrière-plan. Et une esperluette en fin de commande la lance directement en arrière-plan.
Enfin, pour qu'une tâche survive à la fermeture du terminal : nohup, ou mieux, tmux.
Demander avec SIGTERM, forcer avec SIGKILL, suspendre avec Contrôle Z. Tu tiens maintenant les commandes de chaque processus.""",
    "apt": """Sous Windows, on installe un logiciel en le téléchargeant sur un site. Sous Linux, on a mieux : un gestionnaire de paquets.
Un paquet, c'est un logiciel prêt à installer, avec la liste de tout ce dont il a besoin. Et tous ces paquets sont rangés dans des dépôts : d'immenses catalogues en ligne, vérifiés et signés par la distribution. Plus de soixante mille paquets, pour Ubuntu.
Sur Ubuntu, l'outil s'appelle apt. Première étape : sudo apt update. Le système télécharge la liste à jour du catalogue. Rien n'est installé : il apprend juste ce qui existe.
Ensuite : sudo apt install, et le nom du paquet. apt trouve le logiciel, calcule ses dépendances, les télécharge, et installe tout. En une seule commande.
Pour mettre à jour tout le système, applications comprises : sudo apt upgrade. Un seul geste pour tout.
Tu cherches un logiciel ? apt search. Tu veux en savoir plus ? apt show. Tu veux le retirer ? sudo apt remove. Et pour supprimer aussi sa configuration : purge.
Sous le capot, apt s'appuie sur dpkg, l'outil qui manipule les fichiers point deb. Mais au quotidien, c'est apt qui fait tout le travail.
Les dépôts officiels, c'est une garantie : des logiciels vérifiés, signés, et mis à jour automatiquement. Avant de télécharger un programme sur un site inconnu, cherche-le d'abord avec apt.""",

    "snap": """Sur Ubuntu, il existe trois grandes façons d'installer un logiciel. Et chacune a sa philosophie.
Les paquets deb, installés avec apt, sont la méthode historique. Ils partagent les bibliothèques du système : c'est léger et bien intégré. Mais leur version est figée pour toute la durée de vie de ta distribution : parfois, le logiciel a quelques versions de retard.
Les snaps, créés par Canonical, embarquent tout ce dont le logiciel a besoin. Ils sont isolés du reste du système, se mettent à jour tout seuls en arrière-plan, et proposent les dernières versions. Firefox, sur Ubuntu, est un snap. En contrepartie, ils prennent plus de place, et démarrent parfois un peu plus lentement.
Flatpak suit la même idée, mais il est porté par la communauté et fonctionne sur toutes les distributions. Son catalogue s'appelle Flathub.
Et il reste une dernière option : compiler le logiciel depuis son code source. Le maximum de contrôle… mais aussi de travail, et c'est à toi de faire les mises à jour.
Alors, que choisir ? D'abord apt, pour les outils système et la ligne de commande. Un snap ou un flatpak, pour une application de bureau récente. Et les sources, seulement quand il n'existe vraiment rien d'autre.
Trois formats, une seule règle : préfère toujours une source officielle et de confiance.""",

    "variables": """Ton shell garde en mémoire tout un tas d'informations : ton nom, ton dossier personnel, ta langue… Ce sont des variables.
Une variable, c'est un nom associé à une valeur. Pour la lire, on met un dollar devant son nom. echo dollar HOME affiche ton dossier personnel. echo dollar USER, ton nom d'utilisateur.
Pour créer la tienne, c'est simple : un nom, le signe égal, une valeur. Sans espaces autour du égal ! Sinon, le shell croit que tu lances une commande.
Certaines variables sont spéciales : les variables d'environnement. Avec le mot export, une variable est transmise à tous les programmes que lance ton shell. La commande env les affiche toutes.
Et parmi elles, la plus importante, c'est PATH. Quand tu tapes ls, comment le shell sait-il où trouver le programme ? Il fouille, un par un, les dossiers listés dans PATH, séparés par des deux-points. Le premier qui contient ls gagne.
Tu as écrit tes propres scripts dans un dossier bin, chez toi ? Ajoute-le au PATH, et tu pourras les lancer de n'importe où, comme de vraies commandes.
Attention : une variable créée dans le terminal disparaît à sa fermeture. Pour la garder, il faut l'écrire dans un fichier de configuration. C'est le sujet de la prochaine vidéo.
Un dollar pour lire, un égal pour écrire, export pour partager. Et PATH pour trouver toutes les commandes.""",

    "bashrc": """Ton terminal peut devenir vraiment le tien. Et tout se passe dans un fichier caché : point bashrc, dans ton dossier personnel.
À chaque ouverture d'un terminal, Bash lit ce fichier et exécute ce qu'il contient. C'est là qu'on range ses réglages, pour qu'ils soient permanents.
Premier réflexe : les alias. Un alias, c'est un raccourci. alias ll égal ls tiret l a, et tu n'as plus que deux lettres à taper. alias maj égal sudo apt update, et sudo apt upgrade. Tu tapes maj, et ton système se met à jour.
Deuxième réflexe : les variables. Une ligne export, pour ajouter ton dossier de scripts au PATH, et elle sera là à chaque session.
Troisième réflexe : l'invite. La variable PS1 décide de ce qu'affiche ton prompt : ton nom, la machine, le dossier, l'heure, des couleurs… Tout est personnalisable.
Après avoir modifié le fichier, une seule commande pour appliquer les changements sans fermer le terminal : source point bashrc.
Et si tu veux aller plus loin, il existe d'autres shells. Zsh, avec le célèbre Oh My Zsh, ajoute des thèmes, des suggestions, et des centaines d'extensions.
Un conseil : fais toujours une copie de ton bashrc avant de le modifier. Et ajoute un commentaire au-dessus de chaque réglage : dans six mois, tu seras content de savoir pourquoi il est là.""",

    "demarrage": """Tu appuies sur le bouton Power. Quelques secondes plus tard, ton bureau Ubuntu est là. Mais entre les deux, c'est une véritable course de relais.
Premier coureur : le firmware de la carte mère, l'UEFI. Il vérifie le matériel, puis cherche sur le disque un programme de démarrage.
Deuxième coureur : GRUB, le chargeur d'amorçage. C'est lui qui affiche le menu, si tu as plusieurs systèmes. Son travail : charger en mémoire le noyau Linux.
Troisième coureur : le noyau. Il prend le contrôle du processeur, de la mémoire et des périphériques. Pour trouver le vrai disque, il s'aide d'un petit système de secours, chargé en mémoire : l'initramfs.
Une fois la partition racine montée, le noyau lance le tout premier programme. Celui qui porte le numéro un : systemd.
Quatrième coureur, et chef d'orchestre : systemd démarre tous les services, en parallèle. Le réseau, le son, les journaux… et enfin, l'écran de connexion.
Tu entres ton mot de passe : la course est terminée. Le tout, en quelques secondes.
Pour savoir combien de temps a pris chaque étape, une commande : systemd-analyze. Et avec systemd-analyze blame, tu vois quels services ralentissent ton démarrage.
Si un jour ta machine refuse de démarrer, souviens-toi de ce relais : le dernier message affiché te dit où la course s'est arrêtée.
UEFI, GRUB, noyau, systemd : quatre relais, et ton système est prêt.""",

    "systemd": """Sur ton système, des dizaines de programmes tournent en permanence, sans fenêtre : le réseau, l'horloge, les journaux… Ce sont des services. Et c'est systemd qui les gouverne.
Pour leur parler, une seule commande : systemctl.
systemctl status, suivi du nom d'un service, te dit tout : est-il actif ? Depuis quand ? Et il affiche ses dernières lignes de journal. Le petit point vert signifie que tout va bien.
Pour démarrer un service : sudo systemctl start. Pour l'arrêter : stop. Et après avoir changé sa configuration : restart.
Attention, piège classique ! start démarre le service maintenant, mais pas au prochain allumage. Pour qu'il démarre à chaque fois, il faut enable. Et disable, pour l'en empêcher. start, c'est pour maintenant. enable, c'est pour toujours.
Chaque service est décrit par un petit fichier texte : une unité. Elle dit quel programme lancer, après quoi, et quoi faire s'il plante. Tu peux même écrire les tiennes.
Et quand un service refuse de démarrer ? Direction les journaux. journalctl affiche les messages de tout le système. Avec tiret u et le nom du service, tu ne vois que les siens. Et avec tiret f, tu les suis en direct.
Un service en panne ? Le réflexe : status, puis journalctl. La réponse est presque toujours écrite dedans.""",

    "disques": """Un disque neuf, tout juste branché. Comment Linux le rend-il utilisable ? En trois étapes : partitionner, formater, monter.
D'abord, l'inventaire. La commande lsblk dessine tes disques et leurs partitions, en arbre. Sous Linux, les disques ont des noms : sda pour le premier, sdb pour le deuxième… Et dans une machine virtuelle, souvent vda. Les partitions ajoutent un numéro : sda1, sda2.
Étape un : partitionner. On découpe le disque en zones, avec fdisk ou parted. Comme on divise un terrain en parcelles.
Étape deux : formater. Avec mkfs, on installe un système de fichiers sur la partition : la structure qui range les fichiers. Sous Linux, le grand classique, c'est ext4.
Étape trois : monter. Sous Linux, pas de lettre D ou E. La partition se greffe dans l'arbre, sur un dossier vide : le point de montage. Avec la commande mount, ton disque apparaît, par exemple, dans slash mnt slash data.
Mais au redémarrage, le montage disparaît. Pour le rendre permanent, on ajoute une ligne dans le fichier slash etc slash fstab. Avec l'UUID de la partition, son identifiant unique, plutôt que son nom.
Attention : une erreur dans fstab peut empêcher ta machine de démarrer. Après chaque modification, vérifie avec sudo mount tiret a.
Partitionner, formater, monter : trois gestes, et n'importe quel disque rejoint ton arbre.""",

    "espace": """Message d'erreur : plus d'espace disque. Pas de panique : trois commandes pour mener l'enquête.
Premier indice : df. Avec tiret h, pour des tailles lisibles, en gigaoctets. df affiche chaque système de fichiers monté : sa taille, l'espace utilisé, l'espace libre, et le pourcentage. Au-dessus de quatre-vingt-dix pour cent, il est temps d'agir.
Deuxième indice : du. df te dit quel disque est plein ; du te dit qui le remplit. du tiret s h, suivi d'un dossier, donne son poids total. Combiné avec sort, il classe les dossiers du plus lourd au plus léger. Les coupables habituels : les journaux dans slash var slash log, le cache d'apt, et les vieux téléchargements.
Pour une enquête plus confortable, installe ncdu : une interface interactive où tu navigues dans les dossiers, triés par taille.
Et il existe un espace un peu particulier : le swap. Quand la mémoire vive est pleine, Linux y déplace les données les moins utilisées. C'est un débordement, sur le disque. Pratique, mais beaucoup plus lent que la RAM. La commande free tiret h affiche la mémoire et le swap.
Pour faire le ménage : sudo apt autoremove, puis sudo apt clean. Ils suppriment ce dont apt n'a plus besoin.
df pour voir, du pour trouver… et ensuite, tu fais le ménage.""",
    "reseau": """Tu tapes une adresse dans ton navigateur. Une fraction de seconde plus tard, la page s'affiche. Mais que s'est-il passé, en coulisses ?
D'abord, ta machine a besoin d'une adresse : une adresse IP. Comme une adresse postale, mais pour les ordinateurs. La commande ip a affiche la tienne : par exemple, dix point zéro point deux point quinze. Elle t'a été attribuée automatiquement par le routeur, grâce au DHCP.
Deuxième problème : tu as tapé un nom, pas une adresse. Or les ordinateurs ne parlent qu'en chiffres. C'est le rôle du DNS : l'annuaire d'Internet. Il traduit un nom, comme ubuntu point com, en adresse IP. La commande dig te montre cette traduction.
Ta demande part alors vers la passerelle : ton routeur, la porte de sortie vers Internet. La commande ip route te dit qui elle est.
Enfin, sur le serveur, une seule adresse héberge plusieurs services. Pour savoir à qui parler, on ajoute un numéro de port : quatre cent quarante-trois pour le web sécurisé, vingt-deux pour SSH. La commande ss tiret t u l n liste les ports sur lesquels ta machine écoute.
Quand quelque chose ne marche pas, remonte le chemin. ping vérifie qu'une machine répond. ping vers une adresse IP fonctionne, mais pas vers un nom ? Le coupable, c'est le DNS.
Adresse, nom, passerelle, port : quatre questions, et le réseau n'a plus de secret.""",

    "ufw": """Ta machine est branchée au réseau. Mais qui a le droit d'entrer ? C'est le travail du pare-feu.
Imagine un vigile, à l'entrée d'un immeuble. Chaque connexion qui arrive frappe à une porte : un port. Le vigile consulte sa liste. Autorisé ? Il ouvre. Pas sur la liste ? Refusé.
Sous Linux, le vrai vigile s'appelle netfilter, au cœur du noyau. Mais ses règles sont complexes. Alors Ubuntu fournit un outil bien plus simple : ufw, le pare-feu simplifié.
Au départ, il est désactivé. La commande sudo ufw status te le confirme : inactif.
La bonne stratégie : tout refuser à l'entrée, tout autoriser à la sortie. Puis n'ouvrir que ce dont tu as besoin. Pour autoriser SSH : sudo ufw allow ssh. Pour un site web : sudo ufw allow quatre-vingts, slash tcp.
Attention, piège classique ! Si tu administres une machine à distance, autorise SSH avant d'activer le pare-feu. Sinon, tu fermes la porte… et tu restes dehors.
Ensuite seulement : sudo ufw enable. Le vigile prend son poste, et il le reprendra à chaque démarrage.
sudo ufw status verbose affiche toutes les règles. Pour en retirer une : ufw delete, suivi de la règle.
Et pour vérifier depuis l'extérieur, la commande nmap liste les ports ouverts d'une machine. Uniquement sur les tiennes !
Tout fermer, puis n'ouvrir que le strict nécessaire : c'est la règle d'or de la sécurité.""",

    "ssh": """Un serveur, c'est souvent une machine sans écran, dans un centre de données à l'autre bout du monde. Alors, comment l'administrer ? Avec SSH.
SSH, c'est un terminal à distance. Tu tapes des commandes sur ton ordinateur, et elles s'exécutent sur le serveur. Tout le trajet est chiffré : personne ne peut lire ce qui passe, pas même ton mot de passe.
Côté serveur, un service écoute sur le port vingt-deux : sshd. Sur Ubuntu, il s'installe avec sudo apt install openssh-server.
Côté client, une seule commande : ssh, suivi d'un nom d'utilisateur, d'une arobase, et de l'adresse du serveur. Elle existe aussi sous Windows, dans PowerShell.
À la première connexion, SSH te montre l'empreinte du serveur, et te demande si tu lui fais confiance. Tu réponds yes : il s'en souviendra. Si un jour cette empreinte change, SSH t'alerte. Ça peut être une réinstallation… ou quelqu'un qui se fait passer pour ton serveur.
Ensuite, ton mot de passe. Et l'invite change : tu es sur le serveur ! Pour revenir chez toi : exit.
Et pour une machine virtuelle ? Dans VirtualBox, en mode NAT, ajoute une redirection de port : le port deux mille deux de ton ordinateur vers le port vingt-deux de la VM. Puis ssh tiret p deux mille deux, vers localhost.
Pour copier des fichiers, scp et rsync passent par le même tunnel chiffré.
Un terminal, n'importe où dans le monde : c'est ça, SSH.""",

    "cles": """Taper ton mot de passe à chaque connexion SSH ? Pénible. Et surtout, risqué : un mot de passe, ça se devine. Heureusement, il existe bien mieux : les clés SSH.
Le principe est simple : une paire de clés, liées par les mathématiques. Une clé publique, qui fonctionne comme un cadenas. Et une clé privée : la seule capable de l'ouvrir.
Pour créer ta paire : ssh-keygen tiret t ed25519. Deux fichiers apparaissent dans ton dossier point ssh. La clé privée, id ed25519 : elle ne quitte jamais ta machine. Et la clé publique, qui finit par point pub : celle-là, tu peux la donner à tout le monde.
Tu poses ensuite ton cadenas sur le serveur, avec ssh-copy-id. Ta clé publique rejoint le fichier authorized keys : la liste des cadenas acceptés.
À la connexion suivante, le serveur te lance un défi, que seule ta clé privée peut relever. Défi réussi : tu entres. Et aucun mot de passe n'a circulé sur le réseau.
Protège ta clé privée par une phrase de passe : si on te la vole, elle restera inutilisable.
Dernière étape, la plus sûre : interdire les mots de passe sur le serveur. Dans le fichier sshd config, passe PasswordAuthentication à no, puis redémarre le service. Mais avant, vérifie que ta clé fonctionne ! Sinon, tu restes dehors.
Un cadenas sur le serveur, une clé dans ta poche : plus sûr, et plus pratique.""",

}


def generer(voix: str, texte: str) -> bytes:
    corps = {
        "model": MODELE,
        "input": [{
            "type": "user_input",
            "content": [{
                "type": "text",
                "text": texte,
                "annotations": [{"type": "speech_metadata", "style": STYLE}],
            }],
        }],
        "response_format": {"type": "audio"},
        "generation_config": {"speech_config": [{"voice": voix}]},
    }
    req = urllib.request.Request(
        "https://generativelanguage.googleapis.com/v1beta/interactions",
        data=json.dumps(corps).encode("utf-8"),
        headers={"x-goog-api-key": CLE, "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            rep = json.load(r)
    except urllib.error.HTTPError as e:
        raise SystemExit(f"HTTP {e.code}: {e.read().decode('utf-8', 'replace')[:800]}")
    audios = [
        c for s in rep.get("steps", []) if s.get("type") == "model_output"
        for c in s.get("content", []) if c.get("type") == "audio"
    ]
    if not audios:
        raise SystemExit("Réponse sans audio : " + json.dumps(rep)[:800])
    return base64.b64decode(audios[-1]["data"])


if __name__ == "__main__":
    cle, voix = sys.argv[1], sys.argv[2]
    sortie = sys.argv[3] if len(sys.argv) > 3 else f"{RACINE}/voix/{cle}-{voix}.wav"
    print(f"{cle}: {len(TEXTES[cle].split())} mots")
    data = generer(voix, TEXTES[cle])
    with open(sortie, "wb") as f:
        f.write(data)
    try:
        with wave.open(io.BytesIO(data)) as w:
            print(f"{sortie}: {w.getnframes() / w.getframerate():.1f} s")
    except wave.Error:
        print(f"{sortie}: {len(data)} octets (pas un WAV reconnu)")
