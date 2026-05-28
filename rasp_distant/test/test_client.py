#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed May 20 20:02:58 2026

@author: James DAY
"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import socket
import sys

def ask_photo():
    try:
        # Création et connexion du socket client
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print("[Client] Tentative de connexion au serveur...")
        client.connect(("localhost", 9000))
        
        # Envoi de la commande
        print("[Client] Connecté. Envoi de la commande 'photo'...")
        client.sendall(b"photo")
        
        # Attente de la réponse
        print("[Client] En attente de la réponse du serveur...")
        reponse = client.recv(1024).decode('utf-8')
        
        # Vérification de la réponse
        if reponse == "ok":
            print(f"[Client] Succès ! Réponse reçue : '{reponse}'")
            sys.exit(0)
        else: 
            print(f"[Erreur] Mauvaise réponse reçue : '{reponse}'")
            sys.exit(1)
            
    except ConnectionRefusedError:
        print("[Erreur] Connexion refusée. Le serveur est-il bien lancé ?")
        sys.exit(1)
    except Exception as e:
        print(f"[Erreur Client] : {e}")
        sys.exit(1)

if __name__ == "__main__":
    ask_photo()