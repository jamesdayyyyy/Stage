#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module de gestion des communications réseau.

Ce module gère les connexions SSH avec les Raspberry Pi distantes pour la capture
d'images, ainsi que l'échange de données avec l'automate industriel (PLC) pour
détecter la présence des véhicules et récupérer leurs caractéristiques.

Auteur: James DAY
Date de création: 18 mai 2026
"""

import time
import concurrent.futures
import os
import paramiko
import snap7
from snap7.util import get_bool, get_string

from helper_automate import Automate
from config import Config


class Connexion_SSH:
    """
    Gère une connexion SSH persistante vers un Raspberry Pi esclave.

    Cette classe permet d'exécuter des scripts de prise de vue à distance et de
    rapatrier les fichiers images via SFTP.

    Attributs:
        numero (int): Identifiant de la Pi.
        ip (str): Adresse IP de la Pi.
        username (str): Nom d'utilisateur SSH.
        password (str): Mot de passe SSH.
        cameras (list): Liste des IDs de caméras connectées à cette Pi.
        ssh (paramiko.SSHClient): Instance du client SSH.
    """

    def __init__(self, pi):
        """Initialise et tente la connexion SSH."""
        self.numero = pi["NUMERO"]
        self.ip = pi["IP"]
        self.username = pi["USERNAME"]
        self.password = pi["PASSWORD"]
        self.cameras = pi["CAM"]
        self.ssh = None
        self.connect()

    def connect(self):
        """Établit la connexion SSH et lance le service de maintien de caméra."""
        try:
            self.ssh = paramiko.SSHClient()
            self.ssh.load_system_host_keys()
            self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.ssh.connect(
                self.ip,
                username=self.username,
                password=self.password,
                port=22,
                timeout=5,
            )
            self.ssh.get_transport().set_keepalive(15)
            print(f"[SSH] Connecté avec succès à la Pi {self.numero} ({self.ip})")
            self.ssh.exec_command(
                f"nohup python3 /home/{self.username}/rasp_camera_keepalive.py > /dev/null 2>&1 &"
            )

        except Exception as e:
            print(f"[Erreur - Pi {self.numero}] Échec de la connexion : {e}")
            self.ssh = None

    def get_photo(self):
        """
        Déclenche la prise de photo sur la Pi et télécharge les fichiers.

        Returns:
            list: Liste de dictionnaires contenant le chemin local et l'ID de la caméra.
        """
        if self.ssh is None or not self.ssh.get_transport().is_active():
            print(f"[Réseau] Pi {self.numero} hors ligne. Reconnexion...")
            self.connect()
        if self.ssh is None:
            return []
        images = []
        try:
            stdin, stdout, sterr = self.ssh.exec_command(
                f"python3 /home/{self.username}/prise_photo.py"
            )
            erreur = sterr.read().decode("utf-8")
            out = stdout.read().decode("utf-8")
            print(out)
            if erreur != "":
                print(f"[Erreur - Pi {self.numero}] {erreur}")
                return []
            sftp = self.ssh.open_sftp()
            for camera in self.cameras:
                print(
                    f"[Réseau - Pi {self.numero}] Téléchargement photo Caméra {camera} en cours..."
                )
                path_origine = f"/dev/shm/cam{camera}.jpg"
                fichier = f"cam{camera}.jpg"
                path_temp = os.path.join(Config.TEMPORAIRE_PATH, fichier)

                sftp.get(path_origine, path_temp)
                sftp.remove(path_origine)
                print(
                    f"[Réseau - Pi {self.numero}] Photo Caméra {camera} rapatriée avec succès dans {path_temp}"
                )
                images.append({"path": path_temp, "camera_id": camera})

            sftp.close()
            return images

        except Exception as e:
            print(f"[Erreur - Pi {self.numero}] {e}")
            self.ssh.close()
            self.ssh = None
            return []


def check_capture(queue_out):
    """
    Boucle de surveillance de l'automate (exécutée dans un processus séparé).

    Détecte le passage d'un nouveau véhicule, déclenche la capture sur toutes
    les Pi en parallèle, et envoie les informations à la file d'analyse vision.

    Args:
        queue_out (multiprocessing.Queue): File d'attente vers le module vision.
    """
    connexions_ssh = [
        Connexion_SSH(rasp) for rasp in Config.RASPBERRY if rasp["NUMERO"] != 0
    ]
    automate = Automate(
        ip=Config.AUTOMATE_IP,
        db_numero=Config.AUTOMATE_DB,
        rack=Config.AUTOMATE_RACK,
        slot=Config.AUTOMATE_SLOT,
    )
    ancien_etat_presence = False
    print("[Systeme] En ecoute ... Attente voiture")
    try:
        while True:
            time.sleep(0.1)
            data = automate.lire_data()
            if data is None:
                continue
            nouveau_etat_presence = data.get("vh_dans_pas", False)
            if nouveau_etat_presence and not ancien_etat_presence:
                print("[Système] Véhicule détecté. Préparation à la capture...")
                timestamp = time.time()
                vehicule = {
                    "vis": data.get("vis", ""),
                    "vehicule": data.get("vehicule", ""),
                    "motorisation": data.get("motorisation", ""),
                    "variantes": data.get("variantes", {}),
                }
                with concurrent.futures.ThreadPoolExecutor(
                    max_workers=len(connexions_ssh)
                ) as executor:
                    futures = [
                        executor.submit(rasp.get_photo) for rasp in connexions_ssh
                    ]

                    for future in concurrent.futures.as_completed(futures):
                        liste_images = future.result()
                        for img_data in liste_images:
                            id_camera_actuelle = img_data["camera_id"]
                            variante_active = ""

                            for cam in Config.CAM:
                                if cam["NUMERO"] == id_camera_actuelle:
                                    cle_requise = cam.get("VARIANTE_REQUISE", "")
                                    if cle_requise:
                                        variante_active = vehicule["variantes"].get(
                                            cle_requise, ""
                                        )
                                        break

                            to_send = {
                                "vis": vehicule["vis"],
                                "vehicule": vehicule["vehicule"],
                                "motorisation": vehicule["motorisation"],
                                "timestamp": int(timestamp),
                                "image": img_data["path"],
                                "camera_source": img_data["camera_id"],
                                "variante_active": variante_active,
                            }

                            queue_out.put(to_send)
            elif not nouveau_etat_presence and ancien_etat_presence:
                print(
                    "[Système] Le véhicule a quitté le pas. Réinitialisation de l'automate..."
                )
                automate.reset_data()
            ancien_etat_presence = nouveau_etat_presence

    except KeyboardInterrupt:
        print("\n[Système] Arret clavier")
    except Exception as e:
        print(f"\n[Erreur] {e}")
