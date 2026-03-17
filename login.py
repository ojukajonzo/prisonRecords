import tkinter as tk
from tkinter import messagebox

from database import verify_user, init_db
from dashboard import DashboardWindow


class LoginWindow:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("MIS MAIN - Login")
        self.root.geometry("350x220")
        self.root.resizable(False, False)

        # Ensure DB exists before login
        init_db()

        self._build_ui()

    def _build_ui(self):
        main_frame = tk.Frame(self.root, padx=20, pady=20)
        main_frame.pack(fill="both", expand=True)

        title = tk.Label(main_frame, text="MIS MAIN", font=("Segoe UI", 16, "bold"))
        title.pack(pady=(0, 10))

        subtitle = tk.Label(main_frame, text="Visitor Management System", font=("Segoe UI", 9))
        subtitle.pack(pady=(0, 15))

        # Username
        user_frame = tk.Frame(main_frame)
        user_frame.pack(fill="x", pady=5)
        tk.Label(user_frame, text="Username:", width=12, anchor="w").pack(side="left")
        self.entry_username = tk.Entry(user_frame)
        self.entry_username.pack(side="left", fill="x", expand=True)

        # Password
        pass_frame = tk.Frame(main_frame)
        pass_frame.pack(fill="x", pady=5)
        tk.Label(pass_frame, text="Password:", width=12, anchor="w").pack(side="left")
        self.entry_password = tk.Entry(pass_frame, show="*")
        self.entry_password.pack(side="left", fill="x", expand=True)

        btn_frame = tk.Frame(main_frame)
        btn_frame.pack(pady=15)

        login_btn = tk.Button(btn_frame, text="Login", width=10, command=self.handle_login)
        login_btn.pack(side="left", padx=5)

        self.root.bind("<Return>", lambda _event: self.handle_login())

    def handle_login(self):
        username = self.entry_username.get().strip()
        password = self.entry_password.get().strip()

        if not username or not password:
            messagebox.showwarning("Missing Information", "Please enter both username and password.")
            return

        user = verify_user(username, password)
        if not user:
            messagebox.showerror("Login Failed", "Invalid username or password.")
            return

        # Open dashboard and hide login window
        self.open_dashboard(user)

    def open_dashboard(self, user):
        # Create new top-level window for dashboard
        dash_window = tk.Toplevel(self.root)
        DashboardWindow(dash_window, user)
        # Hide login window but keep it in memory in case of logout
        self.root.withdraw()


def run_login_app():
    root = tk.Tk()
    LoginWindow(root)
    root.mainloop()


if __name__ == "__main__":
    run_login_app()

