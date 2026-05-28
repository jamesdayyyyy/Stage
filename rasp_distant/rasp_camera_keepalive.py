#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue May 19 09:36:10 2026

@author: James DAY
"""

import socket
from config_pi import Config
import os
import time 

from picamera2 import Picamera2
from libcamera import controls


def activer_cam():
    photo_info = {}
    for i in range(len(Config.CAM)):
        photo_path = os.path.join(Config.PATH_PHOTO, f"cam{Config.CAM[i]}.jpg")
        picam2 = Picamera2(i)
        photo_config = picam2.create_still_configuration(
            main= {"size" : (4056,3040)}
            )
        picam2.configure(photo_config)
        picam2.start()
        time.sleep(2)
        picam2.set_controls({"AfMode" : controls.AfModeEnum.Manual, "LensPosition" : 1/0.3})
        
        photo_info[i] = {
            "photo_path" : photo_path,
            "picam2" : picam2,
            "cam_id" : Config.CAM[i]
            }
        print(f"[Configuration] Cam {Config.CAM[i]} sur port {i}")
    return photo_info
    
def serveur_connect():
    
    try:
        photo_info = activer_cam()
        
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(('localhost', 9000))
        server.listen()
        
        print("[Daemon] Serveur en écoute sur le port 9000...")

        while True:
            connexion, address = server.accept()
            message = connexion.recv(1024).decode('utf-8')
            if message == "photo":
                for idx, cam_data in photo_info.items():
                        picam = cam_data["picam2"]
                        path = cam_data["photo_path"]
                        
                        picam.capture_file(path)
                        print(f"[Daemon] Photo prise : {path}")
                connexion.sendall(b"ok")
            connexion.close()
    except Exception as e:
        print(f"[Erreur] - Communication socket et prise de photo échouée :\n{e}")
        