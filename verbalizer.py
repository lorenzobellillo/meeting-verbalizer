import customtkinter as ctk
import soundcard as sc
import soundfile as sf
import threading
import whisper
import os
import datetime
import json
import numpy as np
import shutil
from fpdf import FPDF
from pathlib import Path

SAMPLE_RATE = 44100
TEMP_FILENAME = "temp_recording.wav"
CONFIG_FILE = os.path.join(str(Path.home()), ".meeting_recorder_config.json")

class MeetingVerbalizerFinal(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Meeting Transcription AI (Smart Segmentation)")
        self.geometry("950x750")
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        self.is_recording = False
        self.model = None
        self.config = self.load_config()
        
        self.desktop_path = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')
        self.save_folder = os.path.join(self.desktop_path, "Meeting_Recordings")
        
        if not os.path.exists(self.save_folder):
            try:
                os.makedirs(self.save_folder)
            except:
                self.save_folder = self.desktop_path

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(3, weight=1)

        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar.grid(row=0, column=0, rowspan=6, sticky="nsew")
        self.sidebar.grid_rowconfigure(6, weight=1)

        self.logo_label = ctk.CTkLabel(self.sidebar, text="Meeting\nAI Recorder", font=ctk.CTkFont(size=22, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(30, 20))

        self.lbl_info = ctk.CTkLabel(self.sidebar, text="Files saved automatically to:\nDesktop/Meeting_Recordings", 
                                     text_color="gray", font=("Arial", 12), wraplength=180)
        self.lbl_info.grid(row=1, column=0, padx=20, pady=20)

        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.grid(row=0, column=1, sticky="ew", padx=20, pady=(20, 5))
        
        ctk.CTkLabel(self.header_frame, text="Meeting Name:", font=("Arial", 14)).pack(side="left", padx=(0, 10))
        self.entry_name = ctk.CTkEntry(self.header_frame, placeholder_text="Ex: Project Kickoff", width=250)
        self.entry_name.pack(side="left", padx=(0, 20))

        self.chk_save_audio = ctk.CTkCheckBox(self.header_frame, text="Save Audio File (.wav)", font=("Arial", 12))
        self.chk_save_audio.pack(side="left")

        self.btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.btn_frame.grid(row=1, column=1, sticky="ew", padx=20, pady=10)

        self.status_indicator = ctk.CTkLabel(self.btn_frame, text="● READY", text_color="#2ecc71", font=("Arial", 16, "bold"))
        self.status_indicator.pack(side="left", pady=5)

        self.btn_stop = ctk.CTkButton(self.btn_frame, text="⏹ STOP & SAVE PDF", command=self.stop_recording, 
                                      state="disabled", fg_color="#c0392b", hover_color="#e74c3c", width=180, height=45, font=("Arial", 13, "bold"))
        self.btn_stop.pack(side="right", padx=10)

        self.btn_start = ctk.CTkButton(self.btn_frame, text="▶ START RECORDING", command=self.start_recording, 
                                       fg_color="#3498db", hover_color="#2980b9", width=180, height=45, font=("Arial", 13, "bold"))
        self.btn_start.pack(side="right", padx=10)

        ctk.CTkLabel(self, text="Live Transcription Log:", font=("Arial", 14, "bold")).grid(row=2, column=1, sticky="w", padx=20)
        
        self.transcript_box = ctk.CTkTextbox(self, font=("Segoe UI", 16)) 
        self.transcript_box.grid(row=3, column=1, sticky="nsew", padx=20, pady=(5, 20))

        self.progressbar = ctk.CTkProgressBar(self, mode="indeterminate", width=500)
        self.progressbar.grid(row=4, column=1, sticky="ew", padx=20, pady=(0, 20))
        self.progressbar.set(0)

        if self.config.get("show_mic_warning", True):
            self.after(1000, self.check_warning_popup)

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {"show_mic_warning": True}

    def save_config(self):
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(self.config, f)
        except Exception as e:
            print(f"Config save error: {e}")

    def check_warning_popup(self):
        self.popup = ctk.CTkToplevel(self)
        self.popup.title("Audio Setup")
        self.popup.geometry("500x350")
        self.popup.attributes("-topmost", True)
        
        msg = ("⚠️ HOW TO RECORD YOUR OWN VOICE\n\n"
               "This app records System Audio (what you hear).\n"
               "To include YOUR voice in the recording:\n\n"
               "1. Go to Control Panel -> Sound -> Recording.\n"
               "2. Double click your Microphone -> 'Listen' tab.\n"
               "3. Check 'Listen to this device' and Apply.\n\n"
               "(Please use headphones to prevent echo!)")
        
        label = ctk.CTkLabel(self.popup, text=msg, justify="left", wraplength=450, font=("Arial", 14))
        label.pack(pady=20, padx=20)

        self.check_var = ctk.BooleanVar(value=False)
        chk = ctk.CTkCheckBox(self.popup, text="Don't show this again", variable=self.check_var)
        chk.pack(pady=10)

        btn = ctk.CTkButton(self.popup, text="OK, Understood", command=self.close_popup, fg_color="#3498db")
        btn.pack(pady=10)

    def close_popup(self):
        if self.check_var.get():
            self.config["show_mic_warning"] = False
            self.save_config()
        self.popup.destroy()

    def start_recording(self):
        self.is_recording = True
        self.btn_start.configure(state="disabled")
        self.btn_stop.configure(state="normal")
        self.status_indicator.configure(text="● RECORDING...", text_color="#e74c3c")
        self.transcript_box.delete("0.0", "end")
        self.transcript_box.insert("0.0", "Recording started...\nWait for the meeting to end.")
        threading.Thread(target=self.record_thread).start()

    def record_thread(self):
        try:
            default_speaker = sc.default_speaker()
            with sc.get_microphone(id=str(default_speaker.name), include_loopback=True).recorder(samplerate=SAMPLE_RATE) as mic:
                self.recorded_data = []
                while self.is_recording:
                    data = mic.record(numframes=1024)
                    self.recorded_data.append(data)
        except Exception as e:
            self.status_indicator.configure(text="AUDIO DEVICE ERROR", text_color="red")
            print(f"Error: {e}")
            return

        if self.recorded_data:
            full_recording = np.concatenate(self.recorded_data)
            sf.write(TEMP_FILENAME, full_recording, SAMPLE_RATE)
            self.transcribe_audio()

    def stop_recording(self):
        self.is_recording = False
        self.btn_start.configure(state="normal")
        self.btn_stop.configure(state="disabled")
        self.status_indicator.configure(text="● PROCESSING...", text_color="#f39c12")
        self.progressbar.start()

    def transcribe_audio(self):
        threading.Thread(target=self.process_whisper).start()

    def process_whisper(self):
        try:
            if self.model is None:
                self.status_indicator.configure(text="LOADING AI MODEL...")
                self.model = whisper.load_model("base")

            self.status_indicator.configure(text="AI IS ANALYZING TOPICS...")
            
            result = self.model.transcribe(
                TEMP_FILENAME, fp16=False, beam_size=5, best_of=5, temperature=0
            )
            
            segments = result["segments"]
            full_text = result["text"]

            self.transcript_box.delete("0.0", "end")
            self.transcript_box.insert("0.0", full_text)
            
            self.save_outputs(full_text, segments)
            
            self.progressbar.stop()
            self.status_indicator.configure(text="● DONE", text_color="#2ecc71")
        except Exception as e:
            self.status_indicator.configure(text=f"ERROR: {str(e)}", text_color="red")
            self.progressbar.stop()
            print(e)

    def save_outputs(self, full_text, segments):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        meeting_name = self.entry_name.get().strip()
        if not meeting_name:
            meeting_name = f"Meeting_{timestamp}"
            
        safe_filename = "".join([c for c in meeting_name if c.isalnum() or c in (' ', '_', '-')]).rstrip()
        
        pdf_path = os.path.join(self.save_folder, f"{safe_filename}.pdf")
        
        
        self.generate_smart_pdf(meeting_name, segments, pdf_path)
        
        if self.chk_save_audio.get():
            audio_path = os.path.join(self.save_folder, f"{safe_filename}.wav")
            shutil.copy(TEMP_FILENAME, audio_path)

        try:
            os.startfile(pdf_path)
        except:
            pass

    def generate_smart_pdf(self, title, segments, filepath):
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        
        pdf.set_font("Helvetica", "B", 24)
        pdf.set_text_color(33, 33, 33)
        pdf.cell(0, 15, title, ln=True, align='L')
        
        current_date = datetime.datetime.now().strftime("%B %d, %Y")
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 8, f"Date: {current_date}", ln=True, align='L')
        
        pdf.ln(5)
        pdf.set_draw_color(200, 200, 200)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(10)

        
        grouped_topics = []
        if segments:
            current_group = {
                "start": segments[0]['start'],
                "text": segments[0]['text'].strip()
            }
            
            for i in range(1, len(segments)):
                prev_seg = segments[i-1]
                curr_seg = segments[i]
                
                
                time_gap = curr_seg['start'] - prev_seg['end']
                text_len = len(current_group["text"])
                
                if time_gap > 1.5 or text_len > 400:
                    grouped_topics.append(current_group)
                    current_group = {
                        "start": curr_seg['start'],
                        "text": curr_seg['text'].strip()
                    }
                else:
                    current_group["text"] += " " + curr_seg['text'].strip()
            
            grouped_topics.append(current_group)

        
        for topic in grouped_topics:
            start_time = str(datetime.timedelta(seconds=int(topic['start'])))
            text = topic['text']
            
            safe_text = text.encode('latin-1', 'replace').decode('latin-1')
            
            
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(52, 152, 219)
            pdf.cell(25, 6, f"[{start_time}]", 0, 0)
            
            
            pdf.set_font("Helvetica", "", 11)
            pdf.set_text_color(20, 20, 20)
            
            
            current_y = pdf.get_y()
            current_x = pdf.get_x()
            
            pdf.set_xy(35, current_y) 
            pdf.multi_cell(0, 6, safe_text)
            pdf.ln(4) 

        try:
            pdf.output(filepath)
        except Exception as e:
            print(f"Error saving PDF: {e}")

if __name__ == "__main__":
    app = MeetingVerbalizerFinal()
    app.mainloop()