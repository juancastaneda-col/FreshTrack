import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { MaterialCommunityIcons } from '@expo/vector-icons';

import InventarioScreen from '../screens/InventarioScreen';
import EscanearScreen from '../screens/EscanearScreen';
import CuentaScreen from '../screens/CuentaScreen';
import AgregarProductoScreen from '../screens/AgregarProductoScreen';

const Tab = createBottomTabNavigator();

export default function MainTabs() {
  return (
    <Tab.Navigator screenOptions={{ headerShown: true }}>
      <Tab.Screen
        name="Inventario"
        component={InventarioScreen}
        options={{ tabBarIcon: ({ color, size }) => (
          <MaterialCommunityIcons name="fridge-outline" color={color} size={size} />
        )}}
      />
      <Tab.Screen
        name="Escanear"
        component={EscanearScreen}
        options={{ tabBarIcon: ({ color, size }) => (
          <MaterialCommunityIcons name="camera-outline" color={color} size={size} />
        )}}
      />
      <Tab.Screen
        name="Agregar"
        component={AgregarProductoScreen}
        options={{ tabBarIcon: ({ color, size }) => (
          <MaterialCommunityIcons name="plus-circle-outline" color={color} size={size} />
        )}}
      />
      <Tab.Screen
        name="Cuenta"
        component={CuentaScreen}
        options={{ tabBarIcon: ({ color, size }) => (
          <MaterialCommunityIcons name="account-circle-outline" color={color} size={size} />
        )}}
      />
    </Tab.Navigator>
  );
}