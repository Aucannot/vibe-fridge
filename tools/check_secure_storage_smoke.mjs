#!/usr/bin/env node

try {
  await main();
} catch (error) {
  console.error(`Secure storage smoke failed: ${error.message}`);
  process.exit(1);
}

async function main() {
  const vmServiceUrl = parseArgs(process.argv.slice(2));
  if (!vmServiceUrl) {
    console.error(usage());
    process.exit(64);
  }

  const baseUrl = normalizeBaseUrl(vmServiceUrl);
  const vm = await getJson(baseUrl, 'getVM');
  const isolateId = vm.result?.isolates?.find(
    (isolate) => isolate?.isSystemIsolate !== true,
  )?.id;
  if (!isolateId) {
    throw new Error('No runnable app isolate found in VM Service response.');
  }

  const smoke = await getExtensionJson(
    baseUrl,
    `ext.vibe_fridge.secureStorageSmoke?isolateId=${encodeURIComponent(
      isolateId,
    )}`,
  );
  const result = smoke.result;
  validateSmokePayload(result);

  console.log(JSON.stringify({ isolateId, secureStorageSmoke: result }, null, 2));
}

function usage() {
  return 'Usage: node tools/check_secure_storage_smoke.mjs <flutter-vm-service-url>';
}

function parseArgs(args) {
  if (args.length > 1) {
    throw new Error('Only one Flutter VM Service URL can be provided.');
  }
  if (args[0]?.startsWith('--')) {
    throw new Error(`Unknown option: ${args[0]}`);
  }
  return args[0];
}

function validateSmokePayload(result) {
  if (
    result?.wrote !== true ||
    result?.readBackMatches !== true ||
    result?.deleted !== true ||
    result?.keyPrefix !== 'debug.secure_storage_smoke'
  ) {
    throw new Error('Secure storage extension returned invalid payload.');
  }
}

function normalizeBaseUrl(value) {
  const url = new URL(value);
  if (!url.pathname.endsWith('/')) {
    url.pathname = `${url.pathname}/`;
  }
  return url;
}

async function getJson(baseUrl, methodPath) {
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

async function getExtensionJson(baseUrl, methodPath) {
  const deadline = Date.now() + 30000;
  let lastError;
  while (Date.now() < deadline) {
    try {
      return await getJson(baseUrl, methodPath);
    } catch (error) {
      lastError = error;
      if (!String(error.message).includes('Method not found')) {
        throw error;
      }
      await delay(500);
    }
  }
  throw lastError ?? new Error('Timed out waiting for service extension.');
}

function delay(milliseconds) {
  return new Promise((resolve) => {
    setTimeout(resolve, milliseconds);
  });
}
