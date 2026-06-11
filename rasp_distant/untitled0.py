import cv2
import numpy as np

def tester_filtre_sobel(chemin_image):
    # 1. Charger l'image
    image = cv2.imread(chemin_image)
    if image is None:
        print(f"Erreur : Impossible de charger l'image au chemin '{chemin_image}'")
        return

    # 2. Convertir en niveaux de gris
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # 3. Appliquer un très léger flou gaussien pour lisser la texture du métal
    blurred = cv2.GaussianBlur(gray, (21, 21), 0)

    # 4. Appliquer le filtre de Sobel (Calcul des pentes)
    # On calcule les reliefs sur l'axe X (vertical) et l'axe Y (horizontal)
    # On utilise CV_64F (float) temporairement pour ne pas "couper" les valeurs mathématiques négatives
    sobel_x = cv2.Sobel(blurred, cv2.CV_64F, 1, 0, ksize=3)
    sobel_y = cv2.Sobel(blurred, cv2.CV_64F, 0, 1, ksize=3)

    # 5. Combiner les deux axes pour obtenir le relief total (La "Magnitude")
    magnitude = cv2.magnitude(sobel_x, sobel_y)

    # 6. Convertir le résultat mathématique en image classique affichable (pixels de 0 à 255)
    sobel_final = cv2.convertScaleAbs(magnitude)

    # --- Optionnel : Améliorer le contraste visuel ---
    # Parfois Sobel est un peu sombre, on peut forcer le contraste pour que le relief "pète" à l'écran
    #sobel_final = cv2.equalizeHist(sobel_final)

    # 7. Affichage des résultats
    cv2.imshow("1 - Image Originale", image)
    cv2.imshow("2 - Filtre Sobel (Relief)", blurred)

    print("Fenêtres ouvertes ! Appuie sur n'importe quelle touche pour quitter.")
    cv2.waitKey(0)
    cv2.destroyAllWindows()

# --- Lancement du test ---
chemin_de_test = "/Users/james/Downloads/zone_1_1.jpg"  # Mets le nom exact de ton image ici
tester_filtre_sobel(chemin_de_test)