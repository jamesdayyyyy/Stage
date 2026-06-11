#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed May 20 13:59:32 2026

@author: James DAY
"""

import tkinter as tk 
from tkinter import messagebox, ttk
from PIL import Image, ImageTk
import os 
import cv2
import sqlite3
from config import Config
import numpy as np
import glob

class Canvas_interactif(tk.Canvas):
    def __init__(self, parent, db, csv_helper, app = None, max_size = (800,600), **kwargs):
        """
        Initialise un canvas interactif
        """
        super().__init__(parent, cursor="cross",bg = "black", **kwargs)
        self.db = db
        self.csv_helper = csv_helper
        self.app = app
        self.max_w, self.max_h = max_size
        
        self.image_path = None
        self.image_originale_cv = None
        self.image_tk = None 
        
        self.zone_en_deplacement = None
        self.offset_drag_x = 0
        self.offset_drag_y = 0
        self.largeur_drag = 0
        self.hauteur_drag = 0
        self.type_drag = ""
        
        self.canvas_w = 800
        self.canvas_h = 600
        self.ratio = 1.0
        self.zoom_factor = 1.0 
        self.offset_x = 0
        self.offset_y = 0
        
        self.camera = self.vehicule = self.motorisation = self.variante_active = self.vis = None

        self.timer_rafraichissement = None
        
        self.rect = None 
        self.start_x = self.start_y = self.end_x = self.end_y = None 
        
        self.bind("<Configure>", self.on_resize)
        self.bind("<ButtonPress-1>", self.on_press)
        self.bind("<B1-Motion>", self.on_drag)
        self.bind("<ButtonRelease-1>", self.on_release)
        self.bind('<Button-3>', self.on_right_click)
    
    def obtenir_zone_sous_clic(self, orig_x, orig_y):
        """
        Vérifie si les coordonnées du clic correspondent à une zone existante
        Tient compte des coordonées de match et de la zone d'origine
        Params :
        - orig_x, orig_y : coordonnées du clic en pixels sur l'image originale (non redimensionnée)
        Retourne :
        - Si une zone est trouvée : (zone_id, x0_reel, y0_reel, x1_reel, y1_reel, type_zone)
        - Si aucune zone n'est trouvée : None
        """
        zones_existantes = self.csv_helper.lire_zones(self.vehicule, self.motorisation, self.camera)
        scores = self.obtenir_scores_db()
        for z in zones_existantes:
            if z.get("type", "") not in [self.variante_active, "none", "None", ""]:
                continue
            z_id = str(z["numero_zone"])
            data_score = scores.get(z_id)
            match_x = data_score.get("match_x") if data_score else None
            match_y = data_score.get("match_y") if data_score else None

            largeur = int(z['x1']) - int(z['x0'])
            hauteur = int(z['y1']) - int(z['y0'])

            if match_x is not None and match_y is not None:
                if match_x < orig_x < match_x + largeur and match_y < orig_y < match_y + hauteur:
                    return z_id, match_x, match_y, match_x + largeur, match_y + hauteur, z.get("type", "")
            if int(z['x0']) < orig_x < int(z['x1']) and int(z['y0']) < orig_y < int(z['y1']):
                return z_id, int(z['x0']), int(z['y0']), int(z['x1']), int(z['y1']), z.get("type", "")
        return None
                
    def on_resize(self,event):
        """
        Déclanché lors du redimensionnement du canvas
        Ajuste la taille de l'image et les zones
        Params :
        - event : événement de redimensionnement contenant les nouvelles dimensions du canvas
        Retourne :
        - None
        """
        if event.width > 5 and event.height > 5:
            self.canvas_h = event.height
            self.canvas_w = event.width
            if self.image_path:
                self.differer_rafraichissement(200)   

    def extract_data(self, path):
        """
        Extrait les données de nomenclature du fichier image
        Params : 
        -path : chemin du fichier image
        Retourne :
        - True si extraction réussie, False sinon
        """
        nom_fichier = os.path.basename(path)
        detail = nom_fichier.split("_")
        
        if len(detail) == 6:
            self.camera = detail[0]
            self.vehicule = detail[1]
            self.motorisation = detail[2]
            self.variante_active = detail[3]
            self.vis = detail[4]
            self.controle = detail[5].split(".")[0]
                
        elif len(detail) == 5:
            self.camera = detail[0]
            self.vehicule = detail[1]
            self.motorisation = detail[2]
            self.vis = detail[3]
            self.controle = detail[4].split(".")[0]
            self.variante_active = ""
        
        else:
            print("Erreur : nomination fichier incorrect")
            return False
        
        besoin_check = False
        for cam in Config.CAM:
            if str(cam["NUMERO"]) == str(self.camera):
                besoin_check = cam.get("VARIANTE_REQUISE", "")
                break
        if not besoin_check:
            self.variante_active = ""

        return True 
                    
    def charger_image(self,path):
        """
        Charge une image depuis le chemin spécifié et l'affiche sur le canvas
        Params :
        - path : chemin du fichier image à charger
        Retourne :
        - None"""
        if not os.path.exists(path):
            print(f"[Canvas Erreur] Fichier introuvable : {path}")
            return
        
        self.image_path = path
        self.image_originale_cv = cv2.imread(path)
        if not self.extract_data(path) : return

        self.zoom_factor = 1
        self.rafraichir_image()
          
    def rafraichir_image(self):
        """
        Rafraichit l'image affichée en s'adaptant au zoom et à la taille du canvas
        Paramas : 
        - None
        Retourne :
        - None
        """
        if self.image_originale_cv is None : return
        
        h_orig, w_orig = self.image_originale_cv.shape[:2]

        ratio_base = min(self.canvas_w / w_orig, self.canvas_h / h_orig)
        self.ratio = ratio_base * self.zoom_factor
        new_w, new_h = int(w_orig * self.ratio), int(h_orig * self.ratio)
        self.offset_x = max(0, (self.canvas_w - new_w) // 2)
        self.offset_y = max(0, (self.canvas_h - new_h) // 2)
       
        img_resized = cv2.resize(self.image_originale_cv, (new_w, new_h), interpolation=cv2.INTER_AREA)
               
        img_rgb = cv2.cvtColor(img_resized, cv2.COLOR_BGR2RGB)
        self.image_tk = ImageTk.PhotoImage(image=Image.fromarray(img_rgb))
       
        self.delete("image_fond")
        
        self.create_image(self.offset_x, self.offset_y, anchor="nw", image=self.image_tk, tags=("image_fond",))  
        self.tag_lower("image_fond")

        self.dessiner_zones()
        self.tag_raise("zone_rect")
        self.tag_raise("zone_text")

        self.config(scrollregion=(0, 0, max(self.canvas_w, new_w), max(self.canvas_h, new_h)))
        
    def obtenir_scores_db(self):
        """
        Récupère les scores de la base de données pour le VIS et la caméra actuelle
        Params : 
        - None
        Retourne :
        - Dictionnaire : {zone_id: {"score": score, "match_x": match_x, "match_y": match_y}}
        """
        scores_dict = {}
        try:
            conn = sqlite3.connect(self.db.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                           SELECT zr.zone_id, zr.score, zr.match_x, zr.match_y
                           FROM zone_results zr
                           JOIN inspections i ON zr.inspection_id = i.id
                           WHERE i.vis = ? AND i.camera = ?
                           ''', (self.vis, self.camera))
            for row in cursor.fetchall():
                scores_dict[str(row[0])] = {"score": row[1], "match_x": row[2], "match_y": row[3]}
            conn.close()
        except Exception as e:
            print(f"[Canvas DB Error] Impossible de lire les scores : {e}")
        return scores_dict
            
    def dessiner_zones(self):
        """
        Dessine les zones configurées sur l'image en fonction du score
        Params :
        -None
        Retourne :
        -None
        """
        self.delete("zone_rect")
        self.delete("zone_text")
        
        zones_config = self.csv_helper.lire_zones(self.vehicule, self.motorisation, self.camera)
        scores = self.obtenir_scores_db()
        
        for z in zones_config:
            z_id = str(z["numero_zone"])
            if z.get("type") in [self.variante_active, "none", "None", ""]:
                x0 = int(float(z["x0"]) * self.ratio) + self.offset_x
                y0 = int(float(z["y0"]) * self.ratio) + self.offset_y
                x1 = int(float(z["x1"]) * self.ratio) + self.offset_x
                y1 = int(float(z["y1"]) * self.ratio) + self.offset_y
                
                if z_id == "0":
                    couleur = "blue"
                    texte = f"Zone {z_id} : TRIAGE"
                    self.create_rectangle(x0, y0, x1, y1, outline=couleur, width=2, tags=("zone_rect",f"zone_{z_id}",f"carre_{z_id}",))
                    self.create_text((x0+x1)/2, y1+10, text=texte, fill=couleur, tags=("zone_text",f'zone_{z_id}',f"carre_{z_id}",))
                else:
                    data_score = scores.get(z_id)
                    score = data_score.get("score") if data_score else None
                    match_x = data_score.get("match_x") if data_score else None
                    match_y = data_score.get("match_y") if data_score else None
                    if score is not None:
                        couleur = "red" if score < Config.SCORE_SEUIL else  "#00ff00"
                        texte = f"Zone {z_id} : {score}%"
                        if match_x is not None and match_y is not None:
                            largeur_zone = x1 - x0
                            hauteur_zone = y1 - y0
                            pos_x = int(match_x * self.ratio) + self.offset_x
                            pos_y = int(match_y * self.ratio) + self.offset_y
                            self.create_rectangle(x0, y0, x1, y1, outline="#555555", dash=(4, 4), width=1, tags=("zone_rect", f"zone_{z_id}",f"ref_{z_id}",))
                            self.create_rectangle(pos_x, pos_y, pos_x+largeur_zone, pos_y+hauteur_zone, outline=couleur, width=2, tags=("zone_rect",f"zone_{z_id}",f"carre_{z_id}",))
                            self.create_text(pos_x + largeur_zone/2, pos_y + hauteur_zone + 10, text=texte, fill=couleur, tags=("zone_text",f'zone_{z_id}',f"carre_{z_id}",))
                        else:
                            self.create_rectangle(x0, y0, x1, y1, outline=couleur, width=2, tags=("zone_rect",f"zone_{z_id}",f"carre_{z_id}",))
                            self.create_text((x0+x1)/2, y1+10, text=texte, fill=couleur, tags=("zone_text",f'zone_{z_id}',f"carre_{z_id}",))

                    else:
                        couleur = "orange"
                        texte = f"Zone {z_id} : NA"
                        self.create_rectangle(x0, y0, x1, y1, outline=couleur, width=2, tags=("zone_rect",f"zone_{z_id}",f"carre_{z_id}",))
                        self.create_text((x0+x1)/2, y1+10, text=texte, fill=couleur, tags=("zone_text",f'zone_{z_id}',f"carre_{z_id}",))
        
    def on_press(self, event):
        """
        Déclanché lors du clic gauche sur le canvas pour créer zone ou ajouter référence
        Params :
        - event : événement de clic contenant les coordonnées du clic
        Retourne :
        - None
        """
        if self.app and not self.app.mode_admin:
            messagebox.showwarning("Verrouillé", "Activez le mode modification pour interagir.")
            return
        
        if not self.image_path:
             return
        
        orig_x = int((self.canvasx(event.x) - self.offset_x) / self.ratio)
        orig_y = int((self.canvasy(event.y) - self.offset_y) / self.ratio)

        zone_clique = self.obtenir_zone_sous_clic(orig_x, orig_y)
        if zone_clique:
            z_id, x0, y0, x1, y1, z_type = zone_clique
            self.zone_en_deplacement = z_id
            self.offset_drag_x = orig_x - x0
            self.offset_drag_y = orig_y - y0
            self.largeur_drag = x1 - x0
            self.hauteur_drag = y1 - y0
            self.type_drag = z_type

            self.last_mouse_x = self.canvasx(event.x)
            self.last_mouse_y = self.canvasy(event.y)
            return

        self.start_x, self.start_y = self.canvasx(event.x), self.canvasy(event.y)
        if self.rect:
             self.delete(self.rect)
        self.rect = self.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y, outline="green")
        self.end_x = self.end_y = None

    def on_drag(self, event):
        """
        Déclanché lors du clic gauche et glissé sur le canvas pour afficher le rectangle de sélection
        Params :
        - event : événement de clic contenant les coordonnées du clic
        Retourne :
        - None
        """
        if not self.image_path: return

        if self.zone_en_deplacement:
            current_x = self.canvasx(event.x)
            current_y = self.canvasy(event.y)

            dx = current_x - self.last_mouse_x
            dy = current_y - self.last_mouse_y
            self.move(f"zone_{self.zone_en_deplacement}", dx, dy)

            self.last_mouse_x = current_x
            self.last_mouse_y = current_y
            return

        self.end_x, self.end_y = self.canvasx(event.x), self.canvasy(event.y)
        self.coords(self.rect, self.start_x, self.start_y, self.end_x, self.end_y)
        
    def on_release(self, event):
        """
        Déclanché lors de la fin du clic gauche sur le canvas pour créer une zone ou ajouter une référence selon la taille du rectangle
        Params :
        - event : événement de clic contenant les coordonnées du clic
        Retourne :
        - None
        """
        if not self.image_path : return 

        if hasattr(self, "zone_en_deplacement") and self.zone_en_deplacement:
            orig_x = int((self.canvasx(event.x) - self.offset_x) / self.ratio)
            orig_y = int((self.canvasy(event.y) - self.offset_y) / self.ratio)

            x0_reel = orig_x - self.offset_drag_x
            y0_reel = orig_y - self.offset_drag_y
            x1_reel = x0_reel + self.largeur_drag
            y1_reel = y0_reel + self.hauteur_drag
            
            z_id = self.zone_en_deplacement
            z_type = self.type_drag

            h_orig, w_orig = self.image_originale_cv.shape[:2]
            x0_reel, y0_reel = max(0, min(x0_reel, w_orig)), max(0, min(y0_reel, h_orig))
            x1_reel, y1_reel = max(0, min(x1_reel, w_orig)), max(0, min(y1_reel, h_orig))

            self.zone_en_deplacement = None

            if messagebox.askquestion("Ajouter référence", f"Ajouter cette image comme référence pour la zone {z_id} ?") == "yes":
                cropped_img = self.image_originale_cv[y0_reel:y1_reel, x0_reel:x1_reel]
                target_dir = self._get_target_directory(z_type)
                os.makedirs(target_dir, exist_ok=True)
                    
                path_pattern = os.path.join(target_dir, f"zone_{z_id}_%s.jpg")
                i = 1
                while os.path.exists(path_pattern % i): 
                    i += 1
                        
                cv2.imwrite(path_pattern % i, cropped_img)
                
                # Tracer dans la DB
                self.db.add_reference_to_db(self.vis, self.vehicule, self.camera, z_id, x0_reel, y0_reel)
                print(f"[Canvas] Référence ajoutée pour Zone {z_id}")

                if self.app and self.app.infos_vehicule_actuel:
                    for info_cam in self.app.infos_vehicule_actuel:
                        if str(info_cam["camera_source"]) == str(self.camera):
                            for res in info_cam.get("resultats_vision", []):
                                if str(res["numero_zone"]) == str(z_id):
                                    res["score"] = 100.0
                                    res["match_x"] = x0_reel
                                    res["match_y"] = y0_reel
                    self.app.mettre_a_jour_couleurs_boutons()
            self.rafraichir_image()
            return

        if not self.start_x: return
        
        mouvement_x = abs(self.start_x - self.end_x) if self.end_x else 0
        mouvement_y = abs(self.start_y - self.end_y) if self.end_y else 0
        
        if mouvement_x > 10 and mouvement_y > 10:
            if messagebox.askquestion("Ajouter", "Ajouter une nouvelle zone irréversible ?") == "yes": 
                self.action_creer_zone()
            else:
                self.delete(self.rect)
                self.rect = None 
                self.end_x = self.end_y = None
        else:
            self.delete(self.rect)
            self.rect = None 
            self.end_x = self.end_y = None
            self.action_ajouter_reference()
            

    def _get_target_directory(self, type_zone=None):
        """
        Détermine le répertoire cible pour enregistrer les images de référence en fonction du type de zone
        Params :
        - type_zone : type de la zone 
        Retourne :
        - chemin du répertoire cible
        """
        base_dir = f"{Config.REF_PATH}/{self.vehicule}_{self.motorisation}"
        
        if type_zone is not None:
            if type_zone in ["none", "None", ""]:
                return base_dir
            else:
                return os.path.join(base_dir, type_zone)
                
        if self.variante_active in ["none", "None", ""]:
            return base_dir
        else:
            return os.path.join(base_dir, self.variante_active)              

    def action_creer_zone(self):
        """
        Crée une nouvelle zone en fonction du rectangle tracé, vérifie les chevauchements, 
        demande le nom du vissage, sauvegarde dans le CSV et la DB, et rafraîchit l'affichage
        Params :
        - None
        Retourne :
        - None
        """
        h_orig, w_orig = self.image_originale_cv.shape[:2]
        
        orig_x0 = int((min(self.start_x, self.end_x) - self.offset_x) / self.ratio)
        orig_x1 = int((max(self.start_x, self.end_x) - self.offset_x) / self.ratio)
        orig_y0 = int((min(self.start_y, self.end_y) - self.offset_y) / self.ratio)
        orig_y1 = int((max(self.start_y, self.end_y) - self.offset_y) / self.ratio)
        
        orig_x0 = max(0, min(orig_x0, w_orig))
        orig_x1 = max(0, min(orig_x1, w_orig))
        orig_y0 = max(0, min(orig_y0, h_orig))
        orig_y1 = max(0, min(orig_y1, h_orig))
        
        zones_existantes = self.csv_helper.lire_zones(self.vehicule, self.motorisation, self.camera)
        for z in zones_existantes:
            if z["type"] == self.variante_active :
                chevauchement = not (orig_x1 <= int(z['x0']) or orig_x0 >= int(z['x1']) or orig_y1 <= int(z['y0']) or orig_y0 >= int(z['y1']))
                if chevauchement:
                    messagebox.showwarning("Collision", f"La zone chevauche avec la zone {z['numero_zone']}")
                    self.delete(self.rect)
                    return
                    
        new_id = self.obtenir_prochain_id_zone(self.vehicule, self.motorisation, self.variante_active)
                
        if self.rect:
            self.delete(self.rect)
            self.rect = None
        self.end_x = self.end_y = None

        nom_vissage = "Inconnu"

        if new_id == 0:
            zone_triage = self.image_originale_cv[orig_y0:orig_y1, orig_x0:orig_x1]
            gray = cv2.cvtColor(zone_triage, cv2.COLOR_BGR2GRAY)
            variance = np.var(gray)
            
            if variance > Config.TYPE_MATERIAU_SEUIL:
                self.variante_active = "M"
            else:
                self.variante_active = "C"
        else:
            nom_vissage_temp = self.afficher_popup_nom()
            if nom_vissage_temp is None:
                self.delete(self.rect)
                self.rect = None 
                self.end_x = self.end_y = None
                return 
            
            nom_vissage = nom_vissage_temp
            
        self.csv_helper.sauvegarder_nouvelle_zone(
            self.vehicule, self.motorisation, self.camera, new_id, 
            orig_x0, orig_y0, orig_x1, orig_y1, self.variante_active, nom_vissage
            )
        
        if new_id != 0:
            cropped_img = self.image_originale_cv[orig_y0:orig_y1, orig_x0:orig_x1]
            target_dir = self._get_target_directory()
            os.makedirs(target_dir, exist_ok=True)
            cv2.imwrite(os.path.join(target_dir, f"zone_{new_id}_1.jpg"), cropped_img)
            self.db.add_reference_to_db(self.vis, self.vehicule, self.camera, new_id)

            path_to_change = self.image_path
            path_to_change = path_to_change[:-4]
            path_to_change = path_to_change + "1.jpg"
            os.rename(self.image_path, path_to_change)
            self.image_path = path_to_change
        else :
            self.db.update_type_materiau(self.vis, self.camera, self.variante_active)

        print(f"[Canvas] Zone {new_id} créée et historisée.")

        self.charger_image(self.image_path)
            
    def action_ajouter_reference(self):
        """
        Ajoute une image de référence pour la zone cliquée, demande confirmation, sauvegarde l'image, met à jour la DB et rafraîchit l'affichage
        Params :
        - None
        Retourne :
        - None
        """
        orig_x = int((self.start_x - self.offset_x) / self.ratio)
        orig_y = int((self.start_y - self.offset_y) / self.ratio)
    
        resultat_clic = self.obtenir_zone_sous_clic(orig_x, orig_y)
        if resultat_clic:
            z_id, x0_reel, y0_reel, x1_reel, y1_reel, z_type = resultat_clic
            if messagebox.askquestion("Ajouter Référence", f"Ajouter image de référence pour la zone {z_id} ?") == "yes":
                cropped_img = self.image_originale_cv[y0_reel:y1_reel, x0_reel:x1_reel]
                target_dir = self._get_target_directory(z_type)
                os.makedirs(target_dir, exist_ok=True)
                    
                path_pattern = os.path.join(target_dir, f"zone_{z_id}_%s.jpg")
                i = 1
                while os.path.exists(path_pattern % i): 
                    i += 1
                        
                cv2.imwrite(path_pattern % i, cropped_img)
                
                # Tracer dans la DB
                self.db.add_reference_to_db(self.vis, self.vehicule, self.camera, z_id)
                print(f"[Canvas] Référence ajoutée pour Zone {z_id}")

                if self.app and self.app.infos_vehicule_actuel:
                    for info_cam in self.app.infos_vehicule_actuel:
                        if str(info_cam["camera_source"]) == str(self.camera):
                            for res in info_cam.get("resultats_vision", []):
                                if str(res["numero_zone"]) == str(z_id):
                                    res["score"] = 100.0
                    self.app.mettre_a_jour_couleurs_boutons()

                self.delete(f"zone_{z_id}")

                x0 = int(x0_reel * self.ratio) + self.offset_x
                y0 = int(y0_reel * self.ratio) + self.offset_y
                x1 = int(x1_reel * self.ratio) + self.offset_x
                y1 = int(y1_reel * self.ratio) + self.offset_y
                
                couleur = "#00ff00"
                texte = f"Zone {z_id} : 100%"

                self.create_rectangle(x0, y0, x1, y1, outline=couleur, width=2, tags=("zone_rect",f"zone_{z_id}",f"carre_{z_id}",))
                self.create_text((x0+x1)/2, y1+10, text=texte, fill=couleur, tags=("zone_text",f'zone_{z_id}',f"carre_{z_id}",))
            return
            
            
    def obtenir_prochain_id_zone(self, vehicule, motorisation, type_actuel):
        """
        Détermine le prochain ID de zone à utiliser
        Params :
        - vehicule
        - motorisation
        - type_actuel : type de la zone actuelle
        Retourne :
        - id de zone disponible pour le type actuel
        """

        zones = self.csv_helper.lire_zones(vehicule, motorisation)
        
        def norm_type(t):
            return "" if t in ["None", "none", None, ""] else str(t)

        type_actuel_norm = norm_type(type_actuel)

        zones_cam = [z for z in zones if str(z.get('numero_camera')) == str(self.camera)]
        
        ids_du_type_actuel = set()
        ids_des_autres_types = set()

        for z in zones_cam:
            z_id_str = str(z.get('numero_zone', ''))
            if not z_id_str.isdigit():
                continue
            z_id = int(z_id_str)
            
            if norm_type(z.get('type')) == type_actuel_norm:
                ids_du_type_actuel.add(z_id)
            else:
                ids_des_autres_types.add(z_id)


        zones_orphelines = ids_des_autres_types - ids_du_type_actuel
        if zones_orphelines:
            return min(zones_orphelines)


        ids_utilises_vehicule = set(
            int(z['numero_zone']) for z in zones if str(z.get('numero_zone', '')).isdigit()
        )
        
        i = 1
        while i in ids_utilises_vehicule:
            i += 1
        return i
    
    def afficher_popup_nom(self):
        """
        Affiche un popup pour sélectionne le nom du vissage 
        Params :
        - None
        Retourne :
        - Le nom du vissage sélectionné ou None si annulé
        """
        fenetre = tk.Toplevel(self.master)
        fenetre.title("Nom du vissage")
        fenetre.geometry("400x150")
        fenetre.grab_set()

        tk.Label(fenetre, text="Sélectionnez le nom du vissage :").pack(pady=15)

        nom_var = tk.StringVar()
        liste_noms = getattr(Config, "NOM_VIS", ["Vissage"])
        combo = ttk.Combobox(fenetre, textvariable=nom_var, values=liste_noms, state="readonly")

        if liste_noms:
            combo.current(0)
        combo.pack(pady=10)
        resultat = {"nom": None}

        def valider():
            resultat["nom"] = nom_var.get()
            fenetre.destroy()
        
        def annuler():
            fenetre.destroy()
        
        btn_frame = tk.Frame(fenetre)
        btn_frame.pack(pady=15)
        tk.Button(btn_frame, text="Valider", command=valider).pack(side=tk.LEFT, padx=10)
        tk.Button(btn_frame, text="Annuler", command=annuler).pack(side=tk.LEFT, padx=10)

        self.wait_window(fenetre)
        return resultat["nom"]
    
    def on_right_click(self, event):
        """
        Déclanché lors du clic droit sur le canvas pour supprimer une zone
        Params :
        - event : événement de clic contenant les coordonnées du clic
        Retourne :
        - None"""
        if self.app and not self.app.mode_admin:
            messagebox.showwarning("Verrouillé", "Activez le mode modification pour supprimer une zone.")
            return
        orig_x = int((self.canvasx(event.x) - self.offset_x) / self.ratio)
        orig_y = int((self.canvasy(event.y) - self.offset_y) / self.ratio)
        resultat_clic = self.obtenir_zone_sous_clic(orig_x, orig_y)
        if resultat_clic:
            z_id, _, _, _, _, z_type = resultat_clic
            if messagebox.askyesno("Supprimer la zone", f"Voulez-vous vraiment supprimer définitivement la Zone {z_id} ?\n\nCela effacera également toutes ses images de référence."):
                self.csv_helper.supprimer_zone(self.vehicule, self.motorisation, self.camera, z_id)
                target_dir = self._get_target_directory(z_type)
                pattern = os.path.join(target_dir, f"zone_{z_id}_*.jpg")
                fichiers_ref = glob.glob(pattern)
                
                for f in fichiers_ref:
                    try:
                        os.remove(f)
                    except Exception as e:
                        print(f"[Canvas] Impossible de supprimer {f} : {e}")

                print(f"[Canvas] Zone {z_id} supprimée avec succès (CSV et {len(fichiers_ref)} image(s) effacée(s)).")
                if self.app and self.app.infos_vehicule_actuel:
                    for info_cam in self.app.infos_vehicule_actuel:
                        if str(info_cam["camera_source"]) == str(self.camera):
                            info_cam["resultats_vision"] = [
                                res for res in info_cam.get("resultats_vision", []) 
                                if str(res.get("numero_zone")) != str(z_id)
                            ]
                    self.app.mettre_a_jour_couleurs_boutons()
                self.rafraichir_image()

    def differer_rafraichissement(self, delai=150):
        """
        Système Anti-Lag : Annule le précédent rafraîchissement s'il n'est pas encore exécuté, 
        et en programme un nouveau dans 'delai' millisecondes.
        Params:
        - délait en millisecondes
        Retourne:
        - Nones
        """
        if self.timer_rafraichissement is not None:
            self.after_cancel(self.timer_rafraichissement)
        self.timer_rafraichissement = self.after(delai, self.rafraichir_image)