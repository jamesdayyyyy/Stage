#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module de gestion du stockage des images (RAM et HDD).

Ce module gère le cycle de vie des images capturées :
1. Renommage selon une convention stricte (VIS, scores, caméra).
2. Mise en cache en RAM (/dev/shm) avec nettoyage automatique.
3. Archivage permanent sur disque dur (HDD) avec une structure par date.

Auteur: James DAY
Date de création: 20 mai 2026
"""

import os
import shutil
from collections import deque
from datetime import datetime
from config import Config


class GestionnaireRAM:
    """
    Gestionnaire de cache pour les images stockées en RAM.

    Permet de limiter l'occupation mémoire en supprimant les fichiers les plus
    anciens une fois la capacité maximale atteinte.
    """

    def __init__(
        self, nb_voitures_en_cache=Config.CACHE_LIMIT, cams_par_voiture=len(Config.CAM)
    ):
        """
        Initialise le cache avec une capacité calculée.

        Args:
            nb_voitures_en_cache (int): Nombre de véhicules complets à garder.
            cams_par_voiture (int): Nombre de caméras par véhicule.
        """
        # 2 voitures * 14 caméras = 28 images maximum gardées en RAM
        self.capacite_max = nb_voitures_en_cache * cams_par_voiture
        self.fichiers_en_ram = deque()

    def ajouter_et_nettoyer(self, chemin_ram):
        """
        Ajoute une image au cache et supprime le fichier le plus ancien si plein.

        Args:
            chemin_ram (str): Chemin du nouveau fichier image en RAM.
        """
        self.fichiers_en_ram.append(chemin_ram)

        if len(self.fichiers_en_ram) > self.capacite_max:
            plus_vieux_fichier = self.fichiers_en_ram.popleft()

            try:
                if os.path.exists(plus_vieux_fichier):
                    os.remove(plus_vieux_fichier)
                    print(
                        f"[RAM Cache] Nettoyage : {os.path.basename(plus_vieux_fichier)} supprimé."
                    )
            except Exception as e:
                print(
                    f"[RAM Cache Error] Impossible de supprimer {plus_vieux_fichier} : {e}"
                )


def generer_nom(info_vehicule):
    """
    Génère un nom de fichier standardisé basé sur les données de l'inspection.

    Format : {camera}_{vehicule}_{motorisation}_{variante}_{vis}_{chaine_scores}.jpg

    Args:
        info_vehicule (dict): Données complètes du véhicule et de l'analyse.

    Returns:
        str: Nom de fichier généré.
    """
    camera = info_vehicule.get("camera_source", "X")
    vehicule = info_vehicule.get("vehicule", "Inconnu")
    motorisation = info_vehicule.get("motorisation", "Inconnu")
    variante = info_vehicule.get("variante_active")
    vis = info_vehicule.get("vis", "Inconnu")
    sequence = info_vehicule.get ("sequence", "Inconnu")

    resultats = info_vehicule.get("resultats_vision", [])
    try:
        resultats_tries = sorted(resultats, key=lambda x: int(x.get("numero_zone", 0)))
    except ValueError:
        resultats_tries = resultats

    chaine_controle = ""
    for res in resultats_tries:
        score = float(res.get("score", 0.0))
        if score >= Config.SCORE_SEUIL:
            chaine_controle += "1"
        else:
            chaine_controle += "0"

    if variante in [None, "None", "none", ""]:
        return f"{camera}_{vehicule}_{motorisation}_{vis}_{chaine_controle}_{sequence}.jpg"
    return f"{camera}_{vehicule}_{motorisation}_{variante}_{vis}_{chaine_controle}_{sequence}.jpg"


def traiter_stockage(info_vehicule, hdd_path, cache_ram=None):
    """
    Renomme l'image en RAM et effectue la copie de sauvegarde sur le HDD.

    Args:
        info_vehicule (dict): Données de l'inspection.
        hdd_path (str): Chemin racine du disque dur pour l'archivage.
        cache_ram (GestionnaireRAM, optionnel): Instance pour le nettoyage du cache.

    Returns:
        bool: True si les opérations de stockage ont réussi.
    """
    image_temp_ram = info_vehicule.get("image")
    if not image_temp_ram or not os.path.exists(image_temp_ram):
        print(f"[Storage] Image temp non trouvée {image_temp_ram}")
        return None

    try:
        nouveau_nom = generer_nom(info_vehicule)
        dossier_ram = os.path.dirname(image_temp_ram)
        nouveau_chemin_ram = os.path.join(dossier_ram, nouveau_nom)
        os.rename(image_temp_ram, nouveau_chemin_ram)

        info_vehicule["image"] = nouveau_chemin_ram

        timestamp = info_vehicule["timestamp"]
        date = datetime.fromtimestamp(timestamp)
        year = date.year
        month = date.strftime("%m")
        day = date.strftime("%d")
        chemin_hdd_1 = os.path.join(hdd_path, f"{year}/{month}/{day}")
        os.makedirs(chemin_hdd_1, exist_ok=True)

        chemin_hdd = os.path.join(chemin_hdd_1, nouveau_nom)
        shutil.copy2(nouveau_chemin_ram, chemin_hdd)

        print(f"[Stockage] Image sauvegardée avec succès sur HDD : {chemin_hdd}")

        info_vehicule["image_hdd_path"] = chemin_hdd

        if cache_ram is not None:
            cache_ram.ajouter_et_nettoyer(nouveau_chemin_ram)
        return True
    except Exception as e:
        print(f"[Storage ERROR] echec traitement : {e}")


def modifier_nom(camera, vehicule, motorisation, type_mat, vis, chaine_controle):
    """
    Utilitaire pour générer un nom de fichier à partir de paramètres explicites.

    Args:
        camera (int): ID de la caméra.
        vehicule (str): Modèle.
        motorisation (str): Motorisation.
        type_mat (str): Variante/Matériau.
        vis (str): VIS.
        chaine_controle (str): Suite de 0 et 1 pour les scores.

    Returns:
        str: Nom de fichier .jpg généré.
    """
    if type_mat in [None, "None", "none", ""]:
        nom = f"{camera}_{vehicule}_{motorisation}_{vis}_{chaine_controle}.jpg"
    else:
        nom = (
            f"{camera}_{vehicule}_{motorisation}_{type_mat}_{vis}_{chaine_controle}.jpg"
        )
    return nom
