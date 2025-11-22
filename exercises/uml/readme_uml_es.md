# Práctica: Diagramas de Secuencia UML

## Introducción
Este material te ayudará a comprender y practicar la creación de diagramas de secuencia UML. Los diagramas de secuencia son una herramienta fundamental para visualizar interacciones entre componentes de un sistema.

## Conceptos Básicos

### Elementos Principales
1. **Actores**: Representan usuarios o sistemas externos
2. **Participantes**: Representan sistemas, servicios o componentes
3. **Mensajes**: Flechas que indican comunicación entre participantes
4. **Líneas de Vida**: Líneas verticales que representan el tiempo

### Tipos de Mensajes
- **Síncronos**: Flecha sólida con punta llena (→)
- **Respuesta**: Flecha punteada con punta abierta (-->)
- **Asíncronos**: Flecha punteada con punta llena (-->)

## Ejemplos Básicos

### Ejemplo 1: Login Simple
```
actor Usuario
participant Sistema

Usuario->>Sistema: login(usuario, contraseña)
Sistema-->>Usuario: loginExitoso
```

Este ejemplo muestra:
- Un actor (Usuario)
- Un sistema
- Una petición simple
- Una respuesta

### Ejemplo 2: Consulta con Base de Datos
```
actor Usuario
participant Sistema
participant BaseDatos

Usuario->>Sistema: buscarProducto(id)
Sistema->>BaseDatos: query(id)
BaseDatos-->>Sistema: datosProducto
Sistema-->>Usuario: mostrarProducto
```

Este ejemplo muestra:
- Múltiples participantes
- Cadena de mensajes
- Flujo de datos

## Características Avanzadas

### Bucles
```
loop Para cada item en carrito
    Usuario->>Sistema: agregarAlCarrito(item)
    Sistema-->>Usuario: itemAgregado
end
```

### Condiciones
```
alt stock disponible
    Sistema->>BaseDatos: actualizarStock()
    BaseDatos-->>Sistema: stockActualizado
else stock no disponible
    Sistema-->>Usuario: errorStock
end
```

### Procesos Paralelos
```
par Procesos paralelos
    Sistema->>ServicioEmail: enviarNotificacion()
    Sistema->>Sistema: actualizarEstadísticas()
end
```

## Ejercicios Prácticos

### Ejercicio 1: Componentes Básicos
Crea un diagrama de secuencia que muestre:
- Un usuario registrándose en el sistema
- El sistema validando los datos
- Una respuesta de éxito o error

### Ejercicio 2: Interacción con Base de Datos
Diseña un diagrama que represente:
- Un usuario buscando un producto por ID
- El sistema consultando una base de datos
- El manejo de casos cuando el producto existe y cuando no existe

### Ejercicio 3: Proceso de Checkout
Crea un diagrama para un proceso de checkout que incluya:
- Verificación del carrito
- Validación de stock
- Creación de orden

### Ejercicio 4: Sistema de Notificaciones
Diseña un diagrama que muestre:
- Un proceso principal síncrono
- Envío de notificaciones asíncronas
- Múltiples servicios interactuando

## Criterios de Evaluación
- Uso correcto de la sintaxis UML
- Claridad en la representación de las interacciones
- Manejo apropiado de flujos alternativos
- Uso adecuado de características avanzadas cuando sea necesario

## Recursos Adicionales
- [Documentación oficial de UML](https://www.uml.org/)
- [Guía de diagramas de secuencia](https://www.visual-paradigm.com/guide/uml-unified-modeling-language/what-is-sequence-diagram/)
- Herramientas recomendadas para diagramas UML:
  - [PlantUML](https://plantuml.com/)
  - [Draw.io](https://draw.io/)
  - [Lucidchart](https://www.lucidchart.com/)

## Entrega
- Los diagramas deben ser entregados en formato de imagen o mediante un archivo compatible con las herramientas mencionadas
- Incluir una breve descripción de cada diagrama
