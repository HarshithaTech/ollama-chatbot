import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
import ollama
import threading
import queue
import time
import os
import speech_recognition as sr
from history_manager import HistoryManager
from rag_engine import RAGEngine

# Appearance Settings
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

# Theme Palette
BG_MAIN = "#0A1128"
BG_SIDEBAR = "#061A40"
BUBBLE_ASSISTANT = "#132244"
BUBBLE_USER = "#00509D"
ACCENT_PRIMARY = "#247BA0"

class ScrollableChatFrame(ctk.CTkScrollableFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.columnconfigure(0, weight=1)
        self.messages = []

    def add_message(self, role, content):
        bg_color = BUBBLE_ASSISTANT if role == "assistant" else BUBBLE_USER
        text_color = "#ffffff"
        align = "w" if role == "assistant" else "e"
        
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.grid(padx=10, pady=5, sticky=align)
        
        label = ctk.CTkLabel(
            frame, 
            text=content, 
            wraplength=400, 
            fg_color=bg_color, 
            text_color=text_color,
            corner_radius=12,
            padx=15,
            pady=10,
            justify="left"
        )
        label.pack()
        self.messages.append(frame)
        self._parent_canvas.rowconfigure(len(self.messages), weight=1)

class OllamaGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- Data & Settings ---
        self.history_mgr = HistoryManager()
        self.rag_engine = RAGEngine()
        self.session_id = self.history_mgr.generate_session_id()
        self.messages = []
        self.chat_queue = queue.Queue()
        
        # --- UI Layout ---
        self.title("Ollama Desktop AI")
        self.geometry("1000x700")
        self.configure(fg_color=BG_MAIN)

        # Configure grid
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # 1. Sidebar
        self.sidebar = ctk.CTkFrame(self, width=250, corner_radius=0, fg_color=BG_SIDEBAR)
        self.sidebar.grid(row=0, column=0, rowspan=4, sticky="nsew")
        self.sidebar.grid_rowconfigure(4, weight=1)

        self.logo_label = ctk.CTkLabel(self.sidebar, text="🤖 Ollama GUI", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        self.new_chat_btn = ctk.CTkButton(self.sidebar, text="✨ New Chat", command=self.new_chat)
        self.new_chat_btn.grid(row=1, column=0, padx=20, pady=10)

        self.model_label = ctk.CTkLabel(self.sidebar, text="🧠 Model Select:", anchor="w")
        self.model_label.grid(row=2, column=0, padx=20, pady=(10, 0))
        
        try:
            models = [m['name'] for m in ollama.list()['models']]
        except:
            models = ["llama3.2"]
        
        self.model_option = ctk.CTkOptionMenu(self.sidebar, values=models, fg_color=ACCENT_PRIMARY, button_color=ACCENT_PRIMARY)
        self.model_option.grid(row=3, column=0, padx=20, pady=10)

        # History Area (inside sidebar)
        self.history_frame = ctk.CTkScrollableFrame(self.sidebar, label_text="Recent History")
        self.history_frame.grid(row=4, column=0, padx=10, pady=10, sticky="nsew")
        self.refresh_history_ui()

        # RAG Area (inside sidebar bottom)
        self.rag_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.rag_frame.grid(row=5, column=0, padx=10, pady=10, sticky="sew")
        
        self.rag_switch = ctk.CTkSwitch(self.rag_frame, text="Enable RAG")
        self.rag_switch.pack(pady=5)
        
        self.upload_btn = ctk.CTkButton(self.rag_frame, text="📥 Upload Docs", command=self.upload_docs, fg_color="gray")
        self.upload_btn.pack(fill="x", pady=2)
        
        self.clear_kb_btn = ctk.CTkButton(self.rag_frame, text="🗑️ Clear KB", command=self.clear_kb, fg_color="#8b1a1a")
        self.clear_kb_btn.pack(fill="x", pady=2)

        # 2. Main Chat Area
        self.chat_display = ScrollableChatFrame(self, corner_radius=0, fg_color=BG_MAIN)
        self.chat_display.grid(row=0, column=1, padx=20, pady=(20, 0), sticky="nsew")

        # 3. Input Area
        self.input_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.input_frame.grid(row=1, column=1, padx=20, pady=20, sticky="ew")
        self.input_frame.grid_columnconfigure(0, weight=1)

        self.entry = ctk.CTkEntry(self.input_frame, placeholder_text="Type your message here...", height=45)
        self.entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.entry.bind("<Return>", lambda e: self.send_message())

        self.send_btn = ctk.CTkButton(self.input_frame, text="🚀", width=60, height=45, command=self.send_message, fg_color=ACCENT_PRIMARY)
        self.send_btn.grid(row=0, column=1, padx=(0, 5))

        self.voice_btn = ctk.CTkButton(self.input_frame, text="🎤", width=60, height=45, command=self.start_voice_thread, fg_color="#444444")
        self.voice_btn.grid(row=0, column=2)

        # --- Periodic Check for Messages ---
        self.check_queue()

    def start_voice_thread(self):
        self.voice_btn.configure(text="🔴", fg_color="red")
        threading.Thread(target=self.record_voice, daemon=True).start()

    def record_voice(self):
        recognizer = sr.Recognizer()
        # Increased energy threshold to reduce silences
        recognizer.energy_threshold = 300 
        recognizer.dynamic_energy_threshold = True
        
        with sr.Microphone() as source:
            try:
                # Better noise adjustment
                recognizer.adjust_for_ambient_noise(source, duration=1.0)
                # Visual change to show it's active
                self.after(0, lambda: self.voice_btn.configure(text="👂", fg_color="red"))
                
                audio = recognizer.listen(source, timeout=10, phrase_time_limit=15)
                
                # Visual change to show it's processing
                self.after(0, lambda: self.voice_btn.configure(text="⏳", fg_color="orange"))
                
                text = recognizer.recognize_google(audio)
                self.after(0, lambda: self.entry.insert(tk.END, f" {text}"))
            except sr.WaitTimeoutError:
                pass
            except sr.UnknownValueError:
                # Silently fail if nothing understood, or just notify subtly
                pass
            except sr.RequestError:
                self.after(0, lambda: messagebox.showerror("Voice Error", "Could not request results from Google Speech Recognition service"))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Voice Error", str(e)))
            finally:
                self.after(0, lambda: self.voice_btn.configure(text="🎤", fg_color="#444444"))

    def new_chat(self):
        self.session_id = self.history_mgr.generate_session_id()
        self.messages = []
        for widget in self.chat_display.winfo_children():
            widget.destroy()
        self.chat_display.messages = []
        self.refresh_history_ui()

    def refresh_history_ui(self):
        for widget in self.history_frame.winfo_children():
            widget.destroy()
        
        try:
            sessions = self.history_mgr.list_sessions()
        except:
            sessions = []
            
        for s in sessions:
            s_id = s['id']
            btn = ctk.CTkButton(
                self.history_frame, 
                text=s_id[:15], 
                fg_color="transparent", 
                text_color="gray",
                anchor="w",
                command=lambda id=s_id: self.load_session(id)
            )
            btn.pack(fill="x", padx=5, pady=2)

    def load_session(self, s_id):
        self.session_id = s_id
        self.messages = self.history_mgr.load_session(s_id)
        # Clear UI
        for widget in self.chat_display.winfo_children():
            widget.destroy()
        self.chat_display.messages = []
        # Redraw messages
        for msg in self.messages:
            self.chat_display.add_message(msg["role"], msg["content"])

    def upload_docs(self):
        files = filedialog.askopenfilenames(title="Select Documents", filetypes=[("PDF/TXT", "*.pdf *.txt")])
        if files:
            self.upload_btn.configure(text="Processing...", state="disabled")
            threading.Thread(target=self._process_docs, args=(files,), daemon=True).start()

    def _process_docs(self, files):
        try:
            num = self.rag_engine.add_documents(files)
            self.after(0, lambda: messagebox.showinfo("Done", f"Added {num} chunks to Knowledge Base!"))
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Error", str(e)))
        finally:
            self.after(0, lambda: self.upload_btn.configure(text="📥 Upload Docs", state="normal"))

    def clear_kb(self):
        if messagebox.askyesno("Confirm", "Clear everything in Knowledge Base?"):
            self.rag_engine.clear_database()
            messagebox.showinfo("Cleared", "Knowledge Base is now empty.")

    def send_message(self):
        prompt = self.entry.get().strip()
        if not prompt: return
        
        self.entry.delete(0, tk.END)
        self.chat_display.add_message("user", prompt)
        self.messages.append({"role": "user", "content": prompt})
        self.history_mgr.save_session(self.session_id, self.messages)
        
        # Start AI thread
        threading.Thread(target=self.ollama_thread, args=(prompt,), daemon=True).start()

    def ollama_thread(self, prompt):
        try:
            model = self.model_option.get()
            
            # RAG Context
            context_prefix = ""
            if self.rag_switch.get() and self.rag_engine.has_knowledge():
                context = self.rag_engine.query(prompt)
                if context:
                    context_str = "\n".join(context)
                    context_prefix = f"Context from Knowledge Base:\n{context_str}\n\nUser Question: "

            # Prepare messages
            ollama_msgs = []
            for m in self.messages[:-1]:
                ollama_msgs.append(m)
            
            last_msg = self.messages[-1].copy()
            if context_prefix:
                last_msg["content"] = context_prefix + last_msg["content"]
            ollama_msgs.append(last_msg)

            full_response = ""
            # Note: For simple GUI we'll update the full response at once or chunk by chunk
            # To keep it simple and stable, let's gather and then push
            for chunk in ollama.chat(model=model, messages=ollama_msgs, stream=True):
                full_response += chunk['message']['content']
                # Stream partials to queue? (Optional: for smoother UI)
                # self.chat_queue.put(("partial", full_response))
            
            self.chat_queue.put(("final", full_response))
        except Exception as e:
            self.chat_queue.put(("error", str(e)))

    def check_queue(self):
        try:
            while True:
                msg_type, content = self.chat_queue.get_nowait()
                if msg_type == "final":
                    self.chat_display.add_message("assistant", content)
                    self.messages.append({"role": "assistant", "content": content})
                    self.history_mgr.save_session(self.session_id, self.messages)
                elif msg_type == "error":
                    messagebox.showerror("Ollama Error", content)
        except queue.Empty:
            pass
        finally:
            self.after(100, self.check_queue)

if __name__ == "__main__":
    app = OllamaGUI()
    app.mainloop()
