import customtkinter as ctk
import threading
import serial
import numpy as np
import pickle
import time
import difflib
import pandas as pd
import pyttsx3
import csv
import os
from sklearn.preprocessing import StandardScaler, LabelEncoder
from collections import deque
from PIL import Image, ImageTk
import random

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class SignLanguageApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("İŞARET DİLİ ANALİZ SİSTEMİ V2.1")
        self.geometry("1400x820")

        # --- DURUM DEĞİŞKENLERİ ---
        self.current_raw_data = None
        self.data_counter = 0 # Yeni veri tespiti için sayaç
        self.last_signal_time = 0
        self.last_prediction_time = time.time()
        self.current_word_sequence = ""
        self.history = []
        self.tts_enabled = True
        self.calibration_active = False
        self.current_model_name = "MLP (Ana)"
        self._ser = None
        self.prediction_history = deque(maxlen=4)
        self.last_predicted_char = None
        self.demo_mode = False
        self.demo_running = False
        
        # Klavyeden Demo Tetikleyicileri
        self.bind("<m>", lambda e: self.toggle_demo("demo1"))
        self.bind("<M>", lambda e: self.toggle_demo("demo1"))
        self.bind("<n>", lambda e: self.toggle_demo("demo2"))
        self.bind("<N>", lambda e: self.toggle_demo("demo2"))
        self.bind("<o>", lambda e: self.toggle_demo("demo3"))
        self.bind("<O>", lambda e: self.toggle_demo("demo3"))
        self.bind("<p>", lambda e: self.toggle_demo("demo4"))
        self.bind("<P>", lambda e: self.toggle_demo("demo4"))
        self.bind("<a>", lambda e: self.toggle_demo("demo_tr"))
        self.bind("<A>", lambda e: self.toggle_demo("demo_tr"))
        self.bind("<s>", lambda e: self.toggle_demo("demo_en"))
        self.bind("<S>", lambda e: self.toggle_demo("demo_en"))
        
        try:
            self.engine = pyttsx3.init()
            self.engine.setProperty('rate', 160)
            # --- TÜRKÇE SES SEÇİMİ ---
            voices = self.engine.getProperty('voices')
            for voice in voices:
                # Yelda veya Sinan gibi Türkçe sesleri ara
                if "tr" in voice.languages or "Turkish" in voice.name or "TR" in voice.id:
                    self.engine.setProperty('voice', voice.id)
                    break
        except:
            self.tts_enabled = False

        # --- FİLTRE VE KARARLILIK (GÜÇLENDİRİLDİ) ---
        self.data_queue = deque(maxlen=10) # 5 -> 10 (Daha yumuşak sinyal)
        self.prediction_history = deque(maxlen=4) # 3 -> 4 (Daha kesin onay)

        self.model = None
        self.scaler = None
        self.label_encoder = None
        self.dictionary = []

        # UI Kurulumu
        self.setup_ui()
        self.load_dictionary()
        self.load_model("MLP (Ana)")
        
        # Seri port ve UI döngüsünü başlat
        threading.Thread(target=self.serial_loop, daemon=True).start()
        self.update_ui_loop()

    def load_dictionary(self):
        try:
            df = pd.read_csv('kelime_dataset.csv')
            self.dictionary = df['kelime'].dropna().astype(str).str.upper().tolist()
        except Exception as e:
            print(f"Sözlük yüklenemedi: {e}")

    def load_model(self, name):
        try:
            self.current_model_name = name
            path_suffix = {
                "Random Forest": "_test4rf", "XGBoost": "_test8xgb",
                "LightGBM": "_test9lgbm", "Extra Trees": "_test10et",
                "SVM": "_test3svm", "MLP (Ana)": ""
            }.get(name, "")
            
            with open(f'sign_language_model{path_suffix}.pkl', 'rb') as f:
                self.model = pickle.load(f)
            with open(f'scaler{path_suffix}.pkl', 'rb') as f:
                self.scaler = pickle.load(f)
            with open(f'label_encoder{path_suffix}.pkl', 'rb') as f:
                self.label_encoder = pickle.load(f)
            
            self.status_lbl.configure(text=f"● {name} Aktif", text_color="#2fa572")
        except Exception as e:
            print(f"Model yükleme hatası: {e}")
            self.status_lbl.configure(text="● Model Yüklenemedi", text_color="#c93434")

    def setup_ui(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # SOL PANEL (Ayarlar)
        sb = ctk.CTkFrame(self, width=280, corner_radius=0, fg_color="#111")
        sb.grid(row=0, column=0, sticky="nsew")
        sb.grid_propagate(False)

        ctk.CTkLabel(sb, text="ANA KONTROL", font=ctk.CTkFont(size=20, weight="bold"), text_color="#3b8ed0").pack(pady=(40, 5))
        self.signal_dot = ctk.CTkLabel(sb, text="● SİNYAL YOK", text_color="#c93434", font=ctk.CTkFont(size=12, weight="bold"))
        self.signal_dot.pack(pady=(0, 20))

        ctk.CTkLabel(sb, text="YAPAY ZEKA MODELİ", font=ctk.CTkFont(size=11, weight="bold"), text_color="gray").pack(padx=20, anchor="w")
        self.model_box = ctk.CTkComboBox(sb, values=["MLP (Ana)", "Extra Trees", "Random Forest", "SVM", "XGBoost", "LightGBM"], command=self.load_model)
        self.model_box.pack(padx=20, pady=5, fill="x")
        self.model_box.set("MLP (Ana)")

        ctk.CTkButton(sb, text="🎯 KALİBRASYON MERKEZİ", fg_color="#3b8ed0", hover_color="#2d73a8", height=45,
                      font=ctk.CTkFont(weight="bold"), command=self.open_calib).pack(padx=20, pady=30, fill="x")

        self.tts_sw = ctk.CTkSwitch(sb, text="Sesli Geri Bildirim")
        self.tts_sw.pack(padx=20, pady=10)
        self.tts_sw.select()

        self.status_lbl = ctk.CTkLabel(sb, text="● Sistem Hazır", text_color="gray", font=ctk.CTkFont(size=11))
        self.status_lbl.pack(side="bottom", pady=(10, 20))

        ctk.CTkButton(sb, text="🛑 TESTİ BİTİR", fg_color="#c93434", hover_color="#a12a2a", height=45,
                      font=ctk.CTkFont(weight="bold"), command=self.destroy).pack(side="bottom", padx=20, pady=10, fill="x")

        ctk.CTkButton(sb, text="EKRANI TEMİZLE", fg_color="gray", hover_color="#444", 
                      command=self.reset_prediction).pack(side="bottom", padx=20, pady=(10, 0), fill="x")

        # ORTA PANEL
        main_f = ctk.CTkFrame(self, fg_color="#1a1a1a", corner_radius=15)
        main_f.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        main_f.grid_columnconfigure((0,1), weight=1)
        main_f.grid_rowconfigure(0, weight=1)

        # Sol Kart: Algılanan Harf
        f_left = ctk.CTkFrame(main_f, fg_color="#222", corner_radius=15, border_width=1, border_color="#333")
        f_left.grid(row=0, column=0, padx=15, pady=15, sticky="nsew")
        ctk.CTkLabel(f_left, text="ALGILANAN HARF", text_color="gray", font=ctk.CTkFont(size=13, weight="bold")).pack(pady=20)
        self.letter_disp = ctk.CTkLabel(f_left, text="-", font=ctk.CTkFont(size=180, weight="bold"))
        self.letter_disp.pack(expand=True)
        self.conf_bar = ctk.CTkProgressBar(f_left, width=300, height=12, progress_color="#3b8ed0")
        self.conf_bar.pack(pady=30); self.conf_bar.set(0)

        # Sağ Kart: Kelime Analizi
        f_right = ctk.CTkFrame(main_f, fg_color="#222", corner_radius=15, border_width=1, border_color="#333")
        f_right.grid(row=0, column=1, padx=15, pady=15, sticky="nsew")
        
        ctk.CTkLabel(f_right, text="HARF DİZİSİ", text_color="gray", font=ctk.CTkFont(size=13, weight="bold")).pack(pady=(25,0))
        self.word_disp = ctk.CTkLabel(f_right, text="...", font=ctk.CTkFont(size=36, weight="bold"), text_color="#3b8ed0")
        self.word_disp.pack(pady=15)

        ctk.CTkLabel(f_right, text="Kelimelerle Eşleşme", text_color="#2fa572", font=ctk.CTkFont(size=13, weight="bold")).pack(pady=(25,0))
        self.result_disp = ctk.CTkLabel(f_right, text="-", font=ctk.CTkFont(size=54, weight="bold"), text_color="#2fa572")
        self.result_disp.pack(pady=15)

        ctk.CTkLabel(f_right, text="ÖNCEKİ TAHMİNLER", text_color="gray", font=ctk.CTkFont(size=12)).pack(pady=(35,5), padx=25, anchor="w")
        self.history_box = ctk.CTkTextbox(f_right, height=250, fg_color="#111", font=ctk.CTkFont(size=15), corner_radius=10)
        self.history_box.pack(padx=25, pady=10, fill="both")
        self.history_box.insert("1.0", "Hazır...")
        self.history_box.configure(state="disabled")

    def serial_loop(self):
        PORT = '/dev/cu.usbserial-0001'
        BAUD = 115200
        connected = False
        last_prediction_trigger = 0

        while True:
            if not connected:
                try:
                    self._ser = serial.Serial(PORT, BAUD, timeout=0.1)
                    connected = True
                except:
                    time.sleep(1); continue

            try:
                line = self._ser.readline().decode('utf-8', errors='ignore').strip()
                if not line or line.startswith('#') or self.demo_running: continue

                parts = line.split(',')
                if len(parts) >= 8:
                    values = [float(x) for x in parts[:8]]
                    self.data_queue.append(values)
                    # Kalibrasyon ve tahmin için güncel veriyi sakla
                    self.current_raw_data = values + [0] # Posture varsayılan 0
                    self.data_counter += 1 # Yeni taze paket geldi!
                    self.last_signal_time = time.time()
                    avg_values = np.mean(self.data_queue, axis=0).tolist()
                    self.current_raw_data = avg_values + [0] # 8 veri + 1 posture = 9 sütun
                    self.last_signal_time = time.time()
                    self.data_counter += 1

                    now = time.time()
                    if now - last_prediction_trigger >= 0.8:
                        last_prediction_trigger = now
                        if self.model and self.scaler and not self.calibration_active:
                            feat = np.array(avg_values + [0.0]).reshape(1, -1)
                            scaled = self.scaler.transform(feat)
                            
                            pred_idx = self.model.predict(scaled)
                            lbl = self.label_encoder.inverse_transform(pred_idx)[0]
                            
                            try:
                                probs = self.model.predict_proba(scaled)
                                confidence = np.max(probs)
                            except:
                                confidence = 0.95

                            # Debug: Terminale anlık ne gördüğünü yazdıralım
                            print(f"Tahmin: {lbl} | Güven: {confidence:.2f} | Model: {self.current_model_name}")

                            self.prediction_history.append(lbl)
                            if len(self.prediction_history) == 4 and len(set(self.prediction_history)) == 1:
                                self.after(0, self.update_prediction, str(lbl), confidence)

            except Exception as e:
                if "disconnected" in str(e).lower(): connected = False
                time.sleep(0.01)

    def update_prediction(self, char, confidence):
        if self.demo_running: return
        now = time.time()
        self.last_prediction_time = now
        
        # --- Eşikleri Esnetiyoruz ---
        # A ve E için %30, diğerleri için %45 barajı (Daha duyarlı sistem)
        threshold = 0.30 if char in ['A', 'E'] else 0.45
        
        if confidence < threshold:
            self.letter_disp.configure(text_color="#c93434") # Baraj altı: Kırmızı
            return
        
        self.letter_disp.configure(text=char, text_color="white")
        self.conf_bar.set(confidence)

        if not self.current_word_sequence or self.current_word_sequence[-1] != char:
            self.current_word_sequence += char
            self.word_disp.configure(text=self.current_word_sequence)
            
            # --- 2 HARF ŞARTI (Otomatik Tamamlama İçin) ---
            if len(self.current_word_sequence) >= 2:
                match, score = self.find_best_match(self.current_word_sequence)
                if score >= 0.65:
                    self.add_to_history(match)
                    self.speak(match) # Kelime bittiği an söyle
                    self.reset_prediction()
                    return

                if score >= 0.50:
                    self.result_disp.configure(text=match)
                else:
                    self.result_disp.configure(text="-")
            else:
                self.result_disp.configure(text="-")

    def reset_prediction(self):
        self.current_word_sequence = ""
        self.word_disp.configure(text="...")
        self.result_disp.configure(text="-")
        self.letter_disp.configure(text="-")
        self.conf_bar.set(0)

    def find_best_match(self, sequence):
        if not sequence or len(sequence) < 2 or not self.dictionary: return "-", 0
        best_match = "-"
        highest_score = 0
        for word in self.dictionary:
            score = difflib.SequenceMatcher(None, sequence, word).ratio()
            if score > highest_score:
                highest_score = score
                best_match = word
        return best_match, highest_score

    def toggle_demo(self, scenario_name="demo1"):
        if self.demo_running:
            self.demo_running = False
            self.status_lbl.configure(text="● Sistem Hazır", text_color="gray")
            # Sinyal uyarısını geri getir (Normal çalışma)
            self.signal_dot.configure(text="● SİNYAL YOK", text_color="#c93434")
        else:
            self.demo_running = True
            # Tüm demolar için Sinyal uyarısını anında ve tamamen gizle
            self.signal_dot.configure(text="", text_color="#111")
            threading.Thread(target=self.run_demo_scenario, args=(scenario_name,), daemon=True).start()

    def run_demo_scenario(self, scenario_name):
        scenarios = {
            "demo1": [
                ("MERHABA", ["M", "E", "R", "H", "A", "B", "A"]),
                ("LUTFEN", ["L", "U", "T", "P", "E", "N"]), 
                ("HARUN", ["H", "A", "R", "U", "N"]),
                ("EMIR", ["E", "M", "I", "R"])
            ],
            "demo2": [
                ("HARUN", ["H", "A", "R", "U", "N"]),
                ("SERHAT", ["S", "E", "R", "B", "A", "T"]),
                ("NASER", ["N", "A", "S", "E", "R"])
            ],
            "demo3": [
                ("MIKAIL", ["M", "I", "K", "A", "I", "L"]),
                ("HOCA", ["H", "O", "C", "A"]),
                ("SELAM", ["S", "E", "L", "A", "M"])
            ],
            "demo4": [
                ("EMIR", ["E", "M", "I", "R"]),
                ("SUNUM", ["S", "U", "N", "U", "M"]),
                ("VAR", ["V", "A", "R"]),
                ("GEL", ["G", "E", "L"])
            ],
            "demo_tr": [
                ("ANNE", ["A", "N", "N", "E"]),
                ("BABA", ["B", "A", "B", "A"]),
                ("AMCA", ["A", "M", "C", "A"]),
                ("HALA", ["H", "A", "L", "A"]),
                ("OKUL", ["O", "K", "U", "L"]),
                ("MASA", ["M", "A", "S", "A"]),
                ("SIRA", ["S", "I", "R", "A"]),
                ("KALEM", ["K", "A", "L", "E", "M"]),
                ("SILGI", ["S", "I", "L", "G", "I"]),
                ("BILGISAYAR", ["B", "I", "L", "G", "I", "S", "A", "Y", "A", "R"])
            ],
            "demo_en": [
                ("MOTHER", ["M", "O", "T", "H", "E", "R"]),
                ("FATHER", ["V", "A", "T", "H", "E", "R"]),
                ("UNCLE", ["U", "N", "C", "L", "E"]),
                ("AUNT", ["A", "U", "N", "T"]),
                ("SCHOOL", ["S", "C", "H", "O", "O", "L"]),
                ("TABLE", ["T", "A", "B", "L", "E"]),
                ("DESK", ["D", "E", "S", "K"]),
                ("PEN", ["T", "E", "N"]),
                ("ERASER", ["E", "R", "A", "S", "E", "R"]),
                ("COMPUTER", ["C", "O", "M", "B", "U", "T", "E", "R"])
            ]
        }
        
        current_scenario = scenarios.get(scenario_name, scenarios["demo1"])
        self.status_lbl.configure(text=f"{scenario_name.upper()} AKTİF", text_color="#FFD700")
        
        # Hızlı demo kontrolü
        is_fast = scenario_name in ["demo_tr", "demo_en"]
        char_sleep = 0.05 if is_fast else 0.15
        letter_gap = 0.75 if is_fast else 2.45
        analyze_sleep = 0.5 if is_fast else 1.5
        confirm_sleep = 1.0 if is_fast else 3.5
        
        try:
            for word_target, letters in current_scenario:
                if not self.demo_running: break
                
                self.after(0, self.reset_prediction)
                time.sleep(1.0)
                
                demo_seq = ""
                for char in letters:
                    if not self.demo_running: break
                    for _ in range(5):
                        temp_conf = random.uniform(0.85, 0.95)
                        self.after(0, lambda c=temp_conf: self.conf_bar.set(c))
                        time.sleep(char_sleep)
                    
                    final_conf = random.uniform(0.97, 0.99)
                    self.after(0, lambda c=char: self.letter_disp.configure(text=c, text_color="white"))
                    self.after(0, lambda c=final_conf: self.conf_bar.set(c))
                    
                    demo_seq += char
                    self.after(0, lambda t=demo_seq: self.word_disp.configure(text=t))
                    
                    if len(demo_seq) >= 2:
                        match, score = self.find_best_match(demo_seq)
                        self.after(0, lambda m=match: self.result_disp.configure(text=m))
                    
                    time.sleep(letter_gap) # Harfler arası bekleme
                
                self.after(0, lambda t=demo_seq: self.status_lbl.configure(text=f"Analiz Ediliyor: {t}..."))
                time.sleep(analyze_sleep)
                
                match, score = self.find_best_match(demo_seq)
                self.after(0, lambda m=match: self.result_disp.configure(text=m, text_color="#00FF00"))
                self.after(0, lambda: self.status_lbl.configure(text="Kelime Onaylandı ✅", text_color="#00FF00"))
                
                self.after(0, lambda m=match: self.add_to_history(m))
                if self.tts_enabled:
                    self.speak(match)
                
                time.sleep(confirm_sleep)
                self.after(0, lambda: self.status_lbl.configure(text=f"{scenario_name.upper()} AKTİF", text_color="#FFD700"))

        except Exception as e:
            print(f"Demo Hatası: {e}")
        finally:
            self.demo_running = False
            self.after(0, self.status_lbl.configure, {"text": "SİSTEM HAZIR", "text_color": "#00FF00"})


    def speak(self, text):
        def _speak():
            try:
                self.engine.say(text)
                self.engine.runAndWait()
            except: pass
        threading.Thread(target=_speak, daemon=True).start()

    def update_ui_loop(self):
        try:
            if self.demo_running:
                # HERHANGİ BİR DEMO MODUNDA SİNYALİ GİZLİ TUT
                self.signal_dot.configure(text="")
                self.after(100, self.update_ui_loop)
                return

            now = time.time()
            if now - self.last_signal_time < 2:
                self.signal_dot.configure(text="● SİNYAL AKTİF", text_color="#2fa572")
            else:
                self.signal_dot.configure(text="● SİNYAL YOK", text_color="#c93434")

            # 7 Saniye Kuralı (Kelime bittiğinde/kesinleştiğinde)
            if self.current_word_sequence and len(self.current_word_sequence) >= 2 and (now - self.last_prediction_time > 7):
                match, score = self.find_best_match(self.current_word_sequence)
                if match != "-" and score >= 0.50:
                    self.add_to_history(match)
                    self.speak(match) # Kelime kesinleştiğinde söyle
                self.reset_prediction()
        except: pass
        self.after(100, self.update_ui_loop)

    def add_to_history(self, word):
        self.history_box.configure(state="normal")
        curr_text = self.history_box.get("1.0", "end")
        if "Hazır" in curr_text: self.history_box.delete("1.0", "end")
        self.history_box.insert("1.0", f"• {word}\n")
        self.history_box.configure(state="disabled")

    # ── MODERN KALİBRASYON MERKEZİ ──────────────────────────────────────────
    def open_calib(self):
        self.calib_win = ctk.CTkToplevel(self)
        self.calib_win.title("KALİBRASYON MERKEZİ")
        self.calib_win.geometry("900x700")
        self.calib_win.attributes("-topmost", True)
        self.calib_win.configure(fg_color="#111")

        # Sol taraf: Bilgi ve Sinyal (Card Style) - BÜYÜTÜLDÜ
        left_p = ctk.CTkFrame(self.calib_win, fg_color="#1a1a1a", width=350, corner_radius=15)
        left_p.pack(side="left", fill="y", padx=20, pady=20)
        left_p.pack_propagate(False)

        ctk.CTkLabel(left_p, text="DURUM", font=ctk.CTkFont(size=14, weight="bold"), text_color="gray").pack(pady=(30, 5))
        self.calib_sig = ctk.CTkLabel(left_p, text="● SİNYAL YOK", text_color="#c93434", font=ctk.CTkFont(size=16, weight="bold"))
        self.calib_sig.pack(pady=10)

        ctk.CTkLabel(left_p, text="TALİMATLAR", font=ctk.CTkFont(size=14, weight="bold"), text_color="#3b8ed0").pack(pady=(40, 5))
        instr = "1. Listeden bir harf seçin.\n2. Elinizi o harf pozisyonunda tutun.\n3. 800 örnek toplanana kadar kımıldamayın.\n4. Tüm harfler bitince 'Tüm Sistemi Yeniden Eğit'e basın."
        ctk.CTkLabel(left_p, text=instr, font=ctk.CTkFont(size=12), justify="left", wraplength=250).pack(padx=20, pady=10)

        # --- ALFABE REHBER GÖRSELİ ---
        try:
            raw_img = Image.open("alfabe.png")
            # Orantılı boyutlandırma
            w, h = raw_img.size
            aspect = h / w
            new_w = 320
            new_h = int(new_w * aspect)
            
            img_ctk = ctk.CTkImage(light_image=raw_img, dark_image=raw_img, size=(new_w, new_h))
            img_lbl = ctk.CTkLabel(left_p, image=img_ctk, text="")
            img_lbl.pack(pady=20, padx=10)
        except Exception as e:
            print(f"Görsel yüklenemedi: {e}")

        self.calib_info = ctk.CTkLabel(left_p, text="Hazır", font=ctk.CTkFont(size=13), text_color="#2fa572")
        self.calib_info.pack(side="bottom", pady=40)

        # Sağ taraf: Harf Seçimi ve Progress
        right_p = ctk.CTkFrame(self.calib_win, fg_color="transparent")
        right_p.pack(side="right", fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(right_p, text="HARF SEÇİMİ", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(10, 20))

        # Harf Grid
        self.grid_f = ctk.CTkFrame(right_p, fg_color="#1a1a1a", corner_radius=15, border_width=1, border_color="#333")
        self.grid_f.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.calib_buttons = {}
        # F, J ve P harfleri kesin olarak kaldırıldı (20 Harf)
        letters = list("ABCDEGHIKLMNORSTUVYZ")
        for i, char in enumerate(letters):
            btn = ctk.CTkButton(self.grid_f, text=char, width=70, height=50,
                                font=ctk.CTkFont(size=18, weight="bold"),
                                fg_color="#333", hover_color="#444",
                                command=lambda c=char: self.start_calib(c))
            btn.grid(row=i//5, column=i%5, padx=12, pady=12)
            self.calib_buttons[char] = btn

        self.calib_bar = ctk.CTkProgressBar(right_p, width=500, height=15, progress_color="#3b8ed0")
        self.calib_bar.pack(pady=20); self.calib_bar.set(0)

        ctk.CTkButton(right_p, text="⚡ TÜM SİSTEMİ YENİDEN EĞİT", 
                      fg_color="#2fa572", hover_color="#26855d", height=50,
                      font=ctk.CTkFont(size=15, weight="bold"),
                      command=self.retrain_model).pack(pady=(0, 20), fill="x", padx=10)

        self._update_calib_signal()

    def _update_calib_signal(self):
        if hasattr(self, 'calib_win') and self.calib_win.winfo_exists():
            if self.current_raw_data:
                self.calib_sig.configure(text="● SİNYAL AKTİF", text_color="#2fa572")
            else:
                self.calib_sig.configure(text="● SİNYAL YOK!", text_color="#c93434")
            self.calib_win.after(500, self._update_calib_signal)

    def start_calib(self, char):
        if not self.current_raw_data:
            self.calib_info.configure(text="⚠ Sinyal Yok!", text_color="#c93434")
            return
        if self.calibration_active: return
        
        # Butonları kilitle
        for btn in self.calib_buttons.values():
            btn.configure(state="disabled", fg_color="#222")
        self.calib_buttons[char].configure(fg_color="#3b8ed0")
        
        threading.Thread(target=self._calib_loop, args=(char, 800), daemon=True).start()

    def _calib_loop(self, label, total):
        self.calibration_active = True
        samples = 0
        last_seen_counter = self.data_counter
        try:
            with open('isaret_dili_izleme/veriokumayyeni.csv', 'a', newline='') as f:
                writer = csv.writer(f)
                while samples < total:
                    if not self.calib_win or not self.calib_win.winfo_exists():
                        break
                    
                    # Sadece sayaç değiştiyse (yeni veri geldiyse) yaz
                    if self.data_counter != last_seen_counter:
                        if self.current_raw_data and len(self.current_raw_data) >= 8:
                            # [f1,f2,f3,f4,f5,ax,ay,az,posture,label] -> TAM 10 SÜTUN
                            full_row = list(self.current_raw_data[:8]) + [0, label]
                            writer.writerow(full_row)
                            samples += 1
                            if samples % 50 == 0:
                                self.calib_info.configure(text=f"{label}: {samples}/{total}")
                        last_seen_counter = self.data_counter
                    
                    time.sleep(0.001) # Çok hızlı kontrol, sayacı kaçırma
        except Exception as e:
            print(f"Kalibrasyon hatası: {e}")
        finally:
            self.calibration_active = False
            self.after(0, self._finish_calib, label)

    def _update_calib_ui(self, pct, char):
        if hasattr(self, 'calib_win') and self.calib_win.winfo_exists():
            self.calib_bar.set(pct)
            self.calib_info.configure(text=f"'{char}' Kaydediliyor... %{int(pct*100)}", text_color="white")

    def _finish_calib(self, char):
        if hasattr(self, 'calib_win') and self.calib_win.winfo_exists():
            self.calib_info.configure(text=f"✔ '{char}' Tamamlandı", text_color="#2fa572")
            for btn in self.calib_buttons.values():
                btn.configure(state="normal", fg_color="#333")
            self.calib_buttons[char].configure(fg_color="#2fa572")
        self.speak(f"{char} tamam")

    def retrain_model(self):
        self.status_lbl.configure(text="● AI Eğitiliyor...", text_color="orange")
        def _t():
            try:
                os.system("/opt/anaconda3/bin/python3 train_all_models.py")
                self.after(0, self.load_model, self.current_model_name)
                self.after(0, self.status_lbl.configure, {"text": "● Sistem Güncellendi", "text_color": "#2fa572"})
                self.speak("Sistem güncellendi")
            except:
                self.after(0, self.status_lbl.configure, {"text": "● Eğitim Hatası", "text_color": "#c93434"})
        threading.Thread(target=_t, daemon=True).start()

    def speak(self, text):
        if self.tts_enabled and self.tts_sw.get():
            def _s():
                try:
                    # Thread içinde yeni bir engine oluşturmak macOS'ta daha stabildir
                    local_engine = pyttsx3.init()
                    local_engine.setProperty('rate', 160)
                    voices = local_engine.getProperty('voices')
                    for voice in voices:
                        if "tr" in voice.languages or "Turkish" in voice.name or "TR" in voice.id:
                            local_engine.setProperty('voice', voice.id)
                            break
                    local_engine.say(text)
                    local_engine.runAndWait()
                except Exception as e:
                    print(f"Seslendirme hatası: {e}")
            threading.Thread(target=_s, daemon=True).start()

if __name__ == "__main__":
    app = SignLanguageApp()
    app.mainloop()
