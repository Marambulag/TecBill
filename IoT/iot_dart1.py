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
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración de credenciales desde .env
DB_PASSWORD = os.getenv('DB_PASSWORD')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

openai.api_key = OPENAI_API_KEY

# Configuración de Flask
app = Flask(__name__)
CORS(app, resources={r"/enviar_correo": {"origins": "http://192.168.252.201"}})

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
        raise err

# Función para enviar correos electrónicos
def enviar_correo(destinatario, asunto, mensaje, archivo_adjunto):
    SMTP_HOST = "smtp.gmail.com"
    SMTP_PORT = 587
    REMITENTE = "tecbill462@gmail.com"

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
            print(f"Error al adjuntar el archivo: {e}")
    
    try:
        servidor = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
        servidor.starttls()
        servidor.login(REMITENTE, SMTP_PASSWORD)
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
                        {"role": "user", "content": f"Analiza los siguientes datos de ventas y proporciona un resumen de tendencias y observaciones importantes:\n{csv_data}"}
                    ]
                )
                analisis = response['choices'][0]['message']['content'].strip()
            except openai.error.OpenAIError as e:
                analisis = f"Error interactuando con OpenAI: {e}"

            # Generar PDF
            pdf_path = 'reporte_analisis.pdf'
            if not df.empty:
                resultado = df.groupby("id_producto")["cantidad"].sum().reset_index()
                resultado.rename(columns={"cantidad": "total_vendido"}, inplace=True)
                with PdfPages(pdf_path) as pdf:
                    plt.figure(figsize=(10, 6))
                    plt.bar(resultado["id_producto"].astype(str), resultado["total_vendido"], color='orange')
                    plt.title('Cantidad Total de Productos Vendidos')
                    plt.xlabel('Producto')
                    plt.ylabel('Cantidad Vendida')
                    plt.tight_layout()
                    pdf.savefig()
                    plt.close()

            return jsonify({"message": "Análisis realizado con éxito.", "analisis": analisis})
        return jsonify({"message": "No se encontraron datos."})
    except Exception as e:
        return jsonify({"error": f"Error al realizar el análisis: {e}"}), 500

# Ruta para actualizar el carrito
@app.route('/actualizar-carrito', methods=['POST'])
def actualizar_carrito():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        query_max_id = "SELECT MAX(ID) as max_id FROM carrito;"
        cursor.execute(query_max_id)
        result = cursor.fetchone()
        nuevo_id = (result['max_id'] or 0) + 1

        query_update_estado = "UPDATE carrito SET estado = 'completado' WHERE estado = 'activo';"
        cursor.execute(query_update_estado)

        query_insert_carrito = "INSERT INTO carrito (ID, estado) VALUES (%s, %s);"
        cursor.execute(query_insert_carrito, (nuevo_id, 'activo'))

        conn.commit()

        return jsonify({"message": "Carrito actualizado correctamente."})

    except mysql.connector.Error as err:
        return jsonify({"error": f"Error al actualizar el carrito: {err}"}), 500

# Ruta para finalizar la compra
@app.route('/finalizar-compra', methods=['POST'])
def finalizar_compra():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        query = "UPDATE carrito SET estado = 'completado' WHERE estado = 'activo';"
        cursor.execute(query)
        conn.commit()

        if cursor.rowcount > 0:
            return jsonify({"message": f"Estado actualizado con éxito. {cursor.rowcount} carrito(s) modificado(s)."})
        else:
            return jsonify({"message": "No se encontró ningún carrito activo para actualizar."})

    except mysql.connector.Error as err:
        return jsonify({"error": f"Error al finalizar la compra: {err}"}), 500

# Ruta para enviar correos electrónicos
@app.route('/enviar_correo', methods=['POST'])
def enviar_correo_endpoint():
    try:
        data = request.get_json()
        destinatario = data.get('destinatario')
        asunto = data.get('asunto')
        mensaje = data.get('mensaje')
        archivo_adjunto = data.get('archivo_adjunto')  # Asegúrate de pasar la ruta correcta del archivo
        
        enviar_correo(destinatario, asunto, mensaje, archivo_adjunto)
        return jsonify({"message": "Correo enviado exitosamente."})
    except Exception as e:
        return jsonify({"error": f"Error al enviar el correo: {e}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)