import flet as ft
from fpdf import FPDF
import base64
from openai import OpenAI
import os
import shutil
# Actualización final corrección blur
# --- CONFIGURACIÓN ---
API_KEY = os.getenv("OPENAI_API_KEY")

# ¡¡PEGA AQUÍ TU ENLACE DE STRIPE!!
LINK_STRIPE = "https://buy.stripe.com/..."  

def main(page: ft.Page):
    page.title = "Reclamador IA"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = "#f0f4f8"
    page.scroll = "adaptive"

    # --- LOGICA DE ARCHIVOS EN NUBE ---
    # Creamos una carpeta temporal en el servidor para recibir las fotos
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)

    # --- CEREBRO DIGITAL ---
    def conectar_con_cerebro_real(ruta_imagen):
        if not API_KEY: 
            return "Error: Falta la API KEY. Configúrala en Render."
        
        try:
            client = OpenAI(api_key=API_KEY)
            
            # Leemos la imagen codificada
            with open(ruta_imagen, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')

            prompt = """
            Eres un abogado experto. Analiza este documento.
            Redacta UNA SOLA CARTA de reclamación formal y contundente.
            Usa un tono legal serio citando normativas.
            """
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "user", "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}},
                    ]}
                ],
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error IA: {e}"

    # --- EVENTOS DE LA APP ---

    def archivo_seleccionado(e):
        # Paso 1: El usuario elige foto. Iniciamos la subida al servidor.
        if not selector.result or not selector.result.files: return
        
        file = selector.result.files[0]
        
        # UI: Mostramos carga
        btn_subir.visible = False
        col_carga.visible = True
        txt_estado.value = f"Subiendo {file.name} al servidor seguro..."
        page.update()

        # TRUCO WEB: Generamos URL de subida y enviamos
        upload_url = page.get_upload_url(file.name, 600)
        selector.upload([ft.FilePickerUploadFile(file.name, upload_url=upload_url)])

    def archivo_subido(e):
        # Paso 2: La foto ya está en Render. Ahora la IA puede leerla.
        txt_estado.value = "La IA está redactando tu defensa..."
        page.update()
        
        # La ruta en el servidor es: uploads/nombre_archivo
        file_name = selector.result.files[0].name
        ruta_servidor = os.path.join(upload_dir, file_name)

        # Llamamos a la IA
        texto_final = conectar_con_cerebro_real(ruta_servidor)
        
        if "Error" in texto_final:
            txt_estado.value = texto_final
            txt_estado.color = "red"
            page.update()
            return

        # Generamos el PDF (pero no lo damos todavía)
        generar_pdf_local(texto_final)
        
        # UI: Mostramos la "Venta"
        col_carga.visible = False
        col_venta.visible = True
        page.update()

    def generar_pdf_local(texto):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=11)
        pdf.multi_cell(0, 8, txt=texto.encode('latin-1', 'replace').decode('latin-1'))
        # Guardamos en servidor
        pdf.output(os.path.join(upload_dir, "reclamacion_final.pdf"))

    def ir_a_pagar(e):
        page.launch_url(LINK_STRIPE)

    # --- INTERFAZ GRAFICA (UI) ---
    
    selector = ft.FilePicker(on_result=archivo_seleccionado, on_upload=archivo_subido)
    page.overlay.append(selector)

    # 1. Cabecera
    header = ft.Column([
        ft.Icon(ft.Icons.GAVEL, size=50, color="purple"),
        ft.Text("Reclamador IA", size=30, weight="bold"),
        ft.Text("Recupera tu dinero en segundos", color="grey")
    ], horizontal_alignment="center")

    # 2. Botón Subir
    btn_subir = ft.ElevatedButton(
        "SUBIR TICKET/FACTURA", 
        icon=ft.Icons.UPLOAD_FILE, 
        bgcolor="purple", color="white", height=50,
        on_click=lambda _: selector.pick_files(allow_multiple=False)
    )

    # 3. Zona de Carga
    col_carga = ft.Column([
        ft.ProgressBar(width=200, color="purple"),
        txt_estado := ft.Text("Esperando...", color="purple")
    ], visible=False, horizontal_alignment="center")

# 4. Zona de Venta (El Muro de Pago) - CORREGIDO
    col_venta = ft.Column([
        ft.Icon(ft.Icons.LOCK, size=60, color="#d97706"), # Candado
        ft.Text("¡Reclamación Generada!", size=20, weight="bold", color="green"),
        ft.Container(
            content=ft.Text("Vista Previa:\n\nEstimados Sres...\n[CONTENIDO BLOQUEADO]\n[CONTENIDO BLOQUEADO]...", 
                           color="grey", text_align="center"),
            padding=20,
            border=ft.border.all(1, "grey"),
            border_radius=10,
            # CAMBIO AQUÍ: Usamos 'blur' en lugar de 'filter' para máxima compatibilidad
            blur=10, 
            opacity=0.4 # Añadimos opacidad para reforzar el efecto de "bloqueado"
        ),
        ft.ElevatedButton(
            "DESBLOQUEAR Y DESCARGAR PDF (1.99€)", 
            bgcolor="#059669", color="white", height=60,
            on_click=ir_a_pagar
        ),
        ft.Text("Pago seguro vía Stripe", size=12, italic=True)
    ], visible=False, horizontal_alignment="center", spacing=20)

    page.add(ft.Column([
        ft.Divider(height=40, color="transparent"),
        header,
        ft.Divider(height=20, color="transparent"),
        btn_subir,
        col_carga,
        col_venta
    ], horizontal_alignment="center"))

# IMPORTANTE: upload_dir="uploads" permite que funcione en la web
ft.app(target=main, view=ft.AppView.WEB_BROWSER, upload_dir="uploads", port=int(os.getenv("PORT", 8080)), host="0.0.0.0")