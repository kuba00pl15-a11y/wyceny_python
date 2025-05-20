import subprocess
import time
import os
import signal

# Przejdź do folderu projektu
os.chdir(r"C:\Users\justy\Desktop\wyceny_python")

# Ustaw zmienne środowiskowe
os.environ["FLASK_APP"] = "app.py"
os.environ["FLASK_ENV"] = "production"

# Uruchom Flask w tle
flask_process = subprocess.Popen(
    ["python", "-m", "flask", "run"],
    creationflags=subprocess.CREATE_NO_WINDOW,
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL
)

# Poczekaj chwilę na uruchomienie serwera
time.sleep(2)

# Otwórz stronę w przeglądarce (bez oczekiwania)
subprocess.Popen([
    "cmd", "/c", "start", "chrome", "--new-window", "http://127.0.0.1:5000"
], creationflags=subprocess.CREATE_NO_WINDOW)

# Skrypt kończy się tutaj, Flask działa w tle, cmd się zamyka
