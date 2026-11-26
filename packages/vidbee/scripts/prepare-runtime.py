#!/usr/bin/env python3
"""Prepare the native package from the official ARM64 image layers."""

import hashlib
import json
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.request import Request, urlopen

# Both images were built from nexmoe/VidBee@438e4733ec557b8a8e529342f2bddb3d91c4a573.
# The digests refer to the individual ARM64 layers needed by this package.
LAYERS = {
    "alpine": ("web", "b90627b8f4292fd3cb63f0f27f0b11c37f04ba88ef3b78d4948ea0ace18c85e9"),
    "node": ("web", "1d0a7305242947ff5acc28f1d1658e557b48f99d0f8173d83cdb90950dd8a154"),
    "api-deps": ("api", "bedc130a125076dc84737dbe52376a97fa3136a56d750cb55752d8328b43dc16"),
    "api-dist": ("api", "f9b37a582d7b25347955cc26ed1a7393e5cb1249249e0b7ac706f4765bd4e983"),
    "api-migrations": ("api", "e8cbc91ede44c2ba2bf4ec6953a5522be32d2a8b8eaa82c10773066c604faddc"),
    "web-dist": ("web", "7ccd4d20352cd86acc1479eb5789a714af1f59a963fc45fc0af88fcb5faddb68"),
    "web-server": ("web", "9b336a14070fe8f408406a30d503903ecc4955eccd79c08c47a38f20fc133c87"),
    "web-deps": ("web", "ee13ede397b3b897a73cb0396c5062a07f633b5575327361f69c348bbbfd05ed"),
}
PACKAGE_ROOT = "/usr/lib/vidbee"
UPSTREAM_LICENSES = {
    "VidBee.txt": (
        "https://raw.githubusercontent.com/nexmoe/VidBee/438e4733ec557b8a8e529342f2bddb3d91c4a573/LICENSE",
        "5cde322cd1fd10c409c8597eed127a08baa6c73b9430312de1aeb05f1dbb4953",
    ),
    "Node.js.txt": (
        "https://raw.githubusercontent.com/nodejs/node/v22.23.5/LICENSE",
        "c738ae413cf561f174e34f6961f8ca458aae2369a73640dda6234c629b98bcc4",
    ),
    "GCC.txt": (
        "https://raw.githubusercontent.com/gcc-mirror/gcc/releases/gcc-15.2.0/COPYING3",
        "8ceb4b9ee5adedde47b31e975c1d90c73ad27b6b165a1dcd80c7c545eb65b903",
    ),
    "GCC-Runtime-Exception.txt": (
        "https://raw.githubusercontent.com/gcc-mirror/gcc/releases/gcc-15.2.0/COPYING.RUNTIME",
        "9d6b43ce4d8de0c878bf16b54d8e7a10d9bd42b75178153e3af6a815bdc90f74",
    ),
}


def checksum(path):
    with path.open("rb") as stream:
        digest = hashlib.sha256()
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
        return digest.hexdigest()


def fetch_verified(make_request, destination, digest):
    if destination.is_file() and checksum(destination) == digest:
        return

    for attempt in range(3):
        try:
            with tempfile.NamedTemporaryFile(dir=destination.parent, delete=False) as temporary:
                partial = Path(temporary.name)
                try:
                    with urlopen(make_request(), timeout=90) as response:
                        shutil.copyfileobj(response, temporary)
                    temporary.flush()
                    if checksum(partial) != digest:
                        raise ValueError(f"SHA-256 does not match for {destination.name}")
                    partial.replace(destination)
                    return
                finally:
                    partial.unlink(missing_ok=True)
        except (OSError, ValueError):
            if attempt == 2:
                raise
            time.sleep(2 ** attempt)


def download_layer(item, cache):
    name, (app, digest) = item
    archive = cache / f"{name}-{digest}.tar.gz"
    repo = f"nexmoe/vidbee-{app}"

    def make_request():
        with urlopen(f"https://ghcr.io/token?scope=repository:{repo}:pull", timeout=30) as response:
            token = json.load(response)["token"]
        return Request(
            f"https://ghcr.io/v2/{repo}/blobs/sha256:{digest}",
            headers={"Authorization": f"Bearer {token}"},
        )

    fetch_verified(make_request, archive, digest)
    return name, archive


def extract(archive, destination, *paths):
    with tarfile.open(archive, "r:gz") as layer:
        members = [
            member for member in layer
            if any(member.name == path or member.name.startswith(path + "/") for path in paths)
        ]
        for path in paths:
            if not any(member.name == path or member.name.startswith(path + "/") for member in members):
                raise ValueError(f"{path} is missing from {archive.name}")
        layer.extractall(destination, members=members, filter="data")


def install_notices(cache, root):
    notices = root / "licenses"
    notices.mkdir()
    for name, (url, digest) in UPSTREAM_LICENSES.items():
        cached = cache / f"{digest}-{name}"
        fetch_verified(lambda: Request(url), cached, digest)
        shutil.copyfile(cached, notices / name)

    archive = cache / "musl-1.2.6.tar.gz"
    fetch_verified(lambda: Request("https://musl.libc.org/releases/musl-1.2.6.tar.gz"), archive,
                   "d585fd3b613c66151fc3249e8ed44f77020cb5e6c1e635a616d3f9f82460512a")
    with tarfile.open(archive, "r:gz") as source:
        copyright_file = source.extractfile("musl-1.2.6/COPYRIGHT")
        with copyright_file, (notices / "musl.txt").open("wb") as notice:
            shutil.copyfileobj(copyright_file, notice)


def adapt_api(bundle):
    # Keep OpenWrt's yt-dlp in use and disable transcription jobs on this download build.
    changes = {
        'var managedYtDlpPath = () => path5.join(apiDataDir, "bin", process.platform === "win32" ? "yt-dlp.exe" : "yt-dlp");':
            'var managedYtDlpPath = () => trimEnv("YTDLP_PATH") ?? "/usr/bin/yt-dlp";',
        'latestYtDlpVersion = await fetchLatestYtDlpTag();':
            'latestYtDlpVersion = current?.version ?? null;',
        'byKind: { transcription: transcriptionExecutor }':
            'byKind: {}',
        'autoEnabled = settings.autoTranscribeAfterDownload === true;':
            'autoEnabled = false;',
        'autoEnabled = enabled;':
            'autoEnabled = false;',
    }
    source = bundle.read_text(encoding="utf-8")
    for previous, replacement in changes.items():
        if source.count(previous) != 1:
            raise ValueError(f"Expected exactly one upstream match for {previous!r}")
        source = source.replace(previous, replacement)
    start = source.index('var updateYtDlp = async () => {')
    end = source.index('var checkEngineUpdates = async () => {', start)
    source = source[:start] + 'var updateYtDlp = async () => checkEngineUpdates();\n' + source[end:]
    bundle.write_text(source, encoding="utf-8")


def prepare(cache, output):
    cache.mkdir(parents=True, exist_ok=True)
    if not shutil.which("patchelf"):
        raise RuntimeError("Install patchelf on the OpenWrt build host.")
    with ThreadPoolExecutor(max_workers=4) as pool:
        archives = dict(pool.map(lambda item: download_layer(item, cache), LAYERS.items()))

    with tempfile.TemporaryDirectory(dir=output.parent) as temporary:
        tmp = Path(temporary)
        root = tmp / "payload"
        node = root / "node"
        lib = node / "lib"
        lib.mkdir(parents=True)
        (node / "bin").mkdir()
        alpine = tmp / "alpine"
        extract(archives["alpine"], alpine, "lib/ld-musl-aarch64.so.1", "lib/libc.musl-aarch64.so.1")
        extract(
            archives["node"], alpine, "usr/local/bin/node", "usr/lib/libgcc_s.so.1",
            "usr/lib/libstdc++.so.6", "usr/lib/libstdc++.so.6.0.34",
        )
        for name in ("ld-musl-aarch64.so.1", "libc.musl-aarch64.so.1"):
            shutil.copy2(alpine / "lib" / name, lib, follow_symlinks=False)
        for name in ("libgcc_s.so.1", "libstdc++.so.6", "libstdc++.so.6.0.34"):
            shutil.copy2(alpine / "usr/lib" / name, lib, follow_symlinks=False)
        binary = node / "bin/node"
        shutil.copy2(alpine / "usr/local/bin/node", binary)
        subprocess.run(
            ["patchelf", "--set-interpreter", f"{PACKAGE_ROOT}/node/lib/ld-musl-aarch64.so.1",
             "--force-rpath", "--set-rpath", "$ORIGIN/../lib", str(binary)],
            check=True,
        )

        sqlite = "app/node_modules/.pnpm/better-sqlite3@13.0.3/node_modules/better-sqlite3"
        extract(
            archives["api-deps"], tmp / "sqlite",
            f"{sqlite}/package.json", f"{sqlite}/LICENSE", f"{sqlite}/lib",
            f"{sqlite}/prebuilds/linuxmusl-arm64.node",
        )
        api = tmp / "api"
        extract(archives["api-dist"], api, "app/dist/index.js", "app/dist/migrate-history.js")
        extract(archives["api-migrations"], api, "app/resources/drizzle")
        (api / "app/node_modules").mkdir()
        (tmp / "sqlite" / sqlite).rename(api / "app/node_modules/better-sqlite3")
        (api / "app").rename(root / "api")
        adapt_api(root / "api/dist/index.js")

        web = tmp / "web"
        extract(archives["web-dist"], web, "app/dist")
        extract(archives["web-server"], web, "app/server.mjs")
        extract(archives["web-deps"], web, "app/node_modules/@vidbee/logger")
        (web / "app").rename(root / "web")

        # The bundles use ESM. Keep the declaration explicit for Node.
        for app in ("api", "web"):
            (root / app / "package.json").write_text('{"type":"module"}\n', encoding="utf-8")
        install_notices(cache, root)
        if output.exists():
            shutil.rmtree(output)
        root.rename(output)


if __name__ == "__main__":
    prepare(Path(sys.argv[1]), Path(sys.argv[2]))
