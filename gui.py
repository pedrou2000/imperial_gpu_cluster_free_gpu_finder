import tkinter as tk
from tkinter import ttk
import threading
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
from main import get_gpu_usage  # Ensure this imports correctly
import config  # Ensure config module is correctly set up

def fetch_and_display_data():
    # Hide the refresh button and show the fetching label
    refresh_button.pack_forget()
    fetching_label['text'] = "Fetching data..."
    fetching_label.pack(side=tk.BOTTOM, fill=tk.X, pady=10)
    
    usage_data = []
    with ThreadPoolExecutor(max_workers=len(config.TARGETS)) as executor:
        future_to_machine = {
            executor.submit(
                get_gpu_usage,
                machine,
                config.SSH_JUMP_HOSTS,
                config.SSH_USERNAME,
                config.SSH_KEY_FILEPATH
            ): machine for machine in config.TARGETS
        }
        for future in concurrent.futures.as_completed(future_to_machine):
            try:
                data = future.result()
                usage_data.append(data)
            except Exception as exc:
                print(f'{future_to_machine[future]} generated an exception: {exc}')
    
    # Sort the data based on the numeric value of memory left (5th element in the tuple before formatting)
    usage_data.sort(key=lambda x: x[4], reverse=True)  # Ensure this is correct based on the data structure
    
    # Format the data for display after sorting
    formatted_data = [(data[0],) + tuple(f"{n:.2f}" for n in data[1:]) for data in usage_data]
    
    tree.after(0, lambda: update_treeview(formatted_data))

def update_treeview(formatted_data):
    for row in tree.get_children():
        tree.delete(row)
    for row in formatted_data:
        tree.insert('', tk.END, values=row)
    fetching_label.pack_forget()  # Hide fetching label after updating
    refresh_button.pack(side=tk.BOTTOM, fill=tk.X, pady=10)  # Show refresh button again
    root.update_idletasks()





def start_fetch_and_display():
    threading.Thread(target=fetch_and_display_data, daemon=True).start()

root = tk.Tk()
root.title("GPU Usage Viewer")
root.geometry("1000x400")  # Example: Set initial size to 800x600 pixels

frame = ttk.Frame(root)
frame.pack(fill=tk.BOTH, expand=True)

# Temporary label for displaying fetching status
fetching_label = ttk.Label(frame, text="")
fetching_label.pack(side=tk.TOP, pady=10)

tree = ttk.Treeview(frame, columns=('Machine', 'GPU Utilization (%)', 'Memory Used (MiB)', 'Total Memory (MiB)', 'Memory Left (MiB)', 'Memory Used (%)'), show='headings')
for col in tree['columns']:
    tree.heading(col, text=col, anchor=tk.CENTER)  # Center column headings
    tree.column(col, anchor='center')  # Center column contents
tree.pack(fill=tk.BOTH, expand=True)


# Adjust column widths
tree.column('Machine', width=100, anchor='center')
tree.column('GPU Utilization (%)', width=150, anchor='center')
tree.column('Memory Used (MiB)', width=150, anchor='center')
tree.column('Total Memory (MiB)', width=150, anchor='center')
tree.column('Memory Left (MiB)', width=150, anchor='center')
tree.column('Memory Used (%)', width=150, anchor='center')

refresh_button = ttk.Button(frame, text="Refresh", command=start_fetch_and_display)
refresh_button.pack(side=tk.BOTTOM, fill=tk.X)

start_fetch_and_display()

root.mainloop()
