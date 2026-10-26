import { View, StyleSheet } from 'react-native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { MaterialCommunityIcons } from '@expo/vector-icons';

import InventarioScreen from '../screens/InventarioScreen';
import RecetarioScreen from '../screens/RecetarioScreen';
import AnadirScreen from '../screens/AnadirScreen';
import EscanearScreen from '../screens/EscanearScreen';
import EscanearAlimentoScreen from '../screens/EscanearAlimentoScreen';
import AgregarProductoScreen from '../screens/AgregarProductoScreen';
import CuentaScreen from '../screens/CuentaScreen';
import EncabezadoMarca from '../components/EncabezadoMarca';
import { colores, fuentes, sombras } from '../theme/theme';

const Tab = createBottomTabNavigator();

// Pantallas que se abren desde el menú "Añadir". No aparecen en la barra inferior,
// pero siguen siendo parte del navegador (así Escanear Alimento puede ir a Agregar).
const SUBPANTALLAS = ['Escanear Factura', 'Escanear Alimento', 'Agregar'];
const ocultaEnBarra = { tabBarItemStyle: { display: 'none' } };

const icono = (activo, inactivo) => ({ color, size, focused }) => (
  <MaterialCommunityIcons name={focused ? activo : inactivo} color={color} size={size + 2} />
);

export default function MainTabs() {
  const insets = useSafeAreaInsets();
  return (
    <Tab.Navigator
      screenOptions={{
        header: (props) => (
          <EncabezadoMarca {...props} volverA={SUBPANTALLAS.includes(props.route.name) ? 'Anadir' : null} />
        ),
        tabBarActiveTintColor: colores.hoja,
        tabBarInactiveTintColor: '#8A9A8D',
        tabBarLabelStyle: { fontFamily: fuentes.textoNegrita, fontSize: 11 },
        tabBarStyle: {
          backgroundColor: colores.blanco,
          borderTopWidth: 0,
          height: 64 + insets.bottom,
          paddingTop: 6,
          paddingBottom: Math.max(insets.bottom, 8),
          boxShadow: '0 -6px 20px rgba(15, 77, 42, 0.10)',
        },
        sceneStyle: { backgroundColor: colores.fondo },
      }}
    >
      <Tab.Screen
        name="Inventario"
        component={InventarioScreen}
        options={{ tabBarIcon: icono('fridge', 'fridge-outline') }}
      />
      <Tab.Screen
        name="Recetas"
        component={RecetarioScreen}
        options={{ tabBarIcon: icono('chef-hat', 'chef-hat') }}
      />
      <Tab.Screen
        name="Anadir"
        component={AnadirScreen}
        options={{
          tabBarLabel: 'Añadir',
          tabBarIcon: ({ focused }) => (
            <View style={[estilos.mas, focused && estilos.masActivo]}>
              <MaterialCommunityIcons name="plus" size={24} color={colores.blanco} />
            </View>
          ),
        }}
      />
      <Tab.Screen
        name="Cuenta"
        component={CuentaScreen}
        options={{ tabBarIcon: icono('account-circle', 'account-circle-outline') }}
      />

      <Tab.Screen name="Escanear Factura" component={EscanearScreen} options={ocultaEnBarra} />
      <Tab.Screen name="Escanear Alimento" component={EscanearAlimentoScreen} options={ocultaEnBarra} />
      <Tab.Screen name="Agregar" component={AgregarProductoScreen} options={ocultaEnBarra} />
    </Tab.Navigator>
  );
}

const estilos = StyleSheet.create({
  mas: {
    width: 46,
    height: 46,
    borderRadius: 23,
    marginTop: -16,
    backgroundColor: colores.papaya,
    alignItems: 'center',
    justifyContent: 'center',
    boxShadow: sombras.suave,
  },
  masActivo: { backgroundColor: colores.hoja },
});