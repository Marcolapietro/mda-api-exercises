# Solución - Ejercicio 2: Introducción a las APIs

## Definición de API

Una **API (Application Programming Interface)** es un conjunto de reglas y protocolos que permite que diferentes aplicaciones se comuniquen entre sí. Actúa como un intermediario que facilita la interacción entre el cliente (por ejemplo, una aplicación web o móvil) y el servidor, permitiendo el intercambio de datos y funcionalidades sin necesidad de conocer los detalles internos de cada uno.

## Importancia de las APIs

Las APIs son fundamentales en el desarrollo moderno de software por varias razones:

1. **Modularidad y Reutilización:** Permiten dividir una aplicación en componentes más pequeños y reutilizables, facilitando el mantenimiento y la escalabilidad.
2. **Integración entre Servicios:** Facilitan la integración de diferentes servicios y aplicaciones, permitiendo que trabajen juntos de manera eficiente.
3. **Innovación Rápida:** Permiten a los desarrolladores utilizar funcionalidades existentes sin necesidad de desarrollarlas desde cero, acelerando el proceso de desarrollo.

## Ejemplos de APIs Populares

### 1. **Google Maps API**

- **Descripción:** Permite integrar mapas interactivos en aplicaciones web y móviles, ofreciendo funcionalidades como geolocalización, rutas, y marcadores personalizados.
- **Uso Común:** Aplicaciones de navegación, servicios de entrega, y sitios web que requieren visualización de ubicaciones geográficas.
- **Documentación:** [Google Maps Platform Documentation](https://developers.google.com/maps/documentation)

### 2. **GitHub REST API**

- **Descripción:** Da acceso a los datos de GitHub: repositorios, usuarios, issues, pull requests y releases. Muchos endpoints públicos funcionan sin autenticación (con un límite de peticiones por hora más bajo).
- **Uso Común:** Integraciones de CI/CD, bots que gestionan issues y pull requests, paneles de métricas de proyectos y login con GitHub (OAuth).
- **Documentación:** [GitHub REST API Documentation](https://docs.github.com/en/rest)

### 3. **Stripe API**

- **Descripción:** Facilita la integración de pagos en línea, permitiendo procesar transacciones, gestionar suscripciones, y manejar información de tarjetas de crédito de manera segura.
- **Uso Común:** Plataformas de comercio electrónico, aplicaciones de suscripción, y cualquier servicio que requiera procesamiento de pagos.
- **Documentación:** [Stripe API Reference](https://stripe.com/docs/api)

## Prueba en Postman

Google Maps y Stripe necesitan una key; la API REST de GitHub no la pide para datos públicos, así que la petición de prueba se hace a ella:

- **Petición:** `GET https://api.github.com/users/octocat`
- **Código de estado:** `200 OK`
- **Fragmento de la respuesta:**
  ```json
  {"login": "octocat", "id": 583231, "type": "User", "name": "The Octocat", "public_repos": 8}
  ```

## Frameworks de desarrollo de APIs
- FastAPI, Flask, Django REST Framework - Python
- Express - Node.js


