import sys
import os
import json
import tkinter as tk
import locale
import threading
import queue
import time
import random
import re
import urllib.parse
import base64
import tempfile

# ==============================================================================
# CONTROLLO DIPENDENZE
# ==============================================================================
try:
    import customtkinter as ctk
    import requests
    from ddgs import DDGS # <--- ABBIAMO CAMBIATO IL NOME QUI
    import fitz  # PyMuPDF
    import docx
except ImportError as e:
    print("="*60)
    print("MISSING DEPENDENCIES / DIPENDENZE MANCANTI!")
    print(f"Error: {e}")
    print("\nPlease install required packages using / Installa i pacchetti richiesti con:")
    print("pip install customtkinter requests duckduckgo-search PyMuPDF python-docx")
    print("="*60)
    sys.exit(1)

# ==============================================================================
# ICONA SEGNAPOSTO (Base64)
# ==============================================================================
ICON_BASE64 = b'iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAADsMAAA7DAcdvqGQAAAAZdEVYdFNvZnR3YXJlAFBhaW50Lk5FVCB2My41LjbQg61aAAAAJUlEQVQ4T2NkoBAwUqifYdQAxqEwajoYRg1gHAqjpoNh+AAzEwMAJ6YBzXUuIycAAAAASUVORK5CYII='

# ==============================================================================
# DIZIONARIO TRADUZIONI (i18n)
# ==============================================================================
TRANSLATIONS = {
    "en": {
        "app_title": "AI Dataset Builder Pro",
        "menu_file": "File",
        "menu_import": "Import Settings...",
        "menu_export": "Export Settings...",
        "menu_exit": "Exit",
        "title_search_params": "Search Parameters",
        "lbl_include": "Keywords to Include\n(comma or newline separated):",
        "lbl_exclude": "Keywords to Exclude\n(comma or newline separated):",
        "lbl_lang": "Search Language (Preferred):",
        "lbl_age": "File Age / Year Range:\n(e.g., 'Past Year' or '2022-2024')",
        "lbl_max_files": "Max Files to Download:",
        "title_output_dir": "Output Directory",
        "placeholder_dir": "Select destination folder...",
        "btn_browse": "Browse...",
        "chk_clean": "Enable Data Cleaning (Extract text from downloaded PDFs)",
        "btn_start": "START PROCESSING",
        "btn_stop": "STOP",
        
        # Combo boxes options
        "age_any": "Any Time",
        "age_day": "Past Day",
        "age_week": "Past Week",
        "age_month": "Past Month",
        "age_year": "Past Year",
        
        # Languages
        "lang_en": "English",
        "lang_it": "Italian",
        "lang_es": "Spanish",
        "lang_fr": "French",
        "lang_de": "German",

        # Logs and Messages
        "msg_saved": "[SYSTEM] Settings saved successfully in: {}",
        "msg_err_save": "[ERROR] Cannot save settings: {}",
        "msg_loaded": "[SYSTEM] Settings loaded from: {}",
        "msg_err_load": "[ERROR] Cannot load settings: {}",
        "err_include_empty": "[ERROR] 'Keywords to Include' cannot be empty.",
        "err_dir_invalid": "[ERROR] Please select a valid Output Directory.",
        "err_max_files": "[ERROR] 'Max Files' must be a positive integer.",
        "log_start": "=== STARTING DATASET BUILDER ===",
        "log_clean_dir": "Cleaned data folder created: {}",
        "log_stop_req": "[INFO] Stop requested. Waiting for pending operations...",
        "log_stopped": "=== PROCESS STOPPED BY USER ===",
        "log_completed": "=== PROCESS COMPLETED SUCCESSFULLY ===",
        "log_phase": "\n[SEARCH] Starting phase in language: {} ({})",
        "log_strict": "  -> 'Strict' attempt (AND): {}",
        "log_loose": "  -> 'Loose' attempt (OR): {}",
        "log_no_res": "     No results found in this phase.",
        "log_found_url": "[PRODUCER] Found URL: {}",
        "log_skip_html": "   -> [SKIPPED] URL points to a webpage (HTML), not a PDF.",
        "log_saved": "   -> Saved: {}",
        "log_dl_fail": "   -> [FAILED] Could not download {}",
        "log_extracting": "[CONSUMER] Extracting text from: {}...",
        "log_txt_saved": "   -> Cleaned text saved to: {}",
        "log_no_txt": "   -> [WARNING] No detectable text in: {}",
        "log_clean_fail": "   -> [ERROR] Cleaning failed for {}",
        "log_api_err": "[ERROR] Search API Error: {}",
        "log_summary": "\n[INFO] Search finished. Found {}/{} possible documents."
    },
    "it": {
        "app_title": "Costruttore Dataset AI Pro",
        "menu_file": "File",
        "menu_import": "Importa Impostazioni...",
        "menu_export": "Esporta Impostazioni...",
        "menu_exit": "Esci",
        "title_search_params": "Parametri di Ricerca",
        "lbl_include": "Parole da Includere\n(separate da virgola o a capo):",
        "lbl_exclude": "Parole da Escludere\n(separate da virgola o a capo):",
        "lbl_lang": "Lingua di Ricerca (Preferita):",
        "lbl_age": "Età File / Intervallo Anni:\n(es. 'Ultimo Anno' o '2022-2024')",
        "lbl_max_files": "Numero Max File da Scaricare:",
        "title_output_dir": "Cartella di Destinazione",
        "placeholder_dir": "Seleziona cartella di destinazione...",
        "btn_browse": "Sfoglia...",
        "chk_clean": "Abilita Pulizia Dati (Estrai testo dai PDF scaricati)",
        "btn_start": "AVVIA ELABORAZIONE",
        "btn_stop": "FERMA",
        
        "age_any": "Qualsiasi",
        "age_day": "Ultimo Giorno",
        "age_week": "Ultima Settimana",
        "age_month": "Ultimo Mese",
        "age_year": "Ultimo Anno",
        
        "lang_en": "Inglese",
        "lang_it": "Italiano",
        "lang_es": "Spagnolo",
        "lang_fr": "Francese",
        "lang_de": "Tedesco",

        "msg_saved": "[SISTEMA] Impostazioni salvate in: {}",
        "msg_err_save": "[ERRORE] Impossibile salvare: {}",
        "msg_loaded": "[SISTEMA] Impostazioni caricate da: {}",
        "msg_err_load": "[ERRORE] Impossibile caricare: {}",
        "err_include_empty": "[ERRORE] 'Parole da Includere' richiesto.",
        "err_dir_invalid": "[ERRORE] Cartella di Destinazione non valida.",
        "err_max_files": "[ERRORE] 'Numero Max File' deve essere numerico.",
        "log_start": "=== AVVIO COSTRUZIONE DATASET ===",
        "log_clean_dir": "Cartella dati puliti creata: {}",
        "log_stop_req": "[INFO] Arresto richiesto. Attesa completamento...",
        "log_stopped": "=== PROCESSO ARRESTATO DALL'UTENTE ===",
        "log_completed": "=== PROCESSO COMPLETATO CON SUCCESSO ===",
        "log_phase": "\n[RICERCA] Avvio Passaggio in lingua: {} ({})",
        "log_strict": "  -> Tentativo 'Stretto' (AND): {}",
        "log_loose": "  -> Tentativo 'Allargato' (OR): {}",
        "log_no_res": "     Nessun risultato trovato in questa fase.",
        "log_found_url": "[PRODUTTORE] Trovato URL: {}",
        "log_skip_html": "   -> [SALTATO] L'URL punta a una pagina web (HTML), non a un PDF.",
        "log_saved": "   -> Salvato: {}",
        "log_dl_fail": "   -> [FALLITO] Impossibile scaricare {}",
        "log_extracting": "[CONSUMATORE] Estrazione testo da: {}...",
        "log_txt_saved": "   -> Testo pulito salvato in: {}",
        "log_no_txt": "   -> [ATTENZIONE] Nessun testo rilevabile in: {}",
        "log_clean_fail": "   -> [ERRORE] Fallita pulizia per {}",
        "log_api_err": "[ERRORE] Errore API Ricerca: {}",
        "log_summary": "\n[INFO] Ricerca conclusa. Trovati {}/{} documenti."
    },
    "es": {
        "app_title": "Constructor de Datasets IA Pro",
        "menu_file": "Archivo",
        "menu_import": "Importar Configuraciones...",
        "menu_export": "Exportar Configuraciones...",
        "menu_exit": "Salir",
        "title_search_params": "Parámetros de Búsqueda",
        "lbl_include": "Palabras a Incluir\n(separadas por coma o salto de línea):",
        "lbl_exclude": "Palabras a Excluir\n(separadas por coma o salto de línea):",
        "lbl_lang": "Idioma de Búsqueda (Preferido):",
        "lbl_age": "Antigüedad / Rango de Años:\n(ej. 'Último Año' o '2022-2024')",
        "lbl_max_files": "Número Máx de Archivos a Descargar:",
        "title_output_dir": "Directorio de Salida",
        "placeholder_dir": "Seleccione carpeta de destino...",
        "btn_browse": "Explorar...",
        "chk_clean": "Habilitar Limpieza de Datos (Extraer texto de PDFs)",
        "btn_start": "INICIAR PROCESO",
        "btn_stop": "DETENER",
        
        "age_any": "Cualquier fecha",
        "age_day": "Último Día",
        "age_week": "Última Semana",
        "age_month": "Último Mes",
        "age_year": "Último Año",
        
        "lang_en": "Inglés",
        "lang_it": "Italiano",
        "lang_es": "Español",
        "lang_fr": "Francés",
        "lang_de": "Alemán",

        "msg_saved": "[SISTEMA] Configuraciones guardadas en: {}",
        "msg_err_save": "[ERROR] No se pudo guardar: {}",
        "msg_loaded": "[SISTEMA] Configuraciones cargadas de: {}",
        "msg_err_load": "[ERROR] No se pudo cargar: {}",
        "err_include_empty": "[ERROR] 'Palabras a Incluir' no puede estar vacío.",
        "err_dir_invalid": "[ERROR] Seleccione un Directorio de Salida válido.",
        "err_max_files": "[ERROR] 'Máx Archivos' debe ser un entero positivo.",
        "log_start": "=== INICIANDO CONSTRUCTOR DE DATASETS ===",
        "log_clean_dir": "Carpeta de datos limpios creada: {}",
        "log_stop_req": "[INFO] Parada solicitada. Esperando...",
        "log_stopped": "=== PROCESSO DETENIDO POR EL USUARIO ===",
        "log_completed": "=== PROCESSO COMPLETADO CON ÉXITO ===",
        "log_phase": "\n[BÚSQUEDA] Iniciando fase en idioma: {} ({})",
        "log_strict": "  -> Intento 'Estricto' (AND): {}",
        "log_loose": "  -> Intento 'Amplio' (OR): {}",
        "log_no_res": "     No se encontraron resultados.",
        "log_found_url": "[PRODUCTOR] URL encontrada: {}",
        "log_skip_html": "   -> [SALTADO] La URL apunta a una página web (HTML), no a un PDF.",
        "log_saved": "   -> Guardado: {}",
        "log_dl_fail": "   -> [FALLO] No se pudo descargar {}",
        "log_extracting": "[CONSUMIDOR] Extrayendo texto de: {}...",
        "log_txt_saved": "   -> Texto limpio guardado en: {}",
        "log_no_txt": "   -> [ADVERTENCIA] No hay texto detectable en: {}",
        "log_clean_fail": "   -> [ERROR] Fallo limpieza de {}",
        "log_api_err": "[ERROR] Error de API: {}",
        "log_summary": "\n[INFO] Búsqueda finalizada. {}/{} documentos."
    },
    "fr": {
        "app_title": "Créateur de Datasets IA Pro",
        "menu_file": "Fichier",
        "menu_import": "Importer Paramètres...",
        "menu_export": "Exporter Paramètres...",
        "menu_exit": "Quitter",
        "title_search_params": "Paramètres de Recherche",
        "lbl_include": "Mots à Inclure\n(séparés par virgule ou saut de ligne):",
        "lbl_exclude": "Mots à Exclure\n(séparés par virgule ou saut de ligne):",
        "lbl_lang": "Langue de Recherche (Préférée):",
        "lbl_age": "Âge / Plage d'Années:\n(ex. 'Année Dernière' ou '2022-2024')",
        "lbl_max_files": "Fichiers Max à Télécharger:",
        "title_output_dir": "Dossier de Sortie",
        "placeholder_dir": "Sélectionner le dossier...",
        "btn_browse": "Parcourir...",
        "chk_clean": "Activer Nettoyage (Extraire texte des PDFs)",
        "btn_start": "DÉMARRER",
        "btn_stop": "ARRÊTER",
        
        "age_any": "N'importe quand",
        "age_day": "Dernier Jour",
        "age_week": "Dernière Semaine",
        "age_month": "Dernier Mois",
        "age_year": "Dernière Année",
        
        "lang_en": "Anglais",
        "lang_it": "Italien",
        "lang_es": "Espagnol",
        "lang_fr": "Français",
        "lang_de": "Allemand",

        "msg_saved": "[SYSTÈME] Paramètres sauvegardés: {}",
        "msg_err_save": "[ERREUR] Impossible de sauvegarder: {}",
        "msg_loaded": "[SYSTÈME] Paramètres chargés: {}",
        "msg_err_load": "[ERREUR] Impossible de charger: {}",
        "err_include_empty": "[ERREUR] 'Mots à Inclure' requis.",
        "err_dir_invalid": "[ERREUR] Dossier invalide.",
        "err_max_files": "[ERREUR] 'Fichiers Max' doit être positif.",
        "log_start": "=== DÉMARRAGE CRÉATEUR DATASET ===",
        "log_clean_dir": "Dossier de données nettoyées: {}",
        "log_stop_req": "[INFO] Arrêt demandé. En attente...",
        "log_stopped": "=== PROCESSUS ARRÊTÉ ===",
        "log_completed": "=== PROCESSUS TERMINÉ ===",
        "log_phase": "\n[RECHERCHE] Phase en langue: {} ({})",
        "log_strict": "  -> Essai 'Strict' (AND): {}",
        "log_loose": "  -> Essai 'Large' (OR): {}",
        "log_no_res": "     Aucun résultat.",
        "log_found_url": "[PRODUCTEUR] URL trouvée: {}",
        "log_skip_html": "   -> [IGNORÉ] L'URL pointe vers une page web (HTML), pas un PDF.",
        "log_saved": "   -> Sauvegardé: {}",
        "log_dl_fail": "   -> [ÉCHEC] Impossible de télécharger {}",
        "log_extracting": "[CONSOMMATEUR] Extraction texte: {}...",
        "log_txt_saved": "   -> Texte nettoyé sauvegardé: {}",
        "log_no_txt": "   -> [ATTENTION] Aucun texte dans: {}",
        "log_clean_fail": "   -> [ERREUR] Échec nettoyage pour {}",
        "log_api_err": "[ERREUR] Erreur API: {}",
        "log_summary": "\n[INFO] Recherche terminée. {}/{} documents."
    },
    "de": {
        "app_title": "KI Dataset Builder Pro",
        "menu_file": "Datei",
        "menu_import": "Einstellungen importieren...",
        "menu_export": "Einstellungen exportieren...",
        "menu_exit": "Beenden",
        "title_search_params": "Suchparameter",
        "lbl_include": "Einzuschließende Wörter\n(Komma oder Zeilenumbruch):",
        "lbl_exclude": "Auszuschließende Wörter\n(Komma oder Zeilenumbruch):",
        "lbl_lang": "Suchsprache (Bevorzugt):",
        "lbl_age": "Dateialter / Jahresbereich:\n(z.B. 'Letztes Jahr' oder '2022-2024')",
        "lbl_max_files": "Max Dateien zum Herunterladen:",
        "title_output_dir": "Ausgabeverzeichnis",
        "placeholder_dir": "Zielordner auswählen...",
        "btn_browse": "Durchsuchen...",
        "chk_clean": "Datenbereinigung (Text aus PDFs extrahieren)",
        "btn_start": "STARTEN",
        "btn_stop": "STOPP",
        
        "age_any": "Jederzeit",
        "age_day": "Letzter Tag",
        "age_week": "Letzte Woche",
        "age_month": "Letzter Monat",
        "age_year": "Letztes Jahr",
        
        "lang_en": "Englisch",
        "lang_it": "Italienisch",
        "lang_es": "Spanisch",
        "lang_fr": "Französisch",
        "lang_de": "Deutsch",

        "msg_saved": "[SYSTEM] Gespeichert in: {}",
        "msg_err_save": "[FEHLER] Speichern fehlgeschlagen: {}",
        "msg_loaded": "[SYSTEM] Geladen von: {}",
        "msg_err_load": "[FEHLER] Laden fehlgeschlagen: {}",
        "err_include_empty": "[FEHLER] 'Einzuschließende Wörter' erforderlich.",
        "err_dir_invalid": "[FEHLER] Ungültiges Verzeichnis.",
        "err_max_files": "[FEHLER] 'Max Dateien' muss positiv sein.",
        "log_start": "=== START DATASET BUILDER ===",
        "log_clean_dir": "Bereinigter Datenordner: {}",
        "log_stop_req": "[INFO] Stopp angefordert. Bitte warten...",
        "log_stopped": "=== PROZESS GESTOPPT ===",
        "log_completed": "=== PROZESS ABGESCHLOSSEN ===",
        "log_phase": "\n[SUCHE] Phase in Sprache: {} ({})",
        "log_strict": "  -> 'Strikter' Versuch (AND): {}",
        "log_loose": "  -> 'Lockerer' Versuch (OR): {}",
        "log_no_res": "     Keine Ergebnisse gefunden.",
        "log_found_url": "[PRODUCER] URL gefunden: {}",
        "log_skip_html": "   -> [ÜBERSPRUNGEN] URL verweist auf eine Webseite (HTML), nicht auf eine PDF-Datei.",
        "log_saved": "   -> Gespeichert: {}",
        "log_dl_fail": "   -> [FEHLGESCHLAGEN] Download nicht möglich {}",
        "log_extracting": "[CONSUMER] Textextraktion: {}...",
        "log_txt_saved": "   -> Text gespeichert in: {}",
        "log_no_txt": "   -> [WARNUNG] Kein Text in: {}",
        "log_clean_fail": "   -> [FEHLER] Bereinigung fehlgeschlagen für {}",
        "log_api_err": "[FEHLER] Such-API-Fehler: {}",
        "log_summary": "\n[INFO] Suche beendet. {}/{} Dokumente."
    }
}

# ==============================================================================
# CLASSE PRINCIPALE DELL'APPLICAZIONE
# ==============================================================================
class DatasetBuilderApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.os_lang_code = self._detect_os_language()
        self.t = TRANSLATIONS.get(self.os_lang_code, TRANSLATIONS["en"])

        self.title(self.t["app_title"])
        self.geometry("900x850") 
        self.minsize(500, 500)
        
        self._set_app_icon()
        self._build_menu()

        self.main_frame = ctk.CTkScrollableFrame(self)
        self.main_frame.pack(fill="both", expand=True, padx=5, pady=5)
        self.main_frame.grid_columnconfigure(0, weight=1)

        self.is_running = False
        self.stop_event = threading.Event()
        self.download_queue = queue.Queue(maxsize=100)
        
        self.lang_options_map = {
            self.t["lang_en"]: "wt-wt",
            self.t["lang_it"]: "it-it",
            self.t["lang_es"]: "es-es",
            self.t["lang_fr"]: "fr-fr",
            self.t["lang_de"]: "de-de"
        }
        
        self.age_options_map = {
            self.t["age_any"]: None,
            self.t["age_day"]: "d",
            self.t["age_week"]: "w",
            self.t["age_month"]: "m",
            self.t["age_year"]: "y"
        }
        
        self._build_ui()

    def _detect_os_language(self):
        try:
            lang = os.environ.get('LANG', '').split('_')[0].lower()
            if not lang:
                loc = locale.getdefaultlocale()[0]
                if loc:
                    lang = loc.split('_')[0].lower()
            if lang in ['en', 'it', 'es', 'fr', 'de']:
                return lang
        except Exception:
            pass
        return 'en'

    def _set_app_icon(self):
        try:
            icon_data = base64.b64decode(ICON_BASE64)
            temp_icon_path = os.path.join(tempfile.gettempdir(), "placeholder_icon.ico")
            with open(temp_icon_path, "wb") as f:
                f.write(icon_data)
            self.iconbitmap(temp_icon_path)
        except Exception:
            pass 

    def _build_menu(self):
        menubar = tk.Menu(self)
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label=self.t["menu_import"], command=self.load_settings)
        filemenu.add_command(label=self.t["menu_export"], command=self.save_settings)
        filemenu.add_separator()
        filemenu.add_command(label=self.t["menu_exit"], command=self.quit)
        menubar.add_cascade(label=self.t["menu_file"], menu=filemenu)
        self.config(menu=menubar)

    def _build_ui(self):
        # --- 1. PARAMETRI RICERCA ---
        self.frame_params = ctk.CTkFrame(self.main_frame, corner_radius=10)
        self.frame_params.grid(row=0, column=0, padx=10, pady=(10, 10), sticky="ew")
        self.frame_params.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(self.frame_params, text=self.t["title_search_params"], font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, columnspan=2, padx=10, pady=(10, 5), sticky="w")

        ctk.CTkLabel(self.frame_params, text=self.t["lbl_include"], justify="left").grid(row=1, column=0, padx=10, pady=5, sticky="nw")
        self.textbox_include = ctk.CTkTextbox(self.frame_params, height=80)
        self.textbox_include.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        self.textbox_include._textbox.configure(undo=True, autoseparators=True, maxundo=-1)

        ctk.CTkLabel(self.frame_params, text=self.t["lbl_exclude"], justify="left").grid(row=2, column=0, padx=10, pady=5, sticky="nw")
        self.textbox_exclude = ctk.CTkTextbox(self.frame_params, height=80)
        self.textbox_exclude.grid(row=2, column=1, padx=10, pady=5, sticky="ew")
        self.textbox_exclude._textbox.configure(undo=True, autoseparators=True, maxundo=-1)

        ctk.CTkLabel(self.frame_params, text=self.t["lbl_lang"]).grid(row=3, column=0, padx=10, pady=5, sticky="w")
        self.combo_lang = ctk.CTkComboBox(self.frame_params, values=list(self.lang_options_map.keys()))
        self.combo_lang.grid(row=3, column=1, padx=10, pady=5, sticky="ew")
        self.combo_lang.set(self.t.get(f"lang_{self.os_lang_code}", self.t["lang_en"]))

        ctk.CTkLabel(self.frame_params, text=self.t["lbl_age"], justify="left").grid(row=4, column=0, padx=10, pady=5, sticky="nw")
        self.combo_age = ctk.CTkComboBox(self.frame_params, values=list(self.age_options_map.keys()))
        self.combo_age.grid(row=4, column=1, padx=10, pady=10, sticky="ew")
        self.combo_age.set(self.t["age_any"])

        ctk.CTkLabel(self.frame_params, text=self.t["lbl_max_files"]).grid(row=5, column=0, padx=10, pady=(5, 10), sticky="w")
        self.combo_max_files = ctk.CTkComboBox(self.frame_params, values=["10", "20", "50", "100", "200", "500"])
        self.combo_max_files.grid(row=5, column=1, padx=10, pady=(5, 10), sticky="ew")
        self.combo_max_files.set("20")

        # --- NUOVI CAMPI PER LE API DI BRAVE SEARCH ---
        lbl_api_text = "Brave API Key:" if self.os_lang_code == 'en' else "Chiave API Brave:"
        ctk.CTkLabel(self.frame_params, text=lbl_api_text).grid(row=6, column=0, padx=10, pady=(5, 10), sticky="w")
        self.entry_api_key = ctk.CTkEntry(self.frame_params, show="*") 
        self.entry_api_key.grid(row=6, column=1, padx=10, pady=(5, 10), sticky="ew")

        # --- 2. OUTPUT DIR ---
        self.frame_dir = ctk.CTkFrame(self.main_frame, corner_radius=10)
        self.frame_dir.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
        self.frame_dir.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(self.frame_dir, text=self.t["title_output_dir"], font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, columnspan=3, padx=10, pady=(10, 5), sticky="w")
        
        self.entry_out_dir = ctk.CTkEntry(self.frame_dir, placeholder_text=self.t["placeholder_dir"])
        self.entry_out_dir.grid(row=1, column=0, columnspan=2, padx=(10, 5), pady=(5, 10), sticky="ew")
        
        self.btn_browse = ctk.CTkButton(self.frame_dir, text=self.t["btn_browse"], width=100, command=self._browse_directory)
        self.btn_browse.grid(row=1, column=2, padx=(5, 10), pady=(5, 10), sticky="e")

        # --- 3. OPZIONI ---
        self.frame_options = ctk.CTkFrame(self.main_frame, corner_radius=10)
        self.frame_options.grid(row=2, column=0, padx=10, pady=10, sticky="ew")
        
        self.checkbox_clean = ctk.CTkCheckBox(self.frame_options, text=self.t["chk_clean"])
        self.checkbox_clean.grid(row=0, column=0, padx=20, pady=15, sticky="w")
        self.checkbox_clean.select() 

        # --- 4. CONTROLLI ---
        self.frame_controls = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.frame_controls.grid(row=3, column=0, padx=10, pady=10, sticky="ew")
        self.frame_controls.grid_columnconfigure((0, 1), weight=1)

        self.btn_start = ctk.CTkButton(self.frame_controls, text=self.t["btn_start"], fg_color="green", hover_color="darkgreen", height=40, font=ctk.CTkFont(weight="bold"), command=self.start_process)
        self.btn_start.grid(row=0, column=0, padx=(0, 10), pady=0, sticky="ew")

        self.btn_stop = ctk.CTkButton(self.frame_controls, text=self.t["btn_stop"], fg_color="red", hover_color="darkred", height=40, font=ctk.CTkFont(weight="bold"), state="disabled", command=self.stop_process)
        self.btn_stop.grid(row=0, column=1, padx=(10, 0), pady=0, sticky="ew")

        # --- 5. LOG TERMINAL ---
        self.textbox_log = ctk.CTkTextbox(self.main_frame, state="disabled", wrap="word", font=ctk.CTkFont(family="Consolas", size=12), height=300)
        self.textbox_log.grid(row=4, column=0, padx=10, pady=(10, 20), sticky="nsew")

    # ==============================================================================
    # SALVATAGGIO / CARICAMENTO
    # ==============================================================================
    def save_settings(self):
        file_path = ctk.filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Files", "*.json")])
        if not file_path: return

        settings = {
            "include_kw": self.textbox_include.get("1.0", "end-1c"),
            "exclude_kw": self.textbox_exclude.get("1.0", "end-1c"),
            "language": self.combo_lang.get(),
            "age": self.combo_age.get(),
            "max_files": self.combo_max_files.get(),
            "output_dir": self.entry_out_dir.get(),
            "clean_enabled": self.checkbox_clean.get(),
            "brave_api_key": self.entry_api_key.get() # SALVATAGGIO API BRAVE
        }

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=4)
            self.log_message(self.t["msg_saved"].format(file_path))
        except Exception as e:
            self.log_message(self.t["msg_err_save"].format(e))

    def load_settings(self):
        file_path = ctk.filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])
        if not file_path: return

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                settings = json.load(f)

            self.textbox_include.delete("1.0", "end")
            self.textbox_include.insert("1.0", settings.get("include_kw", ""))
            
            self.textbox_exclude.delete("1.0", "end")
            self.textbox_exclude.insert("1.0", settings.get("exclude_kw", ""))
            
            lang_val = settings.get("language", self.combo_lang.get())
            if lang_val in self.lang_options_map: self.combo_lang.set(lang_val)
            
            age_val = settings.get("age", self.combo_age.get())
            if age_val in self.age_options_map: self.combo_age.set(age_val)
            
            self.combo_max_files.set(settings.get("max_files", "20"))
            
            self.entry_out_dir.delete(0, "end")
            self.entry_out_dir.insert(0, settings.get("output_dir", ""))
            
            if settings.get("clean_enabled", 1) == 1: self.checkbox_clean.select()
            else: self.checkbox_clean.deselect()
            
            # CARICAMENTO API BRAVE
            self.entry_api_key.delete(0, "end")
            self.entry_api_key.insert(0, settings.get("brave_api_key", ""))
                
            self.log_message(self.t["msg_loaded"].format(file_path))
        except Exception as e:
            self.log_message(self.t["msg_err_load"].format(e))

    # ==============================================================================
    # UTILITY
    # ==============================================================================
    def _browse_directory(self):
        directory = ctk.filedialog.askdirectory()
        if directory:
            self.entry_out_dir.delete(0, ctk.END)
            self.entry_out_dir.insert(0, directory)

    def log_message(self, message):
        def update_log():
            self.textbox_log.configure(state="normal")
            self.textbox_log.insert(ctk.END, message + "\n")
            self.textbox_log.see(ctk.END) 
            self.textbox_log.configure(state="disabled")
        self.after(0, update_log)

    def toggle_ui_state(self, running: bool):
        state = "disabled" if running else "normal"
        for widget in [self.textbox_include, self.textbox_exclude, self.combo_lang, self.combo_age, 
                       self.combo_max_files, self.entry_out_dir, self.btn_browse, self.checkbox_clean,
                       self.entry_api_key]: # SOLO L'API KEY
            widget.configure(state=state)
        
        self.btn_start.configure(state="disabled" if running else "normal")
        self.btn_stop.configure(state="normal" if running else "disabled")

    # ==============================================================================
    # GESTIONE THREAD
    # ==============================================================================
    def start_process(self):
        include_kw = self.textbox_include.get("1.0", "end-1c").strip()
        out_dir = self.entry_out_dir.get().strip()
        brave_api = self.entry_api_key.get().strip() # LEGGE L'API BRAVE

        if not include_kw:
            self.log_message(self.t["err_include_empty"])
            return
            
        if not out_dir or not os.path.isdir(out_dir):
            self.log_message(self.t["err_dir_invalid"])
            return
            
        try:
            max_files = int(self.combo_max_files.get().strip())
            if max_files <= 0: raise ValueError
        except ValueError:
            self.log_message(self.t["err_max_files"])
            return

        self.is_running = True
        self.stop_event.clear()
        self.toggle_ui_state(running=True)
        
        self.textbox_log.configure(state="normal")
        self.textbox_log.delete("1.0", ctk.END)
        self.textbox_log.configure(state="disabled")

        self.log_message(self.t["log_start"])

        enable_cleaning = self.checkbox_clean.get() == 1
        cleaned_dir = os.path.join(out_dir, "Cleaned_Data")
        if enable_cleaning and not os.path.exists(cleaned_dir):
            os.makedirs(cleaned_dir)
            self.log_message(self.t["log_clean_dir"].format(cleaned_dir))

        if enable_cleaning:
            self.consumer_thread = threading.Thread(target=self._cleaner_consumer_worker, args=(cleaned_dir,), daemon=True)
            self.consumer_thread.start()

        # PASSIAMO L'API AL THREAD DEL PRODUTTORE
        self.producer_thread = threading.Thread(target=self._search_producer_worker, args=(out_dir, enable_cleaning, max_files, brave_api), daemon=True)
        self.producer_thread.start()

        threading.Thread(target=self._monitor_threads, daemon=True).start()

    def stop_process(self):
        self.log_message(self.t["log_stop_req"])
        self.stop_event.set()
        self.btn_stop.configure(state="disabled") 

    def _monitor_threads(self):
        self.producer_thread.join()
        if self.checkbox_clean.get() == 1:
            self.download_queue.put(None)
            self.consumer_thread.join()
            
        self.is_running = False
        self.after(0, lambda: self.toggle_ui_state(running=False))
        
        if self.stop_event.is_set():
            self.log_message(self.t["log_stopped"])
        else:
            self.log_message(self.t["log_completed"])

    # ==============================================================================
    # THREAD PRODUTTORE
    # ==============================================================================
    def _search_producer_worker(self, output_dir, enable_cleaning, max_files, brave_api):
        include_raw = self.textbox_include.get("1.0", "end-1c").strip()
        exclude_raw = self.textbox_exclude.get("1.0", "end-1c").strip()
        
        ui_lang_val = self.combo_lang.get()
        selected_region = self.lang_options_map.get(ui_lang_val, "wt-wt")
        
        ui_age_val = self.combo_age.get()
        time_param = self.age_options_map.get(ui_age_val, None)

        inc_cleaned = [kw.strip() for kw in re.split(r'[,\n]', include_raw) if kw.strip()]
        exc_cleaned = [kw.strip() for kw in re.split(r'[,\n]', exclude_raw) if kw.strip()]
        
        inc_list = inc_cleaned 
        
        exc_list = []
        for kw in exc_cleaned:
            clean_kw = kw.lstrip('-').strip() 
            if ' ' in clean_kw and not clean_kw.startswith('"'):
                exc_list.append(f'-"{clean_kw}"')
            else:
                exc_list.append(f"-{clean_kw}")
                
        # --- BLOCCO ANTI-SPAZZATURA ---
        exc_list.extend(['-site:zhihu.com', '-site:baidu.com', '-site:zhidao.baidu.com'])
        
        exclusions_str = " " + " ".join(exc_list) if exc_list else ""

        date_query_append = ""
        if time_param is None and ui_age_val != self.t["age_any"]:
            match = re.match(r'(\d{4})\s*-\s*(\d{4})', ui_age_val)
            if match:
                start_y, end_y = int(match.group(1)), int(match.group(2))
                if start_y <= end_y:
                    years = [str(y) for y in range(start_y, end_y + 1)]
                    date_query_append = " (" + " OR ".join(years) + ")"
            else:
                date_query_append = f" {ui_age_val}" 
        
        downloaded_count = 0
        seen_urls = set()

        regions_to_try = [selected_region]
        if selected_region != "wt-wt": regions_to_try.append("wt-wt")

        for region in regions_to_try:
            if self.stop_event.is_set() or downloaded_count >= max_files: break
            
            region_name = ui_lang_val if region == selected_region else self.t["lang_en"]
            self.log_message(self.t["log_phase"].format(region_name, region))

            for target_ext in ["pdf", "docx"]:
                if self.stop_event.is_set() or downloaded_count >= max_files: break
                
                self.log_message(f"=== Searching for format: {target_ext.upper()} ===")

                strict_query = " ".join(inc_list) + f" filetype:{target_ext}" + exclusions_str + date_query_append
                self.log_message(self.t["log_strict"].format(strict_query))
                
                downloaded_count = self._execute_search_phase(strict_query, time_param, region, max_files, downloaded_count, seen_urls, output_dir, enable_cleaning, target_ext, brave_api)

                if self.stop_event.is_set() or downloaded_count >= max_files: break

                if len(inc_list) > 1:
                    loose_query = "(" + " OR ".join(inc_list) + f") filetype:{target_ext}" + exclusions_str + date_query_append
                    self.log_message(self.t["log_loose"].format(loose_query))
                    downloaded_count = self._execute_search_phase(loose_query, time_param, region, max_files, downloaded_count, seen_urls, output_dir, enable_cleaning, target_ext, brave_api)

        if downloaded_count < max_files and not self.stop_event.is_set():
            self.log_message(self.t["log_summary"].format(downloaded_count, max_files))

    def _execute_search_phase(self, query, time_param, region, max_files, current_count, seen_urls, output_dir, enable_cleaning, target_ext, brave_api):
        # --- PHASE 1: DUCKDUCKGO ---
        self.log_message(f"   -> [DDG] Searching on DuckDuckGo...")
        try:
            with DDGS() as ddgs:
                ddg_results = list(ddgs.text(query, timelimit=time_param, region=region, max_results=max_files*2, backend="html"))
                
                if ddg_results:
                    for result in ddg_results:
                        if self.stop_event.is_set() or current_count >= max_files: break
                            
                        url = result.get('href')
                        if not url or url in seen_urls: continue 

                        seen_urls.add(url)
                        self.log_message(self.t["log_found_url"].format(url))
                        
                        downloaded_path = self._download_file(url, output_dir, current_count, target_ext)
                        if downloaded_path:
                            current_count += 1
                            if enable_cleaning:
                                self.download_queue.put(downloaded_path)
                                
                        sleep_time = random.uniform(3.0, 6.0)
                        self.stop_event.wait(sleep_time)

        except Exception as e:
            self.log_message(f"   -> [DDG ERROR] {str(e)}")

        # --- PHASE 2: BRAVE SEARCH API ---
        if current_count < max_files and not self.stop_event.is_set():
            missing_files = max_files - current_count
            self.log_message(f"   -> [BRAVE] Target not reached. Using Brave Search API ({missing_files} missing)...")
            
            if not brave_api:
                self.log_message("   -> [WARNING] Brave API Key is missing! Skipping Brave phase.")
            else:
                try:
                    brave_results = []
                    # Brave permette fino a 20 risultati per pagina.
                    for offset in [0, 1]:
                        if self.stop_event.is_set() or current_count >= max_files: break
                        
                        url = "https://api.search.brave.com/res/v1/web/search"
                        headers = {
                            "Accept": "application/json",
                            "Accept-Encoding": "gzip",
                            "X-Subscription-Token": brave_api
                        }
                        params = {
                            "q": query,
                            "count": 20,
                            "offset": offset
                        }
                        
                        response = requests.get(url, headers=headers, params=params, timeout=15)
                        
                        if response.status_code != 200:
                            self.log_message(f"   -> [BRAVE API ERROR] Code {response.status_code}")
                            break
                            
                        data = response.json()
                        items = data.get("web", {}).get("results", [])
                        
                        if not items:
                            if offset == 0:
                                self.log_message("   -> [BRAVE] 0 results returned by API.")
                            break
                            
                        for item in items:
                            brave_results.append(item.get("url"))
                            
                        self.stop_event.wait(1.5) # Limite rateo API Brave gratuito (1 al sec)

                    # Elaboriamo i risultati estratti
                    for url in brave_results:
                        if self.stop_event.is_set() or current_count >= max_files: break
                        if not url or url in seen_urls: continue

                        seen_urls.add(url)
                        self.log_message(self.t["log_found_url"].format(url))
                        
                        downloaded_path = self._download_file(url, output_dir, current_count, target_ext)
                        if downloaded_path:
                            current_count += 1
                            if enable_cleaning:
                                self.download_queue.put(downloaded_path)

                        sleep_time = random.uniform(3.0, 6.0)
                        self.stop_event.wait(sleep_time)

                except Exception as e:
                    self.log_message(f"   -> [BRAVE ERROR] {str(e)}")

        # --- FINAL CHECK ---
        if current_count == 0:
            self.log_message(self.t["log_no_res"])
            
        return current_count

    def _download_file(self, url, output_dir, current_count, target_ext):
        """Scarica il file verificando che non sia una pagina web mascherata e estraendo il vero nome."""
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        try:
            response = requests.get(url, headers=headers, stream=True, timeout=15)
            response.raise_for_status()

            # 1. Verifica che non sia una pagina web (HTML)
            content_type = response.headers.get('Content-Type', '').lower()
            if 'text/html' in content_type:
                self.log_message(self.t["log_skip_html"])
                return None

            # 2. Cerca di recuperare il nome file originale
            filename = ""
            cd = response.headers.get('Content-Disposition', '')
            if 'filename=' in cd:
                matches = re.findall(r'filename="?([^"]+)"?', cd)
                if matches:
                    filename = matches[0]

            # 3. Se non c'è negli header, lo prende dall'URL
            if not filename:
                parsed_url = urllib.parse.urlparse(url)
                filename = os.path.basename(parsed_url.path)

            # 4. Fallback se ancora non assomiglia all'estensione cercata
            if not filename.lower().endswith(f'.{target_ext}'):
                if filename:
                    filename = f"{filename}.{target_ext}" 
                else:
                    filename = f"dataset_doc_{current_count + 1}.{target_ext}"
            
            # Pulisce il nome file da caratteri non validi
            safe_filename = re.sub(r'[\\/*?:"<>|]', "", filename)
            file_path = os.path.join(output_dir, safe_filename)

            # Evita sovrascritture di file omonimi
            if os.path.exists(file_path):
                base, ext = os.path.splitext(safe_filename)
                safe_filename = f"{base}_{int(time.time())}{ext}"
                file_path = os.path.join(output_dir, safe_filename)

            # 5. Salva fisicamente il file sul disco
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if self.stop_event.is_set(): return None
                    if chunk: f.write(chunk)
            
            self.log_message(self.t["log_saved"].format(safe_filename))
            return file_path

        except requests.exceptions.RequestException:
            self.log_message(self.t["log_dl_fail"].format(url))
            return None
        except Exception as e:
            self.log_message(f"   -> [ERROR] {str(e)}")
            return None

    # ==============================================================================
    # THREAD CONSUMATORE
    # ==============================================================================
    def _cleaner_consumer_worker(self, cleaned_dir):
        while True:
            try:
                pdf_path = self.download_queue.get(timeout=2) 
            except queue.Empty:
                if self.stop_event.is_set(): break
                continue

            if pdf_path is None:
                self.download_queue.task_done()
                break

            filename = os.path.basename(pdf_path)
            txt_path = os.path.join(cleaned_dir, f"{os.path.splitext(filename)[0]}.txt")

            self.log_message(self.t["log_extracting"].format(filename))

            try:
                full_text = ""
                ext = os.path.splitext(filename)[1].lower() # Prende l'estensione (.pdf o .docx)

                if ext == '.pdf':
                    doc = fitz.open(pdf_path) # <-- Assicurati che qui ci sia la tua variabile corretta (es. pdf_path o downloaded_path)
                    for page_num in range(len(doc)):
                        if self.stop_event.is_set(): break
                        full_text += doc.load_page(page_num).get_text() + "\n"
                    doc.close()
                    
                elif ext == '.docx':
                    doc = docx.Document(pdf_path) # <-- Stessa cosa qui
                    for para in doc.paragraphs:
                        if self.stop_event.is_set(): break
                        full_text += para.text + "\n"
                else:
                    self.log_message(f"   -> [WARNING] Unsupported format for cleaning: {ext}")
                    continue

                if self.stop_event.is_set(): break

                clean_text = re.sub(r'\n{3,}', '\n\n', full_text).strip()

                if clean_text:
                    with open(txt_path, 'w', encoding='utf-8') as f:
                        f.write(clean_text)
                    self.log_message(self.t["log_txt_saved"].format(os.path.basename(txt_path)))
                else:
                    self.log_message(self.t["log_no_txt"].format(filename))

            except Exception:
                self.log_message(self.t["log_clean_fail"].format(filename))
            finally:
                self.download_queue.task_done()

if __name__ == "__main__":
    ctk.set_appearance_mode("System")  
    ctk.set_default_color_theme("blue")  
    
    if sys.platform == "win32":
        os.system('chcp 65001 > nul')

    app = DatasetBuilderApp()
    app.mainloop()