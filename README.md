# vidbee-openwrt

OpenWrt integration for [VidBee](https://github.com/nexmoe/VidBee).

[简体中文](#简体中文) | [English](#english)

## 简体中文

| 软件包 | 用途 |
| --- | --- |
| `vidbee` | 在 OpenWrt 原生运行 VidBee API 和官方 Web，用于管理下载。 |
| `luci-app-vidbee` | 在 LuCI 的 **服务 → VidBee** 提供 Web 入口。也可连接单独部署的 VidBee。 |

### 安装与启动

后端的初始目标是 OpenWrt 25.12、`mediatek/filogic`（如 RAX3000M）。APK 包含配套的 ARM64 Node.js 和 SQLite 模块，下载工具由 OpenWrt 软件源提供。首版 APK 约 51 MiB，解包后约 153 MiB，另计下载工具和媒体文件。当前构建省略本地转录运行库，yt-dlp 通过 OpenWrt 软件包更新。

安装 `vidbee` APK 后，编辑 `/etc/config/vidbee`，将 `data_dir` 和 `download_dir` 设为有足够空间的目录，再启用服务。新目录由服务创建，已有目录需允许 `vidbee` 用户读写。默认同时下载一个任务。

```sh
uci set vidbee.main.enabled='1'
uci commit vidbee
/etc/init.d/vidbee enable
/etc/init.d/vidbee start
```

默认 Web 入口为 `http://路由器地址:3000`，API 只监听本机。Web 没有独立登录页，请在可信局域网使用。LuCI 插件仍使用当前页面的主机名和协议访问 3000 端口，服务配置目前通过 UCI 操作。

### 构建

使用 OpenWrt 25.12 Filogic SDK 或对应的固件构建树。构建主机需要 Python 3.12 和 `patchelf`。构建过程从 GHCR 下载固定摘要的官方 ARM64 镜像层并校验 SHA-256。将仓库的 `packages/vidbee` 复制为构建树的 `package/vidbee`，将根目录的 `Makefile`、`htdocs`、`po`、`root` 复制到 `package/luci-app-vidbee`。

```sh
./scripts/feeds update base luci packages # 使用完整固件源码时去掉 base
./scripts/feeds install ca-bundle luci-base yt-dlp ffmpeg ffprobe
printf '%s\n' 'CONFIG_PACKAGE_vidbee=m' 'CONFIG_PACKAGE_luci-app-vidbee=m' >> .config
make defconfig
make package/vidbee/compile package/luci-app-vidbee/compile
```

编译固件时可分别将两个包设为 `y`。GitHub Actions 使用同一套 SDK 构建可安装的 APK。

## English

| Package | Purpose |
| --- | --- |
| `vidbee` | Runs the upstream API and Web UI natively on OpenWrt for managing downloads. |
| `luci-app-vidbee` | Opens VidBee Web from **Services → VidBee** in LuCI. It also works with a separately deployed VidBee service. |

### Installation and startup

The backend initially targets OpenWrt 25.12 on `mediatek/filogic`, including the RAX3000M. The APK ships compatible ARM64 Node.js and SQLite binaries and uses the OpenWrt feed for download tools. The first APK is about 51 MiB and unpacks to about 153 MiB before download tools and media files. This build omits the local transcription runtime. Update yt-dlp through the OpenWrt package manager.

After installing the backend APK, set `data_dir` and `download_dir` in `/etc/config/vidbee` to locations with enough space and enable the service. The service creates new directories. Existing directories must be writable by the `vidbee` user. The default is one concurrent download.

```sh
uci set vidbee.main.enabled='1'
uci commit vidbee
/etc/init.d/vidbee enable
/etc/init.d/vidbee start
```

The default Web URL is `http://<router-address>:3000`. The API listens on loopback. Use the Web UI on a trusted LAN, as it has no separate login. The LuCI shortcut uses the current hostname and protocol on port 3000. Manage service settings through UCI.

### Build

Use the OpenWrt 25.12 Filogic SDK or a matching firmware build tree. Install Python 3.12 and `patchelf` on the build host. The build verifies the SHA-256 digest of each pinned ARM64 image layer fetched from GHCR. Copy `packages/vidbee` to `package/vidbee` and copy the repository root's `Makefile`, `htdocs`, `po` and `root` to `package/luci-app-vidbee`.

```sh
./scripts/feeds update base luci packages # Omit base in a full firmware source tree
./scripts/feeds install ca-bundle luci-base yt-dlp ffmpeg ffprobe
printf '%s\n' 'CONFIG_PACKAGE_vidbee=m' 'CONFIG_PACKAGE_luci-app-vidbee=m' >> .config
make defconfig
make package/vidbee/compile package/luci-app-vidbee/compile
```

Select either package with `y` when building it into a firmware image. GitHub Actions uses the same SDK to build installable APKs.

### Upstream sources

- [VidBee API and Web source revision](https://github.com/nexmoe/VidBee/tree/438e4733ec557b8a8e529342f2bddb3d91c4a573)
- [Node.js v22.23.5 source](https://github.com/nodejs/node/tree/v22.23.5) and [Alpine-based build recipes](https://github.com/nodejs/docker-node)
- Alpine build recipes for [musl 1.2.6-r3](https://gitlab.alpinelinux.org/alpine/aports/-/tree/8f79d39391b46d6dbf1800fb68b8212a21d5ee2e/main/musl) and [GCC runtime 15.2.0-r5](https://gitlab.alpinelinux.org/alpine/aports/-/tree/423a8ad043d07f2c7546c8ec3e2b0384cda360ae/main/gcc)
- [better-sqlite3 v13.0.3 source](https://github.com/WiseLibs/better-sqlite3/tree/v13.0.3)
