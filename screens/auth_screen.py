"""
screens/auth_screen.py
──────────────────────
AuthScreen — handles Login, Register, and Password-Recovery flows in a
single frame with an internal state machine (sub-view switching).

Sub-views
─────────
• "login"    — default; Username + Password → authenticate
• "register" — Username, Password, Confirm Password,
               Security Question, Security Answer
• "recover"  — Username → show security question → new password
"""

import tkinter as tk
import customtkinter as ctk
from utils.theme import (
    GlassmorphicFrame, GlowButton, SectionLabel, FieldLabel,
    GlassEntry, Toast
)
from config import GLASS, FONT


class AuthScreen(ctk.CTkFrame):
    """
    Authentication frame.

    Callbacks
    ---------
    on_success(user_dict) : called after a successful login/register
    on_back()             : called when user clicks "← Back" to home
    """

    def __init__(self, master, db, on_success=None, on_back=None, **kwargs):
        kwargs.setdefault("fg_color", "transparent")
        super().__init__(master, **kwargs)
        self.db         = db
        self.on_success = on_success
        self.on_back    = on_back
        self._view      = "login"       # current sub-view
        self._recover_username = ""     # filled during recovery flow
        self._build_ui()

    # ── Layout Shell ───────────────────────────────────────────────────────────

    def _build_ui(self):
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Outer centering wrapper
        self.center = ctk.CTkFrame(self, fg_color="transparent")
        self.center.grid(row=0, column=0)

        self._show_login()

    # ── Helper: clear the center frame ────────────────────────────────────────

    def _clear(self):
        for w in self.center.winfo_children():
            w.destroy()

    # ── Back Button Row ────────────────────────────────────────────────────────

    def _add_back_row(self, label="← Back to Home", command=None):
        btn = ctk.CTkButton(
            self.center,
            text=label,
            command=command or self._go_back,
            fg_color="transparent",
            hover_color=GLASS["sidebar_hover"],
            text_color=GLASS["text_dim"],
            font=FONT["small"],
            width=120, height=28,
        )
        btn.pack(anchor="w", pady=(0, 10))

    # ── Sub-view: LOGIN ────────────────────────────────────────────────────────

    def _show_login(self):
        self._clear()
        self._view = "login"

        self._add_back_row()

        # Card
        card = GlassmorphicFrame(self.center, width=400)
        card.pack(ipadx=30, ipady=24)

        ctk.CTkLabel(card, text="🔐  Welcome Back",
                     font=FONT["title"],
                     text_color=GLASS["text_bright"]).pack(pady=(16, 4))
        ctk.CTkLabel(card, text="Sign in to your account",
                     font=FONT["small"],
                     text_color=GLASS["text_dim"]).pack(pady=(0, 20))

        # Username
        FieldLabel(card, text="Username").pack(anchor="w", padx=24)
        self.login_user = GlassEntry(card, placeholder_text="Enter username",
                                     width=320)
        self.login_user.pack(padx=24, pady=(2, 12))

        # Password
        FieldLabel(card, text="Password").pack(anchor="w", padx=24)
        self.login_pass = GlassEntry(card, placeholder_text="Enter password",
                                     show="●", width=320)
        self.login_pass.pack(padx=24, pady=(2, 6))
        self.login_pass.bind("<Return>", lambda e: self._do_login())

        # Forgot password
        ctk.CTkButton(
            card, text="Forgot Password?",
            command=self._show_recover,
            fg_color="transparent", hover_color=GLASS["sidebar_hover"],
            text_color=GLASS["accent_glow"], font=FONT["caption"],
            width=120, height=24,
        ).pack(anchor="e", padx=24, pady=(0, 16))

        # Login button
        self.login_err = ctk.CTkLabel(card, text="",
                                      text_color=GLASS["danger"],
                                      font=FONT["small"], wraplength=300)
        self.login_err.pack()

        GlowButton(card, text="Login  →", command=self._do_login,
                   width=320, height=44).pack(padx=24, pady=(8, 12))

        # Switch to register
        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(pady=(0, 16))
        ctk.CTkLabel(row, text="New here?", font=FONT["small"],
                     text_color=GLASS["text_dim"]).pack(side="left")
        ctk.CTkButton(row, text=" Create Account",
                      command=self._show_register,
                      fg_color="transparent",
                      hover_color=GLASS["sidebar_hover"],
                      text_color=GLASS["accent_glow"],
                      font=FONT["small"],
                      width=110, height=24).pack(side="left")

    # ── Sub-view: REGISTER ─────────────────────────────────────────────────────

    def _show_register(self):
        self._clear()
        self._view = "register"

        self._add_back_row(label="← Back to Login", command=self._show_login)

        card = GlassmorphicFrame(self.center, width=420)
        card.pack(ipadx=30, ipady=20)

        ctk.CTkLabel(card, text="📝  Create Account",
                     font=FONT["title"],
                     text_color=GLASS["text_bright"]).pack(pady=(16, 4))
        ctk.CTkLabel(card, text="Join the Campus Lost & Found network",
                     font=FONT["small"],
                     text_color=GLASS["text_dim"]).pack(pady=(0, 16))

        def _field(label, placeholder, show=""):
            FieldLabel(card, text=label).pack(anchor="w", padx=24)
            e = GlassEntry(card, placeholder_text=placeholder,
                           show=show, width=340)
            e.pack(padx=24, pady=(2, 10))
            return e

        self.reg_user    = _field("Username",         "Choose a username")
        self.reg_pass    = _field("Password",         "Min. 6 characters", "●")
        self.reg_confirm = _field("Confirm Password", "Re-enter password",  "●")

        # Security question
        FieldLabel(card, text="Security Question (for password recovery)").pack(
            anchor="w", padx=24)
        self.reg_secq = ctk.CTkOptionMenu(
            card,
            values=[
                "What is your mother's maiden name?",
                "What was the name of your first pet?",
                "What city were you born in?",
                "What is your favourite book?",
                "What was your childhood nickname?",
            ],
            fg_color=GLASS["input_bg"],
            button_color=GLASS["accent"],
            button_hover_color=GLASS["accent_glow"],
            text_color=GLASS["text"],
            font=FONT["body"],
            width=340,
        )
        self.reg_secq.pack(padx=24, pady=(2, 10))

        self.reg_seca = _field("Security Answer", "Your answer (case-insensitive)")

        self.reg_err = ctk.CTkLabel(card, text="", text_color=GLASS["danger"],
                                    font=FONT["small"], wraplength=300)
        self.reg_err.pack()

        GlowButton(card, text="Create Account  →", command=self._do_register,
                   width=340, height=44).pack(padx=24, pady=(8, 16))

    # ── Sub-view: RECOVER ──────────────────────────────────────────────────────

    def _show_recover(self):
        self._clear()
        self._view = "recover_step1"
        self._add_back_row(label="← Back to Login", command=self._show_login)

        card = GlassmorphicFrame(self.center, width=400)
        card.pack(ipadx=30, ipady=24)

        ctk.CTkLabel(card, text="🔑  Password Recovery",
                     font=FONT["title"],
                     text_color=GLASS["text_bright"]).pack(pady=(16, 4))
        ctk.CTkLabel(card, text="Enter your username to begin",
                     font=FONT["small"],
                     text_color=GLASS["text_dim"]).pack(pady=(0, 16))

        FieldLabel(card, text="Username").pack(anchor="w", padx=24)
        self.rec_user = GlassEntry(card, placeholder_text="Your username",
                                   width=320)
        self.rec_user.pack(padx=24, pady=(2, 10))

        self.rec_err = ctk.CTkLabel(card, text="", text_color=GLASS["danger"],
                                    font=FONT["small"])
        self.rec_err.pack()

        GlowButton(card, text="Continue →", command=self._do_recover_step1,
                   width=320, height=44).pack(padx=24, pady=(10, 16))

    def _show_recover_step2(self, username: str, question: str):
        """Show the security-question answer form."""
        self._clear()
        self._recover_username = username
        self._add_back_row(label="← Back", command=self._show_recover)

        card = GlassmorphicFrame(self.center, width=420)
        card.pack(ipadx=30, ipady=24)

        ctk.CTkLabel(card, text="🔑  Verify Identity",
                     font=FONT["title"],
                     text_color=GLASS["text_bright"]).pack(pady=(16, 4))

        ctk.CTkLabel(card, text=question,
                     font=FONT["body"],
                     text_color=GLASS["accent_glow"],
                     wraplength=340).pack(padx=24, pady=(8, 4))

        FieldLabel(card, text="Your Answer").pack(anchor="w", padx=24)
        self.rec_ans = GlassEntry(card, placeholder_text="Answer", width=340)
        self.rec_ans.pack(padx=24, pady=(2, 10))

        FieldLabel(card, text="New Password").pack(anchor="w", padx=24)
        self.rec_newpass = GlassEntry(card, placeholder_text="New password",
                                      show="●", width=340)
        self.rec_newpass.pack(padx=24, pady=(2, 10))

        self.rec_err2 = ctk.CTkLabel(card, text="", text_color=GLASS["danger"],
                                     font=FONT["small"])
        self.rec_err2.pack()

        GlowButton(card, text="Reset Password", command=self._do_recover_step2,
                   width=340, height=44).pack(padx=24, pady=(10, 16))

    # ── Actions ────────────────────────────────────────────────────────────────

    def _do_login(self):
        user = self.login_user.get().strip()
        pwd  = self.login_pass.get()
        if not user or not pwd:
            self.login_err.configure(text="Please fill in all fields.")
            return
        result = self.db.login_user(user, pwd)
        if result["ok"]:
            if callable(self.on_success):
                self.on_success(result["user"])
        else:
            self.login_err.configure(text=f"⚠  {result['err']}")

    def _do_register(self):
        user    = self.reg_user.get().strip()
        pwd     = self.reg_pass.get()
        confirm = self.reg_confirm.get()
        secq    = self.reg_secq.get()
        seca    = self.reg_seca.get().strip()

        if not user or not pwd or not confirm:
            self.reg_err.configure(text="Please fill in all required fields.")
            return
        if len(pwd) < 6:
            self.reg_err.configure(text="Password must be at least 6 characters.")
            return
        if pwd != confirm:
            self.reg_err.configure(text="Passwords do not match.")
            return

        result = self.db.register_user(user, pwd, secq, seca)
        if result["ok"]:
            # Auto-login after register
            login_res = self.db.login_user(user, pwd)
            if login_res["ok"] and callable(self.on_success):
                self.on_success(login_res["user"])
        else:
            self.reg_err.configure(text=f"⚠  {result['err']}")

    def _do_recover_step1(self):
        username = self.rec_user.get().strip()
        if not username:
            self.rec_err.configure(text="Enter your username.")
            return
        question = self.db.get_security_question(username)
        if not question:
            self.rec_err.configure(
                text="Username not found or no security question set.")
            return
        self._show_recover_step2(username, question)

    def _do_recover_step2(self):
        answer  = self.rec_ans.get().strip()
        new_pwd = self.rec_newpass.get()
        if not answer or not new_pwd:
            self.rec_err2.configure(text="Please fill in all fields.")
            return
        if len(new_pwd) < 6:
            self.rec_err2.configure(text="Password must be at least 6 characters.")
            return
        ok = self.db.verify_security_answer(self._recover_username, answer)
        if not ok:
            self.rec_err2.configure(text="Incorrect answer. Try again.")
            return
        self.db.reset_password(self._recover_username, new_pwd)
        Toast.show(self, "✅  Password reset!  Please login.", kind="success")
        self.after(1500, self._show_login)

    def _go_back(self):
        if callable(self.on_back):
            self.on_back()
