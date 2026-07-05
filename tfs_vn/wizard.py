"""Tkinter desktop wizard for scaffolding visual novel projects."""

from __future__ import annotations

from pathlib import Path
import traceback
import tkinter as tk
from tkinter import colorchooser, filedialog, messagebox, ttk
from typing import Any

from .config import ConfigError, slugify, titleize_slug, write_json
from .scaffold import scaffold_project
from .validate import ValidationError


class Wizard(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("TFS Visual Novel Tools")
        self.geometry("980x700")
        self.minsize(860, 600)
        self.rooms: list[dict[str, str]] = []
        self.title_var = tk.StringVar(value="Untitled Adventure")
        self.subtitle_var = tk.StringVar(value="A Visual Novel")
        self.dedication_var = tk.StringVar(value="")
        self.accent_var = tk.StringVar(value="#37d2c3")
        self.bg_dir_var = tk.StringVar(value="")
        self.cover_var = tk.StringVar(value="")
        self.output_var = tk.StringVar(value="")
        self.validate_var = tk.BooleanVar(value=True)
        self._build()

    def _build(self) -> None:
        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)
        self._project_tab(notebook)
        self._assets_tab(notebook)
        self._rooms_tab(notebook)
        self._build_tab(notebook)

    def _project_tab(self, notebook: ttk.Notebook) -> None:
        frame = ttk.Frame(notebook, padding=16)
        notebook.add(frame, text="Project")
        self._row(frame, "Title", self.title_var, 0)
        self._row(frame, "Subtitle", self.subtitle_var, 1)
        self._row(frame, "Dedication", self.dedication_var, 2)
        ttk.Label(frame, text="Accent").grid(row=3, column=0, sticky="w", pady=8)
        ttk.Entry(frame, textvariable=self.accent_var).grid(row=3, column=1, sticky="ew", pady=8)
        ttk.Button(frame, text="Pick", command=self._pick_color).grid(row=3, column=2, padx=(8, 0), pady=8)
        frame.columnconfigure(1, weight=1)

    def _assets_tab(self, notebook: ttk.Notebook) -> None:
        frame = ttk.Frame(notebook, padding=16)
        notebook.add(frame, text="Assets")
        self._path_row(frame, "Backgrounds", self.bg_dir_var, 0, self._choose_bg_dir)
        self._path_row(frame, "Cover", self.cover_var, 1, self._choose_cover)
        ttk.Button(frame, text="Import Plates", command=self._import_plates).grid(row=2, column=1, sticky="w", pady=12)
        frame.columnconfigure(1, weight=1)

    def _rooms_tab(self, notebook: ttk.Notebook) -> None:
        frame = ttk.Frame(notebook, padding=16)
        notebook.add(frame, text="Rooms")
        self.room_tree = ttk.Treeview(frame, columns=("id", "name", "bg"), show="headings", height=18)
        for col, label, width in (("id", "ID", 140), ("name", "Name", 280), ("bg", "Plate", 220)):
            self.room_tree.heading(col, text=label)
            self.room_tree.column(col, width=width, anchor="w")
        self.room_tree.grid(row=0, column=0, columnspan=4, sticky="nsew")
        scroll = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.room_tree.yview)
        scroll.grid(row=0, column=4, sticky="ns")
        self.room_tree.configure(yscrollcommand=scroll.set)
        ttk.Button(frame, text="Add", command=self._add_room).grid(row=1, column=0, sticky="w", pady=10)
        ttk.Button(frame, text="Edit", command=self._edit_room).grid(row=1, column=1, sticky="w", pady=10)
        ttk.Button(frame, text="Delete", command=self._delete_room).grid(row=1, column=2, sticky="w", pady=10)
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)

    def _build_tab(self, notebook: ttk.Notebook) -> None:
        frame = ttk.Frame(notebook, padding=16)
        notebook.add(frame, text="Build")
        self._path_row(frame, "Output", self.output_var, 0, self._choose_output)
        ttk.Checkbutton(frame, text="Validate", variable=self.validate_var).grid(row=1, column=1, sticky="w", pady=8)
        actions = ttk.Frame(frame)
        actions.grid(row=2, column=1, sticky="w", pady=8)
        ttk.Button(actions, text="Save Config", command=self._save_config).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(actions, text="Scaffold", command=self._scaffold).pack(side=tk.LEFT)
        self.log = tk.Text(frame, height=18, wrap=tk.WORD)
        self.log.grid(row=3, column=0, columnspan=3, sticky="nsew", pady=(12, 0))
        frame.rowconfigure(3, weight=1)
        frame.columnconfigure(1, weight=1)

    def _row(self, parent: ttk.Frame, label: str, var: tk.StringVar, row: int) -> None:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=8)
        ttk.Entry(parent, textvariable=var).grid(row=row, column=1, sticky="ew", pady=8)

    def _path_row(self, parent: ttk.Frame, label: str, var: tk.StringVar, row: int, command: Any) -> None:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=8)
        ttk.Entry(parent, textvariable=var).grid(row=row, column=1, sticky="ew", pady=8)
        ttk.Button(parent, text="Browse", command=command).grid(row=row, column=2, padx=(8, 0), pady=8)

    def _pick_color(self) -> None:
        color, value = colorchooser.askcolor(color=self.accent_var.get(), parent=self)
        if value:
            self.accent_var.set(value)

    def _choose_bg_dir(self) -> None:
        path = filedialog.askdirectory(parent=self)
        if path:
            self.bg_dir_var.set(path)

    def _choose_cover(self) -> None:
        path = filedialog.askopenfilename(parent=self, filetypes=[("Images", "*.png *.jpg *.jpeg"), ("All files", "*")])
        if path:
            self.cover_var.set(path)

    def _choose_output(self) -> None:
        path = filedialog.askdirectory(parent=self)
        if path:
            self.output_var.set(path)

    def _import_plates(self) -> None:
        if not self.bg_dir_var.get():
            self._choose_bg_dir()
        bg_dir = Path(self.bg_dir_var.get()).expanduser()
        if not bg_dir.exists():
            messagebox.showerror("Backgrounds", "Background folder not found.", parent=self)
            return
        plates = sorted(bg_dir.glob("*.png"))
        self.rooms = [
            {
                "id": slugify(p.stem),
                "name": titleize_slug(p.stem),
                "desc": titleize_slug(p.stem),
                "bg": slugify(p.stem),
            }
            for p in plates
        ]
        self._refresh_rooms()

    def _add_room(self) -> None:
        room = self._room_dialog()
        if room:
            self.rooms.append(room)
            self._refresh_rooms()

    def _edit_room(self) -> None:
        selected = self.room_tree.selection()
        if not selected:
            return
        index = self.room_tree.index(selected[0])
        room = self._room_dialog(self.rooms[index])
        if room:
            self.rooms[index] = room
            self._refresh_rooms()

    def _delete_room(self) -> None:
        selected = self.room_tree.selection()
        if not selected:
            return
        index = self.room_tree.index(selected[0])
        del self.rooms[index]
        self._refresh_rooms()

    def _room_dialog(self, room: dict[str, str] | None = None) -> dict[str, str] | None:
        dialog = tk.Toplevel(self)
        dialog.title("Room")
        dialog.transient(self)
        dialog.grab_set()
        values = {
            "id": tk.StringVar(value=(room or {}).get("id", "")),
            "name": tk.StringVar(value=(room or {}).get("name", "")),
            "desc": tk.StringVar(value=(room or {}).get("desc", "")),
            "bg": tk.StringVar(value=(room or {}).get("bg", "")),
        }
        for row, key in enumerate(("id", "name", "desc", "bg")):
            ttk.Label(dialog, text=key.title()).grid(row=row, column=0, sticky="w", padx=12, pady=8)
            ttk.Entry(dialog, textvariable=values[key], width=60).grid(row=row, column=1, sticky="ew", padx=12, pady=8)
        result: dict[str, str] | None = None

        def save() -> None:
            nonlocal result
            name = values["name"].get().strip()
            rid = slugify(values["id"].get() or name)
            if not name:
                messagebox.showerror("Room", "Name is required.", parent=dialog)
                return
            result = {
                "id": rid,
                "name": name,
                "desc": values["desc"].get().strip() or name,
                "bg": slugify(values["bg"].get()) if values["bg"].get().strip() else "",
            }
            dialog.destroy()

        buttons = ttk.Frame(dialog)
        buttons.grid(row=4, column=1, sticky="e", padx=12, pady=12)
        ttk.Button(buttons, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(buttons, text="Save", command=save).pack(side=tk.LEFT)
        dialog.columnconfigure(1, weight=1)
        dialog.wait_window()
        return result

    def _refresh_rooms(self) -> None:
        for item in self.room_tree.get_children():
            self.room_tree.delete(item)
        for room in self.rooms:
            self.room_tree.insert("", tk.END, values=(room.get("id", ""), room.get("name", ""), room.get("bg", "")))

    def _build_config(self) -> dict[str, Any]:
        if not self.rooms:
            raise ConfigError("add at least one room")
        assets: dict[str, str] = {}
        if self.bg_dir_var.get():
            assets["backgrounds"] = self.bg_dir_var.get()
        if self.cover_var.get():
            assets["cover"] = self.cover_var.get()
        return {
            "title": self.title_var.get().strip() or "Untitled Adventure",
            "subtitle": self.subtitle_var.get().strip(),
            "dedication": self.dedication_var.get().strip(),
            "accent": self.accent_var.get().strip() or "#37d2c3",
            "assets": assets,
            "chapters": [
                {
                    "id": "chapter_1",
                    "title": "Chapter 1",
                    "pov": "protagonist",
                    "pov_name": "Protagonist",
                    "rooms": [dict(room) for room in self.rooms],
                }
            ],
        }

    def _save_config(self) -> None:
        try:
            config = self._build_config()
            path = filedialog.asksaveasfilename(parent=self, defaultextension=".json", filetypes=[("JSON", "*.json")])
            if not path:
                return
            write_json(path, config)
            self._append_log(f"saved config: {path}")
        except ConfigError as exc:
            messagebox.showerror("Config", str(exc), parent=self)

    def _scaffold(self) -> None:
        try:
            config = self._build_config()
            out = self.output_var.get().strip()
            if not out:
                raise ConfigError("output folder is required")
            project = scaffold_project(
                config,
                out,
                config_dir=Path.cwd(),
                force=False,
                run_validation=self.validate_var.get(),
            )
            self._append_log(f"wrote project: {project}")
        except (ConfigError, ValidationError) as exc:
            self._append_log(str(exc))
            messagebox.showerror("Build", str(exc), parent=self)
        except Exception as exc:  # noqa: BLE001
            detail = traceback.format_exc()
            self._append_log(detail)
            messagebox.showerror("Build", str(exc), parent=self)

    def _append_log(self, text: str) -> None:
        self.log.insert(tk.END, text.rstrip() + "\n")
        self.log.see(tk.END)


def main() -> None:
    app = Wizard()
    app.mainloop()
