# Système de Contrôle Vision CV

Système de vérification automatique de conformité de pièces et de vissages par vision industrielle sur ligne de production.

## 1. Architecture Matérielle
*   **Raspberry Pi Maître :** Centralise l'interface graphique (IHM), l'analyse d'image, la base de données et la communication avec l'automate.
*   **Raspberry Pi Esclaves :** Gèrent la capture physique des images via les modules caméras.
*   **Automate (PLC) :** Siemens série S7 (1200/1500). Gère l'avancement de la ligne et les signaux de présence véhicule.
*   **Réseau :** Connexion Ethernet via un switch industriel sur un VLAN dédié.

## 2. Architecture Logicielle
*   **Traitement d'image :** OpenCV (Template Matching).
*   **Interface :** Tkinter.
*   **Communication Inter-Pi :** SSH pour l'exécution de commandes et SFTP pour le transfert de fichiers (librairie Paramiko).
*   **Communication Automate :** Protocole S7 (librairie Snap7).
*   **Parallélisme :** Utilisation du module `multiprocessing` pour séparer l'IHM, la capture réseau et l'analyse vision sur différents cœurs du processeur de la Pi Maître.

## 3. Arborescence du Projet

```text
/Code/
├── main.py                  # Point d'entrée de l'application sur la Pi Maître.
├── config.py                # Paramètres globaux (IP, caméras, automate, seuils).
├── interface.py             # Gestion de l'interface utilisateur.
├── reseau.py                # Gestion des flux SSH/SFTP et surveillance automate.
├── vision.py                # Algorithmes d'analyse d'image.
├── helper_affichage.py      # Composants graphiques et canvas interactif.
├── helper_automate.py       # Fonctions de lecture/écriture S7.
├── helper_csv.py            # Persistance des configurations de zones (CSV).
├── helper_database.py       # Interface avec la base de données SQLite.
├── helper_storage.py        # Gestion du stockage en RAM et sur disque.
├── historique_production.db # Base de données des inspections.
├── /zones/                  # Définitions des zones par modèle (CSV).
├── /ref/                    # Images de référence pour le matching.
└── rasp_distant/            # Scripts à installer sur les Pi Esclaves.
    ├── config_pi.py         # Configuration locale de l'esclave.
    ├── rasp_camera_keepalive.py # Démon de maintien d'activité caméra.
    └── prise_photo.py       # Déclencheur de capture.
```

## 4. Installation

### Sur la Raspberry Pi Maître
1. **Système :** Raspberry Pi OS (64-bit recommandé).
2. **Dépendances Python :**
   ```bash
   pip install opencv-python numpy paramiko python-snap7 Pillow
   ```
3. **Librairie Snap7 :**
   ```bash
   sudo apt-get install libsnap7-dev
   ```

### Sur les Raspberry Pi Esclaves
1. Copier le répertoire `rasp_distant/` dans `/home/[user]/`.
2. S'assurer que `picamera2` est installé.
3. Activer l'interface caméra dans `raspi-config`.

## 5. Configuration (`config.py`)

### Réseau et Esclaves
Le dictionnaire `RASPBERRY` définit les unités distantes :
*   `IP` : Adresse statique de la Pi esclave.
*   `CAM` : Liste des IDs des caméras connectées à cette unité.

### Caméras
La liste `CAM` définit les propriétés de chaque caméra :
*   `NUMERO` : Identifiant unique.
*   `ACTIVE` : État binaire d'utilisation.
*   `VARIANTE_REQUISE` : Condition de déclenchement liée au code cycle automate.

### Automate
*   `AUTOMATE_IP` : Adresse IP du PLC.
*   `AUTOMATE_DB` : Numéro du bloc de données de lecture.
*   `AUTOMATE_DB_LECTURE` : Offsets (en octets) des variables (VIS, type_vh, etc.).

## 6. Procédures de Paramétrage

### Création d'une zone d'inspection
1. Passer en mode Administrateur via l'interface (mot de passe stocké dans `config.py`).
2. Dessiner la zone sur l'image à l'aide de la souris.
3. Sélectionner le nom du vissage dans la liste déroulante.
4. Cliquer sur "Prendre Réf" pour valider.

### Analyse d'image
*   `MARGE_RECHERCHE` : Zone de balayage autour des coordonnées théoriques.
*   `SCORE_SEUIL` : Valeur minimale (0-100) pour déclarer une zone "OK".

## 7. Dépannage

### Erreurs de communication SSH
*   **Vérification :** Accessibilité de l'IP esclave via `ping`.
*   **Action :** Vérifier les droits SSH et la validité des identifiants dans `config.py`. En cas de remplacement d'une Pi, réinitialiser la clé d'hôte : `ssh-keygen -R [IP]`.

### Erreurs Automate
*   **Vérification :** État du service S7 sur le PLC.
*   **Action :** S'assurer que l'accès PUT/GET est autorisé et que les DB ne sont pas optimisées dans TIA Portal.

### Scores de vision bas
*   **Vérification :** Propreté des optiques et état de l'éclairage.
*   **Action :** Nettoyer la lentille. Si le défaut persiste, recréer la zone de référence en mode Administrateur.

### Saturation mémoire
*   **Vérification :** Espace disponible dans `/dev/shm` (RAM).
*   **Action :** Réduire `CACHE_LIMIT` dans `config.py` ou augmenter la fréquence de nettoyage.

## 8. Maintenance

### Physique (Hebdomadaire)
*   Nettoyage des vitres de protection des caméras.
*   Vérification de la rigidité des supports caméras.
*   Contrôle de l'éclairage industriel.

### Système (Mensuel)
*   Sauvegarde de `historique_production.db`.
*   Sauvegarde des répertoires `/zones/` et `/ref/`.
*   Vérification de l'espace disque sur la Pi Maître.

## 9. Données

### Base de données SQLite
*   Table `inspections` : Entête des contrôles véhicules.
*   Table `zone_results` : Détail des scores par zone (liée par `inspection_id`).

### Archivage des images
*   Chemin : `[HDD_PATH]/YYYY/MM/DD/`.
*   Format du nom : `[Caméra]_[Véhicule]_[Moteur]_[Variante]_[VIS]_[Scores].jpg`.
