#!/usr/bin/python
"""
Interface graphique pour le multimètre OWON XDM1041.

Ce programme utilise PyQt6 pour afficher les mesures en temps réel,
avec un graphique facultatif pour visualiser l'évolution des mesures.
Il communique avec le multimètre via SCPI (Standard Commands for Programmable Instruments).

Fonctionnalités :
- Affiche le mode, la plage et la mesure actuelle
- Historique graphique des mesures (optionnel)
- Détection automatique des changements de mode/plage
- Communication série avec gestion des erreurs de décodage

Utilisation :
python script.py --port /dev/ttyUSB0 [--graph]
"""
from dotenv import load_dotenv
import os
import serial
import time
import sys
import argparse
from collections import deque

from PyQt6 import QtWidgets, QtCore
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget, QApplication, QGridLayout, QFrame
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

load_dotenv()

port = os.getenv("PORT", "/dev/ttyUSB0")
baudrate = float(os.getenv("BAUDRATE", 115200))
timeout = float(os.getenv("TIMEOUT", 0.2))
graph = os.getenv("GRAPH", "False").lower() in ("true", "1", "yes")

# Envoie une commande SCPI au multimètre, lit la réponse brute en binaire,
# et gère le décodage des caractères invalides (erreurs de type Unicode)
# Le timeout court (0.2s) permet une lecture réactive même si l'appareil ne répond pas tout de suite.
def envoyer_commande(ser, commande):
    ser.write((commande + '\n').encode('ascii'))
    time.sleep(0.05)
    reponse = ser.read(128)
    return reponse.decode(errors='backslashreplace').strip()

def formater_mesure(valeur, unite):
    try:
        if valeur.startswith("1E+9"):
            return "Surcharge"
        val = float(valeur)
        return f"{val:.3f} {unite}"
    except ValueError:
        return valeur

def extraire_float(valeur):
    try:
        if valeur.startswith("1E+9"):
            return None
        return float(valeur)
    except ValueError:
        return None

unites = {
    "VOLT": "V",
    "VOLT AC": "V~",
    "CURR": "A",
    "CURR AC": "A~",
    "RES": "Ω",
    "CAP": "F",
    "FREQ": "Hz",
    "DIOD": "V",
    "CONT": "Ω"
}

modes_fran = {
    "VOLT": "Tension continue",
    "VOLT AC": "Tension alternative",
    "CURR": "Courant continu",
    "CURR AC": "Courant alternatif",
    "RES": "Résistance",
    "CAP": "Capacité",
    "FREQ": "Fréquence",
    "DIOD": "Diode",
    "CONT": "Continuité"
}

class MultimetreApp(QWidget):
    def __init__(self, port, afficher_graphique=True):
        super().__init__()
        self.setWindowTitle("XDM1041 - Multimètre")
        self.setFixedSize(400, 395 if afficher_graphique else 125)
        self.setStyleSheet("background-color: #1e1e1e;")

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)  # Marges : gauche, haut, droite, bas
        layout.setSpacing(0)  # AJOUT : Supprime l'espacement entre les widgets
        
        title = QLabel("MULTIMÈTRE")
        title.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed)
        title.setFixedHeight(32)  # ou 28 ou 30 si tu veux encore plus serré
        title.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: white;
            margin: 0px;
            padding: 0px;
        """)
        
        layout.addWidget(title)
        
        ligne = QFrame()
        ligne.setFrameShape(QFrame.Shape.HLine)
        ligne.setStyleSheet("""
            color: white;
            margin: 0px;
            padding: 0px;
        """)
        layout.addWidget(ligne)

        self.grid = QGridLayout()
        self.grid.setContentsMargins(10, 4, 10, 4)  # AJOUTEZ cette ligne
        self.grid.setColumnStretch(0, 1)
        self.grid.setColumnStretch(1, 1)
        self.grid.setHorizontalSpacing(10)
        self.grid.setVerticalSpacing(2)

        self.labels = {}
        for i, champ in enumerate(["MODE", "PLAGE", "MESURE"]):
            label = QLabel(f"{champ.capitalize()} :")
            label.setStyleSheet("font-size: 24px; font-weight: bold; color: white; margin: 0px; padding: 0px;")
            label.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter)
            self.grid.addWidget(label, i, 0)

            champ_val = QLabel("-")
            champ_val.setStyleSheet("font-size: 24px; font-weight: bold; color: #90ee90;")
            champ_val.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignVCenter)
            self.grid.addWidget(champ_val, i, 1)

            self.labels[champ] = champ_val

        layout.addLayout(self.grid)

        self.afficher_graphique = afficher_graphique
        if self.afficher_graphique:
            self.canvas_fig = Figure(figsize=(5, 2.5), facecolor='#1e1e1e')
            self.canvas_ax = self.canvas_fig.add_subplot(111)
            self.canvas_ax.set_ylabel("Mesure", color='white')
            self.canvas_ax.tick_params(axis='y', colors='white')
            self.canvas_ax.set_xticks([])
            self.canvas_ax.spines['bottom'].set_color('white')
            self.canvas_ax.spines['top'].set_color('white')
            self.canvas_ax.spines['right'].set_color('white')
            self.canvas_ax.spines['left'].set_color('white')
            self.canvas_line, = self.canvas_ax.plot([], [], lw=2, color='#90ee90')
            self.canvas = FigureCanvas(self.canvas_fig)
            layout.addWidget(self.canvas)

        self.setLayout(layout)
        self.layout().setContentsMargins(0, 0, 0, 0)  # CETTE ligne est la clé !

        self.ser = serial.Serial(port, baudrate=baudrate, timeout=timeout)
        self.ser.write(b"SYST:REM\n")

        self.historique = deque()
        self.dernier_mode = ""
        self.dernier_plage = ""
        self.dernier_unite = ""
        self.start_time = time.time()

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_valeurs)
        self.timer.start(500)

    # Rafraîchit les données toutes les 0.5 secondes, met à jour l'affichage graphique
    # et gère les changements de mode ou de plage.
    def update_valeurs(self):
        try:
            mode = envoyer_commande(self.ser, "FUNC1?").strip('"')
            plage = envoyer_commande(self.ser, "RANGE?")
            val1 = envoyer_commande(self.ser, "MEAS1?")

            mode_str = modes_fran.get(mode.upper(), mode)
            unite = unites.get(mode.upper(), "")
            val_formatee = formater_mesure(val1, unite)

            if mode != self.dernier_mode or plage != self.dernier_plage:
                self.historique.clear()
                self.start_time = time.time()
                if self.afficher_graphique:
                    self.canvas_ax.set_title(mode_str, color='white')
                self.dernier_mode = mode
                self.dernier_plage = plage
                self.dernier_unite = unite

            self.labels["MODE"].setText(mode_str)
            self.labels["PLAGE"].setText(plage)
            self.labels["MESURE"].setText(val_formatee)

            val = extraire_float(val1)
            if val is not None and self.afficher_graphique:
                temps = time.time() - self.start_time
                self.historique.append((temps, val))
                while self.historique and self.historique[0][0] < temps - 60:
                    self.historique.popleft()

                if self.historique:
                    x_vals, y_vals = zip(*self.historique)
                    self.canvas_line.set_data(x_vals, y_vals)
                    min_y, max_y = min(y_vals), max(y_vals)
                    marge = max(0.05 * (max_y - min_y), 0.01)
                    self.canvas_ax.set_ylim(min_y - marge, max_y + marge)
                    self.canvas_ax.set_xlim(max(0, temps - 60), temps)
                    self.canvas_ax.set_ylabel(self.dernier_unite, color='white')
                    self.canvas_ax.ticklabel_format(style='plain', useOffset=False)
                    self.canvas.draw()
        except Exception as e:
            self.labels["MODE"].setText("Erreur")
            self.labels["PLAGE"].setText("--")
            self.labels["MESURE"].setText(str(e))

    def closeEvent(self, event):
        self.timer.stop()
        try:
            self.ser.write(b"SYST:LOC\n")
            self.ser.close()
        except:
            pass
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MultimetreApp(port=port, afficher_graphique=graph)
    window.show()
    sys.exit(app.exec())
