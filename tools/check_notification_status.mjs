#!/usr/bin/env node

const rawVmServiceUrl = process.argv[2];

if (!rawVmServiceUrl) {
  console.error(
    'Usage: node tools/check_notification_status.mjs <flutter-vm-service-url>',
  );
  process.exit(64);
}

const baseUrl = normalizeBaseUrl(rawVmServiceUrl);

try {
  const vm = await getJson('getVM');
  const isolateId = vm.result?.isolates?.find(
    (isolate) => isolate?.isSystemIsolate !== true,
  )?.id;
  if (!isolateId) {
    throw new Error('No runnable app isolate found in VM Service response.');
  }

  const status = await getJson(
    `ext.vibe_fridge.notificationStatus?isolateId=${encodeURIComponent(
      isolateId,
    )}`,
  );
  const result = status.result;
  if (
    typeof result?.supported !== 'boolean' ||
    typeof result?.granted !== 'boolean' ||
    typeof result?.status !== 'string' ||
    typeof result?.displayText !== 'string'
  ) {
    throw new Error('Notification status extension returned invalid payload.');
  }

  console.log(
    JSON.stringify(
      {
        isolateId,
        notificationStatus: result,
      },
      null,
      2,
    ),
  );
} catch (error) {
  console.error(`Notification status smoke failed: ${error.message}`);
  process.exit(1);
}

function normalizeBaseUrl(value) {
  const url = new URL(value);
  if (!url.pathname.endsWith('/')) {
    url.pathname = `${url.pathname}/`;
  }
  return url;
}

async function getJson(methodPath) {
  const url = new URL(methodPath, baseUrl);
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`${url.href} returned HTTP ${response.status}`);
  }
  const payload = await response.json();
  if (payload.error) {
    throw new Error(payload.error.message ?? JSON.stringify(payload.error));
  }
  return payload;
}
