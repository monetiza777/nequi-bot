import os
import sqlite3
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

# CONFIGURACIÓN DE ADMIN - REEMPLAZA CON TU ID DE TELEGRAM
ADMIN_IDS = [7940691187]  # ⚠️ CAMBIA ESTO POR TU ID REAL DE TELEGRAM

class DatabaseManager:
    def __init__(self):
        self.db_name = "bot_database.db"
        self.init_database()
    
    def init_database(self):
        """Inicializar la base de datos y crear tablas"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Tabla de usuarios
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                is_blocked BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                usage_count INTEGER DEFAULT 0
            )
        ''')
        
        # Tabla de logs de uso
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS usage_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                details TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        conn.commit()
        conn.close()
        print("✅ Base de datos inicializada correctamente")
    
    def register_user(self, user_data):
        """Registrar o actualizar usuario"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO users 
                (telegram_id, username, first_name, last_name, last_used, usage_count)
                VALUES (?, ?, ?, ?, ?, COALESCE((SELECT usage_count FROM users WHERE telegram_id = ?), 0) + 1)
            ''', (
                user_data['id'], user_data.get('username'), 
                user_data.get('first_name'), user_data.get('last_name'),
                datetime.datetime.now(), user_data['id']
            ))
            
            conn.commit()
            
            # Obtener el ID del usuario
            cursor.execute('SELECT id FROM users WHERE telegram_id = ?', (user_data['id'],))
            user_id = cursor.fetchone()[0]
            
            # Registrar en logs
            cursor.execute('''
                INSERT INTO usage_logs (user_id, action, details)
                VALUES (?, ?, ?)
            ''', (user_id, 'BOT_USED', 'Usuario usó el bot'))
            
            conn.commit()
            
        except Exception as e:
            print(f"❌ Error registrando usuario: {e}")
        finally:
            conn.close()
    
    def is_user_blocked(self, telegram_id):
        """Verificar si usuario está bloqueado"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('SELECT is_blocked FROM users WHERE telegram_id = ?', (telegram_id,))
        result = cursor.fetchone()
        conn.close()
        
        return result and result[0] == 1
    
    def get_user_stats(self):
        """Obtener estadísticas generales"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM users')
        total_users = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM users WHERE is_blocked = 1')
        blocked_users = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM usage_logs')
        total_uses = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM users WHERE date(last_used) = date("now")')
        active_today = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_users': total_users,
            'blocked_users': blocked_users,
            'total_uses': total_uses,
            'active_today': active_today
        }
    
    def get_all_users(self):
        """Obtener lista de todos los usuarios"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT telegram_id, username, first_name, usage_count, is_blocked, last_used
            FROM users 
            ORDER BY last_used DESC
        ''')
        
        users = cursor.fetchall()
        conn.close()
        return users
    
    def toggle_user_block(self, telegram_id, block=True):
        """Bloquear o desbloquear usuario"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('UPDATE users SET is_blocked = ? WHERE telegram_id = ?', (block, telegram_id))
        conn.commit()
        conn.close()
        
        return f"✅ Usuario {'bloqueado' if block else 'desbloqueado'} correctamente"

class NequiReceiptGenerator:
    def __init__(self):
        try:
            self.template1 = Image.open("template.jpg")
            self.template2 = Image.open("template2.jpg")
            print("✅ Ambas plantillas cargadas correctamente")
        except Exception as e:
            print(f"❌ Error cargando plantillas: {e}")
            raise
        
    def generate_receipt_plantilla1(self, nombre, monto, numero_nequi):
        """Generar comprobante con plantilla 1 (original)"""
        try:
            # Crear copia de la plantilla 1
            img = self.template1.copy()
            draw = ImageDraw.Draw(img)
            
            # DEFINIR COLOR: NEGRO CON TOQUE MUY SUTIL DE MORADO
            color_texto = (20, 0, 35)  # Negro con un toque casi imperceptible de morado
            
            # USAR FUENTE MONTSERRAT - TODA LA FUENTE DEL MISMO TAMAÑO (42px)
            try:
                font_medium = ImageFont.truetype("Montserrat-Light.ttf", 42)
                font_large = ImageFont.truetype("Montserrat-Light.ttf", 42)
            except:
                try:
                    font_medium = ImageFont.truetype("Montserrat-Regular.ttf", 42)
                    font_large = ImageFont.truetype("Montserrat-Regular.ttf", 42)
                except:
                    try:
                        font_medium = ImageFont.truetype("Montserrat.ttf", 42)
                        font_large = ImageFont.truetype("Montserrat.ttf", 42)
                    except:
                        try:
                            font_medium = ImageFont.truetype("Poppins-Light.ttf", 42)
                            font_large = ImageFont.truetype("Poppins-Light.ttf", 42)
                        except:
                            try:
                                font_medium = ImageFont.truetype("segoeui.ttf", 42)
                                font_large = ImageFont.truetype("segoeui.ttf", 42)
                            except:
                                font_medium = ImageFont.load_default()
                                font_large = ImageFont.load_default()
            
            # COORDENADAS PLANTILLA 1
            coordinates = {
                'nombre': (84, 1030),
                'monto': (84, 1174),
                'numero': (84, 1320),
                'fecha': (84, 1460),
                'referencia': (84, 1613)
            }
            
            # Dibujar texto
            draw.text(coordinates['nombre'], nombre, fill=color_texto, font=font_medium)
            
            # MONTO CON $ Y FORMATO
            monto_formateado = f"${float(monto):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            draw.text(coordinates['monto'], monto_formateado, fill=color_texto, font=font_large)
            
            # NÚMERO FORMATEADO
            numero_formateado = f"{numero_nequi[:3]} {numero_nequi[3:6]} {numero_nequi[6:]}"
            draw.text(coordinates['numero'], numero_formateado, fill=color_texto, font=font_medium)
            
            # FECHA ACTUAL
            now = datetime.datetime.now()
            meses = {
                1: "enero", 2: "febrero", 3: "marzo", 4: "abril",
                5: "mayo", 6: "junio", 7: "julio", 8: "agosto",
                9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre"
            }
            fecha_str = f"{now.day} de {meses[now.month]} de {now.year} a las {now.strftime('%I:%M %p').lower()}"
            draw.text(coordinates['fecha'], fecha_str, fill=color_texto, font=font_medium)
            
            # REFERENCIA
            referencia = f"M{now.strftime('%H%M%S%f')[:8]}"
            draw.text(coordinates['referencia'], referencia, fill=color_texto, font=font_medium)
            
            print("✅ Imagen plantilla 1 generada correctamente")
            return img
            
        except Exception as e:
            print(f"❌ Error generando plantilla 1: {e}")
            raise

    def generate_receipt_plantilla2(self, nombre, monto, numero_nequi, llave):
        """Generar comprobante con plantilla 2 (nueva con LlaveB)"""
        try:
            # Crear copia de la plantilla 2
            img = self.template2.copy()
            draw = ImageDraw.Draw(img)
            
            # DEFINIR COLOR: NEGRO CON TOQUE MUY SUTIL DE MORADO
            color_texto = (20, 0, 35)
            
            # USAR FUENTE MONTSERRAT
            try:
                font_medium = ImageFont.truetype("Montserrat-Light.ttf", 42)
                font_large = ImageFont.truetype("Montserrat-Light.ttf", 42)
            except:
                try:
                    font_medium = ImageFont.truetype("Montserrat-Regular.ttf", 42)
                    font_large = ImageFont.truetype("Montserrat-Regular.ttf", 42)
                except:
                    try:
                        font_medium = ImageFont.truetype("Montserrat.ttf", 42)
                        font_large = ImageFont.truetype("Montserrat.ttf", 42)
                    except:
                        try:
                            font_medium = ImageFont.truetype("Poppins-Light.ttf", 42)
                            font_large = ImageFont.truetype("Poppins-Light.ttf", 42)
                        except:
                            try:
                                font_medium = ImageFont.truetype("segoeui.ttf", 42)
                                font_large = ImageFont.truetype("segoeui.ttf", 42)
                            except:
                                font_medium = ImageFont.load_default()
                                font_large = ImageFont.load_default()
            
            # COORDENADAS PLANTILLA 2 - ⚠️ AJUSTAR ESTAS COORDENADAS
            coordinates = {
                'nombre': (98, 1050),
                'monto': (126, 1526),
                'numero': (98, 1761),
                'fecha': (98, 1407),
                'referencia': (99, 1642),
                'llave': (98, 1168)  # ⚠️ NUEVA COORDENADA PARA LLAVE
            }
            
            # Dibujar texto
            draw.text(coordinates['nombre'], nombre, fill=color_texto, font=font_medium)
            
            # MONTO SIN $ - SOLO NÚMEROS
            monto_formateado = f"{float(monto):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            draw.text(coordinates['monto'], monto_formateado, fill=color_texto, font=font_large)
            
            # NÚMERO FORMATEADO
            numero_formateado = f"{numero_nequi[:3]} {numero_nequi[3:6]} {numero_nequi[6:]}"
            draw.text(coordinates['numero'], numero_formateado, fill=color_texto, font=font_medium)
            
            # FECHA ACTUAL
            now = datetime.datetime.now()
            meses = {
                1: "enero", 2: "febrero", 3: "marzo", 4: "abril",
                5: "mayo", 6: "junio", 7: "julio", 8: "agosto",
                9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre"
            }
            fecha_str = f"{now.day} de {meses[now.month]} de {now.year} a las {now.strftime('%I:%M %p').lower()}"
            draw.text(coordinates['fecha'], fecha_str, fill=color_texto, font=font_medium)
            
            # REFERENCIA
            referencia = f"M{now.strftime('%H%M%S%f')[:8]}"
            draw.text(coordinates['referencia'], referencia, fill=color_texto, font=font_medium)
            
            # LLAVE (NUEVO CAMPO) - LIMPIAR TEXTO
            llave_limpia = llave.replace('`', '').strip()  # Remover comillas y espacios
            draw.text(coordinates['llave'], llave_limpia, fill=color_texto, font=font_medium)
            
            print("✅ Imagen plantilla 2 generada correctamente")
            return img
            
        except Exception as e:
            print(f"❌ Error generando plantilla 2: {e}")
            raise

# Inicializar componentes
try:
    generator = NequiReceiptGenerator()
    db = DatabaseManager()
    print("✅ Generador y base de datos inicializados")
except Exception as e:
    print(f"❌ Error inicializando: {e}")
    generator = None
    db = None

# FUNCIONES DE ADMIN
async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Panel de administración"""
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ No tienes permisos de administrador")
        return
    
    stats = db.get_user_stats()
    
    message = (
        "🔧 **PANEL DE ADMINISTRACIÓN**\n\n"
        f"👥 **Usuarios totales:** {stats['total_users']}\n"
        f"🚫 **Usuarios bloqueados:** {stats['blocked_users']}\n"
        f"📊 **Usos totales:** {stats['total_uses']}\n"
        f"🟢 **Activos hoy:** {stats['active_today']}\n\n"
        "**Comandos disponibles:**\n"
        "/users - Listar usuarios\n"
        "/block ID - Bloquear usuario\n"
        "/unblock ID - Desbloquear usuario\n"
        "/stats - Estadísticas detalladas"
    )
    
    await update.message.reply_text(message)

async def users_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Listar todos los usuarios"""
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ No tienes permisos de administrador")
        return
    
    users = db.get_all_users()
    
    if not users:
        await update.message.reply_text("📭 No hay usuarios registrados")
        return
    
    message = "👥 **LISTA DE USUARIOS**\n\n"
    for i, user in enumerate(users[:20], 1):
        telegram_id, username, first_name, usage_count, is_blocked, last_used = user
        status = "🚫" if is_blocked else "✅"
        username_display = f"@{username}" if username else first_name or f"ID: {telegram_id}"
        
        message += f"{i}. {username_display}\n"
        message += f"   🆔: {telegram_id} | 📊: {usage_count} usos | {status}\n\n"
    
    if len(users) > 20:
        message += f"\n... y {len(users) - 20} usuarios más"
    
    await update.message.reply_text(message)

async def block_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Bloquear usuario"""
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ No tienes permisos de administrador")
        return
    
    if not context.args:
        await update.message.reply_text("❌ Uso: /block <ID_USUARIO>")
        return
    
    try:
        user_id = int(context.args[0])
        result = db.toggle_user_block(user_id, block=True)
        await update.message.reply_text(result)
    except ValueError:
        await update.message.reply_text("❌ ID debe ser un número")

async def unblock_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Desbloquear usuario"""
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ No tienes permisos de administrador")
        return
    
    if not context.args:
        await update.message.reply_text("❌ Uso: /unblock <ID_USUARIO>")
        return
    
    try:
        user_id = int(context.args[0])
        result = db.toggle_user_block(user_id, block=False)
        await update.message.reply_text(result)
    except ValueError:
        await update.message.reply_text("❌ ID debe ser un número")

# FUNCIONES PRINCIPALES DEL BOT
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /start"""
    user = update.effective_user
    db.register_user({
        'id': user.id,
        'username': user.username,
        'first_name': user.first_name,
        'last_name': user.last_name
    })
    
    await update.message.reply_text(
        "🤖 **BOT DE COMPROBANTES**\n\n"
        "**Comprobante de pago nequi (Original):**\n"
        "`Nombre | Monto | Número`\n\n"
        "**Comprobante de pago nequi (Llave Bre-B):**\n"
        "`LlaveB Nombre | Monto | Número tuyo | Llave de la persona`\n\n"
        "📝 **Ejemplos:**\n"
        "Comprobante pago nequi normal \n\n"
        "`Juan Perez | 107000 | 3120004444`\n\n"
        "comprobante llave Bre-B \n\n"
        "`LlaveB Maria Gonzalez | 107000 | 3159876543 | xx3tr@gmail.com`"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manejar mensajes normales"""
    if generator is None or db is None:
        await update.message.reply_text("❌ Error: El bot no está disponible")
        return
    
    # Verificar si usuario está bloqueado
    if db.is_user_blocked(update.effective_user.id):
        await update.message.reply_text("❌ Tu acceso ha sido bloqueado")
        return
    
    # Registrar uso
    user = update.effective_user
    db.register_user({
        'id': user.id,
        'username': user.username,
        'first_name': user.first_name,
        'last_name': user.last_name
    })
    
    try:
        text = update.message.text.strip()
        print(f"📨 Mensaje recibido de {user.username}: {text}")
        
        # DETECTAR TIPO DE PLANTILLA
        if text.upper().startswith("LLAVEB"):
            # PLANTILLA 2 - Formato: "LlaveB Nombre | Monto | Número | Llave"
            partes = text.split('|')
            if len(partes) == 4:
                # Remover "LlaveB" del primer elemento
                nombre = partes[0].replace("LlaveB", "").strip()
                monto = partes[1].strip()
                numero = partes[2].strip()
                llave = partes[3].strip()
                
                # Validar datos
                if not nombre or not monto or not numero or not llave:
                    await update.message.reply_text("❌ Todos los campos son obligatorios para LlaveB")
                    return
                
                # Generar imagen plantilla 2
                img = generator.generate_receipt_plantilla2(nombre, monto, numero, llave)
                caption = f"✅ Comprobante LlaveB generado para {nombre}"
                
            else:
                await update.message.reply_text(
                    "❌ Formato incorrecto para LlaveB. Usa:\n"
                    "`LlaveB Nombre | Monto | Número tuyo | Llave de la persona`\n\n"
                    "Ejemplo: `LlaveB Maria Gonzalez | 107000 | 3120007777 | @312007777`"
                )
                return
                
        else:
            # PLANTILLA 1 - Formato original: "Nombre | Monto | Número"
            if '|' in text:
                datos = text.split('|')
            elif ',' in text:
                datos = text.split(',')
            else:
                await update.message.reply_text(
                    "❌ Formato incorrecto. Usa:\n"
                    "🧾RECIBO DE NEQUI NORMAL🧾 \n"
                    "`Nombre | Monto | Número \n"
                    
                    "🧾RECIBO LLAVE Bre-B🧾 \n"
                    " LlaveB  Nombre | Monto | Número | Llave \n " \
                    " ⬇️⬇️⬇️⬇️⬇️⬇️ \n " \
                    "TODO DEBE DE IR SEPARADO CON ESTE SIMBOLO DE BARRA VERTICAL | \n "
                    "RECIBO DE LLAVE Bre-B SIEMPRE VA ESCRITO PRIMERO LlaveB SIGUE EL Nombre TAL CUAL \n" \
                    "COMO EL EJEMPLO DE ARRIBA"
                )
                return
            
            if len(datos) == 3:
                nombre, monto, numero = [d.strip() for d in datos]
                
                # Validar datos
                if not nombre or not monto or not numero:
                    await update.message.reply_text("❌ Todos los campos son obligatorios")
                    return
                
                # Generar imagen plantilla 1
                img = generator.generate_receipt_plantilla1(nombre, monto, numero)
                caption = f"✅ Comprobante generado para {nombre}"
                
            else:
                await update.message.reply_text(
                    "❌ Necesito exactamente 3 datos para Plantilla 1:\n"
                    "1. Nombre\n2. Monto\n3. Número\n\n"
                    "O 4 datos para Plantilla 2 con LlaveB"
                )
                return
        
        # Guardar y enviar imagen
        img_path = f"temp_{update.message.id}.jpg"
        img.save(img_path, quality=95)
        print(f"💾 Imagen guardada: {img_path}")
        
        with open(img_path, 'rb') as photo:
            await update.message.reply_photo(photo=photo, caption=caption)
        print("📤 Imagen enviada al usuario")
        
        # Eliminar archivo temporal
        os.remove(img_path)
        print("🗑️ Archivo temporal eliminado")
            
    except Exception as e:
        error_msg = f"❌ Error procesando tu solicitud: {str(e)}"
        print(error_msg)
        await update.message.reply_text(error_msg)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"❌ Error del bot: {context.error}")

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
    app.add_handler(CommandHandler("admin", admin_command))
    app.add_handler(CommandHandler("users", users_command))
    app.add_handler(CommandHandler("block", block_command))
    app.add_handler(CommandHandler("unblock", unblock_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_error_handler(error_handler)
    
    print("✅ Bot configurado. Iniciando polling...")
    app.run_polling()

if __name__ == '__main__':
    main()