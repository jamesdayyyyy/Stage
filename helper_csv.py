#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed May 20 12:38:01 2026

@author: James DAY
"""

import csv
import os
from config import Config


class ZoneConfigHelper:
    def __init__(self, dossier_base=Config.ZONES_CSV_PATH):
        self.dossier_base = dossier_base
        os.makedirs(self.dossier_base, exist_ok=True)

    def _obtenir_chemin_csv(self, vehicule, motorisation):
        """
        Renvoie le chemin du fichier csv pour un véhicule donné
        Params :
        - véhicule
        - motorisation
        Retourne :
        - chemin du fichier csv"""
        return os.path.join(self.dossier_base, f"{vehicule}_{motorisation}.csv")

    def lire_zones(self, vehicule, motorisation, camera_id=None):
        """
        Lit les zones de référence pour un véhicule et une motorisation donnée
        Params :
        - véhicule
        - motorisation
        - camera_id (optionnel) : si fourni, filtre les zones en fonction de la caméra
        Retourne :
        - liste de dictionnaires
         Chaque dictionnaire contient :
         {
            "numero_camera" : str,
            "numero_zone" : str,
            "x0" : int,
            "y0" : int,
            "x1" : int,
            "y1" : int,
            "type" : str,
            "nom_vissage" : str
         }
         Si le fichier CSV n'existe pas ou en cas d'erreur de lecture, une liste vide sera retournée.

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
        Sauvegarde une nouvelle zone de vissage dans le fichier CSV
        Params:
        - véhicule
        - motorisation
        - camera_id : numéro de la caméra associée à la zone
        - zone_id : numéro de la zone
        - x0, y0 : coordonnées du point en haut à gauche de la zone
        - x1, y1 : coordonnées du point en bas à droite de la zone
        - type_zone : type de la zone
        - nom_vissage : nom du vissage associé à la zone
        Retourne :
        - bool indiquant si la sauvegarde a réussi ou non
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
        Supprime une zone du fichier CSV en filtrant par véhicule, motorisatio, caméra et ID de zone
        Params:
        - véhicule
        - motorisation
        - camera_id : numéro de la caméra associée à la zone
        - zone_id : numéro de la zone à supprimer
        Retourne :
        - bool indiquant si la suppression a réussi ou non
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
