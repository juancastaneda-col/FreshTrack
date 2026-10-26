import { useState, useCallback } from 'react';
import { View, StyleSheet, Platform, ScrollView, Switch } from 'react-native';
import { Text, TextInput, Button, ActivityIndicator, Divider, List } from 'react-native-paper';
import { useFocusEffect, useNavigation } from '@react-navigation/native';
import { api } from '../services/api';
import { avisar } from '../utils/avisar';
import { colores, fuentes, sombras } from '../theme/theme';

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
  const [historial, setHistorial] = useState([]);
  const [cargandoHistorial, setCargandoHistorial] = useState(false);

  const [notifActivas, setNotifActivas] = useState(true);
  const [correoNotif, setCorreoNotif] = useState('');
  const [guardandoNotif, setGuardandoNotif] = useState(false);
  const [enviandoPrueba, setEnviandoPrueba] = useState(false);

  useFocusEffect(
    useCallback(() => {
      if (Platform.OS === 'web') document.title = 'Mi cuenta · FreshTrack';
      cargarCuenta();
      cargarHistorial();
      cargarPreferenciasNotif();
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

  const cargarPreferenciasNotif = async () => {
    try {
      const { data } = await api.get('/api/v1/perfil/notificaciones');
      setNotifActivas(data.notificaciones_activas);
      setCorreoNotif(data.correo_notificaciones || '');
    } catch (_) {}
  };

  const enviarPrueba = async () => {
    setEnviandoPrueba(true);
    try {
      const { data } = await api.post('/api/v1/alertas/prueba');
      avisar('Correo enviado', `Se envió un correo de prueba a ${data.mensaje.replace('Correo de prueba enviado a ', '')}.`);
    } catch (error) {
      avisar('Error', error.response?.data?.detail || 'No se pudo enviar el correo.');
    } finally {
      setEnviandoPrueba(false);
    }
  };

  const guardarNotificaciones = async () => {
    setGuardandoNotif(true);
    try {
      await api.patch('/api/v1/perfil/notificaciones', {
        notificaciones_activas: notifActivas,
        correo_notificaciones: correoNotif.trim() || null,
      });
      avisar('Listo', 'Preferencias de notificación guardadas.');
    } catch (error) {
      avisar('Error', error.response?.data?.detail || 'No se pudo guardar.');
    } finally {
      setGuardandoNotif(false);
    }
  };

  const cargarHistorial = async () => {
    setCargandoHistorial(true);
    try {
      const { data } = await api.get('/api/v1/camara/historial');
      setHistorial(data.identificaciones || []);
    } catch (error) {
      setHistorial([]);
    } finally {
      setCargandoHistorial(false);
    }
  };

  const guardarNombre = async () => {
    if (!nombre.trim()) {
      avisar('Nombre inválido', 'El nombre no puede quedar vacío.');
      return;
    }
    setGuardando(true);
    try {
      await api.patch('/api/v1/auth/me', { nombre: nombre.trim() });
      avisar('Listo', 'Tu nombre se actualizó.');
      setEditando(false);
    } catch (error) {
      avisar('Error', error.response?.data?.detail || 'No se pudo actualizar.');
    } finally {
      setGuardando(false);
    }
  };

  const cambiarPassword = async () => {
    if (!passwordActual || !nuevaPassword) {
      avisar('Campos incompletos', 'Ingresa tu contraseña actual y la nueva.');
      return;
    }
    setCambiandoPassword(true);
    try {
      await api.patch('/api/v1/auth/me', {
        password_actual: passwordActual,
        nueva_password: nuevaPassword,
      });
      avisar('Listo', 'Tu contraseña se actualizó.');
      setPasswordActual('');
      setNuevaPassword('');
    } catch (error) {
      avisar('Error', error.response?.data?.detail || 'No se pudo cambiar la contraseña.');
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
      <View style={styles.perfil}>
        <View style={styles.avatar}>
          <Text style={styles.avatarLetra}>{(nombre || correo || '?').trim().charAt(0).toUpperCase()}</Text>
        </View>
        <View style={{ flex: 1 }}>
          <Text style={styles.perfilNombre} numberOfLines={1}>{nombre || 'Mi cuenta'}</Text>
          <Text style={styles.perfilCorreo} numberOfLines={1}>{correo}</Text>
        </View>
        <Text style={{ fontSize: 30 }}>🥬</Text>
      </View>

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
        <Text variant="titleMedium" style={{ marginBottom: 8 }}>Historial de identificaciones</Text>
        {cargandoHistorial ? <ActivityIndicator /> : null}
        {!cargandoHistorial && historial.length === 0 ? (
          <Text style={styles.historialVacio}>Todavía no has identificado alimentos.</Text>
        ) : null}
        {historial.map((identificacion) => (
          <List.Item
            key={identificacion.id_identificacion}
            title={identificacion.nombre || 'Alimento no reconocido'}
            description={`${identificacion.estado || 'Sin estado'} · ${Math.round(identificacion.confianza * 100)}% · ${new Date(identificacion.creado_en).toLocaleString()}`}
            left={(props) => <List.Icon {...props} icon={identificacion.reconocido ? 'food-apple-outline' : 'help-circle-outline'} />}
          />
        ))}
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

      <Divider style={{ marginVertical: 20 }} />

      <View style={styles.card}>
        <Text variant="titleMedium" style={{ marginBottom: 12 }}>Notificaciones por correo</Text>

        <View style={styles.filaSwitch}>
          <Text style={styles.labelSwitch}>Recibir alertas de vencimiento</Text>
          <Switch value={notifActivas} onValueChange={setNotifActivas} />
        </View>

        {notifActivas && (
          <>
            <Text style={[styles.etiqueta, { marginTop: 16, marginBottom: 4 }]}>
              Correo para las alertas (opcional)
            </Text>
            <Text style={styles.etiquetaHint}>
              Si lo dejas vacío, se usará el correo de tu cuenta.
            </Text>
            <TextInput
              mode="outlined"
              placeholder={correo}
              value={correoNotif}
              onChangeText={setCorreoNotif}
              keyboardType="email-address"
              autoCapitalize="none"
              style={styles.input}
            />
          </>
        )}

        <Button
          mode="contained"
          onPress={guardarNotificaciones}
          loading={guardandoNotif}
          disabled={guardandoNotif}
          style={{ marginTop: 12 }}
        >
          Guardar preferencias
        </Button>

        <Button
          mode="outlined"
          icon="email-outline"
          onPress={enviarPrueba}
          loading={enviandoPrueba}
          disabled={enviandoPrueba}
          style={{ marginTop: 8 }}
        >
          Enviar notificación de prueba
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
  container: { flex: 1, backgroundColor: colores.fondo },
  content: { padding: 24 },
  title: { marginBottom: 20 },
  card: { backgroundColor: '#FFF', borderRadius: 20, padding: 16, boxShadow: sombras.suave },
  perfil: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colores.selva,
    borderRadius: 24,
    padding: 16,
    marginBottom: 20,
    gap: 12,
  },
  avatar: {
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: colores.mango,
    alignItems: 'center',
    justifyContent: 'center',
  },
  avatarLetra: { fontFamily: fuentes.titulo, fontSize: 28, color: colores.selva },
  perfilNombre: { fontFamily: fuentes.subtitulo, fontSize: 20, color: colores.blanco },
  perfilCorreo: { fontFamily: fuentes.textoMedio, fontSize: 13, color: 'rgba(255,255,255,0.8)' },
  etiqueta: { fontSize: 13, color: colores.suave, fontFamily: fuentes.textoMedio },
  valorFijo: { marginTop: 2 },
  input: { marginTop: 8, marginBottom: 4, backgroundColor: '#FFF' },
  filaValor: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  filaBotones: { flexDirection: 'row', marginTop: 8 },
  historialVacio: { color: colores.suave, marginVertical: 8, fontFamily: fuentes.texto },
  cerrarBoton: { marginTop: 24 },
  filaSwitch: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  labelSwitch: { fontSize: 15, flex: 1, marginRight: 8, fontFamily: fuentes.textoMedio },
  etiquetaHint: { fontSize: 12, color: colores.suave, marginBottom: 4, fontFamily: fuentes.texto },
});