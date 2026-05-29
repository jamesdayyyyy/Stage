import tkinter as tk
import os
import queue
import concurrent.futures
from datetime import datetime

from config import Config
from helper_database import Database
from helper_csv import ZoneConfigHelper
from helper_storage import GestionnaireRAM, traiter_stockage
from helper_affichage import Canvas_interactif

class ApplicationTkinter:
    def __init__(self, root, queue_in):
        self.root = root
        self.queue_in = queue_in
        self.root.title("Contrôle Vissages CV")

        self.db = Database()
        self.csv_helper = ZoneConfigHelper()
        self.cache_ram = GestionnaireRAM(nb_voitures_en_cache=Config.CACHE_LIMIT)
        
        # Thread pool pour l'écriture disque/DB sans bloquer l'interface
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)
        
        # Gestion des lots (Attendre le bon nombre de photos)
        self.nombre_cams_attendu = len(Config.CAM)
        self.buffer_vehicules = {}

        self.historique_vehicules = []
        self.index_historique = -1
        
        # État de la visualisation
        self.infos_vehicule_actuel = []
        self.current_index = 0
        self.zoom_factor = 1.0

        self.setup_ui()
        
        # Lancement de la boucle d'écoute de la Queue
        self.root.after(100, self.process_queue)

    def setup_ui(self):
        """Construction de l'interface graphique."""
        # HEADER
        self.header = tk.Label(self.root, text="Contrôle Vision - En attente...", font=("Arial", 20, "bold"))
        self.header.pack(pady=5)

        # BANDEAU ALERTE 
        self.bandeau_alerte = tk.Label(self.root, text="ATTENTION : VOUS CONSULTEZ UN ANCIEN VEHICULE", bg="orange", fg="white", font=("Arial", 14, "bold"))

        # MAIN
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill="both", expand=True)

        # MENU GAUCHE
        menu = tk.Frame(main_frame, width=220, bg="#2b2b2b")
        menu.pack(side="left", fill="y", padx=5, pady=5)

        # ZONE ZOOM
        zoom_frame = tk.LabelFrame(menu, text="Zoom", bg="#2b2b2b", fg="white", font=("Arial", 10, "bold"))
        zoom_frame.pack(fill="x", padx=8, pady=8)
        tk.Button(zoom_frame, text="+", height=2, command=self.zoom_in).pack(side="left", fill="x", expand=True, padx=5, pady=5)
        tk.Button(zoom_frame, text="-", height=2, command=self.zoom_out).pack(side="left", fill="x", expand=True, padx=5, pady=5)

        # ZONE CAMERAS
        cam_frame = tk.LabelFrame(menu, text="Caméras", bg="#2b2b2b", fg="white", font=("Arial", 10, "bold"))
        cam_frame.pack(fill="both", expand=True, padx=8, pady=8)

        self.boutons_cameras = []

        for index, cam_data in enumerate(Config.CAM):
            btn = tk.Button(
                cam_frame,
                text=cam_data["NOM"],
                anchor="w", bg="#eeeeee", fg="#222222", relief="flat",
                command=lambda i=index: self.change_image_by_index(i)
            )
            btn.pack(fill="x", pady=4, padx=4)
            self.boutons_cameras[cam_data["NUMERO"]] = btn


        # ZONE IMAGE PRINCIPALE
        image_frame = tk.Frame(main_frame, bg="black")
        image_frame.pack(fill="both", expand=True)
        
        # Barre d'infos (Fichier / Date) au dessus de l'image
        info_bar = tk.Frame(image_frame, bg="#333333")
        info_bar.pack(fill="x")
        
        self.lbl_filename = tk.Label(info_bar, text="Fichier: -", bg="#333333", fg="white", font=("Arial", 11, "bold"))
        self.lbl_filename.pack(side="left", padx=10, pady=5)
        
        self.lbl_date = tk.Label(info_bar, text="Date: -", bg="#333333", fg="white", font=("Arial", 10))
        self.lbl_date.pack(side="right", padx=10, pady=5)

        # --- INTÉGRATION DU HELPER AFFICHAGE ---
        self.canvas = Canvas_interactif(image_frame, self.db, self.csv_helper, app = self, max_size=(1200, 800))
        self.canvas.pack(fill="both", expand=True)

        # CONTRÔLES NAVIGATION
        nav_frame = tk.Frame(image_frame, bg="black")
        nav_frame.pack(fill="x", side="bottom", pady=5)
        
        tk.Button(nav_frame, text="◀ Caméra Précédente", font=("Arial", 12, "bold"), bg="#444", fg="white", command=self.vehicule_precedent).pack(side="left", padx=20)
        tk.Button(nav_frame, text="Caméra Suivante ▶", font=("Arial", 12, "bold"), bg="#444", fg="white", command=self.vehicule_suivant).pack(side="right", padx=20)


    def process_queue(self):
        """Vérifie si de nouvelles images sont arrivées de vision.py."""
        try:
            while True: 
                info_vehicule = self.queue_in.get_nowait()
                self.gerer_reception_image(info_vehicule)
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self.process_queue)

    def gerer_reception_image(self, info_vehicule):
        """Regroupe les images par vis pour attendre le lot complet."""
        vis = info_vehicule["vis"]
        
        if vis not in self.buffer_vehicules:
            self.buffer_vehicules[vis] = []
            
        self.buffer_vehicules[vis].append(info_vehicule)
        
        print(f"[UI] Réception Cam {info_vehicule['camera_source']} - ({len(self.buffer_vehicules[vis])}/{self.nombre_cams_attendu})")

        if len(self.buffer_vehicules[vis]) == self.nombre_cams_attendu:
            lot_complet = self.buffer_vehicules.pop(vis)
            print("[UI] Lot complet reçu ! Début du traitement.")
            
            self.executor.submit(self.tache_stockage_arriere_plan, lot_complet)

    def tache_stockage_arriere_plan(self, lot_complet):
        """Exécuté en arrière-plan pour ne pas figer Tkinter."""
        infos_traitees = []
        
        for info in lot_complet:
            succes_stockage = traiter_stockage(info, Config.HDD_PATH, self.cache_ram)
            
            if not succes_stockage:
                print(f"[UI/DB] Avertissement: Photo de Cam {info.get('camera_source')} manquante, mais historisée.")
                info["image_hdd_path"] = ""
            self.db.sauvegarder_info(info)
            infos_traitees.append(info)
                
        self.root.after(0, lambda lot=infos_traitees: self.ajouter_historique_et_afficher(lot))

    def afficher_nouveau_vehicule(self, lot_infos):
        """Met à jour l'état de l'application avec le nouveau véhicule."""
        if not lot_infos: return
        
        if self.historique_vehicules:
            est_en_direct = (self.index_historique == len(self.historique_vehicules) - 1)
        else : est_en_direct = True
        if not est_en_direct:
            self.bandeau_alerte.pack(fill="x", after=self.header)
        else:
            self.bandeau_alerte.pack_forget()

        # On trie la liste par numéro de caméra pour la navigation
        self.infos_vehicule_actuel = sorted(lot_infos, key=lambda x: int(x["camera_source"]))
        
        vehicule = self.infos_vehicule_actuel[0]["vehicule"]
        
        print(f"[UI] Mise à jour de l'affichage pour le véhicule {vehicule} avec {len(lot_infos)} caméra(s).")
        
        self.header.config(text=f"Véhicule: {vehicule}")
        self.change_image_by_index(0)
        self.mettre_a_jour_couleurs_boutons()

    def change_image_by_index(self, index):
        if not self.infos_vehicule_actuel: return
        
        self.current_index = index % len(self.infos_vehicule_actuel)
        info_cam = self.infos_vehicule_actuel[self.current_index]
        
        chemin_ram = info_cam.get("image", "")
        nom_fichier = os.path.basename(chemin_ram)
        
        date_obj = datetime.fromtimestamp(info_cam["timestamp"])
        date_str = date_obj.strftime("%d/%m/%Y - %H:%M:%S")
        
        for index, cam_data in enumerate(Config.CAM):
            if cam_data["NUMERO"] == info_cam["camera_source"]:
                self.header.config(text=f"Véhicule: {info_cam.get('vehicule', 'Inconnu')} - Caméra: {cam_data['NOM']}")
                break
            
        self.lbl_filename.config(text=f"Fichier: {nom_fichier}")
        self.lbl_date.config(text=f"Date: {date_str}")
        
        if os.path.exists(chemin_ram):
            self.canvas.charger_image(chemin_ram)
        else:
            chemin_hdd = info_cam.get("image_hdd_path", "")
            if os.path.exists(chemin_hdd):
                self.canvas.charger_image(chemin_hdd)
            else:
                print("[UI Erreur] Image introuvable ni en RAM ni sur HDD.")

    def previous_image(self):
        """Passe à l'image précédente."""
        pass

    def next_image(self):
        """Passe à l'image suivante."""
        pass

    def zoom_in(self):
        self.canvas.zoom_factor *= 1.2
        self.canvas.rafraichir_image()

    def zoom_out(self):
        self.canvas.zoom_factor *= 0.8
        self.canvas.rafraichir_image()
    
    def vehicule_suivant(self):
        if self.index_historique < len(self.historique_vehicules) - 1:
            self.index_historique += 1
            lot_infos = self.historique_vehicules[self.index_historique]
            self.afficher_nouveau_vehicule(lot_infos)
            print(f"[UI] Véhicule suivant affiché (Index Historique: {self.index_historique})")
        else:
            print("[UI] Vous êtes déjà sur le dernier véhicule.")

    def vehicule_precedent(self):
        if self.index_historique > 0:
            self.index_historique -= 1
            lot_infos = self.historique_vehicules[self.index_historique]
            self.afficher_nouveau_vehicule(lot_infos)
            print(f"[UI] Véhicule précédent affiché (Index Historique: {self.index_historique})")
        else:
            print("[UI] Vous êtes déjà sur le premier véhicule.")

    def ajouter_historique_et_afficher(self,lot_infos):
        if not lot_infos: return    
        self.historique_vehicules.append(lot_infos)
        
        if len(self.historique_vehicules) > Config.CACHE_LIMIT:
            self.historique_vehicules.pop(0)
            print("[UI] Historique dépassé, véhicule le plus ancien supprimé.")
        self.index_historique = len(self.historique_vehicules) - 1
        self.afficher_nouveau_vehicule(self.historique_vehicules[self.index_historique])

    def mettre_a_jour_couleurs_boutons(self):
        if not self.infos_vehicule_actuel: return 

        for btn in self.boutons_cameras.values():
            btn.config(bg="#eeeeee",fg="#222222")
        for info_cam in self.infos_vehicule_actuel:
            cam_id = info_cam["camera_source"]
            camera_defaut = False 
            for res in info_cam.get("resultats_vision", []):
                if float(res.get("score"), 0.0) < Config.SCORE_SEUIL:
                    camera_defaut = True
                    break
                if cam_id in self.boutons_cameras:
                    if camera_defaut:
                        self.boutons_cameras[cam_id].config(bg="#ff4d3d", fg="white")
