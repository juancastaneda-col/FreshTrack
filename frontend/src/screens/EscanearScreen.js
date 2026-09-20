import { useState, useCallback } from 'react';
import { View, StyleSheet, Image, Alert, Platform, ScrollView } from 'react-native';
import { Text, Button, TextInput, IconButton, SegmentedButtons } from 'react-native-paper';
import * as ImagePicker from 'expo-image-picker';
import { useFocusEffect } from '@react-navigation/native';
import { api } from '../services/api';

export default function EscanearScreen() {
  const [imagen, setImagen] = useState(null);
  const [procesando, setProcesando] = useState(false);
  const [idEscaneo, setIdEscaneo] = useState(null);
  const [lineas, setLineas] = useState([]);
  const [confirmando, setConfirmando] = useState(false);

  useFocusEffect(
    useCallback(() => {
      if (Platform.OS === 'web') document.title = 'Escanear · FreshTrack';
    }, [])
  );

  const reiniciar = () => {
    setImagen(null);
    setIdEscaneo(null);
    setLineas([]);
  };

  const seleccionarImagen = async () => {
    const permiso = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (!permiso.granted) {
      Alert.alert('Permiso necesario', 'Necesitamos acceso a tus fotos para escanear la factura.');
      return;
    }
    const resultado = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      quality: 0.8,
    });
    if (!resultado.canceled) setImagen(resultado.assets[0].uri);
  };

  const tomarFoto = async () => {
    try {
      const permiso = await ImagePicker.requestCameraPermissionsAsync();
      if (!permiso.granted) {
        Alert.alert('Permiso necesario', 'Necesitamos acceso a tu cámara para escanear la factura.');
        return;
      }
      const resultado = await ImagePicker.launchCameraAsync({ quality: 0.8 });
      if (!resultado.canceled) setImagen(resultado.assets[0].uri);
    } catch (error) {
      Alert.alert('No se pudo abrir la cámara', 'Prueba con "Elegir de galería" o desde tu celular.');
    }
  };

  const enviarFactura = async () => {
    if (!imagen) return;
    setProcesando(true);
    try {
      const formData = new FormData();
      if (Platform.OS === 'web') {
        const respuesta = await fetch(imagen);
        const blob = await respuesta.blob();
        formData.append('archivo', blob, 'factura.jpg');
      } else {
        formData.append('archivo', { uri: imagen, name: 'factura.jpg', type: 'image/jpeg' });
      }

      const { data } = await api.post('/api/v1/facturas/escanear', formData);

      if (data.advertencia) Alert.alert('Aviso', data.advertencia);

      if (!data.productos || data.productos.length === 0) {
        Alert.alert('Sin productos', 'No se detectaron productos en la factura.');
        reiniciar();
        return;
      }

      setIdEscaneo(data.id_escaneo);
      setLineas(
        data.productos.map((p) => ({
          id_linea: p.numero_linea, // se reemplaza abajo con el id real
          nombre: p.nombre_sugerido || p.texto_crudo,
          cantidad: String(p.cantidad),
          unidad: p.unidad,
          condicion: 'fuera',
          id_alimento: p.id_alimento_sugerido,
        }))
      );

      // Pedimos los ids reales de línea (el POST no los devuelve, pero el detalle del escaneo sí)
      const detalle = await api.get(`/api/v1/escaneos/${data.id_escaneo}`);
      setLineas(
        detalle.data.lineas.map((l) => ({
          id_linea: l.id_linea,
          nombre: l.nombre,
          cantidad: String(l.cantidad),
          unidad: l.unidad,
          condicion: l.condicion,
          id_alimento: l.id_alimento_sugerido,
        }))
      );
    } catch (error) {
      Alert.alert('Error', error.response?.data?.detail || 'No se pudo procesar la factura.');
    } finally {
      setProcesando(false);
    }
  };

  const actualizarLinea = (idLinea, campo, valor) => {
    setLineas((prev) =>
      prev.map((l) => (l.id_linea === idLinea ? { ...l, [campo]: valor } : l))
    );
  };

  const eliminarLinea = async (idLinea) => {
    try {
      await api.delete(`/api/v1/escaneos/${idEscaneo}/lineas/${idLinea}`);
      setLineas((prev) => prev.filter((l) => l.id_linea !== idLinea));
    } catch (error) {
      Alert.alert('Error', 'No se pudo eliminar esa línea.');
    }
  };

  const confirmarProductos = async () => {
    if (lineas.length === 0) {
      Alert.alert('Nada que confirmar', 'No quedan productos en la lista.');
      return;
    }
    setConfirmando(true);
    try {
      const payload = {
        lineas: lineas.map((l) => ({
          id_alimento: l.id_alimento || null,
          nombre: l.nombre,
          cantidad: parseFloat(l.cantidad) || 1,
          unidad: l.unidad || 'UND',
          condicion: l.condicion,
        })),
      };
      const { data } = await api.post(`/api/v1/escaneos/${idEscaneo}/confirmar`, payload);
      Alert.alert('¡Listo!', `Se agregaron ${data.items_creados} productos a tu inventario.`);
      reiniciar();
    } catch (error) {
      Alert.alert('Error', error.response?.data?.detail || 'No se pudo confirmar la lista.');
    } finally {
      setConfirmando(false);
    }
  };

  // --- Vista 1: subir imagen ---
  if (!idEscaneo) {
    return (
      <View style={styles.container}>
        <Text variant="headlineMedium" style={styles.title}>Escanear factura</Text>

        {imagen ? (
          <Image source={{ uri: imagen }} style={styles.preview} />
        ) : (
          <View style={styles.placeholder}>
            <Text style={styles.placeholderText}>Aún no has seleccionado una imagen</Text>
          </View>
        )}

        <Button mode="contained" icon="camera" onPress={tomarFoto} style={styles.button} disabled={procesando}>
          Tomar foto
        </Button>
        <Button mode="outlined" icon="image" onPress={seleccionarImagen} style={styles.button} disabled={procesando}>
          Elegir de galería
        </Button>

        {imagen && (
          <Button
            mode="contained"
            buttonColor="#2E7D32"
            onPress={enviarFactura}
            style={styles.button}
            loading={procesando}
            disabled={procesando}
          >
            {procesando ? 'Procesando...' : 'Enviar factura'}
          </Button>
        )}
      </View>
    );
  }

  // --- Vista 2: revisar y confirmar productos detectados ---
  return (
    <ScrollView style={styles.container} contentContainerStyle={{ padding: 16 }}>
      <Text variant="headlineMedium" style={styles.title}>Revisa tus productos</Text>
      <Text style={styles.subtitle}>Corrige nombre o cantidad, o elimina lo que no sirva.</Text>

      {lineas.map((linea) => (
        <View key={linea.id_linea} style={styles.lineaCard}>
          <View style={styles.lineaHeader}>
            <TextInput
              mode="outlined"
              label="Producto"
              value={linea.nombre}
              onChangeText={(v) => actualizarLinea(linea.id_linea, 'nombre', v)}
              style={{ flex: 1 }}
              dense
            />
            <IconButton icon="delete-outline" onPress={() => eliminarLinea(linea.id_linea)} />
          </View>
          <View style={styles.lineaRow}>
            <TextInput
              mode="outlined"
              label="Cantidad"
              value={linea.cantidad}
              onChangeText={(v) => actualizarLinea(linea.id_linea, 'cantidad', v)}
              keyboardType="numeric"
              style={{ flex: 1, marginRight: 8 }}
              dense
            />
            <TextInput
              mode="outlined"
              label="Unidad"
              value={linea.unidad}
              onChangeText={(v) => actualizarLinea(linea.id_linea, 'unidad', v)}
              style={{ flex: 1 }}
              dense
            />
          </View>
          <SegmentedButtons
            value={linea.condicion}
            onValueChange={(v) => actualizarLinea(linea.id_linea, 'condicion', v)}
            style={{ marginTop: 8 }}
            buttons={[
              { value: 'fuera', label: 'Fuera de nevera' },
              { value: 'nevera', label: 'Nevera' },
            ]}
          />
        </View>
      ))}

      <Button mode="outlined" onPress={reiniciar} style={styles.button}>
        Cancelar y volver a empezar
      </Button>
      <Button
        mode="contained"
        buttonColor="#2E7D32"
        onPress={confirmarProductos}
        style={styles.button}
        loading={confirmando}
        disabled={confirmando}
      >
        {confirmando ? 'Guardando...' : 'Confirmar productos'}
      </Button>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F5F7F5' },
  title: { marginBottom: 8, paddingHorizontal: 24, paddingTop: 24 },
  subtitle: { color: '#666', marginBottom: 16, paddingHorizontal: 24 },
  placeholder: {
    width: '90%', alignSelf: 'center', height: 220, backgroundColor: '#EEE',
    justifyContent: 'center', alignItems: 'center',
    borderRadius: 12, marginBottom: 24,
  },
  placeholderText: { color: '#888' },
  preview: { width: '90%', alignSelf: 'center', height: 220, borderRadius: 12, marginBottom: 24, resizeMode: 'cover' },
  button: { marginHorizontal: 24, marginBottom: 12 },
  lineaCard: {
    backgroundColor: '#FFF', borderRadius: 12, padding: 12, marginBottom: 12,
    elevation: 1,
  },
  lineaHeader: { flexDirection: 'row', alignItems: 'center' },
  lineaRow: { flexDirection: 'row', marginTop: 8 },
});