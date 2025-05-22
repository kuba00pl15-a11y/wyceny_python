from flask import Flask, render_template, request, redirect, url_for, Response, session, flash
import math
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin, current_user
import json
import os

app = Flask(__name__)

def wczytaj_ceny_obrobek():
    katalog = "data/obrobki"
    obrobki = {}
    for plik in os.listdir(katalog):
        nazwa = plik.replace("obrobki_", "").replace(".json", "").replace("_", " ").strip().lower().replace(" ", "")
        with open(os.path.join(katalog, plik), encoding="utf-8") as f:
            obrobki[nazwa] = json.load(f)
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

        return tabelka_forma[material][czesc][kolumna]

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
            self._cena_bazowa = self.producent.cena(self.dlugosc, self.szerokosc, self.grubosc, self.typ, self.material)
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
            print(obrobka)
            if ":" in obrobka:
                ilosc = int(obrobka.split(":")[1])
                obrobka = obrobka.split(":")[0]
            if hasattr(self.producent, "licz_cene_obrobki"):
                cena_obrobki = self.producent.licz_cene_obrobki(
                    klucz_producenta, obrobka, self.ilosc, cena_bazowa, mb, m2
                )
                try:
                    suma += float(cena_obrobki) * ilosc
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

            if nazwa not in wynik:
                wynik[nazwa] = {"ilosc": 0, "cena_jednostkowa": 0.0}

            cena = self.producent.licz_cene_obrobki(klucz_producenta, nazwa, 1, cena_bazowa, mb, m2)
            wynik[nazwa]["ilosc"] += ilosc
            wynik[nazwa]["cena_jednostkowa"] = round(cena, 2)

        return [(nazwa, dane["ilosc"], dane["cena_jednostkowa"]) for nazwa, dane in wynik.items()]



usluga_pomiar=False
usluga_transport=False
usluga_montaz=False
usluga_pmt=False

class Zamowienie:
    def __init__(self):
        self.lista_produktow = []
        self.wlasne_obrobki = []

    def dodaj_produkt(self, produkt):
        self.lista_produktow.append(produkt)

    def laczna_cena(self):
        return sum([produkt.cena() + produkt.cena_obrobek() for produkt in self.lista_produktow])


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
        return f"Imię: {self.imie}, Adres: {self.adres}, Telefon: {self.nr_tel}, Adres email: {self.adres_email}, Ofetrę przygotowuje: {self.kto_oferta}"

    def aktualizuj_dane(self, imie="", adres="", nr_tel="", adres_email="", kto_oferta="", dni=0, tygodnie=0, miesiace=0):
        self.imie = imie if imie else ""
        self.adres = adres if adres else ""
        self.nr_tel = nr_tel if nr_tel else ""
        self.adres_email = adres_email if adres_email else ""
        self.kto_oferta = kto_oferta if kto_oferta else ""
        self.dni = dni
        self.tygodnie = tygodnie
        self.miesiace = miesiace


klient = Klient()
# dodaj klienta

app.secret_key = "hfe9hf9wh"
zamowienie = Zamowienie()
producenty = {
    "Stolarz": Stolarz,
    "O rety parapety": Oretyparapety,
    "Olgran": Olgran,
    "Imperial": Imperial,
    "Forma system": Formasystem
}

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

users = {
    'admin': {'password': 'p'}
}

# Klasa użytkownika
class User(UserMixin):
    def __init__(self, username):
        self.id = username

@login_manager.user_loader
def load_user(user_id):
    if user_id in users:
        return User(user_id)
    return None

cena_transportt = ""
cena_montazuu = ""
cena_pomiaruu = ""
cena_ppmmtt = ""



@app.before_request
def require_login():
    public_endpoints = ['login', 'static']

    if request.endpoint not in public_endpoints and not current_user.is_authenticated:
        return redirect(url_for('login'))

@app.route("/uslugi", methods=["POST"])
def uslugi():
    global usluga_transport, usluga_pomiar, usluga_montaz, usluga_pmt
    global cena_transportt, cena_pomiaruu, cena_montazuu, cena_ppmmtt

    usluga_transport = "transport" in request.form
    usluga_pomiar = "pomiar" in request.form
    usluga_montaz = "montaz" in request.form
    usluga_pmt = "pomiar_transport_montaz" in request.form

    cena_pomiaruu = request.form.get("cena_pomiaru", "")
    cena_transportt = request.form.get("cena_transportu", "")
    cena_montazuu = request.form.get("cena_montazu", "")
    cena_ppmmtt = request.form.get("cena_ppmmtt", "")

    return redirect(url_for("strona_glowna"))


@app.route("/", methods=["POST", "GET"])
def strona_glowna():
    custom_obrobki = zamowienie.wlasne_obrobki if hasattr(zamowienie, "wlasne_obrobki") else []

    return render_template("strona_glowna.html.j2",
        zamowienie=zamowienie,
        klient=klient,
        laczna_cena_z_uslugami=0.0,
        usluga_pomiar=usluga_pomiar,
        usluga_montaz=usluga_montaz,
        usluga_transport=usluga_transport,
        usluga_pmt=usluga_pmt,
        cena_pomiaruu=cena_pomiaruu,
        cena_montazuu=cena_montazuu,
        cena_transportt=cena_transportt,
        cena_ppmmtt=cena_ppmmtt,
        custom_obrobki=custom_obrobki)


@app.route("/aktualizuj_klienta", methods=["POST"])
def aktualizuj_klienta():
    imie = request.form.get("imie")
    adres = request.form.get("adres")
    nr_tel = request.form.get("nr_tel")
    adres_email = request.form.get("adres_email")
    kto_oferta = request.form.get("kto_oferta")
    dni = int(request.form.get("dni", 0))
    tygodnie = int(request.form.get("tygodnie", 2))
    miesiace = int(request.form.get("miesiace", 0))

    klient.aktualizuj_dane(imie, adres, nr_tel, adres_email, kto_oferta, dni, tygodnie, miesiace)
    return redirect(url_for("strona_glowna"))



@app.route('/dodaj_produkt', methods=['GET', 'POST'])
def dodaj_produkt():
    global zamowienie

    if 'zamowienie' not in globals():
        zamowienie = Zamowienie()
    custom_obrobki = zamowienie.wlasne_obrobki if hasattr(zamowienie, "wlasne_obrobki") else []

    if not hasattr(zamowienie, 'lista_produktow'):
        zamowienie.lista_produktow = []

    if request.method == "POST":
        print("Otrzymane dane formularza:", request.form)

        produkty = {}
        for klucz, wartosc in request.form.items():
            if "_" in klucz:
                pole, id_ = klucz.rsplit("_", 1)
                if id_ not in produkty:
                    produkty[id_] = {}
                produkty[id_][pole] = wartosc


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
                    "obrobki": [o.strip() for o in request.form.get(f"obrobki_{id_}", "").split(",") if o.strip()],
                    "obrobki_z_iloscia": {
                        o.split(":")[0].strip(): int(o.split(":")[1]) if ":" in o else 1
                        for o in request.form.get(f"obrobki_{id_}", "").split(",") if o.strip()
                    }
                }
                paczki_produktow.append(produkt_data)
            except ValueError as e:
                print(f"Błąd w danych produktu {id_}: {e}")

        zamowienie.lista_produktow = []

        for produkt_data in paczki_produktow:
            try:
                producent = producenty.get(produkt_data["producent"], Stolarz)()
                obrobki_rozwiniete = []
                for nazwa, ilosc in produkt_data["obrobki_z_iloscia"].items():
                    obrobki_rozwiniete.append("{}:{}".format(nazwa, ilosc))

                for _ in range(produkt_data["ilosc"]):
                    produkt = Produkt(
                        producent=producent,
                        material=produkt_data["material"],
                        typ=produkt_data["typ"],
                        rabat=produkt_data["rabat"],
                        dlugosc=produkt_data["dlugosc"],
                        szerokosc=produkt_data["szerokosc"],
                        grubosc=produkt_data["grubosc"],
                        ilosc=1,
                        obrobki=obrobki_rozwiniete
                    )
                    zamowienie.dodaj_produkt(produkt)

                print(f"Dodano produkt: {produkt.__dict__}")
            except Exception as e:
                print(f"Błąd podczas dodawania produktu: {produkt_data}, {e}")


        for produkt in zamowienie.lista_produktow:
            try:
                grubosc_float = float(produkt.grubosc)
                if grubosc_float.is_integer():
                    produkt.grubosc = int(grubosc_float)
                else:
                    produkt.grubosc = grubosc_float
            except (ValueError, TypeError):
                pass

        nowe_obrobki = []
        for key, value in request.form.items():
            if key.startswith("custom_obrobka_nazwa_"):
                index = key.split("_")[-1]
                nazwa = value.strip()
                try:
                    cena = float(request.form.get(f"custom_obrobka_cena_{index}", "0").replace(",", "."))
                except ValueError:
                    cena = 0.0
                if nazwa:
                    nowe_obrobki.append({"nazwa": nazwa, "cena": cena})

        zamowienie.wlasne_obrobki = nowe_obrobki
        return redirect(url_for("strona_glowna"))

    obrobki_data = {}
    sciezka = r"data\obrobki"
    if os.path.exists(sciezka):
        for plik in os.listdir(sciezka):
            print(plik)
            if plik.endswith('.json'):
                producent = plik.replace('.json', '').replace('obrobki_', '')
                with open(os.path.join(sciezka, plik), 'r', encoding='utf-8') as f:
                    try:
                        obrobki_data[producent] = json.load(f)
                    except json.JSONDecodeError:
                        print(f"Błąd wczytywania JSON z pliku {plik}")

    return render_template(
    "dodaj_produkt.html",
    lista_produktow=zamowienie.lista_produktow,
    obrobki_data=obrobki_data,
    custom_obrobki=zamowienie.wlasne_obrobki
)



from PDF_drewkam import generuj_PDF
from flask import request, Response

@app.route("/pdf", methods=["GET"])
def pdf():

    pdf_buffer = generuj_PDF(
        zamowienie,
        klient,
        usluga_pomiar=usluga_pomiar,
        usluga_transport=usluga_transport,
        usluga_montaz=usluga_montaz,
        usluga_pmt=usluga_pmt,
        cena_pomiaruu=cena_pomiaruu,
        cena_montazuu=cena_montazuu,
        cena_ppmmtt=cena_ppmmtt,
        cena_transportt=cena_transportt,
        custom_obrobki=zamowienie.wlasne_obrobki
    )

    return Response(pdf_buffer, mimetype="application/pdf",
                    headers={"Content-Disposition": "inline; filename=wycena_pelna.pdf"})

from PDF_klient import generuj_PDF_klient
from flask import request, Response

@app.route("/pdf_k", methods=["GET"])
def pdf_klient():

    pdf_buffer = generuj_PDF_klient(
        zamowienie,
        klient,
        usluga_pomiar=usluga_pomiar,
        usluga_transport=usluga_transport,
        usluga_montaz=usluga_montaz,
        usluga_pmt=usluga_pmt,
        cena_pomiaruu=cena_pomiaruu,
        cena_montazuu=cena_montazuu,
        cena_ppmmtt=cena_ppmmtt,
        cena_transportt=cena_transportt,
        custom_obrobki=zamowienie.wlasne_obrobki
    )

    return Response(pdf_buffer, mimetype="application/pdf",
                    headers={"Content-Disposition": "inline; filename=wycena_klient.pdf"})

@app.route('/reset_strony', methods=['POST'])
def reset_strony():
    # Wyczyszczenie danych jeśli trzeba
    if os.path.exists('dane.csv'):
        os.remove('dane.csv')

    # Restart serwera - TYLKO do testów lokalnych!
    os._exit(0)  # kończy proces — w trybie debug Flask się zrestartuje automatycznie

    return redirect(url_for('strona_glowna'))  # Nie zostanie wykonane

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = users.get(username)

        if user and user['password'] == password:
            login_user(User(username))
            flash('Zalogowano pomyślnie!')
            return redirect(url_for('strona_glowna'))
        else:
            flash('Nieprawidłowy login lub hasło.')

    return render_template('login.html')


@app.route('/logout')
def logout():
    logout_user()
    flash('Wylogowano.')
    return redirect(url_for('login'))


if __name__ == "__main__":
    app.run(debug=True)

