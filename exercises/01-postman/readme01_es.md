# Ejercicio 1: Explorando una API Pública con Postman

## Inicio Rápido

- Este ejercicio usa solo Postman; no hay ninguna app que ejecutar.
- Instala Postman, crea tú mismo las peticiones y sigue los pasos de abajo.


## **Objetivo**
- Instalar y configurar Postman.
- Hacer una consulta a una API pública para obtener datos.

---

## **Parte 1: Instalar Postman**

### 1. **Descarga Postman**
- Entra en la [web oficial de Postman](https://www.postman.com/downloads/).
- Descarga la versión compatible con tu sistema operativo.

### 2. **Instala Postman**
- Sigue las instrucciones del instalador para completar la instalación.

### 3. **Inicia sesión**
- Abre Postman y crea una cuenta si aún no tienes una. También puedes continuar como invitado.

---

## **Parte 2: Elegir una API Pública**
- Usaremos la API pública [JSONPlaceholder](https://jsonplaceholder.typicode.com/), que ofrece datos de prueba para practicar y aprender.

---

## **Parte 3: Hacer una Petición**

### 1. **Abre Postman**
- Arranca la aplicación Postman.

### 2. **Crea una petición nueva**
- Haz clic en **New Tab** o en el botón **+** de la barra superior.

### 3. **Configura la petición**
- **Método HTTP:** selecciona **GET**.
- **URL:** introduce la siguiente URL:
  ```
  https://jsonplaceholder.typicode.com/posts/1
  ```
  (Esto obtiene un post concreto, el de ID 1).

### 4. **Envía la petición**
- Haz clic en el botón **Send**.

### 5. **Analiza la respuesta**
- Observa la respuesta que aparece en el panel inferior. Deberías ver algo así:
  ```json
  {
    "userId": 1,
    "id": 1,
    "title": "sunt aut facere repellat provident occaecati excepturi optio reprehenderit",
    "body": "quia et suscipit\nsuscipit recusandae consequuntur expedita et cum\nreprehenderit molestiae ut ut quas totam\nnostrum rerum est autem sunt rem eveniet architecto"
  }
  ```
- Fíjate también en el código de estado junto a la respuesta (`200 OK`) y en la pestaña **Headers** de la respuesta (`Content-Type: application/json; charset=utf-8`).

---

## **Parte 4: Consultas Avanzadas**

### 1. **Prueba otros endpoints**
- Cambia la URL a:
  - `https://jsonplaceholder.typicode.com/posts` (obtiene todos los posts).
  - `https://jsonplaceholder.typicode.com/users/1` (obtiene la información de un usuario).

### 2. **Añade parámetros**
- Prueba a añadir parámetros como `?_limit=5` a la URL:
  ```
  https://jsonplaceholder.typicode.com/posts?_limit=5
  ```
  Esto limita los resultados a 5 posts.

---

## **Parte 5: Pasos adicionales**


### 1. **Tareas adicionales (opcional)**
- Haz una petición con el método **POST** para añadir un post nuevo:
  - Cambia el método a **POST**.
  - URL: `https://jsonplaceholder.typicode.com/posts`.
  - En la pestaña **Body**, selecciona **raw** y elige **JSON**.
  - Introduce un objeto JSON como este:
    ```json
    {
      "title": "My New Post",
      "body": "This is the content of the post",
      "userId": 1
    }
    ```
  - Haz clic en **Send** y observa la respuesta: `201 Created` y tu post con `"id": 101`. JSONPlaceholder solo simula las escrituras, así que el post no se guarda de verdad (`GET /posts/101` devuelve `404`).

---

## **Conclusión**
Este ejercicio presenta los conceptos básicos para usar Postman e interactuar con una API pública. Puedes experimentar con otros métodos HTTP y endpoints para familiarizarte más con lo que ofrece una API.

Deja Postman abierto: en el ejercicio 02 investigarás tres APIs reales y llamarás a una de ellas desde Postman, igual que has llamado aquí a JSONPlaceholder.
