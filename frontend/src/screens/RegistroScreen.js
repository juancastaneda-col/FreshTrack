import { useState } from 'react';
import { View, StyleSheet, ActivityIndicator } from 'react-native';
import { Text, TextInput, Button } from 'react-native-paper';
import { api } from '../services/api';

function mensajeDeError(error) {
  if (!error.response) {
    return 'No se pudo conectar con el servidor. Verifica que el backend esté corriendo.';
  }
  const detalle = error.response.data?.detail;
  if (Array.isArray(detalle)) {
    return detalle.map((d) => d.msg).join(' · ');
  }
  if (typeof detalle === 'string') return detalle;
  return `Error ${error.response.status}. Intenta de nuevo.`;
}

export default function RegistroScreen({ navigation }) {
  const [correo, setCorreo] = useState('');
  const [password, setPassword] = useState('');
  const [cargando, setCargando] = useState(false);
  const [errorMensaje, setErrorMensaje] = useState('');

  const handleRegistro = async () => {
    setErrorMensaje('');
    if (!correo || !password) {
      setErrorMensaje('Completa correo y contraseña.');
      return;
    }
    setCargando(true);
    try {
      await api.post('/api/v1/auth/registro', { correo, password });
      navigation.replace('Main');
    } catch (error) {
      setErrorMensaje(mensajeDeError(error));
    } finally {
      setCargando(false);
    }
  };

  return (
    <View style={styles.container}>
      <Text variant="headlineMedium" style={styles.title}>Crear cuenta</Text>
      <TextInput label="Correo electrónico" value={correo} onChangeText={setCorreo} style={styles.input} autoCapitalize="none" keyboardType="email-address" />
      <TextInput label="Contraseña (mín. 8 caracteres)" value={password} onChangeText={setPassword} secureTextEntry style={styles.input} />
      {errorMensaje ? (
        <Text style={styles.error}>{errorMensaje}</Text>
      ) : null}
      {cargando ? (
        <ActivityIndicator style={styles.button} />
      ) : (
        <Button mode="contained" onPress={handleRegistro} style={styles.button}>
          Crear cuenta
        </Button>
      )}
      <Button onPress={() => navigation.goBack()}>
        Ya tengo cuenta, iniciar sesión
      </Button>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, justifyContent: 'center', padding: 24 },
  title: { textAlign: 'center', marginBottom: 32 },
  input: { marginBottom: 16 },
  button: { marginTop: 8, marginBottom: 8 },
  error: { color: '#b3261e', backgroundColor: '#fdecea', padding: 10, borderRadius: 8, marginBottom: 8, textAlign: 'center' },
});