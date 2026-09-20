import { useState } from 'react';
import { View, StyleSheet, Alert } from 'react-native';
import { Text, TextInput, Button } from 'react-native-paper';
import { api } from '../services/api';

export default function RegistroScreen({ navigation }) {
  const [correo, setCorreo] = useState('');
  const [password, setPassword] = useState('');

  const handleRegistro = async () => {
    if (!correo || !password) {
      Alert.alert('Campos incompletos', 'Completa correo y contraseña.');
      return;
    }
    try {
      await api.post('/api/v1/auth/registro', { correo, password });
      Alert.alert('Cuenta creada', 'Ya puedes usar la app.');
      navigation.replace('Main'); // el registro ya inicia sesión automáticamente (deja la cookie puesta)
    } catch (error) {
      const detalle = error.response?.data?.detail || 'No se pudo crear la cuenta.';
      Alert.alert('Error', detalle);
    }
  };

  return (
    <View style={styles.container}>
      <Text variant="headlineMedium" style={styles.title}>Crear cuenta</Text>
      <TextInput label="Correo electrónico" value={correo} onChangeText={setCorreo} style={styles.input} autoCapitalize="none" keyboardType="email-address" />
      <TextInput label="Contraseña (mín. 8 caracteres)" value={password} onChangeText={setPassword} secureTextEntry style={styles.input} />
      <Button mode="contained" onPress={handleRegistro} style={styles.button}>
        Crear cuenta
      </Button>
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
});