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
        return os.path.join(self.dossier_base, f"{vehicule}_{motorisation}.csv")

    def lire_zones(self, vehicule, motorisation, camera_id=None):
        chemin_csv = self._obtenir_chemin_csv(vehicule, motorisation)
        zones = []
        
        if not os.path.exists(chemin_csv):
            return zones 

        try:
            with open(chemin_csv, mode='r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if camera_id is not None and str(row["numero_camera"]) != str(camera_id):
                        continue
                        
                    row['x0'], row['y0'] = int(row['x0']), int(row['y0'])
                    row['x1'], row['y1'] = int(row['x1']), int(row['y1'])
                    zones.append(row)
                    
        except Exception as e:
            print(f"[CSV Helper] Erreur de lecture : {e}")
            
        return zones

    def sauvegarder_nouvelle_zone(self, vehicule, motorisation, camera_id, zone_id, x0, y0, x1, y1, type_zone = None, nom_vissage = "Inconnu"):
        chemin_csv = self._obtenir_chemin_csv(vehicule, motorisation)
        fichier_existe = os.path.exists(chemin_csv)
        colonnes = ["numero_camera", "numero_zone", "x0", "y0", "x1", "y1", "type"]

        try:
            with open(chemin_csv, mode='a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=colonnes)
                if not fichier_existe:
                    writer.writeheader()
                    
                writer.writerow({
                    "numero_camera": camera_id,
                    "numero_zone": zone_id,
                    "nom_visage" : nom_vissage,
                    "x0": x0, "y0": y0, "x1": x1, "y1": y1,
                    "type": type_zone
                })
            return True
        except Exception as e:
            print(f"[CSV Helper] Erreur d'écriture : {e}")
            return False