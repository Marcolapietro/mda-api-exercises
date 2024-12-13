# Guía de Introducción a Flask 🚀

## Índice
1. [¿Qué es Flask?](#qué-es-flask)
2. [Preparación del Entorno](#preparación-del-entorno)
3. [Tu Primera Aplicación Flask](#tu-primera-aplicación-flask)
4. [Conceptos Básicos](#conceptos-básicos)
5. [Proyectos Prácticos](#proyectos-prácticos)
6. [Recursos Adicionales](#recursos-adicionales)

## ¿Qué es Flask?
Flask es un framework web minimalista escrito en Python que permite crear aplicaciones web de manera rápida y con un mínimo número de líneas de código. Es especialmente popular por su simplicidad y flexibilidad.

### Características Principales:
- Servidor de desarrollo integrado
- Depurador integrado
- Soporte para pruebas unitarias
- Motor de plantillas Jinja2
- Compatible con WSGI 1.0
- Documentación extensiva
- Gran comunidad y muchas extensiones disponibles

## Preparación del Entorno

### Paso 1: Instalación de Python
1. Descarga Python desde [python.org](https://python.org)
2. Asegúrate de marcar la opción "Add Python to PATH" durante la instalación
3. Verifica la instalación abriendo una terminal y escribiendo:
   ```bash
   python --version
   ```

### Paso 2: Crear un Entorno Virtual
```bash
# Windows
python -m venv venv

# Linux/Mac
python3 -m venv venv

# Activar el entorno virtual
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### Paso 3: Instalar Flask
```bash
pip install flask
```

## Tu Primera Aplicación Flask

### Paso 1: Crear el archivo app.py
```python
from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello_world():
    return '¡Hola, estudiantes!'

if __name__ == '__main__':
    app.run(debug=True)
```

### Paso 2: Ejecutar la aplicación
```bash
python app.py
```
Visita http://localhost:5000 en tu navegador

## Conceptos Básicos

### 1. Rutas (Routes)
```python
@app.route('/about')
def about():
    return '¡Bienvenidos a mi primera aplicación Flask!'

@app.route('/user/<username>')
def show_user(username):
    return f'¡Hola, {username}!'
```

### 2. Métodos HTTP
```python
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        return 'Procesando login...'
    return 'Por favor, inicia sesión'
```

### 3. Plantillas (Templates)
```python
from flask import render_template

@app.route('/template')
def template_example():
    return render_template('index.html', titulo='Mi Página')
```

## Recursos Adicionales

### Documentación Oficial
- [Documentación de Flask](https://flask.palletsprojects.com/)
- [Tutorial Oficial de Flask](https://flask.palletsprojects.com/tutorial/)

### Herramientas Útiles
- Postman (para probar APIs)
- SQLite Browser (para bases de datos)
- Git (para control de versiones)

### Mejores Prácticas
1. Siempre usa entornos virtuales
2. Mantén el código organizado en módulos
3. Implementa manejo de errores
4. Escribe pruebas para tu código
5. Documenta tu código adecuadamente

## Consejos para Estudiantes
- Practica escribiendo código regularmente
- No tengas miedo de experimentar
- Únete a comunidades de Flask/Python
- Revisa proyectos de código abierto
- Mantén un registro de tu aprendizaje

¡Feliz aprendizaje! 🎉