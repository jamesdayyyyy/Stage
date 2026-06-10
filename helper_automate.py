import snap7
from snap7.util import get_string, get_bool, set_bool, set_string
from config import Config


class Automate:
    def __init__(self, ip, db_numero, rack=0,slot=0):
        self.ip = ip
        self.db_numero = db_numero
        self.rack = rack
        self.slot = slot
        self.client = snap7.client.Client()
        self.connect() 
    
    def connect(self):
        """
        Se connecte à l'automate en utilisant les paramètres de la l'instance
        Params :
        - None
        Retourne :
        - None
        """
        try:
            self.client.connect(self.ip, self.rack, self.slot)
            print(f"[Automate] Connecté à l'automate")
        except Exception as e:
            print(f"[Erreur - Automate {self.ip}] Échec de la connexion : {e}")
            self.client = None
    
    def lire_data(self):
        """
        Lit les données de l'automate et traduit en informations exploitables
        Params :
        - None
        Retourne :
        - Dictionnaire contenant les informations lues ou None en cas d'erreur"""
        if self.client is None or not self.client.get_connected():
            print("[Automate] Automate hors ligne. Reconnexion...")
            self.connect()
        if self.client is None:
            print("[Automate] Impossible de se connecter à l'automate.")
            return None
        try:
            data = self.client.db_read(self.db_numero,0,36)
            vh_dans_pas = get_bool(data,0,0)
            vis = get_string(data,2).strip()
            type_vh = get_string(data,12).strip() # Non utilisé
            silhouette = get_string(data, 18).strip() # Non utilisé
            code_moteur = get_string(data, 24).strip()
            type_ecran = get_string(data, 30).strip()

            info_traduite = Config.MAPPING_VEHICULE.get(
                code_moteur, 
                {"VEHICULE": "Inconnu", "MOTORISATION": code_moteur}
                )
            info_type_ecran = Config.MAPPING_ECRAN.get(
                type_ecran,
                {"NOM" : "Deflecteur", "TYPE" : "10"}
            )

            return {
                "vh_dans_pas" : vh_dans_pas,
                "vis" : vis,
                "vehicule" : info_traduite.get("VEHICULE", "Inconnu"),
                "motorisation" : info_traduite.get("MOTORISATION", "Inconnu"),
                "type_ecran" : info_type_ecran.get("TYPE", "10")
                }
        
        except Exception as e:
            print(f"[Erreur - Automate] {e}")
            self.client.disconnect()
            self.client = None
            return None
        
    def envoyer_data(self, vehicule_ok, liste_defauts, erreur_systeme= False):
        """
        Envoie les résultats de l'inspection à l'automate en formatant les données
        Params :
        - vehicule_ok : bool indiquant si le véhicule est conforme ou non
        - liste_defauts : liste de chaînes de caractères décrivant les défauts détectés
        - erreur_systeme : bool indiquant s'il y a eu une erreur système empêchant l'inspection
        Retourne :
        - bool indiquant si l'envoi a réussi ou non"""
        if self.client is None or not self.client.get_connected():
            print("[Automate] Automate d'envoie hors ligne. Reconnexion...")
            self.connect()
        if self.client is None:
            print("[Automate] Impossible de se connecter à l'automate pour l'envoi.")
            return False
        try:
            OFFSET_BOOLS = 0
            OFFSET_ARRAY = 2

            NB_MAX_DEFAUTS = 15
            TAILLE_STRING = 34 # String de 32 chars max + 2 octets d'en tête
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
                offset_actuel = OFFSET_ARRAY + (i*TAILLE_STRING)
                if i < len(liste_defauts) and not erreur_systeme:
                    set_string(data, offset_actuel, liste_defauts[i][:32])
                else:
                    set_string(data, offset_actuel, "")
            self.client.db_write(Config.AUTOMATE_DB_ENVOIE, 0, data)
            print("[Automate] Données envoyées à l'automate")
            return True 
        
        except Exception as e:
            print(f"[Erreur - Automate] Échec de l'envoi : {e}")
            self.client.disconnect()
            self.client = None
            return False
            