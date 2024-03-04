import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse
import tkinter as tk
from tkinter import ttk, scrolledtext
from ttkthemes import ThemedTk
import threading
from PIL import Image, ImageTk
import webbrowser, os
combined_results = ""
result_text = None
def on_close_button_click():
    global logo_image
    root.destroy()
    logo_image = None
def on_keep_on_top_toggle():
    root.attributes('-topmost', keep_on_top_checkbox_var.get())
def on_lock_window_toggle():
    if lock_window_checkbox_var.get():
        root.unbind('<B1-Motion>', on_drag_start)
    else:
        root.bind('<B1-Motion>', on_drag_motion)
def get_emails_from_page(url):
    try:
        response = requests.get(url, timeout=210)
        soup = BeautifulSoup(response.text, 'html.parser')
        emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', soup.get_text())
        filtered_emails = [email for email in emails if not any(domain in email for domain in ['.gov', '.edu'])]
        return filtered_emails
    except Exception as e:
        print(f"Error getting emails from {url}: {e}")
        return []
def scrape_veterinary_emails(business_type, location, max_results=30, progress_var=None, loading_label=None, event=None):
    global combined_results
    global result_text
    try:
        all_emails = set()
        for page_num in range(0, max_results, 10):
            search_query = f"{business_type} {location}"
            google_search_url = f'https://www.google.com/search?q={search_query}&start={page_num}'
            response = requests.get(google_search_url)
            soup = BeautifulSoup(response.text, 'html.parser')
            links = [a['href'] for a in soup.find_all('a', href=True) if 'url?q=' in a['href']]
            links = links[:max_results]
            for idx, link in enumerate(links):
                clean_link = requests.utils.unquote(link.split('url?q=')[1].split('&sa=U&')[0])
                emails = get_emails_from_page(clean_link)
                domain = urlparse(clean_link).netloc
                for email in emails:
                    email = re.sub(r'\.com.*', '.com', email)
                    formatted_result = f"{domain} - {email}"
                    all_emails.add(formatted_result)
                if len(all_emails) >= max_results:
                    break
            progress_var.set((page_num + 10) * 100 / max_results)
        new_results = "\n".join(list(all_emails))
        combined_results += "\n" + new_results
        if result_text:
            result_text.insert(tk.END, new_results)
    except Exception as e:
        print(f"Error during scraping: {e}")
    finally:
        if event:
            event.set()
def on_logo_click():
    webbrowser.open_new("https://schultztechnology.com")
def on_drag_start(event):
    root.start_x = event.x
    root.start_y = event.y
def on_drag_motion(event):
    delta_x = event.x - root.start_x
    delta_y = event.y - root.start_y
    new_x = root.winfo_x() + delta_x
    new_y = root.winfo_y() + delta_y
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    if 0 <= new_x <= screen_width - root.winfo_width() and 0 <= new_y <= screen_height - root.winfo_height():
        root.geometry(f"+{new_x}+{new_y}")
def on_submit():
    global result_text
    business_type = business_type_entry.get()
    location = location_entry.get()
    max_results = int(max_results_slider.get())
    loading_label = tk.Label(root, text="Loading...")
    loading_label.pack()
    loading_bar_var = tk.DoubleVar()
    loading_bar = ttk.Progressbar(root, mode='determinate', length=200, variable=loading_bar_var)
    loading_bar.pack()
    event = threading.Event()
    threading.Thread(target=scrape_veterinary_emails, args=(business_type, location, max_results, loading_bar_var, loading_label, event)).start()
    threading.Thread(target=check_completion, args=(event, loading_bar, loading_label)).start()
def view_results():
    global result_text
    new_window = tk.Toplevel(root)
    new_window.title("Combined Results")
    result_text = scrolledtext.ScrolledText(new_window, width=80, height=20)
    result_text.pack()
    result_text.insert(tk.END, combined_results)
def check_completion(event, loading_bar, loading_label):
    event.wait()
    root.after(100, lambda: loading_bar.pack_forget())
    root.after(100, lambda: loading_label.pack_forget())
root = ThemedTk(theme="arc")
root.overrideredirect(True)
root.geometry("420x400")
top_frame = tk.Frame(root, bg="#F0F0F0")
top_frame.place(relx=0, rely=0, anchor=tk.NW, relwidth=1.0)
close_button = tk.Button(top_frame, text="Close", command=on_close_button_click, bg="#FFF5F5")
close_button.pack(side=tk.RIGHT, padx=10, pady=10)
keep_on_top_checkbox_var = tk.BooleanVar(value=True)
script_dir = os.path.dirname(os.path.realpath(__file__))
logo_image_path = os.path.join(script_dir, "logo.png")
logo_image = Image.open(logo_image_path)
logo_image = ImageTk.PhotoImage(logo_image)
keep_on_top_checkbox_var = tk.BooleanVar(value=True)
keep_on_top_checkbox = tk.Checkbutton(top_frame, text="Keep on Top", variable=keep_on_top_checkbox_var, command=on_keep_on_top_toggle, bd=0, activebackground="#F0F0F0", bg="#F0F0F0")
keep_on_top_checkbox.place(x=256, y=10)
lock_window_checkbox_var = tk.BooleanVar(value=False)
lock_window_checkbox = tk.Checkbutton(top_frame, text="Lock Window", variable=lock_window_checkbox_var, command=on_lock_window_toggle, bd=0, activebackground="#F0F0F0", bg="#F0F0F0")
lock_window_checkbox.place(x=255, y=35)
on_keep_on_top_toggle()
on_lock_window_toggle()
logo_label = tk.Label(top_frame, image=logo_image, cursor="hand2", bg="#F0F0F0")  
logo_label.pack(side=tk.LEFT, padx=10, pady=10)
logo_label.bind("<Button-1>", lambda e: on_logo_click())
title_label = tk.Label(top_frame, text="Lead Generator", font=("Arial", 12, "bold"), anchor=tk.W, padx=10, cursor="hand2",bg="#F0F0F0")
title_label.pack(side=tk.LEFT,padx=0,pady=0,)
title_label.bind("<Button-1>", lambda e: webbrowser.open_new("https://schultztechnology.com"))
title_label.place(x=47, y=14) 
title_label2 = tk.Label(top_frame, text="by Schultz Technology", font=("Arial", 8, "bold"), anchor=tk.W, padx=10, cursor="hand2",bg="#F0F0F0")
title_label2.pack(side=tk.LEFT,padx=0,pady=0)
title_label2.bind("<Button-1>", lambda e: webbrowser.open_new("https://schultztechnology.com"))
title_label2.place(x=65, y=35)
tk.Label(root, text="Business Type:").pack(pady=(76,8))
business_type_entry = tk.Entry(root, width=48)
business_type_entry.insert(0, "Veterinary Nonprofit")
business_type_entry.pack()
tk.Label(root, text="Enter Location:").pack(pady=(12,0))
location_entry = tk.Entry(root, width=48)
location_entry.insert(0, "New York, NY")
location_entry.pack(pady=8)
tk.Label(root, text="Page Results 10-100").pack(pady=(10,0))
max_results_slider = ttk.Scale(root, from_=10, to=100, orient="horizontal", length=300, value=23)
max_results_slider.pack(pady=8)
search_button = tk.Button(root, text="Search Emails", command=on_submit, width=20)
search_button.pack(pady=(25,8))
view_results_button = tk.Button(root, text="View Results", command=view_results, width=16)
view_results_button.pack(pady=8)
root.bind("<Button-1>", on_drag_start)
root.bind("<B1-Motion>", on_drag_motion)
root.mainloop()