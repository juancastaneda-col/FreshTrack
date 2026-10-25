import { useCallback, useState } from 'react';
import { Image, Platform, ScrollView, StyleSheet, TouchableOpacity, View } from 'react-native';
import { useFocusEffect } from '@react-navigation/native';
import { Button, Text } from 'react-native-paper';
import * as ImagePicker from 'expo-image-picker';

import { api } from '../services/api';

function mensajeDeError(error, fallback) {
  if (!error.response) {
    return 'No se pudo conectar con el servidor. Verifica que el backend esté corriendo.';
  }
  const detalle = error.response.data?.detail;
  if (Array.isArray(detalle)) return detalle.map((d) => d.msg).join(' · ');
  if (typeof detalle === 'string') return detalle;
  return fallback || `Error ${error.response.status}.`;
}

const ALIMENTOS_SOPORTADOS = [
  'Banano', 'Manzana', 'Naranja', 'Tomate', 'Pepino', 'Pimentón', 'Papa',
];

function DisclaimerModelo() {
  const [expandido, setExpandido] = useState(false);
  return (
    <View style={styles.disclaimer}>
      <View style={styles.disclaimerHeader}>
        <Text style={styles.disclaimerTitulo}>⚠️  Limitaciones del modelo</Text>
        <TouchableOpacity onPress={() => setExpandido((v) => !v)}>
          <Text style={styles.disclaimerToggle}>{expandido ? 'Ocultar ▲' : 'Ver más ▼'}</Text>
        </TouchableOpacity>
      </View>
      <Text style={styles.disclaimerTexto}>
        Este modelo <Text style={styles.disclaimerBold}>no tiene precisión del 100%</Text> y puede cometer errores. Verifica siempre el resultado antes de guardarlo.
      </Text>
      {expandido && (
        <>
          <Text style={[styles.disclaimerTexto, { marginTop: 8 }]}>
            Actualmente reconoce <Text style={styles.disclaimerBold}>{ALIMENTOS_SOPORTADOS.length} alimentos</Text>. Si el tuyo no aparece aquí, el resultado puede ser incorrecto:
          </Text>
          <View style={styles.chipGrid}>
            {ALIMENTOS_SOPORTADOS.map((a) => (
              <View key={a} style={styles.chip}>
                <Text style={styles.chipTexto}>{a}</Text>
              </View>
            ))}
          </View>
        </>
      )}
    </View>
  );
}

export default function EscanearAlimentoScreen({ navigation }) {
  const [imagen, setImagen] = useState(null);
  const [resultado, setResultado] = useState(null);
  const [procesando, setProcesando] = useState(false);
  const [error, setError] = useState(null);

  useFocusEffect(
    useCallback(() => {
      if (Platform.OS === 'web') document.title = 'Escanear Alimento · FreshTrack';
    }, [])
  );

  const reiniciar = () => {
    setImagen(null);
    setResultado(null);
    setError(null);
  };

  const tomarFoto = async () => {
    reiniciar();
    try {
      const permiso = await ImagePicker.requestCameraPermissionsAsync();
      if (!permiso.granted) {
        setError('Necesitamos acceso a tu cámara para identificar el alimento.');
        return;
      }
      const seleccion = await ImagePicker.launchCameraAsync({ quality: 0.8 });
      if (!seleccion.canceled) setImagen(seleccion.assets[0].uri);
    } catch {
      setError('No se pudo abrir la cámara. Prueba con "Elegir de galería".');
    }
  };

  const elegirImagen = async () => {
    reiniciar();
    try {
      const permiso = await ImagePicker.requestMediaLibraryPermissionsAsync();
      if (!permiso.granted) {
        setError('Necesitamos acceso a tus fotos para identificar el alimento.');
        return;
      }
      const seleccion = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ImagePicker.MediaTypeOptions.Images,
        quality: 0.8,
      });
      if (!seleccion.canceled) setImagen(seleccion.assets[0].uri);
    } catch {
      setError('No se pudo abrir la galería.');
    }
  };

  const identificarAlimento = async () => {
    if (!imagen) return;
    setError(null);
    setProcesando(true);
    try {
      const formData = new FormData();
      if (Platform.OS === 'web') {
        const respuesta = await fetch(imagen);
        formData.append('archivo', await respuesta.blob(), 'alimento.jpg');
      } else {
        formData.append('archivo', { uri: imagen, name: 'alimento.jpg', type: 'image/jpeg' });
      }
      const { data } = await api.post('/api/v1/camara/identificar', formData);
      setResultado(data);
    } catch (err) {
      setError(mensajeDeError(err, 'No se pudo identificar el alimento.'));
    } finally {
      setProcesando(false);
    }
  };

  const registrarManualmente = () => {
    navigation.navigate('Agregar', { nombre: resultado?.nombre || '' });
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={{ paddingBottom: 24 }}>
      <Text variant="headlineMedium" style={styles.title}>
        Identificar alimento con Visión Artificial
      </Text>
      <Text style={styles.subtitle}>
        Apunta a una fruta o verdura completa, con buena luz y sin objetos que la tapen.
      </Text>

      <DisclaimerModelo />

      {error ? <Text style={styles.error}>{error}</Text> : null}

      {imagen ? (
        <Image source={{ uri: imagen }} style={styles.preview} />
      ) : (
        <View style={styles.placeholder}>
          <Text style={styles.placeholderText}>Aún no has tomado una foto</Text>
        </View>
      )}

      <Button mode="contained" icon="camera" onPress={tomarFoto} style={styles.button} disabled={procesando}>
        Tomar foto
      </Button>
      <Button mode="outlined" icon="image" onPress={elegirImagen} style={styles.button} disabled={procesando}>
        Elegir de galería
      </Button>
      <Button mode="outlined" icon="camera-retake" onPress={reiniciar} style={styles.button} disabled={procesando}>
        Tomar nueva foto
      </Button>

      {imagen && !resultado ? (
        <Button
          mode="contained"
          onPress={identificarAlimento}
          style={styles.button}
          loading={procesando}
          disabled={procesando}
        >
          {procesando ? 'Identificando...' : 'Identificar alimento'}
        </Button>
      ) : null}

      {resultado ? (
        <View style={styles.resultCard}>
          <Text variant="titleLarge">{resultado.nombre || 'Alimento no reconocido'}</Text>
          {resultado.estado ? <Text style={styles.resultState}>Estado: {resultado.estado}</Text> : null}
          <Text style={styles.resultConfidence}>
            Confianza: {Math.round(resultado.confianza * 100)}%
          </Text>
          <Text style={styles.resultMessage}>{resultado.mensaje}</Text>
          {resultado.repetir ? (
            <Button mode="contained" icon="camera-retake" onPress={reiniciar} style={styles.button}>
              Repetir foto
            </Button>
          ) : null}
          {!resultado.aceptado ? (
            <Button mode="outlined" icon="plus" onPress={registrarManualmente} style={styles.button}>
              Registrar manualmente
            </Button>
          ) : null}
        </View>
      ) : null}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F5F7F5' },
  title: { marginBottom: 8, paddingHorizontal: 24, paddingTop: 24 },
  subtitle: { color: '#666', marginBottom: 16, paddingHorizontal: 24 },
  disclaimer: {
    backgroundColor: '#FFF3E0', borderLeftWidth: 4, borderLeftColor: '#E65100',
    borderRadius: 10, marginHorizontal: 24, marginBottom: 20, padding: 14,
  },
  disclaimerHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 },
  disclaimerTitulo: { fontWeight: 'bold', color: '#BF360C', fontSize: 13 },
  disclaimerToggle: { color: '#E65100', fontSize: 12, fontWeight: '600' },
  disclaimerTexto: { color: '#4E2600', fontSize: 13, lineHeight: 19 },
  disclaimerBold: { fontWeight: 'bold' },
  chipGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 6, marginTop: 10 },
  chip: { backgroundColor: '#FFE0B2', borderRadius: 20, paddingHorizontal: 10, paddingVertical: 4 },
  chipTexto: { color: '#4E2600', fontSize: 12 },
  placeholder: {
    width: '90%',
    alignSelf: 'center',
    height: 220,
    backgroundColor: '#EEE',
    justifyContent: 'center',
    alignItems: 'center',
    borderRadius: 12,
    marginBottom: 24,
  },
  placeholderText: { color: '#888' },
  preview: {
    width: '90%',
    alignSelf: 'center',
    height: 220,
    borderRadius: 12,
    marginBottom: 24,
    resizeMode: 'cover',
  },
  button: { marginHorizontal: 24, marginBottom: 12 },
  error: {
    color: '#b3261e',
    backgroundColor: '#fdecea',
    padding: 10,
    borderRadius: 8,
    marginHorizontal: 24,
    marginBottom: 12,
    textAlign: 'center',
  },
  resultCard: {
    backgroundColor: '#FFF',
    borderRadius: 12,
    padding: 16,
    marginHorizontal: 24,
    marginTop: 8,
    elevation: 1,
  },
  resultState: { color: '#2E7D32', fontSize: 18, marginTop: 8, textTransform: 'capitalize' },
  resultConfidence: { marginTop: 8, fontWeight: '600' },
  resultMessage: { color: '#666', marginTop: 8, marginBottom: 8 },
});
