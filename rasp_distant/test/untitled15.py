#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed May 20 20:03:11 2026

@author: James DAY
"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import threading
import time

# On importe les fonctions depuis tes deux fichiers
from simulateur_serveur import serveur_connect
from test_client import ask_photo

if __name__ == "__main__":
    print("[Main] Démarrage du test de communication...")
    
    # 1. On lance le serveur dans un thread en arrière-plan
    # Le paramètre daemon=True permet au thread de s'arrêter tout seul 
    # quand le programme principal se termine.
    serveur_thread = threading.Thread(target=serveur_connect, daemon=True)
    serveur_thread.start()
    
    # 2. On fait une mini-pause pour laisser le temps au serveur 
    # de s'initialiser et d'écouter le port 9000
    time.sleep(0.5)
    
    # 3. On lance le client dans le flux principal
    print("[Main] Lancement du client...\n" + "-"*40)
    ask_photo()
    
    print("-"*40 + "\n[Main] Test terminé avec succès.")