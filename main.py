from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.clock import Clock
from kivy.storage.jsonstore import JsonStore
from plyer import accelerometer
from kivy.graphics import Color, Rectangle
from kivy.uix.widget import Widget
from datetime import datetime, timedelta


class StepHistoryGraph(Widget):
    def __init__(self, store, **kwargs):
        super().__init__(**kwargs)
        self.store = store
        self.days_to_show = 7
        self.labels = []
        self.bind(pos=self.redraw, size=self.redraw)

        # Create labels once
        for _ in range(self.days_to_show):
            lbl = Label(font_size=12, size_hint=(None, None), size=(40, 20))
            self.labels.append(lbl)
            self.add_widget(lbl)

    def redraw(self, *args):
        self.canvas.clear()

        today = datetime.now()
        max_steps = 1  # avoid division by zero
        step_counts = []

        for i in range(self.days_to_show - 1, -1, -1):
            date = (today - timedelta(days=i)).strftime("%Y-%m-%d")
            steps = self.store.get(date)["steps"] if self.store.exists(date) else 0
            step_counts.append(steps)
            if steps > max_steps:
                max_steps = steps

        with self.canvas:
            Color(0.7, 0.7, 0.7, 1)
            Rectangle(pos=(self.x, self.y + 30), size=(self.width, 2))

            bar_width = self.width / (self.days_to_show * 2)
            spacing = bar_width

            for i, steps in enumerate(step_counts):
                bar_height = (steps / max_steps) * (self.height - 50)
                bar_x = self.x + spacing + i * (bar_width + spacing)
                bar_y = self.y + 30

                Color(0.2, 0.6, 0.9, 1)
                Rectangle(pos=(bar_x, bar_y), size=(bar_width, bar_height))

        # Update label text and position
        for i in range(self.days_to_show):
            date = (today - timedelta(days=self.days_to_show - 1 - i)).strftime("%a")
            label_x = self.x + spacing + i * (bar_width + spacing) + bar_width / 4
            label_y = self.y + 5
            self.labels[i].text = date
            self.labels[i].pos = (label_x, label_y)


class StepTrackerLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', padding=20, spacing=10, **kwargs)

        self.store = JsonStore("steps_data.json")
        self.current_date = datetime.now().strftime("%Y-%m-%d")
        self.steps = self.load_steps_for_today()

        self.last_accel = 0
        self.threshold = 1.2  # tune as needed
        self.tracking = False

        self.step_label = Label(text=f"Steps: {self.steps}", font_size=32, size_hint=(1, 0.15))
        self.add_widget(self.step_label)

        self.graph = StepHistoryGraph(self.store, size_hint=(1, None), height=200)
        self.add_widget(self.graph)

        self.start_button = Button(text="Start Tracking", size_hint=(1, 0.15))
        self.start_button.bind(on_press=self.start_tracking)
        self.add_widget(self.start_button)

        self.stop_button = Button(text="Stop Tracking", size_hint=(1, 0.15))
        self.stop_button.bind(on_press=self.stop_tracking)
        self.add_widget(self.stop_button)

        self.reset_button = Button(text="Reset Steps", size_hint=(1, 0.15))
        self.reset_button.bind(on_press=self.reset_steps)
        self.add_widget(self.reset_button)

        Clock.schedule_interval(self.check_new_day, 60)

    def load_steps_for_today(self):
        if self.store.exists(self.current_date):
            return self.store.get(self.current_date)["steps"]
        else:
            return 0

    def save_steps(self):
        self.store.put(self.current_date, steps=self.steps)
        self.graph.redraw()

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
            self.graph.redraw()


class StepTrackerApp(App):
    def build(self):
        return StepTrackerLayout()


if __name__ == '__main__':
    StepTrackerApp().run()
