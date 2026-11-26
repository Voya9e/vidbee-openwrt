# vidbee-openwrt

OpenWrt integration for [VidBee](https://github.com/nexmoe/VidBee).

简体中文 | [English](#english)

## 简体中文

本仓库用于将 VidBee 接入 OpenWrt。目前提供 `luci-app-vidbee`，在 LuCI 的 **服务 → VidBee** 中嵌入 VidBee Web，并提供在新标签页打开的入口。当前版本需要单独部署和启动 VidBee Web 与 API。

后续计划新增 `vidbee` 软件包，将 API、官方 Web 和服务启动脚本打包到 OpenWrt。届时 `luci-app-vidbee` 负责服务配置和 Web 入口，下载任务由官方 Web 管理。

### 要求

- 已安装 LuCI 的 OpenWrt
- VidBee Web UI 可通过路由器主机名的 **3000** 端口访问
- VidBee Web 服务允许被 LuCI 页面嵌入

入口根据当前 LuCI 页面使用的主机名和协议生成 VidBee 地址。若 VidBee 使用其他主机或端口，请修改 `htdocs/luci-static/resources/view/vidbee.js`。如果服务设置了禁止嵌入的 frame 策略，可使用页面上的新标签页按钮。

### 构建

在已安装 LuCI feed 的 OpenWrt 构建树根目录中，将仓库克隆到软件包目录，并编译当前的 LuCI 插件。

```sh
git clone https://github.com/Voya9e/vidbee-openwrt.git package/luci-app-vidbee
make package/luci-app-vidbee/compile
```

安装生成的软件包（APK 或 IPK，取决于 OpenWrt 版本），然后通过 LuCI 的 **服务 → VidBee** 打开已部署的 VidBee Web。

简体中文界面翻译位于 `po/zh_Hans/vidbee.po`。LuCI 选择简体中文时显示中文；其他语言默认显示英文。

## English

This repository integrates VidBee with OpenWrt. It currently provides `luci-app-vidbee`, which embeds VidBee Web under **Services → VidBee** in LuCI and offers a shortcut to open it in a new tab. The current version requires a separately deployed and running VidBee Web UI and API.

The planned `vidbee` package will bundle the API, official Web UI, and service startup scripts for OpenWrt. `luci-app-vidbee` will handle service configuration and link to the Web UI, where you manage downloads.

### Requirements

- OpenWrt with LuCI
- VidBee Web UI reachable on port **3000** using the router's hostname
- VidBee's web service allows embedding in a frame

The entry builds the VidBee URL from the hostname and protocol used by the current LuCI page. If VidBee uses another host or port, edit `htdocs/luci-static/resources/view/vidbee.js`. Use the new-tab button if the service's frame policy prevents embedding.

### Build

From the root of an OpenWrt build tree with the LuCI feed installed, clone the repository into the package directory and build the current LuCI app.

```sh
git clone https://github.com/Voya9e/vidbee-openwrt.git package/luci-app-vidbee
make package/luci-app-vidbee/compile
```

Install the resulting package (APK or IPK, depending on your OpenWrt version), then open the deployed VidBee Web UI from **Services → VidBee** in LuCI.

Simplified Chinese translations are in `po/zh_Hans/vidbee.po`. LuCI uses them when Simplified Chinese is selected and falls back to the English source strings.
