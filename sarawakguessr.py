import customtkinter as ctk
from tkintermapview import TkinterMapView
from PIL import Image, ImageTk
from math import radians, sin, cos, sqrt, atan2
from photos import PHOTOS
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
IMAGES_DIR = BASE_DIR / "images"

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

appWidth, appHeight = 1500, 900


# App Class
class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.photo_image = None
        self.current_photo = 0
        self.guess_lat = None
        self.guess_lon = None
        self.player_score = 0

        self.title("SarawakGuessr")
        self.geometry(f"{appWidth}x{appHeight}")
        self.iconbitmap("images/sarawak_icon.ico")

        image = Image.open("images/transparent_marker.png")
        self.icon_image = ImageTk.PhotoImage(image)

        self.left_frame = ctk.CTkFrame(self)
        self.left_frame.pack(side="left", fill="y", padx=10, pady=10)

        self.title_label = ctk.CTkLabel(self.left_frame, text="Historical Photo", font=("Arial", 20, "bold"))
        self.title_label.pack(pady=10)

        self.image_label = ctk.CTkLabel(self.left_frame, text="")
        self.image_label.pack(pady=10)

        self.guess_year_label = ctk.CTkLabel(self.left_frame, text="Guess Year")
        self.guess_year_label.pack()

        self.year_entry = ctk.CTkEntry(self.left_frame, width=150)
        self.year_entry.pack(pady=5)

        self.submit_button = ctk.CTkButton(self.left_frame, text="Submit Guess", command=self.submit_guess)
        self.submit_button.pack(pady=10)

        self.next_button = ctk.CTkButton(self.left_frame, text="Next Photo", command=self.next_photo)
        self.next_button.pack(pady=5)
        self.next_button.configure(state="disabled")

        self.restart_button = ctk.CTkButton(self.left_frame, text="Start Again", command=self.restart_game)
        self.restart_button.pack(pady=(10, 0))

        self.restart_button.configure(state="disabled")

        self.scoreboard_frame = ctk.CTkFrame(self.left_frame, border_width=2)

        self.scoreboard_frame.pack(fill="both", expand=True, padx=20, pady=20)

        self.result_label = ctk.CTkLabel(self.scoreboard_frame, text="", justify="center", anchor="center")
        self.result_label.pack(pady=20, padx=10, expand=True, fill="both")

        self.map_widget = TkinterMapView(self)

        self.map_widget.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        self.map_widget.set_position(2.8, 113.5)
        self.map_widget.set_zoom(7)

        self.map_widget.add_left_click_map_command(self.map_click)

        self.load_photo()

    # Calculate the great-circle distance between two geographic coordinates via Haversine formula
    @staticmethod
    def distance_km(lat1, lon1, lat2, lon2):
        earth_r = 6371

        distance_lat = radians(lat2 - lat1)
        distance_lon = radians(lon2 - lon1)

        a = (
                sin(distance_lat / 2) ** 2
                + cos(radians(lat1))
                * cos(radians(lat2))
                * sin(distance_lon / 2) ** 2
        )

        c = 2 * atan2(sqrt(a), sqrt(1 - a))

        return earth_r * c

    # Calculate the great-circle distance between two geographic coordinates via Haversine formula
    @staticmethod
    def mid_point(lat1, lon1, lat2, lon2):

        lat_mid = (lat2 + lat1) / 2
        lon_mid = (lon2 + lon1) / 2

        return lat_mid, lon_mid

    # Loads the current photo, updates the UI elements, and resets the map and input fields for a new guess
    def load_photo(self):

        # Reset previous guess
        self.guess_lat = None
        self.guess_lon = None

        data = PHOTOS[self.current_photo]

        image = Image.open(data["image"])

        self.photo_image = ctk.CTkImage(light_image=image, dark_image=image, size=(500, 350))

        self.image_label.configure(image=self.photo_image)

        self.title_label.configure(text=f"Photo {self.current_photo + 1} of {len(PHOTOS)}")

        self.result_label.configure(text="")

        self.year_entry.delete(0, "end")

        self.next_button.configure(state="disabled")

        self.submit_button.configure(state="normal")

        self.map_widget.delete_all_marker()

        self.map_widget.delete_all_path()

        self.map_widget.set_position(2.8, 113.5)
        self.map_widget.set_zoom(7)

    # Handle user clicks on the map
    def map_click(self, coords):
        self.guess_lat, self.guess_lon = coords

        self.map_widget.delete_all_marker()

        self.map_widget.set_marker(self.guess_lat, self.guess_lon, text="Your Guess")

    # Processes the player's location and year guesses, calculates the round score, and displays the results
    def submit_guess(self):

        if self.guess_lat is None:
            self.result_label.configure(
                text="Please click a location on the map."
            )
            return

        try:
            guessed_year = int(self.year_entry.get())
        except ValueError:
            self.result_label.configure(text="Enter a valid year")
            return

        data = PHOTOS[self.current_photo]

        actual_lat, actual_lon = data["location"]
        actual_year = data["year"]

        # Distance
        distance_error = self.distance_km(
            self.guess_lat,
            self.guess_lon,
            actual_lat,
            actual_lon
        )

        # Midpoint coordinate to place distance error marker
        midpoint_lat, midpoint_lon = self.mid_point(self.guess_lat, self.guess_lon, actual_lat, actual_lon)

        # Year
        year_error = abs(
            guessed_year - actual_year
        )

        # Max 5000 points for perfect location, reduced by 1 point for every kilometre of distance error
        distance_score = max(
            0,
            5000 - int(distance_error)
        )

        # Max 1000 points for year score, reduced by 20 points per year difference
        year_score = max(
            0,
            1000 - (year_error * 20)
        )

        round_score = distance_score + year_score

        self.player_score += round_score

        # Show correct location
        self.map_widget.set_marker(actual_lat,
                                   actual_lon,
                                   text="Correct Location",
                                   text_color="black",
                                   marker_color_outside="black",
                                   marker_color_circle="#5C5A59")

        # Show distance error marker
        self.map_widget.set_marker(midpoint_lat,
                                   midpoint_lon,
                                   icon=self.icon_image,
                                   text=f"\n {distance_error:.1f} km",
                                   text_color="#BA4318",
                                   font=("Segoe UI", 12, "bold"))

        self.result_label.configure(
            text=f"Correct Year:       {actual_year}\n\n"
                 f"Distance Error:    {distance_error:.1f} km\n\n"
                 f"Year Error:            {year_error} years\n\n"
                 f"Round Score:       {round_score}\n\n"
                 f"Total Score:         {self.player_score}"
        )

        self.submit_button.configure(state="disabled")

        # Enable "Next Photo" button after submitting a guess
        if self.current_photo < len(PHOTOS) - 1:
            self.next_button.configure(state="normal")

        # Enable restart button after the final photo is submitted
        if self.current_photo == len(PHOTOS) - 1:
            self.result_label.configure(
                text=f"Game Finished!\n\n"
                     f"Distance Error:    {distance_error:.1f} km\n"
                     f"Year Error:            {year_error} years\n"
                     f"Round Score:       {round_score}\n"
                     f"Final Score:         {self.player_score}"
            )
            self.restart_button.configure(state="normal")
            self.next_button.configure(state="disabled")

        # Show the line between player's guess and actual location
        self.map_widget.set_path([(self.guess_lat, self.guess_lon), (actual_lat, actual_lon)],
                                 color="#403E3D",
                                 width=3)

    # Move to the next photo after the player submits a guess
    def next_photo(self):

        if self.current_photo < len(PHOTOS) - 1:
            self.current_photo += 1
            self.load_photo()

    # Restart the game from beginning
    def restart_game(self):
        self.current_photo = 0
        self.player_score = 0
        self.guess_lat = None
        self.guess_lon = None

        self.restart_button.configure(state="disabled")
        self.submit_button.configure(state="normal")

        self.load_photo()


app = App()
app.mainloop()
