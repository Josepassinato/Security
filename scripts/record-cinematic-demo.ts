import { spawn, type ChildProcess } from 'node:child_process';
import { mkdirSync, rmSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { tmpdir } from 'node:os';

interface Args {
  baseUrl: string;
  outDir: string;
  durationSeconds: number;
}

const variants = ['executive', 'technical', 'backup'];

function readArgs(): Args {
  const args = process.argv.slice(2);
  const get = (flag: string) => {
    const index = args.indexOf(flag);
    return index >= 0 ? args[index + 1] : undefined;
  };
  return {
    baseUrl: get('--base-url') ?? process.env.DEMO_URL ?? 'http://127.0.0.1:3000/demo-cinematografica',
    outDir: resolve(get('--out-dir') ?? process.env.DEMO_VIDEO_DIR ?? 'artifacts/demo-videos'),
    durationSeconds: Number(get('--duration') ?? process.env.DEMO_RECORD_SECONDS ?? 28),
  };
}

function withDemoParams(baseUrl: string, variant: string): string {
  const url = new URL(baseUrl);
  url.searchParams.set('speed', url.searchParams.get('speed') ?? 'fast');
  url.searchParams.set('record', '1');
  url.searchParams.set('variant', variant);
  return url.toString();
}

function wait(ms: number) {
  return new Promise((resolveWait) => {
    setTimeout(resolveWait, ms);
  });
}

function spawnProcess(command: string, args: string[], env: NodeJS.ProcessEnv) {
  return spawn(command, args, {
    env,
    stdio: ['ignore', 'inherit', 'inherit'],
  });
}

async function stopProcess(processRef: ChildProcess, signal: NodeJS.Signals) {
  if (processRef.exitCode !== null) return;
  processRef.kill(signal);
  await Promise.race([
    new Promise((resolveStop) => processRef.once('exit', resolveStop)),
    wait(5000).then(() => {
      if (processRef.exitCode === null) processRef.kill('SIGKILL');
    }),
  ]);
}

async function recordVariant(args: Args, variant: string, display: string) {
  const env = { ...process.env, DISPLAY: display };
  const chromeBin = process.env.CHROME_BIN ?? '/usr/bin/google-chrome';
  const xvfbBin = process.env.XVFB_BIN ?? '/usr/bin/Xvfb';
  const ffmpegBin = process.env.FFMPEG_BIN ?? '/usr/bin/ffmpeg';
  const profileDir = join(tmpdir(), `quarry-cinematic-${variant}-${Date.now()}`);
  const outputPath = join(args.outDir, `demo-cinematografica-${variant}.mp4`);
  const url = withDemoParams(args.baseUrl, variant);

  const xvfb = spawnProcess(xvfbBin, [display, '-screen', '0', '1920x1080x24', '-nolisten', 'tcp'], env);
  await wait(900);

  const ffmpeg = spawnProcess(
    ffmpegBin,
    [
      '-hide_banner',
      '-loglevel',
      'error',
      '-y',
      '-video_size',
      '1920x1080',
      '-framerate',
      '30',
      '-f',
      'x11grab',
      '-i',
      `${display}.0`,
      '-codec:v',
      'libx264',
      '-preset',
      'veryfast',
      '-pix_fmt',
      'yuv420p',
      outputPath,
    ],
    env,
  );

  const chrome = spawnProcess(
    chromeBin,
    [
      '--no-sandbox',
      '--no-first-run',
      '--no-default-browser-check',
      '--disable-dev-shm-usage',
      '--disable-default-apps',
      '--disable-gpu',
      '--disable-logging',
      '--disable-sync',
      '--disable-search-engine-choice-screen',
      '--test-type',
      '--hide-scrollbars',
      '--window-size=1920,1080',
      `--user-data-dir=${profileDir}`,
      `--app=${url}`,
    ],
    env,
  );

  await wait(args.durationSeconds * 1000);
  await stopProcess(ffmpeg, 'SIGINT');
  await stopProcess(chrome, 'SIGTERM');
  await stopProcess(xvfb, 'SIGTERM');
  try {
    rmSync(profileDir, { recursive: true, force: true });
  } catch {
    // Chrome may flush profile files a moment after process shutdown. The
    // recording is already finalized, so temp cleanup must not fail the run.
  }
  return outputPath;
}

async function main() {
  const args = readArgs();
  mkdirSync(args.outDir, { recursive: true });
  for (const [index, variant] of variants.entries()) {
    const display = `:${90 + index}`;
    const outputPath = await recordVariant(args, variant, display);
    console.log(`recorded ${variant}: ${outputPath}`);
  }
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
