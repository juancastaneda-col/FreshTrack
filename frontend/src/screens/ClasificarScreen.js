import { useState, useCallback } from 'react';
import { View, StyleSheet, Image, ScrollView, Platform } from 'react-native';
import { Text, Button } from 'react-native-paper';
import * as ImagePicker from 'expo-image-picker';
import { useFocusEffect } from '@react-navigation/native';
import { api } from '../services/api';

const ESTADO_COLOR = {
  fresco: { fondo: '#E8F5E9', texto: '#1B5E20', etiqueta: 'Fresco' },
  danado: { fondo: '#FFEBEE', texto: '#B71C1C', etiqueta: 'Dañado' },
};

function mensajeDeError(error) {
  if (!error.response) return 'No se pudo conectar con el servidor.';
  const d = error.response.data?.detail;
  if (typeof d === 'string') return d;
  return `Error ${error.response.status}.`;
}

export default function ClasificarScreen() {
  const [imagen, setImagen] = useState(null);
  const [analizando, setAnalizando] = useState(false);
  const [resultado, setResultado] = useState(null);
  const [error, setError] = useState(null);

  useFocusEffect(
    useCallback(() => {
      if (Platform.OS === 'web') document.title = 'Clasificar · FreshTrack';
    }, [])
  );

  const reiniciar = () => {
    setImagen(null);
    setResultado(null);
    setError(null);
  };

  const seleccionarImagen = async () => {
    setError(null);
    const permiso = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (!permiso.granted) { setError('Necesitamos acceso a tus fotos.'); return; }
    const r = await ImagePicker.launchImageLibraryAsync({ mediaTypes: ImagePicker.MediaTypeOptions.Images, quality: 0.8 });
    if (!r.canceled) { setImagen(r.assets[0].uri); setResultado(null); }
  };

  const tomarFoto = async () => {
    setError(null);
    try {
      const permiso = await ImagePicker.requestCameraPermissionsAsync();
      if (!permiso.granted) { setError('Necesitamos acceso a tu cámara.'); return; }
      const r = await ImagePicker.launchCameraAsync({ quality: 0.8 });
      if (!r.canceled) { setImagen(r.assets[0].uri); setResultado(null); }
    } catch {
      setError('No se pudo abrir la cámara. Prueba con la galería.');
    }
  };

  const analizar = async () => {
    if (!imagen) return;
    setError(null);
    setAnalizando(true);
    try {
      const formData = new FormData();
      if (Platform.OS === 'web') {
        const resp = await fetch(imagen);
        const blob = await resp.blob();
        formData.append('archivo', blob, 'alimento.jpg');
      } else {
        formData.append('archivo', { uri: imagen, name: 'alimento.jpg', type: 'image/jpeg' });
      }
      const { data } = await api.post('/api/v1/alimentos/clasificar', formData);
      setResultado(data);
    } catch (err) {
      setError(mensajeDeError(err));
    } finally {
      setAnalizando(false);
    }
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={{ paddingBottom: 32 }}>
      <Text variant="headlineMedium" style={styles.title}>Verificar alimento</Text>
      <Text style={styles.subtitle}>
        Toma una foto de una fruta o verdura para saber si está fresca o dañada.
      </Text>

      {error ? <Text style={styles.error}>{error}</Text> : null}

      {imagen ? (
        <Image source={{ uri: imagen }} style={styles.preview} />
      ) : (
        <View style={styles.placeholder}>
          <Text style={styles.placeholderText}>Sin imagen seleccionada</Text>
        </View>
      )}

      {resultado && !resultado.no_reconocido && (
        <View style={[styles.resultado, { backgroundColor: ESTADO_COLOR[resultado.estado]?.fondo ?? '#F5F5F5' }]}>
          <Text variant="headlineSmall" style={[styles.resultadoNombre, { color: ESTADO_COLOR[resultado.estado]?.texto ?? '#333' }]}>
            {resultado.nombre}
          </Text>
          <Text variant="titleMedium" style={[styles.resultadoEstado, { color: ESTADO_COLOR[resultado.estado]?.texto ?? '#333' }]}>
            {ESTADO_COLOR[resultado.estado]?.etiqueta ?? resultado.estado}
          </Text>
          <Text style={styles.resultadoConfianza}>
            Confianza: {Math.round(resultado.confianza * 100)}%
          </Text>
        </View>
      )}

      {resultado && resultado.no_reconocido && (
        <View style={styles.noReconocido}>
          <Text style={styles.noReconocidoText}>
            No se reconoció el alimento. Intenta con una foto más clara o con mejor iluminación.
          </Text>
        </View>
      )}

      <Button mode="contained" icon="camera" onPress={tomarFoto} style={styles.btn} disabled={analizando}>
        Tomar foto
      </Button>
      <Button mode="outlined" icon="image" onPress={seleccionarImagen} style={styles.btn} disabled={analizando}>
        Elegir de galería
      </Button>

      {imagen && !resultado && (
        <Button
          mode="contained"
          buttonColor="#2E7D32"
          icon="leaf"
          onPress={analizar}
          style={styles.btn}
          loading={analizando}
          disabled={analizando}
        >
          {analizando ? 'Analizando...' : 'Analizar alimento'}
        </Button>
      )}

      {resultado && (
        <Button mode="outlined" onPress={reiniciar} style={styles.btn}>
          Analizar otro alimento
        </Button>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F5F7F5' },
  title: { paddingHorizontal: 24, paddingTop: 24, marginBottom: 4 },
  subtitle: { color: '#666', paddingHorizontal: 24, marginBottom: 20 },
  placeholder: {
    width: '90%', alignSelf: 'center', height: 240, backgroundColor: '#EEE',
    justifyContent: 'center', alignItems: 'center', borderRadius: 16, marginBottom: 20,
  },
  placeholderText: { color: '#888' },
  preview: { width: '90%', alignSelf: 'center', height: 240, borderRadius: 16, marginBottom: 20, resizeMode: 'cover' },
  resultado: {
    marginHorizontal: 24, borderRadius: 16, padding: 20, marginBottom: 20, alignItems: 'center',
  },
  resultadoNombre: { fontWeight: 'bold', marginBottom: 4 },
  resultadoEstado: { marginBottom: 8 },
  resultadoConfianza: { color: '#555', fontSize: 13 },
  noReconocido: {
    marginHorizontal: 24, borderRadius: 16, padding: 16, marginBottom: 20,
    backgroundColor: '#FFF8E1',
  },
  noReconocidoText: { color: '#5D4037', textAlign: 'center' },
  error: {
    color: '#b3261e', backgroundColor: '#fdecea', padding: 10, borderRadius: 8,
    marginHorizontal: 24, marginBottom: 12, textAlign: 'center',
  },
  btn: { marginHorizontal: 24, marginBottom: 12 },
});
