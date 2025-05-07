import tkinter as tk
from tkinter import ttk
from tkinter.simpledialog import askstring
from collections import defaultdict


class WellPlateApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Well Plate Data Annotator")

        self.selected_plate_type = tk.StringVar()
        self.plate_canvas = None
        self.condition_data = defaultdict(dict)
        self.selected_wells = set()
        self.ctrl_held = False
        self.dragging = False

        self.color_map = {
            "Time": "blue",
            "Cytokine Concentration": "green",
            "Stain": "red"
        }
        #self.well_buttons = {}
        self._build_initial_ui()


    def _build_initial_ui(self):
        ttk.Label(self.root, text="Select Plate Type:").pack(pady=10)
        plate_menu = ttk.Combobox(self.root, textvariable=self.selected_plate_type, state="readonly")
        plate_menu['values'] = ("96-well plate",)
        plate_menu.pack()

        next_btn = ttk.Button(self.root, text="Next", command=self._show_plate_ui)
        next_btn.pack(pady=10)

    def _show_plate_ui(self):
        if self.selected_plate_type.get() == "96-well plate":
            self._render_plate(rows=8, cols=12)

    def _render_plate(self, rows, cols):
        for widget in self.root.winfo_children():
            widget.pack_forget()

        ttk.Label(self.root, text="96-Well Plate Layout").pack(pady=10)

        self.plate_canvas = tk.Canvas(self.root, width=1200, height=700, bg="white")
        self.plate_canvas.pack()

        self.well_rects = {}
        self.row_labels = [chr(i) for i in range(65, 65 + rows)]
        self.col_labels = list(range(1, cols + 1))
        self.well_texts = {}  # (row, col): text_id

        well_size = 60
        padding = 5
        offset_x = 60
        offset_y = 60

        # Draw column labels
        for j, col in enumerate(self.col_labels):
            self.plate_canvas.create_text(offset_x + j * (well_size + padding) + well_size / 2,
                                          offset_y - 20, text=str(col))

        # Draw row labels
        for i, row in enumerate(self.row_labels):
            self.plate_canvas.create_text(offset_x - 20,
                                          offset_y + i * (well_size + padding) + well_size / 2,
                                          text=row)

        # Draw wells
        for i, row in enumerate(self.row_labels):
            for j, col in enumerate(self.col_labels):
                x1 = offset_x + j * (well_size + padding)
                y1 = offset_y + i * (well_size + padding)
                x2 = x1 + well_size
                y2 = y1 + well_size
                well_id = f"{row}_{col}"
                rect = self.plate_canvas.create_rectangle(x1, y1, x2, y2, fill="white", outline="black", tags=well_id)
                self.well_rects[well_id] = rect

                text_id = self.plate_canvas.create_text((x1 + x2) / 2, (y1 + y2) / 2, text="", font=("Arial", 10))

                self.well_texts[well_id] = text_id


        self.plate_canvas.bind("<ButtonPress-1>", self._on_mouse_down)
        self.plate_canvas.bind("<B1-Motion>", self._on_mouse_drag)
        self.plate_canvas.bind("<ButtonRelease-1>", self._on_mouse_up)
        self.plate_canvas.bind("<Control-ButtonPress-1>", self._on_ctrl_click)

        self.root.bind("<Control_L>", self._ctrl_press)
        self.root.bind("<KeyRelease-Control_L>", self._ctrl_release)

        apply_btn = ttk.Button(self.root, text="Apply Condition to Selected Wells", command=self._apply_condition)
        apply_btn.pack(pady=10)

        # Draw legend
        legend_frame = tk.Frame(self.root)
        legend_frame.pack(side=tk.RIGHT, padx=20)

        tk.Label(legend_frame, text="Legend", font=("Arial", 12, "bold")).pack()
        for condition, color in self.color_map.items():
            frame = tk.Frame(legend_frame)
            frame.pack(anchor='w', pady=2)
            tk.Label(frame, width=2, height=1, bg=color).pack(side='left')
            tk.Label(frame, text=f" {condition}").pack(side='left')


    def _ctrl_press(self, event):
        self.ctrl_held = True

    def _ctrl_release(self, event):
        self.ctrl_held = False

    def _on_ctrl_click(self, event):
        well = self._get_well_at(event.x, event.y)
        if well:
            self.selected_wells.add(well)
            self._highlight_well(well)

    def _on_mouse_down(self, event):
        self.drag_start = (event.x, event.y)
        self.dragging = True
        if not self.ctrl_held:
            self.selected_wells.clear()
            self._reset_highlights()

    def _on_mouse_drag(self, event):
        if not self.dragging:
            return
        x0, y0 = self.drag_start
        x1, y1 = event.x, event.y
        bbox = (min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1))
        for well_id, rect in self.well_rects.items():
            coords = self.plate_canvas.coords(rect)
            if self._rect_overlap(coords, bbox):
                self.selected_wells.add(well_id)
                self._highlight_well(well_id)

    def _on_mouse_up(self, event):
        self.dragging = False

    def _rect_overlap(self, coords, bbox):
        x1, y1, x2, y2 = coords
        bx1, by1, bx2, by2 = bbox
        return not (x2 < bx1 or x1 > bx2 or y2 < by1 or y1 > by2)

    def _get_well_at(self, x, y):
        for well_id, rect in self.well_rects.items():
            coords = self.plate_canvas.coords(rect)
            if coords[0] <= x <= coords[2] and coords[1] <= y <= coords[3]:
                return well_id
        return None

    def _highlight_well(self, well_id, color="#ADD8E6"):
        self.plate_canvas.itemconfig(self.well_rects[well_id], fill=color)

    def _reset_highlights(self):
        for rect in self.well_rects.values():
            self.plate_canvas.itemconfig(rect, fill="white")

    def _apply_condition(self):
        if not self.selected_wells:
            ttk.messagebox.showwarning("No wells selected", "Please select one or more wells.")
            return

        # Create a pop-up window
        popup = tk.Toplevel(self.root)
        popup.title("Assign Condition")

        tk.Label(popup, text="Select Condition Type:").grid(row=0, column=0, padx=10, pady=10, sticky='w')

        # Dropdown menu for condition type
        condition_var = tk.StringVar()
        condition_options = ["Time", "Cytokine Concentration", "Stain"]
        condition_dropdown = ttk.Combobox(popup, textvariable=condition_var, values=condition_options, state='readonly')
        condition_dropdown.grid(row=0, column=1, padx=10, pady=10)

        tk.Label(popup, text="Enter Condition Value:").grid(row=1, column=0, padx=10, pady=10, sticky='w')
        value_entry = tk.Entry(popup)
        value_entry.grid(row=1, column=1, padx=10, pady=10)

        def on_apply():
            condition = condition_var.get()
            value = value_entry.get()

            if not condition or not value:
                ttk.messagebox.showwarning("Incomplete Input", "Please select a condition and enter a value.")
                return
            
            color = self.color_map.get(condition, "black")

            for well in self.selected_wells:
                #row, col = well.split("_")
                if well not in self.condition_data.keys():
                    self.condition_data[well] = {}
                self.condition_data[well][condition] = value

                well_id = self.well_texts[well]
                well_text = self.plate_canvas.itemcget(well_id, "text")
                print(f"WELL TEXT: {well_text}")
                self.plate_canvas.itemconfig(self.well_texts[well], text=value, fill=color)

                print(f"WELL TEXT: {well_text}")

            self.selected_wells.clear()
            #for btn in self.well_buttons.values():
            #    btn.config(relief=tk.RAISED, bg='SystemButtonFace')

            popup.destroy()

        apply_button = tk.Button(popup, text="Apply", command=on_apply)
        apply_button.grid(row=2, column=0, columnspan=2, pady=15)

if __name__ == "__main__":
    root = tk.Tk()
    app = WellPlateApp(root)
    root.mainloop()
