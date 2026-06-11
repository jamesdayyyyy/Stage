#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon May 18 15:23:26 2026

@author: James DAY


MODIFICATION A FAIRE DE LA STRUCTURE:
Mettre le VIS et non le timestamp dans le nom de l'image, et les autres infos dans la base de données
Test a faire

Structure de info_vehicule finale:

info_vehicule = {
    "vis" : str
    "vehciule" : str
    "motorisation" : str
    "timestamp"
    "image" -> path dans la RAM
    "camera_source"
    "variante_active" --> ref de variante
    "resultats_vision" : [{
        "numero_zone"
        "nom_vissage"
        "score"
        "ref_path"
        "match_x" --> ce sont les coordonnées du point en haut a gauche de la zone qui correspond le mieux a la référence
        "match_y"
        }]
    "image_hdd_path"
    }
"""

from dataclasses import dataclass


@dataclass
class Config:
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
        "USERNAME" : "ingpi",
        "PASSWORD" : "raspberry1",
        "CAM" :  [1],
        }
        ,
        {
        "NUMERO" : 4,
        "IP" : "10.226.178.55",
        "USERNAME" : "ingpi",
        "PASSWORD" : "raspberry1",
        "CAM" :  [1],
        },
        {
        "NUMERO" : 5@,
        "IP" : "10.226.178.56",
        "USERNAME" : "ingpi",
        "PASSWORD" : "raspberry1",
        "CAM" :  [1],
        },
        {
        "NUMERO" : 6,
        "IP" : "10.226.178.57",
        "USERNAME" : "ingpi",
        "PASSWORD" : "raspberry1",
        "CAM" :  [1],
        },
        {
        "NUMERO" : 7,
        "IP" : "10.226.178.58",
        "USERNAME" : "ingpi",
        "PASSWORD" : "raspberry1",
        "CAM" :  [1],
        },
        {
        "NUMERO" : 8,
        "IP" : "10.226.178.59",
        "USERNAME" : "ingpi",
        "PASSWORD" : "raspberry1",
        "CAM" :  [1],
        }
    """

    CAM = [
        {
            "NUMERO": 1,
            "VARIANTE_REQUISE": "code_ecran",
            "ACTIVE": True,
            "NOM": "Ecran sous moteur G",
        },
        {"NUMERO": 2, "TYPE": False, "ACTIVE": True, "NOM": "Ecran sous moteur D"},
        {
            "NUMERO": 3,
            "TYPE": False,
            "ACTIVE": True,
            "NOM": "Deflecteur AVD sous plancher (EH)",
        },
    ]
    """
        ,
        {
        "NUMERO" : 4,
        "TYPE" : False,
        "ACTIVE" : True,
        "NOM" : "Déflecteur AVD sous plancher (EM)"
        },
        {
        "NUMERO" : 5,
        "TYPE" : False,
        "ACTIVE" : True,
        "NOM" : "Deflecteur ARD sous reservoir"
        },
        {
        "NUMERO" : 6,
        "TYPE" : False,
        "ACTIVE" : True,
        "NOM" : "Defelcteur AVD sous plancher (IH)"
        },
        {
        "NUMERO" : 7,
        "TYPE" : False,
        "ACTIVE" : True,
        "NOM" : "Deflecteur AVD sous plancher (IB)"
        },
        {
        "NUMERO" : 8,
        "TYPE" : False,
        "ACTIVE" : True,
        "NOM" : "Deflecteur AVG sous plancher (IH)"
        },
        {
        "NUMERO" : 9,
        "TYPE" : False,
        "ACTIVE" : True,
        "NOM" : "Deflecteur AVG sous plancher (IB)"
        },
        {
        "NUMERO" : 10,
        "TYPE" : False,
        "ACTIVE" : True,
        "NOM" : "Deflecteur AVG sous plancher (EH)"
        },
        {
        "NUMERO" : 11,
        "TYPE" : False,
        "ACTIVE" : True,
        "NOM" : "Deflecteur AVG sous plancher (EM)"
        },
        {
        "NUMERO" : 12,
        "TYPE" : False,
        "ACTIVE" : True,
        "NOM" : "Deflecteur ARG sous reservoir"
        }
        ,
        {
        "NUMERO" : 13,
        "TYPE" : False,
        "ACTIVE" : True,
        "NOM" : "Protecteur D / Train AR"
        }
        ,
        {
        "NUMERO" : 14,
        "TYPE" : False,
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

    SCORE_SEUIL = 85.0

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
