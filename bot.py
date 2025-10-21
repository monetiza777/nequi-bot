import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from PIL import Image, ImageDraw, ImageFont
import datetime
from dotenv import load_dotenv
import logging

# Configurar logging para ver errores
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

load_dotenv()

class NequiReceiptGenerator:
    def __init__(self, template_path):
        try:
            self.template = Image.open(template_path)
            print("✅ Plantilla cargada correctamente")
        except Exception as e:
            print(f"❌ Error cargando plantilla: {e}")
            raise
        
    def generate_receipt(self, nombre, monto, numero_nequi):
        try:
            # Crear copia de la plantilla
            img = self.template.copy()
            draw = ImageDraw.Draw(img)
            
            # DEFINIR COLOR: NEGRO CON TOQUE MUY SUTIL DE MORADO
            color_texto = (20, 0, 35)  # Negro con un toque casi imperceptible de morado
            
            # USAR FUENTE MONTSERRAT - TODA LA FUENTE DEL MISMO TAMAÑO (42px)
            try:
                # TODA LA FUENTE DE 42px
                font_medium = ImageFont.truetype("Montserrat-Light.ttf", 42)
                font_large = ImageFont.truetype("Montserrat-Light.ttf", 42)  # Ahora igual
                print("✅ Usando Montserrat Light - Toda la fuente 42px")
            except:
                try:
                    # Si no funciona, probar con Montserrat Regular
                    font_medium = ImageFont.truetype("Montserrat-Regular.ttf", 42)
                    font_large = ImageFont.truetype("Montserrat-Regular.ttf", 42)
                    print("✅ Usando Montserrat Regular - Toda la fuente 42px")
                except:
                    try:
                        # Si no funciona, probar con Montserrat
                        font_medium = ImageFont.truetype("Montserrat.ttf", 42)
                        font_large = ImageFont.truetype("Montserrat.ttf", 42)
                        print("✅ Usando Montserrat - Toda la fuente 42px")
                    except:
                        try:
                            # Si no encuentra Montserrat, probar con Poppins
                            font_medium = ImageFont.truetype("Poppins-Light.ttf", 42)
                            font_large = ImageFont.truetype("Poppins-Light.ttf", 42)
                            print("✅ Usando Poppins Light - Toda la fuente 42px")
                        except:
                            try:
                                # Último respaldo: Segoe UI
                                font_medium = ImageFont.truetype("segoeui.ttf", 42)
                                font_large = ImageFont.truetype("segoeui.ttf", 42)
                                print("⚠️ Usando Segoe UI - Toda la fuente 42px")
                            except:
                                # Si nada funciona, usar por defecto
                                font_medium = ImageFont.load_default()
                                font_large = ImageFont.load_default()
                                print("⚠️ Usando fuentes por defecto")
            
            # COORDENADAS AJUSTADAS - TODOS LOS CAMPOS
            coordinates = {
                'nombre': (84, 1033),    # Encima de "¿Cuánto?"
                'monto': (84, 1174),     # Encima de "Número Nequi"
                'numero': (84, 1320),    # Encima de "Fecha"
                'fecha': (84, 1460),     # Encima de "Referencia"
                'referencia': (84, 1613) # En su campo
            }
            
            # Dibujar texto en las coordenadas CON COLOR
            draw.text(coordinates['nombre'], nombre, fill=color_texto, font=font_medium)
            
            # FORMATEAR MONTO CON SEPARADORES DE MILES
            monto_formateado = f"${float(monto):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            draw.text(coordinates['monto'], monto_formateado, fill=color_texto, font=font_large)
            
            # FORMATEAR NÚMERO TELEFÓNICO CON ESPACIOS CADA 3 DÍGITOS
            numero_formateado = f"{numero_nequi[:3]} {numero_nequi[3:6]} {numero_nequi[6:]}"
            draw.text(coordinates['numero'], numero_formateado, fill=color_texto, font=font_medium)
            
            # Fecha y hora actual
            now = datetime.datetime.now()
            meses = {
                1: "enero", 2: "febrero", 3: "marzo", 4: "abril",
                5: "mayo", 6: "junio", 7: "julio", 8: "agosto",
                9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre"
            }
            fecha_str = f"{now.day} de {meses[now.month]} de {now.year} a las {now.strftime('%I:%M %p').lower()}"
            draw.text(coordinates['fecha'], fecha_str, fill=color_texto, font=font_medium)
            
            # Referencia única de 8 dígitos
            referencia = f"M{now.strftime('%H%M%S%f')[:8]}"
            draw.text(coordinates['referencia'], referencia, fill=color_texto, font=font_medium)
            
            print("✅ Imagen generada correctamente")
            return img
            
        except Exception as e:
            print(f"❌ Error generando imagen: {e}")
            raise

# Inicializar generador
try:
    generator = NequiReceiptGenerator("template.jpg")
    print("✅ Generador inicializado")
except Exception as e:
    print(f"❌ Error inicializando generador: {e}")
    generator = None

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 **BOT DE COMPROBANTES NEQUI**\n\n"
        "Envíame los datos en este formato:\n"
        "`Nombre | Monto | Número Nequi`\n\n"
        "📝 **Ejemplo:**\n"
        "`Dora Valencia | 100.00 | 3122122032`\n\n"
        "¡Y recibirás tu comprobante actualizado!"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if generator is None:
        await update.message.reply_text("❌ Error: El generador no está disponible")
        return
        
    try:
        text = update.message.text
        print(f"📨 Mensaje recibido: {text}")
        
        # Separar por | o ,
        if '|' in text:
            datos = text.split('|')
        elif ',' in text:
            datos = text.split(',')
        else:
            await update.message.reply_text(
                "❌ Formato incorrecto. Usa:\n"
                "`Nombre | Monto | Número`\n\n"
                "Ejemplo: `Juan Perez | 150.50 | 3121234567`"
            )
            return
        
        if len(datos) == 3:
            nombre, monto, numero = [d.strip() for d in datos]
            
            print(f"📊 Procesando: {nombre}, {monto}, {numero}")
            
            # Validar datos
            if not nombre or not monto or not numero:
                await update.message.reply_text("❌ Todos los campos son obligatorios")
                return
            
            # Generar imagen
            img = generator.generate_receipt(nombre, monto, numero)
            
            # Guardar temporalmente
            img_path = f"temp_{update.message.id}.jpg"
            img.save(img_path, quality=95)
            print(f"💾 Imagen guardada: {img_path}")
            
            # Enviar imagen
            with open(img_path, 'rb') as photo:
                await update.message.reply_photo(
                    photo=photo,
                    caption=f"✅ Comprobante generado para {nombre}"
                )
            print("📤 Imagen enviada al usuario")
            
            # Eliminar archivo temporal
            os.remove(img_path)
            print("🗑️ Archivo temporal eliminado")
            
        else:
            await update.message.reply_text(
                "❌ Necesito exactamente 3 datos:\n"
                "1. Nombre\n2. Monto\n3. Número Nequi\n\n"
                "Separados por | o ,"
            )
            
    except Exception as e:
        error_msg = f"❌ Error procesando tu solicitud: {str(e)}"
        print(error_msg)
        await update.message.reply_text(error_msg)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"❌ Error del bot: {context.error}")
    if update and update.message:
        await update.message.reply_text("❌ Ocurrió un error inesperado")

def main():
    # Obtener token desde variable de entorno
    TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    
    if not TOKEN:
        print("❌ No se encontró TELEGRAM_BOT_TOKEN en .env")
        return
    
    print("🤖 Iniciando bot de Telegram...")
    
    # Crear aplicación
    app = Application.builder().token(TOKEN).build()
    
    # Handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_error_handler(error_handler)
    
    print("✅ Bot configurado. Iniciando polling...")
    app.run_polling()

if __name__ == '__main__':
    main()