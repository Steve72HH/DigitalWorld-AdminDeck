import os
import json
import time
import fnmatch
import shutil
import webbrowser
import subprocess
import threading
import queue
from pathlib import Path
from typing import Optional, Dict, Any, List

import psutil
import customtkinter as ctk
from tkinter import messagebox, ttk

APP_NAME = "Digital World AdminDeck"
APP_VERSION = "4.0.0"

APP_DIR = Path(__file__).resolve().parent
CONFIG_DEFAULT_PATH = APP_DIR / "config.apps.json"
CONFIG_LOCAL_PATH = APP_DIR / "config.local.json"
THEME_PATH = APP_DIR / "assets" / "theme.json"

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


def load_json(path: Path, fallback: Dict[str, Any]) -> Dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return fallback


def write_json(path: Path, data: Dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


THEME = load_json(THEME_PATH, {
    "colors": {
        "background": "#07111f",
        "panel": "#0d1b2e",
        "panel_alt": "#12243b",
        "accent": "#00d4ff",
        "accent_alt": "#6c63ff",
        "success": "#2ee59d",
        "warning": "#ffcc00",
        "danger": "#ff4d6d",
        "text": "#e8f1ff",
        "muted": "#91a4bd"
    }
})
COL = THEME["colors"]


def load_config() -> Dict[str, Any]:
    if CONFIG_LOCAL_PATH.exists():
        return load_json(CONFIG_LOCAL_PATH, {})
    cfg = load_json(CONFIG_DEFAULT_PATH, {})
    if cfg and not CONFIG_LOCAL_PATH.exists():
        # Create a local copy on first run so the public template remains safe.
        try:
            write_json(CONFIG_LOCAL_PATH, cfg)
        except Exception:
            pass
    return cfg


CONFIG = load_config()
RESOLVE_CACHE: Dict[str, Optional[str]] = {}


def expand_path(value: str) -> str:
    return os.path.expandvars(os.path.expanduser(value))


def match_name(filename: str, patterns: List[str]) -> bool:
    low = filename.lower()
    return any(fnmatch.fnmatch(low, pat.lower()) for pat in patterns)


def safe_existing_file(path_str: str) -> Optional[str]:
    expanded = expand_path(path_str)
    p = Path(expanded)
    return str(p) if p.is_file() else None


def limited_walk_find(names: List[str], deep: bool = False) -> Optional[str]:
    settings = CONFIG.get("scan_settings", {})
    max_depth = int(settings.get("max_depth", 4 if not deep else 7))
    max_files_per_root = int(settings.get("max_files_per_root", 8000 if not deep else 30000))
    max_seconds = float(settings.get("max_seconds_per_app", 2.5 if not deep else 8.0))

    started = time.monotonic()
    for root in CONFIG.get("scan_roots", []):
        root_path = Path(expand_path(root))
        if not root_path.exists() or not root_path.is_dir():
            continue

        root_depth = len(root_path.parts)
        files_seen = 0

        try:
            for dirpath, dirnames, filenames in os.walk(root_path, topdown=True):
                if time.monotonic() - started > max_seconds:
                    return None

                current_depth = len(Path(dirpath).parts) - root_depth
                if current_depth >= max_depth:
                    dirnames[:] = []

                skip = {
                    "node_modules", ".git", "$recycle.bin", "system volume information",
                    "__pycache__", ".venv", "venv", "windows", "winsxs"
                }
                dirnames[:] = [d for d in dirnames if d.lower() not in skip and not d.startswith(".")]

                for filename in filenames:
                    files_seen += 1
                    if files_seen > max_files_per_root:
                        break
                    if match_name(filename, names):
                        return str(Path(dirpath) / filename)

                if files_seen > max_files_per_root:
                    break
        except Exception:
            continue
    return None


def resolve_command(app: Dict[str, Any], deep: bool = False) -> Optional[str]:
    key = app.get("name", "") + ("|deep" if deep else "")
    if key in RESOLVE_CACHE:
        return RESOLVE_CACHE[key]

    for cmd in app.get("commands", []):
        direct = safe_existing_file(cmd)
        if direct:
            RESOLVE_CACHE[key] = direct
            return direct

        found = shutil.which(expand_path(cmd))
        if found:
            RESOLVE_CACHE[key] = found
            return found

    search_names = app.get("search_names", [])
    found = limited_walk_find(search_names, deep=deep) if search_names else None
    RESOLVE_CACHE[key] = found
    return found


def winget_available() -> bool:
    return shutil.which("winget") is not None


def install_with_winget(package_id: Optional[str]) -> None:
    if not package_id:
        messagebox.showwarning("Keine Winget-ID", "Für diese Anwendung ist keine Winget-ID hinterlegt.")
        return
    if not winget_available():
        messagebox.showerror("Winget fehlt", "Winget wurde nicht gefunden. Installiere zuerst App Installer aus dem Microsoft Store.")
        return
    if not messagebox.askyesno("Installation bestätigen", f"Soll '{package_id}' per winget installiert werden?"):
        return

    subprocess.Popen([
        "powershell.exe", "-NoExit", "-ExecutionPolicy", "Bypass",
        "-Command", f"winget install --id {package_id} -e --accept-package-agreements --accept-source-agreements"
    ])


def start_elevated_mmc(msc_name: str) -> None:
    ps = f"Start-Process mmc.exe -ArgumentList '{msc_name}' -Verb RunAs"
    subprocess.Popen(["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps])


def launch_app(app: Dict[str, Any]) -> None:
    typ = app.get("type", "app")

    if typ == "url":
        webbrowser.open(app["url"])
        return

    if typ == "msc":
        msc_name = app.get("commands", [""])[0]
        try:
            subprocess.Popen(["mmc.exe", msc_name], shell=False)
        except OSError as exc:
            if getattr(exc, "winerror", None) == 740:
                start_elevated_mmc(msc_name)
            else:
                messagebox.showerror("Startfehler", str(exc))
        except Exception as exc:
            messagebox.showerror("Startfehler", str(exc))
        return

    cmd = resolve_command(app)
    if not cmd:
        install_with_winget(app.get("winget_id"))
        return

    try:
        subprocess.Popen([cmd], shell=False)
    except OSError as exc:
        if getattr(exc, "winerror", None) == 740:
            subprocess.Popen([
                "powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
                "-Command", f"Start-Process -FilePath '{cmd}' -Verb RunAs"
            ])
        else:
            messagebox.showerror("Startfehler", str(exc))
    except Exception as exc:
        messagebox.showerror("Startfehler", str(exc))


def open_ssh(profile: Dict[str, Any]) -> None:
    user = profile.get("user", "root")
    host = profile.get("host", "")
    port = profile.get("port", 22)

    if not host or host == "CHANGE_ME":
        messagebox.showwarning("SSH-Profil unvollständig", "Bitte Host/IP in app\\config.local.json eintragen.")
        return

    ssh_cmd = f"ssh -p {port} {user}@{host}"
    try:
        pwsh = shutil.which("pwsh.exe")
        powershell = shutil.which("powershell.exe") or r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"
        if pwsh:
            subprocess.Popen([pwsh, "-NoExit", "-Command", ssh_cmd], shell=False)
        elif powershell and Path(powershell).exists():
            subprocess.Popen([powershell, "-NoExit", "-Command", ssh_cmd], shell=False)
        else:
            subprocess.Popen(["cmd.exe", "/k", ssh_cmd], shell=False)
    except Exception as exc:
        messagebox.showerror("SSH Fehler", str(exc))


def ping_host(host: str) -> bool:
    if not host or host == "CHANGE_ME":
        return False
    try:
        result = subprocess.run(
            ["ping", "-n", "1", "-w", "1000", host],
            capture_output=True,
            text=True,
            timeout=2
        )
        return result.returncode == 0
    except Exception:
        return False


class Gauge(ctk.CTkFrame):
    def __init__(self, master, title: str, **kwargs):
        super().__init__(master, fg_color=COL["panel_alt"], corner_radius=18, **kwargs)
        self.title = ctk.CTkLabel(self, text=title, font=("Segoe UI", 14, "bold"), text_color=COL["text"])
        self.title.pack(pady=(10, 2))
        self.canvas = ctk.CTkCanvas(self, width=160, height=120, bg=COL["panel_alt"], highlightthickness=0)
        self.canvas.pack(pady=(0, 8))
        self.value_label = ctk.CTkLabel(self, text="0%", font=("Segoe UI", 26, "bold"), text_color=COL["accent"])
        self.value_label.pack(pady=(0, 10))
        self.draw(0)

    def draw(self, value: float):
        value = max(0, min(100, value))
        self.canvas.delete("all")
        x0, y0, x1, y1 = 20, 20, 140, 140
        self.canvas.create_arc(x0, y0, x1, y1, start=180, extent=-180, width=14, style="arc", outline="#243851")
        extent = -180 * (value / 100)
        color = COL["success"] if value < 70 else (COL["warning"] if value < 90 else COL["danger"])
        self.canvas.create_arc(x0, y0, x1, y1, start=180, extent=extent, width=14, style="arc", outline=color)
        import math
        angle = 180 + (180 * value / 100)
        rad = math.radians(angle)
        cx, cy, r = 80, 80, 48
        nx = cx + r * math.cos(rad)
        ny = cy + r * math.sin(rad)
        self.canvas.create_line(cx, cy, nx, ny, width=4, fill=COL["accent"])
        self.canvas.create_oval(cx-5, cy-5, cx+5, cy+5, fill=COL["accent"], outline="")
        self.value_label.configure(text=f"{int(value)}%")


class MonitorWindow(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title(f"{APP_NAME} - Monitor")
        self.geometry("620x260")
        self.configure(fg_color=COL["background"])
        self.cpu = Gauge(self, "CPU")
        self.ram = Gauge(self, "RAM")
        self.gpu = Gauge(self, "GPU")
        self.cpu.grid(row=0, column=0, padx=14, pady=16, sticky="nsew")
        self.ram.grid(row=0, column=1, padx=14, pady=16, sticky="nsew")
        self.gpu.grid(row=0, column=2, padx=14, pady=16, sticky="nsew")
        self.running = True
        self.protocol("WM_DELETE_WINDOW", self.close)
        threading.Thread(target=self.update_loop, daemon=True).start()

    def get_gpu_usage(self) -> float:
        ps_script = """
$counter = Get-Counter '\\GPU Engine(*)\\Utilization Percentage' -ErrorAction SilentlyContinue
if ($counter) {
  ($counter.CounterSamples | Measure-Object CookedValue -Sum).Sum
} else { 0 }
"""
        try:
            out = subprocess.check_output(
                ["powershell.exe", "-NoProfile", "-Command", ps_script],
                stderr=subprocess.DEVNULL,
                timeout=2,
                text=True
            ).strip().replace(",", ".")
            val = float(out) if out else 0
            return max(0, min(100, val))
        except Exception:
            return 0

    def update_loop(self):
        while self.running:
            self.after(0, self.cpu.draw, psutil.cpu_percent(interval=0.5))
            self.after(0, self.ram.draw, psutil.virtual_memory().percent)
            self.after(0, self.gpu.draw, self.get_gpu_usage())
            time.sleep(1)

    def close(self):
        self.running = False
        self.destroy()


class ProcessWindow(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title(f"{APP_NAME} - Prozesse")
        self.geometry("1080x700")
        self.configure(fg_color=COL["background"])

        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", background="#0d1b2e", foreground="#e8f1ff", fieldbackground="#0d1b2e", rowheight=28, font=("Segoe UI", 10))
        style.configure("Treeview.Heading", background="#12243b", foreground="#e8f1ff", font=("Segoe UI", 11, "bold"))
        style.map("Treeview", background=[("selected", "#245b8f")], foreground=[("selected", "#ffffff")])

        top = ctk.CTkFrame(self, fg_color=COL["panel"], corner_radius=16)
        top.pack(fill="x", padx=12, pady=12)

        self.search_var = ctk.StringVar()
        ctk.CTkEntry(top, textvariable=self.search_var, placeholder_text="Prozess suchen...", width=260).pack(side="left", padx=10, pady=10)
        ctk.CTkButton(top, text="Aktualisieren", command=self.refresh).pack(side="left", padx=6)
        ctk.CTkButton(top, text="Top RAM", command=self.show_top_ram).pack(side="left", padx=6)
        ctk.CTkButton(top, text="Top CPU", command=self.show_top_cpu).pack(side="left", padx=6)
        ctk.CTkButton(top, text="Safe Kill", fg_color=COL["danger"], command=self.safe_kill).pack(side="right", padx=10)
        ctk.CTkButton(top, text="Hard Kill", fg_color="#8b0000", command=self.hard_kill).pack(side="right", padx=6)

        table_frame = ctk.CTkFrame(self, fg_color=COL["panel"], corner_radius=16)
        table_frame.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        self.tree = ttk.Treeview(table_frame, columns=("pid", "name", "cpu", "ram", "status"), show="headings")
        for col, label, width, anchor in [
            ("pid", "PID", 90, "center"),
            ("name", "Name", 380, "w"),
            ("cpu", "CPU %", 110, "center"),
            ("ram", "RAM MB", 130, "center"),
            ("status", "Status", 160, "center")
        ]:
            self.tree.heading(col, text=label)
            self.tree.column(col, width=width, anchor=anchor)
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)
        self.refresh()

    def collect_processes(self):
        rows = []
        for p in psutil.process_iter(["pid", "name", "memory_info", "status"]):
            try:
                info = p.info
                rows.append({
                    "pid": info["pid"],
                    "name": info.get("name") or "",
                    "cpu": round(p.cpu_percent(interval=None), 1),
                    "ram": round((info.get("memory_info").rss if info.get("memory_info") else 0) / 1024 / 1024, 1),
                    "status": info.get("status") or ""
                })
            except Exception:
                continue
        return rows

    def render(self, rows):
        needle = self.search_var.get().lower().strip()
        self.tree.delete(*self.tree.get_children())
        for r in rows:
            if needle and needle not in r["name"].lower() and needle not in str(r["pid"]):
                continue
            self.tree.insert("", "end", values=(r["pid"], r["name"], r["cpu"], r["ram"], r["status"]))

    def refresh(self):
        self.render(sorted(self.collect_processes(), key=lambda x: x["name"].lower()))

    def show_top_ram(self):
        self.render(sorted(self.collect_processes(), key=lambda x: x["ram"], reverse=True)[:30])

    def show_top_cpu(self):
        for p in psutil.process_iter():
            try:
                p.cpu_percent(interval=None)
            except Exception:
                pass
        time.sleep(0.3)
        self.render(sorted(self.collect_processes(), key=lambda x: x["cpu"], reverse=True)[:30])

    def selected_pid(self) -> Optional[int]:
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Keine Auswahl", "Bitte zuerst einen Prozess auswählen.")
            return None
        return int(self.tree.item(sel[0])["values"][0])

    def safe_kill(self):
        pid = self.selected_pid()
        if pid is None:
            return
        if not messagebox.askyesno("Prozess beenden", f"Prozess PID {pid} wirklich beenden?"):
            return
        try:
            psutil.Process(pid).terminate()
            time.sleep(0.5)
            self.refresh()
        except Exception as exc:
            messagebox.showerror("Fehler", str(exc))

    def hard_kill(self):
        pid = self.selected_pid()
        if pid is None:
            return
        if not messagebox.askyesno("Hard Kill", f"PID {pid} hart killen? Nicht gespeicherte Daten gehen verloren."):
            return
        try:
            psutil.Process(pid).kill()
            time.sleep(0.5)
            self.refresh()
        except Exception as exc:
            messagebox.showerror("Fehler", str(exc))


class AdminDeck(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(APP_NAME)
        self.geometry("1220x800")
        self.minsize(1080, 720)
        self.configure(fg_color=COL["background"])
        self.deep_mode = False
        self.status_queue: queue.Queue = queue.Queue()
        self.buttons: Dict[str, ctk.CTkButton] = {}

        self.build_layout()
        self.render_apps()
        self.render_ssh()
        self.after(100, self.process_queue)
        self.start_background_discovery(deep=False)

    def build_layout(self):
        header = ctk.CTkFrame(self, fg_color=COL["panel"], corner_radius=0)
        header.pack(fill="x")
        ctk.CTkLabel(header, text=f"{APP_NAME} v{APP_VERSION}", font=("Segoe UI", 28, "bold"), text_color=COL["accent"]).pack(side="left", padx=22, pady=16)
        ctk.CTkLabel(header, text="Standalone Admin Launcher · Monitoring · Prozesskontrolle", font=("Segoe UI", 14), text_color=COL["muted"]).pack(side="left", padx=10)

        tools = ctk.CTkFrame(self, fg_color=COL["background"])
        tools.pack(fill="x", padx=18, pady=12)
        ctk.CTkButton(tools, text="Monitoring-Gauges", command=self.open_monitor, height=38).pack(side="left", padx=6)
        ctk.CTkButton(tools, text="Prozess-Manager", command=self.open_processes, height=38).pack(side="left", padx=6)
        ctk.CTkButton(tools, text="Config öffnen", command=self.open_config, height=38).pack(side="left", padx=6)
        ctk.CTkButton(tools, text="App-Suche neu laden", command=self.reload_search, height=38).pack(side="left", padx=6)
        ctk.CTkButton(tools, text="Tiefensuche starten", command=self.start_deep_search, height=38, fg_color=COL["warning"], text_color="#07111f").pack(side="left", padx=6)

        self.status_label = ctk.CTkLabel(tools, text="Bereit", text_color=COL["muted"])
        self.status_label.pack(side="right", padx=12)

        self.body = ctk.CTkScrollableFrame(self, fg_color=COL["background"])
        self.body.pack(fill="both", expand=True, padx=18, pady=(0, 18))

    def get_categories(self) -> Dict[str, List[Dict[str, Any]]]:
        cats: Dict[str, List[Dict[str, Any]]] = {}
        for app in CONFIG.get("apps", []):
            cats.setdefault(app.get("category", "Sonstiges"), []).append(app)
        return cats

    def render_apps(self):
        self.buttons.clear()
        for cat, items in self.get_categories().items():
            frame = ctk.CTkFrame(self.body, fg_color=COL["panel"], corner_radius=18)
            frame.pack(fill="x", pady=10)
            ctk.CTkLabel(frame, text=cat, font=("Segoe UI", 20, "bold"), text_color=COL["text"]).pack(anchor="w", padx=16, pady=(14, 8))

            grid = ctk.CTkFrame(frame, fg_color=COL["panel"])
            grid.pack(fill="x", padx=12, pady=(0, 14))
            for i, app in enumerate(items):
                status = "Prüfe..." if app.get("type") != "url" else "Öffnen"
                fg = COL["panel_alt"]
                btn = ctk.CTkButton(
                    grid,
                    text=f"{app['name']}\n{status}",
                    height=64,
                    width=230,
                    corner_radius=14,
                    fg_color=fg,
                    hover_color=COL["accent_alt"],
                    command=lambda a=app: launch_app(a)
                )
                btn.grid(row=i // 4, column=i % 4, padx=8, pady=8, sticky="ew")
                self.buttons[app["name"]] = btn

    def render_ssh(self):
        frame = ctk.CTkFrame(self.body, fg_color=COL["panel"], corner_radius=18)
        frame.pack(fill="x", pady=10)
        ctk.CTkLabel(frame, text="SSH Schnellzugriff", font=("Segoe UI", 20, "bold"), text_color=COL["text"]).pack(anchor="w", padx=16, pady=(14, 8))

        grid = ctk.CTkFrame(frame, fg_color=COL["panel"])
        grid.pack(fill="x", padx=12, pady=(0, 14))
        for i, profile in enumerate(CONFIG.get("ssh_profiles", [])):
            host = profile.get("host", "")
            text = f"{profile['name']}\n{profile.get('user')}@{host}:{profile.get('port', 22)}"
            ctk.CTkButton(
                grid,
                text=text,
                height=64,
                width=230,
                corner_radius=14,
                fg_color=COL["panel_alt"],
                hover_color=COL["accent_alt"],
                command=lambda p=profile: open_ssh(p)
            ).grid(row=i // 4, column=i % 4, padx=8, pady=8)

    def update_button(self, app_name: str, found: bool):
        btn = self.buttons.get(app_name)
        if not btn:
            return
        app = next((a for a in CONFIG.get("apps", []) if a.get("name") == app_name), None)
        if not app:
            return

        if app.get("type") == "url":
            text = f"{app_name}\nÖffnen"
            fg = COL["panel_alt"]
        elif found:
            text = f"{app_name}\nStarten"
            fg = COL["panel_alt"]
        else:
            text = f"{app_name}\nNicht gefunden – installieren?"
            fg = "#44243b"

        btn.configure(text=text, fg_color=fg)

    def start_background_discovery(self, deep: bool):
        self.status_label.configure(text="App-Suche läuft...")
        def worker():
            for app in CONFIG.get("apps", []):
                if app.get("type") == "url":
                    self.status_queue.put((app["name"], True))
                    continue
                found = resolve_command(app, deep=deep) is not None
                self.status_queue.put((app["name"], found))
            self.status_queue.put(("__DONE__", True))
        threading.Thread(target=worker, daemon=True).start()

    def process_queue(self):
        try:
            while True:
                app_name, found = self.status_queue.get_nowait()
                if app_name == "__DONE__":
                    self.status_label.configure(text="Bereit")
                else:
                    self.update_button(app_name, found)
        except queue.Empty:
            pass
        self.after(200, self.process_queue)

    def reload_search(self):
        RESOLVE_CACHE.clear()
        self.start_background_discovery(deep=False)

    def start_deep_search(self):
        RESOLVE_CACHE.clear()
        self.start_background_discovery(deep=True)

    def open_monitor(self):
        MonitorWindow(self)

    def open_processes(self):
        ProcessWindow(self)

    def open_config(self):
        target = CONFIG_LOCAL_PATH if CONFIG_LOCAL_PATH.exists() else CONFIG_DEFAULT_PATH
        os.startfile(target)


if __name__ == "__main__":
    try:
        app = AdminDeck()
        app.mainloop()
    except Exception as exc:
        messagebox.showerror("Fataler Fehler", str(exc))
