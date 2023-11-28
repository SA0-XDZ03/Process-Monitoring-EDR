import psutil
import tkinter as tk
from tkinter import ttk
import os
import pygraphviz as pgv
from PIL import Image, ImageTk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import pandas as pd

# Function to get process hierarchy
def get_process_hierarchy(process_name):
    process_tree = {}
    for proc in psutil.process_iter(['pid', 'name', 'ppid', 'username', 'cmdline', 'create_time', 'nice']):
        if proc.info['name'] == process_name:
            process_tree[proc.info['pid']] = []
            for child in psutil.Process(proc.info['pid']).children(recursive=True):
                process_tree[proc.info['pid']].append(child.pid)
    return process_tree

# Function to create a directory for the process and save process info & Graph image
def save_process_info(process_name, hierarchy):
    process_dir = f"./{process_name}_info"
    os.makedirs(process_dir, exist_ok=True)
    
    # Save process details
    with open(f"{process_dir}/{process_name}_details.txt", 'w') as file:
        for pid, children in hierarchy.items():
            proc = psutil.Process(pid)
            cmdline = ' '.join(proc.cmdline()) if proc.cmdline() else ""
            file.write(f"PID: {proc.pid}\n")
            file.write(f"Username: {proc.username()}\n")
            file.write(f"Command Line: {cmdline}\n")
            file.write(f"Elevation: {proc.create_time()}\n")
            file.write(f"PPID: {proc.ppid()}\n")
            file.write(f"Base Priority: {proc.nice()}\n\n")
    
    # Save Graph image
    dot = pgv.AGraph(strict=True, directed=True)
    for pid, children in hierarchy.items():
        proc = psutil.Process(pid)
        cmdline = ' '.join(proc.cmdline()) if proc.cmdline() else ""
        label = f"PID: {proc.pid}\nName: {proc.name()}\nUsername: {proc.username()}\nCommand Line: {cmdline}\nElevation: {proc.create_time()}\nPPID: {proc.ppid()}\nBase Priority: {proc.nice()}"
        dot.add_node(pid, label=label)
        for child in children:
            dot.add_node(child)
            dot.add_edge(pid, child)
    
    dot.layout(prog='dot')  # Use Graphviz layout engine
    dot.draw(f"{process_dir}/{process_name}_process_flow.png")  # Save the image as PNG

def update_process_info():
    all_processes = []
    for proc in psutil.process_iter(['pid', 'name', 'ppid', 'username', 'cmdline', 'create_time', 'nice']):
        process_info = {
            'PID': proc.info['pid'],
            'PPID': proc.info['ppid'],
            'Description': proc.info['name'],
            'Command Line': ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else '',
            'Elevation': proc.create_time(),
            'Base Priority': proc.info['nice'],
            'Username': proc.info['username']
        }
        all_processes.append(process_info)

    processes_df = pd.DataFrame(all_processes)

    return processes_df

def display_processes():
    processes_df = update_process_info()
    processes_tree['columns'] = list(processes_df.columns)
    processes_tree.heading('#0', text='Index')
    processes_tree.column('#0', width=50)
    for col in processes_df.columns:
        processes_tree.heading(col, text=col)
        processes_tree.column(col, width=120)

    for index, row in processes_df.iterrows():
        processes_tree.insert("", tk.END, text=index, values=list(row))

# Function to update the visualization based on selected process
def update_visualization():
    selected_process = process_combobox.get()
    if selected_process:
        hierarchy = get_process_hierarchy(selected_process)
        save_process_info(selected_process, hierarchy)
        
        img = Image.open(f"{selected_process}_info/{selected_process}_process_flow.png")
        img.thumbnail((6400, 6400))  # Resize the image - Image Too Small / Increase the Size of Output
        img_tk = ImageTk.PhotoImage(img)
        
        # Clear previous visualization
        for widget in canvas_frame.winfo_children():
            widget.destroy()
        
        # Display the new visualization with navigation toolbar
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.imshow(img)
        ax.axis('on')
        
        canvas = FigureCanvasTkAgg(fig, master=canvas_frame)
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.pack(fill=tk.BOTH, expand=True)
        
        # Add a navigation toolbar for zooming, panning, etc.
        toolbar = NavigationToolbar2Tk(canvas, canvas_frame)
        toolbar.update()
        canvas_widget.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        canvas.draw()

# Retrieve running processes
running_processes = [proc.name() for proc in psutil.process_iter()]

# GUI setup
root = tk.Tk()
root.title('Process Hierarchy Visualizer')

# Left side: Table for displaying process information
processes_tree = ttk.Treeview(root)
processes_tree.grid(row=0, column=0, rowspan=3, padx=10, pady=10, sticky="nsew")
processes_tree['show'] = 'headings'

# Right side: Visualization
process_label = ttk.Label(root, text='Select a running process:')
process_label.grid(row=0, column=1, padx=10, pady=10)

process_combobox = ttk.Combobox(root, values=running_processes)
process_combobox.grid(row=0, column=2, padx=10, pady=10)

visualize_button = ttk.Button(root, text='Visualize', command=update_visualization)
visualize_button.grid(row=0, column=3, padx=10, pady=10)

# Create a frame for Matplotlib canvas
canvas_frame = tk.Frame(root)
canvas_frame.grid(row=1, column=1, columnspan=3, padx=10, pady=10, sticky="nsew")

# Create a figure and canvas for matplotlib
fig, ax = plt.subplots(figsize=(6, 4))
canvas = FigureCanvasTkAgg(fig, master=canvas_frame)
canvas_widget = canvas.get_tk_widget()
canvas_widget.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

# Add a navigation toolbar for zooming, panning, etc.
toolbar = NavigationToolbar2Tk(canvas, canvas_frame)
toolbar.update()
toolbar.pack(side=tk.BOTTOM, fill=tk.X)

# Display processes information
display_processes()

root.mainloop()