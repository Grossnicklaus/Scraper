import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse
import tkinter as tk
from tkinter import ttk, scrolledtext
import threading

def get_emails_from_page(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', soup.get_text())
        return emails
    except Exception as e:
        print(f"Error getting emails from {url}: {e}")
        return []

def scrape_veterinary_emails(business_type, location, max_results=30, result_text=None, progress_var=None, loading_label=None, event=None):
    try:
        all_emails = set()  # Use a set to automatically remove duplicates

        for page_num in range(0, max_results, 10):  # Adjust the step size as needed
            search_query = f"{business_type} {location}"
            google_search_url = f'https://www.google.com/search?q={search_query}&start={page_num}'
            response = requests.get(google_search_url)
            soup = BeautifulSoup(response.text, 'html.parser')
            links = [a['href'] for a in soup.find_all('a', href=True) if 'url?q=' in a['href']]
            links = links[:max_results]

            for idx, link in enumerate(links):
                clean_link = requests.utils.unquote(link.split('url?q=')[1].split('&sa=U&')[0])
                emails = get_emails_from_page(clean_link)
                domain = urlparse(clean_link).netloc  # Extract the domain from the URL

                for email in emails:
                    # Remove anything after ".com" in the email address
                    email = re.sub(r'\.com.*', '.com', email)
                    formatted_result = f"{domain} - {email}"
                    all_emails.add(formatted_result)

                # Break the loop if the desired number of results is reached
                if len(all_emails) >= max_results:
                    break

            # Update the progress bar
            progress_var.set((page_num + 10) * 100 / max_results)
            result_text.update_idletasks()

        # Display the results in the text widget without "Search Results for "
        result_text.insert(tk.END, f"{location} ({business_type}):\n\n" + "\n".join(list(all_emails)) + "\n\n")

    except Exception as e:
        print(f"Error during scraping: {e}")

    finally:
        # Signal the main thread that scraping is complete
        if event:
            event.set()

def on_submit():
    business_type = business_type_entry.get()
    location = location_entry.get()
    max_results = int(max_results_slider.get())

    # Create a loading bar and label
    loading_label = tk.Label(root, text="Loading...")
    loading_label.pack()

    loading_bar_var = tk.DoubleVar()
    loading_bar = ttk.Progressbar(root, mode='determinate', length=200, variable=loading_bar_var)
    loading_bar.pack()

    # Create an event to signal when scraping is complete
    event = threading.Event()

    # Call the scraping function with the specified parameters
    threading.Thread(target=scrape_veterinary_emails, args=(business_type, location, max_results, result_text, loading_bar_var, loading_label, event)).start()

    # Check for scraping completion in a separate thread
    threading.Thread(target=check_completion, args=(event, loading_bar, loading_label)).start()

def check_completion(event, loading_bar, loading_label):
    # Wait for the event to be set, indicating scraping is complete
    event.wait()

    # Hide the progress bar and label when done loading
    root.after(100, lambda: loading_bar.pack_forget())
    root.after(100, lambda: loading_label.pack_forget())

# Create the main window
root = tk.Tk()
root.title("Email Scraper")

# Create and place widgets (labels, entry fields, and button)
tk.Label(root, text="Business Type:").pack()
business_type_entry = tk.Entry(root, width=30)
business_type_entry.insert(0, "Veterinary Hospital")
business_type_entry.pack()

tk.Label(root, text="Enter Location:").pack()
location_entry = tk.Entry(root, width=30)
location_entry.insert(0, "New York, NY")
location_entry.pack()

# Create a slider for max results
tk.Label(root, text="Max Results:").pack()
max_results_slider = tk.Scale(root, from_=10, to=100, orient="horizontal", length=300, tickinterval=45, resolution=1)
max_results_slider.set(30)  # Default value
max_results_slider.pack()

submit_button = tk.Button(root, text="Submit", command=on_submit)
submit_button.pack()

# Create a scrolled text widget for displaying results
result_text = scrolledtext.ScrolledText(root, width=80, height=20)
result_text.pack()

# Start the main event loop
root.mainloop()
