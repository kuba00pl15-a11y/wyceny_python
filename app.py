import math

class Producent:
    def cena(self, d, s, g, typ, material=""):
        return 1.0

    def mb(self, d):
        return d

    def m2(self, d, s):
        return d * s


class Stolarz(Producent):
    def __init__(self):
        super().__init__()

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

        return tabelka[wiersz][kolumna] * d

    def cena_obrobka(self, nazwa_obrobki, ilosc, cena_produktu, mb):
        tabelka = {
            "Otwor": 100 * ilosc,
            "Lakier": 0.3 * cena_produktu,
            "Ksztalt kola": 450 * ilosc,
            "Frez pod okno": 10 * mb,
            "Nieregularne ksztalty": 0.3 * cena_produktu,
            "Podklejka": 150 * mb,
            "Frez na led": 15 * mb,
            "Bateria": 60 * ilosc
        }

        return tabelka.get(nazwa_obrobki, 0)

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
        return self.producent.cena(self.dlugosc, self.szerokosc, self.grubosc, self.typ, self.material) * self.ilosc


class Zamowienie:
    def __init__(self):
        self.lista_produktow = []

    def dodaj_produkt(self, produkt):
        self.lista_produktow.append(produkt)

    def wypisz(self):
        for produkt in self.lista_produktow:
            print(f"{produkt.typ} {produkt.material} {produkt.cena():.2f}")


class Klient:
    def __init__(self, imie="", adres="", nr_tel=""):
        self.imie = imie
        self.adres = adres
        self.nr_tel = nr_tel
        self.lista_zamowien = []

    def wczytaj_klienta(self):
        self.imie = input("Podaj imię i nazwisko klienta: ")
        self.adres = input("Podaj adres klienta (miejscowość, ulica, kod pocztowy, numer domu/mieszkania/klatki): ")
        self.nr_tel = input("Podaj numer telefonu klienta: ")

    def wypisz_dane(self):
        print(self.imie)
        print(self.adres)
        print(self.nr_tel)

    def dodaj_zamowienie(self, zamowienie):
        self.lista_zamowien.append(zamowienie)

    def wypisz_zamowienia(self):
        for i, zamowienie in enumerate(self.lista_zamowien):
            print(f"Zamowienie nr {i}")
            zamowienie.wypisz()
            print()

nowy_klient = Klient()
nowy_klient.wczytaj_klienta()
nowy_klient.wypisz_dane()

a = Zamowienie()
s = Stolarz()
p = Produkt(23.0, 12.0, 3.0, 3, "blat", "", s)
a.dodaj_produkt(p)
nowy_klient.dodaj_zamowienie(a)

nowy_klient.wypisz_zamowienia()