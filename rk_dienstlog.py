import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import pandas as pd
import re
import os
import sys
import json
import urllib.request
import ssl
try:
    import certifi
except Exception:
    certifi = None
import zipfile
import tempfile
import shutil
import subprocess
import threading
from pathlib import Path
from datetime import datetime, timedelta

# Diagramme
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.dates as mdates

try:
    from PIL import Image, ImageTk
except Exception:
    Image = None
    ImageTk = None

try:
    from AppKit import NSApplication, NSImage
except Exception:
    NSApplication = None
    NSImage = None


def resource_path(relative_path: str) -> str:
    """Pfad für normale Ausführung und PyInstaller-App."""
    try:
        base_path = Path(sys._MEIPASS)  # PyInstaller temporärer Ressourcenordner
    except Exception:
        try:
            base_path = Path(__file__).resolve().parent
        except Exception:
            base_path = Path.cwd()
    return str(base_path / relative_path)

def load_version_info():
    try:
        version_file = Path(resource_path("version.json"))
        if version_file.exists():
            with open(version_file, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass

    return {
        "version": "0.0.0",
        "app_name": "RK DienstLog",
        "bundle_id": "at.rk.dienstlog",
        "update_url": ""
    }


VERSION_INFO = load_version_info()

APP_TITLE = VERSION_INFO.get("app_name", "RK DienstLog")
APP_SUBTITLE = "Dienststunden & Auswertung"
APP_VERSION = VERSION_INFO.get("version", "0.0.0")
APP_BUNDLE_ID = VERSION_INFO.get("bundle_id", "at.rk.dienstlog")
APP_UPDATE_URL = VERSION_INFO.get("update_url", "")

CHANGELOG_TEXT = """RK DienstLog – Changelog

Version 3.0.0
- Neues Feature: Projekt speichern/laden (.rkdienstlog Format – speichert alle Daten, Filter und Theme).
- Speichern (⌘S / Strg+S), Speichern unter (⌘⇧S), Projekt öffnen (⌘O).
- Titelleiste zeigt aktuellen Dateinamen und ungespeicherte Änderungen (•).
- Neues Feature: Dubletten-Dialog – bei Importen werden mögliche Dubletten einzeln prüfbar.
- Neues Feature: Datensätze-Tab mit Beschreibungs-Spalte, Suchleiste und Inline-Bearbeitung.
- Doppelklick auf eine Zelle öffnet eine Eingabe direkt in der Tabelle.
- Rechtsklick auf eine Zeile → Löschen oder Bearbeiten.
- Neues Feature: Analytics-Tab mit KPI-Karten, Jahresvergleich-Chart und GitHub-style Aktivitäts-Heatmap.

Version 2.9.3
- GitHub Actions CI/CD eingerichtet: macOS und Windows Build vollautomatisch.
- Spec-Fix: relativer Icon-Pfad für Build-Kompatibilität.
- rk_dienstlog_icon.png wird jetzt korrekt im App-Bundle mitgeliefert.

Version 2.9.2
- Dubletten-Erkennung beim erweiterten Import verbessert.
- Monatsfilter bleibt abhängig vom gewählten Jahr optimiert.
- Save & Load bleibt als nächster sauberer Umsetzungsschritt vorgemerkt.

Version 2.9.1
- Dubletten-Erkennung beim erweiterten Import verbessert.
- Doppelte Einträge werden nun robuster über Datum, Art, Einheit und Stunden erkannt.
- Monatsfilter zeigt bei ausgewähltem Jahr nur Monate mit vorhandenen Diensten an.

Version 2.8.12
- Portal-Import vorerst wieder entfernt.
- Jahresfilter ergänzt.
- Monatsfilter und Jahresfilter getrennt nutzbar gemacht.
- Import kann bestehende Daten nun ersetzen oder erweitern.
- Beim Erweitern werden doppelte Einträge erkannt und übersprungen.

Version 2.8.8
- Kleine sichtbare Textänderung zum Test des Windows Auto-Updates.
- Untertitel auf „Dienststunden, Auswertung & Update-Test“ geändert.

Version 2.8.7
- Kleine sichtbare Textänderung zum Test des Windows Auto-Updates.
- Untertitel auf „Dienststunden, Auswertung & Updates“ geändert.
- Build-Automatisierung für macOS und Windows vorbereitet.

Version 2.8.6
- Windows Auto-Update ergänzt.
- Windows lädt künftig den aktuellen Installer herunter und startet ihn automatisch.
- Update-Logik unterscheidet nun zwischen macOS ZIP-Update und Windows Installer-Update.

Version 2.8.5
- Auto-Update finalisiert und macOS-App-Bundle-Handling stabilisiert.
- Update-Entpacken erfolgt mit macOS ditto statt Python zipfile.
- Update-Installation nutzt Staging, Backup und Restore bei Fehlern.
- Rechte, Quarantine-Attribute und App-Start werden nach dem Update korrigiert.

Version 2.8.4
- Auto-Update-Entpacken auf macOS ditto umgestellt.
- Fix für beschädigte Python-Framework-Datei nach Update.
- macOS-App-Bundle-Struktur wird beim Update nun korrekt erhalten.

Version 2.8.3
- Auto-Update robuster gemacht.
- Backup/Restore-Mechanismus beim Aktualisieren ergänzt.
- Rechte und Quarantine-Attribute werden nach dem Update korrigiert.

Version 2.8.2
- Update-Script-Fix vorbereitet.

Version 2.8.1
- Menüpunkt „Hilfe → Changelog“ ergänzt.

Version 2.8.0
- Auto-Update für macOS ergänzt.
"""


APP_ICON_PNG = resource_path("rk_dienstlog_icon.png")
APP_ICON_ICO = resource_path("rk_dienstlog_windows_fixed.ico")

def set_macos_dock_icon():
    """Setzt Dock/App-Switcher Icon zur Laufzeit auf macOS."""
    if NSApplication is None or NSImage is None:
        return

    try:
        app = NSApplication.sharedApplication()
        image = NSImage.alloc().initWithContentsOfFile_(APP_ICON_PNG)
        if image:
            app.setApplicationIconImage_(image)
    except Exception:
        pass

def enforce_macos_icon(root=None):
    """Setzt das Icon nur einmal. Kein permanentes Nachsetzen, damit macOS nicht flackert."""
    set_macos_dock_icon()



def set_window_icon(root):
    """Setzt das Fenster-/Taskleistenicon plattformübergreifend."""
    try:
        # Windows: .ico ist für Taskleiste/Fenster am zuverlässigsten
        if os.name == "nt" and Path(APP_ICON_ICO).exists():
            root.iconbitmap(APP_ICON_ICO)
            return
    except Exception:
        pass

    try:
        # macOS/Linux fallback
        if Path(APP_ICON_PNG).exists():
            img = tk.PhotoImage(file=APP_ICON_PNG)
            root.iconphoto(True, img)
            root._window_icon_ref = img
    except Exception:
        pass

APP_DIR = Path.home() / ".rk_dienstlog"
APP_DIR.mkdir(exist_ok=True)
SETTINGS_FILE = APP_DIR / "settings.json"
AUTOSAVE_FILE = APP_DIR / "autosave.csv"
RECENT_FILE = APP_DIR / "recent.json"

ART_OPTIONS = [
    "RKT-FRW",
    "Ausbildungen/Fortbildungen",
    "Sonstiges",
    "Alle"
]


def clean_text(value) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()


def normalize_col(name: str) -> str:
    return str(name).strip().lower().replace(".", "").replace(" ", "")


def find_col(df: pd.DataFrame, names: list[str]) -> str | None:
    mapping = {normalize_col(c): c for c in df.columns}
    for name in names:
        key = normalize_col(name)
        if key in mapping:
            return mapping[key]
    return None


def clean_hours(value) -> float:
    if pd.isna(value):
        return 0.0

    text = str(value).strip().replace(",", ".")
    match = re.search(r"-?\d+(?:\.\d+)?", text)
    if not match:
        return 0.0

    try:
        return float(match.group(0))
    except ValueError:
        return 0.0


def format_hours(value: float) -> str:
    return f"{float(value):.2f}".replace(".", ",")


def format_date(value):
    if pd.isna(value):
        return ""
    try:
        dt = pd.to_datetime(value, dayfirst=True, errors="coerce")
        if pd.isna(dt):
            return str(value)
        return dt.strftime("%d.%m.%Y")
    except Exception:
        return str(value)


def format_month_display(value) -> str:
    """YYYY-MM -> MM/YYYY, Datumswerte ebenfalls -> MM/YYYY."""
    if pd.isna(value):
        return ""

    text = str(value).strip()
    match = re.fullmatch(r"(\d{4})-(\d{2})", text)
    if match:
        return f"{match.group(2)}/{match.group(1)}"

    dt = pd.to_datetime(text, dayfirst=True, errors="coerce")
    if pd.isna(dt):
        return text
    return dt.strftime("%m/%Y")


def month_key_from_display(value) -> str:
    """MM/YYYY -> YYYY-MM."""
    text = str(value).strip()
    match = re.fullmatch(r"(\d{2})/(\d{4})", text)
    if match:
        return f"{match.group(2)}-{match.group(1)}"
    return text


def clean_unit_display(value) -> str:
    """Entfernt den Abteilungszusatz, z.B. 'Zug 11 (Abteilung Salzburg 2)' -> 'Zug 11'."""
    text = clean_text(value)
    text = re.sub(r"\s*\(Abteilung[^)]*\)", "", text).strip()
    return text


def prepare_duplicate_key(row) -> tuple:
    """Robuster Schlüssel zur Erkennung doppelter Einträge.

    Beschreibung wird berücksichtigt, damit legitime gleiche Dienste am
    gleichen Tag nicht fälschlich als doppelt erkannt werden.
    """
    date_value = clean_text(row.get("Datum", ""))
    try:
        dt = pd.to_datetime(date_value, dayfirst=True, errors="coerce")
        if not pd.isna(dt):
            date_value = dt.strftime("%Y-%m-%d")
    except Exception:
        pass

    def norm(value):
        value = clean_text(value).lower().strip()
        value = re.sub(r"\\s+", " ", value)
        value = value.replace("–", "-").replace("—", "-")
        return value

    art = norm(row.get("Art", ""))
    unit = norm(clean_unit_display(row.get("Einheit", "")))
    desc = norm(row.get("Beschreibung", ""))
    hours = round(float(clean_hours(row.get("Std.", 0))), 2)

    return (date_value, art, unit, desc, hours)

def merge_without_duplicates(existing_df: pd.DataFrame, new_df: pd.DataFrame) -> tuple[pd.DataFrame, int, int]:
    """Hängt neue Daten an bestehende an und überspringt Dubletten."""
    if existing_df.empty:
        return new_df.copy(), len(new_df), 0

    existing = existing_df.copy()
    new = new_df.copy()

    existing_keys = set(existing.apply(prepare_duplicate_key, axis=1).tolist())

    rows_to_add = []
    skipped = 0

    for _, row in new.iterrows():
        key = prepare_duplicate_key(row)
        if key in existing_keys:
            skipped += 1
            continue

        existing_keys.add(key)
        rows_to_add.append(row)

    if rows_to_add:
        add_df = pd.DataFrame(rows_to_add, columns=new.columns)
        merged = pd.concat([existing, add_df], ignore_index=True)
    else:
        merged = existing

    # Sicherheit: auch bereits entstandene Dubletten nach gleichem Schlüssel entfernen
    before_final = len(merged)
    merged["_dup_key"] = merged.apply(prepare_duplicate_key, axis=1)
    merged = merged.drop_duplicates(subset=["_dup_key"], keep="first").drop(columns=["_dup_key"])
    skipped += before_final - len(merged)

    # Nummerierung neu setzen, damit # sauber bleibt
    if "#" in merged.columns:
        merged["#"] = range(1, len(merged) + 1)

    return merged.reset_index(drop=True), len(rows_to_add), skipped



def read_input_file(path: str) -> pd.DataFrame:
    ext = Path(path).suffix.lower()

    if ext in [".xlsx", ".xls"]:
        return pd.read_excel(path)

    if ext == ".csv":
        try:
            return pd.read_csv(path, sep=None, engine="python")
        except Exception:
            return pd.read_csv(path, sep=";", engine="python")

    raise ValueError("Bitte eine .xlsx, .xls oder .csv Datei auswählen.")


def normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    art_col = find_col(df, ["Art", "Kategorie"])
    hours_col = find_col(df, ["Std", "Std.", "Stunden", "Hours"])
    date_col = find_col(df, ["Datum", "Date"])
    unit_col = find_col(df, ["Einheit", "Zug", "Unit"])
    desc_col = find_col(df, ["Beschreibung", "Titel / Beschreibung", "Titel", "Description"])
    nr_col = find_col(df, ["#", "Nr", "Nummer"])

    if art_col is None:
        raise ValueError("Spalte 'Art' wurde nicht gefunden.")
    if hours_col is None:
        raise ValueError("Spalte 'Std.' bzw. 'Stunden' wurde nicht gefunden.")

    out = pd.DataFrame()
    out["#"] = df[nr_col] if nr_col else range(1, len(df) + 1)
    out["Datum"] = df[date_col].apply(format_date) if date_col else ""
    out["Art"] = df[art_col].apply(clean_text)
    out["Einheit"] = df[unit_col].apply(clean_unit_display) if unit_col else ""
    out["Beschreibung"] = df[desc_col].apply(clean_text) if desc_col else ""
    out["Std."] = df[hours_col].apply(clean_hours)
    out["*"] = ""

    return out


def parse_pasted_portal_text(text: str) -> pd.DataFrame:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\t", " ")
    text = re.sub(r"[ ]+", " ", text)

    start_pattern = re.compile(r"(?m)^\s*(\d+)\s+(\d{2}\.\d{2}\.\d{4})\s+")
    starts = list(start_pattern.finditer(text))

    rows = []

    for idx, match in enumerate(starts):
        start = match.start()
        end = starts[idx + 1].start() if idx + 1 < len(starts) else len(text)
        block = text[start:end].strip()

        nr = match.group(1)
        date = match.group(2)

        one = " ".join(line.strip() for line in block.splitlines() if line.strip())
        one = re.sub(r"\s+", " ", one).strip()

        if "Gesamt:" in one or "davon " in one:
            continue

        art = ""
        for option in ART_OPTIONS:
            if option == "Alle":
                continue
            if option.lower() in one.lower():
                art = option
                break

        if not art:
            continue

        hours = 0.0
        h_match = re.search(r"automatisiert übernommen\s+(-?\d+(?:[.,]\d+)?)\s*(?:edit)?", one, re.IGNORECASE)
        if not h_match:
            h_match = re.search(r"\s(-?\d+(?:[.,]\d+)?)\s*edit\b", one, re.IGNORECASE)

        if h_match:
            hours = clean_hours(h_match.group(1))

        unit = ""
        unit_match = re.search(
            r"(Zug\s+\d{2}\s*\([^)]+\)|Kolonne Salzburg\s*\([^)]+\)|Ausbildungsakademie\s*\([^)]+\)|Ausbilderzug\s*\([^)]+\))",
            one
        )
        if unit_match:
            unit = unit_match.group(1).strip()
        else:
            try:
                after_art = one.split(art, 1)[1].strip()
                before_auto = after_art.split(" automatisiert übernommen", 1)[0].strip()
                unit = before_auto
            except Exception:
                unit = ""

        description = ""
        if unit and unit in one:
            try:
                after_unit = one.split(unit, 1)[1].strip()
                description = after_unit.split(" automatisiert übernommen", 1)[0].strip()
            except Exception:
                description = ""

        rows.append({
            "#": nr,
            "Datum": date,
            "Art": art,
            "Einheit": clean_unit_display(unit),
            "Beschreibung": description,
            "Std.": hours,
            "*": ""
        })

    return pd.DataFrame(rows, columns=["#", "Datum", "Art", "Einheit", "Beschreibung", "Std.", "*"])


def parse_version(version: str):
    """Vergleicht Versionen wie 2.7.10 korrekt."""
    parts = []
    for part in str(version).split("."):
        try:
            parts.append(int(part))
        except ValueError:
            parts.append(0)

    while len(parts) < 3:
        parts.append(0)

    return tuple(parts)


def is_newer_version(online_version: str, current_version: str) -> bool:
    return parse_version(online_version) > parse_version(current_version)


def get_current_app_bundle() -> Path | None:
    """Ermittelt den Pfad zur aktuell laufenden .app."""
    try:
        exe = Path(sys.executable).resolve()

        # PyInstaller .app:
        # RK DienstLog.app/Contents/MacOS/RK DienstLog
        if exe.parent.name == "MacOS" and exe.parent.parent.name == "Contents":
            return exe.parent.parent.parent

        return None
    except Exception:
        return None



def get_ssl_context():
    """Robuster SSL-Kontext für Windows/PyInstaller/GitHub Downloads."""
    try:
        if certifi is not None:
            return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        pass

    try:
        return ssl.create_default_context()
    except Exception:
        return None


def download_file_secure(url: str, target_path: Path):
    """Lädt Dateien mit explizitem Zertifikats-Kontext herunter."""
    context = get_ssl_context()

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": f"{APP_TITLE}/{APP_VERSION}"
        }
    )

    if context is not None:
        response = urllib.request.urlopen(request, context=context, timeout=60)
    else:
        response = urllib.request.urlopen(request, timeout=60)

    with response:
        with open(target_path, "wb") as f:
            shutil.copyfileobj(response, f)

def save_project_file(path: Path, df: pd.DataFrame, state: dict):
    data = {
        "format_version": 1,
        "app_version": APP_VERSION,
        "saved_at": datetime.now().isoformat(),
        "state": state,
        "records": df.to_dict(orient="records")
    }
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


def load_project_file(path: Path) -> dict:
    raw = json.loads(path.read_text(encoding="utf-8"))
    records = raw.get("records", [])
    state = raw.get("state", {})
    if records:
        df = pd.DataFrame(records)
        df = normalize_dataframe(df)
    else:
        df = pd.DataFrame(columns=["#", "Datum", "Art", "Einheit", "Beschreibung", "Std.", "*"])
    return {"df": df, "state": state}


def find_import_diff(existing_df: pd.DataFrame, new_df: pd.DataFrame):
    """Returns (unique_rows, duplicate_rows) as lists of row dicts from new_df."""
    if existing_df.empty:
        return list(new_df.to_dict(orient="records")), []
    existing_keys = set(existing_df.apply(prepare_duplicate_key, axis=1).tolist())
    unique, duplicates = [], []
    for _, row in new_df.iterrows():
        key = prepare_duplicate_key(row)
        if key in existing_keys:
            duplicates.append(row.to_dict())
        else:
            unique.append(row.to_dict())
    return unique, duplicates


class DuplicateReviewDialog(ctk.CTkToplevel):
    """Shows possible duplicate rows; user picks which to import."""

    def __init__(self, parent, duplicates: list, callback):
        super().__init__(parent)
        self.duplicates = duplicates
        self.callback = callback
        self.selected = [False] * len(duplicates)

        self.title("Mögliche Dubletten prüfen")
        self.geometry("1100x620")
        self.minsize(900, 480)
        self.transient(parent)
        self.grab_set()
        self.bind("<Escape>", lambda e: self._skip_all())

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(self, text="Mögliche Dubletten prüfen",
                     font=ctk.CTkFont(size=22, weight="bold")).grid(
            row=0, column=0, sticky="w", padx=24, pady=(20, 4))

        ctk.CTkLabel(
            self,
            text=(f"{len(duplicates)} Einträge wurden als mögliche Dubletten erkannt. "
                  "Wähle aus, welche du trotzdem importieren möchtest (Standard: keine). "
                  "Klick auf eine Zeile zum Umschalten, Klick auf ✓ in der Kopfzeile zum Alle/Keine."),
            wraplength=1060,
            text_color="#AAB2C0",
            justify="left"
        ).grid(row=1, column=0, sticky="ew", padx=24, pady=(0, 10))

        tree_frame = ctk.CTkFrame(self, fg_color="transparent")
        tree_frame.grid(row=2, column=0, sticky="nsew", padx=24, pady=(0, 10))
        tree_frame.grid_columnconfigure(0, weight=1)
        tree_frame.grid_rowconfigure(0, weight=1)

        columns = ["✓", "#", "Datum", "Art", "Einheit", "Beschreibung", "Std."]
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings")
        widths = {"✓": 40, "#": 50, "Datum": 110, "Art": 170,
                  "Einheit": 220, "Beschreibung": 300, "Std.": 75}
        for col in columns:
            if col == "✓":
                self.tree.heading(col, text="✓", command=self._toggle_all)
            else:
                self.tree.heading(col, text=col)
            anchor = "w" if col in ("Art", "Einheit", "Beschreibung") else "center"
            self.tree.column(col, width=widths.get(col, 120), anchor=anchor)

        yscroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        xscroll = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        yscroll.grid(row=0, column=1, sticky="ns")
        xscroll.grid(row=1, column=0, sticky="ew")
        self.tree.bind("<ButtonRelease-1>", self._on_click)

        self._item_ids = []
        for row in duplicates:
            iid = self.tree.insert("", "end", values=(
                "☐",
                clean_text(row.get("#", "")),
                clean_text(row.get("Datum", "")),
                clean_text(row.get("Art", "")),
                clean_text(row.get("Einheit", "")),
                clean_text(row.get("Beschreibung", "")),
                format_hours(row.get("Std.", 0)),
            ))
            self._item_ids.append(iid)

        btns = ctk.CTkFrame(self, fg_color="transparent")
        btns.grid(row=3, column=0, sticky="ew", padx=24, pady=(0, 20))
        btns.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(btns, text="Auswahl importieren", command=self._confirm,
                      fg_color="#2FA572", hover_color="#278B60", width=200).grid(
            row=0, column=0, padx=(0, 12))
        ctk.CTkLabel(btns, text="Klick auf Zeile = auswählen/abwählen",
                     text_color="#AAB2C0").grid(row=0, column=1, sticky="w")
        ctk.CTkButton(btns, text="Alle hinzufügen", command=self._add_all,
                      width=140).grid(row=0, column=2, padx=12)
        ctk.CTkButton(btns, text="Alle überspringen", command=self._skip_all,
                      fg_color="#555B66", hover_color="#464B54", width=140).grid(
            row=0, column=3)

    def _on_click(self, event):
        row_id = self.tree.identify_row(event.y)
        if not row_id or row_id not in self._item_ids:
            return
        idx = self._item_ids.index(row_id)
        self.selected[idx] = not self.selected[idx]
        values = list(self.tree.item(row_id, "values"))
        values[0] = "☑" if self.selected[idx] else "☐"
        self.tree.item(row_id, values=values)

    def _toggle_all(self):
        new_state = not any(self.selected)
        for i, iid in enumerate(self._item_ids):
            self.selected[i] = new_state
            values = list(self.tree.item(iid, "values"))
            values[0] = "☑" if new_state else "☐"
            self.tree.item(iid, values=values)

    def _confirm(self):
        rows_to_add = [self.duplicates[i] for i, s in enumerate(self.selected) if s]
        self.callback(rows_to_add)
        self.destroy()

    def _add_all(self):
        self.callback(self.duplicates)
        self.destroy()

    def _skip_all(self):
        self.callback([])
        self.destroy()


class PasteDialog(ctk.CTkToplevel):
    def __init__(self, parent, callback):
        super().__init__(parent)
        self.callback = callback
        self.preview_df = pd.DataFrame(columns=["#", "Datum", "Art", "Einheit", "Beschreibung", "Std.", "*"])

        self.title("Copy/Paste aus Webportal")
        self.geometry("1180x760")
        self.transient(parent)
        self.grab_set()

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=2)
        self.grid_rowconfigure(5, weight=3)

        title = ctk.CTkLabel(self, text="Webportal-Daten einfügen", font=ctk.CTkFont(size=24, weight="bold"))
        title.grid(row=0, column=0, padx=24, pady=(22, 6), sticky="w")

        info = ctk.CTkLabel(
            self,
            text="Einfügen wie gewohnt aus dem Portal. Darunter siehst du sofort eine Excel-ähnliche Vorschau.",
            text_color="#AAB2C0"
        )
        info.grid(row=1, column=0, padx=24, pady=(0, 12), sticky="w")

        raw_label = ctk.CTkLabel(self, text="Rohdaten / Einfügen", font=ctk.CTkFont(size=14, weight="bold"))
        raw_label.grid(row=2, column=0, padx=24, pady=(0, 4), sticky="w")

        self.textbox = ctk.CTkTextbox(self, font=("Consolas", 13), wrap="none")
        self.textbox.grid(row=3, column=0, padx=24, pady=(0, 12), sticky="nsew")
        self.textbox.bind("<KeyRelease>", lambda event: self.update_preview_silent())
        self.bind("<Escape>", lambda event: self.destroy())

        preview_label = ctk.CTkLabel(self, text="Vorschau / erkannte Tabelle", font=ctk.CTkFont(size=14, weight="bold"))
        preview_label.grid(row=4, column=0, padx=24, pady=(0, 4), sticky="w")

        self.preview_tree = self.create_preview_tree()
        self.preview_tree.grid(row=5, column=0, padx=24, pady=(0, 14), sticky="nsew")

        btns = ctk.CTkFrame(self, fg_color="transparent")
        btns.grid(row=6, column=0, padx=24, pady=(0, 20), sticky="ew")
        btns.grid_columnconfigure(0, weight=1)

        ctk.CTkButton(btns, text="Aus Zwischenablage einfügen", command=self.paste_clipboard).grid(row=0, column=0, padx=(0, 10), sticky="w")
        ctk.CTkButton(btns, text="Vorschau aktualisieren", command=self.update_preview).grid(row=0, column=1, padx=10)
        ctk.CTkButton(btns, text="Übernehmen & auswerten", command=self.apply, fg_color="#2FA572", hover_color="#278B60").grid(row=0, column=2, padx=10)
        ctk.CTkButton(btns, text="Abbrechen", command=self.destroy, fg_color="#555B66", hover_color="#464B54").grid(row=0, column=3, padx=(10, 0))

    def create_preview_tree(self):
        wrapper = ctk.CTkFrame(self, fg_color="transparent")
        wrapper.grid_columnconfigure(0, weight=1)
        wrapper.grid_rowconfigure(0, weight=1)

        columns = ["#", "Datum", "Art", "Einheit", "Beschreibung", "Std.", "*"]
        tree = ttk.Treeview(wrapper, columns=columns, show="headings")

        widths = {"#": 55, "Datum": 110, "Art": 190, "Einheit": 280, "Beschreibung": 360, "Std.": 80, "*": 55}

        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=widths.get(col, 140), anchor="w")

        yscroll = ttk.Scrollbar(wrapper, orient="vertical", command=tree.yview)
        xscroll = ttk.Scrollbar(wrapper, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)

        tree.grid(row=0, column=0, sticky="nsew")
        yscroll.grid(row=0, column=1, sticky="ns")
        xscroll.grid(row=1, column=0, sticky="ew")

        wrapper.tree = tree
        return wrapper

    def clear_preview(self):
        tree = self.preview_tree.tree
        for item in tree.get_children():
            tree.delete(item)

    def fill_preview(self, df: pd.DataFrame):
        self.clear_preview()
        tree = self.preview_tree.tree

        for _, row in df.iterrows():
            tree.insert("", "end", values=(
                clean_text(row.get("#", "")),
                clean_text(row.get("Datum", "")),
                clean_text(row.get("Art", "")),
                clean_text(row.get("Einheit", "")),
                clean_text(row.get("Beschreibung", "")),
                format_hours(row.get("Std.", 0)),
                clean_text(row.get("*", "")),
            ))

    def paste_clipboard(self):
        try:
            data = self.clipboard_get()
            self.textbox.delete("1.0", "end")
            self.textbox.insert("1.0", data)
            self.update_preview()
        except Exception:
            messagebox.showwarning("Zwischenablage leer", "Ich konnte nichts aus der Zwischenablage lesen.")

    def update_preview_silent(self):
        text = self.textbox.get("1.0", "end").strip()
        if not text:
            self.preview_df = pd.DataFrame(columns=["#", "Datum", "Art", "Einheit", "Beschreibung", "Std.", "*"])
            self.clear_preview()
            return

        try:
            df = parse_pasted_portal_text(text)
            if not df.empty:
                self.preview_df = df
                self.fill_preview(df)
        except Exception:
            pass

    def update_preview(self):
        text = self.textbox.get("1.0", "end").strip()
        if not text:
            messagebox.showwarning("Keine Daten", "Bitte zuerst Daten einfügen.")
            return

        try:
            df = parse_pasted_portal_text(text)
            if df.empty:
                raise ValueError("Keine Einträge erkannt. Bitte kopiere die Tabelle inklusive Datum, Art und Std. aus dem Portal.")
            self.preview_df = df
            self.fill_preview(df)
        except Exception as e:
            messagebox.showerror("Fehler beim Einlesen", str(e))

    def apply(self):
        text = self.textbox.get("1.0", "end").strip()
        if not text:
            messagebox.showwarning("Keine Daten", "Bitte zuerst Daten einfügen.")
            return

        try:
            if self.preview_df.empty:
                self.preview_df = parse_pasted_portal_text(text)

            if self.preview_df.empty:
                raise ValueError("Keine Einträge erkannt. Bitte kopiere die Tabelle inklusive Datum, Art und Std. aus dem Portal.")

            self.callback(self.preview_df, "Copy/Paste Webportal")
            self.destroy()
        except Exception as e:
            messagebox.showerror("Fehler beim Einlesen", str(e))


class ExportDialog(ctk.CTkToplevel):
    def __init__(self, parent, export_callback, available_months=None):
        super().__init__(parent)
        self.export_callback = export_callback
        self.calendar_months = available_months or []

        self.title("Export")
        self.geometry("560x620")
        self.minsize(520, 520)
        self.transient(parent)
        self.grab_set()

        self.export_scope = ctk.StringVar(value="Gefilterte Daten")
        self.export_data = ctk.BooleanVar(value=True)
        self.export_months = ctk.BooleanVar(value=True)
        self.export_units = ctk.BooleanVar(value=True)
        self.export_chart = ctk.BooleanVar(value=True)
        self.export_calendar = ctk.BooleanVar(value=True)
        self.month_vars = {}

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.scroll = ctk.CTkScrollableFrame(self)
        self.scroll.grid(row=0, column=0, sticky="nsew")
        self.scroll.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self.scroll,
            text="Export",
            font=ctk.CTkFont(size=24, weight="bold")
        ).grid(row=0, column=0, sticky="w", padx=24, pady=(24, 10))

        ctk.CTkLabel(self.scroll, text="Umfang", text_color="#AAB2C0").grid(row=1, column=0, sticky="w", padx=24, pady=(8, 4))

        ctk.CTkSegmentedButton(
            self.scroll,
            values=["Gefilterte Daten", "Alle Daten"],
            variable=self.export_scope
        ).grid(row=2, column=0, sticky="w", padx=24, pady=(0, 14))

        ctk.CTkLabel(self.scroll, text="Inhalt", text_color="#AAB2C0").grid(row=3, column=0, sticky="w", padx=24, pady=(8, 4))

        ctk.CTkCheckBox(self.scroll, text="Datensätze / Stunden", variable=self.export_data).grid(row=4, column=0, sticky="w", padx=24, pady=7)
        ctk.CTkCheckBox(self.scroll, text="Monatsübersicht", variable=self.export_months).grid(row=5, column=0, sticky="w", padx=24, pady=7)
        ctk.CTkCheckBox(self.scroll, text="Zug-/Einheitübersicht", variable=self.export_units).grid(row=6, column=0, sticky="w", padx=24, pady=7)
        ctk.CTkCheckBox(self.scroll, text="Aktuelle Grafik als PNG", variable=self.export_chart).grid(row=7, column=0, sticky="w", padx=24, pady=7)

        self.calendar_checkbox = ctk.CTkCheckBox(
            self.scroll,
            text="Kalenderansicht als PNG",
            variable=self.export_calendar,
            command=self.toggle_calendar_options
        )
        self.calendar_checkbox.grid(row=8, column=0, sticky="w", padx=24, pady=7)

        self.calendar_options_frame = ctk.CTkFrame(self.scroll, fg_color="transparent")
        self.calendar_options_frame.grid(row=9, column=0, sticky="ew", padx=0, pady=0)
        self.calendar_options_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self.calendar_options_frame,
            text="Kalender-Monate für PNG Export",
            text_color="#AAB2C0"
        ).grid(row=0, column=0, sticky="w", padx=24, pady=(16, 4))

        self.month_box = ctk.CTkScrollableFrame(self.calendar_options_frame, height=170)
        self.month_box.grid(row=1, column=0, sticky="ew", padx=24, pady=(0, 8))
        self.month_box.grid_columnconfigure(0, weight=1)

        for idx, month in enumerate(self.calendar_months):
            var = ctk.BooleanVar(value=False)
            self.month_vars[month] = var
            cb = ctk.CTkCheckBox(self.month_box, text=month, variable=var)
            cb.grid(row=idx, column=0, sticky="w", padx=8, pady=4)

        if self.calendar_months:
            self.month_vars[self.calendar_months[0]].set(True)

        info = ctk.CTkLabel(
            self.scroll,
            text="Excel bekommt je nach Auswahl mehrere Tabellenblätter. Grafiken werden als separate PNG-Dateien gespeichert.",
            text_color="#AAB2C0",
            wraplength=460,
            justify="left"
        )
        info.grid(row=10, column=0, sticky="w", padx=24, pady=(18, 10))

        btns = ctk.CTkFrame(self.scroll, fg_color="transparent")
        btns.grid(row=11, column=0, sticky="ew", padx=24, pady=(18, 28))
        btns.grid_columnconfigure(0, weight=1)

        ctk.CTkButton(
            btns,
            text="Exportieren",
            command=self.apply,
            fg_color="#2FA572",
            hover_color="#278B60"
        ).grid(row=0, column=1, padx=8)

        ctk.CTkButton(
            btns,
            text="Abbrechen",
            command=self.destroy,
            fg_color="#555B66",
            hover_color="#464B54"
        ).grid(row=0, column=2, padx=(8, 0))

        self.toggle_calendar_options()

        # Wichtig: bind_all, weil CustomTkinter interne Canvas-Widgets sonst das Mausrad schlucken.
        self.bind_all("<MouseWheel>", self.on_mousewheel, add="+")   # macOS / Windows
        self.bind_all("<Button-4>", self.on_mousewheel, add="+")     # Linux
        self.bind_all("<Button-5>", self.on_mousewheel, add="+")     # Linux

        self.bind("<Escape>", lambda event: self.close())
        self.protocol("WM_DELETE_WINDOW", self.close)

    def close(self):
        self.unbind_all("<MouseWheel>")
        self.unbind_all("<Button-4>")
        self.unbind_all("<Button-5>")
        self.destroy()

    def toggle_calendar_options(self):
        if self.export_calendar.get():
            self.calendar_options_frame.grid()
        else:
            self.calendar_options_frame.grid_remove()

    def _is_child_of(self, widget, parent):
        current = widget
        while current is not None:
            if current == parent:
                return True
            current = getattr(current, "master", None)
        return False

    def on_mousewheel(self, event):
        # Nur reagieren, wenn die Maus wirklich über diesem Export-Dialog ist.
        target = self.winfo_containing(event.x_root, event.y_root)
        if target is None or not self._is_child_of(target, self):
            return

        # Wenn Maus über Monatsliste ist UND diese sichtbar ist -> Monatsliste scrollen.
        month_visible = self.export_calendar.get()
        if month_visible and self._is_child_of(target, self.month_box):
            canvas = self.month_box._parent_canvas
        else:
            canvas = self.scroll._parent_canvas

        if event.num == 4:
            canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            canvas.yview_scroll(1, "units")
        else:
            delta = event.delta

            # macOS liefert oft sehr kleine Werte, Windows meist 120er.
            if delta == 0:
                return "break"

            if abs(delta) < 120:
                units = -3 if delta > 0 else 3
            else:
                units = int(-1 * (delta / 120))

            canvas.yview_scroll(units, "units")

        return "break"

    def apply(self):
        options = {
            "scope": self.export_scope.get(),
            "data": self.export_data.get(),
            "months": self.export_months.get(),
            "units": self.export_units.get(),
            "chart": self.export_chart.get(),
            "calendar": self.export_calendar.get(),
            "calendar_months": [month for month, var in self.month_vars.items() if var.get()],
        }
        self.export_callback(options)
        self.close()



class SplashScreen(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)

        self.overrideredirect(True)
        self.attributes("-topmost", True)
        set_window_icon(self)

        width = 380
        height = 380

        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()

        x = int((screen_w - width) / 2)
        y = int((screen_h - height) / 2)

        self.geometry(f"{width}x{height}+{x}+{y}")

        container = ctk.CTkFrame(self, corner_radius=26)
        container.pack(fill="both", expand=True, padx=18, pady=18)

        self.icon_image = None
        if Path(APP_ICON_PNG).exists():
            try:
                if Image is not None and ImageTk is not None:
                    img = Image.open(APP_ICON_PNG).convert("RGBA")
                    img.thumbnail((190, 190), Image.LANCZOS)
                    self.icon_image = ImageTk.PhotoImage(img)
                else:
                    self.icon_image = tk.PhotoImage(file=APP_ICON_PNG)

                icon_label = ctk.CTkLabel(container, image=self.icon_image, text="")
                icon_label.pack(pady=(34, 16))
            except Exception:
                ctk.CTkLabel(container, text="✚", text_color="#D71920", font=ctk.CTkFont(size=86, weight="bold")).pack(pady=(42, 16))
        else:
            ctk.CTkLabel(container, text="✚", text_color="#D71920", font=ctk.CTkFont(size=86, weight="bold")).pack(pady=(42, 16))

        ctk.CTkLabel(container, text=APP_TITLE, font=ctk.CTkFont(size=28, weight="bold")).pack(pady=(4, 4))
        ctk.CTkLabel(container, text=APP_SUBTITLE, text_color="#AAB2C0", font=ctk.CTkFont(size=14)).pack(pady=(0, 8))
        ctk.CTkLabel(container, text=f"Version {APP_VERSION}", text_color="#AAB2C0", font=ctk.CTkFont(size=13)).pack(pady=(0, 18))

        self.progress = ctk.CTkProgressBar(container, width=230)
        self.progress.pack(pady=(0, 12))
        self.progress.set(0.25)

        self.status = ctk.CTkLabel(container, text="Wird geladen …", text_color="#AAB2C0")
        self.status.pack()

        self.after(180, lambda: self.progress.set(0.55))
        self.after(420, lambda: self.progress.set(0.85))


class RktApp(ctk.CTk):
    def __init__(self):
        self.settings = self.load_settings()
        initial_theme = self.settings.get("theme", "Dark")

        ctk.set_appearance_mode(initial_theme.lower())
        ctk.set_default_color_theme("blue")

        super().__init__()
        self.withdraw()
        try:
            self.tk.call("tk", "appname", APP_TITLE)
            self.tk.call("set", "tk_patchLevel", APP_VERSION)
        except Exception:
            pass

        set_macos_dock_icon()

        self.title(APP_TITLE)
        set_window_icon(self)
        self.geometry(self.settings.get("geometry", "1320x860"))
        self.minsize(1160, 740)

        self.df_all = pd.DataFrame(columns=["#", "Datum", "Art", "Einheit", "Beschreibung", "Std.", "*"])
        self.filter_var = ctk.StringVar(value=self.settings.get("filter_art", "RKT-FRW"))
        self.year_filter_var = ctk.StringVar(value=self.settings.get("filter_year", "Alle"))
        self.month_filter_var = ctk.StringVar(value=self.settings.get("filter_month", "Alle"))
        self.unit_filter_var = ctk.StringVar(value=self.settings.get("filter_unit", "Alle"))
        self.theme_var = ctk.StringVar(value=initial_theme)
        self.source_name = "Keine Daten geladen"
        self.tree_sort_reverse = {}
        self.current_chart_mode = self.settings.get("chart_mode", "Monat")
        self.chart_canvas = None
        self.current_figure = None
        self.calendar_figure = None
        self.hover_annotation = None
        self.hover_artists = []
        self._project_file = None
        self._dirty = False
        self._rows_search_var = ctk.StringVar()
        self._heatmap_year_var = ctk.StringVar()

        self.create_ui()
        self.setup_macos_menu()
        self.bind_shortcuts()
        self.load_autosave()

        # Automatische Update-Prüfung kurz nach dem Start
        self.after(2500, lambda: self.check_for_updates(silent=True))

        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def load_settings(self):
        if SETTINGS_FILE.exists():
            try:
                return json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
            except Exception:
                return {}
        return {}

    def save_settings(self):
        settings = {
            "theme": self.theme_var.get(),
            "filter_art": self.filter_var.get(),
            "filter_year": self.year_filter_var.get(),
            "filter_month": self.month_filter_var.get(),
            "filter_unit": self.unit_filter_var.get(),
            "chart_mode": self.current_chart_mode,
            "geometry": self.geometry(),
        }
        try:
            SETTINGS_FILE.write_text(json.dumps(settings, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass

    def autosave_data(self):
        try:
            if self.df_all.empty:
                if AUTOSAVE_FILE.exists():
                    AUTOSAVE_FILE.unlink()
            else:
                self.df_all.to_csv(AUTOSAVE_FILE, index=False, sep=";")
        except Exception:
            pass

    def load_autosave(self):
        if AUTOSAVE_FILE.exists():
            try:
                df = pd.read_csv(AUTOSAVE_FILE, sep=";")
                df = normalize_dataframe(df)
                self.df_all = df
                self.source_name = f"Quelle:\nAuto-Speicher\n\nDatensätze:\n{len(self.df_all)}"
                self.source_label.configure(text=self.source_name)
                self.update_filter_options()
                self.refresh_views()
                self.set_status("Auto-Speicher geladen")
            except Exception:
                self.set_status("Auto-Speicher konnte nicht geladen werden")

    def bind_shortcuts(self):
        self.bind_all("<Command-o>", lambda e: self.load_project())
        self.bind_all("<Control-o>", lambda e: self.load_project())
        self.bind_all("<Command-i>", lambda e: self.load_file())
        self.bind_all("<Control-i>", lambda e: self.load_file())
        self.bind_all("<Command-s>", lambda e: self.save_project())
        self.bind_all("<Control-s>", lambda e: self.save_project())
        self.bind_all("<Command-S>", lambda e: self.save_project_as())
        self.bind_all("<Control-S>", lambda e: self.save_project_as())
        self.bind_all("<Command-v>", lambda e: self.open_paste_dialog())
        self.bind_all("<Control-v>", lambda e: self.open_paste_dialog())
        self.bind_all("<Command-e>", lambda e: self.open_export_dialog())
        self.bind_all("<Control-e>", lambda e: self.open_export_dialog())
        self.bind_all("<Command-l>", lambda e: self.toggle_theme())
        self.bind_all("<Control-l>", lambda e: self.toggle_theme())

    def create_ui(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        sidebar = ctk.CTkFrame(self, width=280, corner_radius=0)
        sidebar.grid(row=0, column=0, sticky="nsw")
        sidebar.grid_rowconfigure(18, weight=1)

        ctk.CTkLabel(sidebar, text="RK DienstLog", font=ctk.CTkFont(size=26, weight="bold")).grid(row=0, column=0, padx=24, pady=(28, 8), sticky="w")
        ctk.CTkLabel(sidebar, text=APP_SUBTITLE, text_color="#AAB2C0").grid(row=1, column=0, padx=24, pady=(0, 14), sticky="w")

        ctk.CTkButton(sidebar, text="Projekt öffnen  ⌘O", command=self.load_project, height=38).grid(row=2, column=0, padx=22, pady=(0, 4), sticky="ew")
        ctk.CTkButton(sidebar, text="Speichern  ⌘S", command=self.save_project, height=38, fg_color="#2FA572", hover_color="#278B60").grid(row=3, column=0, padx=22, pady=4, sticky="ew")

        ctk.CTkLabel(sidebar, text="Importieren", text_color="#AAB2C0").grid(row=4, column=0, padx=24, pady=(10, 2), sticky="w")
        ctk.CTkButton(sidebar, text="CSV / Excel laden", command=self.load_file, height=38).grid(row=5, column=0, padx=22, pady=4, sticky="ew")
        ctk.CTkButton(sidebar, text="Copy/Paste öffnen", command=self.open_paste_dialog, height=38).grid(row=6, column=0, padx=22, pady=4, sticky="ew")
        ctk.CTkButton(sidebar, text="Export", command=self.open_export_dialog, height=38).grid(row=7, column=0, padx=22, pady=4, sticky="ew")
        ctk.CTkButton(sidebar, text="Daten löschen", command=self.clear_data, height=38, fg_color="#555B66", hover_color="#464B54").grid(row=8, column=0, padx=22, pady=(4, 2), sticky="ew")

        ctk.CTkLabel(sidebar, text="Filter", font=ctk.CTkFont(size=16, weight="bold")).grid(row=9, column=0, padx=24, pady=(16, 6), sticky="w")

        ctk.CTkLabel(sidebar, text="Art", text_color="#AAB2C0").grid(row=10, column=0, padx=24, pady=(2, 2), sticky="w")
        self.filter_dropdown = ctk.CTkOptionMenu(sidebar, values=ART_OPTIONS, variable=self.filter_var, command=lambda _: self.refresh_views())
        self.filter_dropdown.grid(row=11, column=0, padx=22, pady=(0, 6), sticky="ew")

        ctk.CTkLabel(sidebar, text="Jahr", text_color="#AAB2C0").grid(row=12, column=0, padx=24, pady=(2, 2), sticky="w")
        self.year_dropdown = ctk.CTkOptionMenu(sidebar, values=["Alle"], variable=self.year_filter_var, command=lambda _: self.refresh_views())
        self.year_dropdown.grid(row=13, column=0, padx=22, pady=(0, 6), sticky="ew")

        ctk.CTkLabel(sidebar, text="Monat", text_color="#AAB2C0").grid(row=14, column=0, padx=24, pady=(2, 2), sticky="w")
        self.month_dropdown = ctk.CTkOptionMenu(sidebar, values=["Alle"], variable=self.month_filter_var, command=lambda _: self.refresh_views())
        self.month_dropdown.grid(row=15, column=0, padx=22, pady=(0, 6), sticky="ew")

        ctk.CTkLabel(sidebar, text="Zug / Einheit", text_color="#AAB2C0").grid(row=16, column=0, padx=24, pady=(2, 2), sticky="w")
        self.unit_dropdown = ctk.CTkOptionMenu(sidebar, values=["Alle"], variable=self.unit_filter_var, command=lambda _: self.refresh_views())
        self.unit_dropdown.grid(row=17, column=0, padx=22, pady=(0, 6), sticky="ew")

        ctk.CTkButton(sidebar, text="Filter zurücksetzen", command=self.reset_filters, height=34, fg_color="#3A3F47", hover_color="#4A505A").grid(row=18, column=0, padx=22, pady=(4, 10), sticky="ew")

        ctk.CTkLabel(sidebar, text="Darstellung", text_color="#AAB2C0").grid(row=19, column=0, padx=24, pady=(4, 2), sticky="w")
        self.theme_switch = ctk.CTkSegmentedButton(sidebar, values=["Dark", "Light"], variable=self.theme_var, command=self.change_theme)
        self.theme_switch.grid(row=20, column=0, padx=22, pady=(0, 8), sticky="ew")

        self.source_label = ctk.CTkLabel(sidebar, text=self.source_name, text_color="#AAB2C0", wraplength=230, justify="left")
        self.source_label.grid(row=21, column=0, padx=24, pady=(10, 28), sticky="sw")

        main = ctk.CTkFrame(self, fg_color="transparent")
        main.grid(row=0, column=1, sticky="nsew", padx=24, pady=24)
        main.grid_columnconfigure((0, 1, 2), weight=1)
        main.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(main, text="Auswertung", font=ctk.CTkFont(size=30, weight="bold")).grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 16))

        self.card_total = self.create_stat_card(main, "Gesamtstunden", "0,00 h")
        self.card_total.grid(row=1, column=0, padx=(0, 12), pady=(0, 18), sticky="ew")

        self.card_count = self.create_stat_card(main, "Dienste", "0")
        self.card_count.grid(row=1, column=1, padx=12, pady=(0, 18), sticky="ew")

        self.card_avg = self.create_stat_card(main, "Ø pro Eintrag", "0,00 h")
        self.card_avg.grid(row=1, column=2, padx=(12, 0), pady=(0, 18), sticky="ew")

        content = ctk.CTkFrame(main)
        content.grid(row=2, column=0, columnspan=3, sticky="nsew")
        content.grid_columnconfigure(0, weight=1)
        content.grid_rowconfigure(0, weight=1)

        self.tabs = ctk.CTkTabview(content)
        self.tabs.grid(row=0, column=0, padx=14, pady=14, sticky="nsew")

        self.tab_summary = self.tabs.add("Übersicht")
        self.tab_chart = self.tabs.add("Grafik")
        self.tab_calendar = self.tabs.add("Kalender")
        self.tab_month = self.tabs.add("Monatsübersicht")
        self.tab_unit = self.tabs.add("Zug / Einheit")
        self.tab_rows = self.tabs.add("Datensätze")
        self.tab_analytics = self.tabs.add("Analytics")

        for tab in [self.tab_summary, self.tab_chart, self.tab_calendar,
                    self.tab_month, self.tab_unit, self.tab_analytics]:
            tab.grid_columnconfigure(0, weight=1)
            tab.grid_rowconfigure(0, weight=1)

        # Datensätze tab: row 0 = search bar, row 1 = tree
        self.tab_rows.grid_columnconfigure(0, weight=1)
        self.tab_rows.grid_rowconfigure(1, weight=1)

        self.summary_box = ctk.CTkTextbox(self.tab_summary, font=("Consolas", 13))
        self.summary_box.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        self.summary_box.configure(state="disabled")

        self.chart_frame = ctk.CTkFrame(self.tab_chart)
        self.chart_frame.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        self.chart_frame.grid_columnconfigure(0, weight=1)
        self.chart_frame.grid_rowconfigure(1, weight=1)

        chart_controls = ctk.CTkFrame(self.chart_frame, fg_color="transparent")
        chart_controls.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        chart_controls.grid_columnconfigure(2, weight=1)

        ctk.CTkLabel(chart_controls, text="Grafik:", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, padx=(0, 8))
        self.chart_mode = ctk.CTkSegmentedButton(chart_controls, values=["Monat", "Verlauf"], command=self.change_chart_mode)
        self.chart_mode.set(self.current_chart_mode)
        self.chart_mode.grid(row=0, column=1, sticky="w")

        self.chart_area = ctk.CTkFrame(self.chart_frame)
        self.chart_area.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.chart_area.grid_columnconfigure(0, weight=1)
        self.chart_area.grid_rowconfigure(0, weight=1)

        self.calendar_frame = ctk.CTkFrame(self.tab_calendar)
        self.calendar_frame.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        self.calendar_frame.grid_columnconfigure(0, weight=1)
        self.calendar_frame.grid_rowconfigure(0, weight=1)

        self.month_tree = self.create_tree(self.tab_month, ["Monat", "Dienste", "Stunden"])
        self.unit_tree = self.create_tree(self.tab_unit, ["Einheit", "Dienste", "Stunden"])

        # Datensätze tab: search bar + tree with Beschreibung column
        search_bar = ctk.CTkFrame(self.tab_rows, fg_color="transparent")
        search_bar.grid(row=0, column=0, sticky="ew", padx=8, pady=(8, 0))
        search_bar.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(search_bar, text="Suche:", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, padx=(0, 8))
        ctk.CTkEntry(search_bar, textvariable=self._rows_search_var,
                     placeholder_text="Filtern nach Datum, Art, Einheit, Beschreibung …").grid(
            row=0, column=1, sticky="ew")
        ctk.CTkButton(search_bar, text="✕", width=32, height=28,
                      command=lambda: self._rows_search_var.set("")).grid(row=0, column=2, padx=(6, 0))
        self._rows_search_var.trace_add("write", lambda *_: self._on_rows_search())

        self.rows_tree = self.create_tree(
            self.tab_rows,
            ["#", "Datum", "Art", "Einheit", "Beschreibung", "Std."],
            row=1
        )
        self.rows_tree.bind("<Double-1>", self.on_row_double_click)
        self.rows_tree.bind("<Button-2>", self.on_row_right_click)
        self.rows_tree.bind("<Button-3>", self.on_row_right_click)

        self.month_tree.bind("<Double-1>", self.on_month_double_click)
        self.unit_tree.bind("<Double-1>", self.on_unit_double_click)

        self.status_label = ctk.CTkLabel(main, text="Bereit", text_color="#AAB2C0", anchor="w")
        self.status_label.grid(row=3, column=0, columnspan=3, sticky="ew", pady=(10, 0))

        self.refresh_views()

    def create_stat_card(self, parent, label, value):
        card = ctk.CTkFrame(parent, corner_radius=18)
        card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(card, text=label, text_color="#AAB2C0", font=ctk.CTkFont(size=13)).grid(row=0, column=0, padx=18, pady=(16, 4), sticky="w")
        value_label = ctk.CTkLabel(card, text=value, font=ctk.CTkFont(size=25, weight="bold"))
        value_label.grid(row=1, column=0, padx=18, pady=(0, 16), sticky="w")

        card.value_label = value_label
        return card

    def create_tree(self, parent, columns, row=0):
        wrapper = ctk.CTkFrame(parent, fg_color="transparent")
        wrapper.grid(row=row, column=0, sticky="nsew", padx=8, pady=8)
        wrapper.grid_columnconfigure(0, weight=1)
        wrapper.grid_rowconfigure(0, weight=1)

        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass

        style.configure("Treeview", background="#1E1F22", foreground="#E8EAED", fieldbackground="#1E1F22", rowheight=30, borderwidth=0)
        style.configure("Treeview.Heading", background="#2B2D31", foreground="#FFFFFF", font=("Arial", 12, "bold"))
        style.map("Treeview", background=[("selected", "#1F6AA5")])

        tree = ttk.Treeview(wrapper, columns=columns, show="headings")

        for col in columns:
            tree.heading(col, text=col, command=lambda c=col, t=tree: self.sort_treeview(t, c))
            if col in ["Einträge", "Dienste", "Std.", "Stunden"]:
                tree.column(col, width=110, anchor="e")
            elif col == "#":
                tree.column(col, width=60, anchor="center")
            elif col == "Datum":
                tree.column(col, width=120, anchor="center")
            elif col == "Beschreibung":
                tree.column(col, width=380, anchor="w")
            elif col == "Art":
                tree.column(col, width=180, anchor="w")
            elif col == "Einheit":
                tree.column(col, width=200, anchor="w")
            else:
                tree.column(col, width=300, anchor="w")

        yscroll = ttk.Scrollbar(wrapper, orient="vertical", command=tree.yview)
        xscroll = ttk.Scrollbar(wrapper, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)

        tree.grid(row=0, column=0, sticky="nsew")
        yscroll.grid(row=0, column=1, sticky="ns")
        xscroll.grid(row=1, column=0, sticky="ew")

        return tree

    def setup_macos_menu(self):
        """Ersetzt die Standard-Tk-Menüs wie 'Source…' und 'Run Widget Demo' durch ein eigenes Menü."""
        try:
            menubar = tk.Menu(self)

            file_menu = tk.Menu(menubar, tearoff=0)
            file_menu.add_command(label="Projekt öffnen…  ⌘O", command=self.load_project)
            file_menu.add_command(label="Speichern  ⌘S", command=self.save_project)
            file_menu.add_command(label="Speichern unter…  ⌘⇧S", command=self.save_project_as)
            file_menu.add_separator()
            file_menu.add_command(label="CSV / Excel importieren  ⌘I", command=self.load_file)
            file_menu.add_command(label="Copy/Paste öffnen  ⌘V", command=self.open_paste_dialog)
            file_menu.add_separator()
            file_menu.add_command(label="Export", command=self.open_export_dialog)
            file_menu.add_separator()
            file_menu.add_command(label="Beenden", command=self.on_close)

            view_menu = tk.Menu(menubar, tearoff=0)
            view_menu.add_command(label="Dark / Light wechseln", command=self.toggle_theme)
            view_menu.add_command(label="Filter zurücksetzen", command=self.reset_filters)

            help_menu = tk.Menu(menubar, tearoff=0)
            help_menu.add_command(label="Anleitung", command=self.show_help)
            help_menu.add_command(label="Changelog", command=self.show_changelog)
            help_menu.add_command(label="Nach Updates suchen", command=lambda: self.check_for_updates(silent=False))
            help_menu.add_separator()
            help_menu.add_command(label=f"Über {APP_TITLE}", command=self.show_about)

            menubar.add_cascade(label="Datei", menu=file_menu)
            menubar.add_cascade(label="Ansicht", menu=view_menu)
            menubar.add_cascade(label="Hilfe", menu=help_menu)

            self.config(menu=menubar)

            # macOS-spezifisch: About im App-Menü abfangen, wenn verfügbar
            try:
                self.createcommand("tk::mac::ShowPreferences", self.show_about)
            except Exception:
                pass
        except Exception:
            pass

    def show_about(self):
        top = ctk.CTkToplevel(self)
        top.title(f"Über {APP_TITLE}")
        set_window_icon(top)
        top.geometry("430x300")
        top.resizable(False, False)
        top.transient(self)
        top.grab_set()

        frame = ctk.CTkFrame(top, corner_radius=18)
        frame.pack(fill="both", expand=True, padx=18, pady=18)

        icon_ref = None
        if Path(APP_ICON_PNG).exists():
            try:
                if Image is not None and ImageTk is not None:
                    img_pil = Image.open(APP_ICON_PNG).convert("RGBA")
                    img_pil.thumbnail((92, 92), Image.LANCZOS)
                    icon_ref = ImageTk.PhotoImage(img_pil)
                else:
                    icon_ref = tk.PhotoImage(file=APP_ICON_PNG)
                top._about_icon_ref = icon_ref
                ctk.CTkLabel(frame, image=icon_ref, text="").pack(pady=(18, 8))
            except Exception:
                ctk.CTkLabel(frame, text="✚", text_color="#D71920", font=ctk.CTkFont(size=52, weight="bold")).pack(pady=(18, 8))

        ctk.CTkLabel(frame, text=APP_TITLE, font=ctk.CTkFont(size=22, weight="bold")).pack(pady=(6, 2))
        ctk.CTkLabel(frame, text=f"Version {APP_VERSION}", text_color="#AAB2C0").pack(pady=2)
        ctk.CTkLabel(frame, text=APP_SUBTITLE, text_color="#AAB2C0").pack(pady=(8, 14))
        ctk.CTkButton(frame, text="OK", command=top.destroy, width=160).pack(pady=(6, 16))

    def show_help(self):
        help_text = """RK DienstLog – Anleitung

1. Daten laden
- Über „CSV / Excel laden“ kannst du eine Datei importieren.
- Über „Copy/Paste öffnen“ kannst du die Tabelle direkt aus dem Webportal einfügen.
- Nach dem Einfügen wird eine Vorschau angezeigt, danach kannst du die Daten übernehmen.

2. Filter verwenden
- Art: RKT-FRW, Ausbildungen/Fortbildungen, Sonstiges oder Alle.
- Monat: grenzt die Auswertung auf einen bestimmten Monat ein.
- Zug / Einheit: filtert auf einen bestimmten Zug oder eine bestimmte Einheit.
- „Filter zurücksetzen“ setzt wieder auf die Standardansicht.

3. Übersicht
- Zeigt Gesamtstunden, Dienste und Durchschnitt.
- Zusätzlich werden die wichtigsten Einheiten/Züge zusammengefasst.
- Monate werden im Format MM/JJJJ angezeigt.

4. Tabellen
- Monatsübersicht zeigt Dienste und Stunden pro Monat.
- Zug / Einheit zeigt Dienste und Stunden pro Einheit.
- Datensätze zeigt die einzelnen importierten Einträge.
- Spaltenüberschriften können angeklickt werden, um zu sortieren.

5. Detail-Drilldown
- Doppelklick auf einen Monat filtert auf diesen Monat.
- Doppelklick auf eine Einheit filtert auf diese Einheit.

6. Grafik
- „Monat“ zeigt Stunden pro Monat.
- „Verlauf“ zeigt kumulierte Stunden über die Zeit.
- Beim Darüberfahren mit der Maus werden gerundete Stunden angezeigt.

7. Kalender
- Die Kalenderansicht wird erst angezeigt, wenn links ein konkreter Monat ausgewählt wurde.
- Dadurch bleibt die Ansicht übersichtlich.

8. Export
- Im Export kannst du auswählen, ob gefilterte Daten oder alle Daten exportiert werden.
- Excel-Export kann Datensätze, Monatsübersicht und Zug-/Einheitübersicht enthalten.
- Grafiken und Kalender können als PNG exportiert werden.
- Beim Kalenderexport können mehrere Monate ausgewählt werden.

9. Auto-Speicher
- RK DienstLog merkt sich die zuletzt geladenen Daten und Filter.
- Beim nächsten Start werden diese automatisch wiederhergestellt.
"""
        top = ctk.CTkToplevel(self)
        top.title("Anleitung")
        set_window_icon(top)
        top.geometry("760x620")
        top.transient(self)
        top.grab_set()
        top.bind("<Escape>", lambda event: top.destroy())

        box = ctk.CTkTextbox(top, font=("Arial", 14), wrap="word")
        box.pack(fill="both", expand=True, padx=18, pady=18)
        box.insert("1.0", help_text)
        box.configure(state="disabled")

        ctk.CTkButton(top, text="Schließen", command=top.destroy).pack(pady=(0, 18))

    def show_changelog(self):
        top = ctk.CTkToplevel(self)
        top.title("Changelog")
        top.geometry("760x620")
        top.transient(self)
        top.grab_set()
        top.bind("<Escape>", lambda event: top.destroy())
        set_window_icon(top)

        box = ctk.CTkTextbox(top, font=("Arial", 14), wrap="word")
        box.pack(fill="both", expand=True, padx=18, pady=18)
        box.insert("1.0", CHANGELOG_TEXT)
        box.configure(state="disabled")

        ctk.CTkButton(top, text="Schließen", command=top.destroy).pack(pady=(0, 18))

    def set_status(self, text):
        if hasattr(self, "status_label"):
            self.status_label.configure(text=text)

    def toggle_theme(self):
        new_value = "Light" if self.theme_var.get() == "Dark" else "Dark"
        self.theme_var.set(new_value)
        self.change_theme(new_value)

    def change_theme(self, value):
        ctk.set_appearance_mode(value.lower())
        self.refresh_chart()
        self.refresh_calendar()
        self.save_settings()

    def sort_treeview(self, tree, col):
        key = f"{id(tree)}::{col}"
        reverse = self.tree_sort_reverse.get(key, False)

        rows = []
        for item in tree.get_children(""):
            value = tree.set(item, col)
            rows.append((self.sort_value(value, col), item))

        rows.sort(reverse=reverse, key=lambda x: x[0])

        for index, (_, item) in enumerate(rows):
            tree.move(item, "", index)

        self.tree_sort_reverse[key] = not reverse
        self.set_status(f"Sortiert nach {col} {'absteigend' if reverse else 'aufsteigend'}")

    def sort_value(self, value, col):
        text = str(value).strip()

        if col in ["Einträge", "Dienste", "Std.", "Stunden", "#"]:
            try:
                return float(text.replace(",", "."))
            except ValueError:
                return 0.0

        if col == "Datum":
            try:
                return pd.to_datetime(text, dayfirst=True, errors="coerce")
            except Exception:
                return pd.NaT

        return text.lower()

    def reset_filters(self):
        self.filter_var.set("RKT-FRW")
        self.year_filter_var.set("Alle")
        self.year_filter_var.set("Alle")
        self.month_filter_var.set("Alle")
        self.unit_filter_var.set("Alle")
        self.refresh_views()
        self.set_status("Filter zurückgesetzt")

    def on_month_double_click(self, event):
        selected = self.month_tree.selection()
        if not selected:
            return
        values = self.month_tree.item(selected[0], "values")
        if values:
            self.month_filter_var.set(values[0])
            self.refresh_views()
            self.tabs.set("Datensätze")
            self.set_status(f"Drilldown: Monat {values[0]}")

    def on_unit_double_click(self, event):
        selected = self.unit_tree.selection()
        if not selected:
            return
        values = self.unit_tree.item(selected[0], "values")
        if values:
            self.unit_filter_var.set(values[0])
            self.refresh_views()
            self.tabs.set("Datensätze")
            self.set_status(f"Drilldown: {values[0]}")

    def load_file(self):
        file = filedialog.askopenfilename(
            title="CSV oder Excel auswählen",
            filetypes=[
                ("Excel/CSV Dateien", "*.xlsx *.xls *.csv"),
                ("CSV Dateien", "*.csv"),
                ("Excel Dateien", "*.xlsx *.xls"),
                ("Alle Dateien", "*.*")
            ]
        )

        if not file:
            return

        try:
            raw = read_input_file(file)
            df = normalize_dataframe(raw)
            self.import_data(df, os.path.basename(file))
            self.set_status(f"Datei geladen: {os.path.basename(file)}")
        except Exception as e:
            messagebox.showerror("Fehler beim Dateiimport", str(e))

    def open_paste_dialog(self):
        PasteDialog(self, self.import_data)

    def import_data(self, df: pd.DataFrame, source_name: str):
        """Importiert neue Daten und fragt bei vorhandenen Daten nach Ersetzen/Erweitern."""
        df = df.copy()
        df["Std."] = df["Std."].apply(clean_hours)

        if self.df_all.empty:
            self.set_data(df, source_name)
            return

        dialog_text = (
            "Es sind bereits Daten geladen.\n\n"
            "Ja = bestehende Daten erweitern (Dubletten prüfen)\n"
            "Nein = bestehende Daten löschen und durch neuen Import ersetzen\n"
            "Abbrechen = nichts importieren"
        )

        choice = messagebox.askyesnocancel("Daten importieren", dialog_text)

        if choice is None:
            self.set_status("Import abgebrochen")
            return

        if choice is False:
            self.set_data(df, source_name)
            return

        # Find unique vs duplicate rows
        unique_rows, duplicate_rows = find_import_diff(self.df_all, df)

        def finish_import(extra_rows: list):
            all_new_rows = unique_rows + extra_rows
            if all_new_rows:
                add_df = pd.DataFrame(all_new_rows)
                merged = pd.concat([self.df_all, add_df], ignore_index=True)
                if "#" in merged.columns:
                    merged["#"] = range(1, len(merged) + 1)
            else:
                merged = self.df_all.copy()
            existing_src = self.source_name.splitlines()[1] if "Quelle:" in self.source_name else "Bestehende Daten"
            self.set_data(merged, f"{existing_src} + {source_name}")
            added = len(unique_rows) + len(extra_rows)
            skipped = len(duplicate_rows) - len(extra_rows)
            self.set_status(f"Import: {added} neu, {skipped} übersprungen")
            if added or skipped:
                messagebox.showinfo(
                    "Import abgeschlossen",
                    f"Neue Einträge: {added}\nÜbersprungen: {skipped}\nGesamt: {len(merged)}"
                )

        if duplicate_rows:
            DuplicateReviewDialog(self, duplicate_rows, finish_import)
        else:
            finish_import([])

    def set_data(self, df: pd.DataFrame, source_name: str):
        self.df_all = df.copy()
        self.df_all["Std."] = self.df_all["Std."].apply(clean_hours)
        self.source_name = f"Quelle:\n{source_name}\n\nDatensätze:\n{len(self.df_all)}"
        self.source_label.configure(text=self.source_name)
        self.update_filter_options()
        self.refresh_views()
        self.autosave_data()
        self.save_settings()
        self._dirty = True
        self.update_title_bar()
        self.set_status(f"Daten übernommen: {len(self.df_all)} Datensätze")

    def clear_data(self):
        if not self.df_all.empty:
            if not messagebox.askyesno("Daten löschen", "Möchtest du wirklich alle geladenen Daten löschen?"):
                return

        self.df_all = pd.DataFrame(columns=["#", "Datum", "Art", "Einheit", "Beschreibung", "Std.", "*"])
        self.source_name = "Keine Daten geladen"
        self.source_label.configure(text=self.source_name)
        self.year_filter_var.set("Alle")
        self.month_filter_var.set("Alle")
        self.unit_filter_var.set("Alle")
        self.update_filter_options()
        self.refresh_views()
        self.autosave_data()
        self.set_status("Daten gelöscht")

    def get_month_options_for_year(self, selected_year):
        if self.df_all.empty:
            return ["Alle"]

        tmp = self.df_all.copy()
        tmp["_date"] = pd.to_datetime(tmp["Datum"], dayfirst=True, errors="coerce")
        tmp = tmp.dropna(subset=["_date"])

        if selected_year and selected_year != "Alle":
            tmp = tmp[tmp["_date"].dt.strftime("%Y") == selected_year]

        month_keys = sorted(tmp["_date"].dt.strftime("%m").unique().tolist())
        return ["Alle"] + month_keys

    def update_filter_options(self):
        if self.df_all.empty:
            years = ["Alle"]
            units = ["Alle"]
        else:
            tmp = self.df_all.copy()
            tmp["_date"] = pd.to_datetime(tmp["Datum"], dayfirst=True, errors="coerce")
            valid_dates = tmp.dropna(subset=["_date"])

            year_keys = sorted(valid_dates["_date"].dt.strftime("%Y").unique().tolist())
            years = ["Alle"] + year_keys

            units_raw = sorted([u for u in self.df_all["Einheit"].dropna().astype(str).unique().tolist() if u.strip()])
            units = ["Alle"] + units_raw

        current_year = self.year_filter_var.get()
        current_month = self.month_filter_var.get()
        current_unit = self.unit_filter_var.get()

        if current_year not in years:
            self.year_filter_var.set("Alle")
            current_year = "Alle"

        months = self.get_month_options_for_year(current_year)

        self.year_dropdown.configure(values=years)
        self.month_dropdown.configure(values=months)
        self.unit_dropdown.configure(values=units)

        if current_month not in months:
            self.month_filter_var.set("Alle")
        if current_unit not in units:
            self.unit_filter_var.set("Alle")

    def get_filtered_df(self):
        df = self.df_all.copy()
        selected_art = self.filter_var.get()
        selected_year = self.year_filter_var.get()
        selected_month = self.month_filter_var.get()
        selected_unit = self.unit_filter_var.get()

        if selected_art and selected_art != "Alle" and not df.empty:
            df = df[df["Art"].astype(str).str.contains(selected_art, case=False, na=False)]

        if selected_year and selected_year != "Alle" and not df.empty:
            tmp_dates = pd.to_datetime(df["Datum"], dayfirst=True, errors="coerce")
            df = df[tmp_dates.dt.strftime("%Y") == selected_year]

        if selected_month and selected_month != "Alle" and not df.empty:
            tmp_dates = pd.to_datetime(df["Datum"], dayfirst=True, errors="coerce")
            df = df[tmp_dates.dt.strftime("%m") == selected_month]

        if selected_unit and selected_unit != "Alle" and not df.empty:
            df = df[df["Einheit"].astype(str) == selected_unit]

        return df

    def clear_tree(self, tree):
        for item in tree.get_children():
            tree.delete(item)

    def change_chart_mode(self, value):
        self.current_chart_mode = value
        self.refresh_chart()
        self.save_settings()

    def refresh_views(self):
        df = self.get_filtered_df()

        total = float(df["Std."].sum()) if not df.empty else 0.0
        count = int(len(df))
        avg = total / count if count else 0.0

        self.card_total.value_label.configure(text=f"{format_hours(total)} h")
        self.card_count.value_label.configure(text=str(count))
        self.card_avg.value_label.configure(text=f"{format_hours(avg)} h")

        self.summary_box.configure(state="normal")
        self.summary_box.delete("1.0", "end")

        lines = [
            "ERGEBNIS",
            "=" * 60,
            f"Filter Art: {self.filter_var.get()}",
            f"Filter Jahr: {self.year_filter_var.get()}",
            f"Filter Monat: {self.month_filter_var.get()}",
            f"Filter Einheit: {self.unit_filter_var.get()}",
            "",
            f"Dienste: {count}",
            f"Gesamtstunden: {format_hours(total)} h",
            f"Durchschnitt pro Eintrag: {format_hours(avg)} h",
            ""
        ]

        if df.empty:
            lines.append("Keine Daten geladen oder keine passenden Einträge gefunden.")
        else:
            tmp = df.copy()
            tmp["_date"] = pd.to_datetime(tmp["Datum"], dayfirst=True, errors="coerce")
            valid = tmp.dropna(subset=["_date"])
            if not valid.empty:
                lines.append(f"Zeitraum: {valid['_date'].min().strftime('%d.%m.%Y')} bis {valid['_date'].max().strftime('%d.%m.%Y')}")
                lines.append("")

            monthly = self.get_monthly_summary(df)
            if not monthly.empty:
                best_month = monthly["Stunden"].idxmax()
                lines.append(f"Bester Monat: {format_month_display(best_month)} mit {format_hours(monthly.loc[best_month, 'Stunden'])} h")

            lines.append("")

            lines.append("Top Einheiten/Züge:")
            unit_summary = self.get_unit_summary(df)

            for unit, row in unit_summary.head(12).iterrows():
                count = int(row['Eintraege'])
                label = "Dienst" if count == 1 else "Dienste"
                lines.append(f"- {unit}: {format_hours(row['Stunden'])} h ({count} {label})")



        self.summary_box.insert("1.0", "\n".join(lines))
        self.summary_box.configure(state="disabled")

        self.clear_tree(self.month_tree)
        if not df.empty:
            monthly = self.get_monthly_summary(df)
            for month, row in monthly.iterrows():
                self.month_tree.insert("", "end", values=(format_month_display(month), int(row["Eintraege"]), format_hours(row["Stunden"])))

        self.clear_tree(self.unit_tree)
        if not df.empty:
            unit_summary = self.get_unit_summary(df)
            for unit, row in unit_summary.iterrows():
                self.unit_tree.insert("", "end", values=(str(unit), int(row["Eintraege"]), format_hours(row["Stunden"])))

        self.clear_tree(self.rows_tree)
        search_term = self._rows_search_var.get().strip().lower()
        if not df.empty:
            for idx, row in df.iterrows():
                vals = (
                    clean_text(row.get("#", "")),
                    clean_text(row.get("Datum", "")),
                    clean_text(row.get("Art", "")),
                    clean_text(row.get("Einheit", "")),
                    clean_text(row.get("Beschreibung", "")),
                    format_hours(row.get("Std.", 0))
                )
                if search_term and not any(search_term in str(v).lower() for v in vals):
                    continue
                self.rows_tree.insert("", "end", iid=f"row_{idx}", values=vals)

        self.refresh_chart()
        self.refresh_calendar()
        self.refresh_analytics()
        self.save_settings()

    def get_monthly_summary(self, df):
        month_df = df.copy()
        month_df["_date"] = pd.to_datetime(month_df["Datum"], dayfirst=True, errors="coerce")
        month_df = month_df.dropna(subset=["_date"])
        if month_df.empty:
            return pd.DataFrame(columns=["Eintraege", "Stunden"])
        month_df["_month"] = month_df["_date"].dt.strftime("%Y-%m")
        return (
            month_df.groupby("_month")
            .agg(Eintraege=("Std.", "count"), Stunden=("Std.", "sum"))
            .sort_index()
        )

    def get_unit_summary(self, df):
        if df.empty:
            return pd.DataFrame(columns=["Eintraege", "Stunden"])
        return (
            df.groupby("Einheit", dropna=False)
            .agg(Eintraege=("Std.", "count"), Stunden=("Std.", "sum"))
            .sort_values("Stunden", ascending=False)
        )

    def get_daily_cumulative(self, df):
        tmp = df.copy()
        tmp["_date"] = pd.to_datetime(tmp["Datum"], dayfirst=True, errors="coerce")
        tmp = tmp.dropna(subset=["_date"]).sort_values("_date")
        if tmp.empty:
            return pd.DataFrame(columns=["Datum", "Stunden", "Kumuliert"])
        daily = tmp.groupby("_date").agg(Stunden=("Std.", "sum")).sort_index()
        daily["Kumuliert"] = daily["Stunden"].cumsum()
        return daily

    def make_chart_figure(self, df, mode):
        fig = Figure(figsize=(8, 4.6), dpi=100)
        ax = fig.add_subplot(111)

        is_dark = self.theme_var.get().lower() == "dark"
        bg = "#1E1F22" if is_dark else "#FFFFFF"
        fg = "#E8EAED" if is_dark else "#111111"
        grid = "#44474F" if is_dark else "#DADCE0"

        fig.patch.set_facecolor(bg)
        ax.set_facecolor(bg)
        ax.tick_params(colors=fg)
        ax.xaxis.label.set_color(fg)
        ax.yaxis.label.set_color(fg)
        ax.title.set_color(fg)
        for spine in ax.spines.values():
            spine.set_color(grid)

        hover_items = []

        if df.empty:
            ax.text(0.5, 0.5, "Keine Daten für Grafik", ha="center", va="center", color=fg, fontsize=14)
            ax.set_xticks([])
            ax.set_yticks([])
        elif mode == "Verlauf":
            daily = self.get_daily_cumulative(df)
            if daily.empty:
                ax.text(0.5, 0.5, "Keine Datumswerte erkannt", ha="center", va="center", color=fg, fontsize=14)
            else:
                ax.plot(daily.index, daily["Kumuliert"], marker="o", picker=5)
                ax.set_title("Verlauf kumulierte Stunden")
                ax.set_xlabel("Datum")
                ax.set_ylabel("Stunden kumuliert")
                ax.grid(True, color=grid, alpha=0.4)
                fig.autofmt_xdate(rotation=35)

                for date_value, row in daily.iterrows():
                    hover_items.append({
                        "type": "point",
                        "x": date_value,
                        "x_num": mdates.date2num(date_value.to_pydatetime() if hasattr(date_value, "to_pydatetime") else date_value),
                        "y": float(row["Kumuliert"]),
                        "label": f"{date_value.strftime('%d.%m.%Y')}: {round(float(row['Kumuliert']))} h"
                    })
        else:
            monthly = self.get_monthly_summary(df)
            if monthly.empty:
                ax.text(0.5, 0.5, "Keine Monatsdaten erkannt", ha="center", va="center", color=fg, fontsize=14)
            else:
                month_labels = [format_month_display(m) for m in monthly.index.tolist()]
                bars = ax.bar(month_labels, monthly["Stunden"].tolist())
                ax.set_title("Stunden pro Monat")
                ax.set_xlabel("Monat")
                ax.set_ylabel("Stunden")
                ax.grid(True, axis="y", color=grid, alpha=0.4)
                ax.tick_params(axis="x", rotation=35)

                for bar, (month, row) in zip(bars, monthly.iterrows()):
                    hover_items.append({
                        "type": "bar",
                        "artist": bar,
                        "label": f"{format_month_display(month)}: {round(float(row['Stunden']))} h"
                    })

        fig.tight_layout()
        return fig, ax, hover_items

    def refresh_chart(self):
        for widget in self.chart_area.winfo_children():
            widget.destroy()

        df = self.get_filtered_df()

        fig, ax, hover_items = self.make_chart_figure(df, self.current_chart_mode)

        is_dark = self.theme_var.get().lower() == "dark"
        tooltip_bg = "#2B2D31" if is_dark else "#F1F3F4"
        tooltip_fg = "#FFFFFF" if is_dark else "#111111"
        grid = "#44474F" if is_dark else "#DADCE0"

        self.hover_artists = hover_items
        self.hover_annotation = ax.annotate(
            "",
            xy=(0, 0),
            xytext=(14, 14),
            textcoords="offset points",
            bbox=dict(boxstyle="round,pad=0.45", fc=tooltip_bg, ec=grid, alpha=0.96),
            color=tooltip_fg,
            fontsize=10,
            arrowprops=dict(arrowstyle="->", color=grid)
        )
        self.hover_annotation.set_visible(False)

        self.current_figure = fig
        self.chart_canvas = FigureCanvasTkAgg(fig, master=self.chart_area)
        self.chart_canvas.draw()
        self.chart_canvas.mpl_connect("motion_notify_event", self.on_chart_hover)
        self.chart_canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")

    def on_chart_hover(self, event):
        if not self.hover_annotation or not event.inaxes:
            return

        visible = False

        for item in self.hover_artists:
            if item["type"] == "bar":
                bar = item["artist"]
                contains, _ = bar.contains(event)
                if contains:
                    x = bar.get_x() + bar.get_width() / 2
                    y = bar.get_height()
                    self.hover_annotation.xy = (x, y)
                    self.hover_annotation.set_text(item["label"])
                    self.hover_annotation.set_visible(True)
                    visible = True
                    break

            elif item["type"] == "point":
                ax = event.inaxes
                x_disp, y_disp = ax.transData.transform((item["x_num"], item["y"]))
                distance = ((event.x - x_disp) ** 2 + (event.y - y_disp) ** 2) ** 0.5

                if distance <= 12:
                    self.hover_annotation.xy = (item["x"], item["y"])
                    self.hover_annotation.set_text(item["label"])
                    self.hover_annotation.set_visible(True)
                    visible = True
                    break

        if not visible and self.hover_annotation.get_visible():
            self.hover_annotation.set_visible(False)

        if self.chart_canvas:
            self.chart_canvas.draw_idle()

    def make_calendar_figure(self, df, title_suffix=None, require_single_month=True):
        fig = Figure(figsize=(9, 5.2), dpi=100)
        ax = fig.add_subplot(111)

        is_dark = self.theme_var.get().lower() == "dark"
        bg = "#1E1F22" if is_dark else "#FFFFFF"
        fg = "#E8EAED" if is_dark else "#111111"
        grid = "#44474F" if is_dark else "#DADCE0"

        fig.patch.set_facecolor(bg)
        ax.set_facecolor(bg)
        ax.tick_params(colors=fg)
        ax.title.set_color(fg)
        for spine in ax.spines.values():
            spine.set_color(bg)

        if require_single_month and (self.year_filter_var.get() == "Alle" or self.month_filter_var.get() == "Alle"):
            ax.text(
                0.5,
                0.5,
                "Bitte zuerst links Jahr und Monat auswählen",
                ha="center",
                va="center",
                color=fg,
                fontsize=15
            )
            ax.set_xticks([])
            ax.set_yticks([])
            fig.tight_layout()
            return fig

        tmp = df.copy()
        tmp["_date"] = pd.to_datetime(tmp["Datum"], dayfirst=True, errors="coerce")
        tmp = tmp.dropna(subset=["_date"])

        if tmp.empty:
            ax.text(0.5, 0.5, "Keine Kalenderdaten erkannt", ha="center", va="center", color=fg, fontsize=14)
            ax.set_xticks([])
            ax.set_yticks([])
            fig.tight_layout()
            return fig

        daily = tmp.groupby(tmp["_date"].dt.date).agg(Stunden=("Std.", "sum")).reset_index()
        daily_map = {pd.to_datetime(row["_date"]).date(): float(row["Stunden"]) for _, row in daily.iterrows()}

        start = min(daily_map.keys())
        end = max(daily_map.keys())

        # Kalender auf volle Wochen erweitern
        start_dt = start - timedelta(days=start.weekday())
        end_dt = end + timedelta(days=(6 - end.weekday()))

        days = []
        cur = start_dt
        while cur <= end_dt:
            days.append(cur)
            cur += timedelta(days=1)

        weeks = (len(days) + 6) // 7

        ax.set_xlim(-0.5, 6.5)
        ax.set_ylim(weeks - 0.5, -0.5)
        ax.set_xticks(range(7))
        ax.set_xticklabels(["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"], color=fg)
        ax.set_yticks([])

        max_hours = max(daily_map.values()) if daily_map else 1

        # bewusste feste Farben für Heatmap-Lesbarkeit
        def color_for(hours):
            if hours <= 0:
                return "#2B2D31" if is_dark else "#F1F3F4"
            ratio = min(hours / max_hours, 1)
            if ratio < 0.34:
                return "#4CAF50"
            if ratio < 0.67:
                return "#FFC107"
            return "#F44336"

        for i, day in enumerate(days):
            week = i // 7
            weekday = i % 7
            hours = daily_map.get(day, 0.0)
            rect = matplotlib.patches.Rectangle(
                (weekday - 0.42, week - 0.42),
                0.84,
                0.84,
                facecolor=color_for(hours),
                edgecolor=grid,
                linewidth=1
            )
            ax.add_patch(rect)

            label = str(day.day)
            ax.text(weekday, week - 0.08, label, ha="center", va="center", color=fg, fontsize=9)
            if hours > 0:
                ax.text(weekday, week + 0.20, f"{round(hours)}h", ha="center", va="center", color=fg, fontsize=8)

        title = "Kalenderansicht nach Stunden"
        if title_suffix:
            title += f" – {title_suffix}"
        ax.set_title(title)
        fig.tight_layout()
        return fig

    def refresh_calendar(self):
        for widget in self.calendar_frame.winfo_children():
            widget.destroy()

        df = self.get_filtered_df()
        fig = self.make_calendar_figure(df)
        self.calendar_figure = fig

        canvas = FigureCanvasTkAgg(fig, master=self.calendar_frame)
        canvas.draw()
        canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")

    def get_available_months(self):
        if self.df_all.empty:
            return []
        tmp = self.df_all.copy()
        tmp["_date"] = pd.to_datetime(tmp["Datum"], dayfirst=True, errors="coerce")
        tmp = tmp.dropna(subset=["_date"])
        if tmp.empty:
            return []
        return [format_month_display(m) for m in sorted(tmp["_date"].dt.strftime("%Y-%m").unique().tolist())]

    def check_for_updates(self, silent=False):
        if not APP_UPDATE_URL:
            if not silent:
                messagebox.showinfo(
                    "Updates",
                    "Es ist keine Update-URL konfiguriert.\n\nTrage in version.json eine update_url ein."
                )
            return

        self.set_status("Suche nach Updates …")

        def worker():
            try:
                context = get_ssl_context()
                request = urllib.request.Request(
                    APP_UPDATE_URL,
                    headers={"User-Agent": f"{APP_TITLE}/{APP_VERSION}"}
                )

                if context is not None:
                    response = urllib.request.urlopen(request, context=context, timeout=12)
                else:
                    response = urllib.request.urlopen(request, timeout=12)

                with response:
                    raw = response.read().decode("utf-8")
                    update_info = json.loads(raw)

                self.after(0, lambda: self.handle_update_info(update_info, silent=silent))
            except Exception as e:
                self.after(0, lambda err=e: self.handle_update_error(err, silent=silent))

        threading.Thread(target=worker, daemon=True).start()

    def handle_update_error(self, error, silent=False):
        self.set_status("Update-Prüfung fehlgeschlagen")
        if not silent:
            messagebox.showerror("Update-Prüfung fehlgeschlagen", str(error))

    def handle_update_info(self, update_info: dict, silent=False):
        online_version = update_info.get("version", "0.0.0")

        if not is_newer_version(online_version, APP_VERSION):
            self.set_status("Keine neue Version verfügbar")
            if not silent:
                messagebox.showinfo(
                    "Keine Updates",
                    f"Du nutzt bereits die aktuelle Version {APP_VERSION}."
                )
            return

        changelog = update_info.get("changelog", [])
        changelog_text = "\n".join(f"- {item}" for item in changelog) if changelog else "- Keine Änderungsinfos vorhanden"

        msg = (
            f"Neue Version verfügbar: {online_version}\n\n"
            f"Aktuelle Version: {APP_VERSION}\n\n"
            f"Änderungen:\n{changelog_text}\n\n"
            "Möchtest du das Update jetzt herunterladen und installieren?"
        )

        install = messagebox.askyesno("Update verfügbar", msg)

        if install:
            self.download_and_install_update(update_info)

    def download_and_install_update(self, update_info: dict):
        if sys.platform == "darwin":
            self.download_and_install_macos_update(update_info)
        elif sys.platform.startswith("win"):
            self.download_and_install_windows_update(update_info)
        else:
            messagebox.showinfo(
                "Update",
                "Automatische Installation ist aktuell nur für macOS und Windows umgesetzt."
            )

    def download_and_install_windows_update(self, update_info: dict):
        installer_url = update_info.get("windows_url") or update_info.get("windows_installer_url")
        if not installer_url:
            messagebox.showerror(
                "Update nicht möglich",
                "In der update.json fehlt windows_url."
            )
            return

        online_version = update_info.get("version", "neu")
        self.show_update_progress(f"Windows Update {online_version} wird heruntergeladen …")

        def worker():
            try:
                update_dir = APP_DIR / "updates"
                update_dir.mkdir(exist_ok=True)

                installer_path = update_dir / f"RK_DienstLog_Setup_{online_version}.exe"
                download_file_secure(installer_url, installer_path)

                self.after(0, lambda: self.finish_windows_update(installer_path, online_version))
            except Exception as e:
                self.after(0, lambda err=e: self.update_failed(err))

        threading.Thread(target=worker, daemon=True).start()

    def finish_windows_update(self, installer_path: Path, online_version: str):
        try:
            if hasattr(self, "update_status_label"):
                self.update_status_label.configure(
                    text=f"Update {online_version} ist bereit. Der Installer wird gestartet …"
                )
            if hasattr(self, "update_progress"):
                self.update_progress.stop()

            messagebox.showinfo(
                "Update bereit",
                f"RK DienstLog startet jetzt den Installer für Version {online_version}.\n\n"
                "Falls Windows nach Berechtigungen fragt, bitte bestätigen."
            )

            subprocess.Popen([
                str(installer_path),
                "/SILENT",
                "/SUPPRESSMSGBOXES",
                "/NORESTART"
            ])

        except Exception as e:
            self.update_failed(e)
            return

        self.on_close()

    def download_and_install_macos_update(self, update_info: dict):
        if sys.platform != "darwin":
            messagebox.showinfo(
                "Update",
                "Automatische Installation ist aktuell nur für macOS umgesetzt."
            )
            return

        app_bundle = get_current_app_bundle()
        if app_bundle is None:
            messagebox.showwarning(
                "Update nicht möglich",
                "Die App läuft aktuell nicht als .app Bundle.\n\nStarte RK DienstLog aus der gebauten .app, nicht direkt per Python."
            )
            return

        zip_url = update_info.get("mac_zip_url")
        if not zip_url:
            messagebox.showerror(
                "Update nicht möglich",
                "In der update.json fehlt mac_zip_url."
            )
            return

        online_version = update_info.get("version", "neu")
        self.show_update_progress(f"Update {online_version} wird heruntergeladen …")

        def worker():
            try:
                update_dir = APP_DIR / "updates"
                update_dir.mkdir(exist_ok=True)

                zip_path = update_dir / f"RK_DienstLog_{online_version}_mac.zip"
                extract_dir = update_dir / f"RK_DienstLog_{online_version}_extract"

                if extract_dir.exists():
                    shutil.rmtree(extract_dir)
                extract_dir.mkdir(parents=True, exist_ok=True)

                download_file_secure(zip_url, zip_path)

                # Wichtig auf macOS:
                # Python zipfile zerstört bei .app Bundles teils Symlinks/Frameworks.
                # ditto erhält die macOS App-Struktur korrekt.
                subprocess.run(
                    ["/usr/bin/ditto", "-x", "-k", str(zip_path), str(extract_dir)],
                    check=True
                )

                new_app = None
                for item in extract_dir.rglob("*.app"):
                    if item.name == "RK DienstLog.app":
                        new_app = item
                        break

                if new_app is None:
                    raise RuntimeError("Im Update-ZIP wurde keine 'RK DienstLog.app' gefunden.")

                helper_script = self.create_mac_update_script()
                self.pending_update_new_app = new_app

                self.after(0, lambda: self.finish_update(helper_script, online_version))
            except Exception as e:
                self.after(0, lambda err=e: self.update_failed(err))

        threading.Thread(target=worker, daemon=True).start()

    def show_update_progress(self, text):
        self.update_window = ctk.CTkToplevel(self)
        self.update_window.title("Update")
        self.update_window.geometry("430x190")
        self.update_window.resizable(False, False)
        self.update_window.transient(self)
        self.update_window.grab_set()
        set_window_icon(self.update_window)

        frame = ctk.CTkFrame(self.update_window, corner_radius=18)
        frame.pack(fill="both", expand=True, padx=18, pady=18)

        ctk.CTkLabel(frame, text="RK DienstLog Update", font=ctk.CTkFont(size=19, weight="bold")).pack(pady=(18, 8))
        self.update_status_label = ctk.CTkLabel(frame, text=text, text_color="#AAB2C0", wraplength=350)
        self.update_status_label.pack(pady=(0, 14))

        self.update_progress = ctk.CTkProgressBar(frame, mode="indeterminate", width=280)
        self.update_progress.pack(pady=(0, 18))
        self.update_progress.start()

    def create_mac_update_script(self) -> Path:
        script_path = APP_DIR / "apply_update.sh"

        script = """#!/bin/bash
set -u

OLD_APP="$1"
NEW_APP="$2"
OLD_PID="$3"

EXECUTABLE="RK DienstLog"
OLD_PARENT="$(dirname "$OLD_APP")"
BACKUP_APP="${OLD_APP}.backup"
STAGED_APP="${OLD_PARENT}/.RK DienstLog.app.new"
LOG_FILE="$HOME/.rk_dienstlog/update.log"

echo "---- RK DienstLog Update $(date) ----" >> "$LOG_FILE"
echo "OLD_APP=$OLD_APP" >> "$LOG_FILE"
echo "NEW_APP=$NEW_APP" >> "$LOG_FILE"

while kill -0 "$OLD_PID" 2>/dev/null; do
  sleep 0.5
done

cleanup_failed() {
  echo "Update failed, restoring backup..." >> "$LOG_FILE"
  rm -rf "$OLD_APP"

  if [ -d "$BACKUP_APP" ]; then
    /usr/bin/ditto "$BACKUP_APP" "$OLD_APP"
  fi

  rm -rf "$STAGED_APP"

  if [ -d "$OLD_APP" ]; then
    chmod +x "$OLD_APP/Contents/MacOS/$EXECUTABLE" 2>/dev/null || true
    xattr -dr com.apple.quarantine "$OLD_APP" 2>/dev/null || true
    open "$OLD_APP"
  fi

  exit 1
}

if [ ! -d "$NEW_APP" ]; then
  echo "NEW_APP not found" >> "$LOG_FILE"
  cleanup_failed
fi

rm -rf "$STAGED_APP"
rm -rf "$BACKUP_APP"

echo "Copying new app to staging with ditto..." >> "$LOG_FILE"
/usr/bin/ditto "$NEW_APP" "$STAGED_APP" >> "$LOG_FILE" 2>&1 || cleanup_failed

if [ ! -f "$STAGED_APP/Contents/MacOS/$EXECUTABLE" ]; then
  echo "Executable missing in staged app" >> "$LOG_FILE"
  cleanup_failed
fi

if [ ! -f "$STAGED_APP/Contents/Frameworks/Python" ]; then
  echo "Python framework missing in staged app" >> "$LOG_FILE"
  cleanup_failed
fi

chmod +x "$STAGED_APP/Contents/MacOS/$EXECUTABLE" >> "$LOG_FILE" 2>&1 || cleanup_failed
xattr -dr com.apple.quarantine "$STAGED_APP" 2>/dev/null || true

if /usr/bin/file "$STAGED_APP/Contents/Frameworks/Python" | /usr/bin/grep -q "ASCII text"; then
  echo "Python framework is invalid ASCII text in staged app" >> "$LOG_FILE"
  cleanup_failed
fi

if [ -d "$OLD_APP" ]; then
  echo "Backing up old app with ditto..." >> "$LOG_FILE"
  /usr/bin/ditto "$OLD_APP" "$BACKUP_APP" >> "$LOG_FILE" 2>&1 || cleanup_failed
fi

echo "Installing staged app with ditto..." >> "$LOG_FILE"
rm -rf "$OLD_APP" >> "$LOG_FILE" 2>&1 || cleanup_failed
/usr/bin/ditto "$STAGED_APP" "$OLD_APP" >> "$LOG_FILE" 2>&1 || cleanup_failed

chmod +x "$OLD_APP/Contents/MacOS/$EXECUTABLE" >> "$LOG_FILE" 2>&1 || cleanup_failed
xattr -dr com.apple.quarantine "$OLD_APP" 2>/dev/null || true

if /usr/bin/file "$OLD_APP/Contents/Frameworks/Python" | /usr/bin/grep -q "ASCII text"; then
  echo "Python framework invalid after install" >> "$LOG_FILE"
  cleanup_failed
fi

echo "Starting updated app..." >> "$LOG_FILE"
open "$OLD_APP" >> "$LOG_FILE" 2>&1 || cleanup_failed

sleep 2
rm -rf "$BACKUP_APP"
rm -rf "$STAGED_APP"
rm -f "$0"

echo "Update successful" >> "$LOG_FILE"
exit 0
"""

        script_path.write_text(script, encoding="utf-8")
        script_path.chmod(0o755)
        return script_path

    def finish_update(self, helper_script: Path, online_version: str):
        try:
            if hasattr(self, "update_status_label"):
                self.update_status_label.configure(text=f"Update {online_version} ist bereit. RK DienstLog wird neu gestartet …")
            if hasattr(self, "update_progress"):
                self.update_progress.stop()

            messagebox.showinfo(
                "Update bereit",
                f"RK DienstLog wird jetzt auf Version {online_version} aktualisiert und neu gestartet."
            )

            app_bundle = get_current_app_bundle()
            new_app = getattr(self, "pending_update_new_app", None)

            if app_bundle is None or new_app is None:
                raise RuntimeError("Update-Dateien wurden nicht gefunden.")

            subprocess.Popen([
                "/bin/bash",
                str(helper_script),
                str(app_bundle),
                str(new_app),
                str(os.getpid())
            ])

        except Exception as e:
            self.update_failed(e)
            return

        self.on_close()

    def update_failed(self, error):
        try:
            if hasattr(self, "update_progress"):
                self.update_progress.stop()
            if hasattr(self, "update_window"):
                self.update_window.destroy()
        except Exception:
            pass

        self.set_status("Update fehlgeschlagen")
        messagebox.showerror("Update fehlgeschlagen", str(error))

    def open_export_dialog(self):
        if self.df_all.empty:
            messagebox.showwarning("Keine Daten", "Es gibt aktuell keine Daten zum Exportieren.")
            return
        available_months = self.get_available_months()
        ExportDialog(self, self.export_selected, available_months)

    def export_selected(self, options):
        df = self.df_all.copy() if options.get("scope") == "Alle Daten" else self.get_filtered_df()
        if df.empty:
            messagebox.showwarning("Keine Daten", "Es gibt aktuell keine Daten zum Exportieren.")
            return

        export_any_excel = options.get("data") or options.get("months") or options.get("units")
        saved_files = []

        default_name = f"RKT_Stunden_{datetime.now().strftime('%Y%m%d')}.xlsx"

        if export_any_excel:
            file = filedialog.asksaveasfilename(
                title="Excel Export speichern",
                initialfile=default_name,
                defaultextension=".xlsx",
                filetypes=[("Excel Datei", "*.xlsx")]
            )
            if file:
                try:
                    with pd.ExcelWriter(file, engine="openpyxl") as writer:
                        if options.get("data"):
                            export_df = df.copy()
                            export_df["Std."] = export_df["Std."].apply(lambda x: round(float(x), 2))
                            export_df.to_excel(writer, sheet_name="Datensaetze", index=False)

                        if options.get("months"):
                            monthly = self.get_monthly_summary(df).reset_index().rename(columns={"_month": "Monat"})
                            monthly["Monat"] = monthly["Monat"].apply(format_month_display)
                            monthly = monthly.rename(columns={"Eintraege": "Dienste"})
                            monthly.to_excel(writer, sheet_name="Monate", index=False)

                        if options.get("units"):
                            units = self.get_unit_summary(df).reset_index()
                            units.columns = ["Einheit", "Dienste", "Stunden"]
                            units.to_excel(writer, sheet_name="Zuege_Einheiten", index=False)

                    saved_files.append(file)
                except Exception as e:
                    messagebox.showerror("Export Fehler", str(e))
                    return

        if options.get("chart"):
            chart_file = filedialog.asksaveasfilename(
                title="Aktuelle Grafik speichern",
                initialfile=f"RKT_Grafik_{datetime.now().strftime('%Y%m%d')}.png",
                defaultextension=".png",
                filetypes=[("PNG Grafik", "*.png")]
            )
            if chart_file:
                try:
                    fig, _, _ = self.make_chart_figure(df, self.current_chart_mode)
                    fig.savefig(chart_file, dpi=180, bbox_inches="tight")
                    saved_files.append(chart_file)
                except Exception as e:
                    messagebox.showerror("Grafik Export Fehler", str(e))
                    return

        if options.get("calendar"):
            selected_months = options.get("calendar_months", [])

            if not selected_months:
                messagebox.showwarning("Keine Kalender-Monate", "Bitte im Export mindestens einen Kalender-Monat auswählen.")
                return

            folder = filedialog.askdirectory(title="Ordner für Kalender-PNGs auswählen")
            if folder:
                try:
                    for month in selected_months:
                        tmp_dates = pd.to_datetime(df["Datum"], dayfirst=True, errors="coerce")
                        month_key = month_key_from_display(month)
                        month_df = df[tmp_dates.dt.strftime("%Y-%m") == month_key]

                        if month_df.empty:
                            continue

                        fig = self.make_calendar_figure(month_df, title_suffix=month, require_single_month=False)
                        cal_file = os.path.join(folder, f"RKT_Kalender_{month.replace('/', '-')}.png")
                        fig.savefig(cal_file, dpi=180, bbox_inches="tight")
                        saved_files.append(cal_file)
                except Exception as e:
                    messagebox.showerror("Kalender Export Fehler", str(e))
                    return

        if saved_files:
            self.set_status("Export abgeschlossen")
            messagebox.showinfo("Export fertig", "Gespeichert:\n" + "\n".join(saved_files))

    # ── Project Save / Load ────────────────────────────────────────────────

    def update_title_bar(self):
        if self._project_file:
            name = Path(self._project_file).stem
            marker = " •" if self._dirty else ""
            self.title(f"{APP_TITLE} – {name}{marker}")
        else:
            marker = " •" if self._dirty else ""
            self.title(f"{APP_TITLE}{marker}")

    def save_project(self):
        if not self._project_file:
            self.save_project_as()
            return
        try:
            state = {
                "filter_art": self.filter_var.get(),
                "filter_year": self.year_filter_var.get(),
                "filter_month": self.month_filter_var.get(),
                "filter_unit": self.unit_filter_var.get(),
                "theme": self.theme_var.get(),
                "chart_mode": self.current_chart_mode,
                "source_name": self.source_name,
            }
            save_project_file(Path(self._project_file), self.df_all, state)
            self._dirty = False
            self.update_title_bar()
            self.set_status(f"Gespeichert: {Path(self._project_file).name}")
        except Exception as e:
            messagebox.showerror("Fehler beim Speichern", str(e))

    def save_project_as(self):
        file = filedialog.asksaveasfilename(
            title="Projekt speichern",
            defaultextension=".rkdienstlog",
            filetypes=[("RK DienstLog Projektdatei", "*.rkdienstlog"), ("Alle Dateien", "*.*")]
        )
        if not file:
            return
        self._project_file = file
        self.save_project()

    def load_project(self):
        if self._dirty and not self.df_all.empty:
            answer = messagebox.askyesnocancel(
                "Ungespeicherte Änderungen",
                "Ungespeicherte Änderungen gehen verloren. Jetzt speichern?"
            )
            if answer is None:
                return
            if answer:
                self.save_project()

        file = filedialog.askopenfilename(
            title="Projekt öffnen",
            filetypes=[("RK DienstLog Projektdatei", "*.rkdienstlog"), ("Alle Dateien", "*.*")]
        )
        if not file:
            return
        try:
            result = load_project_file(Path(file))
            df = result["df"]
            state = result.get("state", {})

            self._project_file = file
            self.df_all = df
            self.df_all["Std."] = self.df_all["Std."].apply(clean_hours)
            self.source_name = state.get("source_name", f"Quelle:\n{Path(file).name}\n\nDatensätze:\n{len(df)}")
            self.source_label.configure(text=self.source_name)

            if state.get("theme"):
                self.theme_var.set(state["theme"])
                ctk.set_appearance_mode(state["theme"].lower())
            if state.get("chart_mode"):
                self.current_chart_mode = state["chart_mode"]
                self.chart_mode.set(self.current_chart_mode)

            self.update_filter_options()

            if state.get("filter_art") and state["filter_art"] in ART_OPTIONS:
                self.filter_var.set(state["filter_art"])
            if state.get("filter_year"):
                self.year_filter_var.set(state["filter_year"])
            if state.get("filter_month"):
                self.month_filter_var.set(state["filter_month"])
            if state.get("filter_unit"):
                self.unit_filter_var.set(state["filter_unit"])

            self.refresh_views()
            self.autosave_data()
            self._dirty = False
            self.update_title_bar()
            self.set_status(f"Projekt geladen: {Path(file).name}")
        except Exception as e:
            messagebox.showerror("Fehler beim Öffnen", str(e))

    # ── Datensätze Tab: Search + Inline Edit + Right-click ─────────────────

    def _on_rows_search(self):
        self.clear_tree(self.rows_tree)
        df = self.get_filtered_df()
        search_term = self._rows_search_var.get().strip().lower()
        for idx, row in df.iterrows():
            vals = (
                clean_text(row.get("#", "")),
                clean_text(row.get("Datum", "")),
                clean_text(row.get("Art", "")),
                clean_text(row.get("Einheit", "")),
                clean_text(row.get("Beschreibung", "")),
                format_hours(row.get("Std.", 0))
            )
            if search_term and not any(search_term in str(v).lower() for v in vals):
                continue
            self.rows_tree.insert("", "end", iid=f"row_{idx}", values=vals)

    def on_row_right_click(self, event):
        row_id = self.rows_tree.identify_row(event.y)
        if not row_id:
            return
        self.rows_tree.selection_set(row_id)
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="Zeile löschen", command=self.delete_selected_rows)
        menu.add_command(label="Zeile bearbeiten", command=lambda: self._edit_selected_row())
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def delete_selected_rows(self):
        selected = self.rows_tree.selection()
        if not selected:
            return
        if not messagebox.askyesno("Zeile löschen",
                                   f"{len(selected)} Zeile(n) wirklich löschen?"):
            return
        for iid in selected:
            try:
                idx = int(iid.replace("row_", ""))
                self.df_all = self.df_all.drop(index=idx)
            except Exception:
                pass
        self.df_all = self.df_all.reset_index(drop=True)
        if "#" in self.df_all.columns:
            self.df_all["#"] = range(1, len(self.df_all) + 1)
        self._dirty = True
        self.update_title_bar()
        self.update_filter_options()
        self.refresh_views()
        self.autosave_data()
        self.set_status(f"{len(selected)} Zeile(n) gelöscht")

    def on_row_double_click(self, event):
        region = self.rows_tree.identify_region(event.x, event.y)
        if region != "cell":
            return
        item = self.rows_tree.identify_row(event.y)
        col_id = self.rows_tree.identify_column(event.x)
        if not item or not col_id:
            return
        col_idx = int(col_id[1:]) - 1
        columns = ["#", "Datum", "Art", "Einheit", "Beschreibung", "Std."]
        if col_idx >= len(columns):
            return
        col_name = columns[col_idx]
        if col_name in ("#", "*"):
            return
        bbox = self.rows_tree.bbox(item, col_id)
        if not bbox:
            return
        x, y, width, height = bbox
        current_value = self.rows_tree.set(item, col_name)
        entry_var = tk.StringVar(value=current_value)
        entry = ttk.Entry(self.rows_tree, textvariable=entry_var)
        entry.place(x=x, y=y, width=width, height=height)
        entry.focus_set()
        entry.select_range(0, "end")

        def save_edit(event=None):
            new_value = entry_var.get()
            entry.destroy()
            self._apply_cell_edit(item, col_name, new_value)

        def cancel_edit(event=None):
            entry.destroy()

        entry.bind("<Return>", save_edit)
        entry.bind("<Tab>", save_edit)
        entry.bind("<Escape>", cancel_edit)
        entry.bind("<FocusOut>", save_edit)

    def _apply_cell_edit(self, item, col_name, new_value):
        try:
            idx = int(item.replace("row_", ""))
        except Exception:
            return
        if idx not in self.df_all.index:
            return
        if col_name == "Std.":
            try:
                value = float(new_value.replace(",", "."))
            except ValueError:
                messagebox.showwarning("Ungültige Eingabe", "Stunden müssen eine Zahl sein.")
                return
            self.df_all.loc[idx, col_name] = value
        elif col_name == "Datum":
            try:
                pd.to_datetime(new_value, dayfirst=True)
            except Exception:
                messagebox.showwarning("Ungültiges Datum",
                                       "Format: TT.MM.JJJJ")
                return
            self.df_all.loc[idx, col_name] = new_value
        else:
            self.df_all.loc[idx, col_name] = new_value
        self._dirty = True
        self.update_title_bar()
        self.update_filter_options()
        self.refresh_views()
        self.autosave_data()

    def _edit_selected_row(self):
        selected = self.rows_tree.selection()
        if not selected:
            return
        item = selected[0]
        try:
            idx = int(item.replace("row_", ""))
        except Exception:
            return
        if idx not in self.df_all.index:
            return
        row = self.df_all.loc[idx]

        dialog = ctk.CTkToplevel(self)
        dialog.title("Zeile bearbeiten")
        dialog.geometry("500x360")
        dialog.transient(self)
        dialog.grab_set()
        dialog.bind("<Escape>", lambda e: dialog.destroy())
        dialog.grid_columnconfigure(1, weight=1)

        fields = ["Datum", "Art", "Einheit", "Beschreibung", "Std."]
        vars_ = {}
        for i, field in enumerate(fields):
            ctk.CTkLabel(dialog, text=field + ":").grid(row=i, column=0, padx=16, pady=8, sticky="e")
            var = tk.StringVar(value=str(row.get(field, "")))
            vars_[field] = var
            if field == "Art":
                ctk.CTkOptionMenu(dialog, values=[o for o in ART_OPTIONS if o != "Alle"],
                                  variable=var).grid(row=i, column=1, padx=16, pady=8, sticky="ew")
            else:
                ctk.CTkEntry(dialog, textvariable=var).grid(row=i, column=1, padx=16, pady=8, sticky="ew")

        def apply():
            for field, var in vars_.items():
                val = var.get()
                if field == "Std.":
                    try:
                        val = float(val.replace(",", "."))
                    except ValueError:
                        messagebox.showwarning("Ungültig", "Stunden = Zahl")
                        return
                self.df_all.loc[idx, field] = val
            self._dirty = True
            self.update_title_bar()
            self.update_filter_options()
            self.refresh_views()
            self.autosave_data()
            dialog.destroy()

        btns = ctk.CTkFrame(dialog, fg_color="transparent")
        btns.grid(row=len(fields), column=0, columnspan=2, pady=(12, 16))
        ctk.CTkButton(btns, text="Speichern", command=apply, fg_color="#2FA572", hover_color="#278B60").pack(side="left", padx=8)
        ctk.CTkButton(btns, text="Abbrechen", command=dialog.destroy, fg_color="#555B66", hover_color="#464B54").pack(side="left", padx=8)

    # ── Analytics Tab ──────────────────────────────────────────────────────

    def refresh_analytics(self):
        tab = self.tab_analytics
        for w in tab.winfo_children():
            w.destroy()
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)

        df = self.df_all.copy()

        # ── KPI Cards ──
        kpi_frame = ctk.CTkFrame(tab, fg_color="transparent")
        kpi_frame.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 6))
        for i in range(5):
            kpi_frame.grid_columnconfigure(i, weight=1)

        total_hours = float(df["Std."].sum()) if not df.empty else 0.0
        total_count = len(df)

        df_d = df.copy()
        if not df_d.empty:
            df_d["_date"] = pd.to_datetime(df_d["Datum"], dayfirst=True, errors="coerce")

        best_year = "-"
        best_month = "-"
        avg_month = 0.0
        if not df_d.empty and "_date" in df_d.columns:
            valid = df_d.dropna(subset=["_date"])
            if not valid.empty:
                by_year = valid.groupby(valid["_date"].dt.year)["Std."].sum()
                if not by_year.empty:
                    best_year = str(int(by_year.idxmax()))
                by_month = valid.groupby(valid["_date"].dt.strftime("%Y-%m"))["Std."].sum()
                if not by_month.empty:
                    best_month = format_month_display(by_month.idxmax())
                n_months = valid["_date"].dt.strftime("%Y-%m").nunique()
                if n_months > 0:
                    avg_month = total_hours / n_months

        kpis = [
            ("Gesamtstunden", f"{format_hours(total_hours)} h"),
            ("Dienste gesamt", str(total_count)),
            ("Aktivstes Jahr", best_year),
            ("Bester Monat", best_month),
            ("Ø Stunden/Monat", f"{format_hours(avg_month)} h"),
        ]
        for i, (label, value) in enumerate(kpis):
            card = self.create_stat_card(kpi_frame, label, value)
            card.grid(row=0, column=i, padx=6, sticky="ew")

        # ── Bottom: Jahresvergleich left + Heatmap right ──
        bottom = ctk.CTkFrame(tab, fg_color="transparent")
        bottom.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))
        bottom.grid_columnconfigure(0, weight=3)
        bottom.grid_columnconfigure(1, weight=2)
        bottom.grid_rowconfigure(0, weight=1)

        # Jahresvergleich
        left = ctk.CTkFrame(bottom)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        left.grid_columnconfigure(0, weight=1)
        left.grid_rowconfigure(1, weight=1)
        ctk.CTkLabel(left, text="Jahresvergleich (Stunden pro Monat)",
                     font=ctk.CTkFont(size=13, weight="bold")).grid(
            row=0, column=0, sticky="w", padx=12, pady=(10, 4))
        fig_cmp = self._make_year_comparison_figure(df)
        canvas_cmp = FigureCanvasTkAgg(fig_cmp, master=left)
        canvas_cmp.draw()
        canvas_cmp.get_tk_widget().grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 8))

        # Heatmap
        right = ctk.CTkFrame(bottom)
        right.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(2, weight=1)
        ctk.CTkLabel(right, text="Aktivität (GitHub-Heatmap)",
                     font=ctk.CTkFont(size=13, weight="bold")).grid(
            row=0, column=0, sticky="w", padx=12, pady=(10, 4))

        available_years = []
        if not df.empty:
            tmp_d = pd.to_datetime(df["Datum"], dayfirst=True, errors="coerce").dropna()
            available_years = sorted(tmp_d.dt.year.unique().tolist(), reverse=True)

        if available_years:
            current_hm_year = self._heatmap_year_var.get()
            if not current_hm_year or int(current_hm_year) not in available_years:
                self._heatmap_year_var.set(str(available_years[0]))

            if len(available_years) > 1:
                ctk.CTkSegmentedButton(
                    right,
                    values=[str(y) for y in available_years[:6]],
                    variable=self._heatmap_year_var,
                    command=lambda _: self._redraw_heatmap(right, df, available_years)
                ).grid(row=1, column=0, sticky="w", padx=12, pady=(0, 6))

        self._heatmap_canvas_frame = ctk.CTkFrame(right, fg_color="transparent")
        self._heatmap_canvas_frame.grid(row=2, column=0, sticky="nsew", padx=8, pady=(0, 8))
        self._heatmap_canvas_frame.grid_columnconfigure(0, weight=1)
        self._heatmap_canvas_frame.grid_rowconfigure(0, weight=1)

        if available_years:
            self._draw_heatmap_to_frame(self._heatmap_canvas_frame, df, available_years[0])
        else:
            ctk.CTkLabel(self._heatmap_canvas_frame,
                         text="Keine Daten für Heatmap",
                         text_color="#AAB2C0").grid(row=0, column=0)

    def _redraw_heatmap(self, parent_frame, df, available_years):
        for w in self._heatmap_canvas_frame.winfo_children():
            w.destroy()
        try:
            year = int(self._heatmap_year_var.get())
        except Exception:
            year = available_years[0] if available_years else None
        if year:
            self._draw_heatmap_to_frame(self._heatmap_canvas_frame, df, year)

    def _draw_heatmap_to_frame(self, frame, df, year: int):
        fig = self._make_yearly_heatmap_figure(df, year)
        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")

    def _make_year_comparison_figure(self, df):
        is_dark = self.theme_var.get().lower() == "dark"
        bg = "#1E1F22" if is_dark else "#FFFFFF"
        fg = "#E8EAED" if is_dark else "#111111"
        grid_c = "#44474F" if is_dark else "#DADCE0"

        fig = Figure(figsize=(7, 4), dpi=96)
        ax = fig.add_subplot(111)
        fig.patch.set_facecolor(bg)
        ax.set_facecolor(bg)
        ax.tick_params(colors=fg)
        ax.xaxis.label.set_color(fg)
        ax.yaxis.label.set_color(fg)
        ax.title.set_color(fg)
        for spine in ax.spines.values():
            spine.set_color(grid_c)

        if df.empty:
            ax.text(0.5, 0.5, "Keine Daten", ha="center", va="center", color=fg, fontsize=13)
            ax.set_xticks([])
            ax.set_yticks([])
            fig.tight_layout()
            return fig

        tmp = df.copy()
        tmp["_date"] = pd.to_datetime(tmp["Datum"], dayfirst=True, errors="coerce")
        tmp = tmp.dropna(subset=["_date"])
        if tmp.empty:
            ax.text(0.5, 0.5, "Keine Datumswerte", ha="center", va="center", color=fg, fontsize=13)
            ax.set_xticks([])
            ax.set_yticks([])
            fig.tight_layout()
            return fig

        tmp["_year"] = tmp["_date"].dt.year
        tmp["_month"] = tmp["_date"].dt.month
        years = sorted(tmp["_year"].unique())
        month_labels = ["Jan", "Feb", "Mär", "Apr", "Mai", "Jun",
                        "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"]
        n_years = len(years)
        bar_width = 0.8 / max(n_years, 1)
        colors = ["#1F6AA5", "#2FA572", "#FFC107", "#F44336", "#9C27B0", "#FF9800"]

        for i, year in enumerate(years):
            y_df = tmp[tmp["_year"] == year]
            monthly = y_df.groupby("_month")["Std."].sum().reindex(range(1, 13), fill_value=0)
            x = [m - 1 + (i - n_years / 2 + 0.5) * bar_width for m in range(1, 13)]
            ax.bar(x, monthly.values, width=bar_width * 0.9,
                   color=colors[i % len(colors)], label=str(year), alpha=0.85)

        ax.set_xticks(range(12))
        ax.set_xticklabels(month_labels, color=fg, fontsize=9)
        ax.set_ylabel("Stunden", color=fg)
        ax.grid(True, axis="y", color=grid_c, alpha=0.4)
        if n_years > 1:
            legend = ax.legend(fontsize=9, framealpha=0.7)
            for text in legend.get_texts():
                text.set_color(fg)
            legend.get_frame().set_facecolor(bg)
        fig.tight_layout()
        return fig

    def _make_yearly_heatmap_figure(self, df, year: int):
        from datetime import date as date_type
        import calendar as cal_mod

        is_dark = self.theme_var.get().lower() == "dark"
        bg = "#1E1F22" if is_dark else "#FFFFFF"
        fg = "#E8EAED" if is_dark else "#111111"
        empty_c = "#2B2D31" if is_dark else "#EBEDF0"

        fig = Figure(figsize=(6.5, 2.2), dpi=96)
        ax = fig.add_subplot(111)
        fig.patch.set_facecolor(bg)
        ax.set_facecolor(bg)
        for spine in ax.spines.values():
            spine.set_visible(False)

        # Build daily map for the year
        daily_map = {}
        if not df.empty:
            tmp = df.copy()
            tmp["_date"] = pd.to_datetime(tmp["Datum"], dayfirst=True, errors="coerce")
            tmp = tmp.dropna(subset=["_date"])
            tmp = tmp[tmp["_date"].dt.year == year]
            if not tmp.empty:
                for dt, grp in tmp.groupby(tmp["_date"].dt.date):
                    daily_map[dt] = float(grp["Std."].sum())

        max_h = max(daily_map.values()) if daily_map else 1.0

        def cell_color(h):
            if h <= 0:
                return empty_c
            ratio = min(h / max_h, 1.0)
            if ratio < 0.25:
                return "#196127"
            if ratio < 0.5:
                return "#239a3b"
            if ratio < 0.75:
                return "#7bc96f"
            return "#c6e48b"

        # 52 weeks × 7 days grid
        jan1 = date_type(year, 1, 1)
        # Align to Monday
        start = jan1 - timedelta(days=jan1.weekday())
        weeks = 53
        ax.set_xlim(-0.5, weeks - 0.5)
        ax.set_ylim(-0.5, 6.5)
        ax.invert_yaxis()

        month_ticks = {}
        for w in range(weeks):
            for d in range(7):
                day = start + timedelta(days=w * 7 + d)
                if day.year != year:
                    color = bg
                else:
                    color = cell_color(daily_map.get(day, 0.0))
                    if day.day == 1:
                        month_ticks[w] = day.strftime("%b")
                rect = matplotlib.patches.Rectangle(
                    (w - 0.45, d - 0.45), 0.9, 0.9,
                    facecolor=color, edgecolor=bg, linewidth=0.5
                )
                ax.add_patch(rect)

        ax.set_xticks(list(month_ticks.keys()))
        ax.set_xticklabels(list(month_ticks.values()), color=fg, fontsize=8)
        ax.set_yticks(range(7))
        ax.set_yticklabels(["Mo", "", "Mi", "", "Fr", "", "So"], color=fg, fontsize=8)
        ax.tick_params(length=0)
        ax.set_title(f"Aktivität {year}", color=fg, fontsize=10, pad=6)
        fig.tight_layout(pad=0.4)
        return fig

    def on_close(self):
        if self._dirty and not self.df_all.empty:
            answer = messagebox.askyesnocancel(
                "Ungespeicherte Änderungen",
                "Es gibt ungespeicherte Änderungen.\n\nJetzt speichern?"
            )
            if answer is None:
                return
            if answer:
                self.save_project()
        self.autosave_data()
        self.save_settings()
        self.destroy()


if __name__ == "__main__":
    app = RktApp()

    splash = SplashScreen(app)
    splash.update_idletasks()

    def show_main_window():
        try:
            splash.destroy()
        except Exception:
            pass
        app.deiconify()
        app.lift()
        app.focus_force()
        enforce_macos_icon(app)

    app.after(900, show_main_window)
    app.mainloop()
