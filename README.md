# NEON SNAKE — Sound Edition

A neon-themed Snake arcade game built with **Python 3.11** and **Pygame**. Guide the snake, eat food, avoid collisions, beat your high score, and switch between six visual themes.

## Project Structure

```text
snake_game/
|
├── click.wav
├── die.wav
├── eat.wav
├── highscore.json
├── README.md
├── requirements.txt
├── settings.json
├── snake_game_sound_v1.py
├── snake_game_sound_v2.py
├── snake_game_sound.py       # Main/current game file
└── snake.py
```

**Note:** `snake_game_sound.py` is the main file to run. The `_v1` and `_v2` files are alternate versions/backups. Keep them only if you need them.

## Features

- Cyberpunk-inspired neon visuals
- Six themes with different arena colors, snake designs, and food styles
- Score and high-score HUD
- Normal food and bonus food
- Pause and resume
- Easy, Normal, and Hard difficulty options
- Sound effects for eating, game over, and UI interactions
- Settings saved locally in `settings.json`
- High score and game statistics saved in `highscore.json`
- Keyboard controls and clickable menu buttons

## Themes

Open **Settings** and select **NEXT THEME** to cycle through the available themes. Your selected theme is saved in `settings.json`.

| Theme | Arena style | Snake design | Food design |
|---|---|---|---|
| **Cyberpunk** | Dark navy with neon accents | Glowing cyan segments and bright head | Magenta glowing orb |
| **Retro Arcade** | Dark green, pixel-grid look | Square green pixel segments | Red/orange pixel food |
| **Candy Pop** | Dark purple with candy colors | Rounded pink bubble segments | Wrapped-candy style food |
| **Toxic Lab** | Dark teal laboratory palette | Acid-green segments with markings | Green bio-style orb |
| **Solar Flare** | Dark red/orange palette | Flame-shaped orange segments | Star-shaped food |
| **Ocean** | Deep blue underwater palette | Streamlined blue segments | Shiny pearl-style food |

Bonus food appears gold and gives **30 points**; regular food gives **10 points**. Theme visuals change the arena, snake, and regular food design. Bonus food keeps its gold star appearance so it is easy to recognize.

## Requirements

- **Python 3.11**
- Dependencies listed in `requirements.txt`
- Pygame-compatible desktop environment

## Setup and Run

### 1. Check Python

```bash
python --version
```

Use Python 3.11.x. If your system uses the Python launcher on Windows, you can check with:

```powershell
py -3.11 --version
```

### 2. Open a terminal in the project folder

In VS Code, choose **Terminal → New Terminal**. Make sure the terminal is in the `snake_game` folder—the same folder that contains `snake_game_sound.py` and `requirements.txt`.

### 3. Create a virtual environment (recommended)

**Windows PowerShell:**

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**macOS / Linux:**

```bash
python3.11 -m venv .venv
source .venv/bin/activate
```

### 4. Install requirements

Install dependencies before launching the game:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 5. Start the game

```bash
python snake_game_sound.py
```

## Controls

| Key | Action |
|---|---|
| `Space` / `Enter` | Start the game |
| `Arrow keys` or `WASD` | Move the snake |
| `P` or `Esc` | Pause or resume |
| `1` / `2` / `3` in Settings | Select Easy / Normal / Hard |
| `R` / `Enter` after game over | Restart |
| `M` after game over | Return to menu |
| `Q` after game over | Quit |

You can also use the on-screen buttons to navigate the menus.

## Sound Files

Keep these WAV files in the same folder as `snake_game_sound.py`:

- `eat.wav` — food-eaten sound
- `die.wav` — game-over sound
- `click.wav` — menu interaction sound

The game is designed to continue if a sound file is missing, but the corresponding sound effect will not play.

## Save Files

- `highscore.json` stores the high score and game statistics.
- `settings.json` stores your selected theme, difficulty, sound toggle, and volume.

These files are created or updated by the game. Keep the folder writable so saved settings and scores can persist.

## Troubleshooting

### Pygame is missing

Activate your virtual environment and run:

```bash
python -m pip install -r requirements.txt
```

### The game cannot find a sound

Make sure the WAV files are beside `snake_game_sound.py`, not only inside another folder.

### GitHub does not show screenshots

If you add screenshots later, commit them to the repository and use relative Markdown paths such as `images/gameplay.png`.

## License

This project is licensed under the **MIT License**. See the `LICENSE` file if it is included in the repository.
