import sys
import os
import json
import tkinter as tk
import locale
import threading
import queue
import time
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
    from duckduckgo_search import DDGS
    import fitz  # PyMuPDF per i PDF
    import docx  # python-docx per i file Word
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
        "app_title": "AI Dataset Builder Pro - Ultimate",
        "menu_file": "File",
        "menu_import": "Import Settings...",
        "menu_export": "Export Settings...",
        "menu_exit": "Exit",
        "title_search_params": "Search Parameters",
        "lbl_include": "Keywords to Include:",
        "lbl_exclude": "Keywords to Exclude:",
        "lbl_exts": "File Types (comma separated):",
        "lbl_lang": "Search Language (Preferred):",
        "lbl_age": "File Age / Year Range:",
        "lbl_max_files": "Max Files per Ext:",
        "title_output_dir": "Output Directory",
        "placeholder_dir": "Select destination folder...",
        "btn_browse": "Browse...",
        "chk_clean": "Enable Data Cleaning (Extract text from PDF/DOCX/TXT)",
        "btn_start": "START PROCESSING",
        "btn_stop": "STOP",
        "age_any": "Any Time",
        "age_day": "Past Day",
        "age_week": "Past Week",
        "age_month": "Past Month",
        "age_year": "Past Year",
        "lang_en": "English",
        "lang_it": "Italian",
        "lang_es": "Spanish",
        "lang_fr": "French",
        "lang_de": "German",
        "msg_saved": "[SYSTEM] Settings saved successfully in: {}",
        "msg_err_save": "[ERROR] Cannot save settings: {}",
        "msg_loaded": "[SYSTEM] Settings loaded from: {}",
        "msg_err_load": "[ERROR] Cannot load settings: {}",
        "err_include_empty": "[ERROR] 'Keywords to Include' cannot be empty.",
        "err_exts_empty": "[ERROR] 'File Types' cannot be empty.",
        "err_dir_invalid": "[ERROR] Please select a valid Output Directory.",
        "err_max_files": "[ERROR] 'Max Files' must be a positive integer.",
        "log_start": "=== STARTING DATASET BUILDER ===",
        "log_clean_dir": "Cleaned data folder created: {}",
        "log_stop_req": "[INFO] Stop requested. Waiting for pending operations...",
        "log_stopped": "=== PROCESS STOPPED BY USER ===",
        "log_completed": "=== PROCESS COMPLETED SUCCESSFULLY ===",
        "log_ext_phase": "\n>>> SEARCHING FOR FILE EXTENSION: .{} <<<",
        "log_phase": "[SEARCH] Starting phase in language: {} ({})",
        "log_strict": "  -> 'Strict' query: {}",
        "log_loose": "  -> 'Loose' query: {}",
        "log_no_res": "     No results found for this query.",
        "log_found_url": "[PRODUCER] Found URL: {}",
        "log_skip_html": "   -> [SKIPPED] URL is a webpage (HTML), not a document.",
        "log_saved": "   -> Saved: {}",
        "log_dl_fail": "   -> [FAILED] Download blocked or not accessible.",
        "log_extracting": "[CONSUMER] Extracting text from: {}...",
        "log_txt_saved": "   -> Cleaned text saved to: {}",
        "log_no_txt": "   -> [WARNING] No detectable text in: {}",
        "log_clean_fail": "   -> [ERROR] Cleaning failed for {}",
        "log_clean_skip": "   -> [INFO] Cleaning not supported for {} files. Saved as-is.",
        "log_api_err": "[ERROR] Search API Error: {}",
        "log_summary": "\n[INFO] Search finished. Found {}/{} possible documents for .{}"
    },
    "it": {
        "app_title": "Costruttore Dataset AI Pro - Ultimate",
        "menu_file": "File",
        "menu_import": "Importa Impostazioni...",
        "menu_export": "Esporta Impostazioni...",
        "menu_exit": "Esci",
        "title_search_params": "Parametri di Ricerca",
        "lbl_include": "Parole da Includere (es: concorso, bando):",
        "lbl_exclude": "Parole da Escludere (es: corso, forum):",
        "lbl_exts": "Tipi di File (separati da virgola):",
        "lbl_lang": "Lingua di Ricerca (Preferita):",
        "lbl_age": "Età File / Intervallo Anni:",
        "lbl_max_files": "Max File PER Estensione:",
        "title_output_dir": "Cartella di Destinazione",
        "placeholder_dir": "Seleziona cartella di destinazione...",
        "btn_browse": "Sfoglia...",
        "chk_clean": "Abilita Pulizia Dati (Estrai testo da PDF / DOCX / TXT)",
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
        "err_exts_empty": "[ERRORE] Devi specificare almeno un'estensione (es. pdf).",
        "err_dir_invalid": "[ERRORE] Cartella di Destinazione non valida.",
        "err_max_files": "[ERRORE] 'Max File' deve essere un numero intero.",
        "log_start": "=== AVVIO COSTRUZIONE DATASET ===",
        "log_clean_dir": "Cartella dati puliti creata: {}",
        "log_stop_req": "[INFO] Arresto richiesto. Attesa completamento...",
        "log_stopped": "=== PROCESSO ARRESTATO DALL'UTENTE ===",
        "log_completed": "=== PROCESSO COMPLETATO CON SUCCESSO ===",
        "log_ext_phase": "\n>>> RICERCA PER ESTENSIONE FILE: .{} <<<",
        "log_phase": "[RICERCA] Lingua: {} ({})",
        "log_strict": "  -> Tentativo 'Stretto': {}",
        "log_loose": "  -> Tentativo 'Allargato': {}",
        "log_no_res": "     Nessun risultato trovato per questa query.",
        "log_found_url": "[PRODUTTORE] Trovato URL: {}",
        "log_skip_html": "   -> [SALTATO] È una pagina web, non un documento scaricabile.",
        "log_saved": "   -> Salvato: {}",
        "log_dl_fail": "   -> [FALLITO] Download bloccato dal server (403/Timeout).",
        "log_extracting": "[CONSUMATORE] Estrazione testo da: {}...",
        "log_txt_saved": "   -> Testo estratto salvato in: {}",
        "log_no_txt": "   -> [ATTENZIONE] Nessun testo rilevabile in: {}",
        "log_clean_fail": "   -> [ERRORE] Estrazione fallita per {}",
        "log_clean_skip": "   -> [INFO] Pulizia non supportata per i file {}. Documento salvato così com'è.",
        "log_api_err": "[ERRORE] Errore Motore di Ricerca: {}",
        "log_summary": "\n[INFO] Ricerca conclusa. Trovati {}/{} documenti per .{}"
    },
    "es": {
        "app_title": "Constructor de Datasets AI Pro - Ultimate",
        "menu_file": "Archivo",
        "menu_import": "Importar Ajustes...",
        "menu_export": "Exportar Ajustes...",
        "menu_exit": "Salir",
        "title_search_params": "Parámetros de Búsqueda",
        "lbl_include": "Palabras a Incluir:",
        "lbl_exclude": "Palabras a Excluir:",
        "lbl_exts": "Tipos de Archivo (separados por coma):",
        "lbl_lang": "Idioma de Búsqueda:",
        "lbl_age": "Rango de Edad / Años:",
        "lbl_max_files": "Max Archivos POR Extensión:",
        "title_output_dir": "Carpeta de Destino",
        "placeholder_dir": "Seleccione la carpeta de destino...",
        "btn_browse": "Explorar...",
        "chk_clean": "Habilitar Limpieza de Datos (Extraer texto de PDF/DOCX/TXT)",
        "btn_start": "INICIAR PROCESO",
        "btn_stop": "DETENER",
        "age_any": "Cualquier",
        "age_day": "Último Día",
        "age_week": "Última Semana",
        "age_month": "Último Mes",
        "age_year": "Último Año",
        "lang_en": "Inglés",
        "lang_it": "Italiano",
        "lang_es": "Español",
        "lang_fr": "Francés",
        "lang_de": "Alemán",
        "msg_saved": "[SISTEMA] Ajustes guardados en: {}",
        "msg_err_save": "[ERROR] No se pueden guardar los ajustes: {}",
        "msg_loaded": "[SISTEMA] Ajustes cargados de: {}",
        "msg_err_load": "[ERROR] No se pueden cargar los ajustes: {}",
        "err_include_empty": "[ERROR] 'Palabras a Incluir' es obligatorio.",
        "err_exts_empty": "[ERROR] 'Tipos de Archivo' no puede estar vacío.",
        "err_dir_invalid": "[ERROR] Carpeta de Destino no válida.",
        "err_max_files": "[ERROR] 'Max Archivos' debe ser un número entero.",
        "log_start": "=== INICIANDO CONSTRUCTOR DE DATASET ===",
        "log_clean_dir": "Carpeta de datos limpios creada: {}",
        "log_stop_req": "[INFO] Parada solicitada. Esperando...",
        "log_stopped": "=== PROCESO DETENIDO POR EL USUARIO ===",
        "log_completed": "=== PROCESO COMPLETADO CON ÉXITO ===",
        "log_ext_phase": "\n>>> BUSCANDO EXTENSIÓN: .{} <<<",
        "log_phase": "[BÚSQUEDA] Idioma: {} ({})",
        "log_strict": "  -> Intento 'Estricto': {}",
        "log_loose": "  -> Intento 'Amplio': {}",
        "log_no_res": "     No se encontraron resultados.",
        "log_found_url": "[PRODUCTOR] URL Encontrada: {}",
        "log_skip_html": "   -> [SALTADO] Es una página web (HTML).",
        "log_saved": "   -> Guardado: {}",
        "log_dl_fail": "   -> [FALLO] Descarga bloqueada o inaccesible.",
        "log_extracting": "[CONSUMIDOR] Extrayendo texto de: {}...",
        "log_txt_saved": "   -> Texto guardado en: {}",
        "log_no_txt": "   -> [ADVERTENCIA] No hay texto detectable en: {}",
        "log_clean_fail": "   -> [ERROR] Fallo en limpieza para {}",
        "log_clean_skip": "   -> [INFO] Limpieza no soportada para {}. Guardado tal cual.",
        "log_api_err": "[ERROR] Error de API: {}",
        "log_summary": "\n[INFO] Búsqueda finalizada. Encontrados {}/{} documentos para .{}"
    },
    "fr": {
        "app_title": "Constructeur de Dataset AI Pro - Ultimate",
        "menu_file": "Fichier",
        "menu_import": "Importer Paramètres...",
        "menu_export": "Exporter Paramètres...",
        "menu_exit": "Quitter",
        "title_search_params": "Paramètres de Recherche",
        "lbl_include": "Mots à Inclure:",
        "lbl_exclude": "Mots à Exclure:",
        "lbl_exts": "Types de Fichiers (séparés par virgule):",
        "lbl_lang": "Langue de Recherche:",
        "lbl_age": "Âge du Fichier / Années:",
        "lbl_max_files": "Max Fichiers PAR Extension:",
        "title_output_dir": "Dossier de Destination",
        "placeholder_dir": "Sélectionner le dossier...",
        "btn_browse": "Parcourir...",
        "chk_clean": "Activer Nettoyage (Extraire texte de PDF/DOCX/TXT)",
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
        "msg_saved": "[SYSTÈME] Paramètres enregistrés : {}",
        "msg_err_save": "[ERREUR] Impossible d'enregistrer : {}",
        "msg_loaded": "[SYSTÈME] Paramètres chargés : {}",
        "msg_err_load": "[ERREUR] Impossible de charger : {}",
        "err_include_empty": "[ERREUR] 'Mots à Inclure' requis.",
        "err_exts_empty": "[ERREUR] 'Types de Fichiers' requis.",
        "err_dir_invalid": "[ERREUR] Dossier invalide.",
        "err_max_files": "[ERREUR] 'Max Fichiers' doit être un entier.",
        "log_start": "=== DÉMARRAGE DU CONSTRUCTEUR ===",
        "log_clean_dir": "Dossier de données propres créé : {}",
        "log_stop_req": "[INFO] Arrêt demandé. Patientez...",
        "log_stopped": "=== PROCESSUS ARRÊTÉ PAR L'UTILISATEUR ===",
        "log_completed": "=== PROCESSUS TERMINÉ AVEC SUCCÈS ===",
        "log_ext_phase": "\n>>> RECHERCHE EXTENSION: .{} <<<",
        "log_phase": "[RECHERCHE] Langue: {} ({})",
        "log_strict": "  -> Requête 'Stricte': {}",
        "log_loose": "  -> Requête 'Large': {}",
        "log_no_res": "     Aucun résultat.",
        "log_found_url": "[PRODUCTEUR] URL trouvée: {}",
        "log_skip_html": "   -> [IGNORÉ] Page web (HTML).",
        "log_saved": "   -> Enregistré: {}",
        "log_dl_fail": "   -> [ÉCHEC] Téléchargement bloqué.",
        "log_extracting": "[CONSOMMATEUR] Extraction de: {}...",
        "log_txt_saved": "   -> Texte enregistré: {}",
        "log_no_txt": "   -> [ATTENTION] Aucun texte dans: {}",
        "log_clean_fail": "   -> [ERREUR] Échec nettoyage pour {}",
        "log_clean_skip": "   -> [INFO] Nettoyage non supporté pour {}. Enregistré tel quel.",
        "log_api_err": "[ERREUR] Erreur API: {}",
        "log_summary": "\n[INFO] Recherche terminée. Trouvé {}/{} documents pour .{}"
    },
    "de": {
        "app_title": "KI Dataset Builder Pro - Ultimate",
        "menu_file": "Datei",
        "menu_import": "Einstellungen importieren...",
        "menu_export": "Einstellungen exportieren...",
        "menu_exit": "Beenden",
        "title_search_params": "Suchparameter",
        "lbl_include": "Einzuschließende Wörter:",
        "lbl_exclude": "Auszuschließende Wörter:",
        "lbl_exts": "Dateitypen (kommagetrennt):",
        "lbl_lang": "Suchsprache:",
        "lbl_age": "Dateialter / Jahre:",
        "lbl_max_files": "Max Dateien PRO Endung:",
        "title_output_dir": "Zielordner",
        "placeholder_dir": "Zielordner auswählen...",
        "btn_browse": "Durchsuchen...",
        "chk_clean": "Datenbereinigung (Text aus PDF/DOCX/TXT extrahieren)",
        "btn_start": "STARTEN",
        "btn_stop": "STOPPEN",
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
        "msg_saved": "[SYSTEM] Einstellungen gespeichert in: {}",
        "msg_err_save": "[FEHLER] Speichern fehlgeschlagen: {}",
        "msg_loaded": "[SYSTEM] Einstellungen geladen aus: {}",
        "msg_err_load": "[FEHLER] Laden fehlgeschlagen: {}",
        "err_include_empty": "[FEHLER] 'Einzuschließende Wörter' erforderlich.",
        "err_exts_empty": "[FEHLER] 'Dateitypen' erforderlich.",
        "err_dir_invalid": "[FEHLER] Ungültiger Zielordner.",
        "err_max_files": "[FEHLER] 'Max Dateien' muss eine Ganzzahl sein.",
        "log_start": "=== DATASET BUILDER GESTARTET ===",
        "log_clean_dir": "Ordner für bereinigte Daten erstellt: {}",
        "log_stop_req": "[INFO] Stopp angefordert. Bitte warten...",
        "log_stopped": "=== PROZESS VOM BENUTZER GESTOPPT ===",
        "log_completed": "=== PROZESS ERFOLGREICH ABGESCHLOSSEN ===",
        "log_ext_phase": "\n>>> SUCHE NACH ENDUNG: .{} <<<",
        "log_phase": "[SUCHE] Sprache: {} ({})",
        "log_strict": "  -> 'Strenge' Suche: {}",
        "log_loose": "  -> 'Erweiterte' Suche: {}",
        "log_no_res": "     Keine Ergebnisse gefunden.",
        "log_found_url": "[PRODUZENT] URL gefunden: {}",
        "log_skip_html": "   -> [ÜBERSPRUNGEN] Webseite (HTML).",
        "log_saved": "   -> Gespeichert: {}",
        "log_dl_fail": "   -> [FEHLGESCHLAGEN] Download blockiert.",
        "log_extracting": "[KONSUMENT] Extrahiere Text aus: {}...",
        "log_txt_saved": "   -> Text gespeichert in: {}",
        "log_no_txt": "   -> [WARNUNG] Kein Text gefunden in: {}",
        "log_clean_fail": "   -> [FEHLER] Bereinigung fehlgeschlagen für {}",
        "log_clean_skip": "   -> [INFO] Bereinigung nicht unterstützt für {}. Unverändert gespeichert.",
        "log_api_err": "[FEHLER] API-Fehler: {}",
        "log_summary": "\n[INFO] Suche beendet. {}/{} Dokumente für .{} gefunden."
    }
}

# ==============================================================================
# CLASSE PRINCIPALE DELL'APPLICAZIONE
# ==============================================================================
class DatasetBuilderApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.os_lang_code = self._detect_os_language()
        self.t = TRANSLATIONS.get(self.os_lang_code, TRANSLATIONS["it"]) # Fallback a IT

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
            if lang in ['en', 'it']:
                return lang
        except Exception:
            pass
        return 'it'

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
        self.textbox_include = ctk.CTkTextbox(self.frame_params, height=60)
        self.textbox_include.grid(row=1, column=1, padx=10, pady=5, sticky="ew")

        ctk.CTkLabel(self.frame_params, text=self.t["lbl_exclude"], justify="left").grid(row=2, column=0, padx=10, pady=5, sticky="nw")
        self.textbox_exclude = ctk.CTkTextbox(self.frame_params, height=60)
        self.textbox_exclude.grid(row=2, column=1, padx=10, pady=5, sticky="ew")

        ctk.CTkLabel(self.frame_params, text=self.t["lbl_exts"], justify="left").grid(row=3, column=0, padx=10, pady=5, sticky="w")
        self.entry_exts = ctk.CTkEntry(self.frame_params)
        self.entry_exts.grid(row=3, column=1, padx=10, pady=5, sticky="ew")
        self.entry_exts.insert(0, "pdf, docx, doc, txt")

        ctk.CTkLabel(self.frame_params, text=self.t["lbl_lang"]).grid(row=4, column=0, padx=10, pady=5, sticky="w")
        self.combo_lang = ctk.CTkComboBox(self.frame_params, values=list(self.lang_options_map.keys()))
        self.combo_lang.grid(row=4, column=1, padx=10, pady=5, sticky="ew")
        self.combo_lang.set(self.t.get(f"lang_{self.os_lang_code}", self.t["lang_it"]))

        ctk.CTkLabel(self.frame_params, text=self.t["lbl_age"], justify="left").grid(row=5, column=0, padx=10, pady=5, sticky="w")
        self.combo_age = ctk.CTkComboBox(self.frame_params, values=list(self.age_options_map.keys()))
        self.combo_age.grid(row=5, column=1, padx=10, pady=5, sticky="ew")
        self.combo_age.set(self.t["age_any"])

        ctk.CTkLabel(self.frame_params, text=self.t["lbl_max_files"]).grid(row=6, column=0, padx=10, pady=(5, 10), sticky="w")
        self.combo_max_files = ctk.CTkComboBox(self.frame_params, values=["5", "10", "20", "50", "100"])
        self.combo_max_files.grid(row=6, column=1, padx=10, pady=(5, 10), sticky="ew")
        self.combo_max_files.set("10")

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
    # UTILITY & SALVATAGGIO
    # ==============================================================================
    def save_settings(self):
        file_path = ctk.filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Files", "*.json")])
        if not file_path: return
        settings = {
            "include_kw": self.textbox_include.get("1.0", "end-1c"),
            "exclude_kw": self.textbox_exclude.get("1.0", "end-1c"),
            "extensions": self.entry_exts.get(),
            "language": self.combo_lang.get(),
            "age": self.combo_age.get(),
            "max_files": self.combo_max_files.get(),
            "output_dir": self.entry_out_dir.get(),
            "clean_enabled": self.checkbox_clean.get()
        }
        with open(file_path, 'w', encoding='utf-8') as f: json.dump(settings, f, indent=4)
        self.log_message(self.t["msg_saved"].format(file_path))

    def load_settings(self):
        file_path = ctk.filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])
        if not file_path: return
        with open(file_path, 'r', encoding='utf-8') as f: settings = json.load(f)
        self.textbox_include.delete("1.0", "end"); self.textbox_include.insert("1.0", settings.get("include_kw", ""))
        self.textbox_exclude.delete("1.0", "end"); self.textbox_exclude.insert("1.0", settings.get("exclude_kw", ""))
        self.entry_exts.delete(0, "end"); self.entry_exts.insert(0, settings.get("extensions", "pdf, docx"))
        self.combo_lang.set(settings.get("language", self.combo_lang.get()))
        self.combo_age.set(settings.get("age", self.combo_age.get()))
        self.combo_max_files.set(settings.get("max_files", "10"))
        self.entry_out_dir.delete(0, "end"); self.entry_out_dir.insert(0, settings.get("output_dir", ""))
        if settings.get("clean_enabled", 1) == 1: self.checkbox_clean.select()
        else: self.checkbox_clean.deselect()

    def _browse_directory(self):
        d = ctk.filedialog.askdirectory()
        if d: self.entry_out_dir.delete(0, ctk.END); self.entry_out_dir.insert(0, d)

    def log_message(self, message):
        def update_log():
            self.textbox_log.configure(state="normal")
            self.textbox_log.insert(ctk.END, message + "\n")
            self.textbox_log.see(ctk.END) 
            self.textbox_log.configure(state="disabled")
        self.after(0, update_log)

    def toggle_ui_state(self, running: bool):
        state = "disabled" if running else "normal"
        for widget in [self.textbox_include, self.textbox_exclude, self.entry_exts, self.combo_lang, 
                       self.combo_age, self.combo_max_files, self.entry_out_dir, self.btn_browse, self.checkbox_clean]:
            widget.configure(state=state)
        self.btn_start.configure(state="disabled" if running else "normal")
        self.btn_stop.configure(state="normal" if running else "disabled")

    # ==============================================================================
    # GESTIONE THREAD
    # ==============================================================================
    def start_process(self):
        if not self.textbox_include.get("1.0", "end-1c").strip(): return self.log_message(self.t["err_include_empty"])
        if not self.entry_exts.get().strip(): return self.log_message(self.t["err_exts_empty"])
        out_dir = self.entry_out_dir.get().strip()
        if not out_dir or not os.path.isdir(out_dir): return self.log_message(self.t["err_dir_invalid"])
        try: max_files = int(self.combo_max_files.get().strip())
        except ValueError: return self.log_message(self.t["err_max_files"])

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

        self.producer_thread = threading.Thread(target=self._search_producer_worker, args=(out_dir, enable_cleaning, max_files), daemon=True)
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
        if self.stop_event.is_set(): self.log_message(self.t["log_stopped"])
        else: self.log_message(self.t["log_completed"])

    # ==============================================================================
    # THREAD PRODUTTORE (RICERCA E DOWNLOAD)
    # ==============================================================================
    def _search_producer_worker(self, output_dir, enable_cleaning, max_files):
        inc_list = [kw.strip() for kw in re.split(r'[,\n]', self.textbox_include.get("1.0", "end-1c")) if kw.strip()]
        exc_list = []
        for kw in [k.strip() for k in re.split(r'[,\n]', self.textbox_exclude.get("1.0", "end-1c")) if k.strip()]:
            clean_kw = kw.lstrip('-').strip() 
            exc_list.append(f'-"{clean_kw}"' if ' ' in clean_kw and not clean_kw.startswith('"') else f"-{clean_kw}")
        exclusions_str = " " + " ".join(exc_list) if exc_list else ""

        extensions = [e.strip().lstrip('.').lower() for e in self.entry_exts.get().split(',')]
        ui_lang_val, ui_age_val = self.combo_lang.get(), self.combo_age.get()
        region = self.lang_options_map.get(ui_lang_val, "wt-wt")
        time_param = self.age_options_map.get(ui_age_val, None)

        # Gestione anni personalizzati
        date_query_append = ""
        if time_param is None and ui_age_val != self.t["age_any"]:
            match = re.match(r'(\d{4})\s*-\s*(\d{4})', ui_age_val)
            if match:
                start_y, end_y = int(match.group(1)), int(match.group(2))
                if start_y <= end_y:
                    years = [str(y) for y in range(start_y, end_y + 1)]
                    date_query_append = " (" + " OR ".join(years) + ")"
            else: date_query_append = f" {ui_age_val}" 

        seen_urls = set()

        # Ciclo per ogni estensione richiesta (es. prima PDF, poi DOCX, poi TXT)
        for ext in extensions:
            if self.stop_event.is_set(): break
            self.log_message(self.t["log_ext_phase"].format(ext.upper()))
            
            downloaded_count = 0
            
            # 1. Ricerca Stretta (AND)
            strict_query = " ".join(inc_list) + f" filetype:{ext}" + exclusions_str + date_query_append
            self.log_message(self.t["log_strict"].format(strict_query))
            downloaded_count = self._execute_search_phase(strict_query, time_param, region, max_files, downloaded_count, seen_urls, output_dir, enable_cleaning, ext)

            # 2. Ricerca Larga (OR) se non si è raggiunto il max
            if not self.stop_event.is_set() and downloaded_count < max_files and len(inc_list) > 1:
                loose_query = "(" + " OR ".join(inc_list) + f") filetype:{ext}" + exclusions_str + date_query_append
                self.log_message(self.t["log_loose"].format(loose_query))
                downloaded_count = self._execute_search_phase(loose_query, time_param, region, max_files, downloaded_count, seen_urls, output_dir, enable_cleaning, ext)

            self.log_message(self.t["log_summary"].format(downloaded_count, max_files, ext.upper()))

    def _execute_search_phase(self, query, time_param, region, max_files, current_count, seen_urls, output_dir, enable_cleaning, target_ext):
        try:
            with DDGS() as ddgs:
                results = ddgs.text(query, timelimit=time_param, region=region, max_results=max_files*3)
                if not results:
                    self.log_message(self.t["log_no_res"])
                    return current_count

                for result in results:
                    if self.stop_event.is_set() or current_count >= max_files: break
                        
                    url = result.get('href')
                    if not url or url in seen_urls: continue 

                    seen_urls.add(url)
                    self.log_message(self.t["log_found_url"].format(urllib.parse.unquote(url)[:80] + "..."))
                    
                    downloaded_path = self._download_file(url, output_dir, current_count, target_ext)
                    if downloaded_path:
                        current_count += 1
                        if enable_cleaning:
                            self.download_queue.put((downloaded_path, target_ext))

        except Exception as e:
            self.log_message(self.t["log_api_err"].format(e))
            
        return current_count

    def _download_file(self, url, output_dir, current_count, target_ext):
        """Scaricatore potenziato per aggirare i blocchi della PA e gestire vari formati."""
        # Intestazioni molto più robuste per simulare un browser reale
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, come Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        try:
            response = requests.get(url, headers=headers, stream=True, timeout=15)
            # Se la pagina ci dà 403 Forbidden, proviamo a passare oltre silenziosamente
            if response.status_code in [403, 401, 406]:
                self.log_message(self.t["log_dl_fail"])
                return None
                
            response.raise_for_status()

            # Evitiamo di scaricare pagine HTML pure (forum, siti web)
            content_type = response.headers.get('Content-Type', '').lower()
            if 'text/html' in content_type:
                self.log_message(self.t["log_skip_html"])
                return None

            # Recupero nome file intelligente
            filename = ""
            cd = response.headers.get('Content-Disposition', '')
            if 'filename=' in cd:
                matches = re.findall(r'filename="?([^"]+)"?', cd)
                if matches: filename = matches[0]

            if not filename:
                parsed_url = urllib.parse.urlparse(url)
                filename = os.path.basename(urllib.parse.unquote(parsed_url.path))

            if not filename or '.' not in filename:
                filename = f"documento_trovato_{int(time.time())}.{target_ext}"
            
            # Assicuriamoci che l'estensione finale sia corretta se manca
            if not filename.lower().endswith(f".{target_ext}"):
                filename = f"{filename}.{target_ext}"

            safe_filename = re.sub(r'[\\/*?:"<>|]', "_", filename)
            file_path = os.path.join(output_dir, safe_filename)

            if os.path.exists(file_path):
                base, ext = os.path.splitext(safe_filename)
                safe_filename = f"{base}_{int(time.time())}{ext}"
                file_path = os.path.join(output_dir, safe_filename)

            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if self.stop_event.is_set(): return None
                    if chunk: f.write(chunk)
            
            self.log_message(self.t["log_saved"].format(safe_filename))
            return file_path

        except requests.exceptions.RequestException:
            self.log_message(self.t["log_dl_fail"])
            return None
        except Exception as e:
            self.log_message(f"   -> [ERROR] {str(e)}")
            return None

    # ==============================================================================
    # THREAD CONSUMATORE (ESTRAZIONE TESTO MULTI-FORMATO)
    # ==============================================================================
    def _cleaner_consumer_worker(self, cleaned_dir):
        while True:
            try:
                task = self.download_queue.get(timeout=2) 
            except queue.Empty:
                if self.stop_event.is_set(): break
                continue

            if task is None:
                self.download_queue.task_done()
                break

            file_path, ext = task
            filename = os.path.basename(file_path)
            txt_path = os.path.join(cleaned_dir, f"{os.path.splitext(filename)[0]}.txt")

            self.log_message(self.t["log_extracting"].format(filename))

            try:
                full_text = ""
                
                # --- ESTRAZIONE PDF ---
                if ext == 'pdf':
                    doc = fitz.open(file_path)
                    for page_num in range(len(doc)):
                        if self.stop_event.is_set(): break
                        full_text += doc.load_page(page_num).get_text() + "\n"
                    doc.close()

                # --- ESTRAZIONE WORD (.docx) ---
                elif ext == 'docx':
                    doc = docx.Document(file_path)
                    full_text = "\n".join([para.text for para in doc.paragraphs])

                # --- ESTRAZIONE TESTO PIATTO (.txt, .csv) ---
                elif ext in ['txt', 'csv']:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        full_text = f.read()

                # --- FORMATI NON SUPPORTATI PER L'ESTRAZIONE (es. .doc vecchi, .xlsx) ---
                else:
                    self.log_message(self.t["log_clean_skip"].format(ext.upper()))
                    self.download_queue.task_done()
                    continue

                if self.stop_event.is_set(): break

                # Pulizia del testo estratto (rimuove troppi a capo)
                clean_text = re.sub(r'\n{3,}', '\n\n', full_text).strip()

                if clean_text:
                    with open(txt_path, 'w', encoding='utf-8') as f:
                        f.write(clean_text)
                    self.log_message(self.t["log_txt_saved"].format(os.path.basename(txt_path)))
                else:
                    self.log_message(self.t["log_no_txt"].format(filename))

            except Exception as e:
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