import sys
import os

# ==============================================================================
# DEPENDENCY CHECK
# ==============================================================================
try:
    import customtkinter as ctk
    import requests
    from duckduckgo_search import DDGS
    import fitz  # PyMuPDF
except ImportError as e:
    print("="*60)
    print("MISSING DEPENDENCIES DETECTED!")
    print(f"Error: {e}")
    print("\nPlease install the required packages using the following command:")
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
# PLACEHOLDER ICON (Base64 encoded 16x16 transparent/blank icon)
# ==============================================================================
ICON_BASE64 = b'iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAADsMAAA7DAcdvqGQAAAAZdEVYdFNvZnR3YXJlAFBhaW50Lk5FVCB2My41LjbQg61aAAAAJUlEQVQ4T2NkoBAwUqifYdQAxqEwajoYRg1gHAqjpoNh+AAzEwMAJ6YBzXUuIycAAAAASUVORK5CYII='

# ==============================================================================
# MAIN APPLICATION CLASS
# ==============================================================================
class DatasetBuilderApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Setup main window
        self.title("AI Dataset Builder Pro")
        self.geometry("850x800") # Increased height slightly for bigger text boxes
        self.minsize(700, 700)
        
        # Apply placeholder icon
        self._set_app_icon()

        # Configure Grid Layout (Responsive)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(4, weight=1) # Log text box will expand

        # State Variables
        self.is_running = False
        self.stop_event = threading.Event()
        self.download_queue = queue.Queue(maxsize=100)
        
        # Build UI
        self._build_ui()

    def _set_app_icon(self):
        """Creates a temporary .ico file from base64 and sets it as the window icon."""
        try:
            icon_data = base64.b64decode(ICON_BASE64)
            temp_icon_path = os.path.join(tempfile.gettempdir(), "placeholder_icon.ico")
            with open(temp_icon_path, "wb") as f:
                f.write(icon_data)
            self.iconbitmap(temp_icon_path)
        except Exception:
            pass # Fails silently if icon creation is unsupported on OS

    def _build_ui(self):
        """Constructs the user interface."""
        # --- 1. SEARCH PARAMETERS FRAME ---
        self.frame_params = ctk.CTkFrame(self, corner_radius=10)
        self.frame_params.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
        self.frame_params.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(self.frame_params, text="Search Parameters", font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, columnspan=2, padx=10, pady=(10, 5), sticky="w")

        # Keywords to Include (Multi-line)
        ctk.CTkLabel(self.frame_params, text="Include Keywords\n(comma or newline separated):", justify="left").grid(row=1, column=0, padx=10, pady=5, sticky="nw")
        self.textbox_include = ctk.CTkTextbox(self.frame_params, height=80)
        self.textbox_include.grid(row=1, column=1, padx=10, pady=5, sticky="ew")

        # Keywords to Exclude (Multi-line)
        ctk.CTkLabel(self.frame_params, text="Exclude Keywords\n(comma or newline separated):", justify="left").grid(row=2, column=0, padx=10, pady=5, sticky="nw")
        self.textbox_exclude = ctk.CTkTextbox(self.frame_params, height=80)
        self.textbox_exclude.grid(row=2, column=1, padx=10, pady=5, sticky="ew")

        # Max File Age / Date Range
        ctk.CTkLabel(self.frame_params, text="Max File Age / Date Range:\n(e.g., 'Past Year' or '2024-2026')", justify="left").grid(row=3, column=0, padx=10, pady=5, sticky="nw")
        self.combo_age = ctk.CTkComboBox(self.frame_params, values=["Any", "Past Day", "Past Week", "Past Month", "Past Year"])
        self.combo_age.grid(row=3, column=1, padx=10, pady=10, sticky="ew")
        self.combo_age.set("Any")

        # Max Files to Download
        ctk.CTkLabel(self.frame_params, text="Max Files to Download:").grid(row=4, column=0, padx=10, pady=(5, 10), sticky="w")
        self.combo_max_files = ctk.CTkComboBox(self.frame_params, values=["10", "20", "50", "100", "200"])
        self.combo_max_files.grid(row=4, column=1, padx=10, pady=(5, 10), sticky="ew")
        self.combo_max_files.set("20")

        # --- 2. OUTPUT DIRECTORY FRAME ---
        self.frame_dir = ctk.CTkFrame(self, corner_radius=10)
        self.frame_dir.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        self.frame_dir.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(self.frame_dir, text="Output Directory", font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, columnspan=3, padx=10, pady=(10, 5), sticky="w")
        
        self.entry_out_dir = ctk.CTkEntry(self.frame_dir, placeholder_text="Select destination folder...")
        self.entry_out_dir.grid(row=1, column=0, columnspan=2, padx=(10, 5), pady=(5, 10), sticky="ew")
        
        self.btn_browse = ctk.CTkButton(self.frame_dir, text="Browse...", width=100, command=self._browse_directory)
        self.btn_browse.grid(row=1, column=2, padx=(5, 10), pady=(5, 10), sticky="e")

        # --- 3. REFINEMENT & OPTIONS FRAME ---
        self.frame_options = ctk.CTkFrame(self, corner_radius=10)
        self.frame_options.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        
        self.checkbox_clean = ctk.CTkCheckBox(self.frame_options, text="Enable Data Cleaning (Extract and clean text from PDFs)")
        self.checkbox_clean.grid(row=0, column=0, padx=20, pady=15, sticky="w")
        self.checkbox_clean.select() # Enabled by default

        # --- 4. CONTROLS FRAME ---
        self.frame_controls = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_controls.grid(row=3, column=0, padx=20, pady=10, sticky="ew")
        self.frame_controls.grid_columnconfigure((0, 1), weight=1)

        self.btn_start = ctk.CTkButton(self.frame_controls, text="START PROCESSING", fg_color="green", hover_color="darkgreen", height=40, font=ctk.CTkFont(weight="bold"), command=self.start_process)
        self.btn_start.grid(row=0, column=0, padx=(0, 10), pady=0, sticky="ew")

        self.btn_stop = ctk.CTkButton(self.frame_controls, text="STOP", fg_color="red", hover_color="darkred", height=40, font=ctk.CTkFont(weight="bold"), state="disabled", command=self.stop_process)
        self.btn_stop.grid(row=0, column=1, padx=(10, 0), pady=0, sticky="ew")

        # --- 5. LOG TERMINAL ---
        self.textbox_log = ctk.CTkTextbox(self, state="disabled", wrap="word", font=ctk.CTkFont(family="Consolas", size=12))
        self.textbox_log.grid(row=4, column=0, padx=20, pady=(10, 20), sticky="nsew")

    # ==============================================================================
    # UI INTERACTIONS & HELPER METHODS
    # ==============================================================================
    def _browse_directory(self):
        """Opens native OS folder selection dialog."""
        directory = ctk.filedialog.askdirectory()
        if directory:
            self.entry_out_dir.delete(0, ctk.END)
            self.entry_out_dir.insert(0, directory)

    def log_message(self, message):
        """Thread-safe way to append text to the live log terminal."""
        def update_log():
            self.textbox_log.configure(state="normal")
            self.textbox_log.insert(ctk.END, message + "\n")
            self.textbox_log.see(ctk.END) # Auto-scroll to bottom
            self.textbox_log.configure(state="disabled")
        self.after(0, update_log)

    def toggle_ui_state(self, running: bool):
        """Enables or disables UI elements based on running state."""
        state = "disabled" if running else "normal"
        self.textbox_include.configure(state=state)
        self.textbox_exclude.configure(state=state)
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
    # THREAD MANAGEMENT
    # ==============================================================================
    def start_process(self):
        """Validates inputs and starts the Producer and Consumer threads."""
        include_kw = self.textbox_include.get("1.0", "end-1c").strip()
        out_dir = self.entry_out_dir.get().strip()

        # Validate Include Keywords
        if not include_kw:
            self.log_message("[ERROR] 'Include Keywords' cannot be empty.")
            return
            
        # Validate Output Directory
        if not out_dir or not os.path.isdir(out_dir):
            self.log_message("[ERROR] Please select a valid Output Directory.")
            return
            
        # Validate Max Files
        try:
            max_files = int(self.combo_max_files.get().strip())
            if max_files <= 0:
                raise ValueError
        except ValueError:
            self.log_message("[ERROR] 'Max Files to Download' must be a positive integer.")
            return

        self.is_running = True
        self.stop_event.clear()
        self.toggle_ui_state(running=True)
        
        # Clear log
        self.textbox_log.configure(state="normal")
        self.textbox_log.delete("1.0", ctk.END)
        self.textbox_log.configure(state="disabled")

        self.log_message("=== STARTING DATASET BUILDER ===")

        # Create subfolder for cleaned data if needed
        enable_cleaning = self.checkbox_clean.get() == 1
        cleaned_dir = os.path.join(out_dir, "Cleaned_Data")
        if enable_cleaning and not os.path.exists(cleaned_dir):
            os.makedirs(cleaned_dir)
            self.log_message(f"Created directory for cleaned data: {cleaned_dir}")

        # Start Consumer Thread (Data Cleaner)
        if enable_cleaning:
            self.consumer_thread = threading.Thread(target=self._cleaner_consumer_worker, args=(cleaned_dir,), daemon=True)
            self.consumer_thread.start()

        # Start Producer Thread (Search & Download)
        self.producer_thread = threading.Thread(target=self._search_producer_worker, args=(out_dir, enable_cleaning, max_files), daemon=True)
        self.producer_thread.start()

        # Monitor thread to reset UI when done
        threading.Thread(target=self._monitor_threads, daemon=True).start()

    def stop_process(self):
        """Signals threads to stop gracefully."""
        self.log_message("[INFO] Stop requested. Waiting for current operations to finish...")
        self.stop_event.set()
        self.btn_stop.configure(state="disabled") # Prevent multiple clicks

    def _monitor_threads(self):
        """Waits for producer to finish, then signals consumer to finish, then resets UI."""
        self.producer_thread.join()
        
        if self.checkbox_clean.get() == 1:
            # Send sentinel value to Consumer to terminate
            self.download_queue.put(None)
            self.consumer_thread.join()
            
        self.is_running = False
        self.after(0, lambda: self.toggle_ui_state(running=False))
        
        if self.stop_event.is_set():
            self.log_message("=== PROCESS STOPPED BY USER ===")
        else:
            self.log_message("=== PROCESS COMPLETED SUCCESSFULLY ===")

    # ==============================================================================
    # THREAD 1: PRODUCER (Search & Download)
    # ==============================================================================
    def _search_producer_worker(self, output_dir, enable_cleaning, max_files):
        """Searches for PDFs using DuckDuckGo and downloads them."""
        # 1. Retrieve UI Inputs
        include_kw = self.textbox_include.get("1.0", "end-1c").strip()
        exclude_kw = self.textbox_exclude.get("1.0", "end-1c").strip()
        age = self.combo_age.get().strip()

        # 2. Build Base Query
        # Replace newlines with spaces for the search query
        include_clean = " ".join(include_kw.split())
        query = f"{include_clean} filetype:pdf"
        
        # 3. Add Exclusions
        if exclude_kw:
            # Split exclude keywords by comma or newline and prepend '-' to each
            excludes = [f"-{kw.strip()}" for kw in re.split(r'[,\n]', exclude_kw) if kw.strip()]
            query += " " + " ".join(excludes)

        # 4. Handle Date Ranges / Max Age
        time_param = None
        date_query_append = ""
        
        if age == "Past Day": time_param = 'd'
        elif age == "Past Week": time_param = 'w'
        elif age == "Past Month": time_param = 'm'
        elif age == "Past Year": time_param = 'y'
        elif age != "Any":
            # Smart parsing for ranges like "2024-2026"
            match = re.match(r'(\d{4})\s*-\s*(\d{4})', age)
            if match:
                start_year = int(match.group(1))
                end_year = int(match.group(2))
                # Ensure start is less than or equal to end
                if start_year <= end_year:
                    years = [str(y) for y in range(start_year, end_year + 1)]
                    # Appends (2024 OR 2025 OR 2026) to query
                    date_query_append = " (" + " OR ".join(years) + ")"
            else:
                # If they typed a specific year like "2023", just append it
                date_query_append = f" {age}"
        
        # Append date logic to query string if applicable
        if date_query_append:
            query += date_query_append

        self.log_message(f"[SEARCH] Querying DuckDuckGo: '{query}'")
        self.log_message(f"[SEARCH] Target Max Files: {max_files}")

        try:
            # Use DuckDuckGo Search API
            with DDGS() as ddgs:
                results = ddgs.text(query, timelimit=time_param, max_results=max_files)
                
                if not results:
                    self.log_message("[SEARCH] No results found for the given criteria.")
                    return

                download_count = 0
                for idx, result in enumerate(results):
                    if self.stop_event.is_set(): break
                    if download_count >= max_files: break
                    
                    url = result.get('href')
                    if not url or not url.lower().endswith('.pdf'):
                        continue # Skip non-PDFs just in case

                    self.log_message(f"[PRODUCER] Found URL: {url}")
                    
                    # Generate safe filename
                    parsed_url = urllib.parse.urlparse(url)
                    filename = os.path.basename(parsed_url.path)
                    if not filename.endswith('.pdf'):
                        filename = f"document_{idx}.pdf"
                    
                    # Clean filename to be OS safe
                    safe_filename = re.sub(r'[\\/*?:"<>|]', "", filename)
                    file_path = os.path.join(output_dir, safe_filename)

                    # Download File
                    success = self._download_file(url, file_path)
                    
                    if success:
                        download_count += 1
                        if enable_cleaning:
                            # Push to queue for the consumer
                            self.download_queue.put(file_path)

        except Exception as e:
            self.log_message(f"[ERROR] Search failed: {str(e)}")

    def _download_file(self, url, dest_path):
        """Helper method to download a file with streaming."""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        try:
            self.log_message(f"   -> Downloading: {os.path.basename(dest_path)}...")
            response = requests.get(url, headers=headers, stream=True, timeout=15)
            response.raise_for_status()
            
            with open(dest_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if self.stop_event.is_set():
                        return False # Abort download
                    if chunk:
                        f.write(chunk)
            self.log_message(f"   -> Saved: {os.path.basename(dest_path)}")
            return True
        except requests.exceptions.RequestException as e:
            self.log_message(f"   -> [FAILED] Could not download {url}. Error: {e}")
            return False

    # ==============================================================================
    # THREAD 2: CONSUMER (Data Cleaning)
    # ==============================================================================
    def _cleaner_consumer_worker(self, cleaned_dir):
        """Listens to the queue, extracts text from PDFs, cleans it, and saves as TXT."""
        while True:
            # Check queue. Block until item is available.
            try:
                # Use timeout so we can periodically check stop_event
                pdf_path = self.download_queue.get(timeout=2) 
            except queue.Empty:
                if self.stop_event.is_set():
                    break
                continue

            # Sentinel value to terminate thread
            if pdf_path is None:
                self.download_queue.task_done()
                break

            filename = os.path.basename(pdf_path)
            base_name = os.path.splitext(filename)[0]
            txt_path = os.path.join(cleaned_dir, f"{base_name}.txt")

            self.log_message(f"[CONSUMER] Cleaning data from: {filename}...")

            try:
                # Extract text using PyMuPDF
                doc = fitz.open(pdf_path)
                full_text = ""
                for page_num in range(len(doc)):
                    if self.stop_event.is_set(): break
                    page = doc.load_page(page_num)
                    full_text += page.get_text() + "\n"
                doc.close()

                if self.stop_event.is_set(): break

                # Basic Data Cleaning
                # 1. Remove excessive newlines
                clean_text = re.sub(r'\n{3,}', '\n\n', full_text)
                # 2. Strip trailing whitespace
                clean_text = clean_text.strip()

                if clean_text:
                    with open(txt_path, 'w', encoding='utf-8') as f:
                        f.write(clean_text)
                    self.log_message(f"   -> Cleaned text saved to: {os.path.basename(txt_path)}")
                else:
                    self.log_message(f"   -> [WARNING] No extractable text found in: {filename}")

            except Exception as e:
                self.log_message(f"   -> [ERROR] Failed to clean {filename}: {e}")
            
            finally:
                self.download_queue.task_done()

# ==============================================================================
# ENTRY POINT
# ==============================================================================
if __name__ == "__main__":
    # Set appearance mode and color theme for CustomTkinter
    ctk.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
    ctk.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"
    
    app = DatasetBuilderApp()
    app.mainloop()