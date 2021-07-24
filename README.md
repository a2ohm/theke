# theke
*Lire et étudier la Bible et l'enseignement de l'Église.*

## Installation

Theke s'appuie sur diverses bibliothèques que vous devez avoir sur votre ordinateur pour utiliser l'application.

### SWORD

**Debian / Ubuntu (⩾ 21.04)**

Installer Sword. Si le paquet `python3-sword` n'est pas disponible pour votre distribution (par exemple pour les versions d'Ubuntu inférieures à la version 21.04), consultez la section suivante.

* `sudo apt install python3-sword`

**Debian / Ubuntu (< 21.04)**

Même si le packet `python3-sword` n'est pas disponible pour votre distribution, vous pouvez toujours le compiler par vous même.

Installer les utilitaires et les libraires nécessaires à la compilation de sword.

* `sudo apt install subversion build-essential autotools-dev pkg-config libz-dev libclucene-dev libicu-dev libcurl4-gnutls-dev libtool m4 automake cmake swig`

Créer un dossier de travail et télécharger le code source.

* `mkdir sword && cd sword`
* `svn co http://crosswire.org/svn/sword/trunk sources`

Compiler et installer sword.
* `mkdir build && cd build`
* `cmake -DLIBSWORD_LIBRARY_TYPE="Shared" -DCMAKE_INSTALL_PREFIX="/usr" -DSWORD_PYTHON_3:BOOL=TRUE ../sources`
* `make -j4`
* `sudo make install`

### GTK+ et PyGObject

Installer ensuite GTK+ et PyGObject.

* `sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0`

### Autres bibliothèques

Autres paquets requis : Jinja2.

* `pip3 install Jinja2`

### Theke

Il ne vous reste plus qu'à télécharger le code source de Theke.

* `git clone https://github.com/a2ohm/theke.git`

## Utilisation

### Dépôts Sword

Theke ne sait pas encore télécharger et installer les modules Sword. Il faut passer par un logiciel tiers pour le faire (ex. [Xiphos](https://xiphos.org/)).

**Modules d'intérêts.**

Nom du module | Nom du dépôt | Description
------------- | ------------ | -----------
OSHB | CrossWire > Texte bibliques > ﬠברית מקראית | Open Scriptures Hebrew Bible
EarlyFathers | Xiphos > Livres > English | -
MorphGNT | CrossWire > Textes bibliques > Κοινὴ Ἑλληνική | Morphologically Parsed Greek New Testament based on the SBLGNT

### Theke

Pour lancer Theke, exécuter la commande suivante depuis le répertoire du projet.

* `python3 theke.py`