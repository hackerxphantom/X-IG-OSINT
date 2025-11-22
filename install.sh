#!/bin/bash

echo -e "\e[95m[+] Installing X-IG OSINT Requirements...\e[0m"

pkg update -y
pkg install python -y
pkg install clang -y
pkg install libxml2 libxslt -y

pip install --upgrade pip

pip install requests beautifulsoup4 lxml rich colorama pyfiglet \
            aiohttp tqdm phonenumbers python-whois pillow \
            opencv-python numpy scikit-learn pandas matplotlib \
            dateparser python-dotenv cloudscraper

echo -e "\e[92m[✓] All requirements installed successfully!\e[0m"
