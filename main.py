import streamlit as st
from fpdf import FPDF
import base64
from openai import OpenAI
import os

# --- PRELIMINARY CONFIG ---
st.set_page_config(page_title="Reclamador IA", page_icon="⚖️")

# --- CONFIGURACIÓN ---
API_KEY = os.getenv("OPENAI_API_KEY")
LINK_STRIPE = "https://buy.stripe.com/..."  # Update with your real link

# --- LOGICA DE ARCHIVOS EN NUBE ---
upload_dir = "uploads"
os.makedirs(upload_dir, exist_ok=True)

# --- CEREBRO DIGITAL ---
from pypdf import PdfReader

# --- CEREBRO DIGITAL ---
def conectar_con_cerebro_real(ruta_archivo):
    if not API_KEY: 
        return "Error: Falta la API KEY. Configúrala en Render/Environment."
    
    try:
        client = OpenAI(api_key=API_KEY)
        messages_payload = []
        
        # Detectar tipo de archivo
        ext = os.path.splitext(ruta_archivo)[1].lower()
        
        if ext == ".pdf":
            # LOGICA PDF: Extraer texto
            texto_pdf = ""
            try:
                reader = PdfReader(ruta_archivo)
                for page in reader.pages:
                    texto_pdf += page.extract_text() + "\n"
            except Exception as e:
                return f"Error leyendo PDF: {e}. Prueba subiendo una imagen (JPG/PNG)."
            
            if not texto_pdf.strip():
                return "Error: El PDF parece ser una imagen escaneada sin texto seleccionable. Por favor sube una FOTO (JPG/PNG) del documento."
                
            # Payload solo texto
            prompt = f"""
            Eres un abogado experto. Analiza el siguiente contenido extraído de un PDF de reclamación/factura.
            
            CONTENIDO DEL DOCUMENTO:
            {texto_pdf}
            
            Redacta UNA SOLA CARTA de reclamación formal y contundente.
            Usa un tono legal serio citando normativas.
            """
            messages_payload = [
                {"role": "user", "content": prompt}
            ]
            
        else:
            # LOGICA IMAGEN: Vision API
            with open(ruta_archivo, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')

            prompt = """
            Eres un abogado experto. Analiza este documento visual.
            Redacta UNA SOLA CARTA de reclamación formal y contundente.
            Usa un tono legal serio citando normativas.
            """
            
            messages_payload = [
                {"role": "user", "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}},
                ]}
            ]
        
        with st.spinner("La IA está redactando tu defensa..."):
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages_payload,
            )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error IA: {e}"

def generar_pdf_local(texto):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=11)
    # latin-1 encoding handling
    pdf.multi_cell(0, 8, txt=texto.encode('latin-1', 'replace').decode('latin-1'))
    
    output_path = os.path.join(upload_dir, "reclamacion_final.pdf")
    pdf.output(output_path)
    return output_path

# --- INTERFAZ GRAFICA (UI) ---

st.title("⚖️ Reclamador IA")
st.subheader("Recupera tu dinero en segundos")

# 1. Botón Subir
uploaded_file = st.file_uploader("Sube tu Ticket o Factura", type=["png", "jpg", "jpeg", "pdf"])

if uploaded_file is not None:
    # Guardar archivo localmente
    file_path = os.path.join(upload_dir, uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    st.success(f"Archivo subido: {uploaded_file.name}")
    
    # 2. Procesar (Simulando el flujo automático del Flet app, o con botón)
    if st.button("Generar Reclamación"):
        texto_final = conectar_con_cerebro_real(file_path)
        
        if "Error" in texto_final:
            st.error(texto_final)
        else:
            # Generamos PDF
            pdf_path = generar_pdf_local(texto_final)
            
            # 3. Zona de Venta (Muro de Pago)
            st.divider()
            st.markdown("### ¡Reclamación Generada!")
            
            # Vista previa borrosa (simulada con CSS o texto)
            st.info("Vista Previa:\n\nEstimados Sres...\n[CONTENIDO BLOQUEADO]...")
            
            # Botón de Pago (Link)
            st.markdown(f"""
                <a href="{LINK_STRIPE}" target="_blank">
                    <button style="
                        background-color:#059669; 
                        color:white; 
                        padding:15px; 
                        border:none; 
                        border-radius:5px; 
                        font-size:16px; 
                        cursor:pointer; 
                        width:100%">
                        🔓 DESBLOQUEAR Y DESCARGAR PDF (1.99€)
                    </button>
                </a>
                <p style="text-align:center; font-style:italic; font-size:12px; margin-top:5px;">Pago seguro vía Stripe</p>
            """, unsafe_allow_html=True)

