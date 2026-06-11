#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon May 18 15:05:49 2026

@author: James DAY
"""

import csv 
import os
import cv2
import numpy as np
import glob 

from config import Config

"""
Il faut ajouter la gesiton de type du vehicule
"""

def determiner_path(vehicule, motorisation, type_zone):
    base_dir = f"{Config.REF_PATH}/{vehicule}_{motorisation}"
    if type_zone == "":
        return base_dir
    else :
        return os.path.join(base_dir, type_zone)

def traitement_image(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    return blurred

def analyse_image(queue_in, queue_out, worker_id):
    
    MARGE_RECHERCHE = Config.MARGE_RECHERCHE
    
    while True:
        try:
            info_vehicule = queue_in.get()
            
            path_photo = info_vehicule["image"]
            vehicule = info_vehicule["vehicule"]
            motorisation = info_vehicule["motorisation"]
            camera_id = str(info_vehicule["camera_source"])
            
            print(f"[Vision {worker_id}] Début d'analyse pour Caméra {camera_id} (Véhicule {vehicule})...")
            
            image_couleur = cv2.imread(path_photo)
            
            if image_couleur is None:
                print(f"[Erreur - Vision {worker_id}] Image introuvable : {path_photo}")
                info_vehicule["resultats_vision"] = []
                
                # On envoie quand même dans la queue_out pour débloquer le buffer de l'interface
                queue_out.put(info_vehicule)
                continue
            
            image_traitee = traitement_image(image_couleur)
            h_img, w_img = image_traitee.shape
                
            csv_path = f"{Config.ZONES_CSV_PATH}/{vehicule}_{motorisation}.csv"
            resultats_zones = []
            
            if os.path.exists(csv_path):
                with open(csv_path, newline = "") as csv_data:
                    reader = list(csv.DictReader(csv_data))
                    
                besoin_check = any(str(cam["NUMERO"]) == camera_id and cam.get("VARIANTE_REQUISE") != "" for cam in Config.CAM)

                
                for row in reader:
                    if row["numero_camera"] == camera_id :
                        
                        if besoin_check and row["type"] not in [info_vehicule["variante_active"], "none", "None", ""]:
                            continue
                    
                        zone_id = row["numero_zone"]

                        if zone_id == "0":
                            continue
                        
                        x0 = int(row['x0'])
                        y0 = int(row['y0'])
                        x1 = int(row['x1'])
                        y1 = int(row['y1'])
                    
                        search_x0 = max(0, x0 - MARGE_RECHERCHE)
                        search_y0 = max(0, y0 - MARGE_RECHERCHE)
                        search_x1 = min(w_img, x1 + MARGE_RECHERCHE)
                        search_y1 = min(h_img, y1 + MARGE_RECHERCHE)
                        
                        zone = image_traitee[search_y0:search_y1, search_x0:search_x1]
                        ref_dossier = determiner_path(vehicule, motorisation, row["type"])
                        ref_fichiers = glob.glob(os.path.join(ref_dossier, f"zone_{zone_id}_*.jpg"))
                    
                        meilleur_score = 0.0
                        meilleur_ref = None
                        meilleur_loc = (0,0)
                        for ref_file in ref_fichiers:
                            ref_image = cv2.imread(ref_file)
                            if ref_image is None:
                                continue 
                            ref_traitee = traitement_image(ref_image)
                            if ref_traitee.shape[0] > zone.shape[0] or ref_traitee.shape[1] > zone.shape[1]:
                                continue 
                            res = cv2.matchTemplate(zone, ref_traitee, cv2.TM_CCOEFF_NORMED)
                            _, max_val, _, max_loc = cv2.minMaxLoc(res)

                            if max_val > meilleur_score:
                                meilleur_score = max_val
                                meilleur_ref = ref_file
                                meilleur_loc = max_loc
                            if meilleur_score >= Config.SCORE_SEUIL:
                                break

                        abs_x = search_x0 + meilleur_loc[0]
                        abs_y = search_y0 + meilleur_loc[1]
                        pourcentage = round(meilleur_score *100, 1)
                        nom_vissage = row.get("nom_vissage", f"Zone {zone_id}")

                        resultats_zones.append({
                            "numero_zone" : zone_id,
                            "nom_vissage" : nom_vissage,
                            "score" : pourcentage,
                            "ref_path" : meilleur_ref,
                            "match_x" : abs_x,
                            "match_y" : abs_y
                            })
                        
                        
            info_vehicule["resultats_vision"] = resultats_zones
            
            print(f"[Vision {worker_id}] Analyse terminée (Caméra {camera_id}). {len(resultats_zones)} zones traitées. Envoi à l'UI.")
            
            queue_out.put(info_vehicule)
            
        except Exception as e:
            print(f"[Vision {worker_id}] Crash {e} ")
            info_vehicule.setdefault("resultats_vision", [])
            queue_out.put(info_vehicule)