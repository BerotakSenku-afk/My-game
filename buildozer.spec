[app]
title = Brick Blaster Dynamic
package.name = brickblaster
package.domain = org.game
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf
version = 1.0
requirements = python3, pygame
orientation = portrait
osx.kivy_version = 2.1.0
fullscreen = 1
icon.filename = %(source.dir)s/ikon_setting.png
android.permissions = android.permission.VIBRATE
android.api = 33
android.minapi = 21
android.ndk_api = 21
android.archs = armeabi-v7a, arm64-v8a
p4a.branch = master

[buildozer]
log_level = 2
warn_on_root = 1
