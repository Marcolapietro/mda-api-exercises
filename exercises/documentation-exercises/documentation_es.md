# Documentación de APIs con Swagger/OpenAPI
## Ejercicio Práctico: Sistema de Biblioteca

### 📚 Introducción

Este ejercicio está diseñado para aprender los fundamentos de la documentación de APIs utilizando Swagger/OpenAPI 3.0. A través de un caso práctico de un sistema de biblioteca, aprenderemos a documentar endpoints, definir modelos de datos y establecer parámetros de seguridad.

### 🎯 Objetivos de Aprendizaje

- Comprender la estructura básica de un documento OpenAPI 3.0
- Aprender a documentar endpoints con diferentes métodos HTTP
- Definir modelos de datos utilizando schemas
- Implementar autenticación y seguridad
- Practicar la documentación de respuestas y códigos de estado
- Utilizar el editor Swagger para validar especificaciones

### 🛠️ Herramientas Necesarias

1. **Editor de texto** (recomendados):
   - Visual Studio Code
   - Sublime Text
   - WebStorm

2. **Herramientas online**:
   - [Swagger Editor](https://editor.swagger.io)
   - [Swagger UI](https://swagger.io/tools/swagger-ui/)

### 📝 Ejemplos de Referencia

#### 1. Estructura Básica OpenAPI

```yaml
openapi: 3.0.0
info:
  title: API de Ejemplo
  version: 1.0.0
  description: Una API simple para entender la estructura básica

servers:
  - url: http://api.ejemplo.com/v1
    description: Servidor de producción
  - url: http://staging.ejemplo.com/v1
    description: Servidor de staging

paths:
  /hello:
    get:
      summary: Saludo básico
      description: Retorna un mensaje de saludo
      responses:
        '200':
          description: Saludo exitoso
          content:
            application/json:
              schema:
                type: object
                properties:
                  message:
                    type: string
                    example: "¡Hola, mundo!"
```

#### 2. Endpoint con Parámetros

```yaml
paths:
  /usuarios/{id}:
    get:
      summary: Obtener usuario por ID
      parameters:
        - in: path
          name: id
          required: true
          schema:
            type: integer
          description: ID del usuario
          example: 123
        - in: query
          name: include
          schema:
            type: string
          description: Campos adicionales a incluir
          example: "perfil,preferencias"
      responses:
        '200':
          description: Usuario encontrado
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Usuario'
        '404':
          description: Usuario no encontrado

components:
  schemas:
    Usuario:
      type: object
      properties:
        id:
          type: integer
          example: 123
        nombre:
          type: string
          example: "Juan Pérez"
        email:
          type: string
          example: "juan@ejemplo.com"
```

#### 3. Operación POST con Request Body

```yaml
paths:
  /productos:
    post:
      summary: Crear nuevo producto
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                nombre:
                  type: string
                  example: "Laptop Gaming"
                precio:
                  type: number
                  format: float
                  example: 999.99
                categoria:
                  type: string
                  enum: ["electrónica", "ropa", "alimentos"]
                  example: "electrónica"
              required:
                - nombre
                - precio
                - categoria
      responses:
        '201':
          description: Producto creado exitosamente
        '400':
          description: Datos inválidos
```

### 📋 Ejercicio Principal: API de Biblioteca

#### Especificación Base

```yaml
openapi: 3.0.0
info:
  title: Biblioteca API
  version: 1.0.0
  description: Sistema de gestión para biblioteca

servers:
  - url: http://localhost:3000
    description: Servidor de desarrollo

components:
  securitySchemes:
    ApiKeyAuth:
      type: apiKey
      in: header
      name: X-API-KEY

  schemas:
    Book:
      type: object
      properties:
        id:
          type: string
          example: "book123"
        title:
          type: string
          example: "Don Quijote de la Mancha"
        author:
          type: string
          example: "Miguel de Cervantes"
        isbn:
          type: string
          example: "978-84-376-0494-7"
        availableQuantity:
          type: integer
          example: 5
        category:
          type: string
          example: "Literatura Clásica"
      required:
        - title
        - author
        - isbn
```

#### Endpoints a Documentar

1. **Gestión de Libros**:
   - GET /books
   - GET /books/{id}
   - POST /books
   - PUT /books/{id}
   - DELETE /books/{id}

2. **Gestión de Préstamos**:
   - POST /loans
   - GET /loans
   - PUT /loans/{id}/return
   - GET /loans/user/{userId}

### ✅ Tareas del Ejercicio

1. **Documentación Básica**
   - Completar la información básica de la API
   - Configurar los servidores
   - Implementar esquema de seguridad

2. **Endpoints de Libros**
   - Documentar todos los endpoints de libros
   - Incluir parámetros necesarios
   - Definir respuestas posibles

3. **Endpoints de Préstamos**
   - Crear schema para préstamos
   - Documentar operaciones CRUD
   - Incluir validaciones

4. **Mejoras Adicionales**
   - Implementar paginación
   - Agregar filtros de búsqueda
   - Documentar rate limiting


### 📝 Entregables

1. Archivo `openapi.yaml` completo
2. Capturas del editor Swagger mostrando validación
3. Documento de decisiones de diseño (opcional)

### 🚫 Errores Comunes a Evitar

1. **Sintaxis**
   - Indentación incorrecta
   - Falta de comillas en strings especiales
   - Referencias mal escritas

2. **Diseño**
   - Olvidar documentar errores
   - No incluir ejemplos
   - Schemas incompletos

3. **Validación**
   - No verificar en editor Swagger
   - Ignorar warnings
   - No probar ejemplos

### 💡 Consejos para el Desarrollo

1. **Empezar Simple**
   - Comenzar con un endpoint básico
   - Validar frecuentemente
   - Ir añadiendo complejidad

2. **Documentación**
   - Usar descripciones claras
   - Incluir ejemplos realistas
   - Mantener consistencia

3. **Pruebas**
   - Validar en editor Swagger
   - Probar diferentes casos
   - Verificar referencias

### 🔍 Recursos Adicionales

1. **Documentación Oficial**
   - [OpenAPI Specification](https://swagger.io/specification/)
   - [Swagger Tools](https://swagger.io/tools/)

2. **Herramientas**
   - [Swagger Editor](https://editor.swagger.io)
   - [OpenAPI Generator](https://openapi-generator.tech)

3. **Tutoriales**
   - [Swagger Tutorial](https://swagger.io/docs/specification/basic-structure/)
   - [OpenAPI Best Practices](https://swagger.io/blog/api-best-practices/)

### 🤔 Preguntas Frecuentes

1. **¿Cómo valido mi YAML?**
   - Usar editor Swagger online
   - Verificar indentación
   - Comprobar referencias

2. **¿Cómo organizo mis schemas?**
   - Agrupar por funcionalidad
   - Usar referencias
   - Mantener consistencia

3. **¿Cómo documento errores?**
   - Incluir todos los códigos posibles
   - Dar ejemplos de error
   - Explicar causas comunes


