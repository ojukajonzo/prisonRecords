import tkinter as tk
from tkinter import messagebox, ttk
from typing import Optional
from datetime import date

from database import get_connection


class VisitorFormWindow:
    def __init__(self, root: tk.Toplevel, user: dict):
        """
        Main visitor entry and history window.
        Handles both creating/updating visitor bio data and recording visits.
        """
        self.root = root
        self.user = user
        self.root.title("Visitor Registration and Search")
        self.root.geometry("900x500")

        # Tracks the currently loaded visitor (if any)
        self.current_visitor_id: Optional[int] = None

        self._build_ui()

        # Pre-fill the visit date with the current system date in ISO format (YYYY-MM-DD).
        # The user can still change this value manually if needed.
        self._set_today_date()

    def _build_ui(self):
        container = tk.Frame(self.root, padx=10, pady=10)
        container.pack(fill="both", expand=True)

        # Left: search and visitor info
        left = tk.Frame(container)
        left.pack(side="left", fill="y")

        # Search area
        search_frame = tk.LabelFrame(left, text="Search Visitor", padx=5, pady=5)
        search_frame.pack(fill="x", pady=5)

        tk.Label(search_frame, text="Name or NIN:").grid(row=0, column=0, sticky="w")
        self.search_entry = tk.Entry(search_frame, width=30)
        self.search_entry.grid(row=0, column=1, padx=5)

        tk.Button(search_frame, text="Search", command=self.search_visitor).grid(
            row=0, column=2, padx=5
        )

        # Visitor details
        visitor_frame = tk.LabelFrame(left, text="Visitor Details", padx=5, pady=5)
        visitor_frame.pack(fill="x", pady=5)

        self.entry_full_name = self._add_labeled_entry(visitor_frame, "Full Name:", 0)
        self.entry_nin = self._add_labeled_entry(visitor_frame, "National ID (NIN):", 1)
        self.entry_district = self._add_labeled_entry(visitor_frame, "District:", 2)
        self.entry_sub_county = self._add_labeled_entry(visitor_frame, "Sub County:", 3)
        self.entry_village = self._add_labeled_entry(visitor_frame, "Village:", 4)

        # Right: visit details and history
        right = tk.Frame(container)
        right.pack(side="left", fill="both", expand=True, padx=(10, 0))

        visit_frame = tk.LabelFrame(right, text="Visit Details", padx=5, pady=5)
        visit_frame.pack(fill="x", pady=5)

        self.entry_reason = self._add_labeled_entry(visit_frame, "Reason for Visit:", 0, width=50)
        self.entry_person = self._add_labeled_entry(visit_frame, "Person Visited:", 1, width=50)
        self.entry_items = self._add_labeled_entry(visit_frame, "Items Brought:", 2, width=50)
        self.entry_time_in = self._add_labeled_entry(visit_frame, "Time In (HH:MM):", 3, width=20)
        self.entry_time_out = self._add_labeled_entry(visit_frame, "Time Out (HH:MM):", 4, width=20)
        self.entry_date = self._add_labeled_entry(
            visit_frame, "Date (YYYY-MM-DD):", 5, width=20
        )

        btn_frame = tk.Frame(visit_frame)
        btn_frame.grid(row=6, column=0, columnspan=2, pady=5, sticky="w")

        save_btn = tk.Button(btn_frame, text="Save Visit", command=self.save_visit)
        save_btn.pack(side="left", padx=5)

        clear_btn = tk.Button(btn_frame, text="Clear Form", command=self.clear_form)
        clear_btn.pack(side="left", padx=5)

        # Visit history
        history_frame = tk.LabelFrame(right, text="Visit History", padx=5, pady=5)
        history_frame.pack(fill="both", expand=True, pady=5)

        columns = ("date", "time_in", "time_out", "person", "reason")
        self.history_tree = ttk.Treeview(
            history_frame, columns=columns, show="headings", height=10
        )
        self.history_tree.heading("date", text="Date")
        self.history_tree.heading("time_in", text="Time In")
        self.history_tree.heading("time_out", text="Time Out")
        self.history_tree.heading("person", text="Person Visited")
        self.history_tree.heading("reason", text="Reason")

        for col in columns:
            self.history_tree.column(col, width=120, anchor="w")

        self.history_tree.pack(fill="both", expand=True)

    @staticmethod
    def _add_labeled_entry(parent, label, row, width=30):
        tk.Label(parent, text=label, width=18, anchor="w").grid(row=row, column=0, sticky="w", pady=2)
        entry = tk.Entry(parent, width=width)
        entry.grid(row=row, column=1, sticky="w", pady=2)
        return entry

    def _set_today_date(self):
        """
        Set the visit date entry to the current system date.
        """
        today_str = date.today().isoformat()
        self.entry_date.delete(0, "end")
        self.entry_date.insert(0, today_str)

    def search_visitor(self):
        query = self.search_entry.get().strip()
        if not query:
            messagebox.showwarning("Missing Search", "Please enter a name or NIN to search.")
            return

        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT * FROM visitors
            WHERE nin = ? OR full_name LIKE ?
            """,
            (query, f"%{query}%"),
        )
        row = cur.fetchone()
        if not row:
            messagebox.showinfo(
                "Visitor Not Found",
                "No existing visitor found. You can enter new visitor details.",
            )
            self.current_visitor_id = None
            self.clear_visitor_only()
            conn.close()
            self._clear_history()
            return

        self.current_visitor_id = row["id"]
        self.entry_full_name.delete(0, "end")
        self.entry_full_name.insert(0, row["full_name"])

        self.entry_nin.delete(0, "end")
        self.entry_nin.insert(0, row["nin"])

        self.entry_district.delete(0, "end")
        self.entry_district.insert(0, row["district"] or "")

        self.entry_sub_county.delete(0, "end")
        self.entry_sub_county.insert(0, row["sub_county"] or "")

        self.entry_village.delete(0, "end")
        self.entry_village.insert(0, row["village"] or "")

        self.load_visit_history(conn, self.current_visitor_id)
        conn.close()

    def load_visit_history(self, conn, visitor_id: int):
        self._clear_history()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT visit_date, time_in, time_out, person_visited, reason
            FROM visits
            WHERE visitor_id = ?
            ORDER BY visit_date DESC, time_in DESC
            """,
            (visitor_id,),
        )
        for row in cur.fetchall():
            self.history_tree.insert(
                "",
                "end",
                values=(
                    row["visit_date"],
                    row["time_in"],
                    row["time_out"] or "",
                    row["person_visited"],
                    row["reason"] or "",
                ),
            )

    def _clear_history(self):
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)

    def clear_visitor_only(self):
        self.entry_full_name.delete(0, "end")
        self.entry_nin.delete(0, "end")
        self.entry_district.delete(0, "end")
        self.entry_sub_county.delete(0, "end")
        self.entry_village.delete(0, "end")

    def clear_form(self):
        self.clear_visitor_only()
        self._clear_visit_inputs()
        self._clear_history()
        self.current_visitor_id = None

    def _clear_visit_inputs(self):
        """
        Clear only the visit-specific input fields (reason, times, date, etc.).
        Visitor bio data and history remain for easier repeated entries.
        """
        self.entry_reason.delete(0, "end")
        self.entry_person.delete(0, "end")
        self.entry_items.delete(0, "end")
        self.entry_time_in.delete(0, "end")
        self.entry_time_out.delete(0, "end")
        self.entry_date.delete(0, "end")
        # After clearing, restore today's date to guide the operator
        self._set_today_date()

    def save_visit(self):
        full_name = self.entry_full_name.get().strip()
        nin = self.entry_nin.get().strip()

        if not full_name or not nin:
            messagebox.showwarning(
                "Missing Visitor Details", "Full Name and NIN are required for a visit record."
            )
            return

        district = self.entry_district.get().strip()
        sub_county = self.entry_sub_county.get().strip()
        village = self.entry_village.get().strip()

        reason = self.entry_reason.get().strip()
        person_visited = self.entry_person.get().strip()
        items_brought = self.entry_items.get().strip()
        time_in = self.entry_time_in.get().strip()
        time_out = self.entry_time_out.get().strip()
        visit_date = self.entry_date.get().strip()

        if not person_visited or not time_in or not visit_date:
            messagebox.showwarning(
                "Missing Visit Details",
                "Person Visited, Time In, and Date of Visit are required.",
            )
            return

        conn = get_connection()
        cur = conn.cursor()

        # Insert or update visitor
        if self.current_visitor_id is None:
            # Try find by NIN first to avoid duplicates
            cur.execute("SELECT id FROM visitors WHERE nin = ?", (nin,))
            row = cur.fetchone()
            if row:
                self.current_visitor_id = row["id"]
                cur.execute(
                    """
                    UPDATE visitors
                    SET full_name = ?, district = ?, sub_county = ?, village = ?
                    WHERE id = ?
                    """,
                    (full_name, district, sub_county, village, self.current_visitor_id),
                )
            else:
                cur.execute(
                    """
                    INSERT INTO visitors (full_name, nin, district, sub_county, village)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (full_name, nin, district, sub_county, village),
                )
                self.current_visitor_id = cur.lastrowid
        else:
            # Existing visitor: update basic details (allowed)
            cur.execute(
                """
                UPDATE visitors
                SET full_name = ?, nin = ?, district = ?, sub_county = ?, village = ?
                WHERE id = ?
                """,
                (full_name, nin, district, sub_county, village, self.current_visitor_id),
            )

        # Insert visit record
        cur.execute(
            """
            INSERT INTO visits (
                visitor_id, reason, person_visited, items_brought,
                time_in, time_out, visit_date
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                self.current_visitor_id,
                reason,
                person_visited,
                items_brought,
                time_in,
                time_out,
                visit_date,
            ),
        )

        conn.commit()
        self.load_visit_history(conn, self.current_visitor_id)
        conn.close()

        messagebox.showinfo("Saved", "Visit record saved successfully.")

        # After saving, clear the visit input fields so the next record starts with a clean slate,
        # but keep the visitor details and history visible for quick repeated visits.
        self._clear_visit_inputs()
