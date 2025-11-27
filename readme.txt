# 🎙️ Voice Intelligence & Analytics Tool

An AI-powered desktop application that analyzes call recordings to extract actionable business intelligence. Built with Python, Google Gemini API, and Tkinter.

## 🚀 Features
* **Audio Ingestion:** Supports standard formats (MP3, WAV) and legacy formats (DAT) via automatic conversion.
* **AI Analysis:** Uses Google Gemini 1.5 Flash for verbatim transcription, speaker diarization, and sentiment analysis.
* **Auto-Translation:** Automatically translates non-English audio to English transcripts.
* **Interactive Dashboard:** Displays key metrics: Language, Speaker Count, Main Topic, and Sentiment.
* **RAG Q&A:** Chat with your audio file using a "Retrieval Augmented Generation" style query interface.

## 🛠️ Tech Stack
* **Language:** Python 3.10+
* **AI Model:** Google Gemini 1.5 Flash (Multimodal)
* **GUI:** Tkinter
* **Data Validation:** Pydantic
* **Audio Processing:** FFmpeg & PyDub

## ⚙️ Installation

1. **Clone the repo**
   ```bash
   git clone [https://github.com/YOUR_USERNAME/Voice-Intelligence-Tool.git](https://github.com/YOUR_USERNAME/Voice-Intelligence-Tool.git)
   cd Voice-Intelligence-Tool
