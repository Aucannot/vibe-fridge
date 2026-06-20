#!/usr/bin/env node

import { spawn } from 'node:child_process';
import { existsSync, readFileSync } from 'node:fs';
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
const androidLocalProperties = path.join(
  repoRoot,
  'mobile',
  'android',
  'local.properties',
);

try {
  await main();
} catch (error) {
  console.error(`Android environment check failed: ${error.message}`);
  process.exit(1);
}

async function main() {
  const options = parseArgs(process.argv.slice(2));
  const flutterBin =
    options.flutterBin ??
    (existsSync(defaultFlutterBin) ? defaultFlutterBin : 'flutter');
  const env = {
    ...process.env,
    HOME: options.home ?? process.env.HOME,
  };

  const devices = await run(flutterBin, ['devices'], env);
  const emulators = await run(flutterBin, ['emulators'], env);
  const doctor = await run(flutterBin, ['doctor', '-v'], env);
  const localProperties = readAndroidLocalProperties();
  const report = buildReport({
    devices,
    emulators,
    doctor,
    localProperties,
  });

  console.log(JSON.stringify(report, null, 2));
  if (!report.ready) {
    process.exit(1);
  }
}

function parseArgs(args) {
  const options = {
    flutterBin: undefined,
    home: '/private/tmp/vibe-fridge-flutter-home',
  };
  for (let index = 0; index < args.length; index += 1) {
    const arg = args[index];
    if (arg === '--flutter-bin') {
      options.flutterBin = requireValue(arg, args[++index]);
      continue;
    }
    if (arg === '--home') {
      options.home = requireValue(arg, args[++index]);
      continue;
    }
    throw new Error(`Unknown option: ${arg}`);
  }
  return options;
}

function requireValue(name, value) {
  if (!value || value.startsWith('--')) {
    throw new Error(`${name} requires a value.`);
  }
  return value;
}

function run(command, args, env) {
  return new Promise((resolve) => {
    const child = spawn(command, args, {
      cwd: repoRoot,
      env,
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
    child.once('error', (error) => {
      resolve({
        command: [command, ...args].join(' '),
        exitCode: null,
        stdout,
        stderr: `${stderr}${error.message}`,
      });
    });
    child.once('exit', (code, signal) => {
      resolve({
        command: [command, ...args].join(' '),
        exitCode: code,
        signal,
        stdout,
        stderr,
      });
    });
  });
}

function buildReport({
  devices,
  emulators,
  doctor,
  localProperties,
}) {
  const doctorText = `${doctor.stdout}\n${doctor.stderr}`;
  const devicesText = `${devices.stdout}\n${devices.stderr}`;
  const emulatorsText = `${emulators.stdout}\n${emulators.stderr}`;
  const androidSdkMissing =
    doctorText.includes('Unable to locate Android SDK') ||
    doctorText.includes('No Android SDK found');
  const androidToolchainReady =
    doctorText.includes('[✓] Android toolchain') && !androidSdkMissing;
  const androidDeviceReady = detectAndroidDevice(devicesText);
  const emulatorAvailable =
    emulators.exitCode === 0 &&
    !emulatorsText.includes('Unable to find any emulator sources') &&
    !emulatorsText.includes('No emulators available');
  const sdkPath = localProperties['sdk.dir'] ?? null;
  const ready = androidToolchainReady && (androidDeviceReady || emulatorAvailable);

  return {
    ready,
    androidToolchainReady,
    androidDeviceReady,
    emulatorAvailable,
    sdkPath,
    blockers: blockers({
      androidToolchainReady,
      androidDeviceReady,
      emulatorAvailable,
      androidSdkMissing,
      sdkPath,
    }),
    commands: {
      devices: summarizeCommand(devices),
      emulators: summarizeCommand(emulators),
      doctor: summarizeCommand(doctor),
    },
  };
}

function detectAndroidDevice(output) {
  return output
    .split('\n')
    .some((line) => /\b(android|android-arm|android-arm64|android-x64)\b/i.test(line));
}

function blockers({
  androidToolchainReady,
  androidDeviceReady,
  emulatorAvailable,
  androidSdkMissing,
  sdkPath,
}) {
  const items = [];
  if (!androidToolchainReady) {
    items.push(
      androidSdkMissing
        ? 'Android SDK is not configured for Flutter.'
        : 'Flutter Android toolchain is not ready.',
    );
  }
  if (!androidDeviceReady && !emulatorAvailable) {
    items.push('No Android device or emulator is available.');
  }
  return items;
}

function summarizeCommand(result) {
  return {
    command: result.command,
    exitCode: result.exitCode,
    signal: result.signal ?? null,
    outputTail: `${result.stdout}${result.stderr}`.trim().slice(-2000),
  };
}

function readAndroidLocalProperties() {
  if (!existsSync(androidLocalProperties)) {
    return {};
  }
  const entries = {};
  const text = readFileSync(androidLocalProperties, 'utf8');
  for (const line of text.split(/\r?\n/)) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith('#')) {
      continue;
    }
    const separator = trimmed.indexOf('=');
    if (separator === -1) {
      continue;
    }
    entries[trimmed.slice(0, separator).trim()] = trimmed
      .slice(separator + 1)
      .trim();
  }
  return entries;
}
