import { useState, useCallback } from 'react';
import { View, StyleSheet, Image, Platform, ScrollView } from 'react-native';
import { Text, Button, TextInput, IconButton, SegmentedButtons } from 'react-native-paper';
import * as ImagePicker from 'expo-image-picker';
import { useFocusEffect } from '@react-navigation/native';
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

export default function EscanearScreen() {
  const [imagen, setImagen] = useState(null);
  const [procesando, setProcesando] = useState(false);
  const [idEscaneo, setIdEscaneo] = useState(null);
  const [lineas, setLineas] = useState([]);
  const [confirmando, setConfirmando] = useState(false);
  const [aviso, setAviso] = useState(null);
  const [error, setError] = useState(null);
  const [exito, setExito] = useState(null);

  useFocusEffect(
    useCallback(() => {
      if (Platform.OS === 'web') document.title = 'Escanear · FreshTrack';
    }, [])
  );

  const limpiarMensajes = () => { setAviso(null); setError(null); setExito(null); };

  const reiniciar = () => {
    setImagen(null);
    setIdEscaneo(null);
    setLineas([]);
    limpiarMensajes();
  };

  const seleccionarImagen = async () => {
    limpiarMensajes();
    const permiso = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (!permiso.granted) {
      setError('Necesitamos acceso a tus fotos para escanear la factura.');
      return;
    }
    const resultado = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      quality: 0.8,
    });
    if (!resultado.canceled) setImagen(resultado.assets[0].uri);
  };

  const tomarFoto = async () => {
    limpiarMensajes();
    try {
      const permiso = await ImagePicker.requestCameraPermissionsAsync();
      if (!permiso.granted) {
        setError('Necesitamos acceso a tu cámara para escanear la factura.');
        return;
      }
      const resultado = await ImagePicker.launchCameraAsync({ quality: 0.8 });
      if (!resultado.canceled) setImagen(resultado.assets[0].uri);
    } catch (err) {
      setError('No se pudo abrir la cámara. Prueba con "Elegir de galería".');
    }
  };

  const enviarFactura = async () => {
    if (!imagen) return;
    limpiarMensajes();
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

      if (data.advertencia) setAviso(data.advertencia);

      if (!data.productos || data.productos.length === 0) {
        setError('No se detectaron productos en la factura. Intenta con otra foto o agrégalos manualmente.');
        setImagen(null);
        return;
      }

      setIdEscaneo(data.id_escaneo);
      setLineas(
        data.productos.map((p) => ({
          id_linea: p.numero_linea,
          nombre: p.nombre_sugerido || p.texto_crudo,
          cantidad: String(p.cantidad),
          unidad: p.unidad,
          condicion: 'fuera',
          id_alimento: p.id_alimento_sugerido,
        }))
      );

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
    } catch (err) {
      setError(mensajeDeError(err, 'No se pudo procesar la factura.'));
    } finally {
      setProcesando(false);
    }
  };

  const actualizarLinea = (idLinea, campo, valor) => {
    setLineas((prev) =>
      prev.map((l) => (l.id_linea === idLinea ? { ...l, [campo]: valor } : l))
    );
  };

  const esLineaNueva = (idLinea) => typeof idLinea === 'string' && idLinea.startsWith('nueva-');

  const agregarLineaManual = () => {
    limpiarMensajes();
    setLineas((prev) => [
      ...prev,
      {
        id_linea: `nueva-${Date.now()}`,
        nombre: '',
        cantidad: '1',
        unidad: 'UND',
        condicion: 'fuera',
        id_alimento: null,
      },
    ]);
  };

  const eliminarLinea = async (idLinea) => {
    limpiarMensajes();
    if (esLineaNueva(idLinea)) {
      setLineas((prev) => prev.filter((l) => l.id_linea !== idLinea));
      return;
    }
    try {
      await api.delete(`/api/v1/escaneos/${idEscaneo}/lineas/${idLinea}`);
      setLineas((prev) => prev.filter((l) => l.id_linea !== idLinea));
    } catch (err) {
      setError('No se pudo eliminar esa línea.');
    }
  };

  const confirmarProductos = async () => {
    limpiarMensajes();
    if (lineas.length === 0) {
      setError('No quedan productos en la lista.');
      return;
    }
    const lineasSinNombre = lineas.filter((l) => !l.nombre.trim());
    if (lineasSinNombre.length > 0) {
      setError('Todos los productos deben tener un nombre.');
      return;
    }
    setConfirmando(true);
    try {
      const payload = {
        lineas: lineas.map((l) => ({
          id_alimento: l.id_alimento || null,
          nombre: l.nombre.trim(),
          cantidad: parseFloat(l.cantidad) || 1,
          unidad: l.unidad || 'UND',
          condicion: l.condicion,
        })),
      };
      const { data } = await api.post(`/api/v1/escaneos/${idEscaneo}/confirmar`, payload);
      setExito(`Se agregaron ${data.items_creados} productos a tu inventario.`);
      setIdEscaneo(null);
      setLineas([]);
      setImagen(null);
    } catch (err) {
      setError(mensajeDeError(err, 'No se pudo confirmar la lista.'));
    } finally {
      setConfirmando(false);
    }
  };

  if (!idEscaneo) {
    return (
      <ScrollView style={styles.container} contentContainerStyle={{ paddingBottom: 24 }}>
        <Text variant="headlineMedium" style={styles.title}>Escanear factura</Text>

        {aviso ? <Text style={styles.aviso}>{aviso}</Text> : null}
        {error ? <Text style={styles.error}>{error}</Text> : null}
        {exito ? <Text style={styles.exito}>{exito}</Text> : null}

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
      </ScrollView>
    );
  }

  return (
    <ScrollView style={styles.container} contentContainerStyle={{ padding: 16 }}>
      <Text variant="headlineMedium" style={styles.title}>Revisa tus productos</Text>
      <Text style={styles.subtitle}>Corrige nombre o cantidad, elimina lo que no sirva o agrega uno que faltó.</Text>

      {aviso ? <Text style={styles.aviso}>{aviso}</Text> : null}
      {error ? <Text style={styles.error}>{error}</Text> : null}

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

      <Button mode="outlined" icon="plus" onPress={agregarLineaManual} style={styles.button}>
        Agregar producto manualmente
      </Button>

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
  error: { color: '#b3261e', backgroundColor: '#fdecea', padding: 10, borderRadius: 8, marginHorizontal: 24, marginBottom: 12, textAlign: 'center' },
  aviso: { color: '#5a3d00', backgroundColor: '#FFF4E5', padding: 10, borderRadius: 8, marginHorizontal: 24, marginBottom: 12, textAlign: 'center' },
  exito: { color: '#1B5E20', backgroundColor: '#E8F5E9', padding: 10, borderRadius: 8, marginHorizontal: 24, marginBottom: 12, textAlign: 'center' },
});
