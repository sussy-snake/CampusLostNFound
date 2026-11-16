"""
main.py
───────
Application entry-point and top-level controller for Campus Lost & Found.

Responsibilities
─────────────────
• Bootstrap the CustomTkinter root window.
• Generate and paint the gradient background canvas.
• Manage the frame lifecycle: Home → Auth → Portal.
• Route animated transitions via AnimationManager.
• Own the single DatabaseManager instance and pass it down.
"""

import tkinter as tk
import customtkinter as ctk
from database          import DatabaseManager
from utils.theme       import apply_gradient_bg
from utils.animations  import AnimationManager
from screens.home_screen   import HomeScreen
from screens.auth_screen   import AuthScreen
from screens.portal_screen import PortalScreen
from config import APP_TITLE, WIN_SIZE, MIN_SIZE, GLASS


# ── Appearance ─────────────────────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class App(ctk.CTk):
    """
    Root window and application state machine.

    States
    ──────
    "home"   → HomeScreen    (splash / welcome)
    "auth"   → AuthScreen    (login / register / recover)
    "portal" → PortalScreen  (main dashboard for logged-in user)
    """

    def __init__(self):
        super().__init__()

        # ── Window Setup ───────────────────────────────────────────────────────
        self.title(APP_TITLE)
        self.geometry(WIN_SIZE)
        self.minsize(*MIN_SIZE)
        self.configure(fg_color=GLASS["input_bg"])

        # ── Database ───────────────────────────────────────────────────────────
        self.db = DatabaseManager()

        # ── Background Canvas (gradient + stars) ───────────────────────────────
        self.bg_canvas = tk.Canvas(self, highlightthickness=0,
                                   bg=GLASS["input_bg"])
        self.bg_canvas.place(relx=0, rely=0, relwidth=1, relheight=1)
        apply_gradient_bg(self, self.bg_canvas)

        # ── Frame Container (sits on top of the canvas) ────────────────────────
        self.container = ctk.CTkFrame(self, fg_color="transparent",
                                      corner_radius=0)
        self.container.place(relx=0, rely=0, relwidth=1, relheight=1)

        # ── Animation Manager ─────────────────────────────────────────────────
        self.anim = AnimationManager(
            container   = self.container,
            width_ref   = lambda: self.winfo_width(),
            height_ref  = lambda: self.winfo_height(),
        )

        # ── State ─────────────────────────────────────────────────────────────
        self._current_frame  = None
        self._current_user   = None

        # ── Launch Home Screen ─────────────────────────────────────────────────
        self._go_home()

        # ── Clean shutdown ─────────────────────────────────────────────────────
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ── Navigation ─────────────────────────────────────────────────────────────

    def _go_home(self):
        """Navigate to the splash / welcome screen."""
        new_frame = HomeScreen(
            self.container,
            on_enter=self._go_auth,
        )
        self._transition(new_frame, direction="right")

    def _go_auth(self):
        """Navigate to the login / register screen (slide left)."""
        new_frame = AuthScreen(
            self.container,
            db=self.db,
            on_success=self._on_login_success,
            on_back=self._go_home,
        )
        self._transition(new_frame, direction="left")

    def _on_login_success(self, user: dict):
        """Called by AuthScreen after a valid login or registration."""
        self._current_user = user
        self._go_portal()

    def _go_portal(self):
        """Navigate to the main dashboard (slide left)."""
        new_frame = PortalScreen(
            self.container,
            current_user=self._current_user,
            db=self.db,
            on_logout=self._on_logout,
        )
        self._transition(new_frame, direction="left")

    def _on_logout(self):
        """Log out and return to the home screen."""
        self._current_user = None
        self._go_home()

    # ── Frame Transition Helper ────────────────────────────────────────────────

    def _transition(self, new_frame: ctk.CTkFrame, direction: str = "left"):
        """
        Replace *_current_frame* with *new_frame* using an animated slide.

        Parameters
        ----------
        direction : "left"  → new frame enters from right (forward navigation)
                    "right" → new frame enters from left  (back navigation)
        """
        old_frame = self._current_frame

        # First screen: just place it instantly
        if old_frame is None:
            new_frame.place(relx=0, rely=0, relwidth=1, relheight=1)
            self._current_frame = new_frame
            return

        # Animated transition
        if direction == "left":
            self.anim.slide_left(old_frame, new_frame,
                                 on_done=lambda: self._finish_transition(old_frame))
        else:
            self.anim.slide_right(old_frame, new_frame,
                                  on_done=lambda: self._finish_transition(old_frame))

        self._current_frame = new_frame

    def _finish_transition(self, old_frame: ctk.CTkFrame):
        """Destroy the previous frame after animation completes."""
        try:
            old_frame.destroy()
        except Exception:
            pass

    # ── Shutdown ───────────────────────────────────────────────────────────────

    def _on_close(self):
        """Graceful shutdown: close DB connection then destroy window."""
        try:
            self.db.close()
        except Exception:
            pass
        self.destroy()


# ── Entry Point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = App()
    app.mainloop()
