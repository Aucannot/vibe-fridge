#!/usr/bin/env node

import { spawn } from 'node:child_process';
import { existsSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const repoRoot = path.resolve(
  path.dirname(fileURLToPath(import.meta.url)),
  '..',
);
const defaultFlutterBin = path.join(
  repoRoot,
  '.tools',
  'flutter',
  'bin',
  'flutter',
);
const checkScript = path.join(repoRoot, 'tools', 'check_notification_status.mjs');

try {
  await main();
} catch (error) {
  console.error(`macOS notification smoke failed: ${error.message}`);
  process.exit(1);
}

async function main() {
  const options = parseArgs(process.argv.slice(2));
  const flutterBin =
    options.flutterBin ??
    (existsSync(defaultFlutterBin) ? defaultFlutterBin : 'flutter');

  const run = spawn(flutterBin, ['run', '-d', 'macos'], {
    cwd: path.join(repoRoot, 'mobile'),
    env: process.env,
    stdio: ['pipe', 'pipe', 'pipe'],
  });

  try {
    const vmServiceUrl = await waitForVmServiceUrl(run, options.timeoutMs);
    const checkArgs = [checkScript, ...expectationArgs(options), vmServiceUrl];
    const status = await runNode(checkArgs);
    process.stdout.write(status);
  } finally {
    await stopProcess(run);
  }
}

function parseArgs(args) {
  const options = {
    expectSupported: undefined,
    expectGranted: undefined,
    expectStatus: undefined,
    flutterBin: undefined,
    timeoutMs: 120000,
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
    if (arg === '--flutter-bin') {
      options.flutterBin = requireValue(arg, args[++index]);
      continue;
    }
    if (arg === '--timeout-ms') {
      options.timeoutMs = parsePositiveInteger(arg, args[++index]);
      continue;
    }
    throw new Error(`Unknown option: ${arg}`);
  }
  return options;
}

function expectationArgs(options) {
  const args = [];
  if (options.expectSupported !== undefined) {
    args.push('--expect-supported', String(options.expectSupported));
  }
  if (options.expectGranted !== undefined) {
    args.push('--expect-granted', String(options.expectGranted));
  }
  if (options.expectStatus !== undefined) {
    args.push('--expect-status', options.expectStatus);
  }
  return args;
}

function waitForVmServiceUrl(run, timeoutMs) {
  return new Promise((resolve, reject) => {
    let settled = false;
    let outputTail = '';
    const timer = setTimeout(() => {
      fail(
        new Error(
          `Timed out after ${timeoutMs}ms waiting for Flutter VM Service URL.`,
        ),
      );
    }, timeoutMs);

    run.once('error', fail);
    run.once('exit', (code, signal) => {
      if (settled) {
        return;
      }
      fail(
        new Error(
          `flutter run exited before VM Service was ready ` +
            `(code=${code}, signal=${signal}).\n${outputTail}`,
        ),
      );
    });

    const handleChunk = (chunk) => {
      const text = chunk.toString();
      process.stderr.write(text);
      outputTail = `${outputTail}${text}`.slice(-4000);
      const match = text.match(
        /A Dart VM Service on macOS is available at:\s*(http:\/\/[^\s]+)/,
      );
      if (match) {
        settle(match[1]);
      }
    };

    run.stdout.on('data', handleChunk);
    run.stderr.on('data', handleChunk);

    function settle(value) {
      if (settled) {
        return;
      }
      settled = true;
      clearTimeout(timer);
      resolve(value);
    }

    function fail(error) {
      if (settled) {
        return;
      }
      settled = true;
      clearTimeout(timer);
      reject(error);
    }
  });
}

function runNode(args) {
  return new Promise((resolve, reject) => {
    const child = spawn(process.execPath, args, {
      cwd: repoRoot,
      env: process.env,
      stdio: ['ignore', 'pipe', 'pipe'],
    });
    let stdout = '';
    let stderr = '';
    child.stdout.on('data', (chunk) => {
      stdout += chunk.toString();
    });
    child.stderr.on('data', (chunk) => {
      stderr += chunk.toString();
    });
    child.once('error', reject);
    child.once('exit', (code) => {
      if (code === 0) {
        resolve(stdout);
        return;
      }
      reject(new Error(stderr.trim() || `node exited with ${code}`));
    });
  });
}

function stopProcess(child) {
  return new Promise((resolve) => {
    if (child.exitCode !== null || child.signalCode !== null) {
      resolve();
      return;
    }
    child.stdin.write('q');
    const terminateTimer = setTimeout(() => {
      child.kill('SIGTERM');
    }, 5000);
    const killTimer = setTimeout(() => {
      child.kill('SIGKILL');
      resolve();
    }, 10000);
    child.once('exit', () => {
      clearTimeout(terminateTimer);
      clearTimeout(killTimer);
      resolve();
    });
  });
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

function parsePositiveInteger(name, value) {
  const raw = requireValue(name, value);
  const parsed = Number.parseInt(raw, 10);
  if (!Number.isInteger(parsed) || parsed <= 0) {
    throw new Error(`${name} must be a positive integer.`);
  }
  return parsed;
}

function requireValue(name, value) {
  if (!value || value.startsWith('--')) {
    throw new Error(`${name} requires a value.`);
  }
  return value;
}
