# app.py
import threading
import customtkinter as ctk

from agent import CyberRoninAgent, create_agent
from intent_parser import parse_intent
from safety import requires_confirmation, format_confirmation_prompt
from tool_executor import execute_tool
from summarizer import summarize_result, fallback_summarize

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class CyberRoninApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Cyber-Ronin // Defensive Security Agent")
        self.geometry("1100x750")
        self.minsize(900, 600)

        self.agent = create_agent(llm_provider="mock")

        self.pending_tool_name = None
        self.pending_arguments = None

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_sidebar()
        self._build_main_console()

    def _build_sidebar(self):
        sidebar = ctk.CTkFrame(self, width=240, corner_radius=0, fg_color="#0d1117")
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)

        brand = ctk.CTkLabel(
            sidebar, 
            text="CYBER-RONIN", 
            font=ctk.CTkFont(family="Consolas", size=18, weight="bold"),
            text_color="#00f0ff"
        )
        brand.pack(padx=20, pady=(25, 5), anchor="w")

        subtitle = ctk.CTkLabel(
            sidebar, 
            text="Defensive Agent Console", 
            font=ctk.CTkFont(size=12),
            text_color="#8b949e"
        )
        subtitle.pack(padx=20, pady=(0, 20), anchor="w")

        actions_label = ctk.CTkLabel(
            sidebar, 
            text="QUICK ACTIONS", 
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#6e7681"
        )
        actions_label.pack(padx=20, pady=(10, 5), anchor="w")

        quick_cmds = [
            ("⚡ System Health", "show system health"),
            ("🔍 Scan Localhost", "scan 127.0.0.1 for open ports"),
            ("🐍 List Python", "list processes named python"),
            ("🛡️ Auth Log Check", "check for recent failed logins"),
        ]

        for label, cmd in quick_cmds:
            btn = ctk.CTkButton(
                sidebar,
                text=label,
                anchor="w",
                fg_color="#161b22",
                hover_color="#21262d",
                text_color="#c9d1d9",
                font=ctk.CTkFont(size=13),
                command=lambda c=cmd: self.set_prompt(c)
            )
            btn.pack(padx=15, pady=4, fill="x")

        status_box = ctk.CTkFrame(sidebar, fg_color="#161b22", corner_radius=6)
        status_box.pack(side="bottom", padx=15, pady=20, fill="x")

        status_lbl = ctk.CTkLabel(
            status_box, 
            text="● ENGINE ACTIVE", 
            text_color="#3fb950",
            font=ctk.CTkFont(family="Consolas", size=11, weight="bold")
        )
        status_lbl.pack(padx=10, pady=8)

    def _build_main_console(self):
        main = ctk.CTkFrame(self, fg_color="#0a0d14", corner_radius=0)
        main.grid(row=0, column=1, sticky="nsew")
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(0, weight=1)
        main.grid_rowconfigure(1, weight=0)
        main.grid_rowconfigure(2, weight=0)

        # Output Terminal Area
        self.terminal = ctk.CTkTextbox(
            main,
            fg_color="#0d1117",
            text_color="#c9d1d9",
            font=ctk.CTkFont(family="Consolas", size=13),
            wrap="word",
            corner_radius=8,
            border_width=1,
            border_color="#30363d"
        )
        self.terminal.grid(row=0, column=0, sticky="nsew", padx=20, pady=(20, 10))
        self.terminal.insert("end", "[Cyber-Ronin Desktop Console Initialized]\nEnter intent or select a quick action to begin.\n\n")
        self.terminal.configure(state="disabled")

        # Confirmation Bar Container
        self.safety_frame = ctk.CTkFrame(main, fg_color="#2b200b", border_color="#d29922", border_width=2, corner_radius=8)

        self.safety_label = ctk.CTkLabel(
            self.safety_frame,
            text="⚠️ SENSITIVE ACTION REQUIRES CONFIRMATION",
            text_color="#e3b341",
            font=ctk.CTkFont(family="Consolas", size=12, weight="bold")
        )
        self.safety_label.pack(side="left", padx=15, pady=12)

        self.btn_reject = ctk.CTkButton(
            self.safety_frame, text="REJECT (N)", fg_color="#da3633", hover_color="#b62324", text_color="#ffffff",
            font=ctk.CTkFont(family="Consolas", size=12, weight="bold"), width=110, height=34,
            command=lambda: self.resolve_safety(False)
        )
        self.btn_reject.pack(side="right", padx=(5, 15), pady=8)

        self.btn_approve = ctk.CTkButton(
            self.safety_frame, text="APPROVE (Y)", fg_color="#238636", hover_color="#2ea043", text_color="#ffffff",
            font=ctk.CTkFont(family="Consolas", size=12, weight="bold"), width=110, height=34,
            command=lambda: self.resolve_safety(True)
        )
        self.btn_approve.pack(side="right", padx=5, pady=8)

        # Input Area
        input_container = ctk.CTkFrame(main, fg_color="transparent")
        input_container.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 20))
        input_container.grid_columnconfigure(0, weight=1)

        self.prompt_entry = ctk.CTkEntry(
            input_container,
            placeholder_text="Enter command or query (e.g., 'show system health')...",
            font=ctk.CTkFont(family="Consolas", size=13),
            fg_color="#161b22",
            border_color="#30363d",
            text_color="#ffffff",
            height=44
        )
        self.prompt_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.prompt_entry.bind("<Return>", lambda e: self.send_prompt())

        self.send_btn = ctk.CTkButton(
            input_container,
            text="EXECUTE",
            width=100,
            height=44,
            fg_color="#1f6feb",
            hover_color="#388bfd",
            font=ctk.CTkFont(family="Consolas", size=12, weight="bold"),
            command=self.send_prompt
        )
        self.send_btn.grid(row=0, column=1)

    def set_prompt(self, command: str):
        self.prompt_entry.delete(0, "end")
        self.prompt_entry.insert(0, command)
        self.send_prompt()

    def append_output(self, text: str, prefix=""):
        self.terminal.configure(state="normal")
        if prefix:
            self.terminal.insert("end", f"{prefix} {text}\n")
        else:
            self.terminal.insert("end", f"{text}\n")
        self.terminal.see("end")
        self.terminal.configure(state="disabled")

    def send_prompt(self):
        user_input = self.prompt_entry.get().strip()
        if not user_input:
            return

        # If we are waiting for confirmation, accept typing 'y' or 'n' in the text box
        if self.pending_tool_name:
            self.prompt_entry.delete(0, "end")
            if user_input.lower() in ("y", "yes"):
                self.resolve_safety(True)
            elif user_input.lower() in ("n", "no"):
                self.resolve_safety(False)
            else:
                self.append_output("Please answer with 'y' or 'n', or click the buttons above.", prefix="⚠️")
            return

        self.append_output(f"> {user_input}\n")
        self.prompt_entry.delete(0, "end")
        self.prompt_entry.configure(placeholder_text="Executing pipeline...")
        self.append_output("[PIPELINE] Intent Parser -> Safety Gate...", prefix="⚙️")

        threading.Thread(target=self._execute_pipeline_worker, args=(user_input,), daemon=True).start()

    def _execute_pipeline_worker(self, user_input: str):
        try:
            intent_result = parse_intent(user_input, self.agent.llm_client)
            tool_name = intent_result.get("tool_name")
            arguments = intent_result.get("arguments", {})

            if not tool_name:
                self.after(0, self._render_completion, "I couldn't understand your request. Try something like 'scan this host for open ports' or 'check system health'.")
                return

            if requires_confirmation(tool_name, arguments):
                prompt_text = format_confirmation_prompt(tool_name, arguments)
                self.after(0, self._show_safety_bar, tool_name, arguments, prompt_text)
                return

            self._run_tool_and_summarize(tool_name, arguments)

        except Exception as e:
            self.after(0, self._handle_error, str(e))

    def _show_safety_bar(self, tool_name: str, arguments: dict, prompt_text: str):
        self.pending_tool_name = tool_name
        self.pending_arguments = arguments
        clean_prompt = prompt_text.replace("\n", " ").strip()
        self.safety_label.configure(text=f"⚠️ {clean_prompt}")
        
        # Explicitly grid the confirmation bar above the input row
        self.safety_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 10))
        self.prompt_entry.configure(placeholder_text="Confirm action: type 'y' or 'n', or click buttons above...")
        self.append_output("[SAFETY GATE] Action paused. Click APPROVE / REJECT or type y/n below.\n", prefix="⚠️")

    def _run_tool_and_summarize(self, tool_name: str, arguments: dict):
        try:
            self.after(0, lambda: self.append_output(f"[EXECUTOR] Running tool: {tool_name}...", prefix="⚙️"))
            tool_result = execute_tool(tool_name, arguments)

            try:
                summary = summarize_result(tool_name, tool_result, self.agent.llm_client)
            except Exception:
                summary = fallback_summarize(tool_name, tool_result)

            self.after(0, self._render_completion, summary)
        except Exception as e:
            self.after(0, self._handle_error, str(e))

    def resolve_safety(self, approved: bool):
        self.safety_frame.grid_forget()

        if approved and self.pending_tool_name:
            self.append_output("[SAFETY GATE] Authorized by user. Resuming pipeline...", prefix="✓")
            tool_name = self.pending_tool_name
            arguments = self.pending_arguments
            self.pending_tool_name = None
            self.pending_arguments = None

            self.agent.logger.log_step(
                step="safety_gate",
                action="user_confirmed",
                input_data={"tool_name": tool_name, "arguments": arguments},
                output_data={"confirmed": True},
                confirmed_by_user=True
            )

            threading.Thread(target=self._run_tool_and_summarize, args=(tool_name, arguments), daemon=True).start()
        else:
            self.append_output("[SAFETY GATE] Aborted by user. Execution cancelled.", prefix="✕")
            if self.pending_tool_name:
                self.agent.logger.log_step(
                    step="safety_gate",
                    action="user_denied",
                    input_data={"tool_name": self.pending_tool_name, "arguments": self.pending_arguments},
                    output_data={"confirmed": False},
                    confirmed_by_user=False
                )
            self.pending_tool_name = None
            self.pending_arguments = None
            self.prompt_entry.configure(placeholder_text="Enter command or query (e.g., 'show system health')...")

    def _render_completion(self, output_text: str):
        self.safety_frame.grid_forget()
        self.pending_tool_name = None
        self.pending_arguments = None
        self.prompt_entry.configure(placeholder_text="Enter command or query (e.g., 'show system health')...")
        self.append_output(f"\n{output_text}\n" + "─" * 65 + "\n")

    def _handle_error(self, err_msg: str):
        self.safety_frame.grid_forget()
        self.pending_tool_name = None
        self.pending_arguments = None
        self.prompt_entry.configure(placeholder_text="Enter command or query (e.g., 'show system health')...")
        self.append_output(f"[ERROR] {err_msg}\n", prefix="❌")


if __name__ == "__main__":
    app = CyberRoninApp()
    app.mainloop()