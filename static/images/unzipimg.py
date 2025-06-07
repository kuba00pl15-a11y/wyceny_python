import zipfile
import os

# Ścieżka do pliku .zip (zmień nazwę pliku i ścieżkę jeśli trzeba)
zip_path = '/home/KubaKowalczykk/mysite/wyceny_python/static/images/images.zip'

# Folder, do którego chcesz wypakować pliki
output_dir = '/home/KubaKowalczykk/mysite/wyceny_python/static/images/'

# Utwórz folder, jeśli nie istnieje
os.makedirs(output_dir, exist_ok=True)

# Wypakuj zawartość .zip
with zipfile.ZipFile(zip_path, 'r') as zip_ref:
    zip_ref.extractall(output_dir)

print("Plik został wypakowany do:", output_dir)
