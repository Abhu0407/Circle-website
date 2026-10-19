// Entry point loaded by backend/templates/base.html.
// Reads which .vue component the Django view wants, loads it with
// vue3-sfc-loader and mounts it with the props the view provided.
(function () {
  const { loadModule } = window['vue3-sfc-loader'];

  const mountEl = document.getElementById('app');
  const componentUrl = mountEl.dataset.component;
  const props = JSON.parse(document.getElementById('page-props').textContent || '{}');

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

  const App = Vue.defineAsyncComponent(() => loadModule(componentUrl, options));
  Vue.createApp(App, props).mount(mountEl);
})();
