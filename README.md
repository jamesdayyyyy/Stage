# 👁️ Système de Contrôle Vision CV

Bienvenue dans la documentation complète du **Système de Contrôle Qualité par Vision**. 
Ce document est la référence absolue pour toute personne (développeur, ingénieur vision, automaticien ou technicien de maintenance) reprenant le projet. Il contient toutes les informations nécessaires pour comprendre, installer, configurer, dépanner et faire évoluer le système de A à Z.

---

## 📑 Table des Matières
1. [Introduction et Philosophie](#1-introduction-et-philosophie)
2. [Architecture du Système](#2-architecture-du-système)
3. [Structure du Code Source](#3-structure-du-code-source)
4. [Installation & Prérequis](#4-installation--prérequis)
5. [Configuration Cœur (`config.py`)](#5-configuration-cœur-configpy)
6. [Mode Administrateur & Calibrage Vision](#6-mode-administrateur--calibrage-vision)
7. [Guide de Dépannage Exhaustif (Troubleshooting)](#7-guide-de-dépannage-exhaustif-troubleshooting)
8. [Déploiement sur un Nouveau Site](#8-déploiement-sur-un-nouveau-site)
9. [Maintenance Préventive et Physique](#9-maintenance-préventive-et-physique)
10. [Base de Données et Stockage](#10-base-de-données-et-stockage)

---

## 1. Introduction et Philosophie

Ce système a pour but de vérifier automatiquement la présence et la conformité de pièces (ex: écrans sous moteur, déflecteurs) et de vissages sur des véhicules défilant sur une ligne de production. 

**Principe de base :**
1. L'automate industriel (PLC) détecte un véhicule et envoie un signal au PC central.
2. Le PC central ordonne (via SSH) aux caméras (Raspberry Pi) de prendre des photos.
3. Les photos sont rapatriées sur le PC, traitées par analyse d'image (Template Matching via OpenCV).
4. Le PC détermine si les zones (ROI - Region of Interest) sont conformes en comparant avec des images de référence.
5. Les résultats (OK/NOK, liste des défauts) sont renvoyés à l'automate pour bloquer ou libérer la ligne.

---

## 2. Architecture du Système

### 💻 Hardware
*   **PC Central (Maître) :** Fait tourner l'IHM, la base de données, l'analyse OpenCV, et orchestre le tout.
*   **Raspberry Pi (Esclaves) :** Gèrent physiquement les caméras.
*   **Caméras :** Modules caméra haute résolution connectés en CSI aux Raspberry Pi.
*   **Automate (PLC) :** Type Siemens S7 (ex: S7-1500). Gère le flux de la ligne.

### ⚙️ Software & Réseau
*   **Multiprocessing :** Le programme principal sépare la capture réseau (`reseau.py`), l'analyse vision (`vision.py` - sur plusieurs cœurs), et l'interface Tkinter (`interface.py`) pour éviter les blocages (freezes).
*   **Keepalive Caméra :** Pour éviter le temps de chauffe du capteur photo, un démon tourne 24/7 sur les Pi (`rasp_camera_keepalive.py`). Il écoute sur un socket local. Quand le PC demande une photo (`prise_photo.py`), la prise de vue est instantanée.
*   **Protocole S7 :** La communication PC ↔ Automate se fait via la librairie `snap7`.
*   **Transfert SFTP :** Les images transitent des Pi vers le PC via le protocole SFTP (au-dessus de SSH).

---

## 3. Structure du Code Source

```text
/Code/
│
├── main.py                  # POINT D'ENTRÉE : Lance les processus parallèles et l'IHM.
├── config.py                # LE CERVEAU : Toutes les IP, offsets automates, paramètres.
├── interface.py             # L'interface graphique (Tkinter).
├── reseau.py                # Gestion SSH (Paramiko), SFTP, et écoute de l'automate.
├── vision.py                # Traitement OpenCV (Template Matching, Flou Gaussien).
│
├── helper_affichage.py      # Moteur de rendu du Canvas Tkinter (zoom, dessin des zones).
├── helper_automate.py       # Wrapper Snap7 pour lire/écrire dans l'automate.
├── helper_csv.py            # Lecture/Écriture des coordonnées des zones dans les CSV.
├── helper_database.py       # Requêtes SQLite (sauvegarde historique).
├── helper_storage.py        # Gestion RAM (/dev/shm) et archivage sur Disque Dur.
│
├── historique_production.db # (Généré) Base de données SQLite.
├── /zones/                  # (Généré) Fichiers CSV contenant les x,y des zones de test.
├── /ref/                    # (Généré) Images de références (les "bons" vissages).
│
└── rasp_distant/            # Fichiers À PLACER SUR LES RASPBERRY PI
    ├── config_pi.py         # Config locale de la Pi (quelles caméras sont branchées).
    ├── rasp_camera_keepalive.py # Le démon qui maintient la caméra allumée.
    └── prise_photo.py       # Le script déclenché par le PC pour prendre la photo.
```

---

## 4. Installation & Prérequis

### Sur le PC Central
1. **OS :** Linux (Ubuntu/Debian fortement recommandé pour `/dev/shm`) ou macOS.
2. **Python :** 3.9 ou supérieur.
3. **Dépendances :**
   ```bash
   pip install opencv-python numpy paramiko python-snap7 Pillow
   ```
4. **Librairie Snap7 (OS) :** Vous devez installer la librairie C sous-jacente.
   * Ubuntu: `sudo apt-get install libsnap7-dev`
   * macOS: `brew install snap7`

### Sur les Raspberry Pi
1. Copier le contenu du dossier `rasp_distant/` dans `/home/[user]/`.
2. Installer Picamera2 (généralement inclus dans Raspberry Pi OS récent).
3. Configurer les clés SSH pour que le PC central puisse s'y connecter sans mot de passe (bien que le mot de passe soit géré dans `config.py`, les clés sont plus stables).

---

## 5. Configuration Cœur (`config.py`)

C'est ici que 90% des modifications auront lieu lors de l'exploitation. Ne modifiez le code logique que si absolument nécessaire.

### Ajouter une Raspberry Pi
Modifiez la liste `RASPBERRY` :
```python
{
    "NUMERO": 4,             # ID unique
    "IP": "10.226.178.60",   # IP Statique obligatoire
    "USERNAME": "pi",
    "PASSWORD": "mdp",
    "CAM": [4, 5],           # IDs des caméras physiquement branchées dessus
}
```

### Ajouter/Modifier une Caméra
Modifiez la liste `CAM` :
```python
{
    "NUMERO": 4, 
    "ACTIVE": True, 
    "NOM": "Nouvelle vue sous caisse",
    "VARIANTE_REQUISE": "code_ecran" # (Optionnel) Si la caméra ne s'active que pour certaines pièces
}
```

### Communication Automate
```python
AUTOMATE_IP = "10.226.178.1"
AUTOMATE_DB = 102 # Le DataBlock contenant les infos d'entrée
# ATTENTION AUX OFFSETS : C'est l'adresse en octets dans Siemens TIA Portal
AUTOMATE_DB_LECTURE = {
    "vis": 2,          # String commençant à l'octet 2
    "type_vh": 12,     # etc.
}
```

---

## 6. Mode Administrateur & Calibrage Vision

### Comment créer une zone d'inspection ?
Si vous devez inspecter un nouveau vissage ou si une caméra a bougé :
1. Sur l'interface, attendez qu'un véhicule conforme ("bon") passe ou forcez une capture.
2. Cliquez sur **Mode Modif/Admin** et entrez le mot de passe (`PASSWORD` dans `config.py`).
3. Sur l'image, **cliquez et glissez** pour dessiner un rectangle autour du vissage à vérifier.
4. Une popup demande le **nom du vissage**.
5. Cliquez sur le bouton **"Prendre Réf"**. 
   > *Mécanique interne : Le système extrait ce rectangle, le sauvegarde dans le dossier `/ref/`, et écrit ses coordonnées dans le fichier CSV du dossier `/zones/`.*

### Réglage fin du Matching (OpenCV)
Le système utilise `cv2.matchTemplate`.
* `Config.MARGE_RECHERCHE = 100` : Le système cherchera le vissage dans un rayon de 100 pixels autour de la zone dessinée. Si la ligne est instable mécaniquement, augmentez cette valeur (Attention: augmente le temps de calcul).
* `Config.SCORE_SEUIL = 85.0` : Si la correspondance est < 85%, la pièce est considérée NOK.

---

## 7. Guide de Dépannage Exhaustif (Troubleshooting)

### 🔴 Problèmes Réseau / SSH
* **Symptôme :** *[Erreur - Pi X] Échec de la connexion* dans la console. L'image ne s'affiche pas.
* **Diagnostic :** Le PC ne peut pas joindre la Pi en SSH.
* **Résolution :**
  1. Pinguer la Pi depuis un terminal : `ping 10.226.178.X`.
  2. Si ping OK, tenter une connexion SSH manuelle : `ssh user@10.226.178.X`.
  3. Si erreur `Host key verification failed`, c'est que la Pi a été remplacée (changement d'adresse MAC). Faites `ssh-keygen -R 10.226.178.X` sur le PC central.

### 🔴 Problèmes Automate (Snap7)
* **Symptôme :** *[Automate] Impossible de se connecter*. Le cycle ne démarre jamais.
* **Diagnostic :** L'automate est éteint, câble débranché, ou configuration TIA Portal modifiée (sécurité S7).
* **Résolution :**
  1. Vérifier le câble RJ45.
  2. Dans TIA Portal, s'assurer que "Permettre l'accès PUT/GET" est coché dans les propriétés du CPU.
  3. Les DataBlocks (DB 102, 105) ne doivent PAS être "Optimisés" (décocher "Optimized block access").

### 🔴 Problèmes Vision (Scores Anormalement Bas)
* **Symptôme :** Tous les véhicules sont refusés avec des scores à 30-40%.
* **Diagnostic :** 
  * L'éclairage a changé (tube néon mort, rayon de soleil).
  * La caméra a pris un coup physique et l'angle de vue est modifié.
* **Résolution :**
  1. Nettoyer la lentille de la caméra (dépôt d'huile/poussière).
  2. Vérifier les spots lumineux.
  3. Si la mécanique a bougé définitivement : repasser en mode Admin, supprimer la zone (clic droit), et la recréer pour prendre une nouvelle référence.

### 🔴 Alerte "Disque Plein"
* **Symptôme :** Bandeau rouge sur l'IHM. Crash de l'écriture BDD.
* **Résolution :** Vider les vieux dossiers dans `./YYYY/MM/DD`. Le système garde tout indéfiniment par défaut. Créer une tâche `cron` sous Linux pour purger les dossiers > 90 jours :
  `find /chemin/vers/HDD/* -type d -ctime +90 -exec rm -rf {} +`

### 🔴 Le Système Lag ou Fige
* **Symptôme :** Décalage de 30 secondes entre la voiture et l'affichage.
* **Diagnostic :** La RAM est saturée (dossier `/dev/shm` plein).
* **Résolution :** Relancer l'application. Vérifier que `Config.CACHE_LIMIT` n'est pas trop élevé.

---

## 8. Déploiement sur un Nouveau Site

Si vous devez copier le projet pour une nouvelle usine :

1. **Topologie Réseau :** Demandez à l'IT local de fournir une plage d'IP fixes isolées (VLAN industriel) pour éviter les tempêtes de broadcast.
2. **Setup Automate :** Fournissez le tableau d'échange (les offsets `Config.AUTOMATE_DB_LECTURE`) à l'automaticien du site. Imposez le format String pour le VIS.
3. **Mise à blanc des données :**
   * Supprimez le fichier `historique_production.db` (il se recréera vierge).
   * Videz le dossier `/zones/` (les CSV).
   * Videz le dossier `/ref/`.
4. **Calibrage initial :** Vous devrez repasser en "Mode Admin" sur les 10 premières voitures pour dessiner toutes les zones à la main. Prévoyez 2 heures de setup actif sur la ligne.

---

## 9. Maintenance Préventive et Physique

### A. Mécanique et Optique (Hebdomadaire)
* **Nettoyage :** C'est le point d'échec #1. Passez un chiffon microfibre propre (sans produit agressif) sur les vitres de protection des caméras. La brume d'huile industrielle détruit le contraste.
* **Serrage :** Les vibrations de la ligne desserrent les rotules 3D des caméras. Vérifiez la rigidité des fixations.

### B. Informatique (Mensuel)
* **Reboot Pi :** Il est conseillé de redémarrer les Raspberry Pi préventivement. (Peut être automatisé via `crontab -e` : `0 3 * * 0 /sbin/shutdown -r now`).
* **Update OS :** Évitez les `apt-get upgrade` non contrôlés. Ne mettez à jour que si nécessaire pour la sécurité.

---

## 10. Base de Données et Stockage

### SQLite (`historique_production.db`)
La BDD comporte deux tables (voir `helper_database.py`) :
1. `inspections` : id, vis, timestamp, vehicule, motorisation, camera, type_materiau.
2. `zone_results` : id, inspection_id (FK), zone_id, score, match_x, match_y.

Vous pouvez utiliser un outil comme **DB Browser for SQLite** pour générer des rapports de qualité (Taux de rebut par modèle, caméra la plus problématique).

### Stockage Images
* **Temporaire (`/dev/shm`) :** Stocké en RAM (ultra-rapide) pour le traitement immédiat.
* **Permanent (`HDD_PATH`) :** Arborescence générée automatiquement : `Année/Mois/Jour/image.jpg`.
* **Nomenclature Fichier :** `[Caméra]_[Véhicule]_[Moteur]_[Variante]_[VIS]_[10101].jpg`. 
  *Exemple :* `1_P51_ICE_DeflecteurX_VF1234567_110.jpg` (Ici `110` signifie Zone 1 OK, Zone 2 OK, Zone 3 NOK).

---

## 📞 À qui s'adresser ?
Ce système connecte 3 mondes. En cas de doute :
* Problème de bits, signaux en retard, data vérolée ➡️ **Automaticien**.
* Problème de ping, SSH, droits d'accès ➡️ **Informaticien / Réseau**.
* Problème de qualité, références obsolètes ➡️ **Ingénieur Qualité / Méthodes**.

*Conçu par James DAY - Mai 2026. Code is poetry, keep it clean.*
