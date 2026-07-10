#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module d'interface avec l'automate industriel (PLC) via le protocole S7.

Ce module permet de lire les données de production (VIS, type de véhicule, numéro de séquence)
et d'écrire les résultats des tests de vision pour que l'automate puisse
gérer le flux de la ligne de production.

Auteur: James DAY
Date de création: 18 mai 2026
"""

import snap7
from snap7.util import get_string, get_bool, set_bool, set_string
from config import Config


class Automate:
    """
    Classe de gestion de la communication avec un automate Siemens (S7).

    Fournit des méthodes pour se connecter, lire des blocs de données (DB)
    et écrire des résultats d'inspection.
    """

    def __init__(self, ip, db_numero, rack=0, slot=0):
        """
        Initialise les paramètres de connexion à l'automate.

        Args:
            ip (str): Adresse IP de l'automate.
            db_numero (int): Numéro du bloc de données (DB) à lire.
            rack (int): Rack de l'automate (souvent 0).
            slot (int): Slot de l'automate (souvent 1).
        """
        self.ip = ip
        self.db_numero = db_numero
        self.rack = rack
        self.slot = slot
        self.client = snap7.client.Client()
        self.connect()

    def connect(self):
        """Établit la connexion avec l'automate."""
        try:
            self.client.connect(self.ip, self.rack, self.slot)  #
            print("[Automate] Connecté à l'automate")
        except Exception as e:
            print(f"[Erreur - Automate {self.ip}] Échec de la connexion : {e}")
            self.client = None

    def lire_data(self):
        """
        Lit les informations du véhicule courant depuis la DB de l'automate.

        Récupère le bit de présence, le VIS, le type de véhicule, le numéro de séquence et les variantes
        puis les traduit en informations compréhensibles par le système.

        Returns:
            dict: Données véhicule lues ou None en cas d'erreur.
        """
        if self.client is None or not self.client.get_connected():
            print("[Automate] Automate hors ligne. Reconnexion...")
            self.connect()
        if self.client is None:
            print("[Automate] Impossible de se connecter à l'automate.")
            return None
        try:
            data = self.client.db_read(
                self.db_numero, 0, Config.AUTOMATE_TAILLE_LECTURE
            )
            vh_dans_pas = get_bool(data, 0, 0)

            variantes_recues = {}

            for nom_variable, offset in Config.AUTOMATE_DB_LECTURE.items():
                valeur = get_string(data, offset).strip()
                if nom_variable in Config.MAPPING_PIECE:
                    valeur = Config.MAPPING_PIECE[nom_variable].get(valeur, valeur)
                variantes_recues[nom_variable] = valeur

            code_moteur = variantes_recues.get("code_moteur", "")
            info_traduite = Config.MAPPING_VEHICULE.get(
                code_moteur, {"VEHICULE": "Inconnu", "MOTORISATION": code_moteur}
            )

            return {
                "vh_dans_pas": vh_dans_pas,
                "vis": variantes_recues.get("vis", ""),
                "sequence": variantes_recues.get("sequence","")
                "vehicule": info_traduite.get("VEHICULE", "Inconnu"),
                "motorisation": info_traduite.get("MOTORISATION", "Inconnu"),
                "variantes": variantes_recues,
            }

        except Exception as e:
            print(f"[Erreur - Automate] {e}")
            self.client.disconnect()
            self.client = None
            return None

    def envoyer_data(self, vehicule_ok, liste_defauts, erreur_systeme=False):
        """
        Envoie les résultats de l'inspection à l'automate.

        Écrit dans une DB spécifique le statut (OK/NOK/Erreur) et la liste des
        défauts détectés sous forme de chaînes de caractères.

        Args:
            vehicule_ok (bool): True si toutes les zones sont conformes.
            liste_defauts (list): Liste des noms des zones en défaut.
            erreur_systeme (bool): True en cas de panne logicielle ou matérielle.

        Returns:
            bool: True si l'envoi a réussi.
        """
        if self.client is None or not self.client.get_connected():
            print("[Automate] Automate d'envoie hors ligne. Reconnexion...")
            self.connect()
        if self.client is None:
            print("[Automate] Impossible de se connecter à l'automate pour l'envoi.")
            return False
        try:
            OFFSET_BOOLS = 0
            OFFSET_ARRAY = 2

            NB_MAX_DEFAUTS = Config.AUTOMATE_NB_MAX_DEFAUTS
            TAILLE_STRING = Config.AUTOMATE_OCTETS_DEFAUTS
            taille_totale_db = OFFSET_ARRAY + (NB_MAX_DEFAUTS * TAILLE_STRING)

            data = bytearray(taille_totale_db)
            if erreur_systeme:
                set_bool(data, OFFSET_BOOLS, 0, True)
                set_bool(data, OFFSET_BOOLS, 1, False)
                set_bool(data, OFFSET_BOOLS, 2, False)
            else:
                set_bool(data, OFFSET_BOOLS, 0, False)
                set_bool(data, OFFSET_BOOLS, 1, vehicule_ok)
                set_bool(data, OFFSET_BOOLS, 2, not vehicule_ok)
            for i in range(NB_MAX_DEFAUTS):
                offset_actuel = OFFSET_ARRAY + (i * TAILLE_STRING)
                if i < len(liste_defauts) and not erreur_systeme:
                    set_string(data, offset_actuel, liste_defauts[i][:32], 32)
                else:
                    set_string(data, offset_actuel, "", 32)
            self.client.db_write(Config.AUTOMATE_DB_ENVOIE, 0, data)
            print("[Automate] Données envoyées à l'automate")
            return True

        except Exception as e:
            print(f"[Erreur - Automate] Échec de l'envoi : {e}")
            self.client.disconnect()
            self.client = None
            return False

    def reset_data(self):
        if self.client is None or not self.client.get_connected():
            print("[Automate] Automate hors ligne. Reconnexion pour le reset...")
            self.connect()
        if self.client is None:
            print("[Automate] Impossible de se connecter pour le reset.")
            return False

        try:
            OFFSET_BOOLS = 0
            OFFSET_ARRAY = 2

            NB_MAX_DEFAUTS = Config.AUTOMATE_NB_MAX_DEFAUTS
            TAILLE_STRING = Config.AUTOMATE_OCTETS_DEFAUTS
            taille_totale_db = OFFSET_ARRAY + (NB_MAX_DEFAUTS * TAILLE_STRING)

            data = bytearray(taille_totale_db)

            set_bool(data, OFFSET_BOOLS, 0, False)  # erreur_systeme
            set_bool(data, OFFSET_BOOLS, 1, False)  # vehicule_ok
            set_bool(data, OFFSET_BOOLS, 2, False)  # vehicule_nok

            # On vide proprement les chaînes de caractères (important pour l'en-tête Siemens)
            for i in range(NB_MAX_DEFAUTS):
                offset_actuel = OFFSET_ARRAY + (i * TAILLE_STRING)
                set_string(data, offset_actuel, "", 32)

            self.client.db_write(Config.AUTOMATE_DB_ENVOIE, 0, data)
            print("[Automate] RAZ effectué avec succès (Véhicule sorti du pas).")
            return True

        except Exception as e:
            print(f"[Erreur - Automate] Échec du reset : {e}")
            self.client.disconnect()
            self.client = None
            return False
