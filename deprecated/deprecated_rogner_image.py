#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon May 11 09:52:39 2026

@author: James DAY
"""

import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox
import cv2
from PIL import Image, ImageTk
import csv
import os
from deprecated_sqlite_connect import Database
from config import Config

class Image_cropper:
    def __init__(self,root):
        self.root = root 
        self.root.title("Crop image")
        

        self.canvas= tk.Canvas(self.root, cursor="cross")
        self.canvas.pack(fill = "both", expand = True)
                
        self.image = None
        self.image_path = None
        
        self.rect = None 
        self.start_x = None
        self.start_y = None 
        self.end_x = None
        self.end_y = None 
        
        self.csv_file = None
        self.vehicule = None
        self.motorisation = None
        self.type = None
        self.camera = None
        self.timestamp = None
        self.controle = None
        
        self.load_button = tk.Button(self.root, text = "importer", command = self.load_image)
        self.load_button.pack()
        
        self.canvas.bind("<ButtonPress-1>", self.on_button_press)
        self.canvas.bind("<B1-Motion>", self.on_mouse_move)
        self.canvas.bind("<ButtonRelease-1>", self.on_button_release)
        
        self.db = Database()
                
    def get_data(self):
        detail = os.path.basename(self.image_path)
        detail = detail.split("_")
        
        csv_directory = "zone"
        if not os.path.exists(csv_directory):
            os.makedirs(csv_directory)
            
        if len(detail) == 6:
            self.camera = detail[0]
            self.vehicule = detail[1]
            self.motorisation = detail[2]
            self.type = detail[3]
            self.timestamp = int(detail[4])
            self.controle = detail[5][:-4]
            
            filename = f"{self.vehicule}_{self.motorisation}.csv"
            self.csv_file = os.path.join(csv_directory, filename)
            
        elif len(detail) == 5:
            self.camera = detail[0]
            self.vehicule = detail[1]
            self.motorisation = detail[2]
            self.timestamp = int(detail[3])
            self.controle = detail[4][:-4]
            filename = f"{self.vehicule}_{self.motorisation}.csv"
            self.csv_file = os.path.join(csv_directory, filename)
        else:
            print("Erreur : nomination fichier incorrect")
            
    def load_image(self):
        self.image_path = filedialog.askopenfilename()
        if self.image_path:
            self.image = cv2.imread(self.image_path)
            h, w, _ = self.image.shape
            self.canvas.config(width=w, height=h)
            self.display_image()
            self.get_data()
            if self.csv_file and os.path.exists(self.csv_file):
                print("drawing data")
                self.draw_data()
            
    def display_image(self):
        if self.image is not None:
            image_rgb = cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB)
            image_pil = Image.fromarray(image_rgb)
            self.image_tk = ImageTk.PhotoImage(image = image_pil)
            self.canvas.create_image(0,0, anchor ="nw", image = self.image_tk)

            
    def on_button_press(self, event):
        self.start_x = self.canvas.canvasx(event.x)
        self.start_y = self.canvas.canvasy(event.y)
        if self.rect:
            self.canvas.delete(self.rect)
        self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y,outline="green")
    
    def on_mouse_move(self,event):
        self.end_x = self.canvas.canvasx(event.x)
        self.end_y = self.canvas.canvasy(event.y)
        self.canvas.coords(self.rect, self.start_x,self.start_y,self.end_x,self.end_y)
        
    def on_button_release(self,event):
        if self.image_path and self.start_x and self.start_y and self.end_x and self.end_y:
            output = messagebox.askquestion("Ajouter une zone", "Ajouter une zone est une action irréversible. Voulez-vous continuer ?") 
            if output == "yes": 
                self.crop_image()
                
            else: 
                self.canvas.delete(self.rect)
                self.rect = None
                self.end_x = None
                self.end_y = None 
                print("Capture annulée")
        else:
            try:
                self.ajouter_reference()
            except FileExistsError:
                print("Erreur : fichier csv non valide")
            
        
    def crop_image(self):
        if self.image_path and self.start_x and self.start_y and self.end_x and self.end_y:
            self.x_start = int(min(self.start_x, self.end_x))
            self.x_end = int(max(self.start_x, self.end_x))
            self.y_start = int(min(self.start_y, self.end_y))
            self.y_end = int(max(self.start_y, self.end_y))
            
            if os.path.exists(self.csv_file):
                with open (self.csv_file, newline="") as csv_data:
                    reader = csv.DictReader(csv_data)
                    for row in reader:
                        if row["numero_camera"] == self.camera and row["type"] == self.type:
                            existing_x0 = int(row['x0'])
                            existing_x1 = int(row['x1'])
                            existing_y0 = int(row['y0'])
                            existing_y1 = int(row['y1'])
                            
                            not_chevauche = (self.x_start >= existing_x1 or self.x_end <= existing_x0 or 
                                             self.y_start >= existing_y1 or self.y_end <= existing_y0)
                            if not not_chevauche:
                                messagebox.showwarning("Collision", f"La zone chevauche avec la zone {row['numero_zone']}")
                                self.canvas.delete(self.rect)
                                self.rect = None
                                return

            cropped_img = self.image[self.y_start:self.y_end, self.x_start:self.x_end]
            target_dir = self.get_target_directory()
            os.makedirs(target_dir, exist_ok=True)
            
            zone_id = self.get_next_zone_id()
            
            path_string = os.path.join(target_dir, f"zone_{zone_id}_1.png")
            cv2.imwrite(path_string, cropped_img)
            
            print("Image cropped and saved")
            self.canvas.delete(self.rect)
            self.rect = None
            self.end_x = None
            self.end_y = None 
            
            self.add_to_csv(zone_id)
            self.draw_rect(zone_id)
            self.db.add_reference_to_db('0', self.timestamp, self.vehicule, self.camera, zone_id)

            
    def add_to_csv(self,zone):
        fieldnames = ['numero_camera', 'numero_zone', 'x0', 'y0', 'x1', 'y1', 'type']
        file_exists_and_not_empty = os.path.exists(self.csv_file) and os.path.getsize(self.csv_file) > 0
        
        with open(self.csv_file,"a", newline = "") as csv_data:
            writer = csv.DictWriter(csv_data, fieldnames=fieldnames)
            
            if not file_exists_and_not_empty:  
                writer.writeheader()
                
            writer.writerow({"numero_camera" : self.camera,
                             "numero_zone" : zone,
                             'x0': self.x_start,
                             'y0': self.y_start,
                             'x1': self.x_end,
                             'y1': self.y_end,
                             'type' : self.type})
            #Ajouter systeme pour gerer le type de maniere dynamique
            print("Data added to csv")

    def draw_rect(self,zone_id):
        unique_tag = f"rect_{zone_id}"
        text_x = (self.x_start + self.x_end) / 2
        text_y = self.y_end + 10
        self.added_rect = self.canvas.create_rectangle(self.x_start, self.y_start, self.x_end, self.y_end,outline="#00ff00", width= 2, tags= unique_tag)
        self.canvas.create_text(
            text_x, text_y, 
            text=f"Zone {zone_id} : 100%", fill="#00ff00", 
            tags=unique_tag
            )
        
    def ajouter_reference(self):
        with open(self.csv_file, newline = "") as csv_data:                   
            reader = csv.DictReader(csv_data)
            for row in reader:
                if int(row['x0']) < int(self.start_x) < int(row['x1']) and int(row['y0']) < int(self.start_y) < int(row['y1'])  and row["type"] == self.type:
                    ref = self.image[int(row['y0']):int(row['y1']), int(row['x0']):int(row['x1'])]
                    output = messagebox.askquestion("Ajouter une image référence", "Ajouter une image référence est une action irréversible. Voulez-vous continuer ?") 
                    if output == "yes":
                        target_dir = self.get_target_directory()
                        os.makedirs(target_dir, exist_ok=True)
                                                
                        path_string = os.path.join(target_dir, f"zone_{row['numero_zone']}_%s.png")                        
                        path_pattern = self.next_path(path_string)
                        
                        if not cv2.imwrite(path_pattern, ref):
                            print("ERRREUR")
                        self.db.add_reference_to_db('0', self.timestamp, self.vehicule, self.camera, row['numero_zone'])
                        
                        unique_tag = f"rect_{row['numero_zone']}"
                        self.canvas.delete(unique_tag)
                        text_x = (int(row['x0']) + int(row['x1'])) / 2
                        text_y = int(row['y1']) + 10
                        self.added_rect = self.canvas.create_rectangle(int(row['x0']), int(row['y0']), int(row['x1']), int(row['y1']),outline="#00ff00", width= 2, tags= unique_tag)
                        self.canvas.create_text(
                            text_x, text_y, 
                            text=f"Zone {row['numero_zone']} : 100%", fill="#00ff00", 
                            tags=unique_tag
                            )
                        
                        print("référence ajoutée")
                        
    def draw_data(self):
        
        data = self.db.search_timestamp(self.timestamp)
        dico_pourcentage = {}
        for cam, zone, pct in data:
            dico_pourcentage[(str(cam), str(zone))] = pct
            
        with open(self.csv_file, newline = "") as csv_data:
            reader = csv.DictReader(csv_data)
            for row in reader: 
                if row['numero_camera'] == self.camera and row["type"] == self.type:
                    zone_id = row['numero_zone']
                    unique_tag = f"rect_{zone_id}"
                    text_x = (int(row["x0"]) + int(row["x1"])) / 2
                    text_y = int(row["y1"]) + 10
                    
                    cle_recherche = (str(self.camera), str(zone_id))
                    
                    if cle_recherche in dico_pourcentage:
                        pourcentage = dico_pourcentage[cle_recherche]
                        texte_affichage = f"Zone {zone_id} : {pourcentage}%"
                        
                        if pourcentage < Config.SCORE_SEUIL:
                            couleur = "red"
                        else:
                            couleur = "#00ff00"
                    else :
                        texte_affichage = f"Zone {zone_id} : NA"
                        couleur = "orange"
                        
                    self.canvas.create_rectangle(int(row["x0"]), int(row["y0"]), int(row["x1"]), int(row["y1"]), outline= couleur, width =2, tags=unique_tag)
                    self.canvas.create_text(
                        text_x, text_y, 
                        text= texte_affichage, fill=couleur, 
                        tags=unique_tag
                        )

    def next_path(self, path_pattern):
        """
        Finds the next free path in an sequentially named list of files
        
        e.g. path_pattern = 'file_%s.txt':
            
        file-1.txt
        file-2.txt
        file-3.txt
            
        Runs in log(n) time where n is the number of existing files in sequence
        """
        i = 1
            
        while os.path.exists(path_pattern % i):
            i = i * 2
        a, b = (i // 2, i)
        while a + 1 < b:
            c = (a + b) // 2
            a, b = (c, b) if os.path.exists(path_pattern % c) else (a, c)
            
        return path_pattern % b
    
    
    def get_next_zone_id(self):
        if not self.csv_file or not os.path.exists(self.csv_file):
            return 1
            
        try:
            with open(self.csv_file, newline="") as csv_data:
                reader = list(csv.DictReader(csv_data))
        except Exception:
            return 1
            
        if not reader:
            return 1
            
        all_ids = [int(row['numero_zone']) for row in reader if row.get('numero_zone', '').isdigit()]
        max_id = max(all_ids) if all_ids else 0
        
        if self.type in ["None", "none", None]:
            return max_id + 1
            
        m_ids = set(int(row['numero_zone']) for row in reader if row.get('type') == 'M' and row.get('numero_zone', '').isdigit())
        c_ids = set(int(row['numero_zone']) for row in reader if row.get('type') == 'C' and row.get('numero_zone', '').isdigit())
        
        if self.type == 'M':
            unpaired_c = c_ids - m_ids
            if unpaired_c:
                return min(unpaired_c) 
            return max_id + 1
            
        if self.type == 'C':
            unpaired_m = m_ids - c_ids
            if unpaired_m:
                return min(unpaired_m)
            return max_id + 1
            
        return max_id + 1
    
    def get_target_directory(self):
        """A modifier pour gerer selon les cameras aussi"""
        base_dir = f"./ref/{self.vehicule}_{self.motorisation}"
        if self.type == "M":
            return os.path.join(base_dir, "metal")
        elif self.type == "C":
            return os.path.join(base_dir, "classique")
        else:
            return base_dir
        
root = tk.Tk()
app= Image_cropper(root)
root.mainloop()