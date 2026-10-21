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
                 ├─ <script id="page-props">{...}</scripdef __str__(self):
        return self.user.usernamet>       (props from the view)
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

## Posts with photos or videos

A post can have a photo (up to 5 MB) or a video (MP4, MOV, WebM or OGV, up
to `POST_MAX_VIDEO_MB`, default 50), not both. The composer shows upload
progress. Videos are stored in `media/post_videos/` and played through
`/api/posts/<id>/video/` (signed-in users only), which lets the player skip
ahead; files that only pretend to be videos are refused.

## Chats

`/?tab=chats` lists every community you joined as a box, latest message
first, with the number of unread messages. Opening one
(`/?tab=chats&community=<id>`) shows its group chat with all its members.
The **Chats** item in the sidebar shows the total unread count on every page.

- **Live:** messages go over a WebSocket (`/ws/chat/`, Django Channels) and
  reach everyone in the chat instantly. `daphne` in `INSTALLED_APPS` makes
  `python manage.py runserver` serve the sockets too, so nothing else is
  needed in development. If the connection drops, the page reconnects and
  fetches what it missed.
- **Private:** only signed-in members of a community can read or send its
  messages (checked on every request and socket message). Sockets are only
  accepted from pages on this site (`ALLOWED_HOSTS`), so other sites can't
  open one with your cookie. Message text is shown as plain text, never HTML.
  Sending is limited to 10 messages per 10 seconds; messages are at most
  2000 characters. Leaving a community stops its messages right away.
- **Photos, videos and files:** attach them with the 📎 button, drag them
  onto the chat, or paste them (up to 10 at a time, `CHAT_MAX_FILE_MB`
  each, default 25). Photos and videos show in the chat; other files show
  as a card to download. They are stored in `backend/chat_files/`, **not**
  the public `media/` folder, and only sent (by `/api/chats/files/<id>/`)
  to members of that community. Photos are re-saved without their hidden
  metadata (such as the GPS location they were taken at); files that only
  pretend to be photos or videos are treated as plain downloads; program and
  script files (`.exe`, `.bat`, `.js`, `.html`, `.svg`...) are refused.
- **Emoji:** the 😊 button opens a picker (search, categories, recently
  used). The emoji list is in `frontend/emoji.mjs`, so it works offline. A
  message of only 1-3 emoji is shown large.
- **Unread:** each user has a read marker per community (`ChatRead`).
  Messages after it that someone else wrote are unread; opening the chat
  moves it forward. New members start with nothing unread.

| Path                               | Purpose                                                   |
| ---------------------------------- | --------------------------------------------------------- |
| `backend/apps/chat/services.py`    | Membership checks, sending, history, unread counts        |
| `backend/apps/chat/consumers.py`   | The live socket                                           |
| `backend/apps/chat/attachments.py` | Checks and cleans photos, videos and files before saving  |
| `backend/apps/chat/views.py`       | `GET /api/chats/`, `/api/chats/<id>/messages/`, `/read/`  |
| `frontend/chat.mjs`                | The shared socket and live unread counts                  |
| `frontend/components/ChatList.vue` | Community boxes with unread badges                        |
| `frontend/components/ChatRoom.vue` | One community's chat                                      |
| `frontend/components/EmojiPicker.vue` | The emoji picker (emoji list: `frontend/emoji.mjs`)    |

**Going live:** serve over HTTPS (the page then uses `wss://` automatically),
run with an ASGI server (`daphne config.asgi:application`), and if you run
more than one process, `pip install channels-redis` and set `REDIS_URL` in
`.env` so messages reach users connected to any process.

## Tests

```powershell
cd backend
python manage.py test apps.accounts apps.chat
```
