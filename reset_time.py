#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Utilitaire de réglage manuel de l'heure système.

Ce script permet de synchroniser l'horloge système de la Raspberry Pi manuellement,
ce qui est utile dans des environnements industriels isolés sans serveur NTP.

Auteur: James DAY
"""

import os


def set_time():
    """
    Demande une date et heure à l'utilisateur et l'applique au système via 'date -s'.
    """
    print("Réglage de l'heure")
    print("Format attendu : AAAA-MM-JJ HH:MM:SS (ex: 2026-05-22 14:30:00)")

    nouvelle_heure = input("Entrez la date et l'heure actuelle : ")

    commande = f'sudo date -s "{nouvelle_heure}"'
    code_retour = os.system(commande)

    if code_retour == 0:
        print("[Système] L'heure de la Raspberry Pi a été mise à jour avec succès !")
    else:
        print(
            "[Erreur] Échec de la mise à jour. Vérifiez le format saisi ou les droits sudo."
        )


if __name__ == "__main__":
    set_time()
