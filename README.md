# 🎙️ Meeting Verbalizer AI

A desktop application that records system audio (meetings, webinars) and uses OpenAI's Whisper to transcribe text and generate professional PDF minutes with automated topic segmentation.



## ✨ Features
* **System Audio Loopback:** Records what you hear (Teams, Zoom, Meet) without virtual cables.
* **AI Transcription:** Uses OpenAI Whisper (runs locally, 100% privacy).
* **Smart Segmentation:** Detects topic changes based on pauses and context to structure the PDF.
* **Professional PDF Report:** Generates clean, timestamped minutes.
* **Audio Backup:** Option to save the raw .wav file.

## 🚀 How to Run (No Python required)
1. Go to the [Releases Page](https://github.com/lorenzobellillo/meeting-verbalizer/releases/tag/1.0.0).
2. Download `MeetingVerbalizer_v1.0.zip`.
3. Extract the folder.
4. Run `MeetingVerbalizer.exe`.

## 🛠️ Built With
* **Python 3.12**
* **CustomTkinter** (UI)
* **OpenAI Whisper** (Speech-to-Text)
* **SoundCard** (Audio Loopback)
* **FPDF** (Report Generation)

## ⚠️ Note on Privacy
Everything runs **offline** on your CPU. No audio data is sent to the cloud.

---
*Created by [Lorenzo Bellillo]*
