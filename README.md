# Circle

Circle is a community website. People sign up, join communities near them,
share posts with photos or videos, chat live with community members and get
notifications.

- **Backend:** Django (Python) with Django REST Framework and Django Channels (live chat)
- **Frontend:** Vue 3. You do **not** need Node.js or npm. The browser builds the
  `.vue` files itself with [vue3-sfc-loader](https://github.com/FranckFreiburger/vue3-sfc-loader).
- **Database:** SQLite (one file, `backend/db.sqlite3`). You don't need to install a database.

One command, `python manage.py runserver`, runs the whole website: pages, API and live chat.

---

## Contents

1. [What you need](#1-what-you-need)
2. [Run the project (first time)](#2-run-the-project-first-time)
3. [Run the project (every next time)](#3-run-the-project-every-next-time)
4. [Settings in the `.env` file](#4-settings-in-the-env-file)
5. [Demo data](#5-demo-data)
6. [Errors and how to fix them](#6-errors-and-how-to-fix-them)
7. [How the project is organised](#7-how-the-project-is-organised)
8. [Tests](#8-tests)
9. [Deploy for free (Render + Neon + Backblaze B2)](#9-deploy-for-free-render--neon--backblaze-b2)

---

## 1. What you need

| Tool                                        | Version       | Why                                                                           |
| ------------------------------------------- | ------------- | ----------------------------------------------------------------------------- |
| [Python](https://www.python.org/downloads/) | 3.12 or newer | Runs the backend. On Windows, tick **"Add Python to PATH"** while installing. |
| [Git](https://git-scm.com/downloads)        | any           | To download the code                                                          |
| Internet connection                         |               | Vue is loaded from a CDN, and maps and Google sign in need it                 |

Check that Python works:

```powershell
python --version
```

---

## 2. Run the project (first time)

Open a terminal in the project folder (`Circle-website`) and run these commands one by one.

**Windows (PowerShell):**

```powershell
cd backend

# 1. Make a virtual environment (a private folder for this project's Python packages)
python -m venv venv

# 2. Turn it on. You will see (venv) at the start of the line.
venv\Scripts\activate

# 3. Install the packages
pip install -r requirements.txt

# 4. Create the database tables
python manage.py makemigrations accounts communities posts chat
python manage.py migrate

# 5. (Optional) Make an admin account for /admin/
python manage.py createsuperuser

# 6. (Optional) Add demo users, communities and posts
python manage.py seed_demo

# 7. Start the website
python manage.py runserver
```

**macOS / Linux:** the same, except step 1 and 2:

```bash
python3 -m venv venv
source venv/bin/activate
```

Now open **http://127.0.0.1:8000/** in your browser.

> **Why the app names in `makemigrations`?** The `migrations/` folders are not
> saved in Git (see `.gitignore`). On a fresh copy they don't exist, and plain
> `python manage.py makemigrations` then creates nothing. Naming the apps
> creates them.

To stop the server press **Ctrl + C**.

---

## 3. Run the project (every next time)

```powershell
cd backend
venv\Scripts\activate
python manage.py runserver
```

If you (or someone else) changed a `models.py` file, also run this before `runserver`:

```powershell
python manage.py makemigrations accounts communities posts chat
python manage.py migrate
```

If `requirements.txt` changed, run `pip install -r requirements.txt` again.

---

## 4. Settings in the `.env` file

Some settings are read from a file named **`backend/.env`**. You make this file
yourself; it is not in Git, so secret values stay on your computer.

**All of them are optional.** The project runs without a `.env` file.

```ini
# backend/.env  (example)

# Turns on "Sign in with Google". See below how to get it.
GOOGLE_CLIENT_ID=1234-abc.apps.googleusercontent.com

# Biggest file a user can send in chat, in MB (default 25)
CHAT_MAX_FILE_MB=25

# Biggest video a post can have, in MB (default 50)
POST_MAX_VIDEO_MB=50

# Tells OpenStreetMap who you are. Put your email before going live.
MAPS_USER_AGENT=Circle/1.0 (you@example.com)

# Map picture server and place search server (defaults shown)
MAP_TILE_URL=https://tile.openstreetmap.org/{z}/{x}/{y}.png
PHOTON_URL=https://photon.komoot.io

# Only for live servers with more than one process (needs: pip install channels-redis)
# REDIS_URL=redis://127.0.0.1:6379
```

| Field               | Needed?                                | Default                           | What it does                                                                        |
| ------------------- | -------------------------------------- | --------------------------------- | ----------------------------------------------------------------------------------- |
| `GOOGLE_CLIENT_ID`  | No                                     | empty                             | Turns on the Google sign in button. Empty means clicking it shows "not set up yet". |
| `CHAT_MAX_FILE_MB`  | No                                     | `25`                              | Size limit for each photo, video or file sent in chat                               |
| `POST_MAX_VIDEO_MB` | No                                     | `50`                              | Size limit for a video in a post                                                    |
| `MAPS_USER_AGENT`   | Before going live                      | `CircleWebsite/1.0 (development)` | Name and email sent to OpenStreetMap                                                |
| `MAP_TILE_URL`      | No                                     | OpenStreetMap                     | Where the map pictures come from                                                    |
| `PHOTON_URL`        | No                                     | `https://photon.komoot.io`        | Place search ("type an address")                                                    |
| `REDIS_URL`         | Only with more than one server process | not set                           | Shares live chat messages between processes                                         |

After you change `.env`, **restart the server** (Ctrl + C, then `runserver` again).

### How to get a `GOOGLE_CLIENT_ID`

1. Open [Google Cloud Console → Credentials](https://console.cloud.google.com/apis/credentials).
2. Click **Create credentials → OAuth client ID**, type **Web application**.
3. Under **Authorized JavaScript origins** add `http://127.0.0.1:8000` and
   `http://localhost:8000` (and your real domain later).
4. Copy the client ID into `backend/.env` as `GOOGLE_CLIENT_ID=...` and restart the server.

---

## 5. Demo data

An empty website is hard to test. This command adds 120 users, 36 communities,
posts with photos, likes and comments:

```powershell
python manage.py seed_demo                  # add demo data
python manage.py seed_demo --join yourname  # also put your account in every demo community
python manage.py seed_demo --reset          # delete demo data and add it again
python manage.py seed_demo --clear          # only delete demo data
```

Every demo user's email ends with `@demo.circle` and the password is **`Abcd@1234`**.

---

## 6. Errors and how to fix them

These are the errors people hit most often.

| Error                                                                                       | Why it happens                                                   | Fix                                                                                                          |
| ------------------------------------------------------------------------------------------- | ---------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| `venv\Scripts\activate cannot be loaded because running scripts is disabled on this system` | PowerShell blocks scripts by default                             | Run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once, then activate again.                         |
| `ModuleNotFoundError: No module named 'django'` (or `daphne`, `channels`, `PIL`...)         | The virtual environment is not on, or packages are not installed | Run `venv\Scripts\activate`, then `python -m pip install -r requirements.txt`.                               |
| `can't open file '...manage.py'`                                                            | You are in the wrong folder                                      | `cd backend` first. `manage.py` is inside `backend/`.                                                        |
| `no such table: ...` or `no such column: ...`                                               | Database tables were never made, or a model changed              | `python manage.py makemigrations accounts communities posts chat` then `python manage.py migrate`            |
| `Error: That port is already in use.`                                                       | Another server is already running on port 8000                   | Close the other terminal, or use another port: `python manage.py runserver 8001`                             |
| Blank white page                                                                            | Vue failed to load or a `.vue` file has an error                 | Press **F12 → Console** in the browser and read the red error. No internet means the Vue CDN can't load.     |
| Your change to a `.vue` file doesn't show                                                   | Browser cache                                                    | Reload with **Ctrl + F5**.                                                                                   |
| Google button says "not set up yet"                                                         | `GOOGLE_CLIENT_ID` is not set                                    | See [How to get a GOOGLE_CLIENT_ID](#how-to-get-a-google_client_id), then restart the server.                |

### Still stuck?

1. Read the **full error** in the terminal where `runserver` runs. The last lines say what went wrong and which file/line.
2. For page problems, open the browser **Console** (F12) and the **Network** tab.
3. Run the tests (section 10). A failing test often points at the broken part.

---

## 7. How the project is organised

```
Circle-website/
├── backend/                     Django (Python)
│   ├── manage.py                Run every Django command from here
│   ├── requirements.txt         Python packages
│   ├── .env                     Your local settings (you create it, not in Git)
│   ├── config/
│   │   ├── settings.py          All settings
│   │   ├── urls.py              Joins the URLs of every app
│   │   └── asgi.py              Serves pages + live chat sockets
│   ├── templates/base.html      The ONE HTML template every page uses
│   └── apps/
│       ├── accounts/            Users, sign in/up, Google sign in, profile, For You page
│       ├── communities/         Communities (create, join, leave, discover)
│       ├── posts/               Posts, likes, comments, For You ranking (feed.py), seed_demo
│       ├── chat/                Live group chat, attachments, unread counts
│       ├── notifications/       Notifications page
│       └── maps/                Map tiles and place search (proxied through our site)
└── frontend/                    Vue 3 (served as static files)
    ├── main.js                  Loads and mounts the right .vue page
    ├── api.mjs                  Helpers to call the Django API
    ├── chat.mjs                 Shared chat socket and unread counts
    ├── styles/global.css        Colours, fonts and shared styles
    ├── components/              Reusable parts (BaseLayout, ActionButton, Modal, PostCard...)
    └── pages/<page>/            One folder per page: main.vue (entry) + <Page>.vue (UI)
```

---

## 8. Tests

```powershell
cd backend
python manage.py test apps
```

Run one app only, for example: `python manage.py test apps.chat`.

---

## 9. Deploy for free (Render + Neon + Backblaze B2)

Free hosts wipe their disk on every deploy, so the live site keeps nothing on
its own disk:

| Part                                    | Service                                       | Free plan                                       |
| --------------------------------------- | --------------------------------------------- | ----------------------------------------------- |
| The website (pages, API, live chat)     | [Render](https://render.com)                  | Sleeps after 15 min idle; first visit is slow   |
| Database                                | [Neon](https://neon.tech) (Postgres)          | 0.5 GB                                          |
| Photos, videos and chat files           | [Backblaze B2](https://www.backblaze.com/cloud-storage) | 10 GB, no card needed |

On your computer nothing changes: without these settings the project still
uses `db.sqlite3` and the `media/` and `chat_files/` folders.

### Step 1: Push the code to GitHub

Render deploys from a GitHub repository. Commit everything, including the
`migrations/` folders, and push.

### Step 2: Make the database (Neon)

1. Sign up at [neon.tech](https://neon.tech) and create a project (pick the region closest to your Render region).
2. On the project dashboard click **Connect** and copy the connection string.
   It looks like `postgresql://user:password@ep-xxx.aws.neon.tech/neondb?sslmode=require`.
   This is your `DATABASE_URL`.

### Step 3: Make the file storage (Backblaze B2)

1. Sign up at [backblaze.com/sign-up/cloud-storage](https://www.backblaze.com/sign-up/cloud-storage) (no card needed) and confirm your email.
2. Open **B2 Cloud Storage → Buckets → Create a Bucket**:
   - **Bucket name:** must be unique across all of Backblaze, e.g. `circle-uploads-yourname`
   - **Files in Bucket are:** **Private** (chat files must only reach community members)
   - Leave the rest as it is and click **Create a Bucket**.
3. On the new bucket, copy the **Endpoint**, e.g. `s3.us-west-004.backblazeb2.com`.
   - `S3_ENDPOINT_URL` is it with `https://` in front: `https://s3.us-west-004.backblazeb2.com`
   - `S3_REGION` is the middle part: `us-west-004`
4. Open **Application Keys → Add a New Application Key** (not the "Master Application Key", which doesn't work here):
   - **Name of Key:** `circle`
   - **Allow access to Bucket(s):** your bucket
   - **Type of Access:** **Read and Write**
   - Click **Create New Key**.
5. Copy **keyID** (`S3_ACCESS_KEY_ID`) and **applicationKey** (`S3_SECRET_ACCESS_KEY`) right away.
   The applicationKey is shown **only once**; if you lose it, make a new key.

### Step 4: Make the website (Render)

1. Sign up at [render.com](https://render.com) with GitHub.
2. Click **New → Blueprint** and pick this repository. Render reads `render.yaml`.
3. Fill in the values it asks for:

| Field                  | Value                                                              |
| ---------------------- | ------------------------------------------------------------------ |
| `DATABASE_URL`         | Neon connection string (step 2)                                    |
| `S3_ENDPOINT_URL`      | e.g. `https://s3.us-west-004.backblazeb2.com` (step 3)             |
| `S3_REGION`            | e.g. `us-west-004`                                                 |
| `S3_ACCESS_KEY_ID`     | Backblaze keyID                                                    |
| `S3_SECRET_ACCESS_KEY` | Backblaze applicationKey                                           |
| `S3_BUCKET`            | Bucket name, e.g. `circle-uploads-yourname`                        |
| `DJANGO_SUPERUSER_USERNAME` | Admin username, e.g. `admin`                                  |
| `DJANGO_SUPERUSER_EMAIL`    | Admin email                                                   |
| `DJANGO_SUPERUSER_PASSWORD` | A strong password for the admin                               |
| `GOOGLE_CLIENT_ID`     | Same as in your `.env` (optional)                                  |
| `MAPS_USER_AGENT`      | e.g. `Circle/1.0 (you@example.com)`                                |
| `SPECIAL_EMAIL`, `SPECIAL_NAME` | Same as in your `.env` (optional)                         |

`SECRET_KEY` is made for you and `DEBUG` is `False`. The build installs the
packages, collects the frontend files, creates the database tables and makes
the admin account.

4. When it says **Live**, open `https://<name>.onrender.com`.
5. Sign in at `https://<name>.onrender.com/admin/` with the admin username and password.

The live site starts **empty**: your local database, users and uploads stay on
your computer. The admin account is the only account; everyone else signs up.
It is made on the first deploy only, so changing its password later in
`/admin/` is kept. To make a different admin, change `DJANGO_SUPERUSER_USERNAME`
and deploy again.

**Google sign in:** add `https://<name>.onrender.com` to **Authorized JavaScript
origins** of your Google OAuth client.

**Your own domain:** add it in Render (**Settings → Custom Domains**) and to the
`ALLOWED_HOSTS` setting, e.g. `ALLOWED_HOSTS=circle.example.com`.

### Settings only the live server uses

| Field                  | Default        | What it does                                                         |
| ---------------------- | -------------- | -------------------------------------------------------------------- |
| `DEBUG`                | `True`         | Set `False` on the live server (https only, secure cookies)          |
| `SECRET_KEY`           | built-in key   | Must be set when `DEBUG=False`                                       |
| `ALLOWED_HOSTS`        | local only     | Extra domain names, comma separated (Render's own is added for you)  |
| `DATABASE_URL`         | `db.sqlite3`   | Postgres database address                                            |
| `S3_BUCKET`            | not set        | Turns on cloud storage (needs `S3_ENDPOINT_URL` and the two keys)    |
| `S3_REGION`            | not set        | Region of the bucket, e.g. `us-west-004`                             |
| `S3_LINK_SECONDS`      | `3600`         | How long a link to a photo, video or file keeps working              |

Any S3-compatible storage works with these settings (e.g. Cloudflare R2 with
`S3_ENDPOINT_URL=https://<account id>.r2.cloudflarestorage.com` and `S3_REGION=auto`).
