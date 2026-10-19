# Circle

Django backend + Vue 3 frontend, served together by `python manage.py runserver`.
No Node/npm build is needed: `.vue` files are compiled in the browser by
[vue3-sfc-loader](https://github.com/FranckFreiburger/vue3-sfc-loader).

## Run

```powershell
cd backend
venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Then open http://127.0.0.1:8000/signin/. Sign in and sign up share one page
(`/signin/` and `/signup/` both load it) and switch tabs without a reload.

### Google sign in (optional)

1. In [Google Cloud Console → Credentials](https://console.cloud.google.com/apis/credentials),
   create an **OAuth client ID** of type **Web application**.
2. Under **Authorized JavaScript origins** add `http://127.0.0.1:8000` and
   `http://localhost:8000` (plus your production domain later).
3. Put the client ID in `backend/.env` (git-ignored) and restart the server:
   ```
   GOOGLE_CLIENT_ID=1234-abc.apps.googleusercontent.com
   ```

The "Sign in with Google" / "Sign up with Google" button is always shown on
`/signin/` and `/signup/`; until `GOOGLE_CLIENT_ID` is set, clicking it just
shows a "not set up yet" message. The browser gets an ID token from Google and
posts it to `/api/auth/google/`; Django verifies it, signs in the account with
that email, or creates one (username from the email, no password).

## How it fits together

```
Browser ──> Django TemplateView (apps/accounts/views.py)
              renders backend/templates/base.html
                 ├─ data-component="/static/pages/auth/main.vue"     (which .vue to mount)
                 ├─ <script id="page-props">{...}</script>       (props from the view)
                 └─ frontend/main.js  ──loads──> frontend/pages/*.vue
                                                   └─ calls /api/auth/* (JSON, DRF)
```

| Path | Purpose |
| --- | --- |
| `backend/templates/base.html` | The single Django template every page uses |
| `backend/apps/accounts/models.py` | Custom `User` model (unique email) |
| `backend/apps/accounts/views.py` | Page views (`VuePageView`) + JSON API views |
| `backend/apps/accounts/urls.py` | `/`, `/signin/`, `/signup/`, `/api/auth/...` |
| `frontend/main.js` | Mounts the requested `.vue` file |
| `frontend/api.mjs` | `fetch` helper (CSRF + error parsing) |
| `frontend/pages/<page>/main.vue` | Entry file Django mounts for each page |
| `frontend/pages/<page>/<Page>.vue` | The page UI (`auth/Auth.vue` = sign in + sign up, `home/Home.vue`) |
| `frontend/components/` | `AuthLayout.vue`, `FormField.vue`, `BrandLogo.vue`, `Icon.vue`, `ActivityArt.vue` |

### Adding a new page

1. Create `frontend/pages/mypage/MyPage.vue` (the UI) and
   `frontend/pages/mypage/main.vue` (the entry; it just renders `<MyPage />`).
2. Add a view:
   ```python
   class MyPageView(VuePageView):
       vue_component = 'pages/mypage/main.vue'
       page_title = 'My page'

       def get_page_props(self):
           return {'hello': 'world'}   # becomes a prop on MyPage.vue
   ```
3. Add it to `urls.py`.

> Note: plain JS modules imported from `.vue` files must use the `.mjs`
> extension (vue3-sfc-loader only treats `.mjs` as ES modules).

## Tests

```powershell
cd backend
python manage.py test apps.accounts
```
