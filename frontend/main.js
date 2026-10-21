// Entry point loaded by backend/templates/base.html.
// Reads which .vue component the Django view wants, loads it with
// vue3-sfc-loader and mounts it with the props the view provided.
//
// Links to other pages don't reload the browser: the next page's HTML is
// fetched, its component and props are read from it, and the new component
// replaces the current one. Compiled .vue files stay in `moduleCache`, so
// shared parts (BaseLayout, icons, ...) are only compiled once per visit.
(function () {
  const { loadModule } = window['vue3-sfc-loader'];

  const mountEl = document.getElementById('app');

  const options = {
    moduleCache: { vue: Vue },

    async getFile(url) {
      // Revalidate every time so edited .vue/.mjs files show up on a normal reload.
      const res = await fetch(url, { cache: 'no-cache' });
      if (!res.ok) throw new Error(`${res.status} ${res.statusText}: ${url}`);
      return {
        getContentData: (asBinary) => (asBinary ? res.arrayBuffer() : res.text()),
      };
    },

    addStyle(textContent) {
      const style = Object.assign(document.createElement('style'), { textContent });
      document.head.appendChild(style);
    },

    log(type, ...args) {
      console[type](...args);
    },
  };

  let app = null;
  // The path of the page on screen; pages like Chats change only the query
  // string with pushState, and handle those back/forward steps themselves.
  let currentPath = window.location.pathname;
  let navId = 0;

  async function mount(componentUrl, props) {
    const component = await loadModule(componentUrl, options);
    if (app) app.unmount();
    app = Vue.createApp(component, props);
    app.mount(mountEl);
  }

  // ---------- soft navigation ----------
  const bar = Object.assign(document.createElement('div'), { className: 'nav-progress' });
  document.body.appendChild(bar);

  function readPage(html) {
    const doc = new DOMParser().parseFromString(html, 'text/html');
    const el = doc.getElementById('app');
    const propsEl = doc.getElementById('page-props');
    if (!el || !el.dataset.component || !propsEl) return null;
    return { component: el.dataset.component, props: JSON.parse(propsEl.textContent || '{}'), title: doc.title };
  }

  async function navigate(url, { push = true, scrollY = 0 } = {}) {
    const id = ++navId;
    bar.classList.add('nav-progress--on');
    try {
      const res = await fetch(url, { credentials: 'same-origin', headers: { Accept: 'text/html' } });
      const type = res.headers.get('Content-Type') || '';
      const page = res.ok && type.includes('text/html') ? readPage(await res.text()) : null;
      if (id !== navId) return; // a newer click won
      if (!page) throw new Error('not a page');

      // Remember where we were, so Back returns to the same spot.
      if (push) {
        history.replaceState({ ...history.state, scrollY: window.scrollY }, '');
        history.pushState({}, '', res.url); // res.url follows redirects (e.g. to sign in)
      }
      currentPath = new URL(res.url).pathname;
      await mount(page.component, page.props);
      if (id !== navId) return;
      document.title = page.title;
      window.scrollTo(0, scrollY);
    } catch {
      window.location.href = url; // fall back to a normal page load
    } finally {
      if (id === navId) bar.classList.remove('nav-progress--on');
    }
  }

  function isPageLink(a, event) {
    if (!a || event.defaultPrevented || event.button !== 0) return false;
    if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return false;
    if ((a.target && a.target !== '_self') || a.hasAttribute('download')) return false;
    const url = new URL(a.href, window.location.href);
    if (url.origin !== window.location.origin) return false;
    if (/^\/(api|static|media|admin|maps)\b/.test(url.pathname)) return false;
    // Same page, only a #hash: let the browser scroll.
    if (url.pathname === window.location.pathname && url.search === window.location.search && url.hash) return false;
    return true;
  }

  // Bubble phase, so a component's own @click.prevent (e.g. Home's tabs) wins.
  document.addEventListener('click', (event) => {
    const a = event.target.closest && event.target.closest('a[href]');
    if (!isPageLink(a, event)) return;
    event.preventDefault();
    navigate(a.href);
  });

  window.addEventListener('popstate', (event) => {
    if (window.location.pathname === currentPath) return; // same page: it handles this itself
    navigate(window.location.href, { push: false, scrollY: (event.state && event.state.scrollY) || 0 });
  });

  // For components that go to another page from code (after saving, deleting...).
  window.circleNavigate = (url) => navigate(new URL(url, window.location.href).href);

  // ---------- first page ----------
  const props = JSON.parse(document.getElementById('page-props').textContent || '{}');
  mount(mountEl.dataset.component, props);
})();
