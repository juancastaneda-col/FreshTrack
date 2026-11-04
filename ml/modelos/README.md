# Modelos entrenados




## Cómo regenerar

```bash
# 1. Entrenar (usa splits/ generados por HU-07)
py -3.11 ml/scripts/entrenar.py

# 2. Evaluar sobre test set
py -3.11 ml/scripts/evaluar.py

# 3. Exportar a TFLite
py -3.11 ml/scripts/exportar.py
```

**Requiere Python 3.11** 
## Resultados de la última corrida

- **Precisión global en test:** 99.60% (5,956 imágenes)
- **Precisión por clase:** todas ≥ 95%
- **Base:** MobileNetV2 preentrenado en ImageNet (transfer learning)
- **Entrenamiento:** 5 epochs feature extraction + 3 epochs fine-tuning
- **Batch size:** 32, Adam optimizer, class_weight balanceado
- **Duración:** ~1h 30min en CPU
