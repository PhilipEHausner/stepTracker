from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.clock import Clock
from plyer import accelerometer

class StepTrackerLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', padding=20, spacing=10, **kwargs)

        self.steps = 0
        self.last_accel = 0
        self.threshold = 1.2  # tune as needed
        self.tracking = False

        self.step_label = Label(text="Steps: 0", font_size=32)
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
        self.step_label.text = "Steps: 0"

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
            self.last_accel = magnitude

class StepTrackerApp(App):
    def build(self):
        return StepTrackerLayout()

if __name__ == '__main__':
    StepTrackerApp().run()
