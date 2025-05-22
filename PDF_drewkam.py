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
from reportlab.lib.enums import TA_LEFT, TA_RIGHT
from reportlab.platypus import Paragraph


pdfmetrics.registerFont(TTFont("DejaVu", "DejaVuSans.ttf"))


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
    alignment=TA_RIGHT
)

h2_style = ParagraphStyle(
    name='H2',
    fontName='DejaVu',
    fontSize=13
)

# Ścieżka do zdjęcia
image_path = r"static/images/header.jpg"

def generuj_PDF(zamowienie, klient, usluga_pmt, usluga_pomiar, usluga_transport, usluga_montaz, cena_ppmmtt, cena_pomiaruu, cena_transportt, cena_montazuu, custom_obrobki=None):
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
        tel. 717 371 737<br/>
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
        rabat_paragraph = Paragraph(f"<b>Uwzględniono rabat do</b> {max_rabat:.0f}%", styles['Normal'])
        elements.insert(3, rabat_paragraph) 
        elements.insert(4, Spacer(1, 10))

    # Produkty
        # Produkty
    data = [
        ["LP.",
         "Producent",
         "Materiał",
         "Typ",
         "Ilość",
         "Długość\n[cm]",
         "Szerokość\n[cm]",
         "Grubość\n[cm]",
         "Cena\n[zł]",
         "Rabat\n[%]",
         "Cena\njednostkowa"
         ]
    ]
    for i, produkt in enumerate(zamowienie.lista_produktow):
        data.append([i + 1,
                     produkt.producent.nazwa,
                     produkt.material.replace(" ", "\n"),
                     produkt.typ,produkt.ilosc,
                     produkt.dlugosc,
                     produkt.szerokosc,
                     produkt.grubosc,
                     f"{round(produkt.cena_po_rabacie()):.2f}",
                     produkt.rabat,
                     produkt.cena_jednostkowa()
                     ])

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

    cena_produktow_paragraph = Paragraph(f"<b>Razem (produkty):</b> {laczna_cena_produktow:.2f} zł", laczna_style)

    # Produkty obróbek
    data_obr = [["LP.", "Obróbka", "Ilość", "Cena [zł]"]]

    for i, produkt in enumerate(zamowienie.lista_produktow, start=1):
        for obrobka, ilosc, cena_jednostkowa in produkt.obrobki_z_cenami():
            laczna_cena = ilosc * cena_jednostkowa
            data_obr.append([i, obrobka, ilosc, f"{laczna_cena:.2f}"])

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

    cena_obrobek_paragraph = Paragraph(f"<b>Razem (obróbki):</b> {laczna_cena_obrobek:.2f} zł", laczna_style)

    #Dodatkowe obrobki
    data_obrobki_dodatkowe = [["Nazwa", "Cena (zł)"]]
    for obrobka in custom_obrobki:
        data_obrobki_dodatkowe.append([obrobka["nazwa"], f'{obrobka["cena"]:.2f}'])

    obrobki_table = Table(data_obrobki_dodatkowe, hAlign='LEFT')
    obrobki_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 0), (-1, -1), 'DejaVu'),
        ('FONTSIZE', (0, 0), (-1, -1), 9)
    ]))

    cena_obrobek_dodatkowych_paragraph = Paragraph(
    f"<b>Razem (obróbki dodatkowe):</b> {laczna_cena_obrobek_dodatkowych:.2f} zł", laczna_style
    )
    
    # Usługi
    cena_ppmmtt = float(cena_ppmmtt or 0)
    cena_pomiaruu = float(cena_pomiaruu or 0)
    cena_transportt = float(cena_transportt or 0)
    cena_montazuu = float(cena_montazuu or 0)

    data_uslugi = [
        ["Usługa", "Cena [zł]"]
    ]
    if usluga_pmt:
        data_uslugi.append(["Pomiar, transport i montaż", f"{cena_ppmmtt:.2f}"])
    if usluga_pomiar:
        data_uslugi.append(["Pomiar", f"{cena_pomiaruu:.2f}"])
    if usluga_transport:
        data_uslugi.append(["Transport", f"{cena_transportt:.2f}"])
    if usluga_montaz:
        data_uslugi.append(["Montaż", f"{cena_montazuu:.2f}"])

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
    



    laczna_cena_uslug = cena_pomiaruu + cena_transportt + cena_montazuu + cena_ppmmtt

    cena_uslug_paragraph = Paragraph(f"<b>Razem (usługi):</b> {laczna_cena_uslug:.2f} zł", laczna_style)

    laczna_powierzchnia = sum([
        (produkt.dlugosc * produkt.szerokosc * produkt.ilosc) / 10000 
        for produkt in zamowienie.lista_produktow
    ])

    powierzchnia_paragraph = Paragraph(
        f"{laczna_powierzchnia:.2f} m²", 
        laczna_style
    )

    laczna_cena_wszystko = laczna_cena_produktow + laczna_cena_obrobek + laczna_cena_uslug + laczna_cena_obrobek_dodatkowych
    cena_wszystko_paragraph = Paragraph(f"<b>RAZEM:</b> {laczna_cena_wszystko:.2f} zł", right_align_style)



    if len(data) > 1:
        elements.append(Paragraph("Produkty:", h2_style))
        elements.append(Spacer(1, 8))
        elements.append(table)
        elements.append(Spacer(1, 10))
        elements.append(cena_produktow_paragraph)

    if len(data_obr) > 1:
        elements.append(Spacer(1, 20))
        elements.append(Paragraph("Obróbka:", h2_style))
        elements.append(Spacer(1, 8))
        elements.append(table_obr)
        elements.append(Spacer(1, 10))
        elements.append(cena_obrobek_paragraph)

    if len(data_obrobki_dodatkowe) > 1:
        elements.append(Spacer(1, 20))
        elements.append(Paragraph("Dodatkowa obróbka:", h2_style))
        elements.append(Spacer(1, 8))
        elements.append(obrobki_table)
        elements.append(Spacer(1, 10))
        elements.append(cena_obrobek_dodatkowych_paragraph)



    if len(data_uslugi) > 1:
        elements.append(Spacer(1, 20))
        elements.append(Paragraph("Usługi:", h2_style))
        elements.append(Spacer(1, 8))
        elements.append(table_uslugi)
        elements.append(Spacer(1, 10))
        elements.append(cena_uslug_paragraph)

    if len(data) > 1:
        elements.append(Spacer(1, 20))
        elements.append(powierzchnia_paragraph)

    if len(data) > 1 or len(data_obr) > 1 or len(data_uslugi) > 1 or len(data_obrobki_dodatkowe):
        elements.append(Spacer(1, 7))
        elements.append(cena_wszystko_paragraph)


    # Generowanie PDF
    doc.build(elements)

    buffer.seek(0)  # Resetowanie wskaźnika pliku
    return buffer


