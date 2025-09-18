import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser
import cv2
from PIL import Image, ImageTk
import pandas as pd
import threading
import time
import os


class VideoAnnotationTool:
    def __init__(self, root):
        self.root = root
        self.root.title("Video Annotation Tool")
        self.root.geometry("1400x900")

        # Video variables
        self.video_path = None
        self.cap = None
        self.total_frames = 0
        self.fps = 30
        self.current_frame = 0
        self.current_time = 0.0
        self.is_playing = False
        self.frame_duration = 1000 // 30  # milliseconds

        # Annotation variables
        self.annotations = []
        self.annotation_categories = {
            "Event": "#FF6B6B",
            "Action": "#4ECDC4",
            "Object": "#45B7D1",
            "Scene": "#96CEB4",
            "Person": "#FFEAA7",
            "Other": "#DDA0DD"
        }

        self.setup_ui()

    def setup_ui(self):
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Top frame for file operations
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(top_frame, text="Open Video", command=self.open_video).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(top_frame, text="Load Annotations", command=self.load_annotations).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(top_frame, text="Export CSV", command=self.export_csv).pack(side=tk.LEFT)

        # Main content frame
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)

        # Left side - Video player and controls
        left_frame = ttk.Frame(content_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        # Video display with fixed size
        video_frame = ttk.Frame(left_frame)
        video_frame.pack(pady=(0, 10), fill=tk.X)

        self.video_label = tk.Label(video_frame, bg="black", text="No Video Loaded",
                                    fg="white", font=("Arial", 16), width=80, height=30)
        self.video_label.pack(anchor=tk.CENTER)

        # Video controls frame
        controls_frame = ttk.Frame(left_frame)
        controls_frame.pack(fill=tk.X, pady=(0, 10))

        # Playback buttons
        button_frame = ttk.Frame(controls_frame)
        button_frame.pack(pady=(0, 10))

        ttk.Button(button_frame, text="<<", command=self.prev_frame).pack(side=tk.LEFT, padx=2)
        self.play_button = ttk.Button(button_frame, text="Play", command=self.toggle_playback)
        self.play_button.pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text=">>", command=self.next_frame).pack(side=tk.LEFT, padx=2)

        # Timeline
        timeline_frame = ttk.Frame(controls_frame)
        timeline_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(timeline_frame, text="Timeline:").pack(anchor=tk.W)
        self.timeline_var = tk.DoubleVar()
        self.timeline_scale = ttk.Scale(timeline_frame, from_=0, to=100,
                                        variable=self.timeline_var,
                                        command=self.on_timeline_change)
        self.timeline_scale.pack(fill=tk.X, pady=(5, 0))

        # Frame info
        info_frame = ttk.Frame(controls_frame)
        info_frame.pack(fill=tk.X)

        self.frame_label = ttk.Label(info_frame, text="Frame: 0 / 0")
        self.frame_label.pack(side=tk.LEFT)

        self.time_label = ttk.Label(info_frame, text="Time: 00:00.000")
        self.time_label.pack(side=tk.RIGHT)

        # FPS control
        fps_frame = ttk.Frame(controls_frame)
        fps_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Label(fps_frame, text="FPS:").pack(side=tk.LEFT)
        self.fps_var = tk.StringVar(value="30")
        fps_entry = ttk.Entry(fps_frame, textvariable=self.fps_var, width=5)
        fps_entry.pack(side=tk.LEFT, padx=(5, 0))
        fps_entry.bind('<Return>', self.update_fps)

        # Timeline visualization
        timeline_viz_frame = ttk.LabelFrame(left_frame, text="Annotation Timeline")
        timeline_viz_frame.pack(fill=tk.X, pady=(0, 10))

        self.timeline_canvas = tk.Canvas(timeline_viz_frame, height=60, bg='white')
        self.timeline_canvas.pack(fill=tk.X, padx=5, pady=5)
        self.timeline_canvas.bind('<Button-1>', self.on_timeline_click)

        # Right side - Annotation panel
        right_frame = ttk.Frame(content_frame, width=400)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(10, 0))
        right_frame.pack_propagate(False)

        # Add annotation section
        add_frame = ttk.LabelFrame(right_frame, text="Add Annotation")
        add_frame.pack(fill=tk.X, pady=(0, 10))

        # Category selection
        ttk.Label(add_frame, text="Category:").pack(anchor=tk.W, padx=5, pady=(5, 0))
        self.category_var = tk.StringVar(value="Event")
        category_combo = ttk.Combobox(add_frame, textvariable=self.category_var,
                                      values=list(self.annotation_categories.keys()),
                                      state="readonly")
        category_combo.pack(fill=tk.X, padx=5, pady=(0, 5))

        # Annotation text
        ttk.Label(add_frame, text="Annotation:").pack(anchor=tk.W, padx=5)
        self.annotation_var = tk.StringVar()
        annotation_entry = ttk.Entry(add_frame, textvariable=self.annotation_var)
        annotation_entry.pack(fill=tk.X, padx=5, pady=(0, 5))
        annotation_entry.bind('<Return>', lambda e: self.add_annotation())

        # Comment text
        ttk.Label(add_frame, text="Comment:").pack(anchor=tk.W, padx=5)
        self.comment_text = tk.Text(add_frame, height=3, width=40)
        self.comment_text.pack(fill=tk.X, padx=5, pady=(0, 5))

        ttk.Button(add_frame, text="Add Annotation", command=self.add_annotation).pack(pady=5)

        # Annotations list (FIXED: table and buttons in separate frames so buttons are visible)
        list_frame = ttk.LabelFrame(right_frame, text="Annotations")
        list_frame.pack(fill=tk.BOTH, expand=True)

        # TOP: table (tree + scrollbar) wrapped in its own frame
        table_frame = ttk.Frame(list_frame)
        table_frame.pack(fill=tk.BOTH, expand=True)

        # Treeview for annotations
        columns = ("Frame", "Time", "Category", "Annotation")
        self.annotations_tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=15)

        for col in columns:
            self.annotations_tree.heading(col, text=col)
            self.annotations_tree.column(col, width=80)

        self.annotations_tree.column("Annotation", width=150)

        # Scrollbar for treeview
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.annotations_tree.yview)
        self.annotations_tree.configure(yscrollcommand=scrollbar.set)

        self.annotations_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0), pady=5)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=5)

        # BOTTOM: Annotation operations (now visible under the table)
        ops_frame = ttk.Frame(list_frame)
        ops_frame.pack(fill=tk.X, padx=5, pady=(0, 5))

        ttk.Button(ops_frame, text="Jump to", command=self.jump_to_annotation).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(ops_frame, text="Edit", command=self.edit_annotation).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(ops_frame, text="Delete", command=self.delete_annotation).pack(side=tk.LEFT)

        self.annotations_tree.bind("<Double-1>", lambda e: self.jump_to_annotation())

    def edit_annotation(self):
        """Edit the selected annotation"""
        selection = self.annotations_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select an annotation to edit!")
            return

        item = selection[0]
        frame_number = int(self.annotations_tree.item(item, "values")[0])

        # Find the annotation
        annotation = None
        for ann in self.annotations:
            if ann["frame_number"] == frame_number:
                annotation = ann
                break

        if not annotation:
            messagebox.showerror("Error", "Could not find annotation to edit!")
            return

        # Create edit dialog
        self.create_edit_dialog(annotation)

    def create_edit_dialog(self, annotation):
        """Create dialog for editing annotation"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Edit Annotation")
        dialog.geometry("400x300")
        dialog.transient(self.root)
        dialog.grab_set()

        # Center dialog on parent
        dialog.geometry("+%d+%d" % (self.root.winfo_rootx() + 50, self.root.winfo_rooty() + 50))

        # Frame info
        info_frame = ttk.Frame(dialog)
        info_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(info_frame, text=f"Frame: {annotation['frame_number']}").pack(anchor=tk.W)
        ttk.Label(info_frame, text=f"Time: {annotation['time_instant']:.3f}s").pack(anchor=tk.W)

        # Category
        ttk.Label(dialog, text="Category:").pack(anchor=tk.W, padx=10)
        category_var = tk.StringVar(value=annotation["category"])
        category_combo = ttk.Combobox(dialog, textvariable=category_var,
                                      values=list(self.annotation_categories.keys()),
                                      state="readonly")
        category_combo.pack(fill=tk.X, padx=10, pady=(0, 10))

        # Annotation text
        ttk.Label(dialog, text="Annotation:").pack(anchor=tk.W, padx=10)
        annotation_var = tk.StringVar(value=annotation["annotation"])
        annotation_entry = ttk.Entry(dialog, textvariable=annotation_var)
        annotation_entry.pack(fill=tk.X, padx=10, pady=(0, 10))

        # Comment text
        ttk.Label(dialog, text="Comment:").pack(anchor=tk.W, padx=10)
        comment_text = tk.Text(dialog, height=5, width=40)
        comment_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        comment_text.insert("1.0", annotation["comment"])

        # Buttons
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        def save_changes():
            # Update annotation
            annotation["category"] = category_var.get()
            annotation["annotation"] = annotation_var.get()
            annotation["comment"] = comment_text.get("1.0", tk.END).strip()
            annotation["color"] = self.annotation_categories[annotation["category"]]

            # Update UI
            self.update_annotations_list()
            self.draw_timeline()

            dialog.destroy()
            messagebox.showinfo("Success", "Annotation updated successfully!")

        def cancel_edit():
            dialog.destroy()

        ttk.Button(button_frame, text="Save", command=save_changes).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="Cancel", command=cancel_edit).pack(side=tk.RIGHT)

    def open_video(self):
        file_path = filedialog.askopenfilename(
            title="Select Video File",
            filetypes=[("Video files", "*.mp4 *.avi *.mov *.mkv *.wmv *.flv"),
                       ("All files", "*.*")]
        )

        if file_path:
            self.load_video(file_path)

    def load_video(self, video_path):
        try:
            self.video_path = video_path
            if self.cap:
                self.cap.release()

            self.cap = cv2.VideoCapture(video_path)

            # Get video properties
            self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
            self.fps = int(self.cap.get(cv2.CAP_PROP_FPS)) or 30
            self.fps_var.set(str(self.fps))
            self.frame_duration = 1000 // self.fps

            # Reset video state
            self.current_frame = 0
            self.current_time = 0.0
            self.is_playing = False
            self.play_button.config(text="Play")

            # Update timeline
            self.timeline_scale.config(to=self.total_frames - 1)
            self.timeline_var.set(0)

            # Clear annotations
            self.annotations = []
            self.update_annotations_list()

            # Load first frame
            self.show_frame()
            self.update_info()
            self.draw_timeline()

            messagebox.showinfo("Success", f"Video loaded successfully!\nFrames: {self.total_frames}\nFPS: {self.fps}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load video: {str(e)}")

    def show_frame(self):
        if self.cap and self.cap.isOpened():
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.current_frame)
            ret, frame = self.cap.read()

            if ret:
                # Convert BGR to RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                # Fixed resize dimensions
                display_width = 640
                display_height = 480

                h, w = frame_rgb.shape[:2]
                aspect_ratio = w / h

                # Calculate new dimensions maintaining aspect ratio
                if display_width / display_height > aspect_ratio:
                    new_height = display_height
                    new_width = int(new_height * aspect_ratio)
                else:
                    new_width = display_width
                    new_height = int(new_width / aspect_ratio)

                frame_resized = cv2.resize(frame_rgb, (new_width, new_height))

                # Convert to PIL Image and then to PhotoImage
                image = Image.fromarray(frame_resized)
                photo = ImageTk.PhotoImage(image)

                self.video_label.config(image=photo, text="", width=new_width, height=new_height)
                self.video_label.image = photo

    def toggle_playback(self):
        if not self.cap:
            return

        self.is_playing = not self.is_playing

        if self.is_playing:
            self.play_button.config(text="Pause")
            self.play_video()
        else:
            self.play_button.config(text="Play")

    def play_video(self):
        if self.is_playing and self.current_frame < self.total_frames - 1:
            self.next_frame()
            self.root.after(self.frame_duration, self.play_video)
        else:
            self.is_playing = False
            self.play_button.config(text="Play")

    def next_frame(self):
        if self.cap and self.current_frame < self.total_frames - 1:
            self.current_frame += 1
            self.update_frame_display()

    def prev_frame(self):
        if self.cap and self.current_frame > 0:
            # Stop playback when manually navigating
            self.is_playing = False
            self.play_button.config(text="Play")

            self.current_frame -= 1
            self.update_frame_display()

    def update_frame_display(self):
        """Update frame display and all related UI elements"""
        self.current_time = self.current_frame / self.fps
        self.timeline_var.set(self.current_frame)
        self.show_frame()
        self.update_info()
        self.draw_timeline()

    def on_timeline_change(self, value):
        if self.cap:
            # Stop playback when manually changing timeline
            self.is_playing = False
            self.play_button.config(text="Play")

            self.current_frame = int(float(value))
            self.update_frame_display()

    def update_fps(self, event=None):
        try:
            new_fps = int(self.fps_var.get())
            if new_fps > 0:
                self.fps = new_fps
                self.frame_duration = 1000 // self.fps
                self.current_time = self.current_frame / self.fps
                self.update_info()
        except ValueError:
            self.fps_var.set(str(self.fps))

    def update_info(self):
        self.frame_label.config(text=f"Frame: {self.current_frame} / {self.total_frames}")

        minutes = int(self.current_time // 60)
        seconds = int(self.current_time % 60)
        milliseconds = int((self.current_time % 1) * 1000)
        self.time_label.config(text=f"Time: {minutes:02d}:{seconds:02d}.{milliseconds:03d}")

    def add_annotation(self):
        if not self.cap:
            messagebox.showwarning("Warning", "Please load a video first!")
            return

        annotation_text = self.annotation_var.get().strip()
        if not annotation_text:
            messagebox.showwarning("Warning", "Please enter an annotation!")
            return

        comment_text = self.comment_text.get("1.0", tk.END).strip()
        category = self.category_var.get()

        annotation = {
            'id': len(self.annotations),
            'frame_number': self.current_frame,
            'time_instant': self.current_time,
            'annotation': annotation_text,
            'comment': comment_text,
            'category': category,
            'color': self.annotation_categories[category]
        }

        self.annotations.append(annotation)
        self.update_annotations_list()
        self.draw_timeline()

        # Clear input fields
        self.annotation_var.set("")
        self.comment_text.delete("1.0", tk.END)

        messagebox.showinfo("Success", "Annotation added successfully!")

    def update_annotations_list(self):
        # Clear existing items
        for item in self.annotations_tree.get_children():
            self.annotations_tree.delete(item)

        # Add annotations
        for ann in sorted(self.annotations, key=lambda x: x['frame_number']):
            minutes = int(ann['time_instant'] // 60)
            seconds = int(ann['time_instant'] % 60)
            milliseconds = int((ann['time_instant'] % 1) * 1000)
            time_str = f"{minutes:02d}:{seconds:02d}.{milliseconds:03d}"

            item = self.annotations_tree.insert("", "end", values=(
                ann['frame_number'],
                time_str,
                ann['category'],
                ann['annotation'][:30] + ("..." if len(ann['annotation']) > 30 else "")
            ))

            # Color code the item
            self.annotations_tree.set(item, 'Category', ann['category'])

    def jump_to_annotation(self):
        selection = self.annotations_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select an annotation!")
            return

        # Stop playback when jumping to annotation
        self.is_playing = False
        self.play_button.config(text="Play")

        item = selection[0]
        frame_number = int(self.annotations_tree.item(item, "values")[0])

        self.current_frame = frame_number
        self.update_frame_display()

    def delete_annotation(self):
        selection = self.annotations_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select an annotation to delete!")
            return

        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this annotation?"):
            item = selection[0]
            frame_number = int(self.annotations_tree.item(item, 'values')[0])

            # Find and remove annotation
            self.annotations = [ann for ann in self.annotations if ann['frame_number'] != frame_number]

            self.update_annotations_list()
            self.draw_timeline()

    def draw_timeline(self):
        if not self.cap:
            return

        self.timeline_canvas.delete("all")
        canvas_width = self.timeline_canvas.winfo_width()
        canvas_height = self.timeline_canvas.winfo_height()

        if canvas_width <= 1:
            return

        # Draw timeline background
        self.timeline_canvas.create_rectangle(0, 0, canvas_width, canvas_height,
                                              fill="lightgray", outline="")

        # Draw annotations
        for ann in self.annotations:
            x = (ann['frame_number'] / self.total_frames) * canvas_width
            self.timeline_canvas.create_rectangle(x - 2, 10, x + 2, canvas_height - 10,
                                                  fill=ann['color'], outline="black")

        # Draw current position
        current_x = (self.current_frame / self.total_frames) * canvas_width
        self.timeline_canvas.create_line(current_x, 0, current_x, canvas_height,
                                         fill="red", width=3)

    def on_timeline_click(self, event):
        if not self.cap:
            return

        # Stop playback when clicking timeline
        self.is_playing = False
        self.play_button.config(text="Play")

        canvas_width = self.timeline_canvas.winfo_width()
        click_ratio = event.x / canvas_width
        target_frame = int(click_ratio * self.total_frames)
        target_frame = max(0, min(target_frame, self.total_frames - 1))

        self.current_frame = target_frame
        self.update_frame_display()

    def export_csv(self):
        if not self.annotations:
            messagebox.showwarning("Warning", "No annotations to export!")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Save Annotations"
        )

        if file_path:
            try:
                df_data = []
                for ann in sorted(self.annotations, key=lambda x: x['frame_number']):
                    df_data.append({
                        'Frame Number': ann['frame_number'],
                        'Time Instant (s)': round(ann['time_instant'], 3),
                        'Annotation': ann['annotation'],
                        'Comment': ann['comment'],
                        'Category': ann['category']
                    })

                df = pd.DataFrame(df_data)
                df.to_csv(file_path, index=False)
                messagebox.showinfo("Success", f"Annotations exported to {file_path}")

            except Exception as e:
                messagebox.showerror("Error", f"Failed to export CSV: {str(e)}")

    def load_annotations(self):
        """Load annotations from a CSV file"""
        if not self.cap:
            messagebox.showwarning("Warning", "Please load a video first!")
            return

        file_path = filedialog.askopenfilename(
            title="Load Annotations",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )

        if file_path:
            try:
                df = pd.read_csv(file_path)

                # Validate CSV structure
                required_columns = ["Frame Number", "Time Instant (s)", "Annotation", "Comment", "Category"]
                missing_columns = [col for col in df.columns if col not in required_columns]

                if missing_columns:
                    messagebox.showerror("Error", f"CSV file is missing required columns: {', '.join(missing_columns)}")
                    return

                # Clear existing annotations
                if self.annotations:
                    if not messagebox.askyesno("Confirm", "This will replace existing annotations. Continue?"):
                        return

                self.annotations = []

                # Load annotations from CSV
                loaded_count = 0
                skipped_count = 0

                for index, row in df.iterrows():
                    try:
                        frame_number = int(row["Frame Number"])
                        time_instant = float(row["Time Instant (s)"])
                        annotation_text = str(row["Annotation"]) if pd.notna(row["Annotation"]) else ""
                        comment_text = str(row["Comment"]) if pd.notna(row["Comment"]) else ""
                        category = str(row["Category"]) if pd.notna(row["Category"]) else "Other"

                        # Validate frame number is within video range
                        if frame_number < 0 or frame_number >= self.total_frames:
                            skipped_count += 1
                            continue

                        # Ensure category exists, default to "Other" if not
                        if category not in self.annotation_categories:
                            category = "Other"

                        annotation = {
                            "id": len(self.annotations),
                            "frame_number": frame_number,
                            "time_instant": time_instant,
                            "annotation": annotation_text,
                            "comment": comment_text,
                            "category": category,
                            "color": self.annotation_categories[category]
                        }

                        self.annotations.append(annotation)
                        loaded_count += 1

                    except (ValueError, KeyError) as e:
                        skipped_count += 1
                        continue

                # Update UI
                self.update_annotations_list()
                self.draw_timeline()

                # Show summary
                message = f"Successfully loaded {loaded_count} annotations."
                if skipped_count > 0:
                    message += f"\nSkipped {skipped_count} invalid entries."

                messagebox.showinfo("Load Complete", message)

            except Exception as e:
                messagebox.showerror("Error", f"Failed to load annotations: {str(e)}")

    def validate_annotation_file(self, file_path):
        """Validate that the CSV file has the correct structure"""
        try:
            df = pd.read_csv(file_path, nrows=1)  # Read only first row for validation
            required_columns = ["Frame Number", "Time Instant (s)", "Annotation", "Comment", "Category"]
            return all(col in df.columns for col in required_columns)
        except Exception:
            return False


def main():
    root = tk.Tk()
    app = VideoAnnotationTool(root)

    # Bind canvas resize event
    def on_canvas_resize(event):
        app.draw_timeline()

    app.timeline_canvas.bind('<Configure>', on_canvas_resize)

    root.mainloop()


if __name__ == "__main__":
    main()
