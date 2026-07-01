# FBS Roster Viewer Pro 🏈

A modern, fast, and fully-featured desktop desktop application that pulls live college football data directly from ESPN's Core API. It allows users to browse all 138 FBS teams, view live rosters, and pull up high-resolution player headshots and biographical data instantly.

Built with Python and **CustomTkinter** for a sleek, dark-mode native interface.

## Features
* **Live ESPN API Integration:** Automatically fetches accurate, up-to-date rosters for all active Division 1 FBS programs.
* **Smart Search & Filtering:** Instantly filter a team's roster by a player's name or position (e.g., type "QB" to see all quarterbacks).
* **Asynchronous Threading:** Network requests run in the background, ensuring the UI never freezes while downloading data or high-res images.
* **Intelligent Data Caching:** Rosters, team logos, and player headshots are cached in memory so returning to a previously viewed team or player is instantaneous.
* **Modern UI/UX:** Built with CustomTkinter, featuring automatic window centering, dynamic column alignment, custom loading throbbers, and graceful error handling for missing player images.

## Screenshots
*(Consider adding a screenshot of your app here by uploading it to your repo and linking it like this: `![App Screenshot](image.png)`)*

## Prerequisites
To run the source code, you will need Python 3 installed on your machine. 

Clone the repository and install the required dependencies using pip:
```bash
pip install customtkinter requests Pillow
```

Running the App
Once your dependencies are installed, you can launch the application directly from your terminal:

```Bash
python roster_image_viewer.py
```

Building a Standalone Executable
If you want to package this application into a standalone .exe (Windows) or .app (Mac) file so it can be run without installing Python, use PyInstaller.

Install PyInstaller:

```Bash
pip install pyinstaller
```
Run the build command (this includes the CustomTkinter UI assets and hides the background console):

```Bash
pyinstaller --noconfirm --onefile --windowed --collect-all customtkinter "roster_image_viewer.py"
```
Your compiled application will be located inside the newly generated dist folder.

Disclaimer
This project is for educational purposes. It utilizes ESPN's public/undocumented APIs (site.api.espn.com and a.espncdn.com). Data structures and availability are subject to change at ESPN's discretion.
