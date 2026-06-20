#!/usr/bin/env python3
"""
Signaturfeld-Tool für SEF Ausbildungsnachweis
Fügt digitale Signaturfelder in ein PDF ein.
Benötigt: pip3 install pikepdf
"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import subprocess
import sys
import os

def install_pikepdf():
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pikepdf"])

try:
    import pikepdf
    from pikepdf import Pdf, Dictionary, Array, Name, String
except ImportError:
    print("Installiere pikepdf...")
    install_pikepdf()
    import pikepdf
    from pikepdf import Pdf, Dictionary, Array, Name, String


def add_sig_field(pdf, page, field_name, rect):
    sig_widget = pdf.make_indirect(Dictionary(
        Type=Name("/Annot"),
        Subtype=Name("/Widget"),
        FT=Name("/Sig"),
        T=String(field_name),
        Rect=Array([rect[0], rect[1], rect[2], rect[3]]),
        F=pikepdf.Integer(4),
        P=page.obj,
    ))
    if "/Annots" not in page:
        page["/Annots"] = pdf.make_indirect(Array())
    page.Annots.append(sig_widget)
    pdf.Root.AcroForm.Fields.append(sig_widget)


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Signaturfelder einfügen")
        self.root.geometry("500x520")
        self.root.resizable(False, False)

        self.input_path = tk.StringVar()
        self.output_path = tk.StringVar()

        pad = {"padx": 16, "pady": 6}

        tk.Label(root, text="Signaturfelder einfügen", font=("Helvetica", 16, "bold")).pack(pady=(20, 4))
        tk.Label(root, text="Fügt digitale Signaturfelder in ein PDF ein.", fg="gray").pack()

        tk.Frame(root, height=1, bg="#ddd").pack(fill="x", padx=16, pady=12)

        # Input file
        frm1 = tk.Frame(root)
        frm1.pack(fill="x", **pad)
        tk.Label(frm1, text="PDF Datei:", width=14, anchor="w").pack(side="left")
        tk.Entry(frm1, textvariable=self.input_path, width=32).pack(side="left", padx=4)
        tk.Button(frm1, text="Wählen", command=self.pick_input).pack(side="left")

        # Page number
        frm_page = tk.Frame(root)
        frm_page.pack(fill="x", **pad)
        tk.Label(frm_page, text="Seite:", width=14, anchor="w").pack(side="left")
        self.page_var = tk.IntVar(value=2)
        tk.Spinbox(frm_page, from_=1, to=99, textvariable=self.page_var, width=5).pack(side="left", padx=4)
        tk.Label(frm_page, text="(Seite auf der unterschrieben wird)", fg="gray", font=("Helvetica", 11)).pack(side="left", padx=4)

        tk.Frame(root, height=1, bg="#ddd").pack(fill="x", padx=16, pady=8)

        # Field 1
        tk.Label(root, text="Feld 1: Kursteilnehmer", font=("Helvetica", 13, "bold")).pack(anchor="w", padx=16)
        self.kt = self._field_row(root, "Position (x1, y0, x2, y1):", 45, 88, 201, 125)

        tk.Frame(root, height=1, bg="#ddd").pack(fill="x", padx=16, pady=8)

        # Field 2
        tk.Label(root, text="Feld 2: SEF-Zugsausbilder", font=("Helvetica", 13, "bold")).pack(anchor="w", padx=16)
        self.sef = self._field_row(root, "Position (x1, y0, x2, y1):", 320, 88, 510, 125)

        tk.Frame(root, height=1, bg="#ddd").pack(fill="x", padx=16, pady=8)

        # Output
        frm2 = tk.Frame(root)
        frm2.pack(fill="x", **pad)
        tk.Label(frm2, text="Speichern als:", width=14, anchor="w").pack(side="left")
        tk.Entry(frm2, textvariable=self.output_path, width=32).pack(side="left", padx=4)
        tk.Button(frm2, text="Wählen", command=self.pick_output).pack(side="left")

        tk.Button(root, text="✅  Signaturfelder einfügen", font=("Helvetica", 14),
                  bg="#1a7f4b", fg="white", padx=12, pady=8,
                  command=self.run).pack(pady=16)

    def _field_row(self, parent, label, x1, y0, x2, y1):
        frm = tk.Frame(parent)
        frm.pack(fill="x", padx=16, pady=2)
        tk.Label(frm, text=label, width=22, anchor="w", font=("Helvetica", 11)).pack(side="left")
        vars_ = []
        for val in (x1, y0, x2, y1):
            v = tk.IntVar(value=val)
            tk.Spinbox(frm, from_=0, to=999, textvariable=v, width=5).pack(side="left", padx=2)
            vars_.append(v)
        return vars_

    def pick_input(self):
        path = filedialog.askopenfilename(filetypes=[("PDF Dateien", "*.pdf")])
        if path:
            self.input_path.set(path)
            base, ext = os.path.splitext(path)
            self.output_path.set(base + "_mit_Signatur" + ext)

    def pick_output(self):
        path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF Dateien", "*.pdf")])
        if path:
            self.output_path.set(path)

    def run(self):
        inp = self.input_path.get()
        out = self.output_path.get()
        if not inp or not out:
            messagebox.showerror("Fehler", "Bitte Input- und Output-Datei wählen.")
            return
        try:
            pdf = Pdf.open(inp)
            page_idx = self.page_var.get() - 1
            page = pdf.pages[page_idx]

            x1k, y0k, x2k, y1k = [v.get() for v in self.kt]
            x1s, y0s, x2s, y1s = [v.get() for v in self.sef]

            add_sig_field(pdf, page, "Unterschrift_Kursteilnehmer",    [x1k, y0k, x2k, y1k])
            add_sig_field(pdf, page, "Unterschrift_SEF_Zugsausbilder", [x1s, y0s, x2s, y1s])

            pdf.save(out)
            pdf.close()
            messagebox.showinfo("Fertig", f"Gespeichert:\n{out}")
            os.system(f'open "{out}"')
        except Exception as e:
            messagebox.showerror("Fehler", str(e))


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
