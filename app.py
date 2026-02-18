import streamlit as st
from io import BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas
import os

st.set_page_config(page_title="Cotizador de Terrenos", layout="centered")

# Factores (idénticos a tu Excel)
FACTORES = {
    4: 0.03205147,
    5: 0.02761891,
    6: 0.02512613,
    7: 0.02281223,
    8: 0.02158101,
    9: 0.02067487,
    10: 0.01999317,
}

def money(q: float) -> str:
    return f"Q {q:,.2f}"

def generar_pdf_cotizacion(
    lote_num:str,
    cliente: str,
    asesor: str,
    area_m2: float,
    precio_base: float,
    enganche_pct: float,
    enganche_monto: float,
    saldo: float,
    años: int,
    cuota_mensual: float,
):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=LETTER)
    width, height = LETTER

    #logo
    # Encabezado: título izquierda + logo derecha
    c.setFont("Helvetica-Bold", 16)
    c.drawString(72, height - 72, "Cotización de Terreno")

    logo_path = os.path.join(os.path.dirname(__file__), "logo.png")  # o logo.jpg
    if os.path.exists(logo_path):
        logo_w = 80
        logo_h = 80
        x_logo = width - 72 - logo_w   # esquina superior derecha con margen
        y_logo = height - 90           # altura del logo
        c.drawImage(logo_path, x_logo, y_logo, width=logo_w, height=logo_h, mask='auto')

    # Línea separadora (opcional, se ve pro)
    c.line(72, height - 105, width - 72, height - 105)

    c.setFont("Helvetica", 10)
    c.drawString(72, height - 125, f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    c.drawString(72, height - 139, f"Cliente: {cliente}")
    c.drawString(72, height - 153, f"Asesor: {asesor}")
    c.setFont("Helvetica-Bold", 10)

    y = height - 185
    c.setFont("Helvetica-Bold", 12)
    c.drawString(72, y, "Detalle")
    y -= 18

    c.setFont("Helvetica", 11)
    
    c.drawString(72, y, f"Lote: {lote_num}")
    y -= 16
    c.drawString(72, y, f"Área: {area_m2:.2f} m²")
    y -= 16
    c.drawString(72, y, f"Precio base: {money(precio_base)}")
    y -= 22

    c.setFont("Helvetica-Bold", 12)
    c.drawString(72, y, "Resumen (modelo por factores)")
    y -= 18
    c.setFont("Helvetica", 11)

    def line(label, value):
        nonlocal y
        c.drawString(72, y, label)
        c.drawRightString(width - 72, y, value)
        y -= 16

    line("Enganche:", f"{money(enganche_monto)}  ({enganche_pct:.2f}%)")
    line("Saldo a financiar:", money(saldo))
    line("Plazo:", f"{años} años ({años*12} meses)")
    line("Cuota mensual:", money(cuota_mensual))

    
    # Línea en el pie (footer)
    c.setLineWidth(1)
    c.line(72, 90, width - 72, 90)  # <-- ajustar el 90 si se quieres más arriba/abajo

    c.setFont("Helvetica", 9)
    c.drawString(72, 72, "Desarrollado por M.Alfaro")

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer


st.title("Cotizador de Terrenos")
st.caption("Abre este link desde tu teléfono. Sin instalar nada.")

st.subheader("Datos de entrada")
colA, colB = st.columns(2)
lote_num = st.text_input("Número de lote", value="2-7-29")

area_m2 = colA.number_input("Área (m²)", min_value=0.0, value=189.0, step=1.0)
precio_base = colB.number_input("Precio del terreno (Q)", min_value=0.0, value=90587.41, step=500.0)

años = st.selectbox("Tiempo (años)", [4, 5, 6, 7, 8, 9, 10])
factor = FACTORES[años]

st.divider()
st.subheader("Enganche")

modo_enganche = st.radio(
    "¿Cómo desea ingresar el enganche?",
    ["Porcentaje (%)", "Monto (Q)"],
    horizontal=True
)

# Cálculo del enganche según el modo
if modo_enganche == "Porcentaje (%)":
    c1, c2 = st.columns([2, 1])
    enganche_pct = c1.slider("Enganche (%)", 0.0, 100.0, 7.0, step=0.5)

    enganche_monto = precio_base * (enganche_pct / 100.0)
    c2.metric("Equivalente (Q)", money(enganche_monto))

else:
    c1, c2 = st.columns([2, 1])
    enganche_monto = c1.number_input("Enganche (Q)", min_value=0.0, max_value=float(precio_base), value=min(0.07 * precio_base, precio_base), step=500.0)

    enganche_pct = (enganche_monto / precio_base * 100.0) if precio_base > 0 else 0.0
    c2.metric("Equivalente (%)", f"{enganche_pct:.2f}%")

saldo = max(0.0, precio_base - enganche_monto)
cuota_mensual = saldo * factor

st.divider()
st.subheader("Resumen")
st.caption(f"**Lote {lote_num} — {area_m2:.2f} m²**")

r1, r2 = st.columns(2)
r1.metric("Enganche", money(enganche_monto))
r2.metric("Saldo a financiar", money(saldo))

st.metric(f"Cuota mensual ({años} años)", money(cuota_mensual))

# Opcional: total en cuotas (si lo quieres mostrar)
#total_cuotas = cuota_mensual * (años * 12)
#st.caption(f"Total en cuotas ({años*12} meses): {money(total_cuotas)}")

st.divider()
st.subheader("Generar PDF")

p1, p2 = st.columns(2)
cliente = p1.text_input("Nombre del cliente")
asesor = p2.text_input("Nombre del asesor")

if st.button("Generar PDF"):
    if not cliente.strip() or not asesor.strip():
        st.error("Ingresa el nombre del cliente y del asesor.")
    else:
        pdf = generar_pdf_cotizacion(
            lote_num=lote_num.strip(),
            cliente=cliente.strip(),
            asesor=asesor.strip(),
            area_m2=float(area_m2),
            precio_base=float(precio_base),
            enganche_pct=float(enganche_pct),
            enganche_monto=float(enganche_monto),
            saldo=float(saldo),
            años=int(años),
            cuota_mensual=float(cuota_mensual),
        )

        filename = f"cotizacion_lote_{lote_num.strip().replace(' ','_')}_{cliente.strip().replace(' ','_')}.pdf"
        st.download_button(
            "Descargar PDF",
            data=pdf,
            file_name=filename,
            mime="application/pdf",
        )



st.caption("Tip: en teléfono, usa el menú del navegador → 'Agregar a pantalla de inicio'.")
st.caption("Desarrollado por M. Alfaro")
