/**
 * Service worker for PWA
 */
const CACHE = 'samsung-chromium-pwa';

const filesToCache = [
    'css/style.css',
    'images/btn1.svg',
    'images/btn2.svg',
    'images/btn3.svg',
    'images/btn4.svg',
    'images/btn5.svg',
    'images/btn6.svg',
    'images/btn7.svg',
    'images/btn8.svg',
    'images/chromiumsamsung.svg',
    'images/favicon.png'
];

//Install stage sets up the cache-array to configure pre-cache content
self.addEventListener('install', function(event) {
  event.waitUntil(precache().then(function() {
    return self.skipWaiting();
  }))
});


//allow sw to control of current page
self.addEventListener('activate', function(event) {
  caches.delete(CACHE);
  return self.clients.claim();
});

self.addEventListener('fetch', function(event) {
  if ( !(event.request.url).includes(location.origin) ||
    (event.request.url) == (location.origin + '/') ||
    (event.request.url) == (location.origin + '/index.html')) {
    return;
  }
  event.respondWith(
    caches.match(event.request)
      .then(function(response) {
        if (response) {
          return response;
        } else {
          return fetch(event.request)
            .then(function(res) {
              return caches.open(CACHE)
                .then(function(cache) {
                  cache.put(event.request.url, res.clone());
                  return res;
                })
            })
            .catch(function(err) {
              console.log(err);
            });
        }
      })
  );
  event.waitUntil(update(event.request));
});

function precache() {
  return caches.open(CACHE).then(function (cache) {
    return cache.addAll(filesToCache.map(function(filesToCache) {
        return new Request(filesToCache, {mode:'no-cors'});
    })).then(function() {
    });
  }).catch(function(error){
    console.error('Pre-fetching failed:', error);
  });
}

function fromCache(request) {
  //we pull files from the cache first thing so we can show them fast
  return caches.open(CACHE).then(function (cache) {
    return cache.match(request).then(function (matching) {
      return matching || Promise.reject('no-match');
    });
  });
}

function update(request) {
  //this is where we call the server to get the newest version of the
  //file to use the next time we show view
  return caches.open(CACHE).then(function (cache) {
    return fetch(request).then(function (response) {
      return cache.put(request, response);
    });
  });
}

function fromServer(request){
  //this is the fallback if it is not in the cache to go to the server and get it
  return fetch(request).then(function(response){ return response});
}