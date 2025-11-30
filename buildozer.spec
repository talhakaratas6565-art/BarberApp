[app]
title = BarberApp
package.name = barberapp
package.domain = org.talha
source.dir = .
source.include_exts = py,kv,json
requirements = python3,kivy
orientation = portrait
fullscreen = 0

[buildozer]
log_level = 2
warn_on_root = 1

# Hedef Android ayarları
android.api = 33
android.minapi = 21
android.archs = armeabi-v7a, arm64-v8a
android.permissions = INTERNET
