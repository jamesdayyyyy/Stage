#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Point d'entrée principal de l'application de contrôle qualité par vision.

Ce script initialise les files d'attente (queues) pour la communication entre processus
et lance les différents composants de l'application :
- Un processus de capture réseau (réception des images).
- Deux processus d'analyse d'image (vision par ordinateur) pour paralléliser les calculs.
- L'interface graphique utilisateur (Tkinter).

Auteur: James DAY
Date de création: 18 mai 2026
"""

import multiprocessing
import tkinter as tk

from interface import ApplicationTkinter
from reseau import check_capture
from vision import analyse_image

if __name__ == "__main__":
    print("[Main] Initialisation")

    queue_reseau_vers_vision = multiprocessing.Queue()
    queue_vision_vers_ui = multiprocessing.Queue()

    process_reseau = multiprocessing.Process(
        target=check_capture, args=(queue_reseau_vers_vision,)
    )
    process_vision_1 = multiprocessing.Process(
        target=analyse_image,
        args=(queue_reseau_vers_vision, queue_vision_vers_ui, "Core 3"),
    )
    process_vision_2 = multiprocessing.Process(
        target=analyse_image,
        args=(queue_reseau_vers_vision, queue_vision_vers_ui, "Core 4"),
    )

    process_reseau.daemon = True
    process_vision_1.daemon = True
    process_vision_2.daemon = True

    process_reseau.start()
    process_vision_1.start()
    process_vision_2.start()

    root = tk.Tk()
    app = ApplicationTkinter(root, queue_vision_vers_ui)
    root.mainloop()
