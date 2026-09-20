import { useState } from 'react';
import { View, StyleSheet, ImageBackground, ActivityIndicator } from 'react-native';
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

export default function LoginScreen({ navigation }) {
  const [correo, setCorreo] = useState('');
  const [password, setPassword] = useState('');
  const [cargando, setCargando] = useState(false);
  const [errorMensaje, setErrorMensaje] = useState('');

  const handleLogin = async () => {
    setErrorMensaje('');
    if (!correo || !password) {
      setErrorMensaje('Ingresa tu correo y contraseña.');
      return;
    }
    setCargando(true);
    try {
      await api.post('/api/v1/auth/login', { correo, password });
      navigation.replace('Main');
    } catch (error) {
      setErrorMensaje(mensajeDeError(error));
    } finally {
      setCargando(false);
    }
  };

  return (
    <ImageBackground
      source={require('../../assets/images/login-bg.jpg')}
      style={styles.background}
      resizeMode="cover"
    >
      <View style={styles.overlay} />
      <View style={styles.container}>
        <Text variant="headlineLarge" style={styles.title}>FreshTrack</Text>
        <Text style={styles.subtitle}>Controla el vencimiento de tus alimentos</Text>

        <View style={styles.card}>
          <TextInput label="Correo electrónico" value={correo} onChangeText={setCorreo} style={styles.input} autoCapitalize="none" keyboardType="email-address" mode="outlined" />
          <TextInput label="Contraseña" value={password} onChangeText={setPassword} secureTextEntry style={styles.input} mode="outlined" />
          {errorMensaje ? (
            <Text style={styles.error}>{errorMensaje}</Text>
          ) : null}
          {cargando ? (
            <ActivityIndicator style={styles.button} />
          ) : (
            <Button mode="contained" onPress={handleLogin} style={styles.button}>
              Iniciar sesión
            </Button>
          )}
          <Button onPress={() => navigation.navigate('Registro')}>
            ¿No tienes cuenta? Regístrate
          </Button>
        </View>
      </View>
    </ImageBackground>
  );
}

const styles = StyleSheet.create({
  background: { flex: 1, width: '100%', height: '100%' },
  overlay: { ...StyleSheet.absoluteFillObject, backgroundColor: 'rgba(0,0,0,0.35)' },
  container: { flex: 1, justifyContent: 'center', padding: 24 },
  title: { color: '#FFF', textAlign: 'center', fontWeight: 'bold' },
  subtitle: { color: '#FFF', textAlign: 'center', marginBottom: 32, opacity: 0.9 },
  card: { backgroundColor: 'rgba(255,255,255,0.95)', borderRadius: 16, padding: 20 },
  input: { marginBottom: 16, backgroundColor: '#FFF' },
  button: { marginTop: 8, marginBottom: 8 },
  error: { color: '#b3261e', backgroundColor: '#fdecea', padding: 10, borderRadius: 8, marginBottom: 8, textAlign: 'center' },
});