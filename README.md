# FreshTrack

## Requisitos previos

- **Python 3.11 o 3.12 de 64 bits** (la versión validada es Python 3.12).
- **Node.js LTS** y npm (nodejs.org).
- **Git**, si se clona el proyecto.
- **Tesseract OCR** (necesario para el escaneo de facturas): descárgalo de https://github.com/UB-Mannheim/tesseract/wiki e instálalo con las opciones por defecto.
  - Además del instalador, descarga el paquete de **idioma español**: https://github.com/tesseract-ocr/tessdata/raw/main/spa.traineddata y colócalo en `C:\Program Files\Tesseract-OCR\tessdata\spa.traineddata`.
  - Si `tesseract.exe` no quedó en `C:\Program Files\Tesseract-OCR\`, ajusta la ruta en `backend/app/ocr.py`.

## Instalación y primer arranque

Ejecuta estos pasos una sola vez desde PowerShell en la raíz del proyecto:

```powershell
cd C:\ruta\FreshTrack-main
python -m venv backend\venv
.\backend\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r backend\requirements.txt
python -m pip install -r ml\requirements.txt
```

Si PowerShell bloquea la activación del entorno, ejecuta una vez `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` o usa directamente `backend\venv\Scripts\python.exe` en los comandos.

Si se usará la cámara, el modelo debe existir en `ml\modelos\modelo.tflite` y `ml\modelos\clases.json`. Si no existe, ejecuta:

```powershell
backend\venv\Scripts\python.exe ml\scripts\preparar_modelo.py
```

Ese proceso descarga varios GB y puede tardar alrededor de 90 minutos en CPU. No se debe repetir si ya existen los artefactos del modelo.

## Arranque local

Se necesitan dos terminales abiertas.

### Terminal 1: backend
```powershell
cd backend
.\venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
Verifica que quedó vivo abriendo: http://localhost:8000/salud → debe responder `{"estado":"ok"}`.

### Terminal 2: frontend
```powershell
cd frontend
npm ci
npm run web -- --lan
```
Con `npm ci` solo hace falta instalar dependencias una vez; después puede usarse `npm run web -- --lan`.

En el PC se puede abrir http://localhost:8081. Desde otro dispositivo usa `http://IP_DEL_PC:8081`.

**Importante:** el backend debe quedar corriendo en el puerto **8000** y el frontend en el **8081** — si cambias uno de los dos puertos, actualiza `frontend/src/services/api.js` (`BASE_URL`).

La app detecta automáticamente el host usado para abrir el frontend y consulta el backend en ese mismo host, usando el puerto 8000. Si la detección no aplica (por ejemplo, un dominio o proxy), fija la URL antes de iniciar Expo:

```powershell
$env:EXPO_PUBLIC_API_URL = "http://192.168.1.25:8000"
npm run web -- --lan
```

El celular y el PC deben estar en la misma red. El firewall de Windows debe permitir conexiones entrantes al puerto 8000 y Expo al puerto 8081. La base de datos SQLite permanece en el PC; el celular nunca se conecta directamente al archivo.

## Flujo de prueba sugerido

1. Regístrate con un correo nuevo y contraseña de 8+ caracteres.
2. Ve a **Escanear** → sube o toma foto de una factura → revisa/edita los productos detectados → confirma.
3. Ve a **Inventario** → deberían aparecer los productos, ordenados por el que vence primero.
4. Prueba **Agregar** para registrar un producto a mano.
5. Marca algún producto como "Consumido" o "Desechado".
6. Ve a **Mi cuenta** para editar tu nombre, cambiar tu contraseña, o cerrar sesión.

## Notas

- El escaneo de facturas necesita buena luz y texto legible; si sale "confianza baja", intenta con otra foto.
- Los datos se guardan en una base SQLite local (no se sube al repositorio).