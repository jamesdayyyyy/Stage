#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module de gestion de la base de données SQLite.

Ce module fournit une interface pour stocker et interroger l'historique des inspections,
incluant les données des véhicules, les timestamps et les scores détaillés par zone.

Auteur: James DAY
Date de création: 13 mai 2026
"""

import sqlite3
from config import Config


class Database:
    """
    Gestionnaire de la base de données SQLite pour l'historique de production.

    Cette classe gère la création des tables, l'insertion des résultats d'inspection
    et les recherches multicritères.
    """

    def __init__(self):
        """Initialise le chemin de la base de données et crée les tables si nécessaire."""
        self.db_path = Config.DATABASE_PATH
        self._initialiser()

    def _initialiser(self):
        """
        Initialise la structure de la base de données (tables et index).

        Crée les tables 'inspections' (données générales) et 'zone_results' (détails par zone)
        avec les contraintes d'intégrité et les index de performance.
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON;")
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS inspections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    vis TEXT,
                    timestamp INTEGER,
                    vehicule TEXT,
                    motorisation TEXT,
                    camera INTEGER,
                    type TEXT
                )
                """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS zone_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    inspection_id INTEGER NOT NULL,
                    zone_id TEXT NOT NULL,
                    score REAL NOT NULL,
                    match_x INTEGER,
                    match_y INTEGER,
                    FOREIGN KEY (inspection_id) REFERENCES inspections (id) ON DELETE CASCADE
                    )
                """)

            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_zone_results_zone_id ON zone_results (zone_id);"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_timestamp ON inspections (timestamp);"
            )
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_vis ON inspections (vis);")
            conn.commit()

    def sauvegarder_info(self, info_vehicule):
        """
        Enregistre les résultats complets d'une analyse dans la base de données.

        Args:
            info_vehicule (dict): Dictionnaire contenant les données du véhicule et 
                                 les scores de vision.

        Returns:
            bool: True si la sauvegarde a réussi, False sinon (avec rollback).
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute("PRAGMA foreign_keys = ON;")
            cursor = conn.cursor()
            cursor.execute("BEGIN TRANSACTION")

            cursor.execute(
                """
                           INSERT INTO inspections 
                           (vis, timestamp, vehicule, motorisation, camera, type) 
                           VALUES (?, ?, ?, ?, ?, ?)
                           """,
                (
                    info_vehicule.get("vis"),
                    info_vehicule.get("timestamp"),
                    info_vehicule.get("vehicule"),
                    info_vehicule.get("motorisation"),
                    info_vehicule.get("camera_source"),
                    info_vehicule.get("variante_active"),
                ),
            )

            inspection_id = cursor.lastrowid

            liste_zones = info_vehicule.get("resultats_vision", [])
            for zone_data in liste_zones:
                cursor.execute(
                    """
                               INSERT INTO zone_results (inspection_id, zone_id, score, match_x, match_y) 
                               VALUES (?, ?, ?, ?, ?)
                               """,
                    (
                        inspection_id,
                        str(zone_data.get("numero_zone")),
                        float(zone_data.get("score", 0.0)),
                        int(zone_data.get("match_x", 0)),
                        int(zone_data.get("match_y", 0)),
                    ),
                )
            print(
                f"[BDD] Historique enregistré pour véhicule {info_vehicule.get('vehicule')} (Caméra {info_vehicule.get('camera_source')})"
            )
            conn.commit()
            return True

        except sqlite3.Error as e:
            print(f"[DB Save Error] Rollback effectué : {e}")
            if "conn" in locals() and conn:
                conn.rollback()
            return False
        finally:
            if "conn" in locals() and conn:
                conn.close()

    def add_reference_to_db(
        self, vis, vehicule, camera, zone_id, new_match_x, new_match_y
    ):
        """
        Met à jour un résultat pour marquer une prise de référence (score 100%).

        Args:
            vis (str): Numéro VIS du véhicule.
            vehicule (str): Modèle du véhicule.
            camera (str/int): ID de la caméra.
            zone_id (str): ID de la zone.
            new_match_x (int): Nouvelle coordonnée X de correspondance.
            new_match_y (int): Nouvelle coordonnée Y de correspondance.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute("PRAGMA foreign_keys = ON;")
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE zone_results 
                SET score = 100.0, match_x = ?, match_y = ?
                WHERE zone_id = ? 
                AND inspection_id = (
                    SELECT id FROM inspections 
                    WHERE vis = ? AND camera = ? 
                    ORDER BY id DESC LIMIT 1
                )
            """,
                (int(new_match_x), int(new_match_y), str(zone_id), vis, int(camera)),
            )

            cursor.execute("COMMIT")
            print(f"[DB] Référence de la Zone {zone_id} historisée avec succès.")

        except sqlite3.Error as e:
            print(f"[DB Ref Error] Impossible d'historiser la référence : {e}")
            if "conn" in locals() and conn:
                conn.rollback()
        finally:
            if "conn" in locals() and conn:
                conn.close()

    def update_type_materiau(self, vis, camera, type_mat):
        """
        Met à jour la variante de matériau/type pour une inspection donnée.

        Args:
            vis (str): Numéro VIS du véhicule.
            camera (str/int): ID de la caméra.
            type_mat (str): Nom du type ou matériau.

        Returns:
            bool: True si succès.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                UPDATE inspections 
                SET type = ? 
                WHERE vis = ? AND camera = ?
            """,
                (str(type_mat), vis, int(camera)),
            )

            conn.commit()
            print(
                f"[DB] Type '{type_mat}' mis à jour avec succès pour la caméra {camera}."
            )
            return True

        except sqlite3.Error as e:
            print(f"[DB Update Error] Impossible de mettre à jour le type : {e}")
            if "conn" in locals() and conn:
                conn.rollback()
            return False
        finally:
            if "conn" in locals() and conn:
                conn.close()

    def rechercher_vehicule(
        self,
        vis_query="",
        vehicule_query="",
        motorisation_query="",
        statut_query="Tous",
    ):
        """
        Recherche les véhicules dans l'historique selon plusieurs critères.

        Args:
            vis_query (str): Filtre sur le VIS (partiel).
            vehicule_query (str): Filtre sur le modèle.
            motorisation_query (str): Filtre sur la motorisation.
            statut_query (str): 'Tous', 'OK' (score min >= seuil) ou 'NOK'.

        Returns:
            list: Liste des 50 derniers résultats trouvés (tuples).
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            query = """
                SELECT i.vis, i.vehicule, i.motorisation, i.timestamp , MIN(z.score) as min_score
                FROM inspections i
                LEFT JOIN zone_results z ON i.id = z.inspection_id
                WHERE i.vis LIKE ? AND i.vehicule LIKE ? AND i.motorisation LIKE ?
                GROUP BY I.vis 
            """

            params = [
                f"%{vis_query}%",
                f"%{vehicule_query}%",
                f"%{motorisation_query}%",
            ]
            if statut_query == "OK":
                query += " HAVING min_score >= ?"
                params.append(Config.SCORE_SEUIL)
            elif statut_query == "NOK":
                query += " HAVING min_score < ?"
                params.append(Config.SCORE_SEUIL)
            query += "ORDER BY timestamp DESC LIMIT 50"

            cursor.execute(query, params)
            return cursor.fetchall()

        except sqlite3.Error as e:
            print(f"[DB] Erreur lors de la recherche : {e}")
            return []
        finally:
            if "conn" in locals() and conn:
                conn.close()
