import { useState, useCallback } from 'react';
import { View, StyleSheet, Alert, Platform, ScrollView } from 'react-native';
import { Text, TextInput, Button, ActivityIndicator, Divider } from 'react-native-paper';
import { useFocusEffect, useNavigation } from '@react-navigation/native';
import { api } from '../services/api';

export default function CuentaScreen() {
  const navigation = useNavigation();
  const [cargando, setCargando] = useState(true);
  const [correo, setCorreo] = useState('');
  const [nombre, setNombre] = useState('');
  const [editando, setEditando] = useState(false);
  const [guardando, setGuardando] = useState(false);

  const [passwordActual, setPasswordActual] = useState('');
  const [nuevaPassword, setNuevaPassword] = useState('');
  const [cambiandoPassword, setCambiandoPassword] = useState(false);

  const [cerrando, setCerrando] = useState(false);

  useFocusEffect(
    useCallback(() => {
      if (Platform.OS === 'web') document.title = 'Mi cuenta · FreshTrack';
      cargarCuenta();
    }, [])
  );

  const cargarCuenta = async () => {
    setCargando(true);
    try {
      const { data } = await api.get('/api/v1/auth/me');
      setCorreo(data.correo);
      setNombre(data.nombre);
    } catch (error) {
      // si falla, se queda vacío
    } finally {
      setCargando(false);
    }
  };

  const guardarNombre = async () => {
    if (!nombre.trim()) {
      Alert.alert('Nombre inválido', 'El nombre no puede quedar vacío.');
      return;
    }
    setGuardando(true);
    try {
      await api.patch('/api/v1/auth/me', { nombre: nombre.trim() });
      Alert.alert('Listo', 'Tu nombre se actualizó.');
      setEditando(false);
    } catch (error) {
      Alert.alert('Error', error.response?.data?.detail || 'No se pudo actualizar.');
    } finally {
      setGuardando(false);
    }
  };

  const cambiarPassword = async () => {
    if (!passwordActual || !nuevaPassword) {
      Alert.alert('Campos incompletos', 'Ingresa tu contraseña actual y la nueva.');
      return;
    }
    setCambiandoPassword(true);
    try {
      await api.patch('/api/v1/auth/me', {
        password_actual: passwordActual,
        nueva_password: nuevaPassword,
      });
      Alert.alert('Listo', 'Tu contraseña se actualizó.');
      setPasswordActual('');
      setNuevaPassword('');
    } catch (error) {
      Alert.alert('Error', error.response?.data?.detail || 'No se pudo cambiar la contraseña.');
    } finally {
      setCambiandoPassword(false);
    }
  };

  const cerrarSesion = async () => {
    setCerrando(true);
    try {
      await api.post('/api/v1/auth/logout');
    } catch (error) {
      // igual sacamos al usuario aunque falle la llamada
    } finally {
      setCerrando(false);
      navigation.getParent()?.reset({ index: 0, routes: [{ name: 'Login' }] });
    }
  };

  if (cargando) return <ActivityIndicator style={{ flex: 1 }} size="large" />;

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Text variant="headlineMedium" style={styles.title}>Mi cuenta</Text>

      <View style={styles.card}>
        <Text style={styles.etiqueta}>Correo electrónico</Text>
        <Text variant="titleMedium" style={styles.valorFijo}>{correo}</Text>

        <Text style={[styles.etiqueta, { marginTop: 16 }]}>Nombre</Text>
        {editando ? (
          <>
            <TextInput mode="outlined" value={nombre} onChangeText={setNombre} style={styles.input} />
            <View style={styles.filaBotones}>
              <Button mode="contained" onPress={guardarNombre} loading={guardando} disabled={guardando} style={{ flex: 1, marginRight: 8 }}>
                Guardar
              </Button>
              <Button mode="outlined" onPress={() => setEditando(false)} style={{ flex: 1 }}>
                Cancelar
              </Button>
            </View>
          </>
        ) : (
          <View style={styles.filaValor}>
            <Text variant="titleMedium">{nombre}</Text>
            <Button compact onPress={() => setEditando(true)}>Editar</Button>
          </View>
        )}
      </View>

      <Divider style={{ marginVertical: 20 }} />

      <View style={styles.card}>
        <Text variant="titleMedium" style={{ marginBottom: 12 }}>Cambiar contraseña</Text>
        <TextInput
          mode="outlined"
          label="Contraseña actual"
          value={passwordActual}
          onChangeText={setPasswordActual}
          secureTextEntry
          style={styles.input}
        />
        <TextInput
          mode="outlined"
          label="Nueva contraseña (mín. 8 caracteres)"
          value={nuevaPassword}
          onChangeText={setNuevaPassword}
          secureTextEntry
          style={styles.input}
        />
        <Button
          mode="contained"
          onPress={cambiarPassword}
          loading={cambiandoPassword}
          disabled={cambiandoPassword}
          style={{ marginTop: 4 }}
        >
          Actualizar contraseña
        </Button>
      </View>

      <Button
        mode="contained"
        buttonColor="#C62828"
        onPress={cerrarSesion}
        loading={cerrando}
        disabled={cerrando}
        style={styles.cerrarBoton}
      >
        Cerrar sesión
      </Button>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F5F7F5' },
  content: { padding: 24 },
  title: { marginBottom: 20 },
  card: { backgroundColor: '#FFF', borderRadius: 12, padding: 16 },
  etiqueta: { fontSize: 13, color: '#666' },
  valorFijo: { marginTop: 2 },
  input: { marginTop: 8, marginBottom: 4, backgroundColor: '#FFF' },
  filaValor: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  filaBotones: { flexDirection: 'row', marginTop: 8 },
  cerrarBoton: { marginTop: 24 },
});