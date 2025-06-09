from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.togglebutton import ToggleButton
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
        self.view_mode = "weekly"  # default
        self.days_to_show = 7
        self.labels = []
        self.bind(pos=self.redraw, size=self.redraw)

        # create labels for max 31 days (monthly) or 12 months (yearly)
        max_labels = 31
        for _ in range(max_labels):
            lbl = Label(font_size=12, size_hint=(None, None), size=(40, 20))
            self.labels.append(lbl)
            self.add_widget(lbl)

    def set_view_mode(self, mode):
        self.view_mode = mode
        if mode == "weekly":
            self.days_to_show = 7
        elif mode == "monthly":
            self.days_to_show = 30
        elif mode == "yearly":
            self.days_to_show = 12  # 12 months
        self.redraw()

    def redraw(self, *args):
        self.canvas.clear()
        today = datetime.now()

        with self.canvas:
            # Draw base axis line
            Color(0.7, 0.7, 0.7, 1)
            Rectangle(pos=(self.x, self.y + 30), size=(self.width, 2))

            Color(0.2, 0.6, 0.9, 1)

            if self.view_mode in ("weekly", "monthly"):
                max_steps = 1
                step_counts = []
                days = self.days_to_show

                for i in range(days - 1, -1, -1):
                    date = (today - timedelta(days=i)).strftime("%Y-%m-%d")
                    steps = self.store.get(date)["steps"] if self.store.exists(date) else 0
                    step_counts.append(steps)
                    if steps > max_steps:
                        max_steps = steps

                bar_width = self.width / (days * 2)
                spacing = bar_width

                for i, steps in enumerate(step_counts):
                    bar_height = (steps / max_steps) * (self.height - 50)
                    bar_x = self.x + spacing + i * (bar_width + spacing)
                    bar_y = self.y + 30
                    Rectangle(pos=(bar_x, bar_y), size=(bar_width, bar_height))

                # Update day labels
                for i in range(days):
                    date = (today - timedelta(days=days - 1 - i)).strftime("%d")
                    label_x = self.x + spacing + i * (bar_width + spacing) + bar_width / 4
                    label_y = self.y + 5
                    self.labels[i].text = date
                    self.labels[i].pos = (label_x, label_y)

                # Hide unused labels
                for i in range(days, len(self.labels)):
                    self.labels[i].text = ""
            elif self.view_mode == "yearly":
                # Aggregate steps by month
                month_steps = []
                max_steps = 1
                for i in range(11, -1, -1):
                    month_date = (today.replace(day=1) - timedelta(days=30*i))
                    month_str = month_date.strftime("%Y-%m")
                    steps_sum = 0
                    # sum daily steps in this month
                    for day in range(1, 32):
                        try:
                            day_date = month_date.replace(day=day)
                            day_key = day_date.strftime("%Y-%m-%d")
                            if self.store.exists(day_key):
                                steps_sum += self.store.get(day_key)["steps"]
                        except ValueError:
                            break  # day out of range
                    month_steps.append(steps_sum)
                    if steps_sum > max_steps:
                        max_steps = steps_sum

                bar_width = self.width / (12 * 2)
                spacing = bar_width

                for i, steps in enumerate(month_steps):
                    bar_height = (steps / max_steps) * (self.height - 50)
                    bar_x = self.x + spacing + i * (bar_width + spacing)
                    bar_y = self.y + 30
                    Rectangle(pos=(bar_x, bar_y), size=(bar_width, bar_height))

                # Update month labels
                for i in range(12):
                    month_date = (today.replace(day=1) - timedelta(days=30*(11 - i)))
                    label = month_date.strftime("%b")
                    label_x = self.x + spacing + i * (bar_width + spacing) + bar_width / 4
                    label_y = self.y + 5
                    self.labels[i].text = label
                    self.labels[i].pos = (label_x, label_y)

                # Hide unused labels
                for i in range(12, len(self.labels)):
                    self.labels[i].text = ""

class StepTrackerLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', padding=20, spacing=10, **kwargs)

        self.store = JsonStore("steps_data.json")
        self.steps = 0
        self.last_accel = 0
        self.threshold = 1.2
        self.tracking = False

        self.step_label = Label(text="Steps: 0", font_size=32, size_hint=(1, 0.15))
        self.add_widget(self.step_label)

        # Toggle buttons for view mode
        toggle_layout = GridLayout(cols=3, size_hint=(1, 0.1), spacing=10)
        self.weekly_btn = ToggleButton(text="Weekly", group="view_mode", state="down")
        self.monthly_btn = ToggleButton(text="Monthly", group="view_mode")
        self.yearly_btn = ToggleButton(text="Yearly", group="view_mode")

        self.weekly_btn.bind(on_press=self.set_weekly_view)
        self.monthly_btn.bind(on_press=self.set_monthly_view)
        self.yearly_btn.bind(on_press=self.set_yearly_view)

        toggle_layout.add_widget(self.weekly_btn)
        toggle_layout.add_widget(self.monthly_btn)
        toggle_layout.add_widget(self.yearly_btn)
        self.add_widget(toggle_layout)

        self.graph = StepHistoryGraph(self.store, size_hint=(1, None), height=200)
        self.add_widget(self.graph)

        # Your start/stop/reset buttons go here...

        self.view_mode = "weekly"
        self.graph.set_view_mode(self.view_mode)

    def set_weekly_view(self, instance):
        if instance.state == "down":
            self.view_mode = "weekly"
            self.graph.set_view_mode(self.view_mode)

    def set_monthly_view(self, instance):
        if instance.state == "down":
            self.view_mode = "monthly"
            self.graph.set_view_mode(self.view_mode)

    def set_yearly_view(self, instance):
        if instance.state == "down":
            self.view_mode = "yearly"
            self.graph.set_view_mode(self.view_mode)

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
