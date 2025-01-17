# ------------------------------------------------------------------------------------------
#   Project Ripple
#   by Tejune
# ------------------------------------------------------------------------------------------

import random
import traceback

import pygame

from .constants import (
    BLACK,
    FONT,
    FONT_ARTIST,
    FONT_DIFF,
    FONT_HEADER,
    FONT_PIXEL,
    FONT_SMALL,
    FONT_TITLE,
    FPS_COUNTER_ENABLED,
    HEIGHT,
    RED,
    WHITE,
    WIDTH,
    Framerate,
)
from .helper_methods import resource, user_dir
from .logs import line, log, message

# Imports
from .song_loader import load_songs
from .song_player import play_song  # Tejune stupid? Lägg imports på toppen
from .start_screen import show_loading_screen, show_title_screen

log("Initializing pygame", "info", line())
# Initialize pygame module
pygame.mixer.pre_init(44100, 16, 2, 4096)
pygame.init()
pygame.mixer.init(44100, -16, 2, 2048)  # (frequency, size, channels, buffer))
log("Finished initializing pygame", "update", line())

# Pygame variables & Constants
log("Initializing pygame variables", "info", line())
pygame.display.set_caption("Project Ripple")  # Set Caption
infoObject = pygame.display.Info()
WIN = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
clock = pygame.time.Clock()
log("Finished initializing pygame variables", "update", line())

log("Loading image related directories and dictionaries", "info", line())
# Directory & Dictionary
default_thumbnail = pygame.image.load(resource("images/default_thumb.jpg")).convert()
song_select_fade = pygame.image.load(
    resource("images/song_select_fade.png")
).convert_alpha()
song_selected_fade = pygame.image.load(
    resource("images/song_selected_fade.png")
).convert_alpha()
songs = []
log("Finished loading image related directories and dictionaries", "update", line())


# Song selection & Playing songs
log("Loading song selection and prerequisites for playing songs", "info", line())
scroll_offset = 0
selected_song = None
last_song = None
frames_since_last_song = 500  # Any value high enough will do
song_select_offset = 0

play_button = pygame.image.load(resource("images/play_button.png")).convert_alpha()
play_button = pygame.transform.scale(play_button, (48, 48))


log(
    "Finished loading song selection and prerequisites for playing songs",
    "update",
    line(),
)

############# Functions & Classes ##############


# Button class
class Button:
    """Create a button, then blit the surface in the while loop"""

    def __init__(self, song, text, pos, font, bg="black", feedback="", list_position=0):
        self.x, self.y = pos
        self.font = FONT
        self.input = text
        self.song = song
        self.selected_song_offset = 0
        self.offset = 0
        self.list_position = list_position

        # Ripple related (visible when selected)
        self.ripple_time = 0
        try:
            self.ripple_spawn_frequency = (60 / song["BPM"]) * 1000
        except TypeError:
            self.ripple_spawn_frequency = 1000
        self.ripples = []

        if self.ripple_spawn_frequency > 200:
            self.ripple_spawn_frequency = self.ripple_spawn_frequency * 2

        # Calculate bounds
        self.bound_x, self.bound_y = FONT.size(text)
        self.bound_x = WIDTH * 0.5
        self.bound_y = self.bound_y + 60

        # Create image surface
        preview_image_surface = pygame.Surface((self.bound_x, self.bound_y))
        preview_image_surface.set_alpha(255)

        if self.song["LoadedImageBlurredPreview"] == "None":
            self.song["LoadedImageBlurredPreview"] = self.song[
                "LoadedImage"
            ]  # pygame.transform.scale(self.song["LoadedImageBlurred"], (self.bound_x, HEIGHT * 0.5))

        # Create subtext
        self.subtext = FONT_ARTIST.render("by " + self.song["Artist"], 1, WHITE)

        # Create fade surface
        self.song_select_fade = pygame.transform.scale(
            song_select_fade, (self.bound_x, self.bound_y + 18)
        )
        self.song_selected_fade = pygame.transform.scale(
            song_selected_fade, (self.bound_x, self.bound_y + 18)
        )
        self.bg_fade = self.song_select_fade

        # Create tags
        self.diff_bound_x, self.diff_bound_y = FONT_DIFF.size(
            self.song["DifficultyName"].upper()
        )
        self.difficulty = FONT_DIFF.render(
            self.song["DifficultyName"].upper(), 1, WHITE
        )

        self.bpm_bound_x, self.bpm_bound_y = FONT_DIFF.size(
            str(self.song["BPM"]).upper() + " BPM"
        )
        self.bpm = FONT_DIFF.render(str(self.song["BPM"]).upper() + " BPM", 1, WHITE)

        if feedback == "":
            self.feedback = "text"
        else:
            self.feedback = feedback
        self.change_text(text, bg)

    def change_text(self, text, bg="black"):
        """Change the text when you click"""
        if len(text) > 40:
            text = text[0:37] + "..."
        self.input = text

        # Create text objects
        self.text_standard = self.font.render(self.input, 1, WHITE)
        self.text_highlighted = self.font.render(self.input, 1, (200, 200, 255))
        self.text = self.text_standard

        self.bound_x, self.bound_y = FONT.size(text)
        self.bound_x = WIDTH * 0.5
        self.bound_y = self.bound_y + 60
        self.size = (self.bound_x, self.bound_y + 18)
        self.surface = pygame.Surface(self.size, pygame.SRCALPHA)
        self.surface.convert_alpha()
        # self.surface.fill(bg)
        self.surface.blit(self.text, (WIDTH - WIDTH * 0.4 + 9, 9))
        self.rect = pygame.Rect(self.x, self.y, self.size[0], self.size[1])

    def show(self, delta_time):
        # Get mouse position and create collision mask
        m_x, m_y = pygame.mouse.get_pos()
        self.rect = pygame.Rect(
            self.x, self.y + scroll_offset, self.size[0], self.size[1]
        )

        # Adjust selected song offset
        if selected_song == self.song:
            self.selected_song_offset = max((self.selected_song_offset / 1.4) - 60, -60)
        else:
            self.selected_song_offset = min(self.selected_song_offset / 2, 0)

        # Collision check with mouse (hover)
        if self.rect.collidepoint(m_x, m_y):
            self.text = (
                self.text_highlighted
            )  # Make the text slightly brighter when hovered over or selected
        else:
            self.text = self.text_standard  # Otherwise remain white

        # Create button surface
        self.size = (self.bound_x, self.bound_y + 18)
        self.surface = pygame.Surface(self.size, pygame.SRCALPHA)
        self.surface.convert_alpha()

        # Create mask used by image to create corners
        pygame.draw.rect(
            self.surface, (255, 255, 255), (0, 0, *self.size), border_radius=5
        )

        # Draw image to surface
        self.surface.blit(
            self.song["LoadedImageBlurredPreview"],
            (0, -(HEIGHT * 0.18)),
            None,
            pygame.BLEND_RGBA_MIN,
        )

        # Add transparent background under song list
        _bg = pygame.Surface((self.bound_x, self.bound_y + 18), pygame.SRCALPHA)
        _bg.set_alpha(200)

        # Create another mask used by the background surface to create corners
        pygame.draw.rect(_bg, (255, 255, 255), (0, 0, *_bg.get_size()), border_radius=5)

        if self.song == selected_song:
            self.bg_fade = self.song_selected_fade
        else:
            self.bg_fade = self.song_select_fade

        _bg.blit(self.bg_fade, (0, 0), None, pygame.BLEND_RGBA_MIN)
        self.surface.blit(_bg, (0, 0))

        # Draw difficulty rating and BPM
        _extras = pygame.Surface((self.bound_x, self.bound_y + 18), pygame.SRCALPHA)
        _extras.set_alpha(200)

        pygame.draw.rect(
            _extras, BLACK, pygame.Rect(13, 75, 26 + self.diff_bound_x, 18), 0, 9
        )
        pygame.draw.rect(
            _extras,
            BLACK,
            pygame.Rect(19 + 26 + self.diff_bound_x, 75, 26 + self.bpm_bound_x, 18),
            0,
            9,
        )

        # Draw text and background to surface
        if self.song == selected_song:
            pygame.draw.rect(
                self.surface,
                (200, 200, 255),
                (0, 0, self.bound_x, self.bound_y + 18),
                2,
                5,
            )
        else:
            pygame.draw.rect(
                self.surface,
                (200, 200, 200),
                (0, 0, self.bound_x, self.bound_y + 18),
                2,
                5,
            )

        scrolling_effect_offset = (
            abs((WIDTH / 4) - (self.y + scroll_offset)) / 9
        ) + self.selected_song_offset

        # Topbar ripple effect
        self.ripple_time += delta_time
        if self.ripple_time >= self.ripple_spawn_frequency:
            # Create ripple
            self.ripples.append(0)
            self.ripple_time = 0
        for lifetime in self.ripples:
            self.ripples[self.ripples.index(lifetime)] += 1

            if self.song == selected_song and lifetime > 5:
                ripple_surface = pygame.Surface(
                    (self.bound_x, self.bound_y + 18), pygame.SRCALPHA
                )
                ripple_surface.set_alpha(60 - lifetime)
                ripple_rect = pygame.Rect(
                    (self.bound_x - 152) - 9 * lifetime / 2,
                    (26 + 28) - 9 * lifetime / 2,
                    9 * lifetime,
                    9 * lifetime,
                )
                pygame.draw.ellipse(ripple_surface, (200, 200, 255), ripple_rect, 3)
                self.surface.blit(ripple_surface, (0, 0))

            if lifetime >= 60:
                self.ripples.remove(lifetime + 1)

        self.surface.blit(self.text, (self.offset + 12, 16))
        self.surface.blit(self.subtext, (self.offset + 13, 48))
        self.surface.blit(_extras, (0, 0))
        self.surface.blit(self.difficulty, (24, 78))
        self.surface.blit(self.bpm, (19 + 26 + self.diff_bound_x + 13, 78))

        if self.song == selected_song:
            self.surface.blit(play_button, (self.bound_x - 176, 30))

        # Draw the text surface to the screen
        WIN.blit(
            self.surface,
            (
                self.x + scrolling_effect_offset + (song_select_offset),
                self.y + scroll_offset,
            ),
        )

    def click(self, event, currently_selected_song, forcedSelection=False):
        global last_song
        global frames_since_last_song
        global button_list_position

        try:
            x, y = pygame.mouse.get_pos()
        except Exception:
            exit()  # Allow f4 exit
        if forcedSelection or event.type == pygame.MOUSEBUTTONDOWN:
            if forcedSelection or pygame.mouse.get_pressed()[0]:
                if not forcedSelection:
                    self.rect = pygame.Rect(
                        self.x, self.y + scroll_offset, self.size[0], self.size[1]
                    )

                if forcedSelection or self.rect.collidepoint(x, y):
                    if currently_selected_song == self.song:
                        pygame.mixer.Channel(2).stop()

                        # Play song using the song player. Catch errors and alert the player.
                        try:
                            play_song(self.song, WIN, clock)
                            pygame.mixer.Channel(2).play(
                                pygame.mixer.Sound(resource("sound/Title.wav"))
                            )
                        except Exception as error:
                            log(
                                f"Error while playing song: {str(error)}",
                                "error",
                                line(),
                            )
                            log(f"{str(traceback.format_exc())}", "error", line())
                            message("Song was interrupted due to an unexpected error. Sorry!")

                    else:
                        last_song = selected_song
                        currently_selected_song = self.song
                        button_list_position = self.list_position
                        self.selected_song_offset = 60

                        # Change song (but only if it's actually a new song and not the same one)
                        if self.song["Title"] != last_song["Title"]:
                            frames_since_last_song = 0
                            pygame.mixer.music.stop()
                            pygame.mixer.music.load(self.song["Audio"])
                            pygame.mixer.music.play(
                                start=(int(self.song["SongPreviewTime"]) / 1000)
                            )
                            pygame.mixer.music.set_volume(0.4)
                            pygame.mixer.Channel(2).stop()

                        return currently_selected_song


# --------- Compile songs and show menu screen ------------------------------------------------------------#

log("Compiling songs...", "info", line())
# Show loading screen
show_loading_screen(WIN, FONT, FONT_TITLE, "Converting new image files...", 10)

# Load songs
try:
    songs = load_songs(WIN)
except FileNotFoundError:
    open(user_dir("cache.json"), "w").write("{}")
    songs = load_songs(WIN)

# Start title screen bgm
pygame.mixer.Channel(2).play(pygame.mixer.Sound(resource("sound/Title.wav")))
pygame.mixer.Channel(2).set_volume(0.4)

# Select a random track
total_songs = len(songs)
random_song = random.randint(0, total_songs - 1)
selected_song = songs[random_song]
current_song = random_song
last_song = selected_song

log(f"Total songs: {total_songs}\nSelected song: {random_song}", "warning", line())

# Show title screen
show_title_screen(WIN, FONT, FONT_TITLE, clock, Framerate, FONT_PIXEL, selected_song)
log("Finished compiling songs.", "update", line())

# --------- Song select screen ----------------------------------------------------------------------------#

# ----- Create buttons -----#

log("Initializing song select screen...", "info", line())

# Define button variables
buttons = []
button_offset = 120
button_x = WIDTH * 0.6 - 50
button_y = 144
button_list_position = 0

last_song_y = 0

# Define variables
is_on_select_screen = True
loops = 0
real_loops = 0
scroll = 0

log("Creating buttons...", "update", line())

# Create buttons
buttons_created = -1
for song in songs:
    song_y = button_y + len(buttons) * button_offset
    last_song_y = -song_y + HEIGHT - button_offset - 20

    if selected_song == song:
        button_list_position = buttons_created + 2
        selected_song = song
        pygame.mixer.music.stop()
        pygame.mixer.music.load(song["Audio"])
        pygame.mixer.music.play(start=(int(song["SongPreviewTime"]) / 1000))
        pygame.mixer.music.set_volume(0.4)
        scroll_offset = -song_y + HEIGHT / 2 - 60

    # Create button class
    buttons_created += 1
    buttons.append(
        Button(
            song,
            song["Title"],
            (button_x, song_y),
            font=30,
            bg=BLACK,
            feedback="You clicked me",
            list_position=buttons_created,
        )
    )

    # Create additional buttons for other versions (TODO: Replace with a proper difficulty system)
    if song.get("OtherDifficulties") is not None:
        for difficulty, notes in song["OtherDifficulties"]:
            new_song = song.copy()
            new_song["Notes"] = notes
            new_song["DifficultyName"] = difficulty

            song_y = button_y + len(buttons) * button_offset
            last_song_y = -song_y + HEIGHT - button_offset - 20

            if selected_song == song:
                selected_song = new_song
                pygame.mixer.music.stop()
                pygame.mixer.music.load(new_song["Audio"])
                pygame.mixer.music.play(start=(int(new_song["SongPreviewTime"]) / 1000))
                pygame.mixer.music.set_volume(0.4)
                scroll_offset = -song_y + HEIGHT / 2 - 60

            # Create button class
            buttons_created += 1
            buttons.append(
                Button(
                    new_song,
                    new_song["Title"],
                    (button_x, song_y),
                    font=30,
                    bg=BLACK,
                    feedback="You clicked me",
                    list_position=buttons_created,
                )
            )


log(
    f"Amount of buttons created: {buttons_created}, Amount of songs: {songs.__len__()}",
    "debug",
    line(),
)

log("Finished initializing song select screen.", "update", line())

log("All outer initialization complete. Entering game loop", "info", line())
# Main song selection loop
while is_on_select_screen:
    # Set constant framerate
    delta_time = clock.tick()

    # Check for events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                # Return to title screen after playing associated sound effect
                pygame.mixer.Channel(0).play(
                    pygame.mixer.Sound(resource("sound/cancel.wav"))
                )
                pygame.mixer.Channel(0).set_volume(4)
                show_title_screen(
                    WIN, FONT, FONT_TITLE, clock, Framerate, FONT_PIXEL, selected_song
                )
                loops = 0
                real_loops = 0

        if event.type == pygame.MOUSEWHEEL:
            if event.y > 0:
                scroll = min(scroll + event.y * 30, 120)
            if event.y < 0:
                scroll = max(scroll + event.y * 30, -120)

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP and button_list_position != 0:
                scroll = min(scroll + 34.3, 500)

                selected_button = buttons[max(button_list_position - 1, 0)]
                log(
                    f"Selection position: {max(button_list_position - 1, 0)}",
                    "warning",
                    line(),
                )

                new_selection = selected_button.click(None, selected_song, True)
                selected_song = new_selection

            if (
                event.key == pygame.K_DOWN
                and button_list_position != buttons.__len__() - 1
            ):
                scroll = max(scroll - 34.3, -500)

                selected_button = buttons[
                    min(button_list_position + 1, buttons.__len__() - 1)
                ]
                log(
                    f"Selection position: {min(button_list_position + 1, buttons.__len__() - 1)}",
                    "warning",
                    line(),
                )

                new_selection = selected_button.click(None, selected_song, True)
                selected_song = new_selection

            if event.key == pygame.K_RETURN:
                selected_button = buttons[button_list_position]
                log("Using enter to enter a song! Hah, get it?", "debug", line())

                selected_button.click(None, selected_song, True)

        for button in buttons:
            new_selection = button.click(event, selected_song)
            if new_selection:
                selected_song = new_selection

    # Adjust scroll offset by current scroll speed
    scroll_offset = max(last_song_y, min(scroll_offset + scroll, 0))

    # Asjust song select offset, which offsets the menu elements when opening the menu for a nice effect
    real_loops += 1
    song_select_offset = round(max((WIDTH * 0.5 / (real_loops * 8)) - 5, 0))

    if scroll > 0:
        scroll = scroll / 1.4
    if scroll < 0:
        scroll = scroll / 1.4

    # Fill screen with black
    WIN.fill(BLACK)

    # Draw selected song thumbnail preview
    if selected_song:
        # Draw the previous song's background
        prev_blur_bg_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        prev_blur_bg_surface.set_alpha(max(255 - frames_since_last_song * 150, 0))
        prev_blur_bg_surface.blit(last_song["LoadedImageBlurredFull"], (0, 0))

        # Draw the current songs background
        _blur_bg_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        _blur_bg_surface.set_alpha(min(frames_since_last_song * 150, 255))
        _blur_bg_surface.blit(selected_song["LoadedImageBlurredFull"], (0, 0))

        WIN.blit(prev_blur_bg_surface, (0, 0))
        WIN.blit(_blur_bg_surface, (0, 0))

        # Increment loop counter
        frames_since_last_song += 1

    # Darken the background
    _bg = pygame.Surface((WIDTH, HEIGHT))
    _bg.set_alpha(100)
    pygame.draw.rect(_bg, BLACK, pygame.Rect(0, 0, WIDTH, HEIGHT))
    WIN.blit(_bg, (0, 0))

    # Add transparent background color under song list
    _bg = pygame.Surface((WIDTH, HEIGHT))
    _bg.set_alpha(100)
    pygame.draw.rect(
        _bg, BLACK, pygame.Rect(WIDTH - WIDTH * 0.4, 0, WIDTH * 0.4, HEIGHT)
    )
    WIN.blit(_bg, (WIDTH * 0.6, 130))

    # Draw all buttons currently on screen
    for button in buttons:
        if button.y + scroll_offset < HEIGHT and button.y + scroll_offset > -200:
            sel = button.show(delta_time)
            if sel:
                selected_song = sel

    # Add transparent background under title
    _title = pygame.Surface((WIDTH, 130))
    _title.set_alpha(175)
    pygame.draw.rect(_title, (5, 5, 5), pygame.Rect(0, 0, WIDTH, 130))
    WIN.blit(_title, (0, 0))

    # Draw title
    subtitle = FONT_HEADER.render("SONG SELECT", True, WHITE)
    WIN.blit(subtitle, (25, 30))

    if FPS_COUNTER_ENABLED:
        fps_text = FONT_SMALL.render(
            f"FPS: {str(round(clock.get_fps()))}", True, WHITE
        )
        WIN.blit(fps_text, (10, HEIGHT - 24))


    # ----- Drawing the song preview window -----#

    # Define dimensions
    preview_width = WIDTH * 0.5 + 5
    preview_height = HEIGHT * 0.4
    preview_pos_x = -5 - song_select_offset
    preview_pos_y = 80
    preview_corner_radius = 3

    # Draw background fill
    pygame.draw.rect(
        WIN, BLACK, (preview_pos_x, preview_pos_y, preview_width, preview_height), 0, 5
    )

    # Draw preview image if a song has been selected
    if selected_song:
        preview_image_surface = pygame.Surface(
            (preview_width, preview_height), pygame.SRCALPHA
        )
        preview_image_surface.set_alpha(min(frames_since_last_song * 150, 255))

        prev_preview_image_surface = pygame.Surface(
            (preview_width, preview_height), pygame.SRCALPHA
        )
        prev_preview_image_surface.set_alpha(max(255 - frames_since_last_song * 150, 0))

        if selected_song["LoadedImagePreview"] == "None":
            selected_song["LoadedImagePreview"] = selected_song[
                "LoadedImage"
            ]  # pygame.transform.scale(, (preview_width, HEIGHT * 0.5))

        if last_song["LoadedImagePreview"] == "None":
            last_song["LoadedImagePreview"] = last_song[
                "LoadedImage"
            ]  # pygame.transform.scale(, (preview_width, HEIGHT * 0.5))

        preview_image = selected_song["LoadedImagePreview"]
        prev_preview_image = last_song["LoadedImagePreview"]

        # Used as a mask to create rounded corners for the displayed image
        pygame.draw.rect(
            preview_image_surface,
            (255, 255, 255),
            (0, 0, *(preview_width, preview_height)),
            border_radius=5,
        )
        pygame.draw.rect(
            prev_preview_image_surface,
            (255, 255, 255),
            (0, 0, *(preview_width, preview_height)),
            border_radius=5,
        )

        preview_image_surface.blit(
            preview_image, (0, -(HEIGHT * 0.05)), None, pygame.BLEND_RGBA_MIN
        )
        prev_preview_image_surface.blit(
            prev_preview_image, (0, -(HEIGHT * 0.05)), None, pygame.BLEND_RGBA_MIN
        )

        WIN.blit(preview_image_surface, (preview_pos_x, preview_pos_y))
        WIN.blit(prev_preview_image_surface, (preview_pos_x, preview_pos_y))

    # Draw preview window outline
    pygame.draw.rect(
        WIN,
        WHITE,
        (preview_pos_x, preview_pos_y, preview_width, preview_height),
        preview_corner_radius,
        5,
    )

    # ----- Drawing the flash effect when entering from main menu -----#

    # Draw flash effect
    # wh = pygame.Surface((WIDTH, HEIGHT))
    # wh.set_alpha(max(150 - loops * 10, 0))
    # wh.fill(WHITE)
    # WIN.blit(wh, (0, 0))
    loops += 1

    # Play the enter sound effect when coming from the main menu
    if loops == 1:
        pygame.mixer.Channel(0).play(pygame.mixer.Sound(resource("sound/enter.wav")))
        pygame.mixer.Channel(0).set_volume(4)
        pygame.mixer.Channel(2).stop()

    # Update display
    pygame.display.update()
