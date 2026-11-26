# SPDX-License-Identifier: Apache-2.0

include $(TOPDIR)/rules.mk

PKG_NAME:=vidbee
PKG_VERSION:=0.1.0
PKG_RELEASE:=1
PKG_LICENSE:=Apache-2.0 AND MIT AND (GPL-3.0-or-later WITH GCC-exception-3.1)

include $(INCLUDE_DIR)/package.mk

define Package/vidbee
  SECTION:=multimedia
  CATEGORY:=Multimedia
  TITLE:=VidBee download service and Web UI
  URL:=https://github.com/Voya9e/vidbee-openwrt
  DEPENDS:=@aarch64 +ca-bundle +yt-dlp +ffmpeg +ffprobe
  USERID:=vidbee:vidbee
endef

define Package/vidbee/description
  The upstream VidBee API and Web UI with a private Node.js runtime and
  SQLite module. Runs as an OpenWrt procd service without Docker.
endef

define Package/vidbee/conffiles
/etc/config/vidbee
endef

define Build/Prepare
	mkdir -p "$(PKG_BUILD_DIR)"
	python3 ./scripts/prepare-runtime.py "$(DL_DIR)/vidbee" "$(PKG_BUILD_DIR)/runtime"
endef

define Build/Configure
endef

define Build/Compile
endef

define Package/vidbee/install
	$(INSTALL_DIR) $(1)/usr/lib/vidbee $(1)/etc/init.d $(1)/etc/config
	$(CP) $(PKG_BUILD_DIR)/runtime/. $(1)/usr/lib/vidbee/
	$(INSTALL_BIN) ./files/vidbee.init $(1)/etc/init.d/vidbee
	$(INSTALL_BIN) ./files/start-api.sh $(1)/usr/lib/vidbee/start-api
	$(INSTALL_CONF) ./files/vidbee.config $(1)/etc/config/vidbee
endef

$(eval $(call BuildPackage,vidbee))
