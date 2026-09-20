# FreshTrack

## Requisitos previos

- **Python 3.11+**
- **Node.js LTS** (nodejs.org)
- **Tesseract OCR** (necesario para el escaneo de facturas): descárgalo de https://github.com/UB-Mannheim/tesseract/wiki e instálalo con las opciones por defecto.
  - Además del instalador, descarga el paquete de **idioma español**: https://github.com/tesseract-ocr/tessdata/raw/main/spa.traineddata y colócalo en `C:\Program Files\Tesseract-OCR\tessdata\spa.traineddata`.
  - Si `tesseract.exe` no quedó en `C:\Program Files\Tesseract-OCR\`, ajusta la ruta en `backend/app/ocr.py`.

## Cómo correr el proyecto (necesitas 2 terminales abiertas al mismo tiempo)

### Terminal 1 — Backend
```bash
cd backend
python -m venv venv
source venv/Scripts/activate      # Windows con Git Bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```
Verifica que quedó vivo abriendo: http://localhost:8000/salud → debe responder `{"estado":"ok"}`.

**Cada vez que abras una terminal nueva para el backend**, primero activa el entorno:
```bash
cd backend && source venv/Scripts/activate
uvicorn app.main:app --reload

### Terminal 2 — Frontend
```bash
cd frontend
npm install
npm run web
```
Se abre solo en http://localhost:8081.

**Importante:** el backend debe quedar corriendo en el puerto **8000** y el frontend en el **8081** — si cambias uno de los dos puertos, actualiza `frontend/src/services/api.js` (`BASE_URL`).

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