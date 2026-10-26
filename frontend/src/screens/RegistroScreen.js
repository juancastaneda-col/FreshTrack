import { useState } from 'react';
import { View, Text, StyleSheet, ImageBackground, ScrollView, ActivityIndicator } from 'react-native';
import { TextInput, Button } from 'react-native-paper';
import { api } from '../services/api';
import { colores, fuentes, sombras } from '../theme/theme';
import { mensajeDeError } from '../utils/errores';

export default function RegistroScreen({ navigation }) {
  const [correo, setCorreo] = useState('');
  const [password, setPassword] = useState('');
  const [verPassword, setVerPassword] = useState(false);
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
    <ImageBackground
      source={require('../../assets/images/login-bg.jpg')}
      style={styles.fondo}
      resizeMode="cover"
    >
      <View style={styles.velo} />
      <ScrollView contentContainerStyle={styles.contenido} keyboardShouldPersistTaps="handled">
        <View style={styles.marca}>
          <Text style={styles.emoji}>🥬</Text>
          <Text style={styles.titulo}>Únete a FreshTrack</Text>
          <Text style={styles.lema}>cada alimento cuenta</Text>
        </View>

        <View style={styles.tarjeta}>
          <Text style={styles.saludo}>Crea tu cuenta</Text>
          <Text style={styles.saludoSub}>
            En un minuto empiezas a cuidar tus frutas y verduras.
          </Text>

          <TextInput
            label="Correo electrónico"
            value={correo}
            onChangeText={setCorreo}
            style={styles.input}
            autoCapitalize="none"
            keyboardType="email-address"
            mode="outlined"
            outlineStyle={styles.contornoInput}
            activeOutlineColor={colores.hoja}
            left={<TextInput.Icon icon="email-outline" />}
          />
          <TextInput
            label="Contraseña (mín. 8 caracteres)"
            value={password}
            onChangeText={setPassword}
            secureTextEntry={!verPassword}
            style={styles.input}
            mode="outlined"
            outlineStyle={styles.contornoInput}
            activeOutlineColor={colores.hoja}
            left={<TextInput.Icon icon="lock-outline" />}
            right={
              <TextInput.Icon
                icon={verPassword ? 'eye-off-outline' : 'eye-outline'}
                onPress={() => setVerPassword(!verPassword)}
              />
            }
          />

          {errorMensaje ? <Text style={styles.error}>{errorMensaje}</Text> : null}

          {cargando ? (
            <ActivityIndicator style={styles.boton} color={colores.hoja} />
          ) : (
            <Button
              mode="contained"
              onPress={handleRegistro}
              style={styles.boton}
              contentStyle={styles.botonContenido}
              labelStyle={styles.botonEtiqueta}
              icon="check"
            >
              Crear cuenta
            </Button>
          )}

          <Button
            onPress={() => navigation.goBack()}
            textColor={colores.hoja}
            labelStyle={styles.enlace}
          >
            Ya tengo cuenta, iniciar sesión
          </Button>
        </View>
      </ScrollView>
    </ImageBackground>
  );
}

const styles = StyleSheet.create({
  fondo: { flex: 1, width: '100%', height: '100%' },
  velo: { ...StyleSheet.absoluteFillObject, backgroundColor: 'rgba(8, 55, 28, 0.66)' },
  contenido: { flexGrow: 1, justifyContent: 'center', padding: 24 },
  marca: { alignItems: 'center', marginBottom: 20 },
  emoji: { fontSize: 52, marginBottom: 4 },
  titulo: { fontFamily: fuentes.titulo, fontSize: 34, color: colores.blanco, textAlign: 'center' },
  lema: { fontFamily: fuentes.mano, fontSize: 24, color: colores.mango },
  tarjeta: {
    backgroundColor: colores.blanco,
    borderRadius: 28,
    padding: 22,
    boxShadow: sombras.media,
  },
  saludo: { fontFamily: fuentes.titulo, fontSize: 24, color: colores.selva },
  saludoSub: { fontFamily: fuentes.texto, fontSize: 14, color: colores.suave, marginTop: 2, marginBottom: 16 },
  input: { marginBottom: 12, backgroundColor: colores.blanco, fontFamily: fuentes.texto },
  contornoInput: { borderRadius: 14 },
  error: {
    fontFamily: fuentes.textoMedio,
    color: '#B3261E',
    backgroundColor: '#FDECEA',
    padding: 10,
    borderRadius: 12,
    marginBottom: 8,
    textAlign: 'center',
  },
  boton: { marginTop: 6, marginBottom: 6, borderRadius: 16 },
  botonContenido: { height: 50, flexDirection: 'row-reverse' },
  botonEtiqueta: { fontFamily: fuentes.textoExtra, fontSize: 16 },
  enlace: { fontFamily: fuentes.textoNegrita, fontSize: 14 },
});