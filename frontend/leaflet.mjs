// Loads Leaflet (map library) from the CDN the first time a map is shown.
// Resolves to the global `L`.

const VERSION = '1.9.4';
const BASE = `https://cdnjs.cloudflare.com/ajax/libs/leaflet/${VERSION}`;

let loading = null;

export function loadLeaflet() {
  if (window.L) return Promise.resolve(window.L);
  if (loading) return loading;

  loading = new Promise((resolve, reject) => {
    const css = Object.assign(document.createElement('link'), {
      rel: 'stylesheet',
      href: `${BASE}/leaflet.min.css`,
    });
    document.head.appendChild(css);

    const script = Object.assign(document.createElement('script'), {
      src: `${BASE}/leaflet.min.js`,
      onload: () => resolve(window.L),
      onerror: () => {
        loading = null;
        script.remove();
        reject(new Error('Could not load the map.'));
      },
    });
    document.head.appendChild(script);
  });
  return loading;
}
