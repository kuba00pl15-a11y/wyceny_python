from flask import Flask, render_template, request, redirect, url_for, make_response, Response
import math
import json
import os

def wczytaj_ceny_obrobek():
    katalog = "data/obrobki"
    obrobki = {}
    for plik in os.listdir(katalog):
        nazwa = plik.replace("obrobki_", "").replace(".json", "").replace("_", " ").title()
        with open(os.path.join(katalog, plik), encoding="utf-8") as f:
            obrobki[nazwa] = json.load(f)
    return obrobki

obrobki_cennik = wczytaj_ceny_obrobek()


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
            raise ValueError("Nieprawidłowy materiał albo grubość")                                                                 #zmien na jakis ladnijszty error

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


class Produkt:
    def __init__(self, dlugosc, szerokosc, grubosc, ilosc, typ, material, producent, obrobki=None):
        self.dlugosc = dlugosc
        self.szerokosc = szerokosc
        self.grubosc = grubosc
        self.ilosc = ilosc
        self.typ = typ
        self.material = material
        self.producent = producent
        self.obrobki = obrobki or []

    def cena(self):
        return round(self.producent.cena(self.dlugosc, self.szerokosc, self.grubosc, self.typ, self.material) * self.ilosc, 2)
    
    def cena_obrobek(self, licz_cene_obrobki):
        suma = 0
        mb = self.producent.mb(self.dlugosc)
        m2 = self.producent.m2(self.dlugosc, self.szerokosc)
        cena_bazowa = self.producent.cena(self.dlugosc, self.szerokosc, self.grubosc, self.typ, self.material)

        for obrobka in self.obrobki:
            suma += licz_cene_obrobki(self.producent.nazwa, obrobka, self.ilosc, cena_bazowa, mb, m2)
        return round(suma, 2)



usluga_pomiar=False
usluga_transport=False
usluga_montaz=False
cena_uslugi = None

class Zamowienie:
    def __init__(self):
        self.lista_produktow = []

    def dodaj_produkt(self, produkt):
        self.lista_produktow.append(produkt)

    def laczna_cena(self):
        return sum([produkt.cena() + produkt.cena_obrobek() for produkt in self.lista_produktow])



class Klient:
    def __init__(self):
        self.imie = ""
        self.adres = ""
        self.nr_tel = ""
        self.lista_zamowien = []
        self.dni = 0
        self.tygodnie = 0
        self.miesiace = 0

    def dodaj_zamowienie(self, zamowienie):
        self.lista_zamowien.append(zamowienie)

    def wypisz_dane(self):
        return f"Imię: {self.imie}, Adres: {self.adres}, Telefon: {self.nr_tel}"

    def aktualizuj_dane(self, imie, adres, nr_tel, dni, tygodnie, miesiace):
        self.imie = imie
        self.adres = adres
        self.nr_tel = nr_tel
        self.dni = dni
        self.tygodnie = tygodnie
        self.miesiace = miesiace

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

cena_uslugi = ""

@app.route("/uslugi", methods=["POST"])
def uslugi():
    global usluga_transport
    global usluga_pomiar
    global usluga_montaz
    global cena_uslugi
    if "transport" in request.form.keys():
        usluga_transport=True
    else:
        usluga_transport=False

    if "pomiar" in request.form.keys():
        usluga_pomiar=True

    if "montaz" in request.form.keys():
        usluga_montaz=True
    
    if "cena_u" in request.form.keys():
        cena_uslugi=request.form["cena_u"]
    return redirect(url_for("strona_glowna"))

# Strona główna z formularzem
@app.route("/", methods=["POST", "GET"])
def strona_glowna():
    global usluga_transport, usluga_pomiar, usluga_montaz
    if request.method == "POST":
        print ("Proboje dodac dane klienta", request.form)
    return render_template("strona_glowna.html.j2", zamowienie=zamowienie, klient=klient, laczna_cena_z_uslugami=0.0, usluga_pomiar=usluga_pomiar, usluga_montaz=usluga_montaz, usluga_transport=usluga_transport, cena_uslugi=cena_uslugi)


@app.route("/aktualizuj_klienta", methods=["POST"])
def aktualizuj_klienta():
    imie = request.form["imie"]
    adres = request.form["adres"]
    nr_tel = request.form["nr_tel"]
    dni = int(request.form.get("dni", 0))
    tygodnie = int(request.form.get("tygodnie", 0))
    miesiace = int(request.form.get("miesiace", 0))

    klient.aktualizuj_dane(imie, adres, nr_tel, dni, tygodnie, miesiace)
    return redirect(url_for("strona_glowna"))


@app.route('/dodaj_produkt', methods=['GET', 'POST'])
def dodaj_produkt():
    
# przejrzyj chatGpt i zprawdz 
    # Upewnij się, że obiekt zamowienie istnieje
    global zamowienie
    zamowienie.lista_produktow = zamowienie.lista_produktow if hasattr(zamowienie, 'lista_produktow') else []

    if 'zamowienie' not in globals():
        zamowienie = Zamowienie()

    # Zabezpieczenie listy produktów
    if not hasattr(zamowienie, 'lista_produktow'):
        zamowienie.lista_produktow = []

    # Wczytaj dane obróbek z plików JSON
    obrobki_data = {}
    sciezka = os.path.join('data', 'obrobki')
    if os.path.exists(sciezka):
        for plik in os.listdir(sciezka):
            if plik.endswith('.json'):
                producent = plik.replace('.json', '')
                producent = producent.replace('obrobki_', '')
                print(producent)
                with open(os.path.join(sciezka, plik), 'r', encoding='utf-8') as f:
                    try:
                        obrobki_data[producent] = json.load(f)
                    except json.JSONDecodeError:
                        print(f"Błąd wczytywania JSON z pliku {plik}")
    print(obrobki_data)

    # Renderuj szablon i przekaż dane
    return render_template(
        "dodaj_produkt.html.j2",
        lista_produktow=zamowienie.lista_produktow,
        obrobki_data=obrobki_data
    )



# Strona faktury
from PDF import generuj_PDF

@app.route("/pdf")
def pdf():
    pdf_buffer = generuj_PDF(
        zamowienie, 
        klient,
        usluga_pomiar=usluga_pomiar,
        usluga_transport=usluga_transport,
        usluga_montaz=usluga_montaz,
        cena_uslugi=cena_uslugi
    )    
    return Response(pdf_buffer, mimetype="application/pdf",
                headers={"Content-Disposition": "inline; filename=wycena.pdf"})

if __name__ == "__main__":
    app.run(debug=True)

