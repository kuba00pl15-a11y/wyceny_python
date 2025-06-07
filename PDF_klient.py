from flask import Flask, Response
import io
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Image, Spacer, Paragraph
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from datetime import datetime
from dateutil.relativedelta import relativedelta
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import Paragraph


pdfmetrics.registerFont(TTFont("DejaVu", "DejaVuSans.ttf"))

tiny_style = ParagraphStyle(
    name='Tiny',
    fontName='DejaVu',
    fontSize=5.0,
    leading=6,
    alignment=TA_JUSTIFY,
    allowOrphans=0,
    allowWidows=0,
    spaceAfter=6,
    wordWrap='CJK',
)

right_normal_style = ParagraphStyle(
    name='RightNormal',
    fontName='DejaVu',
    alignment=TA_RIGHT
)

right_align_style = ParagraphStyle(
    name='RightAlign',
    fontName='DejaVu',
    fontSize=15,
    alignment=TA_RIGHT
)

laczna_style = ParagraphStyle(
    name='Laczna',
    fontName='DejaVu',
    fontSize=11,
    alignment=TA_LEFT
)

# Ścieżka do zdjęcia
image_path = r"static/images/header.jpg"

def generuj_PDF_klient(zamowienie, klient, usluga_pmt, usluga_pomiar, usluga_transport, usluga_montaz, cena_ppmmtt, cena_pomiaruu, cena_transportt, cena_montazuu, custom_obrobki=None):
    # Tworzenie dokumentu PDF
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0, leftMargin=10, rightMargin=10, bottomMargin=40)

    # Pobranie szerokości strony
    page_width, _ = A4

    # Wczytanie obrazka o pełnej szerokości strony
    img = Image(image_path, width=page_width, height=page_width * 0.06)


    # Style tekstu
    styles = getSampleStyleSheet()
    styles['Normal'].fontName = 'DejaVu'
    styles['Normal'].fontSize = 9

    elements = []

    teraz = datetime.now()
    data_wyceny = teraz.strftime("%d.%m.%Y")
    data_waznosci = teraz + relativedelta(
        days=klient.dni, weeks=klient.tygodnie, months=klient.miesiace
    )
    data_waznosci_str = data_waznosci.strftime("%d.%m.%Y")

    s = f""
    # Dane klienta (lewa strona)
    klient_html = f"""
        {klient.imie + '<br/>' if klient.imie else ''}
        {klient.adres + '<br/>' if klient.adres else ''}
        {'tel. ' + klient.nr_tel + '<br/>' if klient.nr_tel else ''}
        {klient.adres_email + '<br/>' if klient.adres_email else ''}
        Data wyceny: {data_wyceny}<br/>
        {'Data ważności oferty: ' + data_waznosci_str + '<br/>'}
    """

    # Dane firmy (prawa strona)
    firma_html = f"""
        Galeria Drewna i Kamienia DREWKAM<br/>
        tel. 71 73 71 737<br/>
        www.drewkam.com.pl<br/><br/>
        {"Ofertę sporządzał:" + '<br/>' if klient.kto_oferta else ''}
        {klient.kto_oferta + '<br/>' if klient.kto_oferta else ''}
    """

    # Tabela z dwiema kolumnami
    dane_tabela = Table(
        [[Paragraph(klient_html, styles['Normal']), Paragraph(firma_html, right_normal_style)]],
        colWidths=[page_width * 0.5, page_width * 0.5 - 20]  # prawa kolumna maksymalna z lekkim marginesem
    )

    dane_tabela.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))

    elements.extend([img, Spacer(1, 20), dane_tabela, Spacer(1, 20)])

    max_rabat = max([getattr(produkt, 'rabat', 0) for produkt in zamowienie.lista_produktow], default=0)

    if max_rabat > 0:
        rabat_paragraph = Paragraph(f"<b>Uwzględniono rabat:</b> {max_rabat:.0f}%", styles['Normal'])
        elements.insert(3, rabat_paragraph)
        elements.insert(4, Spacer(1, 10))


    # Produkty
    data = [
        ["LP.", "Materiał", "Typ","Ilość", "Długość [cm]", "Szerokość [cm]", "Grubość [cm]"]
    ]
    for i, produkt in enumerate(zamowienie.lista_produktow):
        data.append([i + 1, produkt.material, produkt.typ, produkt.ilosc, produkt.dlugosc, produkt.szerokosc, produkt.grubosc])


    laczna_cena_produktow = sum([produkt.cena_po_rabacie() for produkt in zamowienie.lista_produktow])
    laczna_cena_obrobek = sum([produkt.cena_obrobek() for produkt in zamowienie.lista_produktow])
    laczna_cena_obrobek_dodatkowych = sum([obrobka["cena"] for obrobka in custom_obrobki])


    # Tworzenie tabeli produktów
    table = Table(data, hAlign='LEFT')
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 0), (-1, -1), 'DejaVu'),
        ('FONTSIZE', (0, 0), (-1, -1), 9)
    ]))


    # Produkty obróbek
    data_obr = [["LP.", "Obróbka", "Ilość"]]

    for i, produkt in enumerate(zamowienie.lista_produktow, start=1):
        obrobki_zliczone = {}

        for obrobka_raw in produkt.obrobki:
            if ":" in obrobka_raw:
                nazwa, ilosc = obrobka_raw.split(":")
                ilosc = int(ilosc)
            else:
                nazwa, ilosc = obrobka_raw, 1

            obrobki_zliczone[nazwa] = obrobki_zliczone.get(nazwa, 0) + ilosc

        for nazwa, ilosc in obrobki_zliczone.items():
            data_obr.append([i, nazwa, ilosc])

    # Tworzenie tabeli obróbek
    table_obr = Table(data_obr, hAlign='LEFT')
    table_obr.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('TEXT-ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 0), (-1, -1), 'DejaVu'),
        ('FONTSIZE', (0, 0), (-1, -1), 9)
    ]))

    #Dodatkowe obrobki
    data_obrobki_dodatkowe = [["Dodatkowa obróbka"]]
    for obrobka in custom_obrobki:
        data_obrobki_dodatkowe.append([obrobka["nazwa"]])

    obrobki_table = Table(data_obrobki_dodatkowe, hAlign='LEFT')
    obrobki_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 0), (-1, -1), 'DejaVu'),
        ('FONTSIZE', (0, 0), (-1, -1), 9)
    ]))

    # Usługi
    data_uslugi = [
        ["Usługa"]
    ]
    if usluga_pmt:
        data_uslugi.append(["Pomiar, transport i montaż"])
    if usluga_pomiar:
        data_uslugi.append(["Pomiar"])
    if usluga_transport:
        data_uslugi.append(["Transport"])
    if usluga_montaz:
        data_uslugi.append(["Montaż"])

    # Tworzenie tabeli usług
    table_uslugi = Table(data_uslugi, colWidths=[200, 100], hAlign='LEFT')
    table_uslugi.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 0), (-1, -1), 'DejaVu'),
        ('FONTSIZE', (0, 0), (-1, -1), 9)

    ]))

    cena_ppmmtt = float(cena_ppmmtt or 0)
    cena_pomiaruu = float(cena_pomiaruu or 0)
    cena_transportt = float(cena_transportt or 0)
    cena_montazuu = float(cena_montazuu or 0)


    laczna_cena_uslug = cena_pomiaruu + cena_transportt + cena_montazuu + cena_ppmmtt


    techniczne_info_text = """
    Tolerancja wymiarowa:<br/>
    Tolerancja elementów ciętych wynosi ±2mm na stronę; tolerancja pomiarowa wynosi ±3–4mm na stronę;
    tolerancja montażowa wynosi ±5mm na stronę, tolerancja grubości materiału wynosi 2mm (±2mm).<br/><br/>

    Techniczne warunki realizacji zamówienia:<br/>
    - przed wykonaniem pomiaru i montażu meble kuchenne muszą być ustawione na swoich miejscach i wypoziomowane<br/>
    - do pomiaru i montażu wszystkie urządzenia AGD powinny stać na swoich miejscach<br/>
    - w przypadku braku przygotowania warunków do pomiaru i montażu blatów zastrzegamy sobie prawo do naliczenia dodatkowych kosztów
    związanych z dodatkowym pomiarem i montażem. W przypadku zamówienia blatu, gdzie łączenie blatu jest na linii otworu, Zamawiający ma
    obowiązek wykonania podpory części newralgicznych blatu
    z płyty meblowej, aby blat nie uległ uszkodzeniu. W przypadku zamówienia blatu w grubości 1,2 cm konieczne jest wykonanie pełnej podbudowy.<br/><br/>

    Materiały wykonane z kamienia naturalnego należy zaimpregnować. Informacji na temat impregnacji wybranego materiału należy zasięgnąć podczas montażu
    lub u sprzedawcy. Kamień czarny, satynowany przed impregnacją ma odcień jaśniejszy niż na próbce, aby nadać mu ciemniejszy odcień i zabezpieczyć przed
    plamieniem, należy użyć impregnatu Transformer Max firmy Akemi zgodnie z instrukcją znajdującą się na opakowaniu.<br/><br/>

    Warunki przystąpienia do pomiaru blatów:<br/>
    W dniu pomiaru na miejscu inwestycji meble powinny być zamontowane na gotowo, wypoziomowane oraz znajdować się powinny wszelkie sprzęty
    wymagające wycięcia otworów: zlewozmywak, bateria, płyta grzewcza, dozownik, okap, power-porty itp. W przypadku braku w/w sprzętów klient zostanie
    obciążony dodatkowym kosztem pomiaru zgodnie z obowiązującym na dzień pomiaru cennikiem.<br/><br/>

    Warunki rezerwacji materiału/ceny i rabatów:<br/>
    Materiał wraz ceną i rabatem jest zarezerwowany na okres 6 miesięcy liczony od dnia wpłaty zaliczki. W przypadku zmiany wymiarów po pomiarze
    podana cena może ulec zmianie z zachowaniem ustalonych w zamówieniu cen jednostkowych i udzielonych rabatów. W przypadku, gdy realizacja zamówienia
    nie zostanie ukończona w w/w terminie - cena blatu zostanie policzona po cenach obowiązujących na dzień wykonania pomiaru. W przypadku rezygnacji
    z zamówienia blatu po pomiarze, kwota zaliczki zostanie pomniejszona o koszt pomiaru zgodnie z obowiązującym na dzień pomiaru cennikiem.<br/><br/>

    Odbiór osobisty:<br/>
    W przypadku zamówienia produktów z odbiorem osobistym, zamówienie należy odebrać max do 3 dni roboczych od otrzymania powiadomienia.
    W przypadku nie odebrania zamówienia w w/w terminie Sprzedawca zastrzega sobie prawo do naliczenia dodatkowych opłat za magazynowanie.
    A w razie nie odebrania zamówienia powyżej 10 dni roboczych naliczona zostanie dodatkowo opłata za transport zamówienia na produkcję i ewentualny
    ponowny transport do salonu przy ul. Inżynierskiej 41/U13 we Wrocławiu. W takim wypadku termin realizacji może się wydłużyć o dodatkowy termin do 3 tygodni.
    """

    techniczne_info_paragraph = Paragraph(techniczne_info_text, tiny_style)

    laczna_cena_wszystko = laczna_cena_produktow + laczna_cena_obrobek + laczna_cena_uslug + laczna_cena_obrobek_dodatkowych
    cena_wszystko_paragraph = Paragraph(f"<b>RAZEM:</b> {f"{laczna_cena_wszystko:.2f}"} zł", right_align_style)


    if len(data) > 1:
        elements.append(table)
        elements.append(Spacer(1, 10))

    if len(data_obr) > 1:
        elements.append(Spacer(1, 20))
        elements.append(table_obr)
        elements.append(Spacer(1, 10))

    if len(data_obrobki_dodatkowe) > 1:
        elements.append(Spacer(1, 20))
        elements.append(obrobki_table)
        elements.append(Spacer(1, 10))

    if len(data_uslugi) > 1:
        elements.append(Spacer(1, 20))
        elements.append(table_uslugi)
        elements.append(Spacer(1, 10))

    if len(data) > 1 or len(data_obr) > 1 or len(data_uslugi) > 1 or len(data_obrobki_dodatkowe):
        elements.append(Spacer(1, 10))
        elements.append(cena_wszystko_paragraph)

    elements.append(Spacer(1, 30))
    elements.append(techniczne_info_paragraph)


    # Generowanie PDF
    doc.build(elements)

    buffer.seek(0)  # Resetowanie wskaźnika pliku
    return buffer


