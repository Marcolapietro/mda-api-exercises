# Exercise 14: OAuth Authentication with GitHub (Authorization Code + PKCE)

## Objective

Learn how to implement **OAuth authentication** in a Flask REST API by integrating with a third-party provider (GitHub), using the flow that current best practice (RFC 9700, OAuth 2.1) recommends for every client: **Authorization Code + PKCE**. Understand the OAuth flow, handle redirects and callbacks, identify users by the provider's stable id, and combine OAuth with JWT for API authentication.

## Quick Start

```bash
cd exercises/14-oauth
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
# Configure GitHub OAuth App (see Setup section below)
python app.py
```

---

## What is OAuth 2.0?

**OAuth 2.0** is an authorization framework that enables applications to obtain limited access to user accounts on third-party services (like GitHub, Google, Facebook) **without exposing passwords**.

> **OAuth 2.0 vs OAuth 2.1:** OAuth 2.0 (RFC 6749, 2012) is the published standard. Since then, security
> experience has been collected in **RFC 9700** (OAuth 2.0 Security Best Current Practice, 2025), and the
> **OAuth 2.1** draft consolidates it: Authorization Code **always with PKCE**, and the Implicit and Password
> grants removed. This exercise follows that modern profile (see "Understanding OAuth Flows" below).

### Real-World Examples

You've probably used OAuth many times:
- **"Sign in with Google"** on websites
- **"Continue with Facebook"** on mobile apps
- **GitHub CLI authentication** (`gh auth login`)
- **Spotify** connecting to Last.fm
- **Mobile apps** accessing your Google Drive

### Why OAuth Over Traditional Login?

| Feature | Traditional Login | OAuth 2.0 |
|---------|------------------|-----------|
| **Password storage** | Your app stores passwords | No passwords stored |
| **User trust** | Users create new account | Users trust GitHub/Google |
| **Account management** | You handle password resets | Provider handles it |
| **Security** | You're responsible for breaches | Provider's security team |
| **User convenience** | Another password to remember | Single sign-on (SSO) |
| **Profile data** | User manually enters | Auto-populated from provider |

---

## Prerequisites

Before starting this exercise, complete:
- **Exercise 06**: JWT Authentication (this exercise combines OAuth + JWT)
- **Exercise 04**: Basic Authentication (understanding auth concepts)

---

## What You'll Learn

1. **OAuth Authorization Code Flow with PKCE** (the recommended flow for every client)
2. **Third-party integration** with GitHub OAuth
3. **Redirect handling** and callback URLs
4. **Token exchange** (authorization code → access token)
5. **API consumption** using OAuth access tokens
6. **Combining OAuth with JWT** for stateless API authentication
7. **Session management** in OAuth flows
8. **Security best practices** (PKCE, state parameter, HTTPS, secrets, stable user ids)

---

## How OAuth 2.0 Works

### The OAuth Actors

```
┌──────────────┐
│   User       │  (The person using the app)
│  (You)       │
└──────────────┘
       │
       │ Wants to use
       ▼
┌──────────────┐         ┌──────────────┐         ┌──────────────┐
│    Client    │◄───────►│ Authorization│◄───────►│   Resource   │
│     App      │         │    Server    │         │    Server    │
│ (Your Flask) │         │  (GitHub)    │         │  (GitHub API)│
└──────────────┘         └──────────────┘         └──────────────┘
```

- **User**: The person trying to log in
- **Client (Your App)**: Your Flask application
- **Authorization Server**: GitHub's OAuth service (issues tokens)
- **Resource Server**: GitHub's API (provides user data)

### OAuth Authorization Code Flow (Step-by-Step)

```
1. User clicks "Login with GitHub"
   ┌──────┐
   │ User │──── Clicks button ────┐
   └──────┘                        ▼
                            ┌─────────────┐
                            │  Your App   │
                            │ /login/github│
                            └─────────────┘
                                   │
                                   │ Creates code_verifier (kept secret)
                                   │ Redirects to GitHub with
                                   │ code_challenge = SHA-256(verifier)
                                   ▼
2. User authorizes on GitHub
   ┌──────────────────────────────────┐
   │  GitHub Authorization Page       │
   │                                  │
   │  [App Name] wants to access:     │
   │  ☑ Read your profile             │
   │  ☑ Read your email               │
   │                                  │
   │  [Authorize] [Cancel]            │
   └──────────────────────────────────┘
                  │
                  │ User clicks Authorize
                  ▼
3. GitHub redirects back with authorization code
   ┌──────────────┐
   │   GitHub     │──── Redirect to callback ────┐
   └──────────────┘                               │
        URL: http://yourapp.com/callback?code=abc123
                                                   ▼
                                          ┌─────────────┐
                                          │  Your App   │
                                          │  /callback  │
                                          └─────────────┘
                                                   │
4. Your app exchanges code for access token       │
                                                   │
   POST https://github.com/login/oauth/access_token
   {
     client_id: "your_client_id",
     client_secret: "your_client_secret",
     code: "abc123",
     code_verifier: "dBjftJeZ4CVP..."   ← PKCE
   }
   GitHub checks SHA-256(code_verifier) == code_challenge
                  │
                  ▼
   Response: { access_token: "gho_xxxx..." }
                  │
                  │
5. Your app fetches user profile                  │
                                                   │
   GET https://api.github.com/user                │
   Authorization: Bearer gho_xxxx...              │
                  │                                │
                  ▼                                │
   Response: {                                     │
     id: 12345678,      ← stable, never changes    │
     login: "alice",    ← can be renamed           │
     email: "alice@example.com",                   │
     name: "Alice Smith"                           │
   }                                               │
                  │                                │
                  │                                │
6. Your app creates JWT token                     │
                  │                                │
   jwt_token = create_access_token(identity="12345678")
                  │                                │
                  ▼                                │
   ┌─────────────────────────────────┐             │
   │  Return JWT to user             │◄────────────┘
   │  { access_token: "eyJ..." }     │
   └─────────────────────────────────┘
                  │
                  │
7. User uses JWT for future requests
                  │
   GET /profile
   Authorization: Bearer eyJ...
```

**Key Points:**
- Authorization code is **temporary** and **single-use**
- Authorization code must be exchanged on **server-side** (never client-side JavaScript)
- Client secret **never leaves your server**
- User's GitHub password **never touches your app**
- With **PKCE**, a stolen code cannot be exchanged without the `code_verifier`
- Users are identified by GitHub's numeric **`id`**, not by `login` (see below)

### PKCE: Proof Key for Code Exchange (always on in this exercise)

The flow above has one weak spot: the **authorization code** travels through the browser (step 3). If an
attacker steals it (a malicious app registered for the same redirect, a leaked log, browser history...), they
could try to exchange it for a token. **PKCE** (RFC 7636, pronounced "pixy") closes that gap: only the app that
*started* the login can finish it.

The current best practice ([RFC 9700](https://datatracker.ietf.org/doc/rfc9700/), OAuth 2.0 Security Best
Current Practice, and the OAuth 2.1 draft) is **Authorization Code + PKCE for every client**: server-side apps
like this one, SPAs and mobile apps. For a confidential client like our Flask app, PKCE is used **in addition
to** the client secret, not instead of it. GitHub supports PKCE with `S256`.

**The 6 steps (as in the slides):**

```
 Your Flask app                          Browser / User                 GitHub (authorization server)
 ──────────────                          ──────────────                 ─────────────────────────────
 1. Create a random code_verifier
    code_challenge = BASE64URL(SHA-256(code_verifier))
    (keep the verifier in the session, never in a URL)
 2. Redirect ─────────────────────────►  /login/oauth/authorize
                                         ?code_challenge=...&code_challenge_method=S256
                                         &state=...&redirect_uri=...   ──────────────►  stores the challenge
 3.                                      User logs in and authorizes   ◄─────────────►
 4. /callback?code=...&state=...  ◄────  GitHub redirects back with the code  ◄───────
 5. POST /login/oauth/access_token
    code + code_verifier (+ client_id, client_secret, redirect_uri)  ─────────────────►
 6.                                                                   checks SHA-256(code_verifier)
                                                                      == stored code_challenge
    ◄─────────────────────────────────────────────── access_token  (only if they match)
```

1. **Verifier and challenge created:** the app generates a random `code_verifier` (43-128 characters) and computes `code_challenge = BASE64URL(SHA-256(code_verifier))`.
2. **Redirect with the challenge:** the authorize URL carries `code_challenge` and `code_challenge_method=S256` (and `state`). Only the hash leaves the app.
3. **Login:** the user signs in on GitHub and authorizes the app.
4. **Code back:** GitHub redirects to `/callback` with a short-lived, single-use `code` (and the same `state`).
5. **Code + verifier:** the app sends the `code` **and the original `code_verifier`** to the token endpoint.
6. **The server checks:** GitHub computes `SHA-256(code_verifier)` and compares it with the challenge it stored in step 2. If they don't match, no token. A stolen code is useless without the verifier, and the verifier is never sent in a URL: whoever intercepts the redirect gets the code, not the verifier.

**With Authlib it is one setting** in `client_kwargs`, already present in `app.py`:

```python
github = oauth.register(
    name='github',
    # ... client_id, client_secret, URLs ...
    client_kwargs={'scope': 'user:email', 'code_challenge_method': 'S256'},
)
```

With that setting, Authlib does steps 1, 2 and 5 for you: `authorize_redirect()` generates the `code_verifier`,
keeps it in the session and adds `code_challenge` + `code_challenge_method=S256` to the redirect;
`authorize_access_token()` reads it back and sends `code_verifier` in the token request. Your `/login/github`
and `/callback` code doesn't change.

**What Authlib computes for you** (to understand it, not needed in the app):

```python
import base64, hashlib, secrets

code_verifier = secrets.token_urlsafe(48)
code_challenge = base64.urlsafe_b64encode(
    hashlib.sha256(code_verifier.encode()).digest()
).rstrip(b'=').decode()
```

> Common mistake: sending the `code_verifier` itself as the `code_challenge` (that is the `plain` method). With
> `S256` the challenge must be the hash; otherwise the server rejects the exchange. Always use `S256`.

> **Where does Authlib keep the verifier?** In the Flask `session`. Flask's default session is a signed cookie in
> the user's own browser (see "Session vs JWT" below), so the verifier never appears in URLs, logs or the
> `Referer` header, which is where codes leak. In production you can pass a server-side `cache` to `OAuth(app, cache=...)`
> so that the OAuth state data stays on the server.

**`state` and PKCE are complementary:** `state` (a random value Authlib stores in the session and checks on
`/callback`) protects **your user** against CSRF, i.e. being logged in with someone else's code. PKCE protects the
**code** against being redeemed by someone else. Keep both.

---

## Setup Instructions

### Part 1: Create a GitHub OAuth App

1. **Go to GitHub Developer Settings:**
   - Visit: https://github.com/settings/developers
   - Click **"OAuth Apps"** → **"New OAuth App"**

2. **Fill in the form:**
   ```
   Application name: Flask OAuth Exercise
   Homepage URL: http://127.0.0.1:5000
   Authorization callback URL: http://127.0.0.1:5000/callback
   ```

   > **Use `127.0.0.1` everywhere, not `localhost`.** The app builds its `redirect_uri` from the
   > host you typed in the browser (`url_for('callback', _external=True)`). If you open
   > `http://localhost:5000/login/github`, the app sends `redirect_uri=http://localhost:5000/callback`,
   > and GitHub compares it **character by character** with the registered callback URL, so it rejects it
   > ("redirect_uri MUST match"). The browser also treats `localhost` and `127.0.0.1` as different
   > sites, so the session cookie that holds the OAuth `state` would not be sent back to the other one.
   > Always start the flow at **http://127.0.0.1:5000/login/github**.

3. **Register the app:**
   - Click **"Register application"**
   - You'll see:
     - **Client ID**: `Iv1.abc123def456...` (public, safe to commit)
     - **Client Secret**: `1a2b3c4d5e6f...` (secret, never commit!)

4. **Save your credentials:**
   - Copy the **Client ID**
   - Click **"Generate a new client secret"**
   - Copy the **Client Secret** (you can only see it once!)

### Part 2: Configure Your App

The app reads the credentials **only from environment variables** (`GITHUB_CLIENT_ID` and
`GITHUB_CLIENT_SECRET`). Do **not** paste them into `app.py`: anything in the code ends up in Git.
If either variable is missing, the app stops at startup with a `Missing GITHUB_CLIENT_ID ...` message.

Set them **in the same terminal** where you will run `python app.py` (they only last for that terminal session):

```bash
# Linux / macOS (bash, zsh)
export GITHUB_CLIENT_ID="Iv1.abc123..."
export GITHUB_CLIENT_SECRET="1a2b3c4d..."
```

```powershell
# Windows PowerShell
$env:GITHUB_CLIENT_ID="Iv1.abc123..."
$env:GITHUB_CLIENT_SECRET="1a2b3c4d..."
```

```bat
:: Windows CMD (no quotes, no spaces around =)
set GITHUB_CLIENT_ID=Iv1.abc123...
set GITHUB_CLIENT_SECRET=1a2b3c4d...
```

Then start the app and open **http://127.0.0.1:5000/login/github** in the browser.

The `.env.example` file at the root of the repo lists every variable the exercises use
(`GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET`, and optionally `FLASK_SECRET_KEY` and `JWT_SECRET_KEY`).
It is only a reference: the app does **not** load it automatically, so you still need to set the
variables with the commands above. If `FLASK_SECRET_KEY` / `JWT_SECRET_KEY` are not set, the app
generates random ones at startup (tokens stop working when you restart it).

This is how the app uses them:

```python
client_id=os.environ['GITHUB_CLIENT_ID'],
client_secret=os.environ['GITHUB_CLIENT_SECRET'],
```

---

## API Structure

### Public Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API information and instructions |
| GET | `/login/github` | Initiate GitHub OAuth flow |
| GET | `/callback` | OAuth callback (automatic redirect) |
| POST | `/logout` | Clear session (logout) |

### Protected Endpoints (JWT Required)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/profile` | JWT | Get current user's profile |
| GET | `/users` | JWT | List all registered users |

---

## Implementation Guide

### TODOs in app.py

You need to fill in **8 blanks** (`_____`). The secrets (`app.secret_key`, `client_id`,
`client_secret`) are **not** blanks: they are read from environment variables (see Part 2).

| # | Where (function / section) | What to write |
|---|----------------------------|---------------|
| 1 | `oauth.register(...)` (line 32) | Provider name: `'github'` |
| 2 | `login_github()` (line 94) | Endpoint for the callback URL: `url_for('callback', _external=True)` |
| 3 | `login_github()` (line 98) | Redirect to GitHub: `github.authorize_redirect(redirect_uri)` |
| 4 | `callback()` (line 120) | Exchange the code (+ PKCE verifier) for a token: `github.authorize_access_token()` |
| 5 | `callback()` (line 124) | GitHub API endpoint for the profile: `github.get('user')` |
| 6 | `callback()` (line 152) | Create our JWT: `create_access_token(identity=user_id)` |
| 7 | `@app.route('/profile', ...)` (line 175) | HTTP method: `'GET'` |
| 8 | `profile()` (line 191) | Read the user from the JWT: `get_jwt_identity()` |

PKCE (`'code_challenge_method': 'S256'`) and the user id (`user_id = str(github_id)`) are already written in
`app.py`: they are not blanks, but read them, they are what makes the flow secure (see "PKCE" above and
"Handling the Callback" below).

(Line numbers refer to the original `app.py`; search for `_____` if they have shifted.)

### Key Concepts to Implement

#### 1. OAuth Provider Registration

**What is Authlib?**
- **Authlib** is the most popular OAuth library for Flask
- Handles OAuth 1.0, OAuth 2.0, and OpenID Connect
- Simplifies token exchange, API calls, and session management

**Registering a provider:**
```python
from authlib.integrations.flask_client import OAuth

oauth = OAuth(app)

github = oauth.register(
    name='github',  # Internal name for this provider
    client_id='...',  # From GitHub OAuth App
    client_secret='...',  # From GitHub OAuth App
    access_token_url='https://github.com/login/oauth/access_token',
    authorize_url='https://github.com/login/oauth/authorize',
    api_base_url='https://api.github.com/',
    client_kwargs={
        'scope': 'user:email',            # Permissions requested
        'code_challenge_method': 'S256',  # PKCE on (OAuth 2.1 / RFC 9700)
    }
)
```

**OAuth Scopes:**
- Scopes define what your app can access
- GitHub scopes: `user`, `user:email`, `repo`, `read:org`, etc.
- Users see requested scopes on authorization page
- Request **minimal scopes** needed (security best practice)

#### 2. Initiating the OAuth Flow

```python
@app.route('/login/github')
def login_github():
    # Generate the callback URL (where GitHub redirects back)
    redirect_uri = url_for('callback', _external=True)
    # Result: "http://127.0.0.1:5000/callback"

    # Redirect user to GitHub's authorization page
    return github.authorize_redirect(redirect_uri)
```

**What happens behind the scenes:**
1. `authorize_redirect()` builds a URL like:
   ```
   https://github.com/login/oauth/authorize
     ?client_id=Iv1.abc123
     &redirect_uri=http://127.0.0.1:5000/callback
     &scope=user:email
     &state=random_csrf_token
     &code_challenge=E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM
     &code_challenge_method=S256
   ```
2. User is redirected to GitHub
3. GitHub shows authorization prompt
4. User clicks "Authorize"
5. GitHub redirects back to your `redirect_uri` with a code

**Why `_external=True`?**
- Generates absolute URL (`http://127.0.0.1:5000/callback`)
- Without it: relative URL (`/callback`) which GitHub can't redirect to
- OAuth requires **absolute URLs** for callbacks

#### 3. Handling the Callback

```python
@app.route('/callback')
def callback():
    # Step 1: Exchange authorization code for access token
    token = github.authorize_access_token()
    # Behind the scenes: checks state, then POST to GitHub with
    # code + code_verifier (PKCE) + client_secret
    # Returns: { "access_token": "gho_xxxx...", "scope": "user:email", ... }

    # Step 2: Use access token to fetch user profile
    response = github.get('user')  # GET https://api.github.com/user
    user_info = response.json()

    # Step 3: Extract user data
    github_id = user_info.get('id')        # 12345678 - stable, never changes
    username = user_info.get('login')      # "alice"  - can be renamed
    email = user_info.get('email')
    name = user_info.get('name')

    # Step 4: Store (or update) the user, keyed by the stable id
    user_id = str(github_id)
    users[user_id] = {'github_id': github_id, 'username': username, ...}

    # Step 5: Create JWT token for your API (sub = the id, as a string)
    access_token = create_access_token(identity=user_id)

    return jsonify({'access_token': access_token})
```

**Why the `id` and not the `login`?**
- On GitHub you can **rename your account**: `login` changes, `id` never does. If we keyed users by `login`, a
  rename would create a "new" user and orphan the old data.
- Worse: after a rename, the old `login` becomes **free**, and someone else can register it. If our database
  were keyed by `login`, that person would inherit the previous owner's account in our app.
- So the **identity** is the provider's stable id (`sub` in OpenID Connect, `id` in GitHub's API); `login`, name and
  avatar are just **display attributes** that we refresh on every login.
- The JWT `sub` claim must be a **string** (PyJWT rejects non-string subjects), so we use `str(github_id)`.

**Why two tokens?**
- **OAuth access token** (`gho_xxxx`): Used to call **GitHub API**
- **JWT token** (`eyJ...`): Used to call **your API**
- We don't store the GitHub token (we only needed it to get user profile)

#### 4. Combining OAuth with JWT

**Why use JWT after OAuth?**
1. **Stateless authentication**: No need to store GitHub tokens
2. **Performance**: Don't call GitHub API on every request
3. **Standardization**: Same auth pattern as Exercise 06
4. **Flexibility**: Works with multiple OAuth providers

**Pattern:**
```
OAuth (one-time)        JWT (every request)
─────────────────       ───────────────────
GitHub login            Your API calls
    ↓                       ↓
User profile            Stateless auth
    ↓                       ↓
Create JWT   ─────────►  Use JWT token
```

#### 5. Session Management

```python
# Flask sessions are needed for OAuth state management
app.secret_key = os.environ.get('FLASK_SECRET_KEY') or secrets.token_hex(32)

# Authlib stores temporary OAuth data in session:
# - state (CSRF protection)
# - code_verifier (PKCE - kept here, never sent in a URL)
# - redirect_uri (validation)

# After successful OAuth, session can be cleared
@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'message': 'Logged out'})
```

**Session vs JWT:**
- **Session**: Temporary, OAuth flow only. Flask's default session is a **signed cookie stored in the
  browser** (client-side): `secret_key` prevents tampering, but the content is only base64-encoded, not
  encrypted, so never put secrets in it.
- **JWT**: Short-lived (the solution uses `JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)`), sent by the
  client in the `Authorization` header, API authentication

---

## Testing the API

### Method 1: Browser Testing (Easiest)

1. **Start the server:**
   ```bash
   python app.py
   ```

2. **Open browser:**
   - Go to: http://127.0.0.1:5000/login/github

3. **Authorize with GitHub:**
   - Click "Authorize [Your App Name]"
   - You'll be redirected to `/callback`
   - Copy the `access_token` from the JSON response

4. **Use the token in Postman/curl:**
   ```bash
   curl http://127.0.0.1:5000/profile \
     -H "Authorization: Bearer <YOUR_JWT_TOKEN>"
   ```

### Method 2: Postman Testing

**Step 1: Initiate OAuth (in browser)**
- Since OAuth requires redirects, start the flow in a browser
- Visit: http://127.0.0.1:5000/login/github
- Authorize and copy the JWT token

**Step 2: Test protected endpoints (in Postman)**

**Get your profile:**
```
GET http://127.0.0.1:5000/profile
Headers:
  Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Expected response:**
```json
{
  "user_id": "12345678",
  "username": "your-github-username",
  "profile": {
    "github_id": 12345678,
    "username": "your-github-username",
    "email": "you@example.com",
    "name": "Your Name",
    "avatar_url": "https://avatars.githubusercontent.com/u/12345678"
  }
}
```

**Get all users:**
```
GET http://127.0.0.1:5000/users
Headers:
  Authorization: Bearer eyJ...
```

**Expected response:**
```json
{
  "users": [
    {"id": "12345678", "username": "alice"},
    {"id": "23456789", "username": "bob"}
  ],
  "count": 2
}
```

### Method 3: curl Testing

**Note:** OAuth redirects don't work well with curl. Use browser to get JWT, then:

```bash
# Save your JWT token
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# Get your profile
curl http://127.0.0.1:5000/profile \
  -H "Authorization: Bearer $TOKEN"

# Get all users
curl http://127.0.0.1:5000/users \
  -H "Authorization: Bearer $TOKEN"

# Logout
curl -X POST http://127.0.0.1:5000/logout
```

---

## Understanding OAuth Flows

### OAuth Grant Types Today (OAuth 2.1 / RFC 9700)

OAuth 2.0 (RFC 6749, 2012) defined several grant types. Years of attacks showed which ones are safe, and the
current guidance consolidates them:

| Grant Type | Use Case | Status |
|------------|----------|--------|
| **Authorization Code + PKCE** | **Every client** where a user logs in: server-side web apps, SPAs, mobile and desktop apps | ✅ Recommended choice |
| **Client Credentials** | Machine-to-machine: a service calling another service, no user involved | ✅ Use for M2M |
| **Device Authorization (Device Code)** | Devices with no browser or keyboard: smart TVs, CLIs (e.g. `gh auth login`) | ✅ Use for TVs / CLIs |
| **Refresh Token** | Getting a new access token without asking the user again | ✅ Alongside the above |
| ~~Implicit~~ | (was: SPAs) | ❌ **Removed in OAuth 2.1**: the access token is returned in the URL fragment, where browser history, extensions and logs can leak it, and it cannot be bound to the client |
| ~~Resource Owner Password~~ | (was: "trusted" first-party apps) | ❌ **Removed in OAuth 2.1**: the app receives the user's password, which is exactly what OAuth exists to avoid, and it cannot support MFA or SSO |

**This exercise uses Authorization Code + PKCE**, the recommended choice.

> **Status of the documents:** OAuth 2.1 is still an **IETF draft** (draft-ietf-oauth-v2-1), not a published RFC.
> The current, published best-practice document is **RFC 9700** ("OAuth 2.0 Security Best Current Practice",
> January 2025). OAuth 2.1 mostly bundles RFC 6749 + RFC 7636 (PKCE) + RFC 9700 into one spec, so following
> RFC 9700 today means you are already OAuth 2.1-ready.

### Why Authorization Code (+ PKCE) is the Safe Choice

```
❌ Implicit Flow (removed):
GitHub → Browser → App
         ↑
      Access token in URL (visible to browser, extensions, history)

✅ Authorization Code + PKCE (this exercise):
GitHub → Browser → App
         ↑          ↓
      Code only   Server exchanges code + code_verifier for token
                  (Token never touches browser; a stolen code is useless)
```

**Benefits:**
- Client secret never exposed to browser
- Access token never in URL (not logged, not in history)
- Code is single-use and short-lived
- Server-to-server token exchange
- PKCE binds the code to the app that started the flow

---

## Security Best Practices

### ✅ DO

1. **Use HTTPS in production**
   - OAuth tokens can be intercepted on HTTP
   - GitHub rejects non-HTTPS callbacks in production

2. **Store secrets securely**
   ```python
   # ❌ Bad: Hardcoded secrets
   client_secret = "abc123"

   # ✅ Good: Environment variables
   client_secret = os.getenv('GITHUB_CLIENT_SECRET')
   ```

3. **Validate redirect URIs**
   - Register **exact** callback URLs with GitHub
   - GitHub rejects mismatched URLs (security feature)

4. **Use state parameter** (Authlib does this automatically)
   - Protects against CSRF attacks
   - Random value verified on callback

5. **Use PKCE with S256** (`'code_challenge_method': 'S256'`)
   - Recommended for every client (RFC 9700, OAuth 2.1)
   - A stolen authorization code is useless without the `code_verifier`

6. **Identify users by the provider's stable id**
   - GitHub `id` (or OIDC `sub`), never the `login`/email, which can change or be reassigned

7. **Request minimal scopes**
   ```python
   # ❌ Bad: Requesting unnecessary permissions
   client_kwargs={'scope': 'user repo delete_repo admin:org'}

   # ✅ Good: Only what you need
   client_kwargs={'scope': 'user:email'}
   ```

8. **Validate tokens**
   - Check token expiration
   - Verify token signature (JWT does this)

9. **Handle errors gracefully**
   ```python
   try:
       token = github.authorize_access_token()
   except Exception as e:
       return jsonify({'error': 'OAuth failed'}), 400
   ```

### ❌ DON'T

1. **Don't commit client secrets**
   ```bash
   # Add to .gitignore
   .env
   config.py
   ```

2. **Don't use the Implicit or Password grants** (removed in OAuth 2.1)
   - Implicit puts the access token in the URL; Password hands the user's password to your app
   - Use Authorization Code + PKCE instead, for SPAs and mobile apps too

3. **Don't skip HTTPS** in production
   - Development (localhost): HTTP is fine
   - Production: HTTPS is mandatory

4. **Don't store OAuth access tokens** (unless needed)
   - If you only need user profile once, don't store it
   - If you need ongoing GitHub API access, store securely

5. **Don't trust user input**
   - Validate `state` parameter
   - Sanitize user profile data

---

## Common Issues and Solutions

### Issue 1: "Redirect URI Mismatch"

**Symptom:**
```
GitHub error: The redirect_uri MUST match the registered callback URL for this application.
```

**Solution:**
- Check GitHub OAuth App settings
- Callback URL must **exactly** match: `http://127.0.0.1:5000/callback`
- Start the flow at `http://127.0.0.1:5000/login/github` (the app builds `redirect_uri` from the host you used)
- Common mistakes:
  - `http://localhost:5000/callback` ≠ `http://127.0.0.1:5000/callback` (GitHub compares the exact string,
    and the browser treats them as different sites)
  - `https://` vs `http://`
  - Trailing slash: `/callback/` vs `/callback`

### Issue 2: "Client ID or Secret Invalid"

**Symptom:**
```json
{
  "error": "invalid_client",
  "error_description": "The client credentials are invalid"
}
```

**Solution:**
- Verify Client ID copied correctly
- Regenerate Client Secret if lost (can only view once)
- Check for extra spaces when pasting
- Ensure you're using the right GitHub OAuth App

### Issue 3: "Session Error"

**Symptom:**
```
RuntimeError: The session is unavailable because no secret key was set.
```

**Solution:**
```python
# Add this to your app
app.secret_key = os.environ.get('FLASK_SECRET_KEY') or secrets.token_hex(32)
```

### Issue 4: "OAuth Callback Never Happens"

**Symptom:**
- Stuck on GitHub authorization page
- Callback endpoint never receives request

**Solution:**
- Check Flask is running: http://127.0.0.1:5000
- Check no firewall blocking port 5000
- Verify callback URL in GitHub settings
- Check browser console for errors

### Issue 5: "Email is None"

**Symptom:**
```json
{
  "email": null
}
```

**Solution:**
- GitHub only returns email if you requested `user:email` scope
- User might have private email settings
- Fetch email separately: `github.get('user/emails')`

```python
# Get primary email if not public
if not email:
    emails_response = github.get('user/emails')
    emails = emails_response.json()
    primary_email = next((e['email'] for e in emails if e['primary']), None)
```

---

## Acceptance Criteria

Your implementation should:

- ✅ Register GitHub as OAuth provider with Authlib, with PKCE (`code_challenge_method='S256'`)
- ✅ Redirect to GitHub authorization page (with `state`, `code_challenge` and `code_challenge_method=S256`)
- ✅ Handle OAuth callback with authorization code
- ✅ Exchange code + `code_verifier` for access token (server-side)
- ✅ Fetch user profile from GitHub API
- ✅ Store user in database keyed by GitHub's numeric `id` (`login` only as display attribute)
- ✅ Generate JWT token after successful OAuth, with `sub` = the GitHub id as a string
- ✅ Protect routes with `@jwt_required()` decorator
- ✅ Use JWT for subsequent API requests
- ✅ Handle OAuth errors gracefully
- ✅ Clear session on logout

---

## Stretch Goals

Once you complete the basic implementation:

### 1. Add Multiple OAuth Providers

Support Google, Facebook, or Twitter:

```python
# Google OAuth
google = oauth.register(
    name='google',
    client_id=os.getenv('GOOGLE_CLIENT_ID'),
    client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

@app.route('/login/google')
def login_google():
    redirect_uri = url_for('google_callback', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/callback/google')
def google_callback():
    token = google.authorize_access_token()
    user_info = token['userinfo']  # OpenID Connect
    # ... create JWT
```

### 2. Implement Token Refresh

Store OAuth refresh tokens for long-term API access:

```python
# When storing user
users[user_id] = {
    'github_id': github_id,
    'access_token': token['access_token'],
    'refresh_token': token.get('refresh_token'),
    'expires_at': token.get('expires_at')
}

# Refresh when expired
if datetime.now().timestamp() > user['expires_at']:
    new_token = github.fetch_access_token(
        refresh_token=user['refresh_token']
    )
    users[user_id]['access_token'] = new_token['access_token']
```

### 3. Add OAuth Scopes Management

Let users choose what permissions to grant:

```python
@app.route('/login/github/full')
def login_github_full():
    # Request additional scopes
    redirect_uri = url_for('callback', _external=True)
    return github.authorize_redirect(
        redirect_uri,
        scope='user:email read:org repo'  # More permissions
    )
```

### 4. Implement Account Linking

Allow users to link multiple OAuth providers:

```python
users = {
    '12345678': {  # our user id
        'primary_email': 'alice@example.com',
        'oauth_providers': {
            'github': {'id': 12345, 'username': 'alice'},
            'google': {'id': 67890, 'email': 'alice@gmail.com'}
        }
    }
}

@app.route('/link/github')
@jwt_required()
def link_github():
    current_user = get_jwt_identity()
    redirect_uri = url_for('link_callback', _external=True)
    return github.authorize_redirect(redirect_uri)

@app.route('/link/callback')
@jwt_required()
def link_callback():
    current_user = get_jwt_identity()
    token = github.authorize_access_token()
    user_info = github.get('user').json()

    # Add GitHub to existing user
    if 'oauth_providers' not in users[current_user]:
        users[current_user]['oauth_providers'] = {}

    users[current_user]['oauth_providers']['github'] = {
        'id': user_info['id'],
        'username': user_info['login']
    }

    return jsonify({'message': 'GitHub account linked'})
```

### 5. Fetch Additional User Data

Get repositories, organizations, etc.:

```python
@app.route('/profile/repos')
@jwt_required()
def get_repos():
    current_user = get_jwt_identity()
    user_data = users[current_user]

    # If we stored GitHub access token
    github_token = user_data.get('github_access_token')

    # Fetch user's repositories
    response = github.get(
        'user/repos',
        token={'access_token': github_token}
    )
    repos = response.json()

    return jsonify({
        'username': user_data['username'],
        'repositories': [
            {
                'name': repo['name'],
                'stars': repo['stargazers_count'],
                'url': repo['html_url']
            }
            for repo in repos
        ]
    })
```

---

## Comparison: Basic Auth vs API Key vs JWT vs OAuth

| Feature | Basic Auth | API Key | JWT | OAuth 2.0 |
|---------|------------|---------|-----|-----------|
| **Credentials sent** | Every request | Once at registration | Once at login | Once (to provider) |
| **Password stored** | Yes (hashed) | Yes (hashed) | Yes (hashed) | No (provider stores) |
| **Stateless** | Yes | Yes | Yes | Hybrid |
| **Expiration** | No | Manual | Automatic | Automatic |
| **Third-party login** | No | No | No | Yes |
| **User trust** | Low (new account) | Low | Low | High (trusted provider) |
| **Setup complexity** | Low | Medium | Medium | High |
| **Best for** | Simple APIs | Public APIs | Modern apps | Consumer apps |

---

## When to Use OAuth

### ✅ Use OAuth When:

1. **Building consumer-facing apps**
   - Users prefer "Sign in with Google" over creating accounts
   - Reduces friction in onboarding

2. **You don't want to store passwords**
   - Security responsibility shifts to provider
   - No password reset flows to build

3. **You need profile data**
   - Auto-populate user profiles
   - Avatar images, verified emails

4. **Building integrations**
   - Access user's GitHub repos
   - Post to user's Twitter
   - Read user's Google Calendar

5. **Enterprise SSO**
   - Integrate with corporate identity providers
   - Support SAML, OpenID Connect

### ❌ Don't Use OAuth When:

1. **Building internal tools**
   - Basic Auth or API keys are simpler
   - You control all users

2. **Server-to-server APIs**
   - Use API keys or client credentials
   - No user interaction needed

3. **You need simplicity**
   - OAuth adds complexity
   - Not worth it for small projects

4. **Offline access required**
   - OAuth requires network to validate
   - Consider JWT or API keys

---

## Additional Resources

- **RFC 6749**: [OAuth 2.0 Authorization Framework](https://tools.ietf.org/html/rfc6749)
- **RFC 7636**: [Proof Key for Code Exchange (PKCE)](https://datatracker.ietf.org/doc/html/rfc7636)
- **RFC 9700**: [OAuth 2.0 Security Best Current Practice](https://datatracker.ietf.org/doc/rfc9700/) (the current best-practice document)
- **OAuth 2.1** (IETF draft): [draft-ietf-oauth-v2-1](https://datatracker.ietf.org/doc/draft-ietf-oauth-v2-1/) and [oauth.net/2.1](https://oauth.net/2.1/)
- **Authlib Documentation**: https://docs.authlib.org/en/latest/
- **GitHub OAuth**: https://docs.github.com/en/developers/apps/building-oauth-apps
- **OAuth 2.0 Playground**: https://www.oauth.com/playground/
- **OWASP OAuth Security**: https://cheatsheetseries.owasp.org/cheatsheets/OAuth2_Cheat_Sheet.html

---

## Summary

**Key Takeaways:**

1. **OAuth = Delegated Authorization**
   - Users log in with trusted providers (GitHub, Google)
   - Your app never sees user passwords
   - Provider handles security and account management

2. **Authorization Code + PKCE**
   - The recommended flow for every client (RFC 9700, OAuth 2.1); Implicit and Password are removed
   - Authorization code + code_verifier → Access token exchange on server
   - Client secret never exposed to browser; a stolen code is useless without the verifier
   - Users identified by the provider's stable `id`, not by `login`

3. **OAuth + JWT Pattern**
   - OAuth for initial authentication
   - JWT for subsequent API requests
   - Best of both worlds: trusted login + stateless auth

4. **Three-Step Process**
   - Redirect to provider → User authorizes → Callback with code
   - Exchange code for token → Fetch user profile → Create JWT
   - Use JWT for your API → Logout clears session

5. **Security First**
   - Never commit client secrets
   - Use HTTPS in production
   - Validate redirect URIs
   - Request minimal scopes
   - Handle errors gracefully

**Next Steps:**
- **Stretch Goals**: Add Google OAuth, implement token refresh
- **Exercise 10**: Combine OAuth with Roles & Permissions
- **Real Project**: Build a full OAuth integration with multiple providers

Good luck! 🚀
