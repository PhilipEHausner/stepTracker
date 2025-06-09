from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.clock import Clock
from plyer import accelerometer
from kivy.storage.jsonstore import JsonStore
from datetime import datetime


class StepTrackerLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', padding=20, spacing=10, **kwargs)

        self.store = JsonStore("steps_data.json")
        self.current_date = datetime.now().strftime("%Y-%m-%d")
        self.steps = self.load_steps_for_today()

        self.last_accel = 0
        self.threshold = 1.2  # tune as needed
        self.tracking = False

        self.step_label = Label(text=f"Steps: {self.steps}", font_size=32)
        self.add_widget(self.step_label)

        self.start_button = Button(text="Start Tracking", size_hint=(1, 0.2))
        self.start_button.bind(on_press=self.start_tracking)
        self.add_widget(self.start_button)

        self.stop_button = Button(text="Stop Tracking", size_hint=(1, 0.2))
        self.stop_button.bind(on_press=self.stop_tracking)
        self.add_widget(self.stop_button)

        self.reset_button = Button(text="Reset Steps", size_hint=(1, 0.2))
        self.reset_button.bind(on_press=self.reset_steps)
        self.add_widget(self.reset_button)

        # Check daily reset every minute
        Clock.schedule_interval(self.check_new_day, 60)

    def load_steps_for_today(self):
        if self.store.exists(self.current_date):
            return self.store.get(self.current_date)["steps"]
        else:
            return 0

    def save_steps(self):
        self.store.put(self.current_date, steps=self.steps)

    def start_tracking(self, instance):
        try:
            accelerometer.enable()
            self.tracking = True
            Clock.schedule_interval(self.detect_step, 0.1)
        except NotImplementedError:
            self.step_label.text = "Accelerometer not supported"

    def stop_tracking(self, instance):
        self.tracking = False
        Clock.unschedule(self.detect_step)
        try:
            accelerometer.disable()
        except:
            pass

    def reset_steps(self, instance):
        self.steps = 0
        self.save_steps()
        self.step_label.text = f"Steps: {self.steps}"

    def detect_step(self, dt):
        if not self.tracking:
            return

        val = accelerometer.acceleration
        if val != (None, None, None):
            x, y, z = val
            magnitude = (x**2 + y**2 + z**2)**0.5
            if abs(magnitude - self.last_accel) > self.threshold:
                self.steps += 1
                self.step_label.text = f"Steps: {self.steps}"
                self.save_steps()
            self.last_accel = magnitude

    def check_new_day(self, dt):
        today = datetime.now().strftime("%Y-%m-%d")
        if today != self.current_date:
            self.current_date = today
            self.steps = self.load_steps_for_today()
            self.step_label.text = f"Steps: {self.steps}"


class StepTrackerApp(App):
    def build(self):
        return StepTrackerLayout()


if __name__ == '__main__':
    StepTrackerApp().run()
