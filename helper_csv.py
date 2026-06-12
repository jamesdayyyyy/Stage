#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module de gestion des configurations de zones via fichiers CSV.

Ce module permet de lire et modifier les définitions des zones d'intérêt (ROI)
pour chaque couple véhicule/motorisation. Ces données incluent les coordonnées
de recherche, l'ID de la caméra associée et le type de pièce.

Auteur: James DAY
Date de création: 20 mai 2026
"""

import csv
import os
from config import Config


class ZoneConfigHelper:
    """
    Classe d'aide pour la manipulation des fichiers CSV de configuration des zones.

    Gère le stockage persistant des zones définies par l'utilisateur via l'interface.
    """

    def __init__(self, dossier_base=Config.ZONES_CSV_PATH):
        """
        Initialise l'accès au dossier contenant les fichiers CSV.

        Args:
            dossier_base (str): Chemin vers le dossier des CSV de zones.
        """
        self.dossier_base = dossier_base
        os.makedirs(self.dossier_base, exist_ok=True)

    def _obtenir_chemin_csv(self, vehicule, motorisation):
        """
        Génère le chemin complet du fichier CSV pour un véhicule donné.

        Args:
            vehicule (str): Modèle du véhicule.
            motorisation (str): Motorisation du véhicule.

        Returns:
            str: Chemin vers le fichier .csv.
        """
        return os.path.join(self.dossier_base, f"{vehicule}_{motorisation}.csv")

    def lire_zones(self, vehicule, motorisation, camera_id=None):
        """
        Lit les zones définies pour un véhicule et une motorisation.

        Args:
            vehicule (str): Modèle du véhicule.
            motorisation (str): Motorisation du véhicule.
            camera_id (str/int, optionnel): Filtrer les zones pour une caméra spécifique.

        Returns:
            list: Liste de dictionnaires représentant chaque zone.
        """
        chemin_csv = self._obtenir_chemin_csv(vehicule, motorisation)
        zones = []

        if not os.path.exists(chemin_csv):
            return zones

        try:
            with open(chemin_csv, mode="r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if camera_id is not None and str(row["numero_camera"]) != str(
                        camera_id
                    ):
                        continue

                    row["x0"], row["y0"] = int(row["x0"]), int(row["y0"])
                    row["x1"], row["y1"] = int(row["x1"]), int(row["y1"])
                    zones.append(row)

        except Exception as e:
            print(f"[CSV Helper] Erreur de lecture : {e}")

        return zones

    def sauvegarder_nouvelle_zone(
        self,
        vehicule,
        motorisation,
        camera_id,
        zone_id,
        x0,
        y0,
        x1,
        y1,
        type_zone=None,
        nom_vissage="Inconnu",
    ):
        """
        Ajoute une nouvelle zone de contrôle au fichier CSV.

        Args:
            vehicule (str): Modèle du véhicule.
            motorisation (str): Motorisation du véhicule.
            camera_id (int): ID de la caméra.
            zone_id (int): ID unique de la zone.
            x0, y0 (int): Coordonnées du coin supérieur gauche.
            x1, y1 (int): Coordonnées du coin inférieur droit.
            type_zone (str, optionnel): Variante de la zone.
            nom_vissage (str): Label humain pour la zone.

        Returns:
            bool: True si l'opération a réussi.
        """
        chemin_csv = self._obtenir_chemin_csv(vehicule, motorisation)
        fichier_existe = os.path.exists(chemin_csv)
        colonnes = [
            "numero_camera",
            "numero_zone",
            "x0",
            "y0",
            "x1",
            "y1",
            "type",
            "nom_vissage",
        ]

        try:
            with open(chemin_csv, mode="a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=colonnes)
                if not fichier_existe:
                    writer.writeheader()

                writer.writerow(
                    {
                        "numero_camera": camera_id,
                        "numero_zone": zone_id,
                        "nom_vissage": nom_vissage,
                        "x0": x0,
                        "y0": y0,
                        "x1": x1,
                        "y1": y1,
                        "type": type_zone,
                    }
                )
            return True
        except Exception as e:
            print(f"[CSV Helper] Erreur d'écriture : {e}")
            return False

    def supprimer_zone(self, vehicule, motorisation, camera_id, zone_id):
        """
        Supprime une zone spécifique d'un fichier CSV.

        Args:
            vehicule (str): Modèle du véhicule.
            motorisation (str): Motorisation du véhicule.
            camera_id (int): ID de la caméra associée.
            zone_id (int): ID de la zone à supprimer.

        Returns:
            bool: True si la suppression est confirmée.
        """
        chemin_csv = self._obtenir_chemin_csv(vehicule, motorisation)
        if not os.path.exists(chemin_csv):
            return False
        zones_restantes = []
        entetes = None

        try:
            with open(chemin_csv, mode="r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                entetes = reader.fieldnames
                for row in reader:
                    if not (
                        str(row["numero_camera"]) == str(camera_id)
                        and str(row["numero_zone"]) == str(zone_id)
                    ):
                        zones_restantes.append(row)
                if entetes:
                    with open(chemin_csv, mode="w", newline="", encoding="utf-8") as f:
                        writer = csv.DictWriter(f, fieldnames=entetes)
                        writer.writeheader()
                        writer.writerows(zones_restantes)
                        return True
        except Exception as e:
            print(f"[CSV Helper] Erreur lors de la suppression : {e}")
            return False
