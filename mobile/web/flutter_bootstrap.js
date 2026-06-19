{{flutter_js}}
{{flutter_build_config}}

const staleServiceWorkerReloadKey = 'vibe_fridge_stale_service_worker_reload';

async function clearStaleServiceWorkers() {
  if (!('serviceWorker' in navigator)) {
    return true;
  }

  const registrations = await navigator.serviceWorker.getRegistrations();
  if (registrations.length === 0) {
    sessionStorage.removeItem(staleServiceWorkerReloadKey);
    return true;
  }

  await Promise.all(
    registrations.map((registration) => registration.unregister()),
  );

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
