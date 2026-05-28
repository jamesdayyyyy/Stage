#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed May 20 20:02:38 2026

@author: James DAY
"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import socket
import time

def serveur_connect():
    # Initialisation du socket serveur
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('localhost', 9000))
    server.listen()
    
    print("[Serveur] Démarré et en écoute sur localhost:9000...")
    
    try:
        while True:
            # Attente d'une connexion du client
            connexion, address = server.accept()
            print(f"\n[Serveur] Nouvelle connexion depuis {address}")
            
            # Réception du message
            message = connexion.recv(1024).decode('utf-8')
            print(f"[Serveur] Message reçu : '{message}'")
            
            if message == "photo":
                print("[Serveur] Simulation de la prise de photo (1 sec)...")
                time.sleep(1)  # Simule le temps matériel
                print("[Serveur] Simulation terminée. Envoi de 'ok'.")
                connexion.sendall(b"ok")
            else:
                print(f"[Serveur] Commande inconnue : {message}")
                
            # Fermeture de la connexion pour ce client
            connexion.close()
            print("[Serveur] Connexion terminée avec ce client.")
            
    except KeyboardInterrupt:
        print("\n[Serveur] Arrêt manuel du serveur.")
    except Exception as e:
        print(f"[Erreur] Crash du serveur :\n{e}")
    finally:
        server.close()

if __name__ == "__main__":
    serveur_connect()