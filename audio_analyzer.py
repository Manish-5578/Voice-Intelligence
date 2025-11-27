import os
import json
import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox, Toplevel
import tempfile
from pydantic import BaseModel, Field
from typing import List, Literal, Optional
from google import genai
from google.genai import types

# --- Dependency for DAT Conversion ---
try:
    from pydub import AudioSegment
except ImportError:
    AudioSegment = None


# --- 1. Enhanced Pydantic Schema (For Better Accuracy & Metadata) ---

class TranscriptLine(BaseModel):
    """Represents a single line of verbatim dialogue."""
    speaker: str = Field(description="The speaker label (e.g., 'Speaker 1').")
    text: str = Field(description="The verbatim content spoken, translated accurately to English.")


class CallReport(BaseModel):
    """The structured analysis of the call."""
    file_name: str
    original_language: str = Field(
        description="The detected language of the original audio (e.g., 'Tamil', 'English').")
    speaker_count: int = Field(description="The total number of unique speakers.")
    main_topic: str = Field(description="A short, 3-5 word title of the conversation topic.")
    overall_sentiment: Literal["Positive", "Neutral", "Negative", "Heated"]
    call_summary: str = Field(description="A concise executive summary.")
    transcript_lines: List[TranscriptLine] = Field(description="The full, word-for-word transcript.")


# --- 2. Configuration ---

GEMINI_API_KEY = "AIzaSyCJ4UuZbeUyaGjMIzmCRnuC_8AwFp2YIQ8"
MODEL = "gemini-2.5-flash"
SUPPORTED_EXTENSIONS = [('Audio Files', '*.mp3 *.wav *.flac *.m4a *.dat'), ('All Files', '*.*')]
DEFAULT_INPUT_PATH = r"D:\Projects\CI\recordings"


def convert_dat_to_mp3(dat_path: str) -> Optional[str]:
    if AudioSegment is None: return None
    temp_dir = tempfile.gettempdir()
    mp3_path = os.path.join(temp_dir, os.path.basename(dat_path).replace(".dat", "_converted.mp3"))
    try:
        audio = AudioSegment.from_file(dat_path)
        audio.export(mp3_path, format="mp3")
        return mp3_path
    except Exception:
        return None


# --- 3. Main Application ---

class VoiceIntelligenceApp:
    def __init__(self, master):
        self.master = master
        master.title("Voice Intelligence Analyst Pro")
        master.geometry("600x700")  # Compact main window

        # Data Stores
        self.audio_file_path = tk.StringVar(master, value="No file selected...")
        self.current_report = None  # To store the analyzed JSON data
        self.context_text = ""  # For the Chatbot

        # Initialize Client
        try:
            self.client = genai.Client(api_key=GEMINI_API_KEY)
        except Exception as e:
            messagebox.showerror("API Error", f"Init failed: {e}")
            self.client = None

        self.create_widgets()

    def create_widgets(self):
        # --- HEADER ---
        tk.Label(self.master, text="Voice Intelligence Analyst", font=("Helvetica", 16, "bold"), pady=10).pack()

        # --- SECTION 1: File & Analyze ---
        control_frame = tk.LabelFrame(self.master, text="1. Input", font=("Arial", 10, "bold"), padx=10, pady=10)
        control_frame.pack(fill="x", padx=10, pady=5)

        tk.Button(control_frame, text="Browse", command=self.browse_audio_file).pack(side=tk.LEFT)
        tk.Entry(control_frame, textvariable=self.audio_file_path, state='readonly', width=40).pack(side=tk.LEFT,
                                                                                                    padx=5)
        tk.Button(control_frame, text="ANALYZE", command=self.run_analysis, bg="#4CAF50", fg="white",
                  font=("Arial", 9, "bold")).pack(side=tk.LEFT)

        # --- SECTION 2: Basic Details Dashboard (Hidden initially) ---
        self.info_frame = tk.LabelFrame(self.master, text="2. Basic Details", font=("Arial", 10, "bold"), padx=10,
                                        pady=10)
        self.info_frame.pack(fill="x", padx=10, pady=5)

        # Grid layout for details
        self.lbl_lang = tk.Label(self.info_frame, text="Language: -", font=("Arial", 11))
        self.lbl_lang.grid(row=0, column=0, sticky="w", padx=10)

        self.lbl_speakers = tk.Label(self.info_frame, text="Speakers: -", font=("Arial", 11))
        self.lbl_speakers.grid(row=0, column=1, sticky="w", padx=10)

        self.lbl_topic = tk.Label(self.info_frame, text="Topic: -", font=("Arial", 11, "bold"), fg="#333")
        self.lbl_topic.grid(row=1, column=0, columnspan=2, sticky="w", padx=10, pady=5)

        # --- SECTION 3: Transcript Button ---
        btn_frame = tk.Frame(self.master, pady=5)
        btn_frame.pack(fill="x", padx=10)

        self.btn_view_transcript = tk.Button(btn_frame, text="📄 VIEW FULL TRANSCRIPT",
                                             command=self.open_transcript_window, state="disabled", width=30)
        self.btn_view_transcript.pack()

        # --- SECTION 4: Q&A Interface ---
        qa_frame = tk.LabelFrame(self.master, text="3. Ask Query", font=("Arial", 10, "bold"), padx=10, pady=10)
        qa_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.query_entry = tk.Entry(qa_frame, font=("Arial", 11), state="disabled")
        self.query_entry.pack(fill="x", pady=5)
        self.query_entry.bind('<Return>', lambda event: self.ask_question())

        self.btn_ask = tk.Button(qa_frame, text="Ask AI", command=self.ask_question, bg="#2196F3", fg="white",
                                 state="disabled")
        self.btn_ask.pack(anchor="e")

        # Chat Display
        self.chat_display = scrolledtext.ScrolledText(qa_frame, height=10, state="disabled", font=("Courier New", 10))
        self.chat_display.pack(fill="both", expand=True, pady=5)
        self.chat_display.tag_config("USER", foreground="blue", font=("Arial", 10, "bold"))
        self.chat_display.tag_config("AI", foreground="green", font=("Arial", 10))

    # --- Actions ---

    def browse_audio_file(self):
        file = filedialog.askopenfilename(initialdir=DEFAULT_INPUT_PATH, filetypes=SUPPORTED_EXTENSIONS)
        if file:
            self.audio_file_path.set(file)

    def run_analysis(self):
        if not self.client: return
        file_path = self.audio_file_path.get()
        if not os.path.exists(file_path):
            messagebox.showwarning("Error", "Select a valid file first.")
            return

        # UI Feedback
        self.btn_ask.config(text="Analyzing...", state="disabled")
        self.master.update()

        # DAT Conversion
        if file_path.lower().endswith('.dat'):
            file_path = convert_dat_to_mp3(file_path)

        try:
            # 1. Upload
            uploaded_file = self.client.files.upload(file=file_path)

            # 2. Strict Prompt for Accuracy
            prompt = (
                "You are a professional transcriber. Task: \n"
                "1. Identify the language. \n"
                "2. Transcribe the audio VERBATIM (word-for-word). Do not summarize the transcript lines. \n"
                "3. If strictly needed, translate the transcript to English accurately. \n"
                "4. Extract speaker count and main topic. \n"
                "Output strictly in JSON."
            )

            response = self.client.models.generate_content(
                model=MODEL,
                contents=[uploaded_file, prompt],
                config=types.GenerateContentConfig(response_mime_type="application/json", response_schema=CallReport)
            )

            # 3. Parse Data
            data = json.loads(response.text)
            self.current_report = CallReport(**data)

            # 4. Update Dashboard (Basic Details)
            self.lbl_lang.config(text=f"Language: {self.current_report.original_language}")
            self.lbl_speakers.config(text=f"Speakers: {self.current_report.speaker_count}")
            self.lbl_topic.config(text=f"Topic: {self.current_report.main_topic}")

            # 5. Prepare Context for Q&A
            self.context_text = f"Summary: {self.current_report.call_summary}\nTranscript:\n"
            for line in self.current_report.transcript_lines:
                self.context_text += f"{line.speaker}: {line.text}\n"

            # 6. Enable UI
            self.btn_view_transcript.config(state="normal", bg="#FF9800", fg="white")
            self.query_entry.config(state="normal")
            self.btn_ask.config(state="normal", text="Ask AI")

            # Cleanup
            self.client.files.delete(name=uploaded_file.name)
            messagebox.showinfo("Success", "Analysis Complete. Check Basic Details and Ask Questions.")

        except Exception as e:
            messagebox.showerror("Analysis Error", str(e))
            self.btn_ask.config(text="Ask AI")

    def open_transcript_window(self):
        """Opens a separate window to show the full transcript."""
        if not self.current_report: return

        win = Toplevel(self.master)
        win.title("Full Transcript")
        win.geometry("600x600")

        txt = scrolledtext.ScrolledText(win, wrap=tk.WORD, font=("Courier New", 11), padx=10, pady=10)
        txt.pack(fill="both", expand=True)

        # Tags for readability
        txt.tag_config("SPK", foreground="darkred", font=("Courier New", 11, "bold"))

        for line in self.current_report.transcript_lines:
            txt.insert(tk.END, f"[{line.speaker}]: ", "SPK")
            txt.insert(tk.END, f"{line.text}\n\n")

        txt.config(state="disabled")

    def ask_question(self):
        question = self.query_entry.get().strip()
        if not question or not self.context_text: return

        # UI Update
        self.chat_display.config(state="normal")
        self.chat_display.insert(tk.END, f"You: {question}\n", "USER")
        self.chat_display.see(tk.END)
        self.query_entry.delete(0, tk.END)
        self.chat_display.config(state="disabled")
        self.master.update()

        try:
            prompt = (
                f"Answer based ONLY on this transcript context.\n"
                f"{self.context_text}\n"
                f"Question: {question}"
            )
            response = self.client.models.generate_content(model=MODEL, contents=prompt)

            self.chat_display.config(state="normal")
            self.chat_display.insert(tk.END, f"AI: {response.text}\n\n", "AI")
            self.chat_display.see(tk.END)
            self.chat_display.config(state="disabled")

        except Exception as e:
            messagebox.showerror("Q&A Error", str(e))


if __name__ == "__main__":
    root = tk.Tk()
    app = VoiceIntelligenceApp(root)
    root.mainloop()