#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuration locale pour une Raspberry Pi esclave.

Ce module définit les IDs des caméras physiquement connectées à cette Pi
et les chemins de stockage temporaires pour les captures.

Auteur: James DAY
"""

from dataclasses import dataclass

@dataclass
class Config:
    """
    Paramètres locaux de la Pi.

    Attributs:
        CAM (list): Liste des numéros de caméras connectées.
        PATH_PHOTO (str): Répertoire de stockage en RAM (/dev/shm).
    """
    CAM = [1]
    PATH_PHOTO = "/dev/shm"