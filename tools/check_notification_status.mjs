#!/usr/bin/env node

try {
  await main();
} catch (error) {
  console.error(`Notification status smoke failed: ${error.message}`);
  process.exit(1);
}

async function main() {
  const options = parseArgs(process.argv.slice(2));
  const rawVmServiceUrl = options.vmServiceUrl;

  if (!rawVmServiceUrl) {
    console.error(usage());
    process.exit(64);
  }

  const baseUrl = normalizeBaseUrl(rawVmServiceUrl);
  const vm = await getJson(baseUrl, 'getVM');
  const isolateId = vm.result?.isolates?.find(
    (isolate) => isolate?.isSystemIsolate !== true,
  )?.id;
  if (!isolateId) {
    throw new Error('No runnable app isolate found in VM Service response.');
  }

  const status = await getJson(
    baseUrl,
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
  validateExpectations(result, options);

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
}

function usage() {
  return (
    'Usage: node tools/check_notification_status.mjs [options] ' +
    '<flutter-vm-service-url>\n\n' +
    'Options:\n' +
    '  --expect-supported true|false\n' +
    '  --expect-granted true|false\n' +
    '  --expect-status <status>'
  );
}

function parseArgs(args) {
  const options = {
    expectSupported: undefined,
    expectGranted: undefined,
    expectStatus: undefined,
    vmServiceUrl: undefined,
  };

  for (let index = 0; index < args.length; index += 1) {
    const arg = args[index];
    if (arg === '--expect-supported') {
      options.expectSupported = parseBooleanOption(arg, args[++index]);
      continue;
    }
    if (arg === '--expect-granted') {
      options.expectGranted = parseBooleanOption(arg, args[++index]);
      continue;
    }
    if (arg === '--expect-status') {
      options.expectStatus = requireValue(arg, args[++index]);
      continue;
    }
    if (arg.startsWith('--')) {
      throw new Error(`Unknown option: ${arg}`);
    }
    if (options.vmServiceUrl) {
      throw new Error('Only one Flutter VM Service URL can be provided.');
    }
    options.vmServiceUrl = arg;
  }
  return options;
}

function validateExpectations(result, options) {
  const checks = [
    ['supported', result.supported, options.expectSupported],
    ['granted', result.granted, options.expectGranted],
    ['status', result.status, options.expectStatus],
  ];

  for (const [field, actual, expected] of checks) {
    if (expected === undefined || actual === expected) {
      continue;
    }
    throw new Error(
      `Expected notification ${field} to be ${expected}, got ${actual}.`,
    );
  }
}

function parseBooleanOption(name, value) {
  const raw = requireValue(name, value);
  if (raw === 'true') {
    return true;
  }
  if (raw === 'false') {
    return false;
  }
  throw new Error(`${name} must be true or false.`);
}

function requireValue(name, value) {
  if (!value || value.startsWith('--')) {
    throw new Error(`${name} requires a value.`);
  }
  return value;
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
