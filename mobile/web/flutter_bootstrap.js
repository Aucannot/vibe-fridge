{{flutter_js}}
{{flutter_build_config}}

const staleServiceWorkerReloadKey = 'vibe_fridge_stale_service_worker_reload';

async function clearStaleFlutterCaches() {
  if (!('caches' in window)) {
    return;
  }

  const cacheNames = await caches.keys();
  await Promise.all(
    cacheNames
      .filter((cacheName) => cacheName.startsWith('flutter-'))
      .map((cacheName) => caches.delete(cacheName)),
  );
}

async function clearStaleServiceWorkers() {
  if (!('serviceWorker' in navigator)) {
    await clearStaleFlutterCaches();
    return true;
  }

  const registrations = await navigator.serviceWorker.getRegistrations();
  if (registrations.length === 0) {
    await clearStaleFlutterCaches();
    sessionStorage.removeItem(staleServiceWorkerReloadKey);
    return true;
  }

  await Promise.all(
    registrations.map((registration) => registration.unregister()),
  );
  await clearStaleFlutterCaches();

  if (
    navigator.serviceWorker.controller &&
    sessionStorage.getItem(staleServiceWorkerReloadKey) !== 'true'
  ) {
    sessionStorage.setItem(staleServiceWorkerReloadKey, 'true');
    window.location.reload();
    return false;
  }

  sessionStorage.removeItem(staleServiceWorkerReloadKey);
  return true;
}

clearStaleServiceWorkers()
  .catch((error) => {
    console.warn('Failed to clear stale service workers:', error);
    return true;
  })
  .then((shouldLoadApp) => {
    if (shouldLoadApp) {
      _flutter.loader.load();
    }
  });
