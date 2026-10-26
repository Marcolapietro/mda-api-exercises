# Ejercicio 11: Exponer tu API Públicamente con ngrok y Webhooks de GitHub

## Introducción

En este ejercicio aprenderás a exponer tu API Flask local a internet usando **ngrok** y a configurar **webhooks reales de GitHub**. Esto es esencial para:
- Recibir notificaciones de webhook de GitHub cuando se hace push de código
- Compartir tu API con compañeros de equipo sin desplegarla
- Entender cómo se comunican los servicios mediante webhooks
- Aprender patrones de webhooks de producción usados en sistemas CI/CD

En cuanto tu API tiene una URL pública, **cualquiera** puede hacerle un POST. Por eso este ejercicio trata la seguridad del webhook como parte central de la tarea, no como un extra: tu endpoint solo aceptará peticiones que lleven una firma válida de GitHub.

## Objetivos de Aprendizaje

Al terminar este ejercicio serás capaz de:

1. Instalar y configurar ngrok en tu sistema (verificado en 2025)
2. Exponer una API Flask local en una URL pública HTTPS
3. Configurar webhooks reales de GitHub en los ajustes del repositorio
4. Implementar endpoints de webhook que manejen payloads auténticos de GitHub
5. **Verificar la firma HMAC `X-Hub-Signature-256`** en cada llamada, con una comparación en tiempo constante
6. **Deduplicar entregas** por `X-GitHub-Delivery`, porque los reintentos ocurren
7. Usar el panel de ngrok para inspeccionar y depurar peticiones
8. Colaborar con compañeros compartiendo URLs de ngrok

## ¿Qué es ngrok?

**ngrok** es una herramienta que crea un túnel seguro desde una URL pública hasta tu servidor de desarrollo local. Proporciona:
- Una URL pública HTTPS que redirige a localhost
- Un panel web que muestra todas las peticiones HTTP en tiempo real
- Capacidades de inspección y repetición (replay) de peticiones
- Un plan gratuito con las funciones esenciales (perfecto para aprender)

**Sitio oficial:** https://ngrok.com

**Casos de Uso:**
- **Webhooks de GitHub**: Recibir notificaciones de push de GitHub en tu app Flask local
- **Colaboración en equipo**: Compartir tu API durante el proyecto ProManage sin desplegarla
- **Desarrollo CI/CD**: Construir flujos automatizados disparados por eventos de GitHub
- **Pruebas de microservicios**: Probar la comunicación entre servicios en local

## Prerrequisitos

Antes de empezar este ejercicio deberías haber completado:
- **Ejercicio 03**: Fundamentos de APIs (entender apps Flask básicas)
- **Ejercicio 06**: Autenticación JWT (opcional, pero recomendado)

## Instalación

### Paso 1: Descargar ngrok

**Windows:**
1. Visita [ngrok.com/download](https://ngrok.com/download)
2. Descarga el ZIP para Windows
3. Extrae `ngrok.exe` en una carpeta (p. ej., `C:\ngrok\`)
4. Añádelo al PATH (opcional pero recomendado):
   - Abre "Variables de entorno" en la Configuración del sistema
   - Edita la variable "Path"
   - Añade `C:\ngrok\` (o la ubicación que hayas elegido)
   - Reinicia la terminal

**Mac (con Homebrew):**
```bash
brew install ngrok/ngrok/ngrok
```

**Linux:**
```bash
# Descargar
curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null
echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | sudo tee /etc/apt/sources.list.d/ngrok.list
sudo apt update && sudo apt install ngrok
```

**Verificar la Instalación:**
```bash
ngrok version
# Debería mostrar: ngrok version 3.x.x
```

### Paso 2: Crear una Cuenta de ngrok (Gratis)

1. Ve a [ngrok.com/signup](https://ngrok.com/signup)
2. Crea una cuenta gratuita (obligatoria, no hace falta tarjeta de crédito)
3. Verifica tu dirección de email

**El plan gratuito incluye:**
- 1 proceso de ngrok en línea
- 40 conexiones/minuto
- Túneles HTTPS
- Inspección de peticiones

### Paso 3: Autenticar ngrok (Actualizado 2025)

1. Inicia sesión en [dashboard.ngrok.com](https://dashboard.ngrok.com)
2. Ve a "Getting Started" → "Your Authtoken"
3. Copia tu authtoken
4. Ejecuta en la terminal:
   ```bash
   ngrok config add-authtoken TU_AUTH_TOKEN_AQUI
   ```

**Ejemplo:**
```bash
ngrok config add-authtoken 2bXjYZ1234abcd5678efgh_9IJKLMnopqrstuvwxyz
```

Esto guarda tu token en el fichero de configuración de ngrok:
- **Mac/Linux**: `~/.ngrok2/ngrok.yml`
- **Windows**: `%USERPROFILE%\.ngrok2\ngrok.yml`

## Inicio Rápido

### Ejecutar una App Flask Básica

```bash
cd exercises/11-ngrok-public-api
python -m venv venv

# Activar el entorno virtual
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

pip install -r requirements.txt
python app.py
```

Tu app se ejecuta en `http://127.0.0.1:5000`

> Al arrancar, la app muestra un **aviso** si `GITHUB_WEBHOOK_SECRET` no está definida. `/health`, `/info` y `/users`
> funcionan igualmente, pero `/webhooks/github` responde **503** hasta que definas el secreto (ver Tarea 2.2).

### Exponer con ngrok

**Abre una terminal nueva** (deja Flask ejecutándose) y ejecuta:
```bash
ngrok http 5000
```

Verás una salida como esta:
```
ngrok

Session Status                online
Account                       your-email@example.com (Plan: Free)
Version                       3.5.0
Region                        United States (us)
Latency                       25ms
Web Interface                 http://127.0.0.1:4040
Forwarding                    https://abcd-1234-5678-efgh.ngrok-free.app -> http://localhost:5000

Connections                   ttl     opn     rt1     rt5     p50     p90
                              0       0       0.00    0.00    0.00    0.00
```

**Tu URL pública**: `https://abcd-1234-5678-efgh.ngrok-free.app`

¡Ahora cualquiera puede acceder a tu API en esta URL!

### Pruébalo

```bash
# Desde cualquier sitio (tu móvil, otro ordenador, etc.)
curl https://abcd-1234-5678-efgh.ngrok-free.app/health
```

## Estructura del Ejercicio

Este ejercicio incluye:
- `app.py` - App Flask inicial con TODOs para implementar el webhook (comprobación de firma, deduplicación, payload)
- `example/example11.py` - Solución de referencia completa
- `example/send_signed_webhook.py` - Script auxiliar que envía webhooks de prueba **firmados** a tu app, sin GitHub
- `readme11.md` / `readme11_es.md` - Este fichero de instrucciones (inglés / español)

## Parte 1: Exposición Básica (15 minutos)

### Tarea 1.1: Ejecutar la App de Ejemplo

El `app.py` incluido tiene una API básica con endpoints de health check y de usuarios.

```bash
python app.py
```

Visita `http://localhost:5000/health`: debería devolver `{"status": "ok"}`

### Tarea 1.2: Exponer con ngrok

En una **terminal nueva**:
```bash
ngrok http 5000
```

Copia tu URL pública (la dirección `https://....ngrok-free.app`).

### Tarea 1.3: Probar el Acceso Público

Desde el navegador o con curl:
```bash
curl https://TU-URL-NGROK.ngrok-free.app/health
```

**Resultado Esperado**: La misma respuesta que en localhost

### Tarea 1.4: Explorar el Panel de ngrok

Abre `http://localhost:4040` en el navegador.

Verás:
- La lista de todas las peticiones HTTP
- Detalles de petición/respuesta (cabeceras, cuerpo, estado)
- La opción de repetir (replay) peticiones
- Estadísticas de conexión

Haz varias peticiones y mira cómo aparecen en tiempo real.

## Parte 2: Webhook Real y Firmado de GitHub (60 minutos)

Esta es la parte central del ejercicio. Configurarás un **webhook real de GitHub** que se dispara cuando haces push, y tu endpoint **solo lo aceptará si la firma de GitHub es válida**.

### Tarea 2.1: Crear o Elegir un Repositorio de GitHub

**Opción A - Crear un Repo de Prueba Nuevo:**
1. Ve a [github.com/new](https://github.com/new)
2. Llámalo `api-webhook-test` (o como quieras)
3. Hazlo **Public** (necesario para webhooks gratuitos)
4. Inicialízalo con un README
5. Crea el repositorio

**Opción B - Usar un Repo Existente:**
- Sirve cualquier repo público tuyo
- Necesitas permisos de administrador para configurar webhooks

### Tarea 2.2: Generar el Secreto del Webhook y Definirlo como Variable de Entorno

GitHub y tu app comparten un **secreto**. GitHub lo usa para firmar cada entrega; tu app lo usa para comprobar la firma. Nadie más lo conoce, así que nadie más puede producir una firma válida.

**Paso 1: Genera un secreto** (funciona igual en Windows, Mac y Linux):
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Esto imprime 64 caracteres hexadecimales (32 bytes aleatorios) del generador **criptográficamente seguro** de Python, por ejemplo `3f9c...e1a7`. Cópialo.

> No inventes el secreto tú mismo ni uses generadores no criptográficos (como `Get-Random` de PowerShell
> o el módulo `random` de Python): su salida se puede predecir.

**Paso 2: Defínelo como variable de entorno** en la **misma terminal** donde vas a ejecutar `python app.py` (solo dura esa sesión de terminal):

```bash
# Linux / macOS (bash, zsh)
export GITHUB_WEBHOOK_SECRET="pega-aqui-los-64-caracteres-hex"
```

```powershell
# Windows PowerShell
$env:GITHUB_WEBHOOK_SECRET="pega-aqui-los-64-caracteres-hex"
```

```bat
:: Windows CMD (sin comillas, sin espacios alrededor del =)
set GITHUB_WEBHOOK_SECRET=pega-aqui-los-64-caracteres-hex
```

**Nunca** pegues el secreto en `app.py`: todo lo que está en el código acaba en Git. Guarda el valor en un sitio seguro: en la Tarea 2.6 pegarás **el mismo valor** en el campo **Secret** del webhook de GitHub.

Si la variable no está definida, la app muestra un aviso al arrancar y `/webhooks/github` responde:
```json
{"error": "Webhook secret not configured", "message": "Set the GITHUB_WEBHOOK_SECRET environment variable and restart the app."}
```
con estado **503**. **Nunca** acepta peticiones sin firmar como alternativa.

### Tarea 2.3: Completar el Endpoint del Webhook

#### Cómo funcionan las firmas (HMAC) de los webhooks de GitHub

```
GitHub                                         Tu app Flask
──────                                         ────────────
body = los bytes JSON en bruto                 body = request.get_data()   (¡bytes en bruto!)
sig  = HMAC-SHA256(secret, body)               expected = HMAC-SHA256(secret, body)

POST /webhooks/github                          la cabecera debe empezar por "sha256="
X-Hub-Signature-256: sha256=<sig en hex>  ──►  ¿compare_digest(expected, received)?
X-GitHub-Delivery:   <id único>                  ✅ iguales     → continuar
                                                 ❌ distintas   → 401 Unauthorized
```

1. Defines el secreto en GitHub al configurar el webhook (y en el entorno de tu app).
2. GitHub calcula un **HMAC-SHA256** del cuerpo de la petición usando el secreto.
3. GitHub lo envía en la cabecera `X-Hub-Signature-256`, como `sha256=<digest en hex>`.
4. Tu app recalcula el HMAC sobre los bytes que ha recibido y compara.
5. Si coinciden → la petición viene de GitHub y el cuerpo no se ha modificado. Si no → se rechaza con **401**.

**Cuatro detalles importantes:**
- **Usa el cuerpo EN BRUTO** (`request.get_data()`), nunca `json.dumps(request.get_json())`. Al volver a serializar cambian los espacios y el orden de las claves, y el HMAC deja de coincidir.
- **Comprueba el prefijo `sha256=`.** Rechaza una cabecera ausente, el formato antiguo `X-Hub-Signature: sha1=...` o cualquier otra cosa. Hacer simplemente un split por `=` aceptaría basura.
- **Compara en tiempo constante** con `hmac.compare_digest`. Un `==` normal termina en cuanto un carácter es distinto, y esa diferencia de tiempo se puede medir para adivinar la firma byte a byte.
- **Sin secreto, no se procesa nada.** Si falta `GITHUB_WEBHOOK_SECRET`, el endpoint responde 503. Un endpoint que "verifica solo si hay un secreto configurado" es un endpoint que acepta peticiones falsificadas.

> **La misma idea en otros proveedores:** GitHub llama a esta cabecera `X-Hub-Signature-256`. Stripe usa
> `Stripe-Signature` (además firma una marca de tiempo para frenar repeticiones), Slack usa `X-Slack-Signature`, etc.
> Cambian el nombre y el formato de la cabecera, pero el patrón es siempre el mismo: secreto compartido + HMAC del
> cuerpo en bruto + comparación en tiempo constante.

#### Deduplicar por ID de entrega

Si tu endpoint es lento, falla o GitHub no recibe la respuesta, GitHub **vuelve a entregar el mismo evento**. También puedes pulsar **Redeliver** en GitHub. Cada entrega lleva una cabecera `X-GitHub-Delivery` con un ID único, y una reentrega mantiene el **mismo** ID. Tu app recuerda los IDs que ya ha procesado (`processed_deliveries`, un `set` de Python) y responde a una repetición con:
```json
{"status": "duplicate, ignored", "delivery_id": "..."}
```
con estado **200**, para que GitHub deje de reintentar, pero el evento **no se guarda dos veces**.

> El ID de entrega no forma parte de la firma, así que la deduplicación te protege de los **reintentos**, no de un
> atacante que repita una petición capturada. Proveedores como Stripe firman también una marca de tiempo para limitarlo.

#### Responder rápido, procesar después

GitHub espera **10 segundos** tu respuesta; después marca la entrega como fallida (y puede reintentarla). Por eso el endpoint solo debe verificar, guardar un registro mínimo y responder **2xx** de inmediato. El trabajo lento (ejecutar tests, desplegar, enviar emails) va a una **cola** que procesa un worker en segundo plano (p. ej. Celery, RQ, una cola en la nube). En este ejercicio "guardar" es añadir a una lista en memoria, que es suficientemente rápido.

#### Tus TODOs en `app.py`

Abre `app.py` y completa los **13 huecos** (`_____`). El orden de las comprobaciones en el endpoint es: secreto configurado → firma → deduplicación → parsear JSON → guardar → responder.

| # | Dónde (función / sección) | Qué escribir |
|---|---------------------------|--------------|
| 1 | `verify_github_signature()` | Prefijo obligatorio: `signature_header.startswith('sha256=')` |
| 2 | `verify_github_signature()` | Calcular el HMAC: `hmac.new(secret.encode(), payload_body, hashlib.sha256).hexdigest()` |
| 3 | `verify_github_signature()` | Comparación en tiempo constante: `hmac.compare_digest(expected_signature, received_signature)` |
| 4 | `@app.route('/webhooks/github', ...)` | Método HTTP: `'POST'` |
| 5 | `github_webhook()` | Cuerpo en bruto: `request.get_data()` |
| 6 | `github_webhook()` | Comprobación de duplicados: `if delivery_id in processed_deliveries:` |
| 7 | `github_webhook()` | Parsear el JSON (¡después de verificar!): `request.get_json(silent=True)` |
| 8 | `github_webhook()` | Repositorio: `data.get('repository', {})` |
| 9 | `github_webhook()` | Quién hizo push: `data.get('pusher', {})` |
| 10 | `github_webhook()` | Commits: `data.get('commits', [])` |
| 11 | `github_webhook()` | Rama: `data.get('ref', 'unknown')` |
| 12 | `github_webhook()` | Recordar la entrega: `processed_deliveries.add(delivery_id)` |
| 13 | `github_webhook()` | Código de estado de éxito: `200` |

La función de firma que completas:

```python
def verify_github_signature(payload_body, signature_header, secret):
    # TODO: Only accept the SHA-256 format
    # Hint: GitHub's header starts with 'sha256='
    if not signature_header or not signature_header.startswith('_____'):
        return False
    received_signature = signature_header[len('sha256='):]

    # TODO: Recompute the signature over the exact bytes we received
    # Hint: hmac.new(key_bytes, message_bytes, hashlib.sha256).hexdigest()
    expected_signature = hmac._____(secret.encode(), payload_body, hashlib.sha256).hexdigest()

    # TODO: Compare the two signatures in CONSTANT time
    # Hint: hmac.compare_digest(a, b) - never use '==', it leaks timing information
    return hmac._____(expected_signature, received_signature)
```

Y la parte de seguridad del endpoint:

```python
@app.route('/webhooks/github', methods=['_____'])  # TODO: Which HTTP method? Hint: POST
def github_webhook():
    # 1. Sin secreto -> rechazar (nunca aceptar peticiones sin firmar)
    secret = os.environ.get('GITHUB_WEBHOOK_SECRET')
    if not secret:
        return jsonify({'error': 'Webhook secret not configured', ...}), 503

    # 2. TODO: Read the RAW body bytes. Hint: request.get_data()
    body = request._____()
    signature = request.headers.get('X-Hub-Signature-256')
    if not verify_github_signature(body, signature, secret):
        return jsonify({'error': 'Unauthorized', ...}), 401

    # 3. Deduplicar
    delivery_id = request.headers.get('X-GitHub-Delivery')
    ...
    # TODO: If we already processed this delivery ID, ignore it
    if delivery_id in _____:
        return jsonify({'status': 'duplicate, ignored', 'delivery_id': delivery_id}), 200

    # TODO: Only now is it safe to parse the JSON. Hint: request.get_json(silent=True)
    data = _____
    ...
    # (extraer repository, pusher, commits y ref, mostrarlos y guardar un registro mínimo)
    ...
    # TODO: Remember this delivery. Hint: processed_deliveries.add(delivery_id)
    processed_deliveries._____(delivery_id)

    # TODO: Return success response. Hint: 200
    return jsonify({'status': 'received', 'commits_processed': len(commits)}), _____
```

Estructura real del payload de push de GitHub (la parte que leemos):
```
{
  "ref": "refs/heads/main",
  "repository": {"name": "...", "full_name": "user/repo"},
  "pusher": {"name": "...", "email": "..."},
  "commits": [{"id": "...", "message": "...", "author": {...}}, ...]
}
```

### Tarea 2.4: Probar en Local sin GitHub

Antes de meter a GitHub por medio, demuestra que tu endpoint acepta las firmas buenas y rechaza las malas. `example/send_signed_webhook.py` firma un payload de push de ejemplo exactamente igual que GitHub y lo envía a tu app.

**Terminal 1 - Flask** (con `GITHUB_WEBHOOK_SECRET` definida, Tarea 2.2):
```bash
python app.py
```

**Terminal 2 - script auxiliar** (define **el mismo** `GITHUB_WEBHOOK_SECRET` también en esta terminal):
```bash
python example/send_signed_webhook.py
```

Salida esperada (los IDs de entrega cambiarán):
```
[valid       ] delivery=6f1c... -> HTTP 200 {"commits_processed":1,"status":"received"}
[valid       ] delivery=0b7e... -> HTTP 200 {"commits_processed":1,"status":"received"}
   ...sending the same delivery ID again (simulating a GitHub retry):
[valid       ] delivery=0b7e... -> HTTP 200 {"delivery_id":"0b7e...","status":"duplicate, ignored"}
[tampered    ] delivery=9a42... -> HTTP 401 {"error":"Unauthorized","message":"Missing or invalid X-Hub-Signature-256 signature"}
[unsigned    ] delivery=c3d5... -> HTTP 401 {"error":"Unauthorized",...}
[wrong-prefix] delivery=e8f0... -> HTTP 401 {"error":"Unauthorized",...}
```

Después comprueba que el duplicado **no** se ha guardado dos veces:
```bash
curl http://127.0.0.1:5000/webhooks/events
# total_events: 2  (dos entregas válidas distintas; la repetida cuenta una sola vez)
```

Puedes ejecutar un solo caso con `--mode valid|duplicate|tampered|unsigned|wrong-prefix`, o apuntar a tu URL pública con `--url https://TU-URL-NGROK.ngrok-free.app/webhooks/github`.

**Qué demuestra cada caso:**
- **valid** → la firma que calculas coincide con el algoritmo de GitHub.
- **duplicate** → un reintento con el mismo `X-GitHub-Delivery` se confirma pero se ignora.
- **tampered** → el cuerpo se modificó después de firmarlo: el HMAC ya no coincide.
- **unsigned** → sin cabecera: rechazado, aunque el JSON sea perfectamente válido.
- **wrong-prefix** → el digest correcto con prefijo `sha1=`: rechazado, solo se acepta `sha256=`.

### Tarea 2.5: Ejecutar tu App Flask y ngrok

**Terminal 1 - Flask** (con `GITHUB_WEBHOOK_SECRET` definida):
```bash
cd exercises/11-ngrok-public-api
python app.py
```

**Terminal 2 - ngrok:**
```bash
ngrok http 5000
```

**Copia tu URL de ngrok** de la salida:
```
Forwarding    https://abc123-xyz.ngrok-free.app -> http://localhost:5000
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
              ¡Copia esta URL!
```

ngrok te da una URL **HTTPS**: úsala. Los payloads y las firmas de los webhooks deben viajar siempre por HTTPS.

### Tarea 2.6: Configurar el Webhook de GitHub

1. **Ve a tu repositorio en GitHub**
   - Navega a `https://github.com/TU-USUARIO/TU-REPO`

2. **Abre Settings → Webhooks**
   - Haz clic en la pestaña **Settings** del repositorio (arriba a la derecha)
   - Baja y haz clic en **Webhooks** en la barra lateral izquierda
   - Haz clic en el botón **Add webhook**

3. **Configura el Webhook**
   - **Payload URL**: `https://TU-URL-NGROK.ngrok-free.app/webhooks/github`
     - Ejemplo: `https://abc123-xyz.ngrok-free.app/webhooks/github`
     - ⚠️ ¡Asegúrate de incluir `/webhooks/github` al final!

   - **Content type**: Selecciona `application/json` (con el valor por defecto `application/x-www-form-urlencoded` el cuerpo no es JSON y la app responde 400)

   - **Secret**: Pega **el mismo valor** que pusiste en `GITHUB_WEBHOOK_SECRET` (Tarea 2.2)

   - **SSL verification**: Déjala activada

   - **Which events?**: Selecciona "Just the push event"

   - **Active**: Marca esta casilla ✅

   - Haz clic en **Add webhook**

4. **Verifica la Configuración**
   - GitHub enviará inmediatamente un evento "ping" firmado
   - Mira tu terminal de Flask: deberías ver `GitHub Webhook Ping Received!`
   - En GitHub, baja hasta "Recent Deliveries": debería aparecer un check verde ✅

**Problema Común**: Si ves una X roja, comprueba:
- ¿Está Flask en marcha? ¿Está ngrok en marcha?
- ¿Copiaste la URL de ngrok correcta, incluyendo `/webhooks/github`?
- **401 Unauthorized** → el Secret de GitHub y `GITHUB_WEBHOOK_SECRET` son distintos (cópialos otra vez, sin espacios de más), o definiste la variable en otra terminal.
- **503** → `GITHUB_WEBHOOK_SECRET` no está definida en la terminal donde se ejecuta Flask.
- **400 Invalid payload** → el Content type no es `application/json`.

### Tarea 2.7: Disparar el Webhook con un Push Real

¡Llega el momento mágico! Haz un cambio en tu repositorio:

**Método 1 - Interfaz Web de GitHub (lo más fácil):**
1. Ve a tu repo en GitHub
2. Haz clic en `README.md`
3. Haz clic en el icono del lápiz (Edit)
4. Añade una línea: `Probando webhook a las [hora actual]`
5. Baja y haz clic en **Commit changes**
6. Vuelve a hacer clic en **Commit changes**

**Mira tu terminal de Flask**: deberías ver:
```
============================================================
🎉 REAL GitHub Webhook Received!
🆔 Delivery: 72d3162e-cc78-11e3-81ab-4c9367dc0958
📦 Repository: tu-usuario/api-webhook-test
👤 Pushed by: tu-usuario
🌿 Branch: refs/heads/main
📝 Commits: 1
   1. [a1b2c3d] Update README.md (by Tu Nombre)
============================================================
```

**Método 2 - Git por Línea de Comandos (si tienes git):**
```bash
git clone https://github.com/TU-USUARIO/TU-REPO.git
cd TU-REPO
echo "Test webhook $(date)" >> README.md
git add README.md
git commit -m "Test webhook trigger"
git push
```

### Tarea 2.8: Inspeccionar (y Repetir) el Webhook en el Panel de ngrok

1. Abre `http://localhost:4040` en el navegador
2. Verás la petición POST de GitHub
3. Haz clic en ella para ver:
   - Todas las cabeceras, incluidas `X-Hub-Signature-256`, `X-GitHub-Delivery` y `X-GitHub-Event`
   - El payload JSON completo (los bytes en bruto que se firmaron)
   - Tu respuesta (200 OK)
4. Haz clic en **Replay**: ngrok reenvía exactamente la misma petición, con el mismo ID de entrega. Tu app responde `"duplicate, ignored"` y `/webhooks/events` no crece. Eso es la deduplicación funcionando.
5. Prueba **Redeliver** en GitHub ("Recent Deliveries" → una entrega → **Redeliver**): mismo resultado, porque una reentrega mantiene su `X-GitHub-Delivery`.

**¡Esto es utilísimo para depurar webhooks!**

### Tarea 2.9: Ver Todos los Webhooks Recibidos

Tu app guarda los eventos de webhook. Consúltalos:

```bash
curl https://TU-URL-NGROK.ngrok-free.app/webhooks/events
```

Verás todos los eventos de GitHub que has recibido, cada uno con su `delivery_id`. `POST /webhooks/events/clear` vacía la lista y olvida los IDs de entrega procesados.

## Parte 3: Colaboración en Equipo (20 minutos)

Ahora que entiendes los webhooks, practica compartiendo tu API con tus compañeros (¡esencial para el proyecto ProManage!).

### Tarea 3.1: Compartir tu API

1. Asegúrate de que tu app Flask y ngrok están en marcha
2. Comparte tu URL de ngrok con un compañero: `https://tu-url.ngrok-free.app`
3. Pídele que pruebe tus endpoints `/health` e `/info`

`/info` devuelve las cabeceras de la petición, pero elimina `Authorization`, `Cookie`, `X-API-Key` y las cabeceras de firma: un endpoint público nunca debe reflejar credenciales.

### Tarea 3.2: Llamar a la API de un Compañero

1. Pide la URL de ngrok a un compañero
2. Prueba sus endpoints:
   ```bash
   # Health check
   curl https://url-ngrok-companero.ngrok-free.app/health

   # Ver información de la petición
   curl https://url-ngrok-companero.ngrok-free.app/info

   # Crear un usuario en su API
   curl -X POST https://url-ngrok-companero.ngrok-free.app/users \
     -H "Content-Type: application/json" \
     -d '{"username": "tunombre", "email": "tu@example.com"}'
   ```

3. Intenta enviarle un push falso sin firma:
   ```bash
   curl -X POST https://url-ngrok-companero.ngrok-free.app/webhooks/github \
     -H "Content-Type: application/json" \
     -H "X-GitHub-Delivery: fake-1" \
     -d '{"ref": "refs/heads/main", "commits": []}'
   ```
   **Esperado:** `401 Unauthorized`. Este es exactamente el ataque que la firma impide.

### Tarea 3.3: Pruebas de Webhooks entre Equipos

**Colaboración avanzada**: ¡Configura tu webhook de GitHub para avisar a tu compañero cuando haces push!

1. Tu compañero comparte su URL de ngrok **y** acordáis un secreto de webhook (él lo define como su `GITHUB_WEBHOOK_SECRET`; compartidlo en privado, no en un chat público)
2. En los ajustes de **tu** repo de GitHub:
   - Añade un **segundo webhook**
   - Usa la URL de tu compañero: `https://url-companero.ngrok-free.app/webhooks/github`
   - Content type `application/json`, y su secreto en el campo **Secret**
3. Haz un commit en **tu** repo
4. ¡La app Flask de tu compañero recibe la notificación!

**Esto demuestra comunicación entre microservicios**: un servicio notifica a otro sobre eventos, autenticado con un secreto compartido.

**Nota**: ¡Este ejercicio te prepara para el Ejercicio 13 (ProManage), donde usarás ngrok para compartir APIs con tu equipo!

## Parte 4: Resumen de Seguridad de Webhooks (15 minutos)

Las partes importantes ya las implementaste en la Parte 2. Esta sección las resume como la lista de comprobación que usan las diapositivas, para que puedas aplicarla a cualquier proveedor.

### Tarea 4.1: Las Cuatro Reglas

| Regla | Por qué | Dónde en tu código |
|-------|---------|--------------------|
| **Verificar la firma HMAC sobre el cuerpo en bruto, en tiempo constante** | Cualquiera puede hacer POST a una URL pública; solo GitHub conoce el secreto | `verify_github_signature()` + `request.get_data()` + `hmac.compare_digest` |
| **Responder 2xx rápido, procesar después** | GitHub corta a los 10 s y reintenta | Guardado mínimo + `return ..., 200`; el trabajo real va a una cola |
| **Deduplicar por ID de evento** | Reintentos y reentregas envían el mismo evento otra vez | `X-GitHub-Delivery` + `processed_deliveries` |
| **Usar HTTPS** | Payloads y firmas no deben viajar en claro | URL `https://` de ngrok, SSL verification activada en GitHub |

### Tarea 4.2: Ataca tu Propio Endpoint

Con la app en marcha en local (y el secreto definido), prueba:
1. `python example/send_signed_webhook.py --mode tampered` → **401**
2. `python example/send_signed_webhook.py --mode unsigned` → **401**
3. Para la app, **elimina** la variable (`unset GITHUB_WEBHOOK_SECRET` / `Remove-Item Env:GITHUB_WEBHOOK_SECRET` / `set GITHUB_WEBHOOK_SECRET=`), arráncala de nuevo y envía un webhook válido desde otra terminal → **503**, y el aviso de arranque en la terminal de Flask.
4. Cambia el secreto en GitHub pero no en tu terminal y haz push → GitHub muestra una X roja con **401** en "Recent Deliveries".

### Tarea 4.3: Inspección y Repetición de Peticiones

El panel de ngrok es utilísimo:

1. Abre `http://localhost:4040`
2. Haz un commit para disparar el webhook de GitHub
3. Haz clic en la petición del webhook en el panel
4. Inspecciona:
   - **Headers**: Mira `X-Hub-Signature-256`, `X-GitHub-Delivery` y otras cabeceras de GitHub
   - **Raw payload**: Mira el JSON exacto que envió GitHub (los bytes que cubre la firma)
   - **Tu respuesta**: Confirma que devolviste 200
5. Haz clic en **Replay**: reenvía exactamente la misma petición → tu app responde `"duplicate, ignored"`


## Buenas Prácticas de Seguridad

### ⚠️ Advertencias de Seguridad Importantes

1. **Nunca expongas bases de datos de producción ni datos sensibles**
   - Las URLs de ngrok son públicas: cualquiera puede encontrarlas
   - Las URLs del plan gratuito no están protegidas por autenticación
   - Expón solo entornos de desarrollo/prueba

2. **Las URLs son temporales**
   - Las URLs del plan gratuito cambian cada vez que reinicias ngrok
   - No escribas URLs de ngrok directamente en el código
   - Usa variables de entorno para las URLs

3. **Valida siempre las firmas de los webhooks**
   - Verifica `X-Hub-Signature-256` en **cada** llamada, sobre el cuerpo en bruto, con `hmac.compare_digest`
   - Exige el prefijo `sha256=`
   - Si el secreto no está configurado, rechaza el procesamiento (503); nunca aceptes peticiones sin firmar
   - Consulta la Parte 2 (Tarea 2.3) para la implementación

4. **Deduplica y responde rápido**
   - Usa el ID de evento/entrega del proveedor (`X-GitHub-Delivery`) para ignorar reintentos
   - Responde 2xx rápido y manda el trabajo lento a una cola

5. **Rate limiting**
   - Añade rate limiting para evitar abusos
   - Usa Flask-Limiter (ver Ejercicio 12)

6. **Variables de entorno**
   - Nunca hagas commit de secretos de webhook, URLs de ngrok ni authtokens
   - Genera los secretos con `secrets.token_hex(32)`, nunca con `random` ni `Get-Random`

### Prácticas Recomendadas

```python
import os

@app.route('/webhooks/github', methods=['POST'])
def github_webhook():
    # El secreto sale solo del entorno, nunca del código
    secret = os.environ.get('GITHUB_WEBHOOK_SECRET')
    if not secret:
        return jsonify({'error': 'Webhook secret not configured'}), 503

    signature = request.headers.get('X-Hub-Signature-256')
    if not verify_github_signature(request.get_data(), signature, secret):
        return jsonify({'error': 'Unauthorized'}), 401
    # Deduplicar, guardar lo mínimo, responder 2xx...
```

## Problemas Comunes y Soluciones

### Problema 1: "ERR_NGROK_108 - You must sign up"
**Solución:** Crea una cuenta gratuita en ngrok.com y añade el authtoken

### Problema 2: La URL de ngrok devuelve "Invalid Host header"
**Solución:** Algunos frameworks comprueban la cabecera Host. Con Flask no debería pasar. En otros frameworks, configura los hosts permitidos.

### Problema 3: No puedo acceder desde el móvil
**Solución:**
- Asegúrate de usar la URL HTTPS (no HTTP localhost)
- Comprueba que el móvil tiene conexión a internet
- Prueba primero desde el navegador del móvil

### Problema 4: Connection timed out
**Solución:**
- Asegúrate de que la app Flask está realmente en marcha
- Confirma que ngrok apunta al puerto correcto (5000)
- Revisa la configuración del firewall

### Problema 5: "ERR_NGROK_3200 - Tunnel Limit Reached"
**Solución:** El plan gratuito permite 1 túnel. Cierra los otros procesos de ngrok con `Ctrl+C`

### Problema 6: Todos los webhooks devuelven 401
**Solución:**
- El Secret de GitHub y `GITHUB_WEBHOOK_SECRET` deben ser **idénticos** (sin espacios, sin comillas dentro del valor)
- La variable debe estar definida en la terminal que ejecuta Flask, **antes** de `python app.py`
- Asegúrate de verificar `request.get_data()` (bytes en bruto), no el JSON re-serializado
- Asegúrate de comparar con la parte **después** de `sha256=`

### Problema 7: El webhook devuelve 503
**Solución:** `GITHUB_WEBHOOK_SECRET` no está definida en la terminal de Flask. Defínela (Tarea 2.2) y reinicia la app.

## Lista de Comprobación

**Parte 1: Configuración Básica**
- [ ] ngrok instalado y autenticado
- [ ] La app Flask se ejecuta en localhost:5000
- [ ] ngrok expone la app correctamente
- [ ] URL pública accesible desde el navegador
- [ ] URL pública accesible desde curl
- [ ] El panel de ngrok muestra las peticiones (localhost:4040)

**Parte 2: Webhook Firmado de GitHub**
- [ ] Secreto generado con `secrets.token_hex(32)` y `GITHUB_WEBHOOK_SECRET` definida
- [ ] Completados los 13 huecos de `app.py`
- [ ] `send_signed_webhook.py`: valid → 200, duplicate → "duplicate, ignored", tampered/unsigned/wrong-prefix → 401
- [ ] Repositorio de GitHub creado o elegido
- [ ] Webhook configurado en los ajustes de GitHub (`application/json`, mismo Secret)
- [ ] Evento ping de GitHub recibido correctamente (check verde)
- [ ] Commit hecho para disparar el webhook
- [ ] Webhook recibido y mostrado en la terminal de Flask
- [ ] Vistos los detalles completos del commit en el log
- [ ] Inspeccionados el payload y las cabeceras de firma en el panel de ngrok
- [ ] Repetida una entrega y visto "duplicate, ignored"

**Parte 3: Colaboración en Equipo**
- [ ] URL de ngrok compartida con un compañero
- [ ] API del compañero probada con éxito
- [ ] Usuario creado en la API del compañero
- [ ] Comprobado que un push falso sin firma al webhook de un compañero recibe 401

**Parte 4: Resumen de Seguridad**
- [ ] Sin `GITHUB_WEBHOOK_SECRET` el webhook responde 503 y la app muestra un aviso
- [ ] Un secreto erróneo en GitHub muestra un 401 en "Recent Deliveries"

## Aplicaciones Reales de los Webhooks de GitHub

Ahora que entiendes los webhooks, estos son escenarios reales donde se usan:

### 1. Integración/Despliegue Continuo (CI/CD)
```
El desarrollador hace push → Webhook de GitHub → Tu servidor
                                               ↓
                                       Automáticamente:
                                       - Ejecutar tests
                                       - Compilar la aplicación
                                       - Desplegar si los tests pasan
```

**Herramientas de ejemplo**: Jenkins, GitHub Actions y CircleCI usan webhooks

### 2. Automatización de Gestión de Proyectos
```
Push al repo → Webhook → Actualizar estado del ticket de Jira
                      → Publicar en un canal de Slack
                      → Actualizar el dashboard del proyecto
```

### 3. Flujos de Revisión de Código
```
Pull Request creado → Webhook → Asignar revisores automáticamente
                              → Ejecutar linters
                              → Buscar problemas de seguridad
```

### 4. Generación de Documentación
```
Push a main → Webhook → Regenerar el sitio de documentación
                     → Actualizar la referencia de la API
                     → Desplegar a producción
```

### 5. Notificaciones al Equipo
```
Evento push → Webhook → Enviar notificación a Discord/Slack
                     → Enviar email al equipo
                     → Actualizar el dashboard del equipo
```

### 6. Pagos
```
El cliente paga → Webhook de Stripe (Stripe-Signature) → Marcar el pedido como pagado
                                                       → Enviar el recibo
```
Mismas reglas: verificar la firma, deduplicar por ID de evento, responder 2xx rápido.

**En el Proyecto ProManage (Ejercicio 13):**
Podrías usar webhooks para avisar a los miembros del equipo cuando:
- Se crea una tarea nueva
- Cambia el estado del proyecto
- Se actualizan las asignaciones

## Preparación para el Proyecto en Equipo ProManage

En el Ejercicio 13 (ProManage) trabajarás en equipos donde:
- **Cada miembro desarrolla su propio microservicio**
- **Los servicios necesitan comunicarse entre sí**
- **ngrok te permite compartir tu API sin desplegarla**

Escenario de ejemplo:
- Estudiante A: Servicio de autenticación de usuarios (puerto 5000)
- Estudiante B: Servicio de gestión de proyectos (puerto 5001)
- Estudiante C: Servicio de gestión de tareas (puerto 5002)

Cada uno ejecuta su servicio en local, lo expone con ngrok y comparte las URLs con el equipo.

```bash
# Servicio de autenticación del Estudiante A
ngrok http 5000
# Compartir: https://student-a.ngrok-free.app

# Servicio de proyectos del Estudiante B
ngrok http 5001
# Compartir: https://student-b.ngrok-free.app

# El Estudiante C ya puede llamar a ambos servicios:
curl https://student-a.ngrok-free.app/login -d '{"username":"test","password":"pass"}'
curl https://student-b.ngrok-free.app/projects -H "Authorization: Bearer <token>"
```

**¡Este ejercicio te prepara exactamente para este flujo de trabajo!**

## Recursos Adicionales

### Documentación Oficial
- **[Documentación de ngrok](https://ngrok.com/docs)** - Referencia completa de ngrok
- **[ngrok Getting Started](https://ngrok.com/docs/getting-started)** - Guía de inicio rápido (2025)
- **[Webhooks de GitHub](https://docs.github.com/en/webhooks/webhook-events-and-payloads)** - Documentación oficial de webhooks
- **[Crear Webhooks de GitHub](https://docs.github.com/en/webhooks/using-webhooks/creating-webhooks)** - Guía de configuración

### Tutoriales
- [Integración ngrok + Flask](https://ngrok.com/docs/integrations/python/flask) - Guía oficial para Flask
- [Validar entregas de webhooks de GitHub](https://docs.github.com/en/webhooks/using-webhooks/validating-webhook-deliveries) - Verificación de firmas
- [Buenas prácticas de webhooks (GitHub)](https://docs.github.com/en/webhooks/using-webhooks/best-practices-for-using-webhooks) - Responder rápido, gestionar reentregas
- [Stripe: verificar firmas de webhooks](https://docs.stripe.com/webhooks#verify-events) - La misma idea con `Stripe-Signature`
- [Probar webhooks en local](https://ngrok.com/docs/guides/webhooks/local-testing) - Buenas prácticas de desarrollo

### Herramientas Alternativas (como referencia)
- [localtunnel](https://localtunnel.me/) - Alternativa de código abierto
- [Cloudflare Tunnel](https://www.cloudflare.com/products/tunnel/) - URLs gratuitas y permanentes
- [Hookdeck](https://hookdeck.com/) - Plataforma de pruebas de webhooks

## Entregables

Al completar este ejercicio deberías tener:

1. **Configuración de ngrok**:
   - ngrok instalado y autenticado
   - API Flask expuesta correctamente con una URL pública

2. **Webhook Real y Firmado de GitHub**:
   - Repositorio de GitHub con el webhook configurado (`application/json`, Secret definido)
   - App Flask recibiendo eventos push reales
   - TODOs de `app.py` completados: verificación de firma, deduplicación y manejo del payload

3. **Evidencias** (capturas o documentación):
   - Terminal de ngrok mostrando la URL pública
   - Página de ajustes del webhook en GitHub mostrando el webhook activo con check verde
   - Terminal de Flask mostrando el webhook recibido con los detalles del commit
   - Salida de `send_signed_webhook.py` mostrando 200 / "duplicate, ignored" / 401
   - Panel de ngrok (localhost:4040) mostrando la petición del webhook de GitHub y su cabecera de firma

4. **Colaboración en Equipo**:
   - API compartida con éxito con un compañero
   - Endpoints de la API de un compañero probados

## Criterios de Evaluación

Tu trabajo se evaluará según:

1. **Configuración de ngrok** (15%):
   - ngrok bien instalado y autenticado
   - App Flask expuesta correctamente con una URL pública

2. **Webhook Real de GitHub** (30%):
   - Webhook de GitHub bien configurado
   - El endpoint Flask maneja correctamente los payloads reales de GitHub
   - Recibe y procesa eventos push con éxito
   - Extracción correcta de repository, pusher, commits y ref

3. **Seguridad del Webhook** (25%):
   - HMAC-SHA256 verificado sobre el cuerpo en bruto con `hmac.compare_digest`, prefijo `sha256=` obligatorio
   - Peticiones sin firmar, manipuladas o con prefijo incorrecto rechazadas con 401
   - Sin secreto configurado → el endpoint se niega a procesar (503)
   - Las entregas duplicadas no se guardan dos veces

4. **Calidad del Código** (15%):
   - Todos los TODOs completados correctamente
   - El código sigue los patrones establecidos
   - Manejo de errores adecuado

5. **Colaboración en Equipo** (10%):
   - API compartida con éxito con un compañero
   - Endpoints de la API del compañero probados

6. **Documentación/Evidencias** (5%):
   - Capturas o notas claras que muestren entregas de webhook correctas
   - Evidencias de pruebas y verificación

## Siguientes Pasos

Después de completar este ejercicio:

1. **Ejercicio 12**: Documentación con Swagger - Documenta tus APIs de forma profesional
2. **Ejercicio 13**: Proyecto en Equipo ProManage - Usa ngrok para colaborar en equipo
3. **Más allá**: Aprende sobre despliegue en producción (Heroku, AWS, Docker) para aplicaciones reales

**Nota**: ngrok es solo para desarrollo/pruebas. Las apps de producción deben desplegarse correctamente.

## Preguntas para Reflexionar

1. ¿Por qué no puedes usar URLs `localhost` para webhooks de servicios externos?
2. ¿Qué implicaciones de seguridad tiene exponer tu servidor de desarrollo?
3. ¿Cuándo usarías ngrok y cuándo un despliegue real (Heroku, AWS, etc.)?
4. ¿Por qué hay que calcular el HMAC sobre el cuerpo en bruto y no sobre el JSON parseado?
5. ¿Por qué `hmac.compare_digest` en lugar de `==`?
6. ¿Qué pasaría con tus datos si no deduplicaras por `X-GitHub-Delivery` y GitHub reintentara una entrega?
7. ¿Qué pasa si tu túnel de ngrok se desconecta durante el proyecto ProManage?

¡Buena suerte exponiendo tus APIs al mundo! 🚀
