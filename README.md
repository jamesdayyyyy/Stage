# Système de Contrôle Qualité par Vision — README Complet

> **Auteur :** James DAY  
> **Dernière mise à jour :** Juin 2026  
> **Contexte :** Application de contrôle qualité industriel par vision (template matching OpenCV) sur ligne de production automobile. Déployée sur un réseau de Raspberry Pi communicant avec un automate Siemens S7.

---

## Table des matières

1. [Vue d'ensemble du système](#1-vue-densemble-du-système)
2. [Architecture technique](#2-architecture-technique)
3. [Matériel requis](#3-matériel-requis)
4. [Prérequis logiciels](#4-prérequis-logiciels)
5. [Structure des fichiers du projet](#5-structure-des-fichiers-du-projet)
6. [Configuration réseau](#6-configuration-réseau)
7. [Installation et déploiement](#7-installation-et-déploiement)
   - [7.1 Raspberry Pi principal (pimain)](#71-raspberry-pi-principal-pimain)
   - [7.2 Raspberry Pi esclaves](#72-raspberry-pi-esclaves)
   - [7.3 Scripts embarqués sur les Pi esclaves](#73-scripts-embarqués-sur-les-pi-esclaves)
8. [Configuration du système — config.py](#8-configuration-du-système--configpy)
   - [8.1 Paramètres réseau Raspberry Pi](#81-paramètres-réseau-raspberry-pi)
   - [8.2 Paramètres caméras](#82-paramètres-caméras)
   - [8.3 Paramètres automate (PLC Siemens S7)](#83-paramètres-automate-plc-siemens-s7)
   - [8.4 Paramètres de stockage](#84-paramètres-de-stockage)
   - [8.5 Paramètres de vision](#85-paramètres-de-vision)
   - [8.6 Mappings véhicules et pièces](#86-mappings-véhicules-et-pièces)
9. [Gestion des zones de contrôle (CSV)](#9-gestion-des-zones-de-contrôle-csv)
   - [9.1 Format du fichier CSV](#91-format-du-fichier-csv)
   - [9.2 Créer une zone](#92-créer-une-zone)
   - [9.3 Modifier une zone](#93-modifier-une-zone)
   - [9.4 Supprimer une zone](#94-supprimer-une-zone)
   - [9.5 Zones avec variantes](#95-zones-avec-variantes)
10. [Gestion des images de référence](#10-gestion-des-images-de-référence)
    - [10.1 Structure des dossiers de référence](#101-structure-des-dossiers-de-référence)
    - [10.2 Nomenclature des fichiers de référence](#102-nomenclature-des-fichiers-de-référence)
    - [10.3 Créer une nouvelle référence](#103-créer-une-nouvelle-référence)
    - [10.4 Mettre à jour une référence](#104-mettre-à-jour-une-référence)
    - [10.5 Références multiples par zone](#105-références-multiples-par-zone)
11. [Déploiement sur un nouveau site](#11-déploiement-sur-un-nouveau-site)
    - [11.1 Checklist pré-déploiement](#111-checklist-pré-déploiement)
    - [11.2 Adaptations réseau](#112-adaptations-réseau)
    - [11.3 Adaptations automate S7](#113-adaptations-automate-s7)
    - [11.4 Ajout de nouveaux types de véhicules](#114-ajout-de-nouveaux-types-de-véhicules)
    - [11.5 Ajout de nouvelles caméras et Pi esclaves](#115-ajout-de-nouvelles-caméras-et-pi-esclaves)
    - [11.6 Ajout de nouvelles pièces/variantes](#116-ajout-de-nouvelles-piècesvariantes)
12. [Maintenance](#12-maintenance)
    - [12.1 Maintenance matérielle](#121-maintenance-matérielle)
    - [12.2 Maintenance logicielle](#122-maintenance-logicielle)
    - [12.3 Gestion de la base de données](#123-gestion-de-la-base-de-données)
    - [12.4 Gestion du stockage images](#124-gestion-du-stockage-images)
13. [Troubleshooting exhaustif](#13-troubleshooting-exhaustif)
    - [13.1 Problèmes réseau / SSH](#131-problèmes-réseau--ssh)
    - [13.2 Problèmes automate / PLC S7](#132-problèmes-automate--plc-s7)
    - [13.3 Problèmes caméras / capture](#133-problèmes-caméras--capture)
    - [13.4 Problèmes vision / analyse d'image](#134-problèmes-vision--analyse-dimage)
    - [13.5 Problèmes base de données](#135-problèmes-base-de-données)
    - [13.6 Problèmes stockage](#136-problèmes-stockage)
    - [13.7 Problèmes interface graphique (UI)](#137-problèmes-interface-graphique-ui)
    - [13.8 Problèmes de performance](#138-problèmes-de-performance)
14. [Nomenclature des fichiers images archivés](#14-nomenclature-des-fichiers-images-archivés)
15. [Référence rapide des commandes utiles](#15-référence-rapide-des-commandes-utiles)

---

## 1. Vue d'ensemble du système

Ce système effectue un **contrôle qualité automatisé** par vision sur une ligne de production automobile. À chaque passage d'un véhicule dans la zone de contrôle :

1. L'**automate Siemens S7** détecte la présence du véhicule et transmet ses données (VIS, type, motorisation, variantes de pièces).
2. Les **Raspberry Pi esclaves** déclenchent leurs caméras et capturent les photos des zones à contrôler.
3. Les images sont rapatriées via SSH/SFTP sur la **Pi principale** et analysées par **OpenCV** (template matching).
4. Les résultats (OK/NOK par zone) sont **renvoyés à l'automate**, stockés en **base de données SQLite**, archivés sur **HDD**, et affichés sur l'**interface Tkinter**.

---

## 2. Architecture technique

```
┌─────────────────────────────────────────────────────────────┐
│                    RASPBERRY PI PRINCIPAL                    │
│                   10.226.178.51 (pimain)                    │
│                                                             │
│  ┌────────────┐   ┌─────────────┐   ┌──────────────────┐   │
│  │  Processus │   │  Processus  │   │    Processus UI   │   │
│  │  Réseau    │──▶│  Vision x2  │──▶│  (Tkinter)       │   │
│  │ reseau.py  │   │  vision.py  │   │  interface.py    │   │
│  └────────────┘   └─────────────┘   └──────────────────┘   │
│       │  ▲                │                                  │
│  SSH  │  │ S7/snap7       │ SQLite + HDD                    │
└───────┼──┼────────────────┼────────────────────────────────┘
        │  │                │
        │  │                ▼
        │  │    ┌──────────────────────┐
        │  └────│  AUTOMATE SIEMENS S7  │
        │       │  10.226.178.1         │
        │       │  DB102 (lecture)      │
        │       │  DB105 (écriture)     │
        │       └──────────────────────┘
        │
        ▼
┌─────────────────┐    ┌─────────────────┐
│  Pi ESCLAVE 1   │    │  Pi ESCLAVE 2   │
│  10.226.178.53  │    │  10.226.178.52  │
│  (rasp1)        │    │  (ingpi)        │
│  Caméras 1, 2   │    │  Caméra 3       │
└─────────────────┘    └─────────────────┘
```

**Flux de données par processus (multiprocessing) :**

```
[Réseau] → queue_reseau_vers_vision → [Vision Core3 / Core4] → queue_vision_vers_ui → [UI]
                                                                         │
                                                                [BDD SQLite + HDD]
                                                                         │
                                                                  [Automate S7]
```

---

## 3. Matériel requis

| Composant | Description | Qté (config actuelle) |
|---|---|---|
| Raspberry Pi 4 ou 5 | Pi principale (pimain) | 1 |
| Raspberry Pi 4 ou 5 | Pi esclaves (rasp1, ingpi…) | 2+ |
| Caméras USB ou CSI | Compatible V4L2 / picamera2 | 1 par point de contrôle |
| Câbles réseau Ethernet | Pour le réseau industriel | 1 par Pi |
| Switch réseau | Réseau local industriel | 1 |
| Disque dur / SSD USB | Archivage images sur Pi principale | 1 |
| Écran + clavier/souris | Pour l'interface Tkinter | 1 |
| Automate Siemens S7-1200/1500 | Communication S7 (snap7) | 1 |

> **Note :** Le projet prévoit jusqu'à 14 caméras (8 Pi esclaves). Seules 3 caméras sont actives dans la configuration courante. Les entrées commentées dans `config.py` indiquent les Pi/caméras à activer ultérieurement.

---

## 4. Prérequis logiciels

### Sur la Pi principale (`pimain`)

```bash
# Système
sudo apt update && sudo apt upgrade -y
sudo apt install python3-pip python3-tk python3-opencv -y

# Bibliothèques Python
pip3 install snap7          # Communication automate S7
pip3 install paramiko       # SSH vers Pi esclaves
pip3 install opencv-python  # Vision / template matching
pip3 install numpy          # Calcul matriciel (dépendance OpenCV)

# Vérification
python3 -c "import snap7; import paramiko; import cv2; print('OK')"
```

> **Important :** La bibliothèque `snap7` nécessite aussi la librairie système `libsnap7` :
> ```bash
> sudo apt install libsnap7-1 libsnap7-dev -y
> ```

### Sur chaque Pi esclave

```bash
# Selon le type de caméra utilisée
sudo apt install python3-picamera2 -y   # Caméra CSI (module officiel Pi)
# OU
pip3 install opencv-python              # Caméra USB via V4L2
```

Les Pi esclaves n'ont besoin que des scripts `prise_photo.py` et `rasp_camera_keepalive.py` (voir section 7.3).

---

## 5. Structure des fichiers du projet

```
projet_vision/
│
├── main.py                    # Point d'entrée — lance tous les processus
├── config.py                  # Configuration centralisée (IPs, seuils, mappings)
├── reseau.py                  # Gestion SSH, capture images, lecture automate
├── vision.py                  # Analyse d'images (template matching OpenCV)
├── interface.py               # Interface graphique Tkinter
├── helper_affichage.py        # Fonctions d'affichage / rendu UI
├── helper_automate.py         # Communication S7 (lecture/écriture DB automate)
├── helper_database.py         # CRUD base de données SQLite
├── helper_storage.py          # Gestion RAM cache + archivage HDD
├── helper_csv.py              # CRUD fichiers CSV de zones
│
├── historique_production.db   # Base de données SQLite (créée automatiquement)
│
├── zones/                     # Définitions des zones par véhicule
│   ├── P51_ICE.csv
│   ├── P51_PHEV.csv
│   ├── P52_ICE.csv
│   └── ...                    # Un CSV par couple (véhicule, motorisation)
│
└── ref/                       # Images de référence par véhicule
    ├── P51_ICE/
    │   ├── zone_1_nom.jpg     # Référence pour la zone 1 sans variante
    │   ├── zone_2_nom.jpg
    │   └── 01/                # Sous-dossier pour la variante "01"
    │       └── zone_3_nom.jpg
    ├── P51_PHEV/
    └── ...
```

Les images sont stockées dans :
- **RAM temporaire :** `/dev/shm/` — images brutes nommées `cam{N}.jpg`
- **HDD permanent :** `./{YYYY}/{MM}/{DD}/` depuis `HDD_PATH` configuré

---

## 6. Configuration réseau

Le réseau doit permettre :
- La **Pi principale** de joindre toutes les **Pi esclaves** en SSH (port 22)
- La **Pi principale** de joindre l'**automate** (port S7 : TCP 102)
- Tous les équipements sur le même **sous-réseau** ou avec routage approprié

**Configuration actuelle :**

| Équipement | IP | Login | Rôle |
|---|---|---|---|
| Pi principale | 10.226.178.51 | pimain / raspberry1 | Analyse, UI, BDD |
| Pi esclave 1 | 10.226.178.53 | rasp1 / raspberry1 | Caméras 1, 2 |
| Pi esclave 2 | 10.226.178.52 | ingpi / raspberry1 | Caméra 3 |
| Automate S7 | 10.226.178.1 | — | PLC Siemens |

> ⚠️ **Sécurité :** Les mots de passe SSH sont en clair dans `config.py`. Sur un déploiement industriel, préférer les clés SSH ou un coffre-fort de secrets.

**Vérifications réseau depuis la Pi principale :**
```bash
ping 10.226.178.53      # Test connectivité Pi esclave 1
ping 10.226.178.52      # Test connectivité Pi esclave 2
ping 10.226.178.1       # Test connectivité automate
ssh rasp1@10.226.178.53 # Test SSH manuel Pi esclave 1
```

---

## 7. Installation et déploiement

### 7.1 Raspberry Pi principal (pimain)

```bash
# 1. Cloner ou copier le projet
cp -r projet_vision/ /home/pimain/projet_vision/
cd /home/pimain/projet_vision/

# 2. Installer les dépendances
sudo apt install libsnap7-1 libsnap7-dev python3-tk python3-opencv -y
pip3 install snap7 paramiko numpy

# 3. Créer les dossiers nécessaires
mkdir -p zones ref
# Le dossier /dev/shm existe déjà (tmpfs en RAM sur Linux)

# 4. Vérifier la configuration dans config.py (voir section 8)

# 5. Lancer l'application
python3 main.py
```

**Lancement automatique au démarrage (optionnel) :**
```bash
# Créer un service systemd
sudo nano /etc/systemd/system/vision_qualite.service
```
Contenu du service :
```ini
[Unit]
Description=Controle Qualite Vision
After=network.target

[Service]
ExecStart=/usr/bin/python3 /home/pimain/projet_vision/main.py
WorkingDirectory=/home/pimain/projet_vision
User=pimain
Restart=on-failure
RestartSec=10
Environment=DISPLAY=:0

[Install]
WantedBy=multi-user.target
```
```bash
sudo systemctl enable vision_qualite
sudo systemctl start vision_qualite
```

---

### 7.2 Raspberry Pi esclaves

Chaque Pi esclave n'a besoin que de deux scripts dans son répertoire home :
- `prise_photo.py` — déclenche la capture et enregistre dans `/dev/shm/`
- `rasp_camera_keepalive.py` — maintient les caméras initialisées en permanence

```bash
# Depuis la Pi principale, copier les scripts vers chaque esclave
scp prise_photo.py rasp1@10.226.178.53:/home/rasp1/
scp rasp_camera_keepalive.py rasp1@10.226.178.53:/home/rasp1/
scp prise_photo.py ingpi@10.226.178.52:/home/ingpi/
scp rasp_camera_keepalive.py ingpi@10.226.178.52:/home/ingpi/
```

**Vérification sur chaque esclave :**
```bash
ssh rasp1@10.226.178.53 "python3 ~/prise_photo.py && ls /dev/shm/cam*.jpg"
```

---

### 7.3 Scripts embarqués sur les Pi esclaves

Ces scripts ne font **pas** partie du dépôt principal mais sont indispensables.

**`prise_photo.py`** (exemple de structure attendue) :
```python
# Ce script doit :
# 1. Capturer une image par caméra connectée à cette Pi
# 2. Enregistrer chaque image dans /dev/shm/cam{NUMERO}.jpg
# 3. Quitter proprement (stdout vide = succès pour reseau.py)
# Adapter le numéro de caméra selon la Pi (Config.RASPBERRY -> CAM)
```

**`rasp_camera_keepalive.py`** (exemple de structure attendue) :
```python
# Ce script doit :
# 1. Initialiser les caméras au démarrage (évite la latence à la première capture)
# 2. Tourner en boucle infinie pour maintenir les handles ouverts
# Il est lancé en arrière-plan (nohup) par reseau.py à chaque connexion SSH
```

> ⚠️ **Important :** La détection d'erreur dans `reseau.py` se fait en vérifiant que `stderr` est vide. Tout print sur stderr dans `prise_photo.py` sera interprété comme une erreur et annulera le transfert.

---

## 8. Configuration du système — `config.py`

Toutes les modifications de configuration se font **uniquement** dans ce fichier. Ne pas modifier les autres fichiers Python pour changer des paramètres.

### 8.1 Paramètres réseau Raspberry Pi

```python
RASPBERRY = [
    {
        "NUMERO": 0,         # Numéro unique (0 = Pi principale, ignorée par check_capture)
        "IP": "10.226.178.51",
        "USERNAME": "pimain",
        "PASSWORD": "raspberry1",
        "CAM": [],           # Caméras connectées à CETTE Pi (vide pour la principale)
    },
    {
        "NUMERO": 1,
        "IP": "10.226.178.53",
        "USERNAME": "rasp1",
        "PASSWORD": "raspberry1",
        "CAM": [1, 2],       # Cette Pi gère les caméras 1 et 2
    },
]
```

> **Règle :** La Pi avec `"NUMERO": 0` est toujours exclue des connexions SSH (c'est la Pi principale qui s'y connecte soi-même).

### 8.2 Paramètres caméras

```python
CAM = [
    {
        "NUMERO": 1,                          # ID unique de la caméra
        "VARIANTE_REQUISE": "code_ecran",     # Clé dans les variantes automate (peut être vide "")
        "ACTIVE": True,                       # Activer/désactiver sans supprimer
        "NOM": "Ecran sous moteur G",         # Nom affiché dans l'UI
    },
    {
        "NUMERO": 2,
        "TYPE": False,                        # Non utilisé actuellement
        "ACTIVE": True,
        "NOM": "Ecran sous moteur D",
    },
]
```

**`VARIANTE_REQUISE`** : Si cette caméra doit contrôler une pièce dont la variante dépend d'un code automate, indiquer ici la clé dans `AUTOMATE_DB_LECTURE`. Le système récupérera automatiquement la bonne variante et ignorera les zones CSV qui ne correspondent pas.

### 8.3 Paramètres automate (PLC Siemens S7)

```python
AUTOMATE_IP = "10.226.178.1"      # Adresse IP de l'automate
AUTOMATE_DB = 102                  # Numéro du DB de lecture (données véhicule)
AUTOMATE_TAILLE_LECTURE = 36       # Taille en octets du bloc à lire
AUTOMATE_DB_ENVOIE = 105           # Numéro du DB d'écriture (résultats vision)
AUTOMATE_NB_MAX_DEFAUTS = 15       # Nombre max de défauts remontés
AUTOMATE_OCTETS_DEFAUTS = 34       # Taille d'une entrée défaut (string 32 chars + 2 octets)
AUTOMATE_RACK = 0                  # Rack physique (0 en général)
AUTOMATE_SLOT = 1                  # Slot CPU (1 pour S7-1200/1500)
```

**Structure du DB de lecture (DB102) :**

| Offset (octet) | Contenu | Taille |
|---|---|---|
| 0, bit 0 | `vh_dans_pas` (booléen présence véhicule) | 1 bit |
| 2 | `vis` (numéro VIS véhicule) | string |
| 12 | `type_vh` | string |
| 18 | `silhouette` | string |
| 24 | `code_moteur` (code cycle motorisation) | string |
| 30 | `code_ecran` (code cycle variante écran) | string |

Ces offsets sont définis dans `AUTOMATE_DB_LECTURE`.

**Structure du DB d'écriture (DB105) :**

| Offset | Contenu |
|---|---|
| 0, bit 0 | Erreur système |
| 0, bit 1 | Véhicule OK |
| 0, bit 2 | Véhicule NOK |
| 2+ | Tableau de strings (noms des zones en défaut) |

### 8.4 Paramètres de stockage

```python
DATABASE_PATH = "./historique_production.db"  # Base de données SQLite
TEMPORAIRE_PATH = "/dev/shm"                  # RAM temporaire (tmpfs Linux)
HDD_PATH = "."                                # Racine archivage HDD (modifier pour pointer vers le disque monté)
ZONES_CSV_PATH = "./zones"                    # Dossier des CSV de zones
REF_PATH = "./ref"                            # Dossier des images de référence
CACHE_LIMIT = 3                               # Nb de véhicules gardés en RAM simultanément
```

> **Pour un HDD externe monté sur `/mnt/hdd` :**
> ```python
> HDD_PATH = "/mnt/hdd/controle_qualite"
> ```

### 8.5 Paramètres de vision

```python
MARGE_RECHERCHE = 100    # Pixels de marge autour de la zone pour la recherche
SCORE_SEUIL = 85.0       # Score minimum (%) pour valider une zone (0-100)
```

- **`MARGE_RECHERCHE` trop faible** → Le template ne sera pas trouvé si la pièce a bougé.
- **`MARGE_RECHERCHE` trop élevé** → Risque de faux positifs et ralentissement.
- **`SCORE_SEUIL` trop élevé** → Trop de NOK (rejets injustifiés).
- **`SCORE_SEUIL` trop bas** → Risque de laisser passer des défauts.

### 8.6 Mappings véhicules et pièces

**`MAPPING_VEHICULE`** — Traduit le code cycle moteur en modèle/motorisation :
```python
MAPPING_VEHICULE = {
    "006": {"VEHICULE": "P51", "MOTORISATION": "ICE"},
    "007": {"VEHICULE": "P51", "MOTORISATION": "PHEV"},
    # Ajouter ici tout nouveau code cycle
}
```

**`MAPPING_PIECE`** — Traduit un code cycle pièce en variante de zone :
```python
MAPPING_PIECE = {
    "code_ecran": {        # Nom de la clé dans AUTOMATE_DB_LECTURE
        "001": "00",       # Code cycle → variante (doit correspondre au champ "type" dans le CSV)
        "002": "01",
        "003": "10",
    }
}
```

---

## 9. Gestion des zones de contrôle (CSV)

Les zones définissent **où** chercher dans l'image pour chaque point de contrôle. Elles sont stockées dans des fichiers CSV dans le dossier `zones/`.

### 9.1 Format du fichier CSV

**Fichier :** `zones/{VEHICULE}_{MOTORISATION}.csv`  
**Exemple :** `zones/P51_ICE.csv`

| Colonne | Type | Description |
|---|---|---|
| `numero_camera` | int | ID de la caméra qui capture cette zone |
| `numero_zone` | int | ID unique de la zone (≠ 0, car 0 est ignoré) |
| `x0` | int | Coordonnée X du coin haut-gauche de la zone (pixels) |
| `y0` | int | Coordonnée Y du coin haut-gauche de la zone (pixels) |
| `x1` | int | Coordonnée X du coin bas-droit de la zone (pixels) |
| `y1` | int | Coordonnée Y du coin bas-droit de la zone (pixels) |
| `type` | str | Variante de pièce associée (vide / `None` = toutes variantes) |
| `nom_vissage` | str | Nom humain lisible affiché dans l'UI et les rapports |

**Exemple de contenu :**
```csv
numero_camera,numero_zone,x0,y0,x1,y1,type,nom_vissage
1,1,450,320,550,400,,Vis berceau avant G
1,2,800,320,900,400,,Vis berceau avant D
1,3,450,500,550,580,01,Ecran tole sous moteur
1,4,450,500,550,580,10,Deflecteur sous moteur
2,5,200,150,350,280,,Vis berceau AVD
```

> **Règle :** Chaque combinaison `(numero_camera, numero_zone)` est unique par fichier. Si deux lignes ont la même zone mais des `type` différents, seule celle dont le `type` correspond à la variante active du véhicule sera traitée (sauf si `type` est vide, auquel qu'elle s'applique à tous).

---

### 9.2 Créer une zone

#### Via l'interface graphique (méthode recommandée)

L'interface permet de dessiner des zones directement sur l'image capturée. Se référer à la section de l'UI dédiée à la configuration des zones.

#### Manuellement dans le fichier CSV

1. Identifier les coordonnées `(x0, y0, x1, y1)` en utilisant un outil d'édition d'image (GIMP, Paint, etc.) sur une photo de référence.
2. Ouvrir (ou créer) le fichier `zones/{VEHICULE}_{MOTORISATION}.csv`.
3. Ajouter une ligne en respectant le format :
   ```csv
   1,6,620,410,720,490,,Ecran sous moteur G
   ```
4. S'assurer que le `numero_zone` est unique dans ce fichier.
5. Créer l'image de référence correspondante (voir section 10).

#### Via le code Python (helper_csv.py)

```python
from helper_csv import ZoneConfigHelper

helper = ZoneConfigHelper()
helper.sauvegarder_nouvelle_zone(
    vehicule="P51",
    motorisation="ICE",
    camera_id=1,
    zone_id=6,
    x0=620, y0=410,
    x1=720, y1=490,
    type_zone=None,        # None ou "" = toutes variantes
    nom_vissage="Ecran sous moteur G"
)
```

---

### 9.3 Modifier une zone

Il n'existe pas de méthode `modifier_zone` directe. Procéder ainsi :

1. **Supprimer** l'ancienne zone (voir 9.4).
2. **Recréer** la zone avec les nouvelles coordonnées (voir 9.2).
3. **Vérifier** que l'image de référence est toujours valide avec les nouvelles coordonnées (la zone de référence doit être contenue dans la zone CSV élargie de `MARGE_RECHERCHE`).

**Ou directement dans le fichier CSV :**
```bash
nano zones/P51_ICE.csv
# Modifier les valeurs x0, y0, x1, y1 de la ligne concernée
```

---

### 9.4 Supprimer une zone

#### Via le code Python

```python
from helper_csv import ZoneConfigHelper

helper = ZoneConfigHelper()
helper.supprimer_zone(
    vehicule="P51",
    motorisation="ICE",
    camera_id=1,
    zone_id=6
)
```

#### Manuellement

Ouvrir le CSV et supprimer la ligne correspondante. Supprimer également l'image de référence associée :
```bash
rm ref/P51_ICE/zone_6_*.jpg
```

---

### 9.5 Zones avec variantes

Lorsqu'une caméra contrôle une pièce qui peut exister en plusieurs variantes (ex : écran tôle vs déflecteur), il faut :

**1.** Que la caméra ait `"VARIANTE_REQUISE": "code_ecran"` dans `config.py`.

**2.** Que le code reçu de l'automate soit mappé dans `MAPPING_PIECE` :
```python
MAPPING_PIECE = {
    "code_ecran": {
        "001": "00",   # Code cycle 001 → variante "00" (Sans)
        "002": "01",   # Code cycle 002 → variante "01" (Ecran tôle)
        "003": "10",   # Code cycle 003 → variante "10" (Déflecteur)
    }
}
```

**3.** Que le CSV contienne une ligne par variante avec le bon `type` :
```csv
1,3,450,500,550,580,01,Ecran tole sous moteur
1,4,450,500,550,580,10,Deflecteur sous moteur
```

**4.** Que les images de référence soient dans les sous-dossiers correspondants :
```
ref/P51_ICE/01/zone_3_ecran_tole.jpg
ref/P51_ICE/10/zone_4_deflecteur.jpg
```

Le système ignorera automatiquement les zones dont le `type` ne correspond pas à la variante du véhicule en cours.

---

## 10. Gestion des images de référence

Les images de référence sont les "templates" utilisés par OpenCV pour le template matching. Chaque zone doit avoir au moins une image de référence valide.

### 10.1 Structure des dossiers de référence

```
ref/
├── {VEHICULE}_{MOTORISATION}/         # Ex: P51_ICE
│   ├── zone_1_vis_berceau_AVG.jpg     # Zone sans variante
│   ├── zone_2_vis_berceau_AVD.jpg
│   ├── 01/                            # Sous-dossier pour variante "01"
│   │   └── zone_3_ecran_tole.jpg
│   └── 10/                            # Sous-dossier pour variante "10"
│       └── zone_3_deflecteur.jpg
├── P51_PHEV/
│   └── ...
```

### 10.2 Nomenclature des fichiers de référence

**Pattern attendu par le code :** `zone_{zone_id}_*.jpg`

Exemples valides :
- `zone_1_vis_berceau.jpg`
- `zone_1_ref.jpg`
- `zone_1_20260515.jpg`
- `zone_1_.jpg`

La partie après `zone_1_` est libre mais doit être unique par dossier si plusieurs références existent.

> ⚠️ **Le `zone_id` dans le nom doit correspondre exactement au `numero_zone` dans le CSV.**

### 10.3 Créer une nouvelle référence

1. Capturer une image d'un véhicule conforme (toutes pièces correctement montées).
2. Extraire la région d'intérêt correspondant à la zone CSV avec un outil d'édition d'image.

   > La région extraite doit être **légèrement plus petite** que la zone CSV définie. L'algorithme recherche le template dans la zone élargie de `MARGE_RECHERCHE` pixels.

3. Nommer le fichier selon la nomenclature et le placer dans le bon dossier.

**Exemple pratique avec OpenCV :**
```python
import cv2

img = cv2.imread("cam1.jpg")  # Image pleine résolution
x0, y0, x1, y1 = 450, 320, 550, 400  # Coordonnées de la zone
ref = img[y0:y1, x0:x1]
cv2.imwrite("ref/P51_ICE/zone_1_vis_berceau.jpg", ref)
```

### 10.4 Mettre à jour une référence

Supprimer l'ancienne et créer la nouvelle :
```bash
rm ref/P51_ICE/zone_1_*.jpg
# Puis placer le nouveau fichier zone_1_nouvelle_ref.jpg
```

L'interface dispose d'une fonctionnalité "Prendre comme référence" qui permet de définir directement un véhicule conforme comme nouvelle référence. Cela met également à jour la base de données (`add_reference_to_db`).

### 10.5 Références multiples par zone

Il est possible d'avoir plusieurs fichiers `zone_{id}_*.jpg` pour une même zone. Le système testera toutes les références et retiendra le meilleur score. Cela est utile lorsque :
- La pièce peut avoir des orientations légèrement différentes selon les véhicules.
- L'éclairage varie entre les passages.

```
ref/P51_ICE/
├── zone_1_ref_eclairage_normal.jpg
├── zone_1_ref_eclairage_bas.jpg
└── zone_1_ref_eclairage_fort.jpg
```

> **Performance :** Plus il y a de références, plus l'analyse est lente. L'algorithme s'arrête dès qu'un score ≥ `SCORE_SEUIL` est atteint, donc placer la référence la plus représentative en premier (tri alphabétique).

---

## 11. Déploiement sur un nouveau site

### 11.1 Checklist pré-déploiement

- [ ] Réseau industriel configuré (IPs fixes, switch, câblage)
- [ ] Automate S7 accessible depuis la Pi principale
- [ ] DBs automate créées et validées avec le service automatisme (DB102 lecture, DB105 écriture)
- [ ] Pi esclaves installées, SSH opérationnel
- [ ] Caméras montées, testées individuellement
- [ ] HDD monté et accessible en écriture
- [ ] Scripts `prise_photo.py` et `rasp_camera_keepalive.py` déployés sur les esclaves
- [ ] Dossiers `zones/` et `ref/` créés
- [ ] `config.py` mis à jour (voir étapes ci-dessous)
- [ ] Premiers CSVs de zones créés et validés
- [ ] Premières images de référence capturées et placées

---

### 11.2 Adaptations réseau

Modifier dans `config.py` :
```python
RASPBERRY = [
    {"NUMERO": 0, "IP": "NOUVELLE_IP_PRINCIPALE", "USERNAME": "...", "PASSWORD": "...", "CAM": []},
    {"NUMERO": 1, "IP": "NOUVELLE_IP_ESCLAVE_1",  "USERNAME": "...", "PASSWORD": "...", "CAM": [1]},
    # ...
]
AUTOMATE_IP = "NOUVELLE_IP_AUTOMATE"
```

Vérifier que le pare-feu réseau autorise :
- TCP port 22 (SSH) : Pi principale → Pi esclaves
- TCP port 102 (S7) : Pi principale → Automate

---

### 11.3 Adaptations automate S7

Si les numéros de DB ou la structure des données changent :

```python
AUTOMATE_DB = 102                  # Changer le numéro de DB de lecture
AUTOMATE_TAILLE_LECTURE = 36       # Adapter si la taille du DB change
AUTOMATE_DB_ENVOIE = 105           # Changer le numéro de DB d'écriture
AUTOMATE_DB_LECTURE = {
    "vis": 2,            # Offset en octets dans le DB pour le VIS
    "type_vh": 12,
    "silhouette": 18,
    "code_moteur": 24,   # Clé utilisée pour MAPPING_VEHICULE
    "code_ecran": 30,    # Clé utilisée si VARIANTE_REQUISE = "code_ecran"
}
```

> La taille de lecture doit être ≥ (offset maximum + longueur de la dernière string). Pour une string S7 en DB, la longueur réelle est la taille max + 2 octets d'en-tête.

---

### 11.4 Ajout de nouveaux types de véhicules

1. Ajouter le code cycle dans `MAPPING_VEHICULE` :
```python
MAPPING_VEHICULE = {
    # ...
    "021": {"VEHICULE": "P56", "MOTORISATION": "ICE"},
    "022": {"VEHICULE": "P56", "MOTORISATION": "BEV"},
}
```

2. Créer les fichiers CSV de zones : `zones/P56_ICE.csv`, `zones/P56_BEV.csv`

3. Créer les dossiers de référence : `ref/P56_ICE/`, `ref/P56_BEV/`

4. Capturer des véhicules conformes et créer les images de référence.

---

### 11.5 Ajout de nouvelles caméras et Pi esclaves

**Étape 1 — Dans `config.py`, ajouter la Pi :**
```python
RASPBERRY = [
    # ... (existants)
    {
        "NUMERO": 3,
        "IP": "10.226.178.54",
        "USERNAME": "ingpi",
        "PASSWORD": "raspberry1",
        "CAM": [4, 5],
    },
]
```

**Étape 2 — Ajouter les caméras :**
```python
CAM = [
    # ... (existantes)
    {"NUMERO": 4, "TYPE": False, "ACTIVE": True, "NOM": "Déflecteur AVD (EH)"},
    {"NUMERO": 5, "TYPE": False, "ACTIVE": True, "NOM": "Déflecteur AVD (EB)"},
]
```

**Étape 3 — Déployer la Pi esclave** (voir section 7.2).

**Étape 4 — Ajouter les zones** pour les nouvelles caméras dans les CSV existants ou créer de nouveaux CSV si de nouveaux véhicules sont concernés.

**Étape 5 — Ajouter les images de référence** pour les nouvelles zones.

---

### 11.6 Ajout de nouvelles pièces/variantes

Si une pièce a une nouvelle variante lue depuis l'automate :

1. Ajouter le code dans `MAPPING_PIECE` :
```python
MAPPING_PIECE = {
    "code_ecran": {
        # ... (existants)
        "007": "20",  # Nouveau code → nouvelle variante "20"
    }
}
```

2. Ajouter les zones correspondantes dans le CSV avec `type=20`.

3. Créer le dossier `ref/{VEHICULE}_{MOTORISATION}/20/` et les images de référence.

---

## 12. Maintenance

### 12.1 Maintenance matérielle

**Caméras :**
- Nettoyer les optiques régulièrement (poussière, huile de ligne) avec un chiffon microfibre.
- Vérifier le serrage mécanique des supports (vibrations de ligne).
- Contrôler les câbles USB/CSI (risque de déconnexion par vibrations).
- Si la qualité image se dégrade : recapturer les images de référence dans les nouvelles conditions.

**Raspberry Pi :**
- Vérifier la température CPU (`vcgencmd measure_temp`) — seuil critique : 80°C.
- Nettoyer les grilles de ventilation si présentes.
- Vérifier l'alimentation électrique (5V / 3A minimum pour Pi 4 sous charge).
- Remplacer la carte SD ou utiliser un SSD si des erreurs d'E/S apparaissent.

**Disque dur :**
- Surveiller l'espace disque disponible (voir section 12.4).
- Vérifier le montage au démarrage (`/etc/fstab` si HDD externe).

**Réseau :**
- Vérifier les câbles Ethernet et les LED du switch.
- S'assurer que les IPs restent fixes (DHCP statique ou IP fixe sur chaque Pi).

---

### 12.2 Maintenance logicielle

**Mise à jour du système :**
```bash
sudo apt update && sudo apt upgrade -y
# Redémarrer si mise à jour du kernel
```

**Sauvegarder la configuration avant toute modification :**
```bash
cp config.py config.py.backup_$(date +%Y%m%d)
cp -r zones/ zones_backup_$(date +%Y%m%d)/
cp -r ref/ ref_backup_$(date +%Y%m%d)/
cp historique_production.db historique_production_$(date +%Y%m%d).db
```

**Surveiller les logs :**
```bash
# Si lancé via systemd
sudo journalctl -u vision_qualite -f

# Si lancé manuellement, rediriger les sorties
python3 main.py 2>&1 | tee logs/vision_$(date +%Y%m%d).log
```

**Vérifier la connectivité des Pi esclaves :**
```bash
for ip in 10.226.178.53 10.226.178.52; do
    ping -c 1 $ip && echo "$ip OK" || echo "$ip HORS LIGNE"
done
```

---

### 12.3 Gestion de la base de données

**Vérifier la taille :**
```bash
ls -lh historique_production.db
```

**Purger les enregistrements anciens (> 6 mois) :**
```python
import sqlite3
from datetime import datetime, timedelta

conn = sqlite3.connect("historique_production.db")
seuil = int((datetime.now() - timedelta(days=180)).timestamp())
conn.execute("DELETE FROM inspections WHERE timestamp < ?", (seuil,))
conn.execute("VACUUM")  # Récupère l'espace disque
conn.commit()
conn.close()
```

**Sauvegarder :**
```bash
sqlite3 historique_production.db ".backup historique_backup_$(date +%Y%m%d).db"
```

**Vérifier l'intégrité :**
```bash
sqlite3 historique_production.db "PRAGMA integrity_check;"
```

---

### 12.4 Gestion du stockage images

**Vérifier l'espace utilisé :**
```bash
df -h /mnt/hdd          # HDD
df -h /dev/shm          # RAM
du -sh /mnt/hdd/2026/   # Par année
```

**Politique d'archivage recommandée :**
Les images sont archivées par date (`{YYYY}/{MM}/{DD}/`). Mettre en place une rotation automatique :
```bash
# Supprimer les images de plus de 90 jours
find /mnt/hdd/ -name "*.jpg" -mtime +90 -delete
find /mnt/hdd/ -type d -empty -delete  # Nettoyer les dossiers vides
```

**Vérifier le cache RAM :**
```bash
ls -la /dev/shm/cam*.jpg   # Images temporaires en RAM
```

Si des images `cam*.jpg` s'accumulent en RAM (crash du système), les supprimer manuellement :
```bash
rm /dev/shm/cam*.jpg
```

---

## 13. Troubleshooting exhaustif

### 13.1 Problèmes réseau / SSH

---

**🔴 Symptôme : `[Erreur - Pi N] Échec de la connexion`**

*Causes possibles et actions :*

1. **Pi esclave éteinte ou redémarrée**
   - Vérifier physiquement l'alimentation de la Pi.
   - `ping 10.226.178.5X` depuis la Pi principale.
   - Si ping OK mais SSH KO : `ssh user@ip` manuellement pour voir l'erreur exacte.

2. **IP de la Pi esclave a changé** (DHCP non statique)
   - Se connecter à la Pi directement et vérifier : `hostname -I`
   - Corriger l'IP dans `config.py` ou configurer une IP fixe sur la Pi esclave.

3. **Mot de passe incorrect**
   - Tester manuellement : `ssh rasp1@10.226.178.53`
   - Corriger `PASSWORD` dans `config.py`.

4. **Clés SSH corrompues** (si `AutoAddPolicy` rejeté)
   - `ssh-keygen -R 10.226.178.53` sur la Pi principale.
   - Reconnecter manuellement pour re-accepter la clé host.

5. **Timeout réseau** (délai trop court `timeout=5`)
   - Augmenter dans `reseau.py` : `timeout=10`

---

**🔴 Symptôme : Capture retourne une liste vide (`[]`)**

1. **`prise_photo.py` plante sur la Pi esclave**
   - Tester manuellement : `ssh rasp1@10.226.178.53 "python3 ~/prise_photo.py"`
   - Vérifier la sortie stderr.

2. **Caméra non reconnue**
   - Sur la Pi esclave : `ls /dev/video*` (USB) ou `libcamera-hello` (CSI).
   - Rebrancher la caméra, redémarrer la Pi si nécessaire.

3. **Fichier `/dev/shm/cam{N}.jpg` absent sur la Pi esclave**
   - Vérifier que `prise_photo.py` écrit bien au bon chemin.
   - `ssh rasp1@10.226.178.53 "ls /dev/shm/"`.

4. **Connexion SSH active mais transport mort**
   - Le keepalive de 15s devrait éviter cela. Si persistant, réduire à 10s dans `reseau.py` : `set_keepalive(10)`.

---

**🔴 Symptôme : `paramiko.ssh_exception.SSHException: Error reading SSH protocol banner`**

- La Pi esclave répond au ping mais le service SSH n'est pas encore démarré (reboot récent).
- Attendre 30-60 secondes et réessayer.
- Sur la Pi esclave : `sudo systemctl status ssh`.

---

### 13.2 Problèmes automate / PLC S7

---

**🔴 Symptôme : `[Erreur - Automate IP] Échec de la connexion`**

1. **Automate éteint ou en défaut**
   - Vérifier les LEDs de l'automate (ERR/RUN).
   - `ping 10.226.178.1`.

2. **Connexions S7 non autorisées sur l'automate**
   - Dans TIA Portal, vérifier que les connexions S7 externes sont autorisées dans les propriétés CPU : *Propriétés > Protection > Autoriser l'accès PUT/GET*.

3. **Rack/Slot incorrects**
   - Pour un S7-1200 : rack=0, slot=1.
   - Pour un S7-300 : rack=0, slot=2 souvent.
   - Vérifier avec TIA Portal et ajuster `AUTOMATE_RACK` / `AUTOMATE_SLOT`.

4. **Pare-feu réseau bloquant TCP 102**
   - Vérifier avec `telnet 10.226.178.1 102`.

---

**🔴 Symptôme : `[Automate] Données lues mais VIS vide ou incohérent`**

1. **Offset incorrect dans `AUTOMATE_DB_LECTURE`**
   - Ouvrir le DB dans TIA Portal et comparer les offsets réels avec ceux configurés.
   - La taille d'une string S7 = `longueur_max + 2` octets. Recalculer si le DB a été modifié.

2. **`AUTOMATE_TAILLE_LECTURE` trop petite**
   - Augmenter pour couvrir le dernier offset + taille de la dernière variable.

3. **Véhicule non enregistré dans `MAPPING_VEHICULE`**
   - Le code_moteur reçu n'est pas dans le dictionnaire → retourne `"Inconnu"`.
   - Ajouter le code manquant : `"021": {"VEHICULE": "P56", "MOTORISATION": "BEV"}`.

---

**🔴 Symptôme : L'automate ne reçoit pas les résultats (DB105 non mis à jour)**

1. **DB d'écriture non créée dans TIA Portal**
   - Créer et télécharger le DB105 sur l'automate.

2. **Taille du DB105 insuffisante**
   - Taille nécessaire = `OFFSET_ARRAY + (NB_MAX_DEFAUTS × OCTETS_DEFAUTS)` = `2 + (15 × 34)` = 512 octets.
   - Vérifier que le DB est assez grand dans TIA Portal.

3. **PUT/GET non activé** (même diagnostic que connexion)

---

**🔴 Symptôme : Le système détecte des véhicules en continu (boucle)**

- Le bit `vh_dans_pas` (offset 0, bit 0) reste à True.
- L'automate n'a pas remis le bit à False entre deux véhicules.
- Vérifier la logique de gestion du bit dans le programme automate.
- Dans le code, ce bit est détecté sur **front montant** (`nouveau_etat and not ancien_etat`), donc si l'automate ne le reset pas, un seul déclenchement se produit. Si le problème persiste, vérifier le câblage du capteur de présence.

---

### 13.3 Problèmes caméras / capture

---

**🔴 Symptôme : Image reçue mais noire ou corrompue**

1. **Caméra mal initialisée** → `rasp_camera_keepalive.py` ne tourne pas.
   - Sur la Pi esclave : `ps aux | grep keepalive`
   - Si absent : `python3 ~/rasp_camera_keepalive.py &`

2. **Problème d'exposition / luminosité**
   - Vérifier l'éclairage de la zone de capture.
   - Ajuster les paramètres d'exposition dans `prise_photo.py`.

3. **Câble CSI mal branché**
   - Éteindre la Pi, revérifier le connecteur CSI (sens et verrouillage).

4. **Résolution image incohérente avec les zones CSV**
   - Si la résolution change, les coordonnées des zones ne correspondent plus.
   - Recapture et reconfiguration des zones obligatoires.

---

**🔴 Symptôme : `[Erreur - Vision N] Image introuvable`**

- Le fichier a été créé en RAM sur la Pi esclave mais le SFTP a échoué.
- Vérifier les droits d'écriture sur `/dev/shm/` de la Pi principale.
- Vérifier que le chemin `Config.TEMPORAIRE_PATH` existe et est accessible.

---

### 13.4 Problèmes vision / analyse d'image

---

**🔴 Symptôme : Toutes les zones sont NOK (score 0 ou très bas)**

1. **Images de référence absentes**
   - Vérifier : `ls ref/{VEHICULE}_{MOTORISATION}/zone_{N}_*.jpg`
   - Créer les références manquantes (section 10).

2. **Mauvaise association véhicule/fichier CSV**
   - Le CSV attendu est `zones/{vehicule}_{motorisation}.csv`
   - Vérifier que `vehicule` et `motorisation` dans le dictionnaire correspondent exactement aux noms de fichiers (casse, underscores).

3. **Zone CSV hors image** (coordonnées > résolution de la caméra)
   - Vérifier les coordonnées du CSV face à la résolution réelle de la caméra.

4. **Référence plus grande que la zone de recherche**
   - La référence `(h_ref, w_ref)` doit être strictement plus petite que la zone élargie `(zone + 2*MARGE_RECHERCHE)`.
   - Réduire la taille de l'image de référence ou augmenter `MARGE_RECHERCHE`.

---

**🔴 Symptôme : Trop de faux NOK (pièces OK détectées NOK)**

1. **Références de mauvaise qualité**
   - Recapturer les références dans des conditions d'éclairage identiques à la production.

2. **`SCORE_SEUIL` trop élevé**
   - Réduire progressivement (ex : 82.0, 80.0) et valider sur un échantillon.

3. **Vibrations pendant la capture**
   - Synchroniser la capture avec un moment de ligne arrêtée ou stabilisée.
   - Augmenter `MARGE_RECHERCHE` pour absorber les petits décalages.

4. **Pièce déplacée par rapport à la référence**
   - Augmenter `MARGE_RECHERCHE` ou recréer la référence au bon emplacement.

---

**🔴 Symptôme : Trop de faux OK (défauts non détectés)**

1. **`SCORE_SEUIL` trop bas** → Augmenter.
2. **Référence incorrecte** (créée sur un véhicule NOK) → Recréer la référence.
3. **Zone trop petite** (la pièce manquante ne change pas suffisamment l'image) → Élargir la zone CSV.

---

**🔴 Symptôme : `[Vision N] Crash {e}`**

- Vérifier les logs pour l'exception complète.
- Les crashes les plus fréquents :
  - `cv2.error` : image corrompue ou dimensions nulles → Vérifier la caméra.
  - `KeyError` : champ manquant dans le dictionnaire → Vérifier la structure des données envoyées par `reseau.py`.
  - `MemoryError` : surcharge RAM → Réduire `MARGE_RECHERCHE` ou `CACHE_LIMIT`.

---

### 13.5 Problèmes base de données

---

**🔴 Symptôme : `[DB Save Error] Rollback effectué`**

1. **Base de données verrouillée** (accès concurrent)
   - SQLite ne supporte qu'un écrivain à la fois. Si plusieurs processus tentent d'écrire simultanément, augmenter le timeout SQLite.
   - Dans `helper_database.py`, ajouter `conn.execute("PRAGMA busy_timeout = 5000;")` après la connexion.

2. **Espace disque plein**
   - `df -h .`
   - Libérer de l'espace ou déplacer la BDD sur un autre disque.

3. **Base de données corrompue**
   - `sqlite3 historique_production.db "PRAGMA integrity_check;"`
   - Si KO, restaurer depuis la dernière sauvegarde.

---

**🔴 Symptôme : La recherche historique ne renvoie pas de résultats**

1. **Bug SQL connu dans `rechercher_vehicule`** — il manque un espace avant `ORDER BY` :
   ```python
   # Ligne actuelle (buggée) :
   query += "ORDER BY timestamp DESC LIMIT 50"
   # Correction :
   query += " ORDER BY timestamp DESC LIMIT 50"
   ```

2. **Filtres trop restrictifs** → Essayer avec tous les champs vides.

---

**🔴 Symptôme : `[DB] Erreur lors de la recherche`**

- La BDD a peut-être été créée par une version différente du schéma.
- Supprimer le fichier `.db` et relancer pour recréer (perte des données !).
- Ou effectuer une migration manuelle via `sqlite3`.

---

### 13.6 Problèmes stockage

---

**🔴 Symptôme : `[Storage] Image temp non trouvée`**

- L'image a été supprimée du cache RAM avant d'être traitée.
- `CACHE_LIMIT` trop faible par rapport au flux de véhicules.
- Augmenter `CACHE_LIMIT` dans `config.py`.

---

**🔴 Symptôme : Images non archivées sur le HDD**

1. **HDD non monté**
   - `mount | grep mnt` ou `lsblk`
   - Remonter : `sudo mount /dev/sda1 /mnt/hdd`
   - Vérifier `/etc/fstab` pour le montage automatique.

2. **Droits insuffisants**
   - `ls -la /mnt/hdd/` → vérifier propriétaire et droits.
   - `sudo chown -R pimain:pimain /mnt/hdd/`

3. **`HDD_PATH` incorrect dans config.py**
   - Vérifier que le chemin existe : `ls /mnt/hdd/`

---

**🔴 Symptôme : `/dev/shm` plein**

- Des images `cam*.jpg` ou des fichiers de la session précédente traînent.
```bash
df -h /dev/shm
rm /dev/shm/cam*.jpg
rm /dev/shm/*.jpg
```
- Si le problème est récurrent, réduire `CACHE_LIMIT` ou `cams_par_voiture` dans `GestionnaireRAM`.

---

**🔴 Symptôme : Nom de fichier image incorrect ou `Inconnu` dans le nom**

- Les champs `vehicule`, `motorisation` ou `vis` n'ont pas été correctement reçus de l'automate.
- Vérifier les offsets dans `AUTOMATE_DB_LECTURE` et la connexion automate.

---

### 13.7 Problèmes interface graphique (UI)

---

**🔴 Symptôme : L'UI ne se lance pas (`TclError`, `_tkinter` absent)**

```bash
sudo apt install python3-tk -y
# Vérifier l'affichage X11
echo $DISPLAY   # Doit retourner ":0" ou similaire
export DISPLAY=:0
```

---

**🔴 Symptôme : L'UI se fige (ne répond plus)**

- La queue `queue_vision_vers_ui` est saturée (les processus vision produisent plus vite que l'UI ne consomme).
- Vérifier que `after()` ou le mécanisme de polling de la queue est bien implémenté dans `interface.py` (doit être non-bloquant).
- Un appel bloquant (ex : `queue.get()` sans timeout) dans le thread UI gèle Tkinter.

---

**🔴 Symptôme : Verrouillage par inactivité intempestif**

- `DELAI_INACTIVITE = 300000` ms = 5 minutes.
- Augmenter dans `config.py` si nécessaire : `DELAI_INACTIVITE = 600000` (10 min).

---

**🔴 Symptôme : Mot de passe refusé**

- Le mot de passe est `"ing"` (défini dans `Config.PASSWORD`).
- Si modifié, le chercher dans `config.py`.

---

### 13.8 Problèmes de performance

---

**🔴 Symptôme : Analyse trop lente (retard sur la ligne)**

1. **Réduire `MARGE_RECHERCHE`** (impact direct sur la surface de recherche).
2. **Réduire la résolution des images** dans `prise_photo.py` (pas toujours possible sans perdre en précision).
3. **Augmenter le nombre de workers vision** dans `main.py` :
   ```python
   process_vision_3 = multiprocessing.Process(
       target=analyse_image,
       args=(queue_reseau_vers_vision, queue_vision_vers_ui, "Core 5"),
   )
   process_vision_3.daemon = True
   process_vision_3.start()
   ```
4. **Limiter le nombre de références par zone** (choisir 1 référence représentative plutôt que 5).

---

**🔴 Symptôme : Surchauffe de la Pi principale**

```bash
watch -n 2 vcgencmd measure_temp   # Surveiller en temps réel
```

- Au-delà de 80°C : le CPU briderait (throttling).
- Ajouter un dissipateur thermique / ventilateur.
- Réduire le nombre de processus concurrents.

---

## 14. Nomenclature des fichiers images archivés

**Format :**
```
{camera}_{vehicule}_{motorisation}_{variante}_{vis}_{chaine_controle}.jpg
```

**Ou si pas de variante :**
```
{camera}_{vehicule}_{motorisation}_{vis}_{chaine_controle}.jpg
```

| Champ | Exemple | Description |
|---|---|---|
| `camera` | `1` | ID de la caméra source |
| `vehicule` | `P51` | Modèle du véhicule |
| `motorisation` | `ICE` | Type de motorisation |
| `variante` | `01` | Variante de pièce (absent si none) |
| `vis` | `VF1RFB00123456789` | Numéro VIS du véhicule |
| `chaine_controle` | `11010` | 1 = zone OK, 0 = zone NOK (1 chiffre par zone, triées par ID) |

**Exemples :**
```
1_P51_ICE_01_VF1RFB001234_11110.jpg   # Cam1, P51 ICE, variante 01, 4 zones OK + 1 NOK
2_P51_PHEV_VF1RFB005678_111.jpg       # Cam2, P51 PHEV, sans variante, 3 zones OK
```

---

## 15. Référence rapide des commandes utiles

```bash
# Lancer l'application
cd /home/pimain/projet_vision && python3 main.py

# Vérifier la connectivité réseau
ping 10.226.178.53 && ping 10.226.178.52 && ping 10.226.178.1

# Tester SSH vers un esclave
ssh rasp1@10.226.178.53 "python3 ~/prise_photo.py && ls /dev/shm/cam*.jpg"

# Vérifier les logs systemd
sudo journalctl -u vision_qualite -f --since "1 hour ago"

# Surveiller la température Pi
watch -n 2 vcgencmd measure_temp

# Vérifier l'espace disque
df -h . /dev/shm

# Sauvegarder la base de données
sqlite3 historique_production.db ".backup backup_$(date +%Y%m%d).db"

# Vérifier l'intégrité BDD
sqlite3 historique_production.db "PRAGMA integrity_check;"

# Lister les zones d'un véhicule
cat zones/P51_ICE.csv

# Lister les images de référence d'un véhicule
ls -la ref/P51_ICE/

# Vider le cache RAM
rm -f /dev/shm/cam*.jpg

# Compter les inspections du jour
sqlite3 historique_production.db "SELECT COUNT(*) FROM inspections WHERE timestamp > strftime('%s', 'now', 'start of day');"

# Afficher les 10 dernières inspections
sqlite3 historique_production.db "SELECT vis, vehicule, motorisation, datetime(timestamp, 'unixepoch', 'localtime') FROM inspections ORDER BY timestamp DESC LIMIT 10;"
```

---

*Fin du document — Pour toute question sur l'architecture ou les évolutions, contacter James DAY.*