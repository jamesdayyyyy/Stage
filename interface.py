#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module de l'interface graphique utilisateur (GUI).

Ce script définit la classe principale ApplicationTkinter qui gère l'affichage
en temps réel des résultats d'inspection, la navigation dans l'historique,
le mode administrateur pour le paramétrage des zones, et la communication
avec les autres modules (BDD, Automate, Stockage).

Auteur: James DAY
Date de création: 18 mai 2026
"""

import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
import os
import queue
import concurrent.futures
from datetime import datetime
import glob
import shutil

from config import Config
from helper_database import Database
from helper_csv import ZoneConfigHelper
from helper_storage import GestionnaireRAM, traiter_stockage
from helper_affichage import Canvas_interactif
from helper_automate import Automate


class ApplicationTkinter:
    """
    Classe principale pilotant l'interface Tkinter du système.

    Responsable du cycle de vie de l'UI : 
    - Consommation de la queue de résultats vision.
    - Affichage des images et des scores.
    - Gestion des alertes (disque plein, erreurs).
    - Mode administrateur (création de références, définition de zones).
    - Envoi des résultats finaux à l'automate.
    """

    def __init__(self, root, queue_in):
        """
        Initialise l'application et ses composants.

        Args:
            root (tk.Tk): Fenêtre racine Tkinter.
            queue_in (multiprocessing.Queue): File d'entrée des résultats d'analyse.
        """
        self.root = root
        self.queue_in = queue_in
        self.root.title("Contrôle Vissages CV")

        self.db = Database()
        self.csv_helper = ZoneConfigHelper()
        self.cache_ram = GestionnaireRAM(nb_voitures_en_cache=Config.CACHE_LIMIT)

        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)

        self.nombre_cams_attendu = len(Config.CAM)
        self.buffer_vehicules = {}

        self.historique_vehicules = []
        self.index_historique = -1
        self.mode_recherche = False
        self.fenetre_recherche = None

        self.mode_admin = False
        self.timer_inactive = None
        self.delai_inactive = Config.DELAI_INACTIVITE

        self.disque_critique = False

        self.infos_vehicule_actuel = []
        self.current_index = 0
        self.zoom_factor = 1.0

        self.setup_ui()

        self.root.after(100, self.process_queue)
        self.verifier_espace_disque()

    def setup_ui(self):
        """Construction de l'interface graphique."""
        # HEADER
        self.header = tk.Label(
            self.root,
            text="Contrôle Vision - En attente...",
            font=("Arial", 20, "bold"),
        )
        self.header.pack(pady=5)

        # BANDEAU ALERTE
        self.bandeau_alerte = tk.Label(
            self.root,
            text="ATTENTION : VOUS CONSULTEZ UN ANCIEN VEHICULE",
            bg="orange",
            fg="white",
            font=("Arial", 14, "bold"),
        )
        self.bandeau_disque = tk.Label(
            self.root, text="", bg="#e74c3c", fg="white", font=("Arial", 14, "bold")
        )

        # MAIN
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill="both", expand=True)

        # MENU GAUCHE
        menu = tk.Frame(main_frame, width=220, bg="#2b2b2b")
        menu.pack(side="left", fill="y", padx=5, pady=5)

        # ZONE ZOOM ET RECHERCHE
        zoom_frame = tk.LabelFrame(
            menu, text="Zoom", bg="#2b2b2b", fg="white", font=("Arial", 10, "bold")
        )
        zoom_frame.pack(fill="x", padx=8, pady=8)
        tk.Button(zoom_frame, text="+", height=2, command=self.zoom_in).pack(
            side="left", fill="x", expand=True, padx=5, pady=5
        )
        tk.Button(zoom_frame, text="-", height=2, command=self.zoom_out).pack(
            side="left", fill="x", expand=True, padx=5, pady=5
        )

        btn_recherche = tk.Button(
            menu,
            text="Recherche véhicule",
            bg="#2b2b2b",
            fg="white",
            font=("Arial", 10, "bold"),
            command=self.ouvrir_gestionnaire,
        )
        btn_recherche.pack(fill="x", padx=8, pady=10)

        self.btn_admin = tk.Button(
            menu,
            text="Modifs : OFF",
            bg="#e74c3c",
            fg="white",
            font=("Arial", 10, "bold"),
            command=self.toggle_admin,
        )
        self.btn_admin.pack(fill="x", padx=8, pady=5)

        # ZONE CAMERAS
        cam_frame = tk.LabelFrame(
            menu, text="Caméras", bg="#2b2b2b", fg="white", font=("Arial", 10, "bold")
        )
        cam_frame.pack(fill="both", expand=True, padx=8, pady=8)

        self.boutons_cameras = {}

        for index, cam_data in enumerate(Config.CAM):
            btn = tk.Button(
                cam_frame,
                text=f"{cam_data['NUMERO']} : {cam_data['NOM']}",
                anchor="w",
                bg="#eeeeee",
                fg="#222222",
                relief="flat",
                command=lambda i=index: self.change_image_by_index(i),
            )
            btn.pack(fill="x", pady=4, padx=4)
            self.boutons_cameras[cam_data["NUMERO"]] = btn

        # ZONE IMAGE PRINCIPALE
        image_frame = tk.Frame(main_frame, bg="black")
        image_frame.pack(fill="both", expand=True)

        # Barre d'infos (Fichier / Date) au dessus de l'image
        info_bar = tk.Frame(image_frame, bg="#333333")
        info_bar.pack(fill="x")

        self.lbl_filename = tk.Label(
            info_bar,
            text="Fichier: -",
            bg="#333333",
            fg="white",
            font=("Arial", 11, "bold"),
        )
        self.lbl_filename.pack(side="left", padx=10, pady=5)

        self.lbl_date = tk.Label(
            info_bar, text="Date: -", bg="#333333", fg="white", font=("Arial", 10)
        )
        self.lbl_date.pack(side="right", padx=10, pady=5)

        # --- INTÉGRATION DU HELPER AFFICHAGE ---
        canvas_container = tk.Frame(image_frame, bg="black")
        canvas_container.pack(fill="both", expand=True)

        self.canvas = Canvas_interactif(
            canvas_container, self.db, self.csv_helper, app=self, max_size=(1200, 800)
        )

        scroll_y = ttk.Scrollbar(
            canvas_container, orient="vertical", command=self.canvas.yview
        )
        scroll_y.pack(side="right", fill="y")

        scroll_x = ttk.Scrollbar(
            canvas_container, orient="horizontal", command=self.canvas.xview
        )
        scroll_x.pack(side="bottom", fill="x")

        self.canvas.pack(side="left", fill="both", expand=True)
        self.canvas.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

        # CONTRÔLES NAVIGATION
        nav_frame = tk.Frame(image_frame, bg="black")
        nav_frame.pack(fill="x", side="bottom", pady=5)

        self.btn_prec = tk.Button(
            nav_frame,
            text="◀ Véhicule Précédent",
            font=("Arial", 12, "bold"),
            bg="#444",
            fg="white",
            command=self.vehicule_precedent,
        )
        self.btn_next = tk.Button(
            nav_frame,
            text="Véhicule Suivant ▶",
            font=("Arial", 12, "bold"),
            bg="#444",
            fg="white",
            command=self.vehicule_suivant,
        )
        self.btn_retour_direct = tk.Button(
            nav_frame,
            text="RETOUR AU DIRECT",
            font=("Arial", 12, "bold"),
            bg="#e74c3c",
            fg="white",
            command=self.retour_au_direct,
        )
        self.btn_next.pack(side="right", padx=20)
        self.btn_prec.pack(side="left", padx=20)
        self.btn_prec.config(state="disabled")
        self.btn_next.config(state="disabled")

        self.root.bind("<Motion>", self.reinitialiser_timer)

    def reinitialiser_timer(self, event=None):
        if self.timer_inactive is not None:
            self.root.after_cancel(self.timer_inactive)
        if self.mode_admin:
            self.timer_inactive = self.root.after(
                self.delai_inactive, self.desactiver_auto_admin
            )

    def desactiver_auto_admin(self):
        if self.mode_admin:
            self.mode_admin = False
            self.btn_admin.config(text="Modifs : OFF", bg="#e74c3c")
            print("[UI] Mode Modification verrouillé automatiquement : inactivité.")

    def toggle_admin(self):
        if self.mode_admin:
            self.mode_admin = False
            self.btn_admin.config(text="Modifs : OFF", bg="#e74c3c")
            if self.timer_inactivite is not None:
                self.root.after_cancel(self.timer_inactivite)
            print("[UI] Mode Modification verrouillé.")
        else:
            mdp = simpledialog.askstring(
                "Authentification", "Entrez le mot de passe pour modifier :", show="*"
            )
            if mdp == Config.PASSWORD:
                self.mode_admin = True
                self.btn_admin.config(text="Modifs : ON", bg="#2ecc71")
                print("[UI] Mode Modification déverrouillé.")
                self.reinitialiser_timer()
            elif mdp is not None:
                messagebox.showerror("Erreur", "Mot de passe incorrect.")

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

    def verifier_espace_disque(self):
        try:
            if os.path.exists(Config.HDD_PATH):
                total, used, free = shutil.disk_usage(Config.HDD_PATH)
                free_gb = free / (1024**3)
                seuil_alerte_gb = 10.0
                if free_gb < 0.244:
                    if not self.disque_critique:
                        self.disque_critique = True
                        print(
                            "[Alerte] Disque dur plein, les contrôles continuent mais sans sauvegarde d'images"
                        )
                        self.bandeau_disque.config(
                            text="MODE DEGRADE : Disque dur plein. Les contrôles continuent mais sans sauvegarde d'images"
                        )
                        self.bandeau_disque.pack(fill="x", after=self.header)

                elif free_gb < seuil_alerte_gb:
                    self.bandeau_disque.config(
                        text=f"ALERTE : Plus que {free_gb:.1f} Go d'espace sur le disque dur ({Config.HDD_PATH}) ! Arrêt stockage dans {free_gb - 0.244} Go"
                    )
                    self.bandeau_disque.pack(fill="x", after=self.header)
                else:
                    self.bandeau_disque.pack_forget()
        except Exception as e:
            print(f"[UI Erreur] Impossible de vérifier l'espace disque: {e}")

        self.root.after(300000, self.verifier_espace_disque)  # relance apres 5 min

    def gerer_reception_image(self, info_vehicule):
        """Regroupe les images par vis pour attendre le lot complet."""
        vis = info_vehicule["vis"]

        if vis not in self.buffer_vehicules:
            self.buffer_vehicules[vis] = []

        self.buffer_vehicules[vis].append(info_vehicule)

        print(
            f"[UI] Réception Cam {info_vehicule['camera_source']} - ({len(self.buffer_vehicules[vis])}/{self.nombre_cams_attendu})"
        )

        if len(self.buffer_vehicules[vis]) == self.nombre_cams_attendu:
            lot_complet = self.buffer_vehicules.pop(vis)
            print("[UI] Lot complet reçu ! Début du traitement.")

            self.executor.submit(self.tache_stockage_arriere_plan, lot_complet)

    def tache_stockage_arriere_plan(self, lot_complet):
        """Exécuté en arrière-plan pour ne pas figer Tkinter."""
        infos_traitees = []
        vehicule_est_ok = True
        erreur_systeme = False
        zones_nok = []

        for info in lot_complet:
            if self.disque_critique:
                info["image_hdd_path"] = ""
                print(f"[Alerte RAM] Pas suffisament de stockage pour HDD")
            else:
                succes_stockage = traiter_stockage(
                    info, Config.HDD_PATH, self.cache_ram
                )

                if not succes_stockage:
                    print(
                        f"[UI/DB] Avertissement: Photo de Cam {info.get('camera_source')} manquante, mais historisée."
                    )
                    info["image_hdd_path"] = ""
                    erreur_systeme = True

            self.db.sauvegarder_info(info)
            infos_traitees.append(info)

            for res in info.get("resultats_vision", []):
                if float(res.get("score", 0.0)) < Config.SCORE_SEUIL:
                    vehicule_est_ok = False
                    nom_defaut = res.get(
                        "nom_vissage", f"Z{res.get('numero_zone', 'X')}"
                    )
                    zones_nok.append(nom_defaut)
        if erreur_systeme:
            vehicule_est_ok = False
        """"
        try:
            automate = Automate(Config.AUTOMATE_IP, Config.AUTOMATE_DB_ENVOIE, Config.AUTOMATE_RACK, Config.AUTOMATE_SLOT)
            automate.envoyer_resultats(vehicule_est_ok, zones_nok, erreur_systeme)
            if automate.client is not None:
                automate.client.disconnect()
                
        except Exception as e:
            print(f"[UI/Automate] Erreur lors de l'envoi des résultats à l'automate : {e}")
        """
        self.root.after(
            0, lambda lot=infos_traitees: self.ajouter_historique_et_afficher(lot)
        )

    def afficher_nouveau_vehicule(self, lot_infos):
        """Met à jour l'état de l'application avec le nouveau véhicule."""
        if not lot_infos:
            return

        if self.mode_recherche:
            self.bandeau_alerte.pack(fill="x", after=self.header)
        else:
            if self.historique_vehicules:
                est_en_direct = (
                    self.index_historique == len(self.historique_vehicules) - 1
                )
            else:
                est_en_direct = True
            if not est_en_direct:
                self.bandeau_alerte.pack(fill="x", after=self.header)
            else:
                self.bandeau_alerte.pack_forget()

        self.infos_vehicule_actuel = sorted(
            lot_infos, key=lambda x: int(x["camera_source"])
        )

        vehicule = self.infos_vehicule_actuel[0]["vehicule"]

        print(
            f"[UI] Mise à jour de l'affichage pour le véhicule {vehicule} avec {len(lot_infos)} caméra(s)."
        )
        if self.index_historique == 0:
            self.btn_prec.config(state="disabled")
        else:
            self.btn_prec.config(state="normal")
        if self.index_historique == len(self.historique_vehicules) - 1:
            self.btn_next.config(state="disabled")
        else:
            self.btn_next.config(state="normal")

        self.header.config(text=f"Véhicule: {vehicule}")

        index_depart = 0
        for i, info_cam in enumerate(self.infos_vehicule_actuel):
            camera_en_defaut = False

            for res in info_cam.get("resultats_vision", []):
                if float(res.get("score", 100.0)) < Config.SCORE_SEUIL:
                    camera_en_defaut = True
                    break

            if camera_en_defaut:
                index_depart = i
                break

        self.change_image_by_index(index_depart)
        self.mettre_a_jour_couleurs_boutons()

    def change_image_by_index(self, index):
        if not self.infos_vehicule_actuel:
            return

        self.current_index = index % len(self.infos_vehicule_actuel)
        info_cam = self.infos_vehicule_actuel[self.current_index]

        chemin_ram = info_cam.get("image", "")
        chemin_hdd = info_cam.get("image_hdd_path", "")

        if chemin_ram and os.path.exists(chemin_ram):
            nom_fichier = os.path.basename(chemin_ram)
        elif chemin_hdd and os.path.exists(chemin_hdd):
            nom_fichier = os.path.basename(chemin_hdd)
        else:
            nom_fichier = "Image introuvable"

        date_obj = datetime.fromtimestamp(info_cam["timestamp"])
        date_str = date_obj.strftime("%d/%m/%Y - %H:%M:%S")

        for index, cam_data in enumerate(Config.CAM):
            if cam_data["NUMERO"] == info_cam["camera_source"]:
                self.header.config(
                    text=f"Caméra {cam_data['NUMERO']}: {cam_data['NOM']}"
                )
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
        self.mettre_a_jour_couleurs_boutons()

    def previous_image(self):
        """Passe à l'image précédente."""
        pass

    def next_image(self):
        """Passe à l'image suivante."""
        pass

    def zoom_in(self):
        self.canvas.zoom_factor *= 1.2
        self.canvas.differer_rafraichissement(100)

    def zoom_out(self):
        self.canvas.zoom_factor *= 0.8
        self.canvas.differer_rafraichissement(100)

    def vehicule_suivant(self):
        if self.index_historique < len(self.historique_vehicules) - 1:
            self.index_historique += 1
            lot_infos = self.historique_vehicules[self.index_historique]
            self.afficher_nouveau_vehicule(lot_infos)
            print(
                f"[UI] Véhicule suivant affiché (Index Historique: {self.index_historique})"
            )
        else:
            print("[UI] Vous êtes déjà sur le dernier véhicule.")

    def vehicule_precedent(self):
        if self.index_historique > 0:
            self.index_historique -= 1
            lot_infos = self.historique_vehicules[self.index_historique]
            self.afficher_nouveau_vehicule(lot_infos)
            print(
                f"[UI] Véhicule précédent affiché (Index Historique: {self.index_historique})"
            )
        else:
            print("[UI] Vous êtes déjà sur le premier véhicule.")

    def ajouter_historique_et_afficher(self, lot_infos):
        if not lot_infos:
            return
        self.historique_vehicules.append(lot_infos)

        if len(self.historique_vehicules) > Config.CACHE_LIMIT:
            self.historique_vehicules.pop(0)
            print("[UI] Historique dépassé, véhicule le plus ancien supprimé.")
        if not self.mode_recherche:
            self.index_historique = len(self.historique_vehicules) - 1
            self.afficher_nouveau_vehicule(
                self.historique_vehicules[self.index_historique]
            )
        else:
            print(
                f"[UI] Un véhicule live a été traité en arrière-plan. (Affichage bloqué par le mode Recherche)"
            )

    def mettre_a_jour_couleurs_boutons(self):
        if not self.infos_vehicule_actuel:
            return
        cam_active = self.infos_vehicule_actuel[self.current_index]["camera_source"]
        for btn in self.boutons_cameras.values():
            btn.config(bg="#eeeeee", fg="#222222", relief="flat", borderwidth=1)
        for info_cam in self.infos_vehicule_actuel:
            cam_id = info_cam["camera_source"]
            camera_defaut = False
            for res in info_cam.get("resultats_vision", []):
                if float(res.get("score", 0.0)) < Config.SCORE_SEUIL:
                    camera_defaut = True
                    break
            if cam_id in self.boutons_cameras:
                if camera_defaut:
                    self.boutons_cameras[cam_id].config(bg="#ff4d3d", fg="white")
                if cam_id == cam_active:
                    self.boutons_cameras[cam_id].config(relief="sunken", borderwidth=3)

    def ouvrir_gestionnaire(self):
        if self.fenetre_recherche is not None and tk.Toplevel.winfo_exists(
            self.fenetre_recherche
        ):
            self.fenetre_recherche.deiconify()
            self.fenetre_recherche.lift()
            self.fenetre_recherche.focus_force()
            return

        self.fenetre_recherche = tk.Toplevel(self.root)
        self.fenetre_recherche.title("Gestionnaire de Fichiers / Archives")
        self.fenetre_recherche.geometry("1200x400")
        self.fenetre_recherche.grab_set()
        self.fenetre_recherche.config(bg="#2b2b2b")

        def on_close_gestionnaire():
            self.fenetre_recherche.destroy()
            self.fenetre_recherche = None

        # Champs de recherche
        search_frame = tk.Frame(self.fenetre_recherche, bg="#2b2b2b")
        search_frame.pack(fill="x", padx=10, pady=10)

        tk.Label(search_frame, text="Statut :", bg="#2b2b2b", fg="white").grid(
            row=0, column=0, padx=5
        )
        ent_statut = ttk.Combobox(
            search_frame, values=["Tous", "OK", "NOK"], state="readonly", width=8
        )
        ent_statut.current(0)
        ent_statut.grid(row=0, column=1, padx=5)

        tk.Label(search_frame, text="VIS :", bg="#2b2b2b", fg="white").grid(
            row=0, column=2, padx=5
        )
        ent_vis = tk.Entry(search_frame)
        ent_vis.grid(row=0, column=3, padx=5)

        tk.Label(search_frame, text="Modèle :", bg="#2b2b2b", fg="white").grid(
            row=0, column=4, padx=5
        )
        ent_veh = tk.Entry(search_frame)
        ent_veh.grid(row=0, column=5, padx=5)

        tk.Label(search_frame, text="Motorisation :", bg="#2b2b2b", fg="white").grid(
            row=0, column=6, padx=5
        )
        ent_mot = tk.Entry(search_frame)
        ent_mot.grid(row=0, column=7, padx=5)

        colonnes = (
            "Statut",
            "VIS",
            "Véhicule",
            "Motorisation",
            "Date & Heure",
            "Timestamp",
        )
        tree = ttk.Treeview(self.fenetre_recherche, columns=colonnes, show="headings")
        tree.tag_configure("DEFAUT", background="#ff4d3d", foreground="white")
        for col in colonnes:
            tree.heading(col, text=col)
            if col == "Timestamp":
                tree.column(col, width=0, stretch=tk.NO)
            elif col == "Statut":
                tree.column(col, width=60, anchor="center")
            else:
                tree.column(col, width=150, anchor="center")
        tree.pack(fill="both", expand=True, padx=10, pady=10)

        def lancer_recherche():
            for item in tree.get_children():
                tree.delete(item)
            resultats = self.db.rechercher_vehicule(
                ent_vis.get(), ent_veh.get(), ent_mot.get(), ent_statut.get()
            )
            for res in resultats:
                vis, veh, mot, timestamp, min_score = res
                date_str = datetime.fromtimestamp(int(timestamp)).strftime(
                    "%d/%m/%Y %H:%M:%S"
                )
                tag_ligne = ()
                if min_score is None:
                    texte_statut = "--"
                elif min_score >= Config.SCORE_SEUIL:
                    texte_statut = "OK"
                else:
                    texte_statut = "NOK"
                    tag_ligne = ("DEFAUT",)
                tree.insert(
                    "",
                    tk.END,
                    values=(texte_statut, vis, veh, mot, date_str, timestamp),
                    tags=tag_ligne,
                )

        tk.Button(
            search_frame,
            text="Rechercher",
            bg="#2b2b2b",
            fg="white",
            command=lancer_recherche,
        ).grid(row=0, column=8, padx=10)

        def on_double_click(event):
            selection = tree.selection()
            if not selection:
                return
            valeurs = tree.item(selection[0], "values")
            vis, timestamp = valeurs[1], valeurs[5]
            self.charger_vehicule_archive(vis, timestamp)
            on_close_gestionnaire()

        tree.bind("<Double-1>", on_double_click)
        lancer_recherche()

    def charger_vehicule_archive(self, vis, timestamp):
        dt = datetime.fromtimestamp(int(timestamp))
        dossier_hdd = os.path.join(
            Config.HDD_PATH, f"{dt.year}/{dt.strftime('%m')}/{dt.strftime('%d')}"
        )
        pattern = os.path.join(dossier_hdd, f"*_{vis}_*.jpg")
        fichiers = glob.glob(pattern)

        if not fichiers:
            print("[UI] Erreur : BDD trouvée mais images purgées du disque dur.")
            return

        lot_reconstruit = []

        for f in fichiers:
            nom_fichier = os.path.basename(f)
            detail = nom_fichier.split("_")
            cam_id, veh, mot = detail[0], detail[1], detail[2]
            if len(detail) == 6:
                variante_archive = detail[3]
            else:
                variante_archive = ""
            chaine = detail[-1].split(".")[0]
            score_factice = 0.0 if "0" in chaine else 100.0

            lot_reconstruit.append(
                {
                    "vis": vis,
                    "vehicule": veh,
                    "motorisation": mot,
                    "camera_source": int(cam_id),
                    "timestamp": int(timestamp),
                    "variante_active": variante_archive,
                    "image_hdd_path": f,
                    "image": "",
                    "resultats_vision": [{"numero_zone": "0", "score": score_factice}],
                }
            )

        self.mode_recherche = True
        self.btn_retour_direct.pack(side="left", padx=20)
        self.btn_prec.pack_forget()
        self.btn_next.pack_forget()
        self.afficher_nouveau_vehicule(lot_reconstruit)
        self.bandeau_alerte.config(
            text=f"MODE ARCHIVE (Analyse en arrière plan activée)"
        )

    def retour_au_direct(self):
        self.mode_recherche = False
        self.btn_retour_direct.pack_forget()
        self.btn_prec.pack(side="left", padx=10)
        self.btn_next.pack(side="right", padx=10)
        self.bandeau_alerte.config(text="ATTENTION : VOUS CONSULTEZ UN ANCIEN VEHICULE")

        if self.historique_vehicules:
            self.index_historique = len(self.historique_vehicules) - 1
            self.afficher_nouveau_vehicule(
                self.historique_vehicules[self.index_historique]
            )
        print("[UI] Retour au visionnage en direct.")
