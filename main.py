import kivy
kivy.require("2.3.0")

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.utils import get_color_from_hex
from datetime import datetime, timedelta

import firebase_admin
from firebase_admin import credentials, firestore

# --------------------------------------------------------
# FIREBASE BAĞLANTISI
# --------------------------------------------------------
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)
db = firestore.client()


# ========================================================
# 1) BERBER LİSTE
# ========================================================
class BarberListScreen(Screen):
    def on_pre_enter(self):
        self.ids.barber_list.clear_widgets()

        barbers = db.collection("BarberApp").stream()
        for barber in barbers:
            data = barber.to_dict()

            btn = Button(
                text=data.get("name", "İsimsiz"),
                size_hint_y=None,
                height=60,
                font_size=20
            )
            btn.bind(on_release=lambda x, bid=barber.id: self.open_detail(bid))
            self.ids.barber_list.add_widget(btn)

    def open_detail(self, barber_id):
        screen = self.manager.get_screen("detail")
        screen.load_barber(barber_id)
        self.manager.current = "detail"

    def go_add_barber(self):
        self.manager.current = "addbarber"

    def go_admin(self):
        self.manager.current = "adminlogin"


# ========================================================
# 2) BERBER DETAY
# ========================================================
class BarberDetailScreen(Screen):
    barber_id = None

    def load_barber(self, barber_id):
        self.barber_id = barber_id

        self.ids.services_box.clear_widgets()
        self.ids.prices_box.clear_widgets()

        doc = db.collection("BarberApp").document(barber_id).get()
        data = doc.to_dict() or {}

        # Fotoğraf
        self.ids.barber_photo.source = data.get("photo", "")

        self.ids.barber_name.text = data.get("name", "")
        self.ids.barber_phone.text = "Telefon: " + data.get("phone", "")
        self.ids.barber_location.text = "Konum: " + data.get("location", "")

        # Hizmetler
        services = data.get("services", [])
        for s in services:
            self.ids.services_box.add_widget(Label(
                text="• " + str(s),
                size_hint_y=None,
                height=30,
                font_size=18
            ))

        # Fiyatlar
        prices = data.get("prices", [])
        for p in prices:
            if isinstance(p, str):
                self.ids.prices_box.add_widget(Label(
                    text="• " + p,
                    size_hint_y=None,
                    height=30
                ))
                continue

            service_name = p.get("Service") or p.get("service") or p.get("name")
            price_value = p.get("Price") or p.get("price")

            self.ids.prices_box.add_widget(
                Label(
                    text=f"• {service_name}: {price_value}",
                    size_hint_y=None,
                    height=30
                )
            )

    def go_appointment(self):
        a = self.manager.get_screen("appointment")
        a.barber_id = self.barber_id
        a.selected_date_value = None
        a.selected_time_value = None
        self.manager.current = "appointment"

    def go_list(self):
        l = self.manager.get_screen("appointments")
        l.barber_id = self.barber_id
        self.manager.current = "appointments"

    def go_edit(self):
        e = self.manager.get_screen("editbarber")
        e.load_barber(self.barber_id)
        self.manager.current = "editbarber"


# ========================================================
# 3) TARİH SEÇİM
# ========================================================
class DateSelectScreen(Screen):
    caller_screen = None

    def on_pre_enter(self):
        self.ids.date_list.clear_widgets()
        today = datetime.today()

        for i in range(30):
            day = today + timedelta(days=i)
            label = day.strftime("%Y-%m-%d")

            btn = Button(
                text=label,
                size_hint_y=None,
                height=45
            )
            btn.bind(on_release=lambda x, v=label: self.select_date(v))
            self.ids.date_list.add_widget(btn)

    def select_date(self, value):
        self.caller_screen.selected_date_value = value
        self.caller_screen.ids.selected_date.text = "Seçilen tarih: " + value
        self.caller_screen.on_pre_enter()
        self.manager.current = "appointment"


# ========================================================
# 4) RANDEVU OLUŞTURMA
# ========================================================
class AppointmentScreen(Screen):
    barber_id = None
    selected_date_value = None
    selected_time_value = None

    COLOR_AVAILABLE = get_color_from_hex("#2ecc71")
    COLOR_FULL = get_color_from_hex("#e74c3c")
    COLOR_PAST = get_color_from_hex("#7f8c8d")

    def on_pre_enter(self):
        self.ids.time_buttons.clear_widgets()
        self.ids.selected_time.text = "Saat seçilmedi"

        if self.selected_date_value:
            self.generate_time_slots()

    def open_date_select(self):
        d = self.manager.get_screen("dateselect")
        d.caller_screen = self
        self.manager.current = "dateselect"

    def generate_time_slots(self):
        start = datetime.strptime("09:00", "%H:%M")
        end = datetime.strptime("21:00", "%H:%M")

        today = datetime.today().strftime("%Y-%m-%d")
        now_time = datetime.now().strftime("%H:%M")

        appointments = db.collection("BarberApp").document(self.barber_id).collection("Appointments") \
            .where("date", "==", self.selected_date_value).stream()

        booked = [a.to_dict().get("time") for a in appointments]

        while start < end:
            t = start.strftime("%H:%M")
            btn = Button(text=t, size_hint_y=None, height=45)

            if self.selected_date_value == today and t < now_time:
                btn.disabled = True
                btn.background_color = self.COLOR_PAST
            elif t in booked:
                btn.disabled = True
                btn.background_color = self.COLOR_FULL
            else:
                btn.background_color = self.COLOR_AVAILABLE
                btn.bind(on_release=lambda x, v=t: self.select_time(v))

            self.ids.time_buttons.add_widget(btn)
            start += timedelta(minutes=30)

    def select_time(self, t):
        self.selected_time_value = t
        self.ids.selected_time.text = "Seçilen saat: " + t

    def save_appointment(self):
        if not self.selected_date_value or not self.selected_time_value:
            print("Tarih veya saat eksik")
            return

        name = self.ids.input_name.text.strip()
        if not name:
            print("İsim girilmedi")
            return

        db.collection("BarberApp").document(self.barber_id).collection("Appointments").add({
            "name": name,
            "date": self.selected_date_value,
            "time": self.selected_time_value
        })

        print("Randevu kaydedildi!")
        self.manager.current = "detail"


# ========================================================
# 5) RANDEVU LİSTESİ
# ========================================================
class AppointmentListScreen(Screen):
    barber_id = None

    def on_pre_enter(self):
        self.ids.appointment_list.clear_widgets()

        items = db.collection("BarberApp").document(self.barber_id).collection("Appointments").stream()

        for a in items:
            d = a.to_dict()
            row = BoxLayout(size_hint_y=None, height=45, spacing=10)

            row.add_widget(Label(text=f"{d.get('date')}  {d.get('time')}  {d.get('name')}"))

            # Randevu iptal butonu
            cancel_btn = Button(
                text="Sil",
                size_hint_x=0.25,
                background_color=(0.8, 0.2, 0.2, 1)
            )
            cancel_btn.bind(on_release=lambda x, doc_id=a.id: self.delete_appointment(doc_id))
            row.add_widget(cancel_btn)

            self.ids.appointment_list.add_widget(row)

    def delete_appointment(self, appointment_id):
        db.collection("BarberApp").document(self.barber_id).collection("Appointments").document(appointment_id).delete()
        print("Randevu silindi!")
        self.on_pre_enter()

    def go_back(self):
        self.manager.current = "detail"


# ========================================================
# 6) YENİ BERBER EKLE
# ========================================================
class AddBarberScreen(Screen):
    def save_new_barber(self):
        name = self.ids.add_name.text.strip()
        if not name:
            print("Ad boş olamaz")
            return

        db.collection("BarberApp").add({
            "name": name,
            "phone": self.ids.add_phone.text.strip(),
            "location": self.ids.add_location.text.strip(),
            "photo": self.ids.add_photo.text.strip(),
            "services": [],
            "prices": []
        })

        print("Berber eklendi!")
        self.manager.current = "barbers"


# ========================================================
# 7) BERBER DÜZENLE
# ========================================================
class EditBarberScreen(Screen):
    barber_id = None

    def load_barber(self, barber_id):
        self.barber_id = barber_id
        doc = db.collection("BarberApp").document(barber_id).get()
        data = doc.to_dict() or {}

        self.ids.edit_name.text = data.get("name", "")
        self.ids.edit_phone.text = data.get("phone", "")
        self.ids.edit_location.text = data.get("location", "")
        self.ids.edit_photo.text = data.get("photo", "")

    def save_changes(self):
        db.collection("BarberApp").document(self.barber_id).update({
            "name": self.ids.edit_name.text.strip(),
            "phone": self.ids.edit_phone.text.strip(),
            "location": self.ids.edit_location.text.strip(),
            "photo": self.ids.edit_photo.text.strip()
        })

        print("Berber güncellendi!")
        self.manager.current = "detail"

# ======================================================
# 10) ADMIN - TÜM RANDEVULARI YÖNET
# ======================================================
class AdminAppointmentScreen(Screen):

    def on_pre_enter(self):
        self.ids.admin_appointment_list.clear_widgets()

        barbers = db.collection("BarberApp").stream()

        for barber in barbers:
            bdata = barber.to_dict()
            barber_name = bdata.get("name", "Berber")

            # Berber başlığı
            self.ids.admin_appointment_list.add_widget(
                Label(
                    text=f"[b]{barber_name}[/b]",
                    markup=True,
                    size_hint_y=None,
                    height=40,
                    color=(0.96, 0.82, 0.26, 1),
                    font_size=22
                )
            )

            # Randevular
            appointments = db.collection("BarberApp") \
                .document(barber.id) \
                .collection("Appointments") \
                .order_by("date") \
                .stream()

            for a in appointments:
                data = a.to_dict()
                row = BoxLayout(size_hint_y=None, height=45, spacing=10)

                row.add_widget(
                    Label(
                        text=f"{data['date']} - {data['time']} | {data['name']}",
                        color=(1,1,1,1)
                    )
                )

                # ONAYLA (sadece yazı, gerçek onay sistemi istenirse ekleriz)
                ok_btn = Button(
                    text="Onayla",
                    size_hint_x=0.25,
                    background_normal="",
                    background_color=(0.2, 0.5, 0.2, 1),
                    color=(1,1,1,1)
                )

                # SİL
                del_btn = Button(
                    text="Sil",
                    size_hint_x=0.25,
                    background_normal="",
                    background_color=(0.6, 0.1, 0.1, 1),
                    color=(1,1,1,1)
                )
                del_btn.bind(on_release=lambda btn, barber_id=barber.id, app_id=a.id: self.delete_appointment(barber_id, app_id))

                row.add_widget(ok_btn)
                row.add_widget(del_btn)

                self.ids.admin_appointment_list.add_widget(row)

    def delete_appointment(self, barber_id, app_id):
        db.collection("BarberApp").document(barber_id) \
          .collection("Appointments").document(app_id).delete()

        print("Randevu silindi!")
        self.on_pre_enter()  # ekranı yenile

    def go_back(self):
        setattr(self.manager, "current", "adminpanel")



# ========================================================
# 8) ADMIN GİRİŞ
# ========================================================
class AdminLoginScreen(Screen):
    ADMIN_PASSWORD = "TalhaKara65"

    def check_password(self):
        pwd = self.ids.admin_password.text.strip()

        if pwd == self.ADMIN_PASSWORD:
            self.ids.admin_error.text = ""
            self.manager.current = "adminpanel"
        else:
            self.ids.admin_error.text = "Şifre hatalı!"


# ========================================================
# 9) ADMIN PANEL
# ========================================================
class AdminPanelScreen(Screen):
    def go_add_barber(self):
        self.manager.current = "addbarber"

    def go_home(self):
        self.manager.current = "barbers"

    def go_admin_appointments(self):
       setattr(self.manager, "current", "adminappointments")



# ========================================================
# APP
# ========================================================
class MyApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(BarberListScreen(name="barbers"))
        sm.add_widget(BarberDetailScreen(name="detail"))
        sm.add_widget(AppointmentScreen(name="appointment"))
        sm.add_widget(DateSelectScreen(name="dateselect"))
        sm.add_widget(AppointmentListScreen(name="appointments"))
        sm.add_widget(AddBarberScreen(name="addbarber"))
        sm.add_widget(EditBarberScreen(name="editbarber"))
        sm.add_widget(AdminLoginScreen(name="adminlogin"))
        sm.add_widget(AdminPanelScreen(name="adminpanel"))
        sm.add_widget(AdminAppointmentScreen(name="adminappointments"))
        return sm


if __name__ == "__main__":
    MyApp().run()
 