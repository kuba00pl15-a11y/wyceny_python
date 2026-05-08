from flask import Flask, render_template, request, redirect, url_for, Response, session, flash, jsonify
import math
from flask_login import LoginManager, login_user, logout_user, UserMixin, current_user
import json
import os
import pickle
import logging

app = Flask(__name__)
def wczytaj_ceny_obrobek():
    katalog = os.path.join(app.root_path, "data", "obrobki")
    obrobki = {}
    if not os.path.isdir(katalog):
        return obrobki

    for plik in os.listdir(katalog):
        if not (plik.startswith("obrobki_") and plik.endswith(".json")):
            continue

        nazwa = plik.replace("obrobki_", "").replace(".json", "").replace("_", " ").strip().lower().replace(" ", "")
        path = os.path.join(katalog, plik)
        try:
            with open(path, encoding="utf-8") as f:
                loaded = json.load(f)
                if isinstance(loaded, dict):
                    obrobki[nazwa] = loaded
                else:
                    logging.warning(f"Plik {path} nie zawiera obiektu JSON.")
        except Exception as e:
            logging.warning(f"Nie udało się wczytać obróbek z pliku {path}: {e}")
    return obrobki

obrobki_cennik = wczytaj_ceny_obrobek()


class Producent:
    def cena(self, d, s, g, typ, material=""):
        return 1.0

    def cena_jed(self, d, s, g, typ, material=""):
        return 1.0

    def mb(self, d):
        return d / 100

    def m2(self, d, s):
        return d / 100 * s / 100


class Stolarz(Producent):
    nazwa="Stolarz"
    def cena_jed(self, d, s, g, typ, material=""):
        tabelka = [
            [200, 250, 360, 420], [280, 400, 480, 550],
            [380, 480, 540, 700], [480, 550, 680, 730],
            [550, 670, 770, 860], [710, 770, 860, 970],
            [830, 950, 990, 1070], [900, 1030, 1160, 1230],
            [990, 1150, 1240, 1430]
        ]
        kolumna = int(g - 3)
        wiersz = int(math.ceil(s / 10) - 2)
        try:
            return tabelka[wiersz][kolumna]
        except IndexError:
            print(f"Błąd indeksu: wiersz={wiersz}, kolumna={kolumna}, szerokość={s}, grubość={g}")
            return 0

    def cena(self, d, s, g, typ, material=""):
        cena_jednostkowa = self.cena_jed(d, s, g, typ)
        return cena_jednostkowa * self.mb(d)

    @staticmethod
    def licz_cene_obrobki(nazwa_producenta, obrobka, ilosc, cena_produktu, mb, m2):
        dane = obrobki_cennik.get(nazwa_producenta.lower().replace(" ", ""), {}).get(obrobka)
        if not dane:
            return 0

        jednostka = dane["jednostka"]
        cena = dane["cena"]

        if obrobka.lower() in ["lakier", "nieregularne kształty"]:
            return 0.3 * cena_produktu
        elif dane.get("typ") == "od_produktu":
            return cena * cena_produktu
        elif jednostka == "ilosc":
            return cena * ilosc
        elif jednostka == "mb":
            return cena * mb
        elif jednostka == "m2":
            return cena * m2
        return 0


class Oretyparapety(Producent):
    nazwa="O rety parapety"
    def cena_jed(self, d, s, g, typ, material=""):
        try:
            with open('data/tabelka_oretyparapety.json', 'r') as file:
                tabelka_oretyparapety = json.load(file)
        except FileNotFoundError:
            raise FileNotFoundError("Plik 'tabelka.json' nie istnieje")

        kolumna = int(g - 2)
        if material in tabelka_oretyparapety and 0 <= kolumna < len(tabelka_oretyparapety[material]):
            return tabelka_oretyparapety[material][kolumna]
        else:
            raise ValueError("Invalid material or thickness")

    def cena(self, d, s, g, typ, material=""):
        cena_jednostkowa = self.cena_jed(d, s, g, typ, material)
        return cena_jednostkowa * self.m2(d, s)


    @staticmethod
    def licz_cene_obrobki(nazwa_producenta, obrobka, ilosc, cena_produktu, mb, m2):
        dane = obrobki_cennik.get(nazwa_producenta, {}).get(obrobka)
        if not dane:
            return 0

        jednostka = dane["jednostka"]
        cena = dane["cena"]

        if dane.get("typ") == "od_produktu":
            return cena * cena_produktu
        elif jednostka == "ilosc":
            return cena * ilosc
        elif jednostka == "mb":
            return cena * mb
        elif jednostka == "m2":
            return cena * m2
        return 0



class Olgran(Producent):
    nazwa="Olgran"
    def cena_jed(self, d, s, g, typ, material=""):
        try:
            with open('data/tabelka_olgran.json', 'r') as file:
                tabelka_olgran = json.load(file)
        except FileNotFoundError:
            raise FileNotFoundError("Plik 'tabelka.json' nie istnieje")

        kolumna = int(g - 2)
        if typ == "Blat":
            kolumna += 2
        if material in tabelka_olgran and 0 <= kolumna < len(tabelka_olgran[material]):
            return tabelka_olgran[material][kolumna]
        else:
            raise ValueError("Invalid material or thickness")

    def cena(self, d, s, g, typ, material=""):
            cena_jednostkowa = self.cena_jed(d, s, g, typ, material)
            return cena_jednostkowa * self.m2(d, s)

    @staticmethod
    def licz_cene_obrobki(nazwa_producenta, obrobka, ilosc, cena_produktu, mb, m2):
        dane = obrobki_cennik.get(nazwa_producenta, {}).get(obrobka)
        if not dane:
            return 0

        jednostka = dane["jednostka"]
        cena = dane["cena"]

        if dane.get("typ") == "od_produktu":
            return cena * cena_produktu
        elif jednostka == "ilosc":
            return cena * ilosc
        elif jednostka == "mb":
            return cena * mb
        elif jednostka == "m2":
            return cena * m2
        return 0



class Imperial(Producent):
    nazwa="Imperial"
    def cena_jed(self, d, s, g, typ, material=""):
        try:
            with open('data/tabelka_imperial.json', 'r') as file:
                tabelka_imperial = json.load(file)
        except FileNotFoundError:
            raise FileNotFoundError("Plik 'tabelka_imperial.json' nie istnieje")

        kolumna = int(g - 2)
        if typ == "Blat":
            kolumna += 2
        if material in tabelka_imperial and 0 <= kolumna < len(tabelka_imperial[material]):
            return tabelka_imperial[material][kolumna]
        else:
            raise ValueError("Nieprawidłowy materiał albo grubość")

    def cena(self, d, s, g, typ, material=""):
        cena_jednostkowa = self.cena_jed(d, s, g, typ, material)
        return cena_jednostkowa * self.m2(d, s)


    @staticmethod
    def licz_cene_obrobki(nazwa_producenta, obrobka, ilosc, cena_produktu, mb, m2):
        dane = obrobki_cennik.get(nazwa_producenta, {}).get(obrobka)
        if not dane:
            return 0

        jednostka = dane["jednostka"]
        cena = dane["cena"]

        if dane.get("typ") == "od_produktu":
            return cena * cena_produktu
        elif jednostka == "ilosc":
            return cena * ilosc
        elif jednostka == "mb":
            return cena * mb
        elif jednostka == "m2":
            return cena * m2
        return 0


class Formasystem(Producent):
    nazwa="Forma system"
    def cena_jed(self, d, s, g, typ, material=""):
        try:
            with open('data/tabelka_forma.json', 'r') as file:
                tabelka_forma = json.load(file)
        except FileNotFoundError:
            raise FileNotFoundError("Plik 'tabelka.json' nie istnieje")

        czesc = 0
        kolumna = 0
        przedzialy = []

        if g == 2.0:
            czesc = 1
            przedzialy = [151, 301, 501, 636, 751, 851, 1001, 1261, 1400]

        if g == 1.2:
            czesc = 0
            przedzialy = [151, 301, 501, 636, 751, 851, 1001, 1261, 1400]

        for wartosc in przedzialy:
            if s * 10 >= wartosc:
                kolumna += 1
                if kolumna == 8:
                    break
            else:
                break

        if material not in tabelka_forma:
            logging.warning(f"Nieznany materiał Forma system: {material}. Zwracam 0.")
            return 0

        try:
            return tabelka_forma[material][czesc][kolumna]
        except (IndexError, TypeError):
            logging.warning(
                f"Nieprawidłowe dane cennika dla materiału {material} (czesc={czesc}, kolumna={kolumna}). Zwracam 0."
            )
            return 0

    def cena(self, d, s, g, typ, material=""):
        cena_jednostkowa = self.cena_jed(d, s, g, typ, material)
        return cena_jednostkowa * self.mb(d) * 1.6

    @staticmethod
    def licz_cene_obrobki(nazwa_producenta, obrobka, ilosc, cena_produktu, mb, m2):
        dane = obrobki_cennik.get(nazwa_producenta, {}).get(obrobka)
        if not dane:
            return 0

        jednostka = dane["jednostka"]
        try:
            cena = float(dane["cena"])
        except ValueError:
            print(f"Nieprawidłowa cena w danych: {dane}")
            return 0

        if dane.get("typ") == "od_produktu":
            return cena * cena_produktu
        elif jednostka == "ilosc":
            return cena * ilosc
        elif jednostka == "mb":
            return cena * mb
        elif jednostka == "m2":
            return cena * m2
        return 0

producenty = {
    "Stolarz": Stolarz,
    "O rety parapety": Oretyparapety,
    "Olgran": Olgran,
    "Imperial": Imperial,
    "Forma system": Formasystem
}
def get_zamowienie_from_session():
    return Zamowienie.from_dict(session.get("zamowienie", Zamowienie().to_dict()))

def save_zamowienie_to_session(zamowienie):
    session["zamowienie"] = zamowienie.to_dict()

def get_klient_from_session():
    data = session.get("klient")
    return Klient.from_dict(data) if isinstance(data, dict) else Klient()

def save_klient_to_session(klient):
    session["klient"] = klient.to_dict()

class Produkt:
    def __init__(self, dlugosc, szerokosc, grubosc, ilosc, typ, material, producent, obrobki=None, rabat=0):
        self.dlugosc = dlugosc
        self.szerokosc = szerokosc
        self.grubosc = grubosc
        self.ilosc = ilosc
        self.typ = typ
        self.material = material
        self.producent = producent
        self.obrobki = obrobki or []
        self.rabat = rabat
        self._cena_bazowa = None

    def _wylicz_cene_bazowa(self):
        if self._cena_bazowa is None:
            try:
                self._cena_bazowa = self.producent.cena(
                    self.dlugosc,
                    self.szerokosc,
                    self.grubosc,
                    self.typ,
                    self.material,
                )
            except Exception as e:
                logging.warning(
                    f"Nie udało się wyliczyć ceny bazowej dla materiału {self.material} ({self.producent.nazwa}): {e}. Zwracam 0."
                )
                self._cena_bazowa = 0
        return self._cena_bazowa

    def cena_jednostkowa(self):
        return self.producent.cena_jed(self.dlugosc, self.szerokosc, self.grubosc, self.typ, self.material)

    def cena(self):
        return round(self._wylicz_cene_bazowa() * self.ilosc)

    def cena_przed_rabatem(self):
        return self.cena()

    def cena_po_rabacie(self):
        cena = self.cena_przed_rabatem()
        if self.rabat:
            cena = cena - cena * (self.rabat / 100)
        return round(cena)

    def cena_obrobek(self):
        suma = 0
        mb = self.producent.mb(self.dlugosc)
        m2 = self.producent.m2(self.dlugosc, self.szerokosc)
        cena_bazowa = self._wylicz_cene_bazowa()
        klucz_producenta = self.producent.nazwa.lower().replace(" ", "")

        for obrobka in self.obrobki:
            ilosc = 1
            if ":" in obrobka:
                ilosc = int(obrobka.split(":")[1])
                obrobka = obrobka.split(":")[0]

            if hasattr(self.producent, "licz_cene_obrobki"):
                cena_obrobki = self.producent.licz_cene_obrobki(
                    klucz_producenta, obrobka, ilosc, cena_bazowa, mb, m2
                )
                try:
                    suma += float(cena_obrobki) * self.ilosc
                except ValueError:
                    print(f"Nieprawidłowa cena dla obróbki: {obrobka} → {cena_obrobki}")

        return round(suma, 2)


    def obrobki_z_cenami(self):
        wynik = {}
        mb = self.producent.mb(self.dlugosc)
        m2 = self.producent.m2(self.dlugosc, self.szerokosc)
        cena_bazowa = self._wylicz_cene_bazowa()
        klucz_producenta = self.producent.nazwa.lower().replace(" ", "")

        for obrobka_raw in self.obrobki:
            if ":" in obrobka_raw:
                nazwa, ilosc = obrobka_raw.split(":")
                ilosc = int(ilosc)
            else:
                nazwa, ilosc = obrobka_raw, 1

            ilosc_calkowita = ilosc * self.ilosc

            if nazwa not in wynik:
                wynik[nazwa] = {"ilosc": 0, "cena_jednostkowa": 0.0}

            cena = self.producent.licz_cene_obrobki(klucz_producenta, nazwa, 1, cena_bazowa, mb, m2)
            wynik[nazwa]["ilosc"] += ilosc_calkowita
            wynik[nazwa]["cena_jednostkowa"] = round(cena, 2)

        return [(nazwa, dane["ilosc"], dane["cena_jednostkowa"]) for nazwa, dane in wynik.items()]
    
    def to_dict(self):
        return {
            "dlugosc": self.dlugosc,
            "szerokosc": self.szerokosc,
            "grubosc": self.grubosc,
            "ilosc": self.ilosc,
            "typ": self.typ,
            "material": self.material,
            "producent": self.producent.nazwa,
            "obrobki": self.obrobki,
            "rabat": self.rabat
        }
    
    @classmethod
    def from_dict(cls, data, producent):
        return cls(
            dlugosc=data["dlugosc"],
            szerokosc=data["szerokosc"],
            grubosc=data["grubosc"],
            ilosc=data["ilosc"],
            typ=data["typ"],
            material=data["material"],
            producent=producent,
            obrobki=data.get("obrobki", []),
            rabat=data.get("rabat", 0)
        )




class Zamowienie:
    def __init__(self):
        self.lista_produktow = []
        self.wlasne_obrobki = []

    def dodaj_produkt(self, produkt):
        self.lista_produktow.append(produkt)

    def laczna_cena(self):
        return sum([produkt.cena() + produkt.cena_obrobek() for produkt in self.lista_produktow])
    
    def to_dict(self):
        return {
            "lista_produktow": [p.to_dict() for p in self.lista_produktow],
            "wlasne_obrobki": self.wlasne_obrobki
        }
    @classmethod
    def from_dict(cls, data):
        obj = cls()
        for produkt_data in data.get("lista_produktow", []):
            producent_klasa = producenty.get(produkt_data["producent"], Stolarz)
            produkt = Produkt.from_dict(produkt_data, producent_klasa())
            obj.lista_produktow.append(produkt)
        obj.wlasne_obrobki = data.get("wlasne_obrobki", [])
        return obj
    
    


class Klient:
    def __init__(self):
        self.imie = ""
        self.adres = ""
        self.nr_tel = ""
        self.adres_email = ""
        self.kto_oferta = ""
        self.lista_zamowien = []
        self.dni = 0
        self.tygodnie = 0
        self.miesiace = 0

    def dodaj_zamowienie(self, zamowienie):
        self.lista_zamowien.append(zamowienie)

    def wypisz_dane(self):
        return f"Imię: {self.imie}, Adres: {self.adres}, Telefon: {self.nr_tel}, Adres email: {self.adres_email}, Ofertę przygotowuje: {self.kto_oferta}"

    def aktualizuj_dane(self, imie="", adres="", nr_tel="", adres_email="", kto_oferta="", dni=0, tygodnie=0, miesiace=0):
        self.imie = imie if imie else ""
        self.adres = adres if adres else ""
        self.nr_tel = nr_tel if nr_tel else ""
        self.adres_email = adres_email if adres_email else ""
        self.kto_oferta = kto_oferta if kto_oferta else ""
        self.dni = dni
        self.tygodnie = tygodnie
        self.miesiace = miesiace

    def to_dict(self):
        return {
            "imie": self.imie,
            "adres": self.adres,
            "nr_tel": self.nr_tel,
            "adres_email": self.adres_email,
            "kto_oferta": self.kto_oferta,
            "lista_zamowien": [z.to_dict() for z in self.lista_zamowien],
            "dni": self.dni,
            "tygodnie": self.tygodnie,
            "miesiace": self.miesiace
        }

    @classmethod
    def from_dict(cls, data):
        obj = cls()
        obj.imie = data.get("imie", "")
        obj.adres = data.get("adres", "")
        obj.nr_tel = data.get("nr_tel", "")
        obj.adres_email = data.get("adres_email", "")
        obj.kto_oferta = data.get("kto_oferta", "")
        obj.dni = data.get("dni", 0)
        obj.tygodnie = data.get("tygodnie", 0)
        obj.miesiace = data.get("miesiace", 0)
        for zamowienie_dict in data.get("lista_zamowien", []):
            obj.lista_zamowien.append(Zamowienie.from_dict(zamowienie_dict))
        return obj

def get_klient_from_session():
    data = session.get("klient")
    if isinstance(data, dict):
        return Klient.from_dict(data)
    return Klient()


# Read SECRET_KEY from environment (set on production host). Falls back to an explicit dev default.
secret = os.environ.get("SECRET_KEY")
if not secret:
    logging.warning("SECRET_KEY not set in environment; using insecure default. Set SECRET_KEY in production.")
app.secret_key = secret or "dev-secret-please-change"

@app.before_request
def init_session_once():
    if "zamowienie" not in session:
        save_zamowienie_to_session(Zamowienie())
    if "klient" not in session:
        save_klient_to_session(Klient())

# Jinja filter to format timestamps
from datetime import datetime
@app.template_filter('datetimeformat')
def datetimeformat(value):
    try:
        return datetime.fromtimestamp(int(value)).strftime('%d.%m.%Y %H:%M')
    except Exception:
        return value

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Configure server-side sessions (filesystem). On PythonAnywhere this avoids large cookies.
# Set SESSION_FILE_DIR via env var or default to instance folder.
from flask_session import Session

app.config.setdefault('SESSION_TYPE', 'filesystem')
session_file_dir = os.environ.get('SESSION_FILE_DIR', os.path.join(app.instance_path, 'flask_session'))
app.config.setdefault('SESSION_FILE_DIR', session_file_dir)
app.config.setdefault('SESSION_PERMANENT', False)
# Ensure directory exists
os.makedirs(app.config['SESSION_FILE_DIR'], exist_ok=True)
Session(app)


# Users configuration: read admin username and password/hash from environment to avoid hardcoding secrets.
# Supported env vars:
#  - ADMIN_USER (username)
#  - ADMIN_PASSWORD_HASH (werkzeug hash, preferred)
#  - ADMIN_PASSWORD (plain password, only for convenience; will be hashed on startup and a warning logged)

from werkzeug.security import generate_password_hash, check_password_hash

users = {}
admin_user = os.environ.get('ADMIN_USER', 'Drewkam')
admin_password_hash = os.environ.get('ADMIN_PASSWORD_HASH')
admin_password_plain = os.environ.get('ADMIN_PASSWORD')
if not admin_password_hash and admin_password_plain:
    # Convenience: hash the provided plain password at startup (not recommended for production long-term)
    logging.warning('ADMIN_PASSWORD provided in env — it will be hashed at startup. Prefer setting ADMIN_PASSWORD_HASH instead.')
    admin_password_hash = generate_password_hash(admin_password_plain)

if admin_password_hash:
    users[admin_user] = {'password_hash': admin_password_hash}
else:
    # For backwards compatibility during local development only: set a default (very insecure)
    logging.warning('No admin credentials found in environment; using default insecure password for user Drewkam.')
    users[admin_user] = {'password_hash': generate_password_hash('1105')}

# Klasa użytkownika
class User(UserMixin):
    def __init__(self, username):
        self.id = username

@login_manager.user_loader
def load_user(user_id):
    if user_id in users:
        return User(user_id)
    return None

# Helper to validate credentials
def validate_credentials(username, password):
    user = users.get(username)
    if not user:
        return False
    stored_hash = user.get('password_hash')
    return check_password_hash(stored_hash, password)



@app.before_request
def require_login():
    public_endpoints = ['login', 'static']

    if request.endpoint not in public_endpoints and not current_user.is_authenticated:
        return redirect(url_for('login'))

def ustaw_cookie_jako_sesyjny():
    session.permanent = False


@app.route("/uslugi", methods=["POST"])
def uslugi():

    session["usluga_transport"] = "transport" in request.form
    session["usluga_pomiar"] = "pomiar" in request.form
    session["usluga_montaz"] = "montaz" in request.form
    session["usluga_pmt"] = "pomiar_transport_montaz" in request.form

    session["cena_pomiaruu"] = request.form.get("cena_pomiaru", "")
    session["cena_transportt"] = request.form.get("cena_transportu", "")
    session["cena_montazuu"] = request.form.get("cena_montazu", "")
    session["cena_ppmmtt"] = request.form.get("cena_ppmmtt", "")

    return redirect(url_for("strona_glowna"))


@app.route("/", methods=["POST", "GET"])
def strona_glowna():
    zamowienie = get_zamowienie_from_session()
    klient = get_klient_from_session()

    return render_template("strona_glowna.html.j2",
        zamowienie=zamowienie,
        klient=klient,
        laczna_cena_z_uslugami=0.0,
        usluga_pomiar = session.get("usluga_pomiar", False),
        usluga_montaz = session.get("usluga_montaz", False),
        usluga_transport = session.get("usluga_transport", False),
        usluga_pmt = session.get("usluga_pmt", False),
        cena_montazuu=session.get('cena_montazuu', 0),
        cena_pomiaruu=session.get('cena_pomiaruu', 0),
        cena_transportt=session.get('cena_transportt', 0),
        cena_ppmmtt=session.get('cena_ppmmtt', 0),
        custom_obrobki=zamowienie.wlasne_obrobki)

@app.route("/aktualizuj_klienta", methods=["POST"])
def aktualizuj_klienta():
    klient = get_klient_from_session() 

    klient.aktualizuj_dane(
        imie=request.form.get("imie"),
        adres=request.form.get("adres"),
        nr_tel=request.form.get("nr_tel"),
        adres_email=request.form.get("adres_email"),
        kto_oferta=request.form.get("kto_oferta"),
        dni=int(request.form.get("dni", 0)),
        tygodnie=int(request.form.get("tygodnie", 2)),
        miesiace=int(request.form.get("miesiace", 0))
    )
    session["klient"] = klient.to_dict()
    return redirect(url_for("strona_glowna"))


@app.route('/dodaj_produkt', methods=['GET', 'POST'])
def dodaj_produkt():
    zamowienie = get_zamowienie_from_session()

    if request.method == "POST":
        produkty = {}
        for klucz, wartosc in request.form.items():
            if "_" in klucz:
                pole, id_ = klucz.rsplit("_", 1)
                produkty.setdefault(id_, {})[pole] = wartosc

        paczki_produktow = []
        for id_, dane in produkty.items():
            try:
                produkt_data = {
                    "producent": dane.get("producent"),
                    "material": dane.get("material"),
                    "typ": dane.get("typ"),
                    "rabat": float(dane.get("rabat", "0").replace(",", ".")),
                    "dlugosc": float(dane.get("dlugosc", "0").replace(",", ".")),
                    "szerokosc": float(dane.get("szerokosc", "0").replace(",", ".")),
                    "grubosc": float(dane.get("grubosc", 0)),
                    "ilosc": int(dane.get("ilosc", 0)),
                    "obrobki_z_iloscia": {
                        o.split(":")[0].strip(): int(o.split(":")[1]) if ":" in o else 1
                        for o in request.form.get(f"obrobki_{id_}", "").split(",") if o.strip()
                    }
                }
                paczki_produktow.append(produkt_data)
            except ValueError as e:
                print(f"Błąd w danych produktu {id_}: {e}")

        # Filter out incomplete products and log them
        przefiltrowane = []
        for p in paczki_produktow:
            if not p.get('producent') or not p.get('material') or not p.get('typ') or int(p.get('ilosc', 0)) <= 0:
                print(f"Pomijam niekompletne dane produktu: {p}")
                continue
            przefiltrowane.append(p)

        nowa_lista = []

        for produkt_data in przefiltrowane:
            try:
                producent = producenty.get(produkt_data["producent"], Stolarz)()
                obrobki_rozwiniete = [f"{n}:{i}" for n, i in produkt_data["obrobki_z_iloscia"].items()]

                produkt = Produkt(
                    producent=producent,
                    material=produkt_data["material"],
                    typ=produkt_data["typ"],
                    rabat=produkt_data["rabat"],
                    dlugosc=produkt_data["dlugosc"],
                    szerokosc=produkt_data["szerokosc"],
                    grubosc=produkt_data["grubosc"],
                    ilosc=produkt_data["ilosc"],
                    obrobki=obrobki_rozwiniete
                )
                nowa_lista.append(produkt)
            except Exception as e:
                print(f"Błąd podczas dodawania produktu: {produkt_data}, {e}")

        # Only overwrite existing list if we parsed at least one valid product
        if nowa_lista:
            zamowienie.lista_produktow = nowa_lista
        else:
            print('Brak poprawnych produktów w żądaniu — nie nadpisuję listy produktów w sesji.')

        nowe_obrobki = []
        for key, value in request.form.items():
            if key.startswith("custom_obrobka_nazwa_"):
                index = key.split("_")[-1]
                nazwa = value.strip()
                try:
                    cena = float(request.form.get(f"custom_obrobka_cena_{index}", "0").replace(",", "."))
                    if nazwa:
                        nowe_obrobki.append({"nazwa": nazwa, "cena": cena})
                except ValueError:
                    pass

        zamowienie.wlasne_obrobki = nowe_obrobki
        save_zamowienie_to_session(zamowienie)

        return redirect(url_for("strona_glowna"))

    # GET
    obrobki_data = {}
    forma_obrobki_groups = _load_forma_obrobki_groups()
    sciezka = "data/obrobki"
    if os.path.exists(sciezka):
        for plik in os.listdir(sciezka):
            if plik.endswith(".json"):
                producent = plik.replace(".json", "").replace("obrobki_", "")
                with open(os.path.join(sciezka, plik), "r", encoding="utf-8") as f:
                    try:
                        obrobki_data[producent] = json.load(f)
                    except json.JSONDecodeError:
                        print(f"Błąd wczytywania JSON z pliku {plik}")

    return render_template(
        "dodaj_produkt.html",
        lista_produktow=zamowienie.lista_produktow,
        obrobki_data=obrobki_data,
        forma_obrobki_groups=forma_obrobki_groups,
        custom_obrobki=zamowienie.wlasne_obrobki
    )
    



from PDF_drewkam import generuj_PDF
from flask import request, Response

@app.route("/pdf", methods=["GET"])
def pdf():

    pdf_buffer = generuj_PDF(
        Zamowienie.from_dict(session['zamowienie']),
        Klient.from_dict(session['klient']),
        usluga_pomiar = session.get("usluga_pomiar", False),
        usluga_montaz = session.get("usluga_montaz", False),
        usluga_transport = session.get("usluga_transport", False),
        usluga_pmt = session.get("usluga_pmt", False),
        cena_montazuu=session.get('cena_montazuu', 0),
        cena_pomiaruu=session.get('cena_pomiaruu', 0),
        cena_transportt=session.get('cena_transportt', 0),
        cena_ppmmtt=session.get('cena_ppmmtt', 0),
        custom_obrobki=Zamowienie.from_dict(session['zamowienie']).wlasne_obrobki
    )

    return Response(pdf_buffer, mimetype="application/pdf",
                    headers={"Content-Disposition": "inline; filename=wycena_pelna.pdf"})

from PDF_klient import generuj_PDF_klient
from flask import request, Response

@app.route("/pdf_k", methods=["GET"])
def pdf_klient():

    pdf_buffer = generuj_PDF_klient(
        Zamowienie.from_dict(session['zamowienie']),
        Klient.from_dict(session['klient']),        
        usluga_pomiar = session.get("usluga_pomiar", False),
        usluga_montaz = session.get("usluga_montaz", False),
        usluga_transport = session.get("usluga_transport", False),
        usluga_pmt = session.get("usluga_pmt", False),
        cena_montazuu=session.get('cena_montazuu', 0),
        cena_pomiaruu=session.get('cena_pomiaruu', 0),
        cena_transportt=session.get('cena_transportt', 0),
        cena_ppmmtt=session.get('cena_ppmmtt', 0),
        custom_obrobki=Zamowienie.from_dict(session['zamowienie']).wlasne_obrobki
    )

    return Response(pdf_buffer, mimetype="application/pdf",
                    headers={"Content-Disposition": "inline; filename=wycena_klient.pdf"})

@app.before_request
def usun_blednego_klienta_jesli_bytes():
    if isinstance(session.get("klient"), bytes):
        print("Usuwam klienta typu bytes z sesji!")
        session.pop("klient", None)

@app.route('/reset_strony', methods=['POST'])
def reset_strony():
    session.clear()
    return redirect(url_for('login'))



@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if validate_credentials(username, password):
            login_user(User(username))
            flash('Zalogowano pomyślnie!')
            zamowienie = Zamowienie()
            session['zamowienie'] = zamowienie.to_dict()

            session["klient"] = Klient().to_dict()
            session["usluga_pomiar"]=False
            session["usluga_transport"]=False
            session["usluga_montaz"]=False
            session["usluga_pmt"]=False
            session["cena_pomiaruu"]=0
            session["cena_transportt"]=0
            session["cena_montazuu"]=0
            session["cena_ppmmtt"]=0
            return redirect(url_for('strona_glowna'))
        else:
            flash('Nieprawidłowy login lub hasło.')
    return render_template('login.html')


@app.route('/logout')
def logout():
    logout_user()
    flash('Wylogowano.')
    return redirect(url_for('login'))

from flask_login import login_required

# --- Admin: simple JSON editor for data files (protected) ---

def get_editable_files():
    base = os.path.join(app.root_path, 'data')
    files = []
    for root, dirs, filenames in os.walk(base):
        for fn in filenames:
            if fn.endswith('.json'):
                rel = os.path.relpath(os.path.join(root, fn), app.root_path)
                files.append(rel.replace('\\', '/'))
    return files


MATERIAL_SCHEMAS = {
    "Forma system": {
        "file": "data/tabelka_forma.json",
        "thicknesses": [1.2, 2.0],
        "mode": "forma",
    },
    "Imperial": {
        "file": "data/tabelka_imperial.json",
        "thicknesses": [2.0, 3.0],
        "mode": "4col",
        "columns": [
            {"key": "parapet_2_0", "label": "Parapet 2.0"},
            {"key": "parapet_3_0", "label": "Parapet 3.0"},
            {"key": "blat_2_0", "label": "Blat 2.0"},
            {"key": "blat_3_0", "label": "Blat 3.0"},
        ],
    },
    "Olgran": {
        "file": "data/tabelka_olgran.json",
        "thicknesses": [2.0, 3.0],
        "mode": "4col",
        "columns": [
            {"key": "parapet_2_0", "label": "Parapet 2.0"},
            {"key": "parapet_3_0", "label": "Parapet 3.0"},
            {"key": "blat_2_0", "label": "Blat 2.0"},
            {"key": "blat_3_0", "label": "Blat 3.0"},
        ],
    },
    "O rety parapety": {
        "file": "data/tabelka_oretyparapety.json",
        "thicknesses": [2.0, 3.0],
        "mode": "2col",
        "columns": [
            {"key": "parapet_2_0", "label": "Parapet 2.0"},
            {"key": "parapet_3_0", "label": "Parapet 3.0"},
        ],
    },
}

OBROBKI_SCHEMAS = {
    "Forma system": "data/obrobki/obrobki_formasystem.json",
    "Imperial": "data/obrobki/obrobki_imperial.json",
    "Olgran": "data/obrobki/obrobki_olgran.json",
    "O rety parapety": "data/obrobki/obrobki_oretyparapety.json",
    "Stolarz": "data/obrobki/obrobki_stolarz.json",
}

OBROBKI_UNIT_OPTIONS = [
    {"value": "ilosc", "label": "szt."},
    {"value": "mb", "label": "mb"},
    {"value": "m2", "label": "m2"},
    {"value": "procent", "label": "%"},
]

OBROBKI_TYPE_OPTIONS = [
    {"value": "", "label": "standard"},
    {"value": "od_produktu", "label": "od ceny produktu"},
]

FORMA_GROUPS_FILE = os.path.join("data", "forma_material_konglomeraty.json")
FORMA_GROUP_DEFAULT = "1"
FORMA_GROUP_OPTIONS = {"1", "2"}
FORMA_OBROBKI_GROUPS_FILE = os.path.join("data", "obrobki", "forma_obrobki_groups.json")
FORMA_OBROBKI_GROUP_DEFAULT = "1"
FORMA_OBROBKI_GROUP_OPTIONS = {"1", "2"}


def _obrobki_file_path(producent):
    rel = OBROBKI_SCHEMAS.get(producent)
    if not rel:
        return None
    return os.path.join(app.root_path, rel)


def _normalize_obrobka_unit(value):
    val = str(value or "").strip().lower()
    return val or "ilosc"


def _normalize_obrobka_type(value):
    val = str(value or "").strip().lower()
    return "od_produktu" if val == "od_produktu" else ""


def _load_obrobki_table(producent):
    path = _obrobki_file_path(producent)
    if not path:
        raise ValueError("Nieznany producent")
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)
        if not isinstance(raw, dict):
            raise ValueError("Nieprawidłowy format danych obróbek")
        return raw


def _save_obrobki_table(producent, data):
    path = _obrobki_file_path(producent)
    if not path:
        raise ValueError("Nieznany producent")

    backup = path + ".bak"
    tmp_path = path + ".tmp"

    try:
        import shutil
        shutil.copy2(path, backup)
    except Exception as e:
        logging.warning(f"Nie udało się utworzyć backupu dla {path}: {e}")

    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    os.replace(tmp_path, path)

    global obrobki_cennik
    obrobki_cennik = wczytaj_ceny_obrobek()


def _serialize_obrobka_item(name, raw_value, producent=None):
    raw = raw_value if isinstance(raw_value, dict) else {}
    item = {
        "name": str(name),
        "unit": _normalize_obrobka_unit(raw.get("jednostka", "ilosc")),
        "price": _to_float(raw.get("cena"), 0),
        "type": _normalize_obrobka_type(raw.get("typ", "")),
    }
    if producent == "Forma system":
        groups = _load_forma_obrobki_groups()
        item["group"] = groups.get(str(name), _guess_forma_obrobka_group(name))
    return item


def _build_raw_obrobka_value(unit, price, calc_type):
    item = {
        "jednostka": _normalize_obrobka_unit(unit),
        "cena": _to_float(price, 0),
    }
    normalized_type = _normalize_obrobka_type(calc_type)
    if normalized_type:
        item["typ"] = normalized_type
    return item


def _forma_obrobki_groups_path():
    return os.path.join(app.root_path, FORMA_OBROBKI_GROUPS_FILE)


def _normalize_forma_obrobka_group(value):
    value = str(value or "").strip()
    return value if value in FORMA_OBROBKI_GROUP_OPTIONS else FORMA_OBROBKI_GROUP_DEFAULT


def _guess_forma_obrobka_group(name):
    return "2" if "spiek" in str(name).lower() else "1"


def _load_forma_obrobki_groups():
    path = _forma_obrobki_groups_path()
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
            if not isinstance(raw, dict):
                return {}
            return {str(k): _normalize_forma_obrobka_group(v) for k, v in raw.items()}
    except Exception as e:
        logging.warning(f"Nie udało się wczytać mapy grup obróbek Forma system: {e}")
        return {}


def _save_forma_obrobki_groups(groups):
    path = _forma_obrobki_groups_path()
    backup = path + ".bak"
    tmp_path = path + ".tmp"

    try:
        import shutil
        if os.path.exists(path):
            shutil.copy2(path, backup)
    except Exception as e:
        logging.warning(f"Nie udało się utworzyć backupu mapy grup obróbek: {e}")

    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(groups, f, ensure_ascii=False, indent=4)
    os.replace(tmp_path, path)


def _forma_groups_path():
    return os.path.join(app.root_path, FORMA_GROUPS_FILE)


def _normalize_forma_group(value):
    value = str(value).strip()
    return value if value in FORMA_GROUP_OPTIONS else FORMA_GROUP_DEFAULT


def _load_forma_groups():
    path = _forma_groups_path()
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
            if not isinstance(raw, dict):
                return {}
            return {str(k): _normalize_forma_group(v) for k, v in raw.items()}
    except Exception as e:
        logging.warning(f"Nie udało się wczytać mapy grup Forma system: {e}")
        return {}


def _save_forma_groups(groups):
    path = _forma_groups_path()
    backup = path + ".bak"
    tmp_path = path + ".tmp"

    try:
        import shutil
        if os.path.exists(path):
            shutil.copy2(path, backup)
    except Exception as e:
        logging.warning(f"Nie udało się utworzyć backupu mapy grup: {e}")

    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(groups, f, ensure_ascii=False, indent=4)
    os.replace(tmp_path, path)


def _forma_columns():
    columns = []
    for idx in range(1, 10):
        columns.append({"key": f"t12_p{idx}", "label": f"1.2 / P{idx}"})
    for idx in range(1, 10):
        columns.append({"key": f"t20_p{idx}", "label": f"2.0 / P{idx}"})
    return columns


def _material_schema_with_columns(producent):
    schema = MATERIAL_SCHEMAS.get(producent)
    if not schema:
        return None
    if schema["mode"] == "forma":
        return {
            "producent": producent,
            "thicknesses": schema["thicknesses"],
            "mode": schema["mode"],
            "columns": _forma_columns(),
            "groupOptions": [
                {"value": "1", "label": "Konglomeraty"},
                {"value": "2", "label": "Dekton"},
            ],
        }
    return {
        "producent": producent,
        "thicknesses": schema["thicknesses"],
        "mode": schema["mode"],
        "columns": schema["columns"],
    }


def _material_file_path(producent):
    schema = MATERIAL_SCHEMAS.get(producent)
    if not schema:
        return None
    return os.path.join(app.root_path, schema["file"])


def _load_material_table(producent):
    path = _material_file_path(producent)
    if not path:
        raise ValueError("Nieznany producent")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_material_table(producent, data):
    path = _material_file_path(producent)
    if not path:
        raise ValueError("Nieznany producent")

    backup = path + ".bak"
    tmp_path = path + ".tmp"

    try:
        import shutil
        shutil.copy2(path, backup)
    except Exception as e:
        logging.warning(f"Nie udało się utworzyć backupu dla {path}: {e}")

    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    os.replace(tmp_path, path)


def _to_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _serialize_material_item(producent, material, raw_value):
    schema = MATERIAL_SCHEMAS[producent]
    mode = schema["mode"]
    prices = {}

    if mode == "forma":
        part_12 = raw_value[0] if isinstance(raw_value, list) and len(raw_value) > 0 else []
        part_20 = raw_value[1] if isinstance(raw_value, list) and len(raw_value) > 1 else []
        for idx in range(9):
            prices[f"t12_p{idx + 1}"] = _to_float(part_12[idx] if idx < len(part_12) else 0)
        for idx in range(9):
            prices[f"t20_p{idx + 1}"] = _to_float(part_20[idx] if idx < len(part_20) else 0)
    elif mode == "4col":
        raw = raw_value if isinstance(raw_value, list) else []
        keys = ["parapet_2_0", "parapet_3_0", "blat_2_0", "blat_3_0"]
        for idx, key in enumerate(keys):
            prices[key] = _to_float(raw[idx] if idx < len(raw) else 0)
    elif mode == "2col":
        raw = raw_value if isinstance(raw_value, list) else []
        keys = ["parapet_2_0", "parapet_3_0"]
        for idx, key in enumerate(keys):
            prices[key] = _to_float(raw[idx] if idx < len(raw) else 0)

    item = {"material": material, "prices": prices}
    if producent == "Forma system":
        groups = _load_forma_groups()
        item["group"] = groups.get(material, FORMA_GROUP_DEFAULT)
    return item


def _build_raw_material_value(producent, prices):
    schema = MATERIAL_SCHEMAS[producent]
    mode = schema["mode"]

    if mode == "forma":
        part_12 = []
        part_20 = []
        for idx in range(1, 10):
            part_12.append(_to_float(prices.get(f"t12_p{idx}"), 0.0))
        for idx in range(1, 10):
            part_20.append(_to_float(prices.get(f"t20_p{idx}"), 0.0))
        return [part_12, part_20]

    if mode == "4col":
        keys = ["parapet_2_0", "parapet_3_0", "blat_2_0", "blat_3_0"]
        return [_to_float(prices.get(k), 0.0) for k in keys]

    keys = ["parapet_2_0", "parapet_3_0"]
    return [_to_float(prices.get(k), 0.0) for k in keys]


@app.route('/api/materials', methods=['GET'])
def api_materials():
    material_map = {}
    thickness_map = {}
    forma_groups = _load_forma_groups()

    for producent, schema in MATERIAL_SCHEMAS.items():
        try:
            table = _load_material_table(producent)
            names = sorted(table.keys(), key=lambda x: x.lower())
        except Exception as e:
            logging.warning(f"Nie udało się wczytać cennika dla {producent}: {e}")
            names = []

        material_map[producent] = names
        for material in names:
            if material not in thickness_map:
                thickness_map[material] = {}
            thickness_map[material][producent] = schema["thicknesses"]

    # Stolarz pozostaje pozycją stałą
    material_map["Stolarz"] = ["Dąb"]
    if "Dąb" not in thickness_map:
        thickness_map["Dąb"] = {}
    thickness_map["Dąb"]["Stolarz"] = [3.0, 4.0, 5.0, 6.0]

    return jsonify({"materials": material_map, "thicknesses": thickness_map, "forma_groups": forma_groups})


@app.route('/api/materials/schema', methods=['GET'])
def api_materials_schema():
    producent = request.args.get('producent', '').strip()
    schema = _material_schema_with_columns(producent)
    if not schema:
        return jsonify({"error": "Nieznany producent"}), 400
    return jsonify(schema)


@app.route('/api/materials/details', methods=['GET'])
def api_materials_details():
    producent = request.args.get('producent', '').strip()
    if producent not in MATERIAL_SCHEMAS:
        return jsonify({"error": "Nieznany producent"}), 400

    table = _load_material_table(producent)
    items = []
    for material, raw_value in table.items():
        items.append(_serialize_material_item(producent, material, raw_value))
    items.sort(key=lambda x: x["material"].lower())

    return jsonify({
        "producent": producent,
        "schema": _material_schema_with_columns(producent),
        "items": items,
    })


@app.route('/api/materials', methods=['POST'])
def api_materials_create():
    payload = request.get_json(silent=True) or {}
    producent = (payload.get('producent') or '').strip()
    material = (payload.get('material') or '').strip()
    prices = payload.get('prices') or {}
    group = _normalize_forma_group(payload.get('group', FORMA_GROUP_DEFAULT))

    if producent not in MATERIAL_SCHEMAS:
        return jsonify({"error": "Nieznany producent"}), 400
    if not material:
        return jsonify({"error": "Nazwa materiału jest wymagana"}), 400

    table = _load_material_table(producent)
    if material in table:
        return jsonify({"error": "Materiał już istnieje"}), 409

    table[material] = _build_raw_material_value(producent, prices)
    _save_material_table(producent, table)

    if producent == "Forma system":
        groups = _load_forma_groups()
        groups[material] = group
        _save_forma_groups(groups)

    return jsonify({"status": "ok", "message": "Materiał dodany"}), 201


@app.route('/api/materials/<path:material_name>', methods=['PUT'])
def api_materials_update(material_name):
    payload = request.get_json(silent=True) or {}
    producent = (payload.get('producent') or request.args.get('producent') or '').strip()
    nowa_nazwa = (payload.get('material') or material_name or '').strip()
    prices = payload.get('prices') or {}
    group = _normalize_forma_group(payload.get('group', FORMA_GROUP_DEFAULT))

    if producent not in MATERIAL_SCHEMAS:
        return jsonify({"error": "Nieznany producent"}), 400

    table = _load_material_table(producent)
    if material_name not in table:
        return jsonify({"error": "Nie znaleziono materiału"}), 404

    if nowa_nazwa != material_name and nowa_nazwa in table:
        return jsonify({"error": "Materiał o nowej nazwie już istnieje"}), 409

    raw_value = _build_raw_material_value(producent, prices)
    if nowa_nazwa != material_name:
        table.pop(material_name)
    table[nowa_nazwa] = raw_value

    _save_material_table(producent, table)

    if producent == "Forma system":
        groups = _load_forma_groups()
        if material_name in groups:
            groups.pop(material_name)
        groups[nowa_nazwa] = group
        _save_forma_groups(groups)

    return jsonify({"status": "ok", "message": "Materiał zaktualizowany"})


@app.route('/api/materials/<path:material_name>', methods=['DELETE'])
def api_materials_delete(material_name):
    producent = (request.args.get('producent') or '').strip()
    if producent not in MATERIAL_SCHEMAS:
        return jsonify({"error": "Nieznany producent"}), 400

    table = _load_material_table(producent)
    if material_name not in table:
        return jsonify({"error": "Nie znaleziono materiału"}), 404

    table.pop(material_name)
    _save_material_table(producent, table)

    if producent == "Forma system":
        groups = _load_forma_groups()
        if material_name in groups:
            groups.pop(material_name)
            _save_forma_groups(groups)

    return jsonify({"status": "ok", "message": "Materiał usunięty"})


@app.route('/api/obrobki/details', methods=['GET'])
def api_obrobki_details():
    producent = request.args.get('producent', '').strip()
    if producent not in OBROBKI_SCHEMAS:
        return jsonify({"error": "Nieznany producent"}), 400

    table = _load_obrobki_table(producent)
    items = [_serialize_obrobka_item(name, raw_value, producent) for name, raw_value in table.items()]
    items.sort(key=lambda x: x["name"].lower())

    return jsonify({
        "producent": producent,
        "items": items,
        "unitOptions": OBROBKI_UNIT_OPTIONS,
        "typeOptions": OBROBKI_TYPE_OPTIONS,
        "groupOptions": [
            {"value": "1", "label": "Konglomeraty"},
            {"value": "2", "label": "Dekton"},
        ],
        "supportsGroup": producent == "Forma system",
    })


@app.route('/api/obrobki', methods=['POST'])
def api_obrobki_create():
    payload = request.get_json(silent=True) or {}
    producent = (payload.get('producent') or '').strip()
    name = (payload.get('name') or '').strip()
    unit = payload.get('unit')
    price = payload.get('price')
    calc_type = payload.get('type')
    group = _normalize_forma_obrobka_group(payload.get('group', FORMA_OBROBKI_GROUP_DEFAULT))

    if producent not in OBROBKI_SCHEMAS:
        return jsonify({"error": "Nieznany producent"}), 400
    if not name:
        return jsonify({"error": "Nazwa obróbki jest wymagana"}), 400

    table = _load_obrobki_table(producent)
    if name in table:
        return jsonify({"error": "Obróbka już istnieje"}), 409

    table[name] = _build_raw_obrobka_value(unit, price, calc_type)
    _save_obrobki_table(producent, table)

    if producent == "Forma system":
        groups = _load_forma_obrobki_groups()
        groups[name] = group
        _save_forma_obrobki_groups(groups)

    return jsonify({"status": "ok", "message": "Obróbka dodana"}), 201


@app.route('/api/obrobki/<path:obrobka_name>', methods=['PUT'])
def api_obrobki_update(obrobka_name):
    payload = request.get_json(silent=True) or {}
    producent = (payload.get('producent') or request.args.get('producent') or '').strip()
    new_name = (payload.get('name') or obrobka_name or '').strip()
    unit = payload.get('unit')
    price = payload.get('price')
    calc_type = payload.get('type')
    group = _normalize_forma_obrobka_group(payload.get('group', FORMA_OBROBKI_GROUP_DEFAULT))

    if producent not in OBROBKI_SCHEMAS:
        return jsonify({"error": "Nieznany producent"}), 400

    table = _load_obrobki_table(producent)
    if obrobka_name not in table:
        return jsonify({"error": "Nie znaleziono obróbki"}), 404
    if not new_name:
        return jsonify({"error": "Nazwa obróbki jest wymagana"}), 400
    if new_name != obrobka_name and new_name in table:
        return jsonify({"error": "Obróbka o nowej nazwie już istnieje"}), 409

    raw_value = _build_raw_obrobka_value(unit, price, calc_type)
    if new_name != obrobka_name:
        table.pop(obrobka_name)
    table[new_name] = raw_value
    _save_obrobki_table(producent, table)

    if producent == "Forma system":
        groups = _load_forma_obrobki_groups()
        if obrobka_name in groups:
            groups.pop(obrobka_name)
        groups[new_name] = group
        _save_forma_obrobki_groups(groups)

    return jsonify({"status": "ok", "message": "Obróbka zaktualizowana"})


@app.route('/api/obrobki/<path:obrobka_name>', methods=['DELETE'])
def api_obrobki_delete(obrobka_name):
    producent = (request.args.get('producent') or '').strip()
    if producent not in OBROBKI_SCHEMAS:
        return jsonify({"error": "Nieznany producent"}), 400

    table = _load_obrobki_table(producent)
    if obrobka_name not in table:
        return jsonify({"error": "Nie znaleziono obróbki"}), 404

    table.pop(obrobka_name)
    _save_obrobki_table(producent, table)

    if producent == "Forma system":
        groups = _load_forma_obrobki_groups()
        if obrobka_name in groups:
            groups.pop(obrobka_name)
            _save_forma_obrobki_groups(groups)

    return jsonify({"status": "ok", "message": "Obróbka usunięta"})


@app.route('/admin')
@login_required
def admin_index():
    files = get_editable_files()
    # show last modified times
    file_infos = []
    for f in files:
        path = os.path.join(app.root_path, f)
        try:
            mtime = os.path.getmtime(path)
        except OSError:
            mtime = None
        file_infos.append({'path': f, 'mtime': mtime})
    return render_template('admin.html', files=file_infos)


@app.route('/admin/materials')
@login_required
def admin_materials():
    producenci = list(MATERIAL_SCHEMAS.keys())
    return render_template('admin_materials.html', producenci=producenci)


@app.route('/admin/obrobki')
@login_required
def admin_obrobki():
    producenci = list(OBROBKI_SCHEMAS.keys())
    return render_template('admin_obrobki.html', producenci=producenci)


@app.route('/admin/edit', methods=['GET'])
@login_required
def admin_edit():
    file = request.args.get('file')
    if not file:
        flash('Nie wybrano pliku do edycji.')
        return redirect(url_for('admin_index'))
    editable = get_editable_files()
    if file not in editable:
        flash('Wybrany plik nie jest dozwolony.')
        return redirect(url_for('admin_index'))
    path = os.path.join(app.root_path, file)
    try:
        with open(path, encoding='utf-8') as f:
            content = f.read()
        parsed = json.loads(content)
        pretty = json.dumps(parsed, ensure_ascii=False, indent=4)
    except Exception:
        # fallback na surowy content w razie błędów
        pretty = content
    return render_template('edit_file.html', file=file, content=pretty)


@app.route('/admin/save', methods=['POST'])
@login_required
def admin_save():
    file = request.form.get('file')
    content = request.form.get('content')
    editable = get_editable_files()
    if file not in editable:
        flash('Plik niedozwolony.')
        return redirect(url_for('admin_index'))
    path = os.path.join(app.root_path, file)
    # validate JSON
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as e:
        flash(f'Błąd JSON: {e}')
        return redirect(url_for('admin_edit', file=file))
    import shutil
    try:
        backup = path + '.bak'
        shutil.copy2(path, backup)
    except Exception as e:
        logging.warning(f'Nie udało się utworzyć backupu: {e}')
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(parsed, f, ensure_ascii=False, indent=4)
        flash('Plik zapisany, backup utworzony.')
    except Exception as e:
        flash(f'Błąd przy zapisie: {e}')
    return redirect(url_for('admin_index'))


if __name__ == "__main__":
    debug_flag = os.environ.get("FLASK_DEBUG", "0").lower() in ("1", "true", "yes")
    app.run(debug=debug_flag)

