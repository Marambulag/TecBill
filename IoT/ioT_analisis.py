import mysql.connector
import pandas as pd
import openai
import os
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from flask import Flask, jsonify, request
from flask_cors import CORS

# Configuración de Flask
app = Flask(__name__)
CORS(app)  # Habilita CORS para solicitudes entre dominios

# Configuración de la base de datos
def get_db_connection():
    try:
        connection = mysql.connector.connect(
             host="10.43.127.176",
            user="root",
            password="1234",
            database="autobill"
        )

        if connection.is_connected():
            print("Conexión a la base de datos exitosa.")
        return connection
    except mysql.connector.Error as err:
        print(f"Error al conectar a la base de datos: {err}")
        return None

# Configuración de la API de OpenAI
api_key = "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"
openai.api_key = api_key

# Función para enviar correos electrónicos
def enviar_correo(destinatario, asunto, mensaje, archivo_adjunto):
    SMTP_HOST = "smtp.gmail.com"
    SMTP_PORT = 587
    REMITENTE = "tecbill462@gmail.com"
    PASSWORD = "gnnh iipj jzch oigq"

    correo = MIMEMultipart()
    correo['From'] = REMITENTE
    correo['To'] = destinatario
    correo['Subject'] = asunto

    correo.attach(MIMEText(mensaje, 'plain', 'utf-8'))

    if archivo_adjunto:
        try:
            with open(archivo_adjunto, 'rb') as archivo:
                adjunto = MIMEBase('application', 'octet-stream')
                adjunto.set_payload(archivo.read())
            encoders.encode_base64(adjunto)
            adjunto.add_header('Content-Disposition', f'attachment; filename={os.path.basename(archivo_adjunto)}')
            correo.attach(adjunto)
        except Exception as e:
            print(f"Error al adjuntar el archvio: {e}")
    try:
        servidor = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
        servidor.starttls()
        servidor.login(REMITENTE, PASSWORD)
        servidor.sendmail(REMITENTE, destinatario, correo.as_string())
        servidor.quit()
        print("Correo enviado exitosamente.")
    except Exception as e:
        print(f"Error al enviar el correo: {e}")


# Ruta para realizar análisis de ventas, generar gráficos y utilizar OpenAI
@app.route('/analisis', methods=['GET'])
def realizar_analisis():
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        select_query = "SELECT * FROM carrito_producto"
        cursor.execute(select_query)
        rows = cursor.fetchall()

        if rows:
            df = pd.DataFrame(rows, columns=['id_carrito', 'id_producto', 'cantidad'])

            # Análisis de datos con OpenAI
            csv_data = df.to_string()
            try:
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "Eres un asistente de análisis de datos."},
                        {"role": "user", "content": f"Analiza los siguientes datos de ventas y proporciona un resumen de tendencias y observaciones importantes. Ademas dame posibles opciones de promociones y/o posibles mejoras en la tienda para que los productos menos vendidos sean mas vendidos.:\n{csv_data}"}
                    ]
                )
                analisis = response['choices'][0]['message']['content'].strip()
                print("Análisis de la API de OpenAI:")
                print(analisis)
            except openai.error.RateLimitError:
                analisis = "Rate limit alcanzado. Intenta más tarde."
            except openai.error.OpenAIError as e:
                analisis = f"Error al interactuar con la API de OpenAI: {e}"
            except Exception as e:
                analisis = f"Error inesperado: {e}"
            
                # Generar PDF con la gráfica y análisis
            pdf_path = 'reporte_analisis.pdf'
            with PdfPages(pdf_path) as pdf:
                try:
                # Página 1: Título y Gráfica
                    fig, ax = plt.subplots(figsize=(8.5, 11))
                    ax.axis('off')
                    ax.text(0.5, 0.7, 'Reporte de Productos Vendidos', fontsize=24, ha='center', va='center', fontweight='bold')
                    ax.text(0.5, 0.6, 'Tecbill', fontsize=16, ha='center', va='center', style='italic')
                    ax.text(0.5, 0.3, 'Fecha: 28/11/2024', fontsize=12, ha='center', va='center')
                    pdf.savefig(fig)
                    plt.close()

                    resultado = df.groupby("id_producto")["cantidad"].sum().reset_index()
                    resultado.rename(columns={"cantidad": "total_vendido"}, inplace=True)
                    plt.figure(figsize=(10, 6))
                    plt.bar(resultado["id_producto"].astype(str), resultado["total_vendido"], color='orange')
                    plt.title('Cantidad Total de Productos Vendidos', fontsize=16)
                    plt.xlabel('Producto', fontsize=14)
                    plt.ylabel('Cantidad Vendida', fontsize=14)
                    plt.xticks(rotation=45, ha='right')
                    plt.tight_layout()
                    plt.grid(axis='y', linestyle='--', alpha=0.7)
                    pdf.savefig()
                    plt.close()
                except Exception as e:
                    print("Error al generar la gráfica:", e)
        
                # Página 2: Análisis de OpenAI
                    # Página 2: Tabla
                fig, ax = plt.subplots(figsize=(8.5, 11))
                ax.axis('off')
                ax.text(0.5, 1, 'Analisis de datos', fontsize=16, ha='center', va='center', fontweight='bold')
                try:
                    # Dividir el texto si es muy largo
                    texto_dividido = analisis.split('\n')
                    pagina_actual = 1
                    max_lineas_por_pagina = 50  # Número máximo de líneas por página

                    while texto_dividido:
                        lineas_a_imprimir = texto_dividido[:max_lineas_por_pagina]  # Tomar las primeras líneas
                        texto_corto = '\n'.join(lineas_a_imprimir)  # Combinar en un solo texto
                        texto_dividido = texto_dividido[max_lineas_por_pagina:]  # Eliminar las líneas procesadas

                        # Crear nueva página en el PDF
                        fig, ax = plt.subplots(figsize=(8.5, 11))
                        ax.axis('off')
                        ax.text(0.1, 0.9, texto_corto, fontsize=12, wrap=True, transform=ax.transAxes, va='top')
                        pdf.savefig(fig)  # Guardar la página en el PDF
                        plt.close(fig)

                        print(f"Página {pagina_actual} generada con éxito.")
                        pagina_actual += 1

                    if os.path.exists(pdf_path):
                        file_size = os.path.getsize(pdf_path)
                        print(f"PDF generado correctamente. Tamaño del archivo: {file_size} bytes")
                    if file_size == 0:
                        print("Error: El PDF está vacío.")
                    else:
                        print("Error: No se generó el archivo PDF.")
                    
                    print("¿PDF generado?:", os.path.exists(pdf_path))  # Verificación del archivo
                except Exception as e:
                    print("Error al agregar el análisis:", e)
            
            # Verifica si el PDF se generó correctamente
            if os.path.exists(pdf_path):
                print(f"PDF generado con éxito: {pdf_path}")
                # Prueba abrir el PDF automáticamente (opcional, dependiendo del sistema operativo)
                try:
                    os.system(f"start {pdf_path}")  # Windows
                    # os.system(f"open {pdf_path}")  # macOS
                    # os.system(f"xdg-open {pdf_path}")  # Linux
                except Exception as e:
                    print(f"No se pudo abrir el PDF automáticamente: {e}")
            else:
                print("Error: No se pudo generar el PDF.")

            return jsonify({"message": "Análisis realizado y gráfico generado con éxito.", "analisis": analisis})

        return jsonify({"message": "No se encontraron datos en la tabla 'detalles_venta'."})
    except Exception as e:
        return jsonify({"error": f"Error al realizar el análisis: {str(e) or 'Error desconocido.'}"}), 500


# Ruta para enviar el PDF por correo
@app.route('/enviar_correo', methods=['POST'])
def enviar_correo_endpoint():
    realizar_analisis()
    data = request.get_json()
    destinatario = data.get('destinatario')
    asunto = data.get('asunto')
    mensaje = data.get('mensaje')
    archivo_adjunto = "reporte_analisis.pdf"

    if os.path.exists(archivo_adjunto):
        enviar_correo(destinatario, asunto, mensaje, archivo_adjunto)
        return jsonify({"message": "Correo enviado con éxito."})
    return jsonify({"error": f"El archivo {archivo_adjunto} no existe."}), 404

#realizar_analisis()
if __name__ == '__main__':
    #app.run(debug=True)
    app.run(host='0.0.0.0', port=5000)