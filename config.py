#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module de configuration centralisé pour l'application.

Ce module contient toutes les constantes, les paramètres matériels (Raspberry Pi, Automates),
les chemins d'accès aux fichiers (Base de données, images, CSV) ainsi que les seuils
et paramètres pour l'analyse d'image.

Auteur: James DAY
Date de création: 18 mai 2026
"""

from dataclasses import dataclass


@dataclass
class Config:
    """
    Classe regroupant l'ensemble des paramètres de configuration du système.

    Attributs:
        PASSWORD (str): Mot de passe pour les actions sécurisées dans l'interface.
        RASPBERRY (list): Liste des configurations réseau pour chaque Raspberry Pi esclave.
        CAM (list): Liste des caméras configurées et leurs caractéristiques.
        DATABASE_PATH (str): Chemin vers le fichier de base de données SQLite.
        TEMPORAIRE_PATH (str): Chemin pour le stockage temporaire en RAM (/dev/shm).
        HDD_PATH (str): Chemin pour le stockage permanent sur disque.
        ZONES_CSV_PATH (str): Répertoire contenant les définitions des zones de recherche.
        REF_PATH (str): Répertoire contenant les images de référence.
        MARGE_RECHERCHE (int): Marge de pixels pour la recherche de template.
        SCORE_SEUIL (float): Score minimum pour valider une correspondance d'image.
        AUTOMATE_* : Paramètres de communication avec l'automate (S7).
        MAPPING_VEHICULE (dict): Correspondance entre codes cycles et types de véhicules.
        MAPPING_PIECE (dict): Correspondance entre codes cycles et variantes de pièces.
    """

    PASSWORD = "ing"  # pas secret car accéssible dans ce fichier mais enlève risque de modif accidentelle

    RASPBERRY = [
        {
            "NUMERO": 0,
            "IP": "10.226.178.51",
            "USERNAME": "pimain",
            "PASSWORD": "raspberry1",
            "CAM": [],
        },
        {
            "NUMERO": 1,
            "IP": "10.226.178.53",
            "USERNAME": "rasp1",
            "PASSWORD": "raspberry1",
            "CAM": [1, 2],
        },
        {
            "NUMERO": 2,
            "IP": "10.226.178.52",
            "USERNAME": "ingpi",
            "PASSWORD": "raspberry1",
            "CAM": [3],
        },
    ]
    """
        ,
        {
        "NUMERO" : 3,
        "IP" : "10.226.178.54",
        "USERNAME" : "rasp3",
        "PASSWORD" : "raspberry1",
        "CAM" :  [4, 5],
        }
        ,
        {
        "NUMERO" : 4,
        "IP" : "10.226.178.55",
        "USERNAME" : "ingpi",
        "PASSWORD" : "raspberry1",
        "CAM" :  [6, 7],
        },
        {
        "NUMERO" : 5@,
        "IP" : "10.226.178.56",
        "USERNAME" : "rasp5",
        "PASSWORD" : "raspberry1",
        "CAM" :  [8],
        },
        {
        "NUMERO" : 6,
        "IP" : "10.226.178.57",
        "USERNAME" : "rasp6",
        "PASSWORD" : "raspberry1",
        "CAM" :  [9, 10],
        },
        {
        "NUMERO" : 7,
        "IP" : "10.226.178.58",
        "USERNAME" : "rasp7",
        "PASSWORD" : "raspberry1",
        "CAM" :  [11, 12],
        },
        {
        "NUMERO" : 8,
        "IP" : "10.226.178.59",
        "USERNAME" : "rasp8",
        "PASSWORD" : "raspberry1",
        "CAM" :  [13, 14],
        }
    """

    CAM = [
        {
            "NUMERO": 1,
            "VARIANTE_REQUISE": "code_ecran",
            "ACTIVE": True,
            "NOM": "Ecran sous moteur G",
        },
        {
            "NUMERO": 2,
            "VARIANTE_REQUISE": "code_ecran",
            "ACTIVE": True,
            "NOM": "Ecran sous moteur D",
        },
        {
            "NUMERO": 3,
            "VARIANTE_REQUISE": "",
            "ACTIVE": True,
            "NOM": "Deflecteur AVD sous plancher (EH)",
        },
    ]
    """
        ,
        {
        "NUMERO" : 4,
        "VARIANTE_REQUISE": "",
        "ACTIVE" : True,
        "NOM" : "Déflecteur AVD sous plancher (EM)"
        },
        {
        "NUMERO" : 5,
        "VARIANTE_REQUISE": "",
        "ACTIVE" : True,
        "NOM" : "Deflecteur ARD sous reservoir"
        },
        {
        "NUMERO" : 6,
        "VARIANTE_REQUISE": "",
        "ACTIVE" : True,
        "NOM" : "Defelcteur AVD sous plancher (IH)"
        },
        {
        "NUMERO" : 7,
        "VARIANTE_REQUISE": "",
        "ACTIVE" : True,
        "NOM" : "Deflecteur AVD sous plancher (IB)"
        },
        {
        "NUMERO" : 8,
        "VARIANTE_REQUISE": "",
        "ACTIVE" : True,
        "NOM" : "Deflecteur AVG sous plancher (IH)"
        },
        {
        "NUMERO" : 9,
        "VARIANTE_REQUISE": "",
        "ACTIVE" : True,
        "NOM" : "Deflecteur AVG sous plancher (IB)"
        },
        {
        "NUMERO" : 10,
        "VARIANTE_REQUISE": "",
        "ACTIVE" : True,
        "NOM" : "Deflecteur AVG sous plancher (EH)"
        },
        {
        "NUMERO" : 11,
        "VARIANTE_REQUISE": "",
        "ACTIVE" : True,
        "NOM" : "Deflecteur AVG sous plancher (EM)"
        },
        {
        "NUMERO" : 12,
        "VARIANTE_REQUISE": "",
        "ACTIVE" : True,
        "NOM" : "Deflecteur ARG sous reservoir"
        }
        ,
        {
        "NUMERO" : 13,
        "VARIANTE_REQUISE": "",
        "ACTIVE" : True,
        "NOM" : "Protecteur D / Train AR"
        }
        ,
        {
        "NUMERO" : 14,
        "VARIANTE_REQUISE": "",
        "ACTIVE" : True,
        "NOM" : "Protecteur G / Train AR"
        }
        """

    DATABASE_PATH = "./historique_production.db"
    TEMPORAIRE_PATH = "/dev/shm"
    HDD_PATH = "."
    ZONES_CSV_PATH = "./zones"
    REF_PATH = "./ref"

    MARGE_RECHERCHE = 100

    SCORE_SEUIL = 80.0

    CACHE_LIMIT = 3

    AUTOMATE_IP = "10.226.178.1"
    AUTOMATE_DB = 102
    AUTOMATE_TAILLE_LECTURE = 36
    AUTOMATE_DB_ENVOIE = 105
    AUTOMATE_NB_MAX_DEFAUTS = 15
    AUTOMATE_OCTETS_DEFAUTS = 34  # String de 32 chars max + 2 octets d'en tête
    AUTOMATE_RACK = 0
    AUTOMATE_SLOT = 1

    PASSWORD = "ing"  # pas secret car accéssible dans ce fichier mais enlève risque de modif accidentelle
    DELAI_INACTIVITE = 300000  # 5 min

    # TODO:Ceci permet d'ajouter des code pour pièces
    # ! Afin de mettre a jour il faut ajouter les codes cycles reçue dans MAPPING_PIECE
    AUTOMATE_DB_LECTURE = {
        "vis": 2,
        "type_vh": 12,
        "silhouette": 18,
        "code_moteur": 24,
        "code_ecran": 30,
    }

    MAPPING_VEHICULE = {
        "006": {"VEHICULE": "P51", "MOTORISATION": "ICE"},
        "007": {"VEHICULE": "P51", "MOTORISATION": "PHEV"},
        "008": {"VEHICULE": "P52", "MOTORISATION": "ICE"},
        "009": {"VEHICULE": "P52", "MOTORISATION": "PHEV"},
        "010": {"VEHICULE": "P54", "MOTORISATION": "ICE"},
        "011": {"VEHICULE": "P54", "MOTORISATION": "PHEV"},
        "012": {"VEHICULE": "P51", "MOTORISATION": "MHEV"},
        "013": {"VEHICULE": "P52", "MOTORISATION": "MHEV"},
        "014": {"VEHICULE": "P54", "MOTORISATION": "MHEV"},
        "015": {"VEHICULE": "P51", "MOTORISATION": "PHEV"},
        "016": {"VEHICULE": "P52", "MOTORISATION": "PHEV"},
        "017": {"VEHICULE": "P54", "MOTORISATION": "PHEV"},
        "018": {"VEHICULE": "P51", "MOTORISATION": "BEV"},
        "019": {"VEHICULE": "P52", "MOTORISATION": "BEV"},
        "020": {"VEHICULE": "P54", "MOTORISATION": "BEV"},
    }

    # format nom_du_code :{
    #       "code_cycle" : "information_a_extraire"}

    MAPPING_PIECE = {
        "code_ecran": {
            "001": "00",  # Sans
            "002": "01",  # Ecran tole
            "003": "10",  # Deflecteur
            "004": "10",  # Deflecteur
            "005": "01",  # Ecran tole
            "006": "10",  # Deflecteur
        }
    }

    NOM_VIS = [
        "Deflecteur ARG sous reservoir",
        "Deflecteur AIR AVG sous plancher",
        "Ecran sous moteur / berceau",
        "Deflecteur sous moteur",
        "Deflecteur AIR AVD sous plancher",
        "Deflecteur AR sous batterie",
        "Deflecteur AV sous batterie",
        "Protecteur G / Train AR",
        "Protecteur D / Train AR",
        "Deflecteur AR",
        "Deflecteur sous chargeur",
    ]
