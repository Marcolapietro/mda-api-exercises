# Ejercicio 4: Autenticación con API Key

## Objetivo
Implementar autenticación utilizando API Keys en una API REST desarrollada con Python y Flask.

## Descripción
En este ejercicio, ampliarás la API desarrollada en el Ejercicio 2 para incluir autenticación mediante API Keys. Cada usuario registrado recibirá una API Key única que deberá ser enviada en las solicitudes para acceder a rutas protegidas. Esto permitirá una forma adicional de autenticar solicitudes, además de la autenticación básica.

## Instrucciones

Actualiza el Archivo 'app.py' :

Importa la biblioteca uuid.
Modifica el registro de usuarios para generar y almacenar una API Key.
Crea un nuevo decorador o middleware para verificar la API Key en las solicitudes.

## Requisitos
1. **Generación de API Keys:**
   - Al registrar un nuevo usuario, genera una API Key única (puedes usar la biblioteca `uuid`).
   - Almacena la API Key asociada al usuario en la "base de datos".

2. **Envío de API Key:**
   - Las solicitudes a rutas protegidas deben incluir la API Key en los encabezados (`x-api-key`).

3. **Validación de API Keys:**
   - Implementa un middleware que verifique la validez de la API Key en cada solicitud protegida.
   - Si la API Key es válida, permite el acceso; de lo contrario, responde con un error de autenticación.

4. **Actualización de Rutas:**
   - Ajusta las rutas protegidas para que acepten autenticación tanto mediante Basic Auth como mediante API Keys.

5. **Pruebas:**
   - Utiliza herramientas como Postman o `curl` para probar el acceso a rutas protegidas usando API Keys válidas e inválidas.


   - Registrar un estudiante y obtener su API key:

   ```bash
   curl -X POST -H "Content-Type: application/json" -d '{"username":"ejemplo", "password":"secreto"}' http://127.0.0.1:5000/estudiantes
   ```

   - Acceder a 'estudiantes' con API Key:

   ```bash
   curl -H "x-api-key: <tu_api_key_aqui>" http://127.0.0.1:5000/estudiantes
   ```





## Pasos Sugeridos

1. **Instala Dependencias Adicionales:**
   ```bash
   pip install uuid
