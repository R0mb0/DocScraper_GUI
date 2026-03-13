import sys
import os
import json
import tkinter as tk

# ==============================================================================
# CONTROLLO DIPENDENZE
# ==============================================================================
try:
    import customtkinter as ctk
    import requests
    from duckduckgo_search import DDGS
    import fitz  # PyMuPDF
except ImportError as e:
    print("="*60)
    print("DIPENDENZE MANCANTI RILEVATE!")
    print(f"Errore: {e}")
    print("\nPer favore, installa i pacchetti richiesti usando il seguente comando:")
    print("pip install customtkinter requests duckduckgo-search PyMuPDF")
    print("="*60)
    sys.exit(1)

import threading
import queue
import time
import re
import urllib.parse
import base64
import tempfile

# ==============================================================================
# ICONA SEGNAPOSTO (Icona 16x16 trasparente/vuota codificata in Base64)
# ==============================================================================
ICON_BASE64 = b'iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAADsMAAA7DAcdvqGQAAAAZdEVYdFNvZnR3YXJlAFBhaW50Lk5FVCB2My41LjbQg61aAAAAJUlEQVQ4T2NkoBAwUqifYdQAxqEwajoYRg1gHAqjpoNh+AAzEwMAJ6YBzXUuIycAAAAASUVORK5CYII='

# ==============================================================================
# CLASSE PRINCIPALE DELL'APPLICAZIONE
# ==============================================================================
class DatasetBuilderApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Configurazione finestra principale
        self.title("Costruttore Dataset AI Pro")
        self.geometry("900x850") 
        self.minsize(500, 500)
        
        # Applica icona
        self._set_app_icon()

        # Menu di sistema per Import/Export
        self._build_menu()

        # Frame Scorrevole Principale (Risolve i problemi di ridimensionamento)
        self.main_frame = ctk.CTkScrollableFrame(self)
        self.main_frame.pack(fill="both", expand=True, padx=5, pady=5)
        self.main_frame.grid_columnconfigure(0, weight=1)

        # Variabili di Stato
        self.is_running = False
        self.stop_event = threading.Event()
        self.download_queue = queue.Queue(maxsize=100)
        
        # Mappatura Lingue DuckDuckGo
        self.languages_map = {
            "Italiano": "it-it",
            "Inglese (Predefinito)": "wt-wt",
            "Spagnolo": "es-es",
            "Francese": "fr-fr",
            "Tedesco": "de-de"
        }
        
        # Costruzione UI
        self._build_ui()

    def _set_app_icon(self):
        """Crea un file .ico temporaneo dal base64 e lo imposta come icona."""
        try:
            icon_data = base64.b64decode(ICON_BASE64)
            temp_icon_path = os.path.join(tempfile.gettempdir(), "placeholder_icon.ico")
            with open(temp_icon_path, "wb") as f:
                f.write(icon_data)
            self.iconbitmap(temp_icon_path)
        except Exception:
            pass 

    def _build_menu(self):
        """Crea la barra dei menu in alto per gestire importazione/esportazione."""
        menubar = tk.Menu(self)
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="Importa Impostazioni...", command=self.load_settings)
        filemenu.add_command(label="Esporta Impostazioni...", command=self.save_settings)
        filemenu.add_separator()
        filemenu.add_command(label="Esci", command=self.quit)
        menubar.add_cascade(label="File", menu=filemenu)
        self.config(menu=menubar)

    def _build_ui(self):
        """Costruisce l'interfaccia utente."""
        # --- 1. FRAME PARAMETRI DI RICERCA ---
        self.frame_params = ctk.CTkFrame(self.main_frame, corner_radius=10)
        self.frame_params.grid(row=0, column=0, padx=10, pady=(10, 10), sticky="ew")
        self.frame_params.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(self.frame_params, text="Parametri di Ricerca", font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, columnspan=2, padx=10, pady=(10, 5), sticky="w")

        # Parole Chiave da Includere (Multilinea con Undo/Redo)
        ctk.CTkLabel(self.frame_params, text="Parole da Includere\n(separate da virgola o a capo):", justify="left").grid(row=1, column=0, padx=10, pady=5, sticky="nw")
        self.textbox_include = ctk.CTkTextbox(self.frame_params, height=80)
        self.textbox_include.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        self.textbox_include._textbox.configure(undo=True, autoseparators=True, maxundo=-1) # Abilita Ctrl+Z e Ctrl+Y

        # Parole Chiave da Escludere (Multilinea con Undo/Redo)
        ctk.CTkLabel(self.frame_params, text="Parole da Escludere\n(separate da virgola o a capo):", justify="left").grid(row=2, column=0, padx=10, pady=5, sticky="nw")
        self.textbox_exclude = ctk.CTkTextbox(self.frame_params, height=80)
        self.textbox_exclude.grid(row=2, column=1, padx=10, pady=5, sticky="ew")
        self.textbox_exclude._textbox.configure(undo=True, autoseparators=True, maxundo=-1) # Abilita Ctrl+Z e Ctrl+Y

        # Lingua Preferita
        ctk.CTkLabel(self.frame_params, text="Lingua di Ricerca (Preferita):").grid(row=3, column=0, padx=10, pady=5, sticky="w")
        self.combo_lang = ctk.CTkComboBox(self.frame_params, values=list(self.languages_map.keys()))
        self.combo_lang.grid(row=3, column=1, padx=10, pady=5, sticky="ew")
        self.combo_lang.set("Italiano") # Predefinito a Italiano

        # Età Massima / Range Date
        ctk.CTkLabel(self.frame_params, text="Età File / Intervallo Anni:\n(es. 'Ultimo Anno' o '2022-2024')", justify="left").grid(row=4, column=0, padx=10, pady=5, sticky="nw")
        self.combo_age = ctk.CTkComboBox(self.frame_params, values=["Qualsiasi", "Ultimo Giorno", "Ultima Settimana", "Ultimo Mese", "Ultimo Anno"])
        self.combo_age.grid(row=4, column=1, padx=10, pady=10, sticky="ew")
        self.combo_age.set("Qualsiasi")

        # Limite File da Scaricare
        ctk.CTkLabel(self.frame_params, text="Numero Max File da Scaricare:").grid(row=5, column=0, padx=10, pady=(5, 10), sticky="w")
        self.combo_max_files = ctk.CTkComboBox(self.frame_params, values=["10", "20", "50", "100", "200"])
        self.combo_max_files.grid(row=5, column=1, padx=10, pady=(5, 10), sticky="ew")
        self.combo_max_files.set("20")

        # --- 2. FRAME DIRECTORY DI OUTPUT ---
        self.frame_dir = ctk.CTkFrame(self.main_frame, corner_radius=10)
        self.frame_dir.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
        self.frame_dir.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(self.frame_dir, text="Cartella di Destinazione", font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, columnspan=3, padx=10, pady=(10, 5), sticky="w")
        
        self.entry_out_dir = ctk.CTkEntry(self.frame_dir, placeholder_text="Seleziona cartella di destinazione...")
        self.entry_out_dir.grid(row=1, column=0, columnspan=2, padx=(10, 5), pady=(5, 10), sticky="ew")
        
        self.btn_browse = ctk.CTkButton(self.frame_dir, text="Sfoglia...", width=100, command=self._browse_directory)
        self.btn_browse.grid(row=1, column=2, padx=(5, 10), pady=(5, 10), sticky="e")

        # --- 3. FRAME OPZIONI ---
        self.frame_options = ctk.CTkFrame(self.main_frame, corner_radius=10)
        self.frame_options.grid(row=2, column=0, padx=10, pady=10, sticky="ew")
        
        self.checkbox_clean = ctk.CTkCheckBox(self.frame_options, text="Abilita Pulizia Dati (Estrai e salva il testo dai PDF scaricati)")
        self.checkbox_clean.grid(row=0, column=0, padx=20, pady=15, sticky="w")
        self.checkbox_clean.select() 

        # --- 4. FRAME CONTROLLI ---
        self.frame_controls = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.frame_controls.grid(row=3, column=0, padx=10, pady=10, sticky="ew")
        self.frame_controls.grid_columnconfigure((0, 1), weight=1)

        self.btn_start = ctk.CTkButton(self.frame_controls, text="AVVIA ELABORAZIONE", fg_color="green", hover_color="darkgreen", height=40, font=ctk.CTkFont(weight="bold"), command=self.start_process)
        self.btn_start.grid(row=0, column=0, padx=(0, 10), pady=0, sticky="ew")

        self.btn_stop = ctk.CTkButton(self.frame_controls, text="FERMA", fg_color="red", hover_color="darkred", height=40, font=ctk.CTkFont(weight="bold"), state="disabled", command=self.stop_process)
        self.btn_stop.grid(row=0, column=1, padx=(10, 0), pady=0, sticky="ew")

        # --- 5. TERMINALE LOG ---
        self.textbox_log = ctk.CTkTextbox(self.main_frame, state="disabled", wrap="word", font=ctk.CTkFont(family="Consolas", size=12), height=300)
        self.textbox_log.grid(row=4, column=0, padx=10, pady=(10, 20), sticky="nsew")

    # ==============================================================================
    # SALVATAGGIO & CARICAMENTO IMPOSTAZIONI (JSON)
    # ==============================================================================
    def save_settings(self):
        """Salva lo stato corrente dell'interfaccia in un file JSON."""
        file_path = ctk.filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json"), ("Tutti i file", "*.*")],
            title="Salva Impostazioni"
        )
        if not file_path:
            return

        settings = {
            "include_kw": self.textbox_include.get("1.0", "end-1c"),
            "exclude_kw": self.textbox_exclude.get("1.0", "end-1c"),
            "language": self.combo_lang.get(),
            "age": self.combo_age.get(),
            "max_files": self.combo_max_files.get(),
            "output_dir": self.entry_out_dir.get(),
            "clean_enabled": self.checkbox_clean.get()
        }

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=4)
            self.log_message(f"[SISTEMA] Impostazioni salvate correttamente in: {file_path}")
        except Exception as e:
            self.log_message(f"[ERRORE] Impossibile salvare le impostazioni: {e}")

    def load_settings(self):
        """Carica lo stato dell'interfaccia da un file JSON."""
        file_path = ctk.filedialog.askopenfilename(
            filetypes=[("JSON Files", "*.json"), ("Tutti i file", "*.*")],
            title="Carica Impostazioni"
        )
        if not file_path:
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                settings = json.load(f)

            # Svuota e riempi i campi
            self.textbox_include.delete("1.0", "end")
            self.textbox_include.insert("1.0", settings.get("include_kw", ""))
            
            self.textbox_exclude.delete("1.0", "end")
            self.textbox_exclude.insert("1.0", settings.get("exclude_kw", ""))
            
            self.combo_lang.set(settings.get("language", "Italiano"))
            self.combo_age.set(settings.get("age", "Qualsiasi"))
            self.combo_max_files.set(settings.get("max_files", "20"))
            
            self.entry_out_dir.delete(0, "end")
            self.entry_out_dir.insert(0, settings.get("output_dir", ""))
            
            if settings.get("clean_enabled", 1) == 1:
                self.checkbox_clean.select()
            else:
                self.checkbox_clean.deselect()
                
            self.log_message(f"[SISTEMA] Impostazioni caricate da: {file_path}")
        except Exception as e:
            self.log_message(f"[ERRORE] Impossibile caricare le impostazioni: {e}")


    # ==============================================================================
    # METODI HELPER E INTERAZIONE UI
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
        self.textbox_include.configure(state=state)
        self.textbox_exclude.configure(state=state)
        self.combo_lang.configure(state=state)
        self.combo_age.configure(state=state)
        self.combo_max_files.configure(state=state)
        self.entry_out_dir.configure(state=state)
        self.btn_browse.configure(state=state)
        self.checkbox_clean.configure(state=state)
        
        if running:
            self.btn_start.configure(state="disabled")
            self.btn_stop.configure(state="normal")
        else:
            self.btn_start.configure(state="normal")
            self.btn_stop.configure(state="disabled")

    # ==============================================================================
    # GESTIONE THREAD
    # ==============================================================================
    def start_process(self):
        include_kw = self.textbox_include.get("1.0", "end-1c").strip()
        out_dir = self.entry_out_dir.get().strip()

        if not include_kw:
            self.log_message("[ERRORE] 'Parole da Includere' non può essere vuoto.")
            return
            
        if not out_dir or not os.path.isdir(out_dir):
            self.log_message("[ERRORE] Seleziona una Cartella di Destinazione valida.")
            return
            
        try:
            max_files = int(self.combo_max_files.get().strip())
            if max_files <= 0:
                raise ValueError
        except ValueError:
            self.log_message("[ERRORE] 'Numero Max File' deve essere un numero intero positivo.")
            return

        self.is_running = True
        self.stop_event.clear()
        self.toggle_ui_state(running=True)
        
        # Pulisci log
        self.textbox_log.configure(state="normal")
        self.textbox_log.delete("1.0", ctk.END)
        self.textbox_log.configure(state="disabled")

        self.log_message("=== AVVIO COSTRUZIONE DATASET ===")

        enable_cleaning = self.checkbox_clean.get() == 1
        cleaned_dir = os.path.join(out_dir, "Cleaned_Data")
        if enable_cleaning and not os.path.exists(cleaned_dir):
            os.makedirs(cleaned_dir)
            self.log_message(f"Cartella dati puliti creata: {cleaned_dir}")

        if enable_cleaning:
            self.consumer_thread = threading.Thread(target=self._cleaner_consumer_worker, args=(cleaned_dir,), daemon=True)
            self.consumer_thread.start()

        self.producer_thread = threading.Thread(target=self._search_producer_worker, args=(out_dir, enable_cleaning, max_files), daemon=True)
        self.producer_thread.start()

        threading.Thread(target=self._monitor_threads, daemon=True).start()

    def stop_process(self):
        self.log_message("[INFO] Arresto richiesto. Attesa completamento operazioni in corso...")
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
            self.log_message("=== PROCESSO ARRESTATO DALL'UTENTE ===")
        else:
            self.log_message("=== PROCESSO COMPLETATO CON SUCCESSO ===")

    # ==============================================================================
    # THREAD 1: PRODUTTORE (Ricerca Progressiva & Download)
    # ==============================================================================
    def _search_producer_worker(self, output_dir, enable_cleaning, max_files):
        """Esegue una ricerca progressiva e gestisce il fallback lingua."""
        # 1. Recupera Input
        include_raw = self.textbox_include.get("1.0", "end-1c").strip()
        exclude_raw = self.textbox_exclude.get("1.0", "end-1c").strip()
        age = self.combo_age.get().strip()
        selected_lang_key = self.combo_lang.get()
        selected_region = self.languages_map.get(selected_lang_key, "wt-wt")

        # Parsing Liste Parole Chiave
        # Divide per virgola o a capo per creare liste logiche
        inc_list = [f'"{kw.strip()}"' if ' ' in kw else kw.strip() for kw in re.split(r'[,\n]', include_raw) if kw.strip()]
        exc_list = [f'-"{kw.strip()}"' if ' ' in kw else f"-{kw.strip()}" for kw in re.split(r'[,\n]', exclude_raw) if kw.strip()]
        
        exclusions_str = " " + " ".join(exc_list) if exc_list else ""

        # Parsing Date
        time_param = None
        date_query_append = ""
        
        if age == "Ultimo Giorno": time_param = 'd'
        elif age == "Ultima Settimana": time_param = 'w'
        elif age == "Ultimo Mese": time_param = 'm'
        elif age == "Ultimo Anno": time_param = 'y'
        elif age != "Qualsiasi":
            match = re.match(r'(\d{4})\s*-\s*(\d{4})', age)
            if match:
                start_year, end_year = int(match.group(1)), int(match.group(2))
                if start_year <= end_year:
                    years = [str(y) for y in range(start_year, end_year + 1)]
                    date_query_append = " (" + " OR ".join(years) + ")"
            else:
                date_query_append = f" {age}"
        
        # --- STRATEGIA DI RICERCA PROGRESSIVA ---
        downloaded_count = 0
        seen_urls = set()

        # Definisci le lingue da provare (Prima la preferita, poi l'inglese/globale se serve)
        regions_to_try = [selected_region]
        if selected_region != "wt-wt":
            regions_to_try.append("wt-wt") # Fallback globale all'inglese

        for region in regions_to_try:
            if self.stop_event.is_set() or downloaded_count >= max_files: break
            
            region_name = "Preferita" if region == selected_region else "Globale (Inglese)"
            self.log_message(f"\n[RICERCA] Avvio Passaggio in lingua: {region_name} ({region})")

            # FASE 1: Ricerca STRETTA (AND) - Tutte le parole chiave insieme
            strict_query = " ".join(inc_list) + " filetype:pdf" + exclusions_str + date_query_append
            self.log_message(f"  -> Tentativo 'Stretto' (AND): {strict_query}")
            downloaded_count = self._execute_search_phase(strict_query, time_param, region, max_files, downloaded_count, seen_urls, output_dir, enable_cleaning)

            if self.stop_event.is_set() or downloaded_count >= max_files: break

            # FASE 2: Ricerca ALLARGATA (OR) - Se ci sono più parole chiave e non abbiamo finito
            if len(inc_list) > 1:
                loose_query = "(" + " OR ".join(inc_list) + ") filetype:pdf" + exclusions_str + date_query_append
                self.log_message(f"  -> Tentativo 'Allargato' (OR): {loose_query}")
                downloaded_count = self._execute_search_phase(loose_query, time_param, region, max_files, downloaded_count, seen_urls, output_dir, enable_cleaning)

        if downloaded_count < max_files and not self.stop_event.is_set():
            self.log_message(f"\n[INFO] Ricerca conclusa. Trovati {downloaded_count}/{max_files} documenti possibili.")

    def _execute_search_phase(self, query, time_param, region, max_files, current_count, seen_urls, output_dir, enable_cleaning):
        """Esegue una specifica query e gestisce i download di quella fase."""
        try:
            with DDGS() as ddgs:
                results = ddgs.text(query, timelimit=time_param, region=region, max_results=max_files*2) # Chiedi di più in caso di scarti
                
                if not results:
                    self.log_message("     Nessun risultato trovato in questa fase.")
                    return current_count

                for result in results:
                    if self.stop_event.is_set() or current_count >= max_files: 
                        break
                        
                    url = result.get('href')
                    if not url or not url.lower().endswith('.pdf') or url in seen_urls:
                        continue 

                    seen_urls.add(url)
                    self.log_message(f"[PRODUTTORE] Trovato URL: {url}")
                    
                    # Genera nome sicuro
                    parsed_url = urllib.parse.urlparse(url)
                    filename = os.path.basename(parsed_url.path)
                    if not filename.endswith('.pdf'):
                        filename = f"doc_{current_count}.pdf"
                    
                    safe_filename = re.sub(r'[\\/*?:"<>|]', "", filename)
                    file_path = os.path.join(output_dir, safe_filename)

                    # Evita sovrascritture se file esiste già
                    if os.path.exists(file_path):
                        base, ext = os.path.splitext(safe_filename)
                        safe_filename = f"{base}_{int(time.time())}{ext}"
                        file_path = os.path.join(output_dir, safe_filename)

                    # Download File
                    success = self._download_file(url, file_path)
                    
                    if success:
                        current_count += 1
                        if enable_cleaning:
                            self.download_queue.put(file_path)

        except Exception as e:
            self.log_message(f"[ERRORE] Errore API Ricerca: {str(e)}")
            
        return current_count

    def _download_file(self, url, dest_path):
        """Scarica fisicamente il file."""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        try:
            response = requests.get(url, headers=headers, stream=True, timeout=15)
            response.raise_for_status()
            
            with open(dest_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if self.stop_event.is_set():
                        return False 
                    if chunk:
                        f.write(chunk)
            self.log_message(f"   -> Salvato: {os.path.basename(dest_path)}")
            return True
        except requests.exceptions.RequestException as e:
            self.log_message(f"   -> [FALLITO] Impossibile scaricare {url}")
            return False

    # ==============================================================================
    # THREAD 2: CONSUMATORE (Pulizia Dati PDF)
    # ==============================================================================
    def _cleaner_consumer_worker(self, cleaned_dir):
        """Estrae e pulisce il testo dai PDF."""
        while True:
            try:
                pdf_path = self.download_queue.get(timeout=2) 
            except queue.Empty:
                if self.stop_event.is_set():
                    break
                continue

            if pdf_path is None:
                self.download_queue.task_done()
                break

            filename = os.path.basename(pdf_path)
            base_name = os.path.splitext(filename)[0]
            txt_path = os.path.join(cleaned_dir, f"{base_name}.txt")

            self.log_message(f"[CONSUMATORE] Estrazione testo da: {filename}...")

            try:
                doc = fitz.open(pdf_path)
                full_text = ""
                for page_num in range(len(doc)):
                    if self.stop_event.is_set(): break
                    page = doc.load_page(page_num)
                    full_text += page.get_text() + "\n"
                doc.close()

                if self.stop_event.is_set(): break

                # Pulizia base del testo
                clean_text = re.sub(r'\n{3,}', '\n\n', full_text)
                clean_text = clean_text.strip()

                if clean_text:
                    with open(txt_path, 'w', encoding='utf-8') as f:
                        f.write(clean_text)
                    self.log_message(f"   -> Testo pulito salvato in: {os.path.basename(txt_path)}")
                else:
                    self.log_message(f"   -> [ATTENZIONE] Nessun testo rilevabile in: {filename}")

            except Exception as e:
                self.log_message(f"   -> [ERRORE] Fallita pulizia per {filename}")
            
            finally:
                self.download_queue.task_done()

# ==============================================================================
# PUNTO D'INGRESSO
# ==============================================================================
if __name__ == "__main__":
    ctk.set_appearance_mode("System")  
    ctk.set_default_color_theme("blue")  
    
    app = DatasetBuilderApp()
    app.mainloop()