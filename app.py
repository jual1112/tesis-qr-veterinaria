import io
import os
from flask import Flask, redirect, render_template, request, send_file, url_for
import qrcode
from werkzeug.utils import secure_filename

app = Flask(__name__)

UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Base de datos en memoria con historial de vacunas
mascotas_db = {
    "PERRO-001": {
        "id": "PERRO-001",
        "nombre": "Bobby",
        "especie": "Canino - Mestizo",
        "edad": "3 Años",
        "sexo": "Macho (Castrado)",
        "color": "Marrón con manchas blancas",
        "foto": (
            "https://images.unsplash.com/photo-1543466835-00a7907e9de1?auto=format&fit=crop&q=80&w=400"
        ),
        "alerta_perdido": True,
        "tutor": "Juan Pérez",
        "telefono": "+59170000000",
        "zona": "Equipetrol, Santa Cruz",
        "cuidados": "Requiere medicación diaria para alergia cutánea.",
        "pin": "1234",
        "vacunas": [
            {
                "nombre": "Antirrábica",
                "estado": "Vigente",
                "vencimiento": "Nov 2027",
            },
            {
                "nombre": "Polivalente (Séxtuple)",
                "estado": "Vigente",
                "vencimiento": "Ene 2027",
            },
        ],
    }
}

ADMIN_PASSWORD = "admin"


# ==========================================
# 1. MENÚ PRINCIPAL CON BUSCADOR
# ==========================================
@app.route("/")
def index():
  busqueda = request.args.get("busqueda", "").strip().lower()
  lista_html = ""

  for id_m, m in mascotas_db.items():
    # Si hay texto en el buscador, filtramos por nombre, código o tutor
    if busqueda and not (
        busqueda in m["nombre"].lower()
        or busqueda in id_m.lower()
        or busqueda in m["tutor"].lower()
    ):
      continue

    estado_alerta = (
        ' <span style="background: #fee2e2; color: #dc2626; padding: 2px 6px; border-radius: 4px; font-size: 11px; font-weight: bold;">🚨 PERDIDO</span>'
        if m.get("alerta_perdido")
        else ""
    )
    lista_html += f"""
        <li style="margin-bottom: 12px; background: #ffffff; padding: 12px 15px; border-radius: 10px; border: 1px solid #e5e7eb; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 2px 4px rgba(0,0,0,0.02);">
            <div>
                <span style="font-size: 16px;"><b>{m['nombre']}</b> <span style="color: #6b7280; font-size: 13px;">({id_m})</span>{estado_alerta}</span><br>
                <span style="font-size: 13px; color: #4b5563;">Tutor: {m['tutor']}</span>
            </div>
            <div style="display: flex; gap: 8px;">
                <a href="/mascota/{id_m}" style="background: #047857; color: white; padding: 6px 10px; text-decoration: none; border-radius: 6px; font-size: 13px; font-weight: bold;">Ver Ficha</a>
                <a href="/qr/{id_m}" target="_blank" style="background: #2563eb; color: white; padding: 6px 10px; text-decoration: none; border-radius: 6px; font-size: 13px; font-weight: bold;">QR</a>
                <a href="/editar/{id_m}" style="background: #d97706; color: white; padding: 6px 10px; text-decoration: none; border-radius: 6px; font-size: 13px; font-weight: bold;">PIN</a>
            </div>
        </li>
        """

  if not lista_html:
    lista_html = (
        '<p style="text-align: center; color: #6b7280;">No se encontraron'
        " mascotas que coincidan con la búsqueda.</p>"
    )

  paw_svg = """
    <svg width="22" height="22" viewBox="0 0 24 24" fill="#059669" style="vertical-align: middle; display: inline-block;">
        <path d="M12 13c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zM7.5 10c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm9 0c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm-9-4c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm9 0c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm-4.5 9c-2.21 0-4 1.79-4 4 0 1.1.45 2.1 1.17 2.83.73.73 1.73 1.17 2.83 1.17s2.1-.45 2.83-1.17c.72-.73 1.17-1.73 1.17-2.83 0-2.21-1.79-4-4-4z"/>
    </svg>
    """

  limpiar_btn = (
      f'<a href="/" style="background: #6b7280; color: white; padding: 10px 15px; text-decoration: none; border-radius: 8px; font-weight: bold; display: flex; align-items: center;">Ver Todos</a>'
      if busqueda
      else ""
  )

  return f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <title>Sistema de Tesis QR Veterinario</title>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #f0fdf4 0%, #ecfdf5 100%);
                margin: 0;
                padding: 20px;
            }}
            .container {{
                max-width: 650px;
                margin: 40px auto;
                background: #ffffff;
                padding: 30px;
                border-radius: 16px;
                box-shadow: 0 10px 25px rgba(0, 0, 0, 0.08);
                border: 2px solid #a7f3d0;
                position: relative;
                overflow: hidden;
            }}
            .paw-decor {{
                position: absolute;
                opacity: 0.12;
            }}
            h2 {{
                color: #065f46;
                margin-top: 0;
                display: flex;
                align-items: center;
                gap: 10px;
            }}
            .btn-main {{
                background: #059669;
                color: white;
                padding: 12px 20px;
                text-decoration: none;
                border-radius: 8px;
                font-weight: bold;
                display: inline-block;
                box-shadow: 0 4px 6px rgba(5, 150, 105, 0.2);
            }}
            .btn-admin {{
                background: #374151;
                color: white;
                padding: 12px 20px;
                text-decoration: none;
                border-radius: 8px;
                font-weight: bold;
                display: inline-block;
                box-shadow: 0 4px 6px rgba(55, 65, 81, 0.2);
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="paw-decor" style="top: 15px; right: 20px; transform: rotate(20deg);">{paw_svg}</div>
            <div class="paw-decor" style="bottom: 15px; left: 20px; transform: rotate(-15deg);">{paw_svg}</div>

            <h2>{paw_svg} Sistema Inteligente de Identificación y Salud QR</h2>
            <p style="color: #4b5563; font-size: 15px;">Plataforma cloud para la gestión de registros clínicos, control de vacunación y localización de mascotas.</p>
            
            <!-- Barra de Búsqueda -->
            <form method="GET" action="/" style="margin: 20px 0; display: flex; gap: 10px;">
                <input type="text" name="busqueda" value="{busqueda}" placeholder="🔍 Buscar por nombre, código o tutor..." style="flex: 1; padding: 10px 14px; border: 1.5px solid #d1d5db; border-radius: 8px; font-size: 14px; outline: none;">
                <button type="submit" style="background: #059669; color: white; border: none; padding: 10px 18px; border-radius: 8px; font-weight: bold; cursor: pointer;">Buscar</button>
                {limpiar_btn}
            </form>

            <hr style="border: 0; border-top: 1px solid #e5e7eb; margin: 20px 0;">
            
            <h3 style="color: #1f2937; font-size: 18px;">{paw_svg} Mascotas Registradas:</h3>
            <ul style="list-style: none; padding: 0; margin-top: 15px;">
                {lista_html}
            </ul>
            
            <br>
            <div style="display: flex; gap: 12px; flex-wrap: wrap; margin-top: 10px;">
                <a href="/registrar" class="btn-main">+ Registrar Nueva Mascota</a>
                <a href="/admin" class="btn-admin">🔒 Panel Administrador</a>
            </div>
        </div>
    </body>
    </html>
    """


@app.route("/mascota/<id_mascota>")
def perfil_mascota(id_mascota):
  mascota = mascotas_db.get(id_mascota)
  if not mascota:
    return "Mascota no encontrada en el sistema", 404
  return render_template("perfil.html", mascota=mascota)


@app.route("/qr/<id_mascota>")
def generar_qr(id_mascota):
  mascota = mascotas_db.get(id_mascota)
  if not mascota:
    return "Mascota no encontrada", 404

  host_url = request.host_url.rstrip("/")
  url_perfil = f"{host_url}/mascota/{id_mascota}"

  img = qrcode.make(url_perfil)
  buffer = io.BytesIO()
  img.save(buffer, format="PNG")
  buffer.seek(0)

  return send_file(buffer, mimetype="image/png")


@app.route("/registrar", methods=["GET", "POST"])
def registrar():
  if request.method == "POST":
    id_m = request.form["id_mascota"]

    foto_url = "https://images.unsplash.com/photo-1583511655857-d19b40a7a54e?auto=format&fit=crop&q=80&w=400"
    if "foto" in request.files:
      file = request.files["foto"]
      if file and file.filename != "":
        filename = secure_filename(f"{id_m}_{file.filename}")
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(filepath)
        foto_url = f"/{filepath}"

    vacunas_iniciales = []
    v_nombre = request.form.get("vacuna_nombre")
    if v_nombre:
      vacunas_iniciales.append({
          "nombre": v_nombre,
          "estado": request.form.get("vacuna_estado", "Vigente"),
          "vencimiento": request.form.get("vacuna_vencimiento", "Próximamente"),
      })

    mascotas_db[id_m] = {
        "id": id_m,
        "nombre": request.form["nombre"],
        "especie": request.form["especie"],
        "edad": request.form["edad"],
        "sexo": request.form["sexo"],
        "color": request.form["color"],
        "foto": foto_url,
        "alerta_perdido": False,
        "tutor": request.form["tutor"],
        "telefono": request.form["telefono"],
        "zona": request.form["zona"],
        "cuidados": request.form["cuidados"],
        "pin": request.form["pin"],
        "vacunas": vacunas_iniciales,
    }
    return redirect(url_for("index"))

  return """
    <div style="font-family: Arial; max-width: 500px; margin: 40px auto; padding: 20px; border: 1px solid #ccc; border-radius: 10px; background: #fff;">
        <h2 style="color: #047857;">📝 Registrar Nueva Mascota</h2>
        <form method="POST" enctype="multipart/form-data" style="display: flex; flex-direction: column; gap: 10px;">
            <label><b>Código Único (Ej: PERRO-002):</b></label>
            <input type="text" name="id_mascota" required style="padding: 8px;">
            <label><b>Nombre del Perro:</b></label>
            <input type="text" name="nombre" required style="padding: 8px;">
            <label><b>Especie y Raza:</b></label>
            <input type="text" name="especie" value="Canino - " required style="padding: 8px;">
            <label><b>Edad:</b></label>
            <input type="text" name="edad" placeholder="Ej: 2 Años" style="padding: 8px;">
            <label><b>Sexo y Estado:</b></label>
            <input type="text" name="sexo" value="Macho / Hembra" style="padding: 8px;">
            <label><b>Señas / Color:</b></label>
            <input type="text" name="color" style="padding: 8px;">
            <label><b>📸 Sube la Foto del Perro:</b></label>
            <input type="file" name="foto" accept="image/*" style="padding: 8px; border: 1px solid #ccc; border-radius: 5px;">
            <label><b>Nombre del Tutor:</b></label>
            <input type="text" name="tutor" required style="padding: 8px;">
            <label><b>Teléfono (WhatsApp):</b></label>
            <input type="text" name="telefono" required style="padding: 8px;">
            <label><b>Zona / Ciudad:</b></label>
            <input type="text" name="zona" style="padding: 8px;">
            <label><b>Cuidados Médicos Especiales:</b></label>
            <textarea name="cuidados" style="padding: 8px;"></textarea>
            <hr style="margin: 10px 0;">
            <h4 style="color: #047857; margin: 0;">💉 Primera Vacuna (Opcional)</h4>
            <label>Nombre de la Vacuna:</label>
            <input type="text" name="vacuna_nombre" style="padding: 8px;">
            <label>Estado:</label>
            <select name="vacuna_estado" style="padding: 8px;">
                <option value="Vigente">Vigente</option>
                <option value="Por vencer">Por vencer</option>
            </select>
            <label>Fecha de Vencimiento:</label>
            <input type="text" name="vacuna_vencimiento" style="padding: 8px;">
            <hr style="margin: 10px 0;">
            <label style="color: #d97706; font-weight: bold;">🔑 PIN Secreto de 4 dígitos:</label>
            <input type="password" name="pin" maxlength="4" required style="padding: 8px; border: 2px solid #d97706;">
            <button type="submit" style="background: #047857; color: white; padding: 12px; border: none; border-radius: 5px; font-weight: bold; cursor: pointer; margin-top: 10px;">Guardar y Generar QR</button>
        </form>
        <br>
        <a href="/" style="color: #666;">← Volver al inicio</a>
    </div>
    """


# ==========================================
# 2. EDICIÓN POR PARTE DEL DUEÑO (CON PIN)
# ==========================================
@app.route("/editar/<id_mascota>", methods=["GET", "POST"])
def editar_mascota(id_mascota):
  mascota = mascotas_db.get(id_mascota)
  if not mascota:
    return "Mascota no encontrada", 404

  error = ""
  if request.method == "POST":
    pin_ingresado = request.form.get("pin")
    if pin_ingresado == mascota.get("pin"):
      mascota["nombre"] = request.form["nombre"]
      mascota["telefono"] = request.form["telefono"]
      mascota["zona"] = request.form["zona"]
      mascota["cuidados"] = request.form["cuidados"]
      mascota["alerta_perdido"] = "alerta_perdido" in request.form

      if "foto" in request.files:
        file = request.files["foto"]
        if file and file.filename != "":
          # Cambiamos id_m por id_mascota aquí abajo:
          filename = secure_filename(f"{id_mascota}_{file.filename}")
          filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
          file.save(filepath)
          mascota["foto"] = f"/{filepath}"

      nueva_vac_nombre = request.form.get("nueva_vac_nombre")
      if nueva_vac_nombre:
        mascota["vacunas"].append({
            "nombre": nueva_vac_nombre,
            "estado": request.form.get("nueva_vac_estado", "Vigente"),
            "vencimiento": request.form.get(
                "nueva_vac_vencimiento", "Próximamente"
            ),
        })

      return redirect(url_for("perfil_mascota", id_mascota=id_mascota))
    else:
      error = "❌ PIN incorrecto."

  perdidocheck = "checked" if mascota.get("alerta_perdido") else ""
  vacs_actuales = ""
  for v in mascota.get("vacunas", []):
    vacs_actuales += (
        f"<li>✔️ {v['nombre']} (Vence: {v['vencimiento']} - {v['estado']})</li>"
    )

  return f"""
    <div style="font-family: Arial; max-width: 500px; margin: 40px auto; padding: 20px; border: 1px solid #ccc; border-radius: 10px; background: #fff;">
        <h2 style="color: #d97706;">✏️ Editar Ficha de {mascota['nombre']}</h2>
        <p style="color: red; font-weight: bold;">{error}</p>
        <form method="POST" enctype="multipart/form-data" style="display: flex; flex-direction: column; gap: 10px;">
            <label><b>Nombre del Perro:</b></label>
            <input type="text" name="nombre" value="{mascota['nombre']}" required style="padding: 8px;">
            <label><b>Teléfono:</b></label>
            <input type="text" name="telefono" value="{mascota['telefono']}" required style="padding: 8px;">
            <label><b>Zona / Ciudad:</b></label>
            <input type="text" name="zona" value="{mascota['zona']}" style="padding: 8px;">
            <label><b>Cuidados:</b></label>
            <textarea name="cuidados" style="padding: 8px;">{mascota['cuidados']}</textarea>
            <label><b>📸 Cambiar Foto:</b></label>
            <input type="file" name="foto" accept="image/*" style="padding: 8px;">
            <label style="margin-top: 10px;">
                <input type="checkbox" name="alerta_perdido" {perdidocheck}> <b>🚨 Activar Alerta de "Perro Perdido"</b>
            </label>
            <hr style="margin: 10px 0;">
            <h4 style="color: #047857; margin: 0;">📋 Vacunas:</h4>
            <ul style="font-size: 13px; color: #4b5563; padding-left: 20px;">
                {vacs_actuales if vacs_actuales else "<li>No hay vacunas.</li>"}
            </ul>
            <h4 style="color: #d97706; margin: 0; margin-top: 5px;">💉 Agregar Vacuna:</h4>
            <input type="text" name="nueva_vac_nombre" placeholder="Nombre" style="padding: 8px;">
            <select name="nueva_vac_estado" style="padding: 8px;">
                <option value="Vigente">Vigente</option>
                <option value="Por vencer">Por vencer</option>
            </select>
            <input type="text" name="nueva_vac_vencimiento" placeholder="Vencimiento" style="padding: 8px;">
            <hr style="margin: 10px 0;">
            <label style="color: #d97706; font-weight: bold;">🔑 PIN Secreto:</label>
            <input type="password" name="pin" maxlength="4" required style="padding: 8px; border: 2px solid #d97706;">
            <button type="submit" style="background: #d97706; color: white; padding: 12px; border: none; border-radius: 5px; font-weight: bold; cursor: pointer; margin-top: 10px;">Actualizar</button>
        </form>
        <br>
        <a href="/" style="color: #666;">← Volver al inicio</a>
    </div>
    """


# ==========================================
# 3. PANEL DE ADMINISTRADOR GENERAL Y EDICIÓN ADMIN
# ==========================================
@app.route("/admin", methods=["GET", "POST"])
def admin_panel():
  # Verificamos si se envió la contraseña por POST o si ya está guardada en la sesión (simplificado con password form)
  password = request.form.get("password")

  # Para mantener la sesión simple en este prototipo de tesis, si hace POST con password correcto mostramos el panel
  if request.method == "POST" and password == ADMIN_PASSWORD:
    filas_admin = ""
    for id_m, m in mascotas_db.items():
      filas_admin += f"""
            <tr>
                <td style="padding: 10px; border-bottom: 1px solid #ddd;"><b>{id_m}</b></td>
                <td style="padding: 10px; border-bottom: 1px solid #ddd;">{m['nombre']}</td>
                <td style="padding: 10px; border-bottom: 1px solid #ddd;">{m['tutor']}</td>
                <td style="padding: 10px; border-bottom: 1px solid #ddd;">
                    <a href="/mascota/{id_m}" style="color: #047857; font-weight: bold;">Ver</a> | 
                    <a href="/admin/editar/{id_m}" style="color: #d97706; font-weight: bold;">Modificar</a> | 
                    <a href="/eliminar/{id_m}" style="color: #dc2626; font-weight: bold;" onclick="return confirm('¿Seguro que deseas eliminar esta mascota?');">Borrar</a>
                </td>
            </tr>
            """
    return f"""
        <div style="font-family: Arial; max-width: 850px; margin: 40px auto; padding: 25px; border: 1px solid #ccc; border-radius: 12px; background: #fff; box-shadow: 0 4px 10px rgba(0,0,0,0.05);">
            <h2 style="color: #1f2937;">🔒 Panel de Control del Administrador</h2>
            <p style="color: #666;">Gestión absoluta: puedes ver, modificar cualquier parámetro o eliminar registros del sistema.</p>
            <table style="width: 100%; border-collapse: collapse; margin-top: 20px;">
                <thead>
                    <tr style="background: #f3f4f6; text-align: left;">
                        <th style="padding: 10px;">ID</th>
                        <th style="padding: 10px;">Mascota</th>
                        <th style="padding: 10px;">Tutor</th>
                        <th style="padding: 10px;">Acciones de Control</th>
                    </tr>
                </thead>
                <tbody>
                    {filas_admin}
                </tbody>
            </table>
            <br>
            <a href="/" style="background: #1f2937; color: white; padding: 10px 18px; text-decoration: none; border-radius: 6px; font-weight: bold; display: inline-block;">← Volver al Inicio</a>
        </div>
        """

  # Formulario de Acceso al Admin
  return """
    <div style="font-family: Arial; max-width: 400px; margin: 60px auto; padding: 25px; border: 1px solid #ccc; border-radius: 12px; background: #fff; box-shadow: 0 4px 10px rgba(0,0,0,0.05);">
        <h2 style="color: #1f2937;">🔒 Acceso Administrador</h2>
        <p style="font-size: 13px; color: #666;">(Contraseña por defecto para tesis: <b>admin</b>)</p>
        <form method="POST" style="display: flex; flex-direction: column; gap: 12px;">
            <label><b>Contraseña:</b></label>
            <input type="password" name="password" required style="padding: 10px; border: 1px solid #ccc; border-radius: 6px;">
            <button type="submit" style="background: #1f2937; color: white; padding: 12px; border: none; border-radius: 6px; font-weight: bold; cursor: pointer;">Ingresar al Panel</button>
        </form>
        <br>
        <a href="/" style="color: #666; font-size: 14px; text-decoration: none;">← Volver al inicio</a>
    </div>
    """


# Ruta para que el administrador modifique los parámetros de cualquier mascota sin PIN
@app.route("/admin/editar/<id_mascota>", methods=["GET", "POST"])
def admin_editar_mascota(id_mascota):
  mascota = mascotas_db.get(id_mascota)
  if not mascota:
    return "Mascota no encontrada", 404

  if request.method == "POST":
    mascota["nombre"] = request.form["nombre"]
    mascota["especie"] = request.form["especie"]
    mascota["edad"] = request.form["edad"]
    mascota["sexo"] = request.form["sexo"]
    mascota["color"] = request.form["color"]
    mascota["tutor"] = request.form["tutor"]
    mascota["telefono"] = request.form["telefono"]
    mascota["zona"] = request.form["zona"]
    mascota["cuidados"] = request.form["cuidados"]
    mascota["pin"] = request.form[
        "pin"
    ]  # El admin puede ver o cambiar el PIN si es necesario
    mascota["alerta_perdido"] = "alerta_perdido" in request.form

    if "foto" in request.files:
      file = request.files["foto"]
      if file and file.filename != "":
        filename = secure_filename(f"{id_mascota}_{file.filename}")
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(filepath)
        mascota["foto"] = f"/{filepath}"

    return redirect(url_for("admin_panel"))

  perdidocheck = "checked" if mascota.get("alerta_perdido") else ""

  return f"""
    <div style="font-family: Arial; max-width: 550px; margin: 40px auto; padding: 25px; border: 1px solid #ccc; border-radius: 12px; background: #fff;">
        <h2 style="color: #1f2937;">🛠️ Administrador: Modificar Parámetros de {mascota['nombre']}</h2>
        <p style="color: #666; font-size: 13px;">Acceso de autoridad: puedes cambiar cualquier parámetro clínico o de contacto.</p>
        
        <form method="POST" enctype="multipart/form-data" style="display: flex; flex-direction: column; gap: 10px;">
            <label><b>Nombre de la Mascota:</b></label>
            <input type="text" name="nombre" value="{mascota['nombre']}" required style="padding: 8px;">
            
            <label><b>Especie y Raza:</b></label>
            <input type="text" name="especie" value="{mascota['especie']}" required style="padding: 8px;">
            
            <label><b>Edad:</b></label>
            <input type="text" name="edad" value="{mascota['edad']}" style="padding: 8px;">
            
            <label><b>Sexo y Estado:</b></label>
            <input type="text" name="sexo" value="{mascota['sexo']}" style="padding: 8px;">
            
            <label><b>Señas / Color:</b></label>
            <input type="text" name="color" value="{mascota['color']}" style="padding: 8px;">
            
            <label><b>Nombre del Tutor:</b></label>
            <input type="text" name="tutor" value="{mascota['tutor']}" required style="padding: 8px;">
            
            <label><b>Teléfono de Contacto:</b></label>
            <input type="text" name="telefono" value="{mascota['telefono']}" required style="padding: 8px;">
            
            <label><b>Zona / Ciudad:</b></label>
            <input type="text" name="zona" value="{mascota['zona']}" style="padding: 8px;">
            
            <label><b>Cuidados Médicos Especiales:</b></label>
            <textarea name="cuidados" style="padding: 8px; height: 60px;">{mascota['cuidados']}</textarea>
            
            <label><b>PIN Secreto del Dueño:</b></label>
            <input type="text" name="pin" value="{mascota.get('pin', '1234')}" maxlength="4" required style="padding: 8px;">
            
            <label><b>📸 Cambiar Fotografía:</b></label>
            <input type="file" name="foto" accept="image/*" style="padding: 6px;">

            <label style="margin-top: 5px;">
                <input type="checkbox" name="alerta_perdido" {perdidocheck}> <b>🚨 Activar Alerta de "Perro Perdido"</b>
            </label>
            
            <button type="submit" style="background: #1f2937; color: white; padding: 12px; border: none; border-radius: 6px; font-weight: bold; cursor: pointer; margin-top: 15px;">Guardar Cambios como Administrador</button>
        </form>
        <br>
        <a href="/admin" style="color: #666; text-decoration: none;">← Volver al Panel Administrador</a>
    </div>
    """


@app.route("/eliminar/<id_mascota>")
def eliminar_mascota(id_mascota):
  if id_mascota in mascotas_db:
    del mascotas_db[id_mascota]
  return redirect(url_for("admin_panel"))


if __name__ == "__main__":
  app.run(host="0.0.0.0", port=5000, debug=True)