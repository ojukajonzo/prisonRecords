import tkinter as tk
from tkinter import messagebox

from visitor_form import VisitorFormWindow
from admin_panel import AdminPanelWindow


class DashboardWindow:
    def __init__(self, root: tk.Toplevel, user: dict):
        self.root = root
        self.user = user

        self.root.title(f"MIS MAIN - Dashboard ({self.user['role']})")
        self.root.geometry("600x320")
        self.root.resizable(False, False)

        self._build_ui()

    def _build_ui(self):
        top_frame = tk.Frame(self.root, padx=10, pady=10)
        top_frame.pack(fill="x")

        title = tk.Label(
            top_frame,
            text="MIS MAIN - Visitor Management",
            font=("Segoe UI", 16, "bold"),
            anchor="w",
        )
        title.pack(side="left", fill="x", expand=True)

        user_label = tk.Label(
            top_frame, text=f"User: {self.user['username']} ({self.user['role']})", font=("Segoe UI", 9)
        )
        user_label.pack(side="right")

        sep = tk.Frame(self.root, height=2, bd=1, relief="sunken")
        sep.pack(fill="x", padx=5, pady=5)

        center_frame = tk.Frame(self.root, padx=20, pady=20)
        center_frame.pack(fill="both", expand=True)

        btn_width = 25
        row_pad = 8

        # Visitor management
        visitor_btn = tk.Button(
            center_frame,
            text="Register / Search Visitor",
            width=btn_width,
            command=self.open_visitor_form,
        )
        visitor_btn.grid(row=0, column=0, sticky="w", pady=row_pad)

        # Admin panel (only for admins)
        self.admin_btn = tk.Button(
            center_frame,
            text="Admin Panel (User & Record Management)",
            width=btn_width,
            command=self.open_admin_panel,
        )
        self.admin_btn.grid(row=1, column=0, sticky="w", pady=row_pad)

        if self.user["role"] != "ADMIN":
            self.admin_btn.configure(state="disabled")

        # Exit
        exit_btn = tk.Button(center_frame, text="Exit", width=btn_width, command=self.root.quit)
        exit_btn.grid(row=3, column=0, sticky="w", pady=row_pad)

        info_text = (
            "Recording User:\n"
            "- Add new visit records\n"
            "- Search and view visitors\n"
            "- Cannot edit or delete previous records\n\n"
            "Admin:\n"
            "- Full access to all functions"
        )
        info_label = tk.Label(center_frame, text=info_text, justify="left", font=("Segoe UI", 9))
        info_label.grid(row=0, column=1, rowspan=4, padx=30, sticky="n")

    def open_visitor_form(self):
        win = tk.Toplevel(self.root)
        VisitorFormWindow(win, self.user)

    def open_admin_panel(self):
        if self.user["role"] != "ADMIN":
            messagebox.showerror("Access Denied", "Only ADMIN users can access the Admin Panel.")
            return
        win = tk.Toplevel(self.root)
        AdminPanelWindow(win, self.user)

