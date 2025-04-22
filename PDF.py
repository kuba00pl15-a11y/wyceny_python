from flask import Flask, Response
import io
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Image, Spacer, Paragraph
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.styles import getSampleStyleSheet
from datetime import datetime
from dateutil.relativedelta import relativedelta


pdfmetrics.registerFont(TTFont("DejaVu", "DejaVuSans.ttf"))

# Ścieżka do zdjęcia
image_path = "D:\\GitHub_projects\\wyceny_python\\static\\images\\header.jpg"

def generuj_PDF(zamowienie, klient, usluga_pomiar, usluga_transport, usluga_montaz, cena_uslugi):
    # Tworzenie dokumentu PDF
    buffer = io.BytesIO()    
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0, leftMargin=0, rightMargin=0, bottomMargin=40)

    # Pobranie szerokości strony
    page_width, _ = A4

    # Wczytanie obrazka o pełnej szerokości strony
    img = Image(image_path, width=page_width, height=page_width * 0.07)  # Wysokość 20% szerokości

    # Style tekstu
    styles = getSampleStyleSheet()
    styles['Normal'].fontName = 'DejaVu'

    teraz = datetime.now()
    data_wyceny = teraz.strftime("%d.%m.%Y")
    data_waznosci = teraz + relativedelta(
        days=klient.dni, weeks=klient.tygodnie, months=klient.miesiace
    )
    data_waznosci_str = data_waznosci.strftime("%d.%m.%Y")

    s = f""
    dane_klienta_text = Paragraph(f"""
        {klient.imie + '<br/>' if len(klient.imie) else ''}
        {klient.adres + '<br/>' if len(klient.adres) else ''}
        {'tel. ' + klient.nr_tel + '<br/>' if len(klient.nr_tel) else ''}
        Data wyceny: {data_wyceny}<br/>
        {'Data ważności: ' + data_waznosci_str + '<br/>' if len(data_waznosci_str) else ''}
    """, styles['Normal'])

    # Produkty
    data = [
        ["LP.", "Producent", "Materiał", "Typ", "Długość [cm]", "Szerokość [cm]", "Grubość [cm]", "Cena [zł]"]
    ]
    for i, produkt in enumerate(zamowienie.lista_produktow):
        data.append([i + 1, produkt.producent.nazwa, produkt.material, produkt.typ, produkt.dlugosc, produkt.szerokosc, produkt.grubosc, produkt.cena()])

    # Dane klienta
    laczna_cena_produktow = sum([produkt.cena() for produkt in zamowienie.lista_produktow])
    laczna_cena_obrobek = sum([produkt.cena_obrobek() for produkt in zamowienie.lista_produktow])

    # Tworzenie tabeli produktów
    table = Table(data, hAlign='LEFT')
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 0), (-1, -1), 'DejaVu')
    ]))

    cena_produktow_paragraph = Paragraph(f"<b>Łączna cena produktów:</b> {laczna_cena_produktow:.2f} zł", styles['Normal'])

    # Produkty obróbek
    data_obr = [
        ["LP.", "Obróbki", "Cena [zł]"]
    ]
    for i, produkt in enumerate(zamowienie.lista_produktow):
        for obrobka in produkt.obrobki:
            data_obr.append([i, obrobka, 0])

    # Tworzenie tabeli obróbek
    table_obr = Table(data_obr, hAlign='LEFT')
    table_obr.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('TEXT-ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 0), (-1, -1), 'DejaVu')
    ]))

    cena_obrobek_paragraph = Paragraph(f"<b>Łączna cena obróbek:</b> {laczna_cena_obrobek:.2f} zł", styles['Normal'])

    # Usługi
    data_uslugi = [
        ["Usługa", "Cena [zł]"]
    ]
    if usluga_pomiar:
        data_uslugi.append(["Pomiar", cena_uslugi])
    if usluga_transport:
        data_uslugi.append(["Transport", cena_uslugi])
    if usluga_montaz:
        data_uslugi.append(["Montaż", cena_uslugi])

    # Tworzenie tabeli usług
    table_uslugi = Table(data_uslugi, colWidths=[200, 100], hAlign='LEFT')
    table_uslugi.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 0), (-1, -1), 'DejaVu')
    ]))

    # Dodajemy wszystkie elementy do listy 'elements'
    elements = [
        img, 
        Spacer(1, 20), 
        dane_klienta_text, 
        Spacer(1, 20), 
        (table if len(data) > 1 else None), 
        Spacer(1, 10), 
        (cena_produktow_paragraph if len(data) > 1 else None), 
        Spacer(1, 20), 
        (table_obr if len(data_obr) > 1 else None), 
        Spacer(1, 10), 
        (cena_obrobek_paragraph if len(data_obr) > 1 else None), 
        Spacer(1, 20), 
        (table_uslugi if len(data_uslugi) > 1 else None)]

    # Generowanie PDF
    doc.build(elements)

    buffer.seek(0)  # Resetowanie wskaźnika pliku
    return buffer


