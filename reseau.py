#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon May 18 15:00:32 2026

@author: James DAY
"""

import time
import RPi.GPIO as GPIO
import concurrent.futures
import os
from config import Config
import paramiko
import snap7
from snap7.util import get_bool, get_string

class Connexion_SSH:
    def __init__(self,pi):
        self.numero = pi["NUMERO"]
        self.ip = pi["IP"]
        self.username = pi["USERNAME"]
        self.password = pi["PASSWORD"]
        self.cameras = pi["CAM"]
        self.ssh = None
        self.connect()
        
    def connect(self):
        try:
            self.ssh = paramiko.SSHClient()
            self.ssh.load_system_host_keys()
            self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.ssh.connect(self.ip,
                        username = self.username,
                        password = self.password,
                        port = 22,
                        timeout = 5)
            self.ssh.get_transport().set_keepalive(15)
            print(f"[SSH] Connecté avec succès à la Pi {self.numero} ({self.ip})")
            self.ssh.exec_command(f"nohup python3 /home/{self.username}/rasp_camera_keepalive.py > /dev/null 2>&1 &")
            
        except Exception as e:
            print(f"[Erreur - Pi {self.numero}] Échec de la connexion : {e}")
            self.ssh = None
    
    def get_photo(self):
        if self.ssh is None or not self.ssh.get_transport().is_active():
            print(f"[Réseau] Pi {self.numero} hors ligne. Reconnexion...")
            self.connect()
        if self.ssh is None :
            return []
        images = []
        try :
            stdin, stdout,sterr = self.ssh.exec_command(f"python3 /home/{self.username}/prise_photo.py")
            erreur = sterr.read().decode('utf-8')
            out = stdout.read().decode('utf-8')
            print(out)
            if erreur != "":
                print(f"[Erreur - Pi {self.numero}] {erreur}")
                return []
            sftp = self.ssh.open_sftp()
            for camera in self.cameras:
                print(f"[Réseau - Pi {self.numero}] Téléchargement photo Caméra {camera} en cours...")
                path_origine = f"/dev/shm/cam{camera}.jpg"
                fichier = f"cam{camera}.jpg"
                path_temp = os.path.join(Config.TEMPORAIRE_PATH, fichier)
            
                sftp.get(path_origine, path_temp)
                sftp.remove(path_origine)
                print(f"[Réseau - Pi {self.numero}] Photo Caméra {camera} rapatriée avec succès dans {path_temp}")
                images.append({
                    "path" : path_temp,
                    "camera_id" : camera
                    })
                
            sftp.close()
            return images

        except Exception as e:
            print(f"[Erreur - Pi {self.numero}] {e}")
            self.ssh.close()
            self.ssh = None
            return []
        
class Automate:
    def __init__(self, ip, db_numero, rack=0,slot=0):
        self.ip = ip
        self.db_numero = db_numero
        self.rack = rack
        self.slot = slot
        self.client = snap7.client.Client()
        self.connect()
    
    def connect(self):
        try:
            self.client.connect(self.ip, self.rack, self.slot)
            print(f"[Automate] Connecté à l'automate")
        except Exception as e:
            print(f"[Erreur - Automate {self.ip}] Échec de la connexion : {e}")
            self.client = None
    
    def lire_data(self):
        if self.client is None or not self.client.get_connected():
            print("[Automate] Automate hors ligne. Reconnexion...")
            self.connect()
        if self.client is None:
            print("[Automate] Impossible de se connecter à l'automate.")
            return None
        try:
            data = self.automate.db_read(self.db_numero,0,40)
            vh_dans_pas = get_bool(data,0,0)
            vis = get_string(data,2,8).strip()
            type_vh = get_string(data,12,3).strip() # Non utilisé
            silhouette = get_string(data, 18,3).strip() # Non utilisé
            code_moteur = get_string(data, 24,3).strip()
            type_ecran = get_string(data, 30, 3).strip()

            info_traduite = Config.MAPPING_AUTOMATE.get(
                code_moteur, 
                {"vehicule": "Inconnu", "motorisation": code_moteur}
                )

            return {
                "vh_dans_pas" : vh_dans_pas,
                "vis" : vis,
                "vehicule" : info_traduite.get("vehicule", "Inconnu"),
                "motorisation" : info_traduite.get("motorisation", "Inconnu"),
                "type_ecran" : type_ecran
                }
        
        except Exception as e:
            print(f"[Erreur - Automate] {e}")
            self.client.disconnect()
            self.client = None
            return None

def check_capture(queue_out):
    connexions_ssh = [Connexion_SSH(rasp) for rasp in Config.RASPBERRY if rasp["NUMERO"] != 0]
    automate = Automate(
        ip = Config.AUTOMATE_IP,
        db_numero= Config.AUTOMATE_DB,
        rack = Config.AUTOMATE_RACK,
        slot = Config.AUTOMATE_SLOT
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
                    "badge" : data.get("badge", ""),
                    "vis" : data.get("vis", ""),
                    "vehicule" : data.get("vehicule", ""),
                    "motorisation" : data.get("motorisation", ""),
                    "silhouette" : data.get("silhouette", ""),
                }
                with concurrent.futures.ThreadPoolExecutor(max_workers = len(connexions_ssh)) as executor:
                    futures = [executor.submit(rasp.get_photo) for rasp in connexions_ssh]
                    
                    for future in concurrent.futures.as_completed(futures):
                        liste_images = future.result()
                        for img_data in liste_images:
                            to_send = {
                                **vehicule,
                                "timestamp" : int(timestamp),
                                "image": img_data["path"],
                                "camera_source": img_data["camera_id"]
                                }
                            queue_out.put(to_send)
            ancien_etat_presence = nouveau_etat_presence
            
    except KeyboardInterrupt:
        print("\n[Système] Arret clavier")
    except Exception as e:
        print(f"\n[Erreur] {e}")
        
    finally:
        GPIO.cleanup()