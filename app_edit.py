from flask import Flask, render_template, request, redirect, url_for, make_response
import math
import json

# from weasyprint import HTML 

# Definiowanie klas dla producentów
class Producent:
    def cena(self, d, s, g, typ, material=""):
        return 1.0

    def mb(self, d):
        return d / 100

    def m2(self, d, s):
        return d / 100 * s / 100


class Stolarz(Producent):
    nazwa="Stolarz"
    def cena(self, d, s, g, typ, material=""):
        tabelka = [
            [200, 250, 360, 420], [280, 400, 480, 550],
            [380, 480, 540, 700], [480, 550, 680, 730],
            [550, 670, 770, 860], [710, 770, 860, 970],
            [830, 950, 990, 1070], [900, 1030, 1160, 1230],
            [990, 1150, 1240, 1430]
        ]
        kolumna = int(g - 3)
        wiersz = int(math.ceil(s / 10) - 2)
        return tabelka[wiersz][kolumna] * self.mb(d)

    def cena_obrobka(nazwa_obrobki, ilosc, cena_produktu, mb):
        tabelka = {
            "Otwor": 100 * ilosc,
            "Lakier": 0.3 * cena_produktu
        }

        return tabelka.get(nazwa_obrobki, 0) 

class Oretyparapety(Producent):
    nazwa="O rety parapety"

    def cena(self, d, s, g, typ, material=""):
        try:
            with open('data/tabelka_oretyparapety.json', 'r') as file:
                tabelka_oretyparapety = json.load(file)
        except FileNotFoundError:
            raise FileNotFoundError("Plik 'tabelka.json' nie istnieje")

        kolumna = int(g - 2)
        if material in tabelka_oretyparapety and 0 <= kolumna < len(tabelka_oretyparapety[material]):
            return tabelka_oretyparapety[material][kolumna] * self.m2(d, s)
          


    def cena_obrobka(nazwa_obrobki, ilosc, cena_produktu, mb):
        tabelka = {
        "Ciecie po skosie": 50 * ilosc,
        "Otwor nablatowy": 500 * ilosc
    }

        return tabelka.get(nazwa_obrobki, 0)


class Olgran(Producent):
    nazwa="Olgran"

    def cena(self, d, s, g, typ, material=""):
        try:
            with open('data/tabelka_olgran.json', 'r') as file:
                tabelka_olgran = json.load(file)
        except FileNotFoundError:
            raise FileNotFoundError("Plik 'tabelka.json' nie istnieje")

        kolumna = int(g - 2)
        if typ == "blat":
            kolumna += 2
        if material in tabelka_olgran and 0 <= kolumna < len(tabelka_olgran[material]):
            return tabelka_olgran[material][kolumna] * self.m2(d, s)
        else:
            raise ValueError("Invalid material or thickness")

        
    def cena_obrobka(nazwa_obrobki, ilosc, cena_produktu, mb, m2):
        tabelka = {
            # otwory
            "Bateria": 150 * ilosc,
            "Power-port": 250 * ilosc
        }
        
        return tabelka.get(nazwa_obrobki, 0)


class Imperial(Producent):
    nazwa="Imperial"

    def cena(self, d, s, g, typ, material=""):
        try:
            with open('data/tabelka_imperial.json', 'r') as file:
                tabelka_imperial = json.load(file)
        except FileNotFoundError:
            raise FileNotFoundError("Plik 'tabelka_imperial.json' nie istnieje")

        kolumna = int(g - 2)
        if typ == "blat":
            kolumna += 2
        if material in tabelka_imperial and 0 <= kolumna < len(tabelka_imperial[material]):
            return tabelka_imperial[material][kolumna] * self.m2(d, s)
        else:
            raise ValueError("Nieprawidłowy materiał albo grubość")                                         #zmien na jakis ladnijszty error


    def cena_obrobka(nazwa_obrobki, ilosc, cena_produktu, mb, m2):
        tabelka = {
            # otwory
            "Bateria": 150 * ilosc,
            "Fazowanie plytek": 30 * mb
        }
        
        return tabelka.get(nazwa_obrobki, 0)

class Formasystem(Producent):
    nazwa="Forma system"
    
    def cena(self, d, s, g, typ, material=""):
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
            przedzialy = [151, 301, 501, 636, 701, 851, 1001]
        
        for wartosc in przedzialy:
            if s >= wartosc:
                kolumna += 1

        return tabelka_forma[material][czesc][kolumna] * self.mb(d)
      
    def cena_obrobka(self, nazwa_obrobki, ilosc, mb):
        tabelka_o = {
            "Ciecie po skosie": 50 * ilosc,
            "Otwor nablatowy": 500 * ilosc,
            "Otwor bateria": 100 * ilosc,
            "Otwor syfon": 200 * ilosc,
            "Wyciecie naroznika": 40 * ilosc,
            "Wyciecie naroznika (poler)": 80 * ilosc,
            "Podpoler": 60 * mb
        }
        
        return tabelka_o.get(nazwa_obrobki, 0)

class Produkt:
    def __init__(self, dlugosc, szerokosc, grubosc, ilosc, typ, material, producent):
        self.dlugosc = dlugosc
        self.szerokosc = szerokosc
        self.grubosc = grubosc
        self.ilosc = ilosc
        self.typ = typ
        self.material = material
        self.producent = producent

    def cena(self):
        return round(self.producent.cena(self.dlugosc, self.szerokosc, self.grubosc, self.typ, self.material) * self.ilosc, 2)

usluga_pomiar=False
usluga_transport=False
usluga_montaz=False

class Zamowienie:
    def __init__(self):
        self.lista_produktow = []

    def dodaj_produkt(self, produkt):
        self.lista_produktow.append(produkt)

    def laczna_cena(self):
        return sum([produkt.cena() for produkt in self.lista_produktow])


class Klient:
    def __init__(self):
        self.imie = ""
        self.adres = ""
        self.nr_tel = ""
        self.lista_zamowien = []

    def dodaj_zamowienie(self, zamowienie):
        self.lista_zamowien.append(zamowienie)

    def wypisz_dane(self):
        return f"Imię: {self.imie}, Adres: {self.adres}, Telefon: {self.nr_tel}"

    def aktualizuj_dane(self, imie, adres, nr_tel):
        self.imie = imie
        self.adres = adres
        self.nr_tel = nr_tel

klient = Klient()
# dodaj klienta
app = Flask(__name__)
zamowienie = Zamowienie()
producenty = {
    "Stolarz": Stolarz,
    "O rety parapety": Oretyparapety,
    "Olgran": Olgran,
    "Imperial": Imperial,
    "Forma system": Formasystem
}


@app.route("/uslugi", methods=["POST"])
def uslugi():
    global usluga_transport
    global usluga_pomiar
    global usluga_montaz
    if "transport" in request.form.keys():
        usluga_transport=True
    print(request.form)

    if "pomiar" in request.form.keys():
        usluga_pomiar=True
    print(request.form)

    if "montaz" in request.form.keys():
        usluga_montaz=True
    print(request.form)
    
    return redirect(url_for("strona_glowna"))


dane_klienta = {}

@app.route('/dane_klienta', methods=['GET', 'POST'])
def dane_klienta_view():
    global dane_klienta
    if request.method == 'POST':
        dane_klienta['imie'] = request.form['imie']
        dane_klienta['adres'] = request.form['adres']
        dane_klienta['nr_tel'] = request.form['nr_tel']
        return render_template('lista_produktow.html', dane_klienta=dane_klienta)
    return render_template('dane_klienta.html')

@app.route('/lista_produktow')
def lista_produktow_view():
    global dane_klienta
    return render_template('lista_produktow.html', dane_klienta=dane_klienta)

@app.route("/faktura")
def faktura():
    produkty = zamowienie.lista_produktow
    laczna_cena = zamowienie.laczna_cena()
    return render_template("faktura.html", produkty=produkty, laczna_cena=laczna_cena)

# Strona główna z formularzem
@app.route("/", methods=["POST", "GET"])
def strona_glowna():
    global usluga_transport, usluga_pomiar, usluga_montaz
    if request.method == "POST":
        print ("Proboje dodac dane klienta", request.form)
    return render_template("strona_glowna.html", zamowienie=zamowienie, klient=klient, laczna_cena_z_uslugami=0.0, usluga_pomiar=usluga_pomiar, usluga_montaz=usluga_montaz, usluga_transport=usluga_transport)


@app.route("/aktualizuj_klienta", methods=["POST"])
def aktualizuj_klienta():
    klient.aktualizuj_dane(request.form["imie"], request.form["adres"], request.form["nr_tel"])
    return redirect(url_for("strona_glowna"))


@app.route("/dodaj_produkt", methods=["POST", "GET"])
def dodaj_produkt():
    if request.method == "POST":
        print("Otrzymane dane formularza:", request.form)

        # Grupowanie danych na podstawie identyfikatorów
        produkty = {}
        for klucz, wartosc in request.form.items():
            if "_" in klucz:
                pole, id_ = klucz.rsplit("_", 1)
                if id_ not in produkty:
                    produkty[id_] = {}
                produkty[id_][pole] = wartosc

        # Konwersja i budowanie paczek produktów
        paczki_produktow = []
        for id_, dane in produkty.items():
            try:
                produkt_data = {
                    "producent": dane.get("producent"),
                    "material": dane.get("material"),
                    "typ": dane.get("typ"),
                    "dlugosc": float(dane.get("dlugosc", 0)),
                    "szerokosc": float(dane.get("szerokosc", 0)),
                    "grubosc": float(dane.get("grubosc", 0)),
                    "ilosc": int(dane.get("ilosc", 0)),
                }
                paczki_produktow.append(produkt_data)
            except ValueError as e:
                print(f"Błąd w danych produktu {id_}: {e}")

        # Debug: Wyświetlenie zebranych paczek
        print("Zebrane paczki danych produktów:", paczki_produktow)
        zamowienie.lista_produktow=[]
        # Przetwarzanie produktów
        for produkt_data in paczki_produktow:
            try:
                producent = producenty.get(produkt_data["producent"], Stolarz)()
                produkt = Produkt(
                    dlugosc=produkt_data["dlugosc"],
                    szerokosc=produkt_data["szerokosc"],
                    grubosc=produkt_data["grubosc"],
                    ilosc=produkt_data["ilosc"],
                    typ=produkt_data["typ"],
                    material=produkt_data["material"],
                    producent=producent,
                )
                zamowienie.dodaj_produkt(produkt)
                print(f"Dodano produkt: {produkt.__dict__}")
            except Exception as e:
                print(f"Błąd podczas dodawania produktu: {produkt_data}, {e}")

        return redirect(url_for("strona_glowna"))
    return render_template("dodaj_produkt.html", lista_produktow=zamowienie.lista_produktow)

@app.route("/dodaj_obrobke", methods=["POST", "GET"])
def dodaj_obrobke():
    if request.method == "POST":
        

        return redirect(url_for("strona_glowna"))
    return render_template("dodaj_obrobke.html")

# ^ Post if

# Strona faktury
from PDF import generuj_PDF

@app.route("/pdf")
def pdf():
    generuj_PDF(zamowienie, dane_klienta)    
    return redirect(url_for("strona_glowna"))

if __name__ == "__main__":
    app.run(debug=True)

