#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Client de déclenchement de prise de vue.

Ce script est appelé par le serveur central (via SSH) pour ordonner la capture
d'une image. Il communique par socket locale avec le démon rasp_camera_keepalive.py
qui maintient la caméra active.

Auteur: James DAY
"""

import socket
import sys

def ask_photo():
    """
    Envoie une commande 'photo' au démon local via une socket TCP.
    Quitte avec le code 0 en cas de succès, 1 sinon.
    """
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(("localhost", 9000))
        client.sendall(b"photo")
        reponse = client.recv(1024).decode('utf-8')
        if reponse == "ok":
            sys.exit(0)
        else: 
            print("[Erreur] Mauvaise reponse keepalive")
            sys.exit(1)
    except ConnectionRefusedError:
        print("[Erreur] Connexion non réusiie - KeepAlive FAIL")
    except Exception as e:
        print(f"[Erreur] {e}")

if __name__ == "__main__":
    ask_photo()