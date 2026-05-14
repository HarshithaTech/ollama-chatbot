# Ollama Desktop GUI

A privacy-first, fully local desktop chat application that brings the power of Large Language Models (LLMs) directly to your Windows desktop using Ollama. Built with Python and CustomTkinter, this application features a modern, responsive UI and advanced capabilities like RAG (Retrieval-Augmented Generation), Voice Input, and Text-to-Speech.

## 🌟 Key Features

### 1. Fully Local AI & Privacy
- **Ollama Integration:** Runs models locally on your machine without sending your data to the cloud.
- **Smart Model Presets:** Choose from purpose-built AI modes to fit your workflow:
  - ⚡ **Fast Mode** (`mistral`): Quick and lightweight responses.
  - 🧠 **Smart Mode** (`llama3.2`): Advanced reasoning and logic.
  - 📄 **Document QA** (`llama3.2` + RAG): Automatically toggles Knowledge Base retrieval to answer questions from your documents.
  - 💻 **Coding Mode** (`codellama`): Optimized specifically for code generation and debugging.

### 2. Retrieval-Augmented Generation (RAG) Knowledge Base
- **Upload Documents:** Easily upload `.pdf` and `.txt` files directly into the AI's knowledge base.
- **Context-Aware Responses:** The AI uses ChromaDB and LangChain to fetch relevant chunks from your documents to answer questions accurately.
- **Hallucination Mitigation:** Strict system prompting ensures the AI relies on its general knowledge if your uploaded documents are irrelevant to the question.
- **Knowledge Base Manager:** View all uploaded files in a dedicated window and delete individual files or clear the entire database.

### 3. Voice Input & Speech Recognition
- **Microphone Integration:** Speak your prompts directly using `speech_recognition`.
- **Smart Calibration:** Automatically calibrates for ambient noise and provides visual indicators (⚙️ calibrating, 👂 listening, ⏳ processing).
- **Error Handling:** Robust timeout and background noise handling prevents the app from freezing while listening.

### 4. Text-to-Speech (TTS)
- **On-Demand Audio:** Click the 🔊 speaker button on any AI response to have it read out loud using your system's native voice engine (`pyttsx3`).
- **Interruptible:** Instantly stop the speech mid-sentence by clicking the stop button (⏹️).

### 5. Advanced UI/UX
- **CustomTkinter Aesthetics:** Modern dark-mode UI with sleek, borderless elements and responsive layouts.
- **Markdown & Syntax Highlighting:** AI responses are parsed for Markdown code blocks. Code is rendered in a dedicated terminal-style box with full `pygments` syntax highlighting for maximum readability.
- **Auto-Titling History:** Chat sessions are automatically summarized into a clean, 3-5 word human-readable title (e.g., "Python Setup Issue") by a background AI thread, replacing clunky timestamps.
- **Real-time Streaming:** AI responses stream into the UI character-by-character for a fast, "typewriter" feel without freezing the main application.

## 🛠️ Architecture & Technologies Used

- **GUI Framework:** `customtkinter` (Modern Tkinter wrapper)
- **AI Backend:** `ollama-python` (Local LLM inference)
- **Vector Database:** `chromadb` (Local storage for document embeddings)
- **RAG Orchestration:** `langchain`, `langchain-community`, `langchain-chroma`
- **Voice Recognition:** `SpeechRecognition` (Google Web Speech API)
- **Text-to-Speech:** `pyttsx3` (Offline native TTS engine via isolated subprocess)
- **Syntax Highlighting:** `pygments` (Tokenizing and rendering Python/JS/JSON code blocks)

## 📂 Project Structure

- **`gui_app.py`**: The main entry point. Handles the UI layout, threading, chat queue management, markdown rendering, and TTS subprocesses.
- **`rag_engine.py`**: Manages the ChromaDB vector store, document splitting (`RecursiveCharacterTextSplitter`), and embedding generation.
- **`history_manager.py`**: Handles creating, loading, renaming, and deleting local JSON files to persist chat history across application restarts.
- **`chat_history/`**: Directory where JSON chat session logs are saved.
- **`chroma_db/`**: Directory where the vector embeddings for your uploaded documents are stored.

## 🚀 How to Run

1. Ensure Ollama is running in the background (`ollama serve`).
2. Install the necessary Python packages:
   ```bash
   pip install customtkinter ollama langchain langchain-community langchain-chroma speechrecognition pyttsx3 pygments markdown
   ```
3. Run the application:
   ```bash
   python gui_app.py
   ```
