import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { MaterialCommunityIcons } from '@expo/vector-icons';

import CatalogoScreen from '../screens/CatalogoScreen';
import EscanearScreen from '../screens/EscanearScreen';
import DetalleProductoScreen from '../screens/DetalleProductoScreen';
import AgregarProductoScreen from '../screens/AgregarProductoScreen';

const Tab = createBottomTabNavigator();

export default function MainTabs() {
  return (
    <Tab.Navigator screenOptions={{ headerShown: true }}>
      <Tab.Screen
        name="Catálogo"
        component={CatalogoScreen}
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
        name="Detalle"
        component={DetalleProductoScreen}
        options={{ tabBarIcon: ({ color, size }) => (
          <MaterialCommunityIcons name="food-apple-outline" color={color} size={size} />
        )}}
      />
    </Tab.Navigator>
  );
}