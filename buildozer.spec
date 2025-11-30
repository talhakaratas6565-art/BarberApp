[app]

title = BarberApp
package.name = barberapp
package.domain = org.test
source.dir = .
source.include_exts = py,kv,png,jpg,ttf,json
version = 1.0
requirements = python3,kivy,requests,google-auth,google-cloud-firestore
orientation = portrait
fullscreen = 0

android.api = 33
android.minapi = 21
android.sdk = 33
android.ndk = 25b
android.ndk_path = 
android.sdk_path = 
android.archs = arm64-v8a, armeabi-v7a

# İkon eklemiyorsan boş bırakabilirsin
icon.filename = 

[buildozer]
log_level = 2
warn_on_root = 0
