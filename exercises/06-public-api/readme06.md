# Ejercicio 6: Consumo de API Pública

## Objetivo

Consumir APIs externas e integrar sus datos en tu propia API utilizando Python y Flask.

## Descripción

En este ejercicio, ampliarás la API desarrollada en los ejercicios anteriores para incluir una nueva ruta que consuma datos de la API de OpenWeatherMap para obtener información meteorológica. Los estudiantes deberán implementar esta funcionalidad llenando los espacios en blanco proporcionados.

## Requisitos

### 1. Instalación de Dependencias Adicionales
- Instala la biblioteca `requests` para realizar solicitudes HTTP.

### 2. Registro en OpenWeatherMap
- Ve a [OpenWeatherMap](https://openweathermap.org/)
- Haz clic en "Sign Up" y crea una cuenta gratuita
- Una vez registrado, ve a "API Keys" en tu perfil
- Genera una nueva API key (puede tardar hasta 2 horas en activarse, aunque normalmente es instantáneo. Si tarda mucho avisa al profesor)
- Guarda tu API key de forma segura

### 3. Estructura de la API
- Crea una ruta (`GET /clima`) que obtenga datos meteorológicos usando la API de OpenWeatherMap
- Utiliza tu API key en las peticiones

### 4. Implementación del Consumo de API
- Utiliza la biblioteca `requests` para hacer una solicitud a OpenWeatherMap
- Procesa la respuesta y retorna datos relevantes (temperatura, descripción, ciudad)

### 5. Pruebas
- Utiliza herramientas como Postman o `curl` para probar la nueva ruta
- Prueba diferentes ciudades usando el parámetro `?ciudad=NombreCiudad`

## Pasos Sugeridos

### 1. Instrucciones
En el espacio _____ dentro de la función `login`, utiliza la función adecuada de Flask-JWT-Extended para crear un token de acceso.

En la ruta /perfil, utiliza la función adecuada para obtener la identidad del usuario desde el token.

### 2. Instala Dependencias Adicionales
```bash
pip install requests
```

### 3. Ejemplo de uso de la API
```bash
# Obtener el clima de Madrid (default)
curl http://localhost:5000/clima

# Obtener el clima de otra ciudad
curl http://localhost:5000/clima?ciudad=Barcelona
```

## Documentación Adicional
- [Documentación de OpenWeatherMap API](https://openweathermap.org/api)
- [Guía de inicio rápido de OpenWeatherMap](https://openweathermap.org/guide)