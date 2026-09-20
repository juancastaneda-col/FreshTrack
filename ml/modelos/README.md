# Modelos entrenados

Artefactos que produce el pipeline de HU-08. Nada de este directorio va al repo (ver `.gitignore` local).

## Archivos generados

| Archivo | Uso |
|---|---|
| `modelo.keras` | Modelo Keras (~24 MB). Formato para reentrenar o continuar. |
| `modelo.tflite` | TensorFlow Lite float32 (~9.5 MB). Para uso en móvil. |
| `modelo_int8.tflite` | TFLite cuantizado a int8 (~2.8 MB). 3× más chico, más rápido en móvil. |
| `clases.json` | Mapeo índice → nombre de clase (importante para leer la predicción). |
| `reporte.txt` / `reporte.json` | Precisión global y por clase sobre el test set. |
| `matriz_confusion.png` | Matriz de confusión normalizada (imagen). |

## Cómo regenerar

```bash
# 1. Entrenar (usa splits/ generados por HU-07)
py -3.11 ml/scripts/entrenar.py

# 2. Evaluar sobre test set
py -3.11 ml/scripts/evaluar.py

# 3. Exportar a TFLite
py -3.11 ml/scripts/exportar.py
```

**Requiere Python 3.11** (TensorFlow 2.18 no soporta Python 3.14 en Windows).

## Resultados de la última corrida

- **Precisión global en test:** 99.60% (5,956 imágenes)
- **Precisión por clase:** todas ≥ 95%
- **Base:** MobileNetV2 preentrenado en ImageNet (transfer learning)
- **Entrenamiento:** 5 epochs feature extraction + 3 epochs fine-tuning
- **Batch size:** 32, Adam optimizer, class_weight balanceado
- **Duración:** ~1h 30min en CPU
