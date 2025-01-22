from flask import Flask, render_template, request
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import threading
import socket
import whois as w
import sublist3r
import subprocess

app = Flask(__name__)

# To store crawled links
# crawled_links = set()
# lock = threading.Lock()

# def crawl(url, depth):
#     if depth < 0:
#         return
#     try:
#         response = requests.get(url)
#         if response.status_code == 200:
#             with lock:
#                 crawled_links.add(url)
#             soup = BeautifulSoup(response.text, 'html.parser')
#             for link in soup.find_all('a', href=True):
#                 full_url = urljoin(url, link['href'])
#                 if full_url not in crawled_links:
#                     crawl(full_url, depth - 1)
#     except requests.RequestException:
#         pass


@app.route('/')
def home():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/crawler',methods=['GET','POST'])
def crawler():
    global crawled_links
    crawled_links = []
    if request.method == 'POST':
        url = request.form['url']
        response = requests.get(url)

        response.raise_for_status()  # Raise an error for bad responses

        # Parse the HTML content
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find all links on the page
        links = soup.find_all('a')

        # Print the title and URL of each link
        for link in links:
            title = link.get('title')  
            href = link.get('href')   
            if href: 
                full_url = urljoin(url, href)  
                crawled_links.append(full_url)

        return render_template('crawler.html', links=crawled_links)
    return render_template('crawler.html',links=None)



# @app.route('/crawler', methods=['GET', 'POST'])
# def crawler():
#     global crawled_links
#     if request.method == 'POST':
#         url = request.form['url']
#         depth = int(request.form['depth'])
#         crawled_links = set()  # Reset the crawled links
#         thread = threading.Thread(target=crawl, args=(url, depth))
#         thread.start()
#         thread.join()  # Wait for the thread to finish
#         return render_template('crawler.html', links=crawled_links)
#     return render_template('crawler.html')


@app.route('/find_js', methods=['GET','POST'])
def find_js():
    js_files = []
    if request.method == 'POST':
        url = request.form['url']
        try:
            response = requests.get(url)
            response.raise_for_status()  # Raise an error for bad responses
            soup = BeautifulSoup(response.text, 'html.parser')

            # Find all script tags
            for script in soup.find_all('script'):
                src = script.get('src')
                if src:
                    js_files.append(urljoin(url, src))  # Resolve relative URLs

        except requests.exceptions.RequestException as e:
            js_files.append(f"Error: {str(e)}")

    return render_template('js_files.html', js_files=js_files)


#code to check technologies used in website
@app.route('/technology', methods=['GET', 'POST'])
def technology():
    technologies = []
    if request.method == 'POST':
        url = request.form['url']
        try:
            response = requests.get(url)
            response.raise_for_status()  # Raise an error for bad responses
            soup = BeautifulSoup(response.text, 'html.parser')

            # Check for common technologies
            if soup.find('script', src=lambda x: x and 'jquery' in x):
                technologies.append('jQuery')
            if soup.find('link', href=lambda x: x and 'bootstrap' in x):
                technologies.append('Bootstrap')
            if soup.find('script', src=lambda x: x and 'react' in x):
                technologies.append('React')
            if soup.find('script', src=lambda x: x and 'angular' in x):
                technologies.append('Angular')
            if soup.find('script', src=lambda x: x and 'vue' in x):
                technologies.append('Vue.js')
            if soup.find('script', src=lambda x: x and 'd3' in x):
                technologies.append('D3.js')
            if soup.find('link', href=lambda x: x and 'font-awesome' in x):
                technologies.append('Font Awesome')

        except requests.exceptions.RequestException as e:
            technologies.append(f"Error: {str(e)}")

    return render_template('tech.html', technologies=technologies)

#check vulnerabilities ::

def check_vulnerabilities(url):
    vulnerabilities = []
    
    # Example checks (these are very basic and for demonstration purposes only)
    try:
        response = requests.get(url)
        
        # Check for common vulnerabilities
        if "SQL" in response.text:
            vulnerabilities.append("Potential SQL Injection vulnerability detected.")
        if "XSS" in response.text:
            vulnerabilities.append("Potential Cross-Site Scripting (XSS) vulnerability detected.")
        if response.status_code == 200:
            vulnerabilities.append("Website is reachable.")
        else:
            vulnerabilities.append(f"Website returned status code: {response.status_code}")
    except requests.exceptions.RequestException as e:
        vulnerabilities.append(f"Error accessing the URL: {str(e)}")
    
    return vulnerabilities

@app.route('/vuln', methods=['GET', 'POST'])
def vuln():
    vulnerabilities = []
    if request.method == 'POST':
        url = request.form['url']
        vulnerabilities = check_vulnerabilities(url)
    return render_template('check_vuln.html', vulnerabilities=vulnerabilities)


#Fetch Whois Data

@app.route("/whois_func", methods=["GET", "POST"])
def whois_func():
    if request.method == "POST":
        url = request.form.get("url")
        if not url:
            return render_template("whois.html", error="Please enter a URL.")
        try:
            whois_data = w.whois(url)  
            # print("aniket")
            # print(whois_data)
            whois_data = dict(whois_data)
            return render_template("whois.html",whois_data=whois_data)
        
        except Exception as e:
            error = f"Error fetching WHOIS data: {str(e)}"
            return render_template("whois.html",error=error)
    
    return render_template("whois.html")


#Find out subdomains 

def find_subdomains(domain):
    try:
        # Run Sublist3r as a subprocess
        result = subprocess.run(['sublist3r', '-d', domain, '-o', 'subdomains.txt'], capture_output=True, text=True)
        with open('subdomains.txt', 'r') as file:
            subdomains = file.readlines()
        return [subdomain.strip() for subdomain in subdomains]
    except Exception as e:
        return str(e)

@app.route('/subs', methods=['GET', 'POST'])
def subs():
    subdomains = []
    if request.method == 'POST':
        domain = request.form['domain']
        subdomains = find_subdomains(domain)
    return render_template('subdomains.html', subdomains=subdomains)
