#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import cv2
import os
from tkinter import filedialog
import tkinter as tk

def traiter_image_selectionnee_gris_et_flou():
    # 1. Initialiser une fenêtre Tkinter masquée pour l'explorateur de fichiers
    root = tk.Tk()
    root.withdraw() 
    
    # 2. Ouvrir la boîte de dialogue pour sélectionner l'image
    print("[Système] En attente de sélection d'une image...")
    chemin_image = filedialog.askopenfilename(
        title="Sélectionner l'image à traiter (Gris + Flou Gaussien)",
        filetypes=[("Images jointes", "*.jpg *.jpeg *.png *.bmp *.tiff"), ("Tous les fichiers", "*.*")]
    )
    
    if not chemin_image:
        print("[Annulation] Aucune image n'a été sélectionnée.")
        return

    print(f"[Analyse] Image sélectionnée : {os.path.basename(chemin_image)}")

    try:
        # 3. Charger l'image d'origine en couleur
        image_origine = cv2.imread(chemin_image)
        
        if image_origine is None:
            print("[Erreur] Impossible de lire le fichier.")
            return

        # 4. ÉTAPE 1 : Conversion en niveaux de gris
        # Formule mathématique appliquée par OpenCV : Y = 0.299*R + 0.587*G + 0.114*B
        image_gris = cv2.cvtColor(image_origine, cv2.COLOR_BGR2GRAY)
        print("[Succès] Conversion en niveaux de gris effectuée (Passage à 1 canal).")

        # 5. ÉTAPE 2 : Application du Flou Gaussien sur l'image en niveaux de gris
        taille_noyau = (9, 9)
        image_floue = cv2.GaussianBlur(image_gris, taille_noyau, 0)
        print(f"[Succès] Filtrage Gaussien appliqué sur les niveaux de gris (Noyau {taille_noyau[0]}x{taille_noyau[1]}).")

        # 6. Affichage des 3 étapes à l'écran pour ton rapport
        cv2.imshow("1. Image d'origine (Couleur / Brute)", image_origine)
        cv2.imshow("2. Image en Niveaux de Gris (1 Canal)", image_gris)
        cv2.imshow("3. Image finale (Gris + Flou Gaussien)", image_floue)
        
        print("[IHM] Appuie sur n'importe quelle touche sur l'une des images pour fermer.")
        cv2.waitKey(0)
        cv2.destroyAllWindows()

        # 7. Sauvegarde du résultat final
        dossier, nom_fichier = os.path.split(chemin_image)
        nouveau_nom = "gris_flou_" + nom_fichier
        chemin_sauvegarde = os.path.join(dossier, nouveau_nom)
        nouveau_nom = "gris" + nom_fichier
        chemin_sauvegarde_2 = os.path.join(dossier, nouveau_nom)
        
        cv2.imwrite(chemin_sauvegarde_2 , image_gris)
        cv2.imwrite(chemin_sauvegarde, image_floue)
        print(f"[Stockage] Image finale sauvegardée sous : {chemin_sauvegarde}")

    except Exception as e:
        print(f"[🚨 Erreur Traitement] {e}")

if __name__ == "__main__":
    traiter_image_selectionnee_gris_et_flou()