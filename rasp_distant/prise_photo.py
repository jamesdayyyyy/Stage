#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue May 19 10:22:22 2026

@author: James DAY
"""

import socket
import sys

def ask_photo():
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