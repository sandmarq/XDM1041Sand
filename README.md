# XDM1041 - Interface Graphique Python

🇫🇷 Interface graphique en temps réel pour le multimètre **OWON XDM1041**, écrite en Python avec **PyQt6**.  
🇬🇧 Real-time graphical interface for the **OWON XDM1041** multimeter, written in Python using **PyQt6**.

## 🇫🇷 Fonctionnalités / 🇬🇧 Features

- Connexion série avec commandes SCPI / Serial SCPI connection  
- Affichage du mode, plage et mesure / Mode, range, and measurement display  
- Thème sombre épuré / Clean dark theme  
- Graphique optionnel / Optional measurement graph  
- Configuration via `.env`

## 📦 Installation

### Cloner le projet / Clone the project

```bash
git clone https://github.com/sandmarq/XDM1041Sand.git
cd XDM1041Sand
```

### Créer un environnement virtuel / Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate  # ou 'source venv/bin/activate.fish' pour Fish
```

### Installer les dépendances / Install dependencies

```bash
pip install -r requirements.txt
```

## ⚙️ Configuration (.env)

Créez un fichier `.env` à la racine avec le contenu suivant (ou laissez vide pour les valeurs par défaut) :  
Create a `.env` file at the root with the following content (or leave it empty to use defaults):

```env
PORT=/dev/ttyUSB0
BAUDRATE=115200
TIMEOUT=0.2
GRAPH=True
```

## ▶️ Lancer l'application / Run the application

```bash
python main.py --port /dev/ttyUSB0 --graph
```

- `--port` : Spécifie le port série utilisé par le multimètre (ex. `/dev/ttyUSB0` sous Linux).  
  Specifies the serial port used by the multimeter (e.g., `/dev/ttyUSB0` on Linux).  
- `--graph` *(optionnel / optional)* : Active l'affichage du graphique en temps réel.  
  Enables the real-time measurement graph display. Without this option, the interface is more compact.

## 🐧 Dépendances Linux (si Qt ne se lance pas) / Linux Dependencies (if Qt doesn't start)

🇫🇷 Si vous avez une erreur Qt de type `Could not load the Qt platform plugin "xcb"` lors du démarrage de l'application, vous devez installer quelques bibliothèques système.  
🇬🇧 If you get a Qt error like `Could not load the Qt platform plugin "xcb"` when launching the app, you need to install some system libraries.

### 🔧 Pour Arch Linux, Manjaro, CachyOS, EndeavourOS :

```bash
sudo pacman -S libxcb xcb-util xcb-util-image xcb-util-keysyms xcb-util-renderutil xcb-util-wm libxkbcommon-x11 qt6-base xcb-util-cursor
```

### 🔧 Pour Debian, Ubuntu, Linux Mint :

```bash
sudo apt install libxcb-xinerama0 libxcb-cursor0 libxkbcommon-x11-0
```

🇫🇷 Sans ces librairies, Qt ne peut pas démarrer correctement avec le backend `xcb`, même s’il est installé.  
🇬🇧 Without these libraries, Qt won't start properly with the `xcb` backend, even if it's installed.

## 🖼️ Aperçu / Preview

![Capture](images/capture1.png)

## 📄 Licence

Ce projet est distribué sous la licence MIT.  
This project is licensed under the MIT License.

## 🤝 Contribuer / Contributing

Les contributions sont les bienvenues !  
Contributions are welcome! Fork, propose des améliorations ou rapporte un bug.