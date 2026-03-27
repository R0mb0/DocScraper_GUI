<div align="center">
<h1>🕵️‍♂️ DocScraper GUI - Stealth Mode 📦</h1>

<p>
An automated, anti-bot document scraper and dataset generator built with Python and CustomTkinter. It bypasses search engine rate limits and strict academic servers to bulk-download PDFs, DOCXs, and text files, instantly extracting and cleaning their text for AI/LLM training.
</p>

[![Codacy Badge](https://app.codacy.com/project/badge/Grade/3eb0017b740249d18ca360e283eade8e)](https://app.codacy.com/gh/R0mb0/DocScraper_GUI/dashboard?utm_source=gh&utm_medium=referral&utm_content=&utm_campaign=Badge_grade)
![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://github.com/R0mb0/DocScraper_GUI)
[![Open Source Love svg3](https://badges.frapsoft.com/os/v3/open-source.svg?v=103)](https://github.com/R0mb0/DocScraper_GUI)
[![MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/license/mit)
[![Donate](https://img.shields.io/badge/PayPal-Donate%20to%20Author-blue.svg)](http://paypal.me/R0mb0)

</div>

 ![demo.png](https://github.com/R0mb0/DocScraper_GUI/blob/main/Readme_imgs/demo.png)

<hr>

<h2>🚀 Features</h2>
<ul>
<li><strong>Stealth Scraping Engine</strong>: Completely bypasses official APIs (which are prone to rate-limiting and blocking). It uses a custom HTML scraper directed at DuckDuckGo to gather URLs securely and anonymously.</li>
<li><strong>Anti-Bot Downloader</strong>: Specifically designed to bypass strict university servers, Cloudflare-protected academic repositories, and expired SSL certificates (<code>verify=False</code>) that usually block standard Python requests.</li>
<li><strong>Multi-Format Support</strong>: Seamlessly downloads and processes <code>.pdf</code>, <code>.docx</code>, <code>.txt</code>, and <code>.csv</code> files based on your custom queries.</li>
<li><strong>Auto-Extraction & Data Cleaning</strong>: No need for a secondary pipeline. A built-in Consumer thread automatically reads the downloaded files, strips away excessive blank lines, and exports a pure <code>_CLEAN.txt</code> file ready for NLP/LLM ingestion.</li>
<li><strong>Multithreaded Architecture</strong>: Features a Producer-Consumer queue system. The UI (built with CustomTkinter) never freezes while the app searches, downloads, and parses documents simultaneously.</li>
<li><strong>Bilingual UI</strong>: Fully supports English and Italian out of the box.</li>
</ul>

<h2>🛠️ How it works (Under the Hood)</h2>
<ol>
<li><strong>The Query Injection</strong>: You input your <i>Include</i> and <i>Exclude</i> keywords. The app formats them into advanced search operators (e.g., <code>machine learning cancer detection filetype:pdf -syllabus</code>).</li>
<li><strong>The Producer (Bypass Search)</strong>: Instead of using easily-blocked APIs, a background thread sends a raw POST request with custom headers to <code>https://www.google.com/search?q=html.duckduckgo.com</code>. It parses the HTML response using <code>BeautifulSoup</code> to extract the hidden redirect URLs.</li>
<li><strong>The Stealth Download</strong>: The app attempts to download the matched files. It applies a human-like User-Agent and ignores insecure SSL warnings—a common issue with old university document servers. It also filters out fake PDFs (HTML block pages disguised as documents).</li>
<li><strong>The Consumer (Extraction)</strong>: As soon as a file is downloaded, it goes into a thread-safe <code>queue.Queue</code>. The Consumer thread picks it up:
<ul>
<li>For <strong>PDFs</strong>, it uses <code>PyMuPDF (fitz)</code> to extract raw text blocks.</li>
<li>For <strong>DOCX</strong>, it iterates through paragraphs using <code>python-docx</code>.</li>
</ul>
</li>
<li><strong>Sanitization</strong>: The extracted text is processed via Regex (<code>re.sub</code>) to collapse excessive line breaks and trim whitespaces, finally saving it as a clean text file.</li>
</ol>

<h2>🏆 What makes it special?</h2>
<ul>
<li><strong>No API Keys Required</strong>: Most scrapers break when Google or DuckDuckGo changes their API policies. By scraping the raw HTML fallback site, this tool remains highly resilient.</li>
<li><strong>Smart Error Handling</strong>: If a server blocks the download or the file is an empty HTML masquerading as a PDF, the tool detects it, deletes the corrupted stub, and gracefully moves on to the next URL without crashing.</li>
</ul>

<h2>📚 Dependencies & Libraries</h2>
<p>This project relies on a few powerful, carefully selected Python libraries. You can install them all at once (see <i>Getting Started</i>).</p>
<ul>
<li><code>customtkinter</code>: Provides the modern, dark-mode ready graphical user interface.</li>
<li><code>requests</code>: Handles the HTTP/HTTPS requests with custom headers for the stealth downloader.</li>
<li><code>beautifulsoup4</code>: Parses the raw HTML returned by the search engine to cleanly extract document URLs.</li>
<li><code>PyMuPDF</code> <i>(imported as <code>fitz</code>)</i>: An incredibly fast C-based library used to extract text from PDF documents.</li>
<li><code>python-docx</code>: Used to open and read text from Microsoft Word (<code>.docx</code>) files.</li>
</ul>

<h2>💡 Why use this tool?</h2>
<ul>
<li><strong>AI/ML Researchers</strong>: Instantly build domain-specific text datasets (e.g., medical papers, legal acts) to fine-tune Large Language Models (LLMs).</li>
<li><strong>Data Scientists</strong>: Automate the tedious process of finding, downloading, and converting hundreds of documents into plain text.</li>
<li><strong>Students & Academics</strong>: Mass-download research papers on a specific topic without manually clicking "Save As" on dozens of websites.</li>
</ul>

<h2>⚡ Getting Started</h2>

<h3>Local Installation</h3>
<p>Running this tool requires Python 3.8 or higher.</p>
<ol>
<li><strong>Clone this repository</strong> or download the source code ZIP.</li>
<li><strong>Open your terminal / command prompt</strong> in the folder where you extracted the files.</li>
<li><strong>Install the required dependencies</strong> by running the following command:
<pre><code>pip install customtkinter requests beautifulsoup4 PyMuPDF python-docx</code></pre>
</li>
<li><strong>Run the application</strong>:
<pre><code>python Dataset_builder.py</code></pre>
</li>
<li>Set your parameters, choose a destination folder, and click <strong>START SEARCH</strong>!</li>
</ol>

<a href="https://github.com/R0mb0/Crafted_with_AI">
<picture>
<source media="(prefers-color-scheme: dark)" srcset="https://github.com/R0mb0/Crafted_with_AI/blob/main/Badge/SVG/CraftedWithAIDark.svg">
<source media="(prefers-color-scheme: light)" srcset="https://github.com/R0mb0/Crafted_with_AI/blob/main/Badge/SVG/NotMadeByAILight.svg">
<img alt="Crafted with AI" src="https://www.google.com/search?q=https://github.com/R0mb0/Crafted_with_AI/blob/main/Badge/SVG/CraftedWithAIDefault.svg">
</picture>
</a>
