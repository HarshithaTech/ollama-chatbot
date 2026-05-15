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

    def add_message(self, role, content, is_final=True):
        bg_color = BUBBLE_ASSISTANT if role == "assistant" else BUBBLE_USER
        text_color = "#ffffff"
        align = "w" if role == "assistant" else "e"
        
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.grid(padx=10, pady=5, sticky=align)
        
        if is_final:
            self._render_content(frame, role, content, bg_color, text_color)
        else:
            label = ctk.CTkLabel(frame, text=content, wraplength=400, fg_color=bg_color, text_color=text_color, corner_radius=12, padx=15, pady=10, justify="left")
            label.pack(side="left")
            frame._stream_label = label
            frame._full_text = content
            
        if role == "assistant":
            tts_btn = ctk.CTkButton(frame, text="🔊", width=30, height=30, fg_color="transparent", hover_color="#333333")
            tts_btn.pack(side="left", padx=(5, 0), anchor="s")
            tts_btn.configure(command=lambda b=tts_btn, f=frame: self.winfo_toplevel().toggle_tts(b, getattr(f, "_full_text", "")))
            frame._tts_btn = tts_btn

        self.messages.append(frame)
        self._parent_canvas.rowconfigure(len(self.messages), weight=1)
        return frame

    def update_stream(self, frame, content):
        frame._full_text = content
        if hasattr(frame, '_stream_label'):
            frame._stream_label.configure(text=content)

    def finalize_stream(self, frame, role, content):
        frame._full_text = content
        bg_color = BUBBLE_ASSISTANT if role == "assistant" else BUBBLE_USER
        text_color = "#ffffff"
        
        if hasattr(frame, '_stream_label'):
            frame._stream_label.destroy()
            delattr(frame, '_stream_label')
            
        self._render_content(frame, role, content, bg_color, text_color)

    def _render_content(self, frame, role, content, bg_color, text_color):
        frame._full_text = content
        parts = content.split("```")
        
        content_frame = ctk.CTkFrame(frame, fg_color="transparent")
        
        tts_btn = getattr(frame, "_tts_btn", None)
        if tts_btn: tts_btn.pack_forget()
        
        content_frame.pack(side="left", fill="both", expand=True)
        if tts_btn: tts_btn.pack(side="left", padx=(5, 0), anchor="s")
        
        if len(parts) == 1:
            lbl = ctk.CTkLabel(content_frame, text=content, wraplength=400, fg_color=bg_color, text_color=text_color, corner_radius=12, padx=15, pady=10, justify="left")
            lbl.pack(fill="x")
            return
            
        import pygments
        from pygments.lexers import get_lexer_by_name, guess_lexer
        
        for i, part in enumerate(parts):
            if i % 2 == 0:
                text = part.strip('\n')
                if text:
                    lbl = ctk.CTkLabel(content_frame, text=text, wraplength=400, fg_color=bg_color, text_color=text_color, corner_radius=12, padx=15, pady=10, justify="left")
                    lbl.pack(pady=(0, 5), fill="x")
            else:
                lines = part.split("\n", 1)
                lang = lines[0].strip() if len(lines) > 0 else ""
                code = lines[1] if len(lines) > 1 else ""
                
                textbox = ctk.CTkTextbox(content_frame, fg_color="#1E1E1E", text_color="#F8F8F2", font=("Consolas", 13), height=min(400, max(40, len(code.split('\n')) * 22)), width=450)
                textbox.pack(pady=5, fill="x")
                
                try:
                    lexer = get_lexer_by_name(lang, stripall=True) if lang else guess_lexer(code)
                except:
                    lexer = get_lexer_by_name("text")
                
                tokens = pygments.lex(code, lexer)
                tk_text = textbox._textbox
                tk_text.tag_config("Token.Keyword", foreground="#F92672")
                tk_text.tag_config("Token.Name.Builtin", foreground="#66D9EF")
                tk_text.tag_config("Token.Name.Function", foreground="#A6E22E")
                tk_text.tag_config("Token.Name.Class", foreground="#A6E22E")
                tk_text.tag_config("Token.String", foreground="#E6DB74")
                tk_text.tag_config("Token.Comment", foreground="#75715E")
                tk_text.tag_config("Token.Operator", foreground="#F92672")
                tk_text.tag_config("Token.Literal.Number", foreground="#AE81FF")
                
                for ttype, val in tokens:
                    tag_name = str(ttype)
                    if tag_name.startswith("Token.Keyword"): tag_name = "Token.Keyword"
                    elif tag_name.startswith("Token.String"): tag_name = "Token.String"
                    elif tag_name.startswith("Token.Comment"): tag_name = "Token.Comment"
                    elif tag_name.startswith("Token.Name.Builtin"): tag_name = "Token.Name.Builtin"
                    elif tag_name.startswith("Token.Name.Function"): tag_name = "Token.Name.Function"
                    elif tag_name.startswith("Token.Name.Class"): tag_name = "Token.Name.Class"
                    elif tag_name.startswith("Token.Operator"): tag_name = "Token.Operator"
                    elif tag_name.startswith("Token.Literal.Number"): tag_name = "Token.Literal.Number"
                    tk_text.insert("end", val, tag_name)
                    
                textbox.configure(state="disabled")

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
        self.sidebar.grid_rowconfigure(5, weight=1)

        self.logo_label = ctk.CTkLabel(self.sidebar, text="🤖 Ollama GUI", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        self.new_chat_btn = ctk.CTkButton(self.sidebar, text="✨ New Chat", command=self.new_chat)
        self.new_chat_btn.grid(row=1, column=0, padx=20, pady=10)

        self.model_label = ctk.CTkLabel(self.sidebar, text="🧠 Model Select:", anchor="w")
        self.model_label.grid(row=2, column=0, padx=20, pady=(10, 0))
        
        self.model_mapping = {
            "⚡ Fast Mode (Mistral)": "mistral",
            "🧠 Smart Mode (Llama 3.2)": "llama3.2",
            "📄 Document QA (Llama 3.2 + RAG)": "llama3.2",
            "💻 Coding Mode (Llama 3.2)": "llama3.2"
        }
        
        self.model_option = ctk.CTkOptionMenu(
            self.sidebar, 
            values=list(self.model_mapping.keys()), 
            fg_color=ACCENT_PRIMARY, 
            button_color=ACCENT_PRIMARY,
            command=self.on_model_change
        )
        self.model_option.grid(row=3, column=0, padx=20, pady=10)

        # History Area (inside sidebar)
        self.history_label = ctk.CTkLabel(self.sidebar, text="Recents", font=ctk.CTkFont(size=14, weight="bold"), anchor="w")
        self.history_label.grid(row=4, column=0, padx=20, pady=(15, 5), sticky="w")
        
        self.history_frame = ctk.CTkScrollableFrame(self.sidebar, fg_color="transparent")
        self.history_frame.grid(row=5, column=0, padx=10, pady=(0, 10), sticky="nsew")
        self.refresh_history_ui()

        # RAG Area (inside sidebar bottom)
        self.rag_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.rag_frame.grid(row=6, column=0, padx=10, pady=10, sticky="sew")
        
        self.rag_switch = ctk.CTkSwitch(self.rag_frame, text="Enable RAG")
        self.rag_switch.pack(pady=5)
        
        self.upload_btn = ctk.CTkButton(self.rag_frame, text="📥 Upload Docs", command=self.upload_docs, fg_color="gray")
        self.upload_btn.pack(fill="x", pady=2)
        
        self.view_kb_btn = ctk.CTkButton(self.rag_frame, text="📄 View KB Files", command=self.view_kb_files, fg_color="#334155")
        self.view_kb_btn.pack(fill="x", pady=2)
        
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
        # Reset to defaults
        recognizer.energy_threshold = 300
        recognizer.dynamic_energy_threshold = True
        
        with sr.Microphone() as source:
            try:
                # Visual change to show it's calibrating
                self.after(0, lambda: self.voice_btn.configure(text="⚙️", fg_color="orange"))
                recognizer.adjust_for_ambient_noise(source, duration=1.0)
                
                # Visual change to show it's ready and listening
                self.after(0, lambda: self.voice_btn.configure(text="👂", fg_color="red"))
                
                audio = recognizer.listen(source, timeout=10, phrase_time_limit=15)
                
                # Visual change to show it's processing
                self.after(0, lambda: self.voice_btn.configure(text="⏳", fg_color="orange"))
                
                text = recognizer.recognize_google(audio)
                self.after(0, lambda: self.entry.insert(tk.END, f" {text}"))
            except sr.WaitTimeoutError:
                self.after(0, lambda: messagebox.showwarning("Voice Warning", "No speech detected (Timeout)"))
            except sr.UnknownValueError:
                self.after(0, lambda: messagebox.showwarning("Voice Warning", "Could not understand audio"))
            except sr.RequestError:
                self.after(0, lambda: messagebox.showerror("Voice Error", "Could not request results from Google Speech Recognition service"))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Voice Error", str(e)))
            finally:
                self.after(0, lambda: self.voice_btn.configure(text="🎤", fg_color="#444444"))

    def on_model_change(self, selected_mode):
        if "Document QA" in selected_mode:
            self.rag_switch.select()

    def new_chat(self):
        self.session_id = self.history_mgr.generate_session_id()
        self.messages = []
        for frame in self.chat_display.messages:
            frame.destroy()
        self.chat_display.messages = []
        self.current_response_frame = None
        self.current_response_text = ""
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
            display_text = s_id.split(" - ", 1)[1] if " - " in s_id else s_id
            btn = ctk.CTkButton(
                self.history_frame, 
                text=display_text[:30], 
                fg_color="transparent", 
                text_color="white",
                hover_color="#1E293B",
                anchor="w",
                font=ctk.CTkFont(size=13),
                corner_radius=8,
                command=lambda id=s_id: self.load_session(id)
            )
            btn.pack(fill="x", padx=5, pady=2)

    def load_session(self, s_id):
        self.session_id = s_id
        self.messages = self.history_mgr.load_session(s_id)
        # Clear UI
        for frame in self.chat_display.messages:
            frame.destroy()
        self.chat_display.messages = []
        self.current_response_frame = None
        self.current_response_text = ""
        # Redraw messages
        for msg in self.messages:
            self.chat_display.add_message(msg["role"], msg["content"], is_final=True)

    def view_kb_files(self):
        files_dict = self.rag_engine.get_uploaded_files()
        
        top = ctk.CTkToplevel(self)
        top.title("KB Files")
        top.geometry("500x400")
        top.attributes("-topmost", True)
        
        lbl = ctk.CTkLabel(top, text="Files currently in Knowledge Base:", font=ctk.CTkFont(weight="bold"))
        lbl.pack(pady=10)
        
        if not files_dict:
            ctk.CTkLabel(top, text="No files found.").pack(pady=20)
        else:
            scroll = ctk.CTkScrollableFrame(top)
            scroll.pack(fill="both", expand=True, padx=10, pady=10)
            
            def _delete_file(basename, source_path, frame):
                if messagebox.askyesno("Confirm Delete", f"Are you sure you want to remove '{basename}' from the Knowledge Base?", parent=top):
                    if self.rag_engine.delete_file(source_path):
                        frame.destroy()
                        if not scroll.winfo_children():
                            top.destroy()
                            
            for basename, source_path in files_dict.items():
                item_frame = ctk.CTkFrame(scroll, fg_color="transparent")
                item_frame.pack(fill="x", pady=2)
                
                name_lbl = ctk.CTkLabel(item_frame, text=basename, anchor="w")
                name_lbl.pack(side="left", fill="x", expand=True)
                
                del_btn = ctk.CTkButton(item_frame, text="❌", width=30, height=30, fg_color="transparent", hover_color="#8b1a1a", text_color="red", command=lambda b=basename, s=source_path, f=item_frame: _delete_file(b, s, f))
                del_btn.pack(side="right", padx=5)

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
        self.chat_display.add_message("user", prompt, is_final=True)
        self.messages.append({"role": "user", "content": prompt})
        self.history_mgr.save_session(self.session_id, self.messages)
        
        # Start AI thread
        threading.Thread(target=self.ollama_thread, args=(prompt, self.session_id), daemon=True).start()

    def ollama_thread(self, prompt, current_session_id):
        try:
            mode_name = self.model_option.get()
            model = self.model_mapping.get(mode_name, "llama3.2")
            
            # RAG Context
            context_prefix = ""
            if self.rag_switch.get() and self.rag_engine.has_knowledge():
                context = self.rag_engine.query(prompt)
                if context:
                    context_str = "\n".join(context)
                    context_prefix = f"Context from Knowledge Base:\n{context_str}\n\nIMPORTANT: Answer the User Question based strictly on the Context above. If the context does not contain the answer or is completely irrelevant to the question, ignore the context completely and answer from your general knowledge.\n\nUser Question: "

            # Prepare messages
            ollama_msgs = []
            for m in self.messages[:-1]:
                ollama_msgs.append(m)
            
            last_msg = self.messages[-1].copy()
            if context_prefix:
                last_msg["content"] = context_prefix + last_msg["content"]
            ollama_msgs.append(last_msg)

            full_response = ""
            self.chat_queue.put(("start", "", current_session_id))
            
            for chunk in ollama.chat(model=model, messages=ollama_msgs, stream=True):
                chunk_text = chunk['message']['content']
                full_response += chunk_text
                self.chat_queue.put(("chunk", chunk_text, current_session_id))
            
            self.chat_queue.put(("final", full_response, current_session_id))
        except Exception as e:
            self.chat_queue.put(("error", str(e), current_session_id))

    def check_queue(self):
        try:
            while True:
                msg_type, content, msg_session_id = self.chat_queue.get_nowait()
                
                # Ignore messages from older chat sessions
                if msg_session_id != self.session_id:
                    continue
                    
                if msg_type == "start":
                    self.current_response_frame = self.chat_display.add_message("assistant", "", is_final=False)
                    self.current_response_text = ""
                elif msg_type == "chunk":
                    self.current_response_text += content
                    if getattr(self, "current_response_frame", None) and self.current_response_frame.winfo_exists():
                        self.chat_display.update_stream(self.current_response_frame, self.current_response_text)
                elif msg_type == "final":
                    if getattr(self, "current_response_frame", None) and self.current_response_frame.winfo_exists():
                        self.chat_display.finalize_stream(self.current_response_frame, "assistant", self.current_response_text)
                        self.messages.append({"role": "assistant", "content": self.current_response_text})
                        self.history_mgr.save_session(self.session_id, self.messages)
                        self.current_response_frame = None
                        if len(self.messages) == 2:
                            self.auto_title_session()
                elif msg_type == "error":
                    messagebox.showerror("Ollama Error", content)
        except queue.Empty:
            pass
        finally:
            self.after(100, self.check_queue)

    def auto_title_session(self):
        def _generate_title():
            try:
                mode_name = self.model_option.get()
                model = self.model_mapping.get(mode_name, "llama3.2")
                prompt = "Generate a short 3-5 word title for this chat based on the conversation so far. Return ONLY the title string, no quotes or extra text."
                msgs = self.messages + [{"role": "user", "content": prompt}]
                response = ollama.chat(model=model, messages=msgs)
                title = response['message']['content'].strip(' "\'')
                
                valid_chars = "-_.() abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
                safe_title = ''.join(c for c in title if c in valid_chars)[:40]
                
                if safe_title:
                    new_id = f"{self.session_id} - {safe_title}"
                    self.history_mgr.rename_session(self.session_id, new_id)
                    self.session_id = new_id
                    self.after(0, self.refresh_history_ui)
            except Exception as e:
                print(f"Auto-title error: {e}")
                
        threading.Thread(target=_generate_title, daemon=True).start()

    def toggle_tts(self, btn, text):
        if hasattr(self, 'current_tts_process') and self.current_tts_process.poll() is None:
            try:
                self.current_tts_process.terminate()
            except:
                pass
            btn.configure(text="🔊")
        else:
            if not text.strip(): return
            btn.configure(text="⏹️")
            import subprocess
            import tempfile
            
            with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8", suffix=".txt") as f:
                f.write(text)
                temp_path = f.name
            
            script = f"""
import pyttsx3
import sys
import os

try:
    with open(r'{temp_path}', 'r', encoding='utf-8') as f:
        text = f.read()
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()
finally:
    try:
        os.remove(r'{temp_path}')
    except:
        pass
"""
            self.current_tts_process = subprocess.Popen(["python", "-c", script])
            
            def _wait_for_process():
                self.current_tts_process.wait()
                try:
                    self.after(0, lambda: btn.configure(text="🔊"))
                except:
                    pass
            threading.Thread(target=_wait_for_process, daemon=True).start()

if __name__ == "__main__":
    app = OllamaGUI()
    app.mainloop()
