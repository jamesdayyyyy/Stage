#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon May 18 08:15:01 2026

@author: James DAY
"""

import multiprocessing
import tkinter as tk 

from interface import ApplicationTkinter
from reseau import check_capture
from vision import analyse_image


if __name__ == '__main__':
    print("[Main] Initialisation")
    
    queue_reseau_vers_vision = multiprocessing.Queue()
    queue_vision_vers_ui = multiprocessing.Queue()
    
    process_reseau = multiprocessing.Process(
        target=check_capture,
        args=(queue_reseau_vers_vision,)
    )
    process_vision_1 = multiprocessing.Process(
        target=analyse_image,
        args=(queue_reseau_vers_vision,queue_vision_vers_ui, "Core 3")
    )
    process_vision_2 = multiprocessing.Process(
        target=analyse_image,
        args=(queue_reseau_vers_vision,queue_vision_vers_ui, "Core 4")
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