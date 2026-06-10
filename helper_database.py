#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed May 20 08:48:21 2026

@author: James DAY
"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed May 13 09:53:19 2026

@author: James DAY
"""

import sqlite3
from config import Config

class Database:
    def __init__(self):
        self.db_path = Config.DATABASE_PATH
        self._initialiser()
        
    def _initialiser(self):
        """
        Initialise la base de données au démarrage si elle n'existe pas déjà
        Params :
        - None
        Retourne :
        - None
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON;")
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS inspections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    vis TEXT,
                    timestamp INTEGER,
                    vehicule TEXT,
                    motorisation TEXT,
                    camera INTEGER,
                    type TEXT
                )
                ''')
                
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS zone_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    inspection_id INTEGER NOT NULL,
                    zone_id TEXT NOT NULL,
                    score REAL NOT NULL,
                    match_x INTEGER,
                    match_y INTEGER,
                    FOREIGN KEY (inspection_id) REFERENCES inspections (id) ON DELETE CASCADE
                    )
                ''')
                
            
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_zone_results_zone_id ON zone_results (zone_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON inspections (timestamp);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_vis ON inspections (vis);")
            conn.commit()
            
    def sauvegarder_info(self, info_vehicule):
        """
        Ajoute à la base de donnée les résultats d'une ananlyse
        Params :
        - info_vehicule (dict)
        Retourne : 
        - bool en fonction de si réussi ou non
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute("PRAGMA foreign_keys = ON;") 
            cursor = conn.cursor()
            cursor.execute("BEGIN TRANSACTION")
            
            cursor.execute('''
                           INSERT INTO inspections 
                           (vis, timestamp, vehicule, motorisation, camera, type) 
                           VALUES (?, ?, ?, ?, ?, ?)
                           ''', (
                           info_vehicule.get('vis'),
                           info_vehicule.get('timestamp'),
                           info_vehicule.get('vehicule'),
                           info_vehicule.get('motorisation'),
                           info_vehicule.get('camera_source'),
                           info_vehicule.get('type_ecran'),
                           ))
        
            inspection_id = cursor.lastrowid
        
            liste_zones = info_vehicule.get("resultats_vision", [])
            for zone_data in liste_zones:
                cursor.execute('''
                               INSERT INTO zone_results (inspection_id, zone_id, score, match_x, match_y) 
                               VALUES (?, ?, ?, ?, ?)
                               ''', (
                               inspection_id, 
                               str(zone_data.get("numero_zone")), 
                               float(zone_data.get("score", 0.0)),
                               int(zone_data.get("match_x", 0)),
                               int(zone_data.get("match_y", 0))
                               ))
            print(f"[BDD] Historique enregistré pour véhicule {info_vehicule.get('vehicule')} (Caméra {info_vehicule.get('camera_source')})")
            conn.commit()
            return True
        
        except sqlite3.Error as e:
            print(f"[DB Save Error] Rollback effectué : {e}")
            if 'conn' in locals() and conn:
                conn.rollback()
            return False
        finally:
            if 'conn' in locals() and conn:
                conn.close()

    def add_reference_to_db(self, vis, vehicule, camera, zone_id, new_match_x, new_match_y):
        """
        Enregistre une prise de référence en utilisant les tables existantes.
        Params:
        - vis 
        - vehicule 
        - camera : id de la caméra (str)
        - zone_id :  id de la zone (str)
        Retourne :
        - None
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute("PRAGMA foreign_keys = ON;")
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE zone_results 
                SET score = 100.0, match_x = ?, match_y = ?
                WHERE zone_id = ? 
                AND inspection_id = (
                    SELECT id FROM inspections 
                    WHERE vis = ? AND camera = ? 
                    ORDER BY id DESC LIMIT 1
                )
            ''', (int(new_match_x), int(new_match_y), str(zone_id), vis, int(camera)))
            
            cursor.execute("COMMIT")
            print(f"[DB] Référence de la Zone {zone_id} historisée avec succès.")

        except sqlite3.Error as e:
            print(f"[DB Ref Error] Impossible d'historiser la référence : {e}")
            if 'conn' in locals() and conn:
                conn.rollback()
        finally:
            if 'conn' in locals() and conn:
                conn.close()

            
    def update_type_materiau(self, vis, camera, type_mat):
        """
        Met à jour le type du véhicule dans la base de données
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE inspections 
                SET type = ? 
                WHERE vis = ? AND camera = ?
            ''', (str(type_mat), vis, int(camera)))
            
            conn.commit()
            print(f"[DB] Type '{type_mat}' mis à jour avec succès pour la caméra {camera}.")
            return True
            
        except sqlite3.Error as e:
            print(f"[DB Update Error] Impossible de mettre à jour le type : {e}")
            if 'conn' in locals() and conn:
                conn.rollback()
            return False
        finally:
            if 'conn' in locals() and conn:
                conn.close()

    def rechercher_vehicule(self, vis_query = "", vehicule_query = "", motorisation_query = "", statut_query = "Tous"):
        """
        Effectue une recherche sur la base de données afin d'afficher les 50 derniers véhicules correspondant
        Params:
        - vis_query : VIS recherché
        - vehicule_query : vehicule_recherché
        - motorisation_query : motorisation recherché
        - statut_query : statut du véhicule (OK/NOK ou tous) recherché
        Retourne : 
        - liste des résultats de recherche avec vis, vehicule, motorisation, timestamp, et le score min sur le véhicule
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

            params = [f"%{vis_query}%", f"%{vehicule_query}%", f"%{motorisation_query}%"]
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
            if 'conn' in locals() and conn:
                conn.close()