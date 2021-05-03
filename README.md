# theke
*Lire et étudier la Bible et l'enseignement de l'Église.*

## Installation

**Debian / Ubuntu**

Installer GTK+ et PyGObject.

* `sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0`

Installer Sword.

* `sudo apt install python3-sword`

Autres paquets requis : Jinja2.

* `pip3 install Jinja2`

## Utilisation

### Dépôts Sword

Theke ne sait pas encore télécharger et installer les modules Sword. Il faut passer par un logiciel tiers pour le faire (ex. [Xiphos](https://xiphos.org/)).

**Modules d'intérêts.**

Nom du module | Nom du dépôt | Description
------------- | ------------ | -----------
MorphGNT | CrossWire > Textes bibliques > Κοινὴ Ἑλληνική | Morphologically Parsed Greek New Testament based on the SBLGNT
EarlyFathers | Xiphos > Livres > English | -

### Theke

Pour lancer Theke, exécuter la commande suivante depuis le répertoire du projet.

* `python3 theke.py`