import tkinter as tk
from tkinter import messagebox, ttk

from database import get_connection, create_user


class AdminPanelWindow:
    def __init__(self, root: tk.Toplevel, user: dict):
        self.root = root
        self.user = user
        self.root.title("Admin Panel")
        self.root.geometry("950x520")

        self._build_ui()
        self.load_users()
        self.load_recent_visits()

    def _build_ui(self):
        container = tk.Frame(self.root, padx=10, pady=10)
        container.pack(fill="both", expand=True)

        # Left: user management
        left = tk.LabelFrame(container, text="User Management", padx=5, pady=5)
        left.pack(side="left", fill="y")

        self.entry_new_username = self._add_labeled_entry(left, "Username:", 0)
        self.entry_new_password = self._add_labeled_entry(left, "Password:", 1, show="*")

        tk.Label(left, text="Role:", width=15, anchor="w").grid(row=2, column=0, sticky="w", pady=2)
        self.role_var = tk.StringVar(value="RECORDING_USER")
        role_combo = ttk.Combobox(
            left,
            textvariable=self.role_var,
            values=["ADMIN", "RECORDING_USER"],
            state="readonly",
            width=17,
        )
        role_combo.grid(row=2, column=1, sticky="w", pady=2)

        btn_frame = tk.Frame(left)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=8)
        tk.Button(btn_frame, text="Add User", command=self.add_user).pack(side="left", padx=5)

        users_frame = tk.LabelFrame(left, text="Existing Users", padx=5, pady=5)
        users_frame.grid(row=4, column=0, columnspan=2, pady=10, sticky="nsew")

        columns = ("id", "username", "role")
        self.users_tree = ttk.Treeview(
            users_frame, columns=columns, show="headings", height=10, selectmode="browse"
        )
        for col, text, width in [
            ("id", "ID", 40),
            ("username", "Username", 120),
            ("role", "Role", 120),
        ]:
            self.users_tree.heading(col, text=text)
            self.users_tree.column(col, width=width, anchor="w")
        self.users_tree.pack(fill="both", expand=True)

        # Right: record view/edit/delete (basic)
        right = tk.LabelFrame(container, text="Visit Records (View / Edit / Delete)", padx=5, pady=5)
        right.pack(side="left", fill="both", expand=True, padx=(10, 0))

        columns = ("id", "visitor", "nin", "date", "person", "reason")
        self.records_tree = ttk.Treeview(
            right, columns=columns, show="headings", height=15, selectmode="browse"
        )
        headings = [
            ("id", "ID", 40),
            ("visitor", "Visitor Name", 150),
            ("nin", "NIN", 120),
            ("date", "Date", 90),
            ("person", "Person Visited", 150),
            ("reason", "Reason", 180),
        ]
        for col, text, width in headings:
            self.records_tree.heading(col, text=text)
            self.records_tree.column(col, width=width, anchor="w")
        self.records_tree.pack(fill="both", expand=True)

        btn_frame2 = tk.Frame(right)
        btn_frame2.pack(pady=5, anchor="w")

        tk.Button(btn_frame2, text="Refresh", command=self.load_recent_visits).pack(
            side="left", padx=3
        )
        tk.Button(btn_frame2, text="Edit Selected", command=self.edit_selected).pack(
            side="left", padx=3
        )
        tk.Button(btn_frame2, text="Delete Selected", command=self.delete_selected).pack(
            side="left", padx=3
        )

    @staticmethod
    def _add_labeled_entry(parent, label, row, show=None):
        tk.Label(parent, text=label, width=15, anchor="w").grid(row=row, column=0, sticky="w", pady=2)
        entry = tk.Entry(parent, width=20, show=show)
        entry.grid(row=row, column=1, sticky="w", pady=2)
        return entry

    def add_user(self):
        username = self.entry_new_username.get().strip()
        password = self.entry_new_password.get().strip()
        role = self.role_var.get()

        if not username or not password:
            messagebox.showwarning("Missing Data", "Username and password are required.")
            return

        try:
            create_user(username, password, role)
        except Exception as exc:
            messagebox.showerror("Error", f"Could not create user:\n{exc}")
            return

        messagebox.showinfo("User Added", f"User '{username}' created successfully.")
        self.entry_new_username.delete(0, "end")
        self.entry_new_password.delete(0, "end")
        self.load_users()

    def load_users(self):
        for item in self.users_tree.get_children():
            self.users_tree.delete(item)

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, username, role FROM users ORDER BY username")
        for row in cur.fetchall():
            self.users_tree.insert(
                "",
                "end",
                values=(row["id"], row["username"], row["role"]),
            )
        conn.close()

    def load_recent_visits(self):
        for item in self.records_tree.get_children():
            self.records_tree.delete(item)

        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT v.id,
                   vis.full_name AS visitor_name,
                   vis.nin,
                   v.visit_date,
                   v.person_visited,
                   v.reason
            FROM visits v
            JOIN visitors vis ON v.visitor_id = vis.id
            ORDER BY v.visit_date DESC, v.time_in DESC
            LIMIT 200
            """
        )
        for row in cur.fetchall():
            self.records_tree.insert(
                "",
                "end",
                values=(
                    row["id"],
                    row["visitor_name"],
                    row["nin"],
                    row["visit_date"],
                    row["person_visited"],
                    row["reason"] or "",
                ),
            )
        conn.close()

    def get_selected_visit_id(self):
        sel = self.records_tree.selection()
        if not sel:
            return None
        item = sel[0]
        values = self.records_tree.item(item, "values")
        return int(values[0])

    def edit_selected(self):
        visit_id = self.get_selected_visit_id()
        if visit_id is None:
            messagebox.showwarning("No Selection", "Please select a visit record to edit.")
            return

        EditVisitDialog(self.root, visit_id, on_saved=self.load_recent_visits)

    def delete_selected(self):
        visit_id = self.get_selected_visit_id()
        if visit_id is None:
            messagebox.showwarning("No Selection", "Please select a visit record to delete.")
            return

        if messagebox.askyesno(
            "Confirm Delete",
            "Are you sure you want to permanently delete this visit record?",
        ):
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("DELETE FROM visits WHERE id = ?", (visit_id,))
            conn.commit()
            conn.close()
            self.load_recent_visits()
            messagebox.showinfo("Deleted", "Visit record deleted.")


class EditVisitDialog:
    def __init__(self, parent: tk.Tk, visit_id: int, on_saved=None):
        self.visit_id = visit_id
        self.on_saved = on_saved

        self.top = tk.Toplevel(parent)
        self.top.title(f"Edit Visit #{visit_id}")
        self.top.geometry("420x320")
        self._build_ui()
        self.load_visit()

    def _build_ui(self):
        frame = tk.Frame(self.top, padx=10, pady=10)
        frame.pack(fill="both", expand=True)

        self.entry_date = self._add_labeled_entry(frame, "Date (YYYY-MM-DD):", 0)
        self.entry_time_in = self._add_labeled_entry(frame, "Time In (HH:MM):", 1)
        self.entry_time_out = self._add_labeled_entry(frame, "Time Out (HH:MM):", 2)
        self.entry_person = self._add_labeled_entry(frame, "Person Visited:", 3)
        self.entry_reason = self._add_labeled_entry(frame, "Reason:", 4)
        self.entry_items = self._add_labeled_entry(frame, "Items Brought:", 5)

        btn_frame = tk.Frame(frame)
        btn_frame.grid(row=6, column=0, columnspan=2, pady=10)

        tk.Button(btn_frame, text="Save", command=self.save).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Cancel", command=self.top.destroy).pack(side="left", padx=5)

    @staticmethod
    def _add_labeled_entry(parent, label, row):
        tk.Label(parent, text=label, width=18, anchor="w").grid(row=row, column=0, sticky="w", pady=2)
        entry = tk.Entry(parent, width=30)
        entry.grid(row=row, column=1, sticky="w", pady=2)
        return entry

    def load_visit(self):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT visit_date, time_in, time_out, person_visited, reason, items_brought
            FROM visits
            WHERE id = ?
            """,
            (self.visit_id,),
        )
        row = cur.fetchone()
        conn.close()

        if not row:
            messagebox.showerror("Error", "Visit record not found.")
            self.top.destroy()
            return

        self.entry_date.insert(0, row["visit_date"])
        self.entry_time_in.insert(0, row["time_in"])
        self.entry_time_out.insert(0, row["time_out"] or "")
        self.entry_person.insert(0, row["person_visited"])
        self.entry_reason.insert(0, row["reason"] or "")
        self.entry_items.insert(0, row["items_brought"] or "")

    def save(self):
        visit_date = self.entry_date.get().strip()
        time_in = self.entry_time_in.get().strip()
        time_out = self.entry_time_out.get().strip()
        person_visited = self.entry_person.get().strip()
        reason = self.entry_reason.get().strip()
        items_brought = self.entry_items.get().strip()

        if not visit_date or not time_in or not person_visited:
            messagebox.showwarning(
                "Missing Data", "Date, Time In, and Person Visited are required."
            )
            return

        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE visits
            SET visit_date = ?, time_in = ?, time_out = ?,
                person_visited = ?, reason = ?, items_brought = ?
            WHERE id = ?
            """,
            (
                visit_date,
                time_in,
                time_out,
                person_visited,
                reason,
                items_brought,
                self.visit_id,
            ),
        )
        conn.commit()
        conn.close()

        messagebox.showinfo("Saved", "Visit record updated.")
        if self.on_saved:
            self.on_saved()
        self.top.destroy()

