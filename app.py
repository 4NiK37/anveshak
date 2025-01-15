from flask import Flask, render_template, request
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import threading
import socket

app = Flask(__name__)

# To store crawled links
crawled_links = set()
lock = threading.Lock()

def crawl(url, depth):
    if depth < 0:
        return
    try:
        response = requests.get(url)
        if response.status_code == 200:
            with lock:
                crawled_links.add(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            for link in soup.find_all('a', href=True):
                full_url = urljoin(url, link['href'])
                if full_url not in crawled_links:
                    crawl(full_url, depth - 1)
    except requests.RequestException:
        pass

def check_open_ports(host, ports):
    open_ports = []
    for port in ports:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(1)  # Set a timeout for the connection attempt
            result = sock.connect_ex((host, port))
            if result == 0:
                open_ports.append(port)
    return open_ports

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/crawler', methods=['GET', 'POST'])
def crawler():
    global crawled_links
    if request.method == 'POST':
        url = request.form['url']
        depth = int(request.form['depth'])
        crawled_links = set()  # Reset the crawled links
        thread = threading.Thread(target=crawl, args=(url, depth))
        thread.start()
        thread.join()  # Wait for the thread to finish
        return render_template('crawler.html', links=crawled_links)
    return render_template('crawler.html', links=None)

@app.route('/check_ports', methods=['POST'])
def check_ports():
    host = request.form['host']
    ports = list(map(int, request.form.getlist('ports')))
    open_ports = check_open_ports(host, ports)
    return render_template('port_check.html', host=host, open_ports=open_ports)

@app.route('/find_js', methods=['POST'])
def find_js():
    js_url = request.form['js_url']
    js_files = []
    try:
        response = requests.get(js_url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            for script in soup.find_all('script', src=True):
                js_files.append(urljoin(js_url, script['src']))
    except requests.RequestException:
        pass
    return render_template('js_files.html', js_files=js_files)

if __name__ == '__main__':
    app.run(debug=False,host='0.0.0.0')