#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed May 20 09:54:35 2026

@author: James DAY
"""
import time 
import os 
import shutil
from collections import deque
from datetime import datetime
from config import Config

class GestionnaireRAM:
    def __init__(self, nb_voitures_en_cache=Config.CACHE_LIMIT, cams_par_voiture=len(Config.CAM)):
        # 2 voitures * 14 caméras = 28 images maximum gardées en RAM
        self.capacite_max = nb_voitures_en_cache * cams_par_voiture
        self.fichiers_en_ram = deque()

    def ajouter_et_nettoyer(self, chemin_ram):
        """Ajoute la nouvelle image au cache et supprime la plus vieille si plein."""
        self.fichiers_en_ram.append(chemin_ram)
        
        if len(self.fichiers_en_ram) > self.capacite_max:
            plus_vieux_fichier = self.fichiers_en_ram.popleft()
            
            try:
                if os.path.exists(plus_vieux_fichier):
                    os.remove(plus_vieux_fichier)
                    print(f"[RAM Cache] Nettoyage : {os.path.basename(plus_vieux_fichier)} supprimé.")
            except Exception as e:
                print(f"[RAM Cache Error] Impossible de supprimer {plus_vieux_fichier} : {e}")

def generer_nom(info_vehicule):
    camera = info_vehicule.get('camera_source', 'X')    
    vehicule = info_vehicule.get('vehicule', "Inconnu")
    motorisation = info_vehicule.get('motorisation', "Inconnu")
    variante = info_vehicule.get('variante_active')
    vis = info_vehicule.get('vis', "Inconnu")
    
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
        return f"{camera}_{vehicule}_{motorisation}_{vis}_{chaine_controle}.jpg"
    return f"{camera}_{vehicule}_{motorisation}_{variante}_{vis}_{chaine_controle}.jpg"

def traiter_stockage(info_vehicule, hdd_path, cache_ram=None):
    image_temp_ram = info_vehicule.get("image")
    if not image_temp_ram or not os.path.exists(image_temp_ram):
        print(f"[Storage] Image temp non trouvée {image_temp_ram}")
        return None
    
    try :
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
        os.makedirs(chemin_hdd_1, exist_ok = True)
        
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
    if type_mat in [None, "None", "none", ""]:
        nom = f"{camera}_{vehicule}_{motorisation}_{vis}_{chaine_controle}.jpg"
    else:
        nom = f"{camera}_{vehicule}_{motorisation}_{type_mat}_{vis}_{chaine_controle}.jpg"
    return nom