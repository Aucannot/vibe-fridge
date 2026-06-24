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

  const extensionName = options.sendTest
    ? 'ext.vibe_fridge.notificationTest'
    : 'ext.vibe_fridge.notificationStatus';
  const status = await getJsonWithRetry(
    baseUrl,
    `${extensionName}?isolateId=${encodeURIComponent(isolateId)}`,
    {
      retryMs: options.waitExtensionMs,
      shouldRetry: isMethodNotFoundError,
    },
  );
  const result = status.result;
  const permission = options.sendTest ? result?.permission : result;
  validatePermissionPayload(permission);
  if (options.sendTest) {
    validateTestPayload(result);
  }
  validateExpectations(result, permission, options);

  console.log(
    JSON.stringify(
      {
        isolateId,
        [options.sendTest ? 'notificationTest' : 'notificationStatus']: result,
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
    '  --expect-status <status>\n' +
    '  --wait-extension-ms <milliseconds>\n' +
    '  --send-test\n' +
    '  --expect-sent true|false\n' +
    '  --expect-skipped-reason <reason>'
  );
}

function parseArgs(args) {
  const options = {
    expectSupported: undefined,
    expectGranted: undefined,
    expectStatus: undefined,
    expectSent: undefined,
    expectSkippedReason: undefined,
    sendTest: false,
    waitExtensionMs: 0,
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
    if (arg === '--wait-extension-ms') {
      options.waitExtensionMs = parseNonNegativeInteger(arg, args[++index]);
      continue;
    }
    if (arg === '--send-test') {
      options.sendTest = true;
      continue;
    }
    if (arg === '--expect-sent') {
      options.expectSent = parseBooleanOption(arg, args[++index]);
      continue;
    }
    if (arg === '--expect-skipped-reason') {
      options.expectSkippedReason = requireValue(arg, args[++index]);
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
  if (!options.sendTest) {
    if (options.expectSent !== undefined) {
      throw new Error('--expect-sent requires --send-test.');
    }
    if (options.expectSkippedReason !== undefined) {
      throw new Error('--expect-skipped-reason requires --send-test.');
    }
  }
  return options;
}

function validatePermissionPayload(result) {
  if (
    typeof result?.supported !== 'boolean' ||
    typeof result?.granted !== 'boolean' ||
    typeof result?.status !== 'string' ||
    typeof result?.displayText !== 'string'
  ) {
    throw new Error('Notification status extension returned invalid payload.');
  }
}

function validateTestPayload(result) {
  if (
    typeof result?.sent !== 'boolean' ||
    typeof result?.displayText !== 'string' ||
    (result.skippedReason !== null &&
      result.skippedReason !== undefined &&
      typeof result.skippedReason !== 'string')
  ) {
    throw new Error('Notification test extension returned invalid payload.');
  }
}

function validateExpectations(result, permission, options) {
  const checks = [
    ['supported', permission.supported, options.expectSupported],
    ['granted', permission.granted, options.expectGranted],
    ['status', permission.status, options.expectStatus],
    ['sent', result.sent, options.expectSent],
    ['skippedReason', result.skippedReason, options.expectSkippedReason],
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

function parseNonNegativeInteger(name, value) {
  const raw = requireValue(name, value);
  const parsed = Number.parseInt(raw, 10);
  if (!Number.isInteger(parsed) || parsed < 0) {
    throw new Error(`${name} must be a non-negative integer.`);
  }
  return parsed;
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

async function getJsonWithRetry(baseUrl, methodPath, options) {
  const deadline = Date.now() + options.retryMs;
  let lastError;

  do {
    try {
      return await getJson(baseUrl, methodPath);
    } catch (error) {
      lastError = error;
      if (!options.shouldRetry(error) || Date.now() >= deadline) {
        throw error;
      }
      await delay(500);
    }
  } while (Date.now() <= deadline);

  throw lastError;
}

function isMethodNotFoundError(error) {
  return /Method not found/i.test(error.message);
}

function delay(ms) {
  return new Promise((resolve) => {
    setTimeout(resolve, ms);
  });
}
