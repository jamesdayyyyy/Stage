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
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS historique (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    vis TEXT,
                    timestamp INTEGER,
                    vehicule TEXT,
                    numero_camera INTEGER,
                    numero_zone INTEGER,
                    pourcentage_ressemblance REAL
                )
                ''')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON historique(timestamp)')
            conn.commit()
            
    def ajouter_resultat(self, vis, timestamp, vehicule, numero_camera, numero_zone, ressemblance):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO historique
                (vis, timestamp, vehicule, numero_camera, numero_zone, pourcentage_ressemblance)
                VALUES (?,?,?,?,?,?)
                ''', (vis, timestamp, vehicule,numero_camera,numero_zone,ressemblance))
            conn.commit()
    
    def search_timestamp(self, timestamp):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT numero_camera, numero_zone, pourcentage_ressemblance
                FROM historique
                WHERE timestamp = ?
                ''', (timestamp,))
            return cursor.fetchall()
        
    def add_reference_to_db(self, vis, timestamp, vehicule, numero_camera, numero_zone):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE historique
                SET pourcentage_ressemblance = 100
                WHERE timestamp = ? AND numero_camera = ? AND numero_zone = ?
                ''', (timestamp, numero_camera, numero_zone))
                
            if cursor.rowcount == 0:
                cursor.execute('''
                    INSERT INTO historique
                    (vis, timestamp, vehicule, numero_camera, numero_zone, pourcentage_ressemblance)
                    VALUES (?,?,?,?,?,?)
                    ''', (vis, timestamp,vehicule,numero_camera,numero_zone,100))

            conn.commit()