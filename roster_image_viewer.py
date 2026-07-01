import customtkinter as ctk
import tkinter as tk
from tkinter import ttk
import requests
import threading
from io import BytesIO
from PIL import Image, ImageDraw
import webbrowser
import re

# Set global appearance for CustomTkinter
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class ESPNAppPro(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("FBS Roster Viewer Pro")
        
        # --- UI Improvement: Center the Window on Screen ---
        window_width = 950
        window_height = 650
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        center_x = int(screen_width / 2 - window_width / 2)
        center_y = int(screen_height / 2 - window_height / 2)
        self.geometry(f"{window_width}x{window_height}+{center_x}+{center_y}")
        self.minsize(850, 600)
        
        # --- Data & Caching ---
        self.team_dict = {}
        self.roster_data = []       # Active team roster list
        self.roster_cache = {}      # Optimization: Caches full rosters per team ID
        self.image_cache = {}       # Stores downloaded headshots
        self.logo_cache = {}        # Stores downloaded team logos
        self.current_url = ""

        self.setup_ui()
        
        # Start fetching teams immediately
        threading.Thread(target=self.fetch_teams_thread, daemon=True).start()

    def setup_ui(self):
        # --- Top Frame: Controls & Team Info ---
        self.top_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.top_frame.pack(side="top", fill="x", pady=15, padx=20)
        
        self.team_logo_label = ctk.CTkLabel(self.top_frame, text="", width=60, height=60)
        self.team_logo_label.pack(side="left", padx=(0, 15))

        # Dropdown Dark Mode Styling Fix
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TCombobox", 
                        fieldbackground="#343638", 
                        background="#2b2b2b", 
                        foreground="white", 
                        bordercolor="#2b2b2b",
                        arrowcolor="white")
        style.map("TCombobox",
                  fieldbackground=[("readonly", "#343638")],
                  foreground=[("readonly", "white")],
                  selectbackground=[("readonly", "#1f538d")],
                  selectforeground=[("readonly", "white")])
        
        self.team_cb = ttk.Combobox(self.top_frame, values=["Loading..."], state="readonly", width=40)
        self.team_cb.pack(side="left")
        self.team_cb.bind("<<ComboboxSelected>>", lambda e: self.on_team_select(self.team_cb.get()))
        
        self.status_label = ctk.CTkLabel(self.top_frame, text="Loading FBS Teams...", text_color="gray")
        self.status_label.pack(side="left", padx=20)

        # --- Main Layout: Left & Right Columns ---
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # --- Left Column: Search & Roster List ---
        self.left_frame = ctk.CTkFrame(self.main_frame, width=340) # Slightly widened for Arial padding
        self.left_frame.pack(side="left", fill="y", padx=(0, 20))
        self.left_frame.pack_propagate(False) 
        
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self.filter_roster)
        self.search_entry = ctk.CTkEntry(self.left_frame, textvariable=self.search_var, placeholder_text="Search by name or position...")
        self.search_entry.pack(fill="x", padx=10, pady=10)
        
        self.listbox_frame = ctk.CTkFrame(self.left_frame)
        self.listbox_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        self.scrollbar = ctk.CTkScrollbar(self.listbox_frame)
        self.scrollbar.pack(side="right", fill="y")
        
        # FIX: Updated to a clean modern Arial font with optimized padding
        self.player_listbox = tk.Listbox(
            self.listbox_frame, bg="#2b2b2b", fg="white", selectbackground="#1f538d", 
            selectforeground="white", highlightthickness=0, borderwidth=0, font=("Arial", 12),
            yscrollcommand=self.scrollbar.set
        )
        self.player_listbox.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        self.scrollbar.configure(command=self.player_listbox.yview)
        self.player_listbox.bind("<<ListboxSelect>>", self.on_player_select)

        # --- Right Column: Player Details & Image ---
        self.right_frame = ctk.CTkFrame(self.main_frame)
        self.right_frame.pack(side="left", fill="both", expand=True)
        
        self.img_label = ctk.CTkLabel(self.right_frame, text="", width=300, height=300)
        self.img_label.pack(pady=(35, 10))
        
        self.name_label = ctk.CTkLabel(self.right_frame, text="Select a team to begin", font=("Arial", 24, "bold"))
        self.name_label.pack()
        
        self.details_label = ctk.CTkLabel(self.right_frame, text="", font=("Arial", 14), text_color="lightgray")
        self.details_label.pack(pady=5)
        
        self.hometown_label = ctk.CTkLabel(self.right_frame, text="", font=("Arial", 14), text_color="lightgray")
        self.hometown_label.pack()
        
        self.link_label = ctk.CTkLabel(self.right_frame, text="", text_color="#5ea8ff", cursor="hand2", font=("Arial", 12, "underline"))
        self.link_label.pack(pady=20)
        self.link_label.bind("<Button-1>", self.open_link)

    # --- Threading & Data Fetching ---
    
    def fetch_teams_thread(self):
        try:
            target_teams = [
                "Air Force Falcons", "Akron Zips", "Alabama Crimson Tide", "Appalachian State Mountaineers", 
                "Arizona Wildcats", "Arizona State Sun Devils", "Arkansas Razorbacks", "Arkansas State Red Wolves", 
                "Army Black Knights", "Auburn Tigers", "Ball State Cardinals", "Baylor Bears", "Boise State Broncos", 
                "Boston College Eagles", "Bowling Green Falcons", "Buffalo Bulls", "BYU Cougars", "California Golden Bears", 
                "Central Michigan Chippewas", "Charlotte 49ers", "Cincinnati Bearcats", "Clemson Tigers", 
                "Coastal Carolina Chanticleers", "Colorado Buffaloes", "Colorado State Rams", "Delaware Fightin’ Blue Hens", 
                "Duke Blue Devils", "East Carolina Pirates", "Eastern Michigan Eagles", "FIU Panthers", "Florida Gators", 
                "Florida Atlantic Owls", "Florida State Seminoles", "Fresno State Bulldogs", "Georgia Bulldogs", 
                "Georgia Southern Eagles", "Georgia State Panthers", "Georgia Tech Yellow Jackets", "Hawaii Rainbow Warriors", 
                "Houston Cougars", "Illinois Fighting Illini", "Indiana Hoosiers", "Iowa Hawkeyes", "Iowa State Cyclones", 
                "Jacksonville State Gamecocks", "James Madison Dukes", "Kansas Jayhawks", "Kansas State Wildcats", 
                "Kennesaw State Owls", "Kent State Golden Flashes", "Kentucky Wildcats", "Liberty Flames", 
                "Louisiana Ragin’ Cajuns", "Louisiana-Monroe Warhawks", "Louisiana Tech Bulldogs", "Louisville Cardinals", 
                "LSU Tigers", "Marshall Thundering Herd", "Maryland Terrapins", "Memphis Tigers", "Miami (FL) Hurricanes", 
                "Miami (OH) RedHawks", "Michigan Wolverines", "Michigan State Spartans", "Middle Tennessee Blue Raiders", 
                "Minnesota Golden Gophers", "Mississippi State Bulldogs", "Missouri Tigers", "Missouri State Bears", 
                "Navy Midshipmen", "NC State Wolfpack", "Nebraska Cornhuskers", "Nevada Wolf Pack", "New Mexico Lobos", 
                "New Mexico State Aggies", "North Carolina Tar Heels", "North Dakota State Bison", "North Texas Mean Green", 
                "Northern Illinois Huskies", "Northwestern Wildcats", "Notre Dame Fighting Irish", "Ohio Bobcats", 
                "Ohio State Buckeyes", "Oklahoma Sooners", "Oklahoma State Cowboys", "Old Dominion Monarchs", "Ole Miss Rebels", 
                "Oregon Ducks", "Oregon State Beavers", "Penn State Nittany Lions", "Pittsburgh Panthers", "Purdue Boilermakers", 
                "Rice Owls", "Rutgers Scarlet Knights", "Sacramento State Hornets", "Sam Houston Bearkats", 
                "San Diego State Aztecs", "San Jose State Spartans", "SMU Mustangs", "South Alabama Jaguars", 
                "South Carolina Gamecocks", "South Florida Bulls", "Southern Miss Golden Eagles", "Stanford Cardinal", 
                "Syracuse Orange", "TCU Horned Frogs", "Temple Owls", "Tennessee Volunteers", "Texas Longhorns", 
                "Texas A&M Aggies", "Texas State Bobcats", "Texas Tech Red Raiders", "Toledo Rockets", "Troy Trojans", 
                "Tulane Green Wave", "Tulsa Golden Hurricane", "UAB Blazers", "UCF Knights", "UCLA Bruins", "UConn Huskies", 
                "UMass Minutemen", "UNLV Rebels", "USC Trojans", "UTEP Miners", "UTSA Roadrunners", "Utah Utes", 
                "Utah State Aggies", "Vanderbilt Commodores", "Virginia Cavaliers", "Virginia Tech Hokies", 
                "Wake Forest Demon Deacons", "Washington Huskies", "Washington State Cougars", "West Virginia Mountaineers", 
                "Western Kentucky Hilltoppers", "Western Michigan Broncos", "Wisconsin Badgers", "Wyoming Cowboys"
            ]

            def normalize(name):
                name = re.sub(r'\(.*?\)', '', name)
                return re.sub(r'[^a-zA-Z0-9]', '', name).lower()

            target_normalized = {normalize(name): name for name in target_teams}
            
            url = "https://site.api.espn.com/apis/site/v2/sports/football/college-football/teams?limit=500"
            data = requests.get(url).json()
            teams = []
            
            for t in data['sports'][0]['leagues'][0]['teams']:
                api_name = t['team']['displayName']
                norm_api_name = normalize(api_name)
                
                if norm_api_name in target_normalized:
                    teams.append({
                        'id': t['team']['id'],
                        'name': target_normalized[norm_api_name],
                        'logo': t['team']['logos'][0]['href'] if 'logos' in t['team'] else None
                    })
            
            teams.sort(key=lambda x: x['name'])
            self.team_dict = {t['name']: t for t in teams}
            
            self.after(0, self.update_teams_ui, list(self.team_dict.keys()))
        except Exception:
            self.after(0, lambda: self.status_label.configure(text="Error loading teams."))

    def update_teams_ui(self, team_names):
        self.team_cb['values'] = team_names
        self.team_cb.set("Select an FBS Team...")
        self.status_label.configure(text="")

    def on_team_select(self, choice):
        team = self.team_dict[choice]
        self.status_label.configure(text=f"Loading {choice}...")
        self.search_var.set("") 
        
        if team['logo']:
            threading.Thread(target=self.fetch_image_thread, args=(team['logo'], True, team['id']), daemon=True).start()
            
        # Optimization check: Read from cache before hitting the web API
        if team['id'] in self.roster_cache:
            self.update_roster_ui(self.roster_cache[team['id']])
        else:
            threading.Thread(target=self.fetch_roster_thread, args=(team['id'],), daemon=True).start()

    def fetch_roster_thread(self, team_id):
        try:
            url = f"https://site.api.espn.com/apis/site/v2/sports/football/college-football/teams/{team_id}/roster"
            data = requests.get(url).json()
            roster = []
            
            if 'athletes' in data:
                for group in data['athletes']:
                    for p in group.get('items', []):
                        bp = p.get('birthplace', {})
                        city, state = bp.get('city', ''), bp.get('stateProvince', '')
                        hometown = f"{city}, {state}".strip(", ")
                        
                        roster.append({
                            'id': p.get('id'),
                            'name': p.get('fullName', 'Unknown'),
                            'jersey': p.get('jersey', '--'),
                            'position': p.get('position', {}).get('abbreviation', '??'),
                            'height': p.get('displayHeight', '-'),
                            'weight': p.get('displayWeight', '-'),
                            'hometown': hometown if hometown else "Unknown"
                        })
                        
            roster.sort(key=lambda x: x['name'])
            
            # Save to Cache
            self.roster_cache[team_id] = roster
            self.after(0, self.update_roster_ui, roster)
        except Exception:
            self.after(0, lambda: self.status_label.configure(text="Error loading roster."))

    def update_roster_ui(self, roster):
        self.roster_data = roster
        self.filter_roster() 
        self.status_label.configure(text="")
        
        # UI Improvement: Automatically select and display the first player in the list
        if self.player_listbox.size() > 0:
            self.player_listbox.selection_set(0)
            self.on_player_select(None)

    def filter_roster(self, *args):
        search_term = self.search_var.get().lower()
        self.player_listbox.delete(0, tk.END)
        
        for player in self.roster_data:
            if search_term in player['name'].lower() or search_term in player['position'].lower():
                # Format Jersey to always take 3 spaces
                jersey_str = f"#{player['jersey']}".ljust(5)
                
                # Dynamically pad the name string so columns line up beautifully in Arial
                name_str = player['name']
                padding_needed = max(1, 26 - len(name_str))
                spacer = " " * padding_needed
                
                display_str = f"{jersey_str}{spacer}{name_str}{spacer}"
                self.player_listbox.insert(tk.END, display_str)

    def on_player_select(self, event):
        selection = self.player_listbox.curselection()
        if not selection: return
        
        selected_row = self.player_listbox.get(selection[0])
        
        # Safely parse the row text back into the player name by stripping the jersey and position tags
        # Splitting off the jersey prefix first
        clean_row = selected_row[5:]
        # Splitting off the trailing position parentheses
        selected_name = clean_row.split(" (")[0].strip()
        
        player = next((p for p in self.roster_data if p['name'] == selected_name), None)
        
        if player:
            self.name_label.configure(text=player['name'])
            self.details_label.configure(text=f"#{player['jersey']} | {player['position']} | {player['height']} | {player['weight']}")
            # self.hometown_label.configure(text=f"📍 {player['hometown']}")
            
            self.current_url = f"https://a.espncdn.com/i/headshots/college-football/players/full/{player['id']}.png"
            self.link_label.configure(text=self.current_url)
            
            # Start the Throbber Animation
            self.start_throbber()
            
            threading.Thread(target=self.fetch_image_thread, args=(self.current_url, False, player['id']), daemon=True).start()

    def fetch_image_thread(self, url, is_logo, item_id):
        cache = self.logo_cache if is_logo else self.image_cache
        
        if item_id in cache:
            self.after(0, self.update_image_ui, cache[item_id], is_logo)
            return
            
        try:
            response = requests.get(url)
            if response.status_code == 200:
                img_data = Image.open(BytesIO(response.content))
            else:
                img_data = self.create_placeholder()
                
            orig_width, orig_height = img_data.size
            max_size = 60 if is_logo else 300
            
            ratio = min(max_size / orig_width, max_size / orig_height)
            new_width = int(orig_width * ratio)
            new_height = int(orig_height * ratio)
            
            ctk_img = ctk.CTkImage(light_image=img_data, dark_image=img_data, size=(new_width, new_height))
            
            cache[item_id] = ctk_img
            self.after(0, self.update_image_ui, ctk_img, is_logo)
        except Exception:
            placeholder = self.create_placeholder()
            ctk_img = ctk.CTkImage(light_image=placeholder, dark_image=placeholder, size=(300, 300))
            self.after(0, self.update_image_ui, ctk_img, is_logo)

    def update_image_ui(self, ctk_img, is_logo):
        if not is_logo:
            self.is_loading_image = False # Turn off the throbber loop
            self.img_label.configure(image=ctk_img, text="")
        else:
            self.team_logo_label.configure(image=ctk_img, text="")

    def start_throbber(self):
        # Braille loading spinner array
        self.throbber_frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self.throbber_index = 0
        self.is_loading_image = True
        self.img_label.configure(image=None) # Wipe old image immediately
        self.animate_throbber()

    def animate_throbber(self):
        if not self.is_loading_image:
            return
            
        frame = self.throbber_frames[self.throbber_index]
        self.img_label.configure(text=f"{frame} Loading headshot...")
        self.throbber_index = (self.throbber_index + 1) % len(self.throbber_frames)
        
        # Fire again in 100 milliseconds
        self.after(100, self.animate_throbber)

    def create_placeholder(self):
        img = Image.new('RGB', (300, 300), color=(43, 43, 43))
        d = ImageDraw.Draw(img)
        d.text((120, 140), "No Image", fill=(200, 200, 200))
        return img

    def open_link(self, event):
        if self.current_url:
            webbrowser.open_new(self.current_url)

if __name__ == "__main__":
    app = ESPNAppPro()
    app.mainloop()