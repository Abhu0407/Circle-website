# Circle

Django backend + Vue 3 frontend, served together by `python manage.py runserver`.
No Node/npm build is needed: `.vue` files are compiled in the browser by
[vue3-sfc-loader](https://github.com/FranckFreiburger/vue3-sfc-loader).

## Run

```powershell
cd backend
venv\Scripts\activate
pip install -r requirements.txt
python manage.py makemigrations
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

| Path                                 | Purpose                                                                                                                                                   |
| ------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `backend/templates/base.html`        | The single Django template every page uses                                                                                                                |
| `backend/apps/accounts/models.py`    | Custom `User` model (unique email)                                                                                                                        |
| `backend/apps/accounts/views.py`     | Page views (`VuePageView`) + JSON API views                                                                                                               |
| `backend/apps/accounts/urls.py`      | `/`, `/profile/`, `/signin/`, `/signup/`, `/api/auth/...`                                                                                                 |
| `frontend/main.js`                   | Mounts the requested `.vue` file                                                                                                                          |
| `frontend/api.mjs`                   | `fetch` helper (CSRF + error parsing)                                                                                                                     |
| `frontend/pages/<page>/main.vue`     | Entry file Django mounts for each page                                                                                                                    |
| `frontend/pages/<page>/<Page>.vue`   | The page UI (`auth/Auth.vue` = sign in + sign up, `home/Home.vue` = For You, Discover, ..., `profile/Profile.vue`)                                        |
| `backend/apps/posts/feed.py`         | For You ranking: shuffled posts weighted by interests + activity, and suggested communities                                                               |
| `frontend/components/BaseLayout.vue` | Frame shared by every signed-in page: sidebar, header band, right panel                                                                                   |
| `frontend/components/`               | Also `ActionButton.vue` (the app's button), `Modal.vue`, `MapView.vue`, `AuthLayout.vue`, `FormField.vue`, `BrandLogo.vue`, `Icon.vue`, `ActivityArt.vue` |

### Adding a new page

1. Create `frontend/pages/mypage/MyPage.vue` (the UI) and
   `frontend/pages/mypage/main.vue` (the entry; it just renders `<MyPage />`).
   For a signed-in page, wrap `MyPage.vue`'s content in `<BaseLayout>` so it
   gets the sidebar, header band and right panel (see `profile/Profile.vue`).
2. Add a view. Signed-in pages extend `AppPageView`, which requires login
   and passes the props `BaseLayout` needs (`user`, `homeUrl`, ...):

   ```python
   class MyPageView(AppPageView):          # or VuePageView for a public page
       vue_component = 'pages/mypage/main.vue'
       page_title = 'My page'

       def get_page_props(self):
           return {**super().get_page_props(), 'hello': 'world'}   # props on MyPage.vue
   ```

3. Add it to `urls.py`.

> Note: plain JS modules imported from `.vue` files must use the `.mjs`
> extension (vue3-sfc-loader only treats `.mjs` as ES modules).

## For You (the home page)

`/` opens **For You**; Discover is at `/?tab=discover`.

- **Posts** (`GET /api/feed/?seed=&offset=`): other people's posts from every
  community, in a weighted random order. A post's weight is
  `1 + 4·(category is an interest) + 3·(activity in that category, 0–1)`,
  roughly doubled for posts from the last few days. Activity counts
  communities joined, posts written, comments and likes. The page picks a
  random `seed`, so each visit (or **Shuffle**) gives a new order while
  pages of one visit follow on without repeats.
- **Suggested communities** (`GET /api/feed/communities/`): communities you
  haven't joined, scored by your interests, your activity, posts of theirs you
  liked or commented on, members you share communities with, distance and
  size. Each comes with a `reason` ("You like Sports", "Near you"...). They
  appear between posts as rows you can scroll sideways.

## Tests

```powershell
cd backend
python manage.py test apps.accounts
```
