import os
import tkinter as tk
from tkinter import ttk, scrolledtext, font, messagebox
from groq import Groq
from dataclasses import dataclass
from typing import List, Dict
import json
from dotenv import load_dotenv
import threading
import copy
import re

# Load environment variables from .env file
load_dotenv()

# Custom styling constants
BACKGROUND_COLOR = "#2C3E50"  # Dark blue-gray
TEXT_COLOR = "#ECF0F1"  # Light gray
ACCENT_COLOR = "#E74C3C"  # Red
GOLD_COLOR = "#F1C40F"  # Yellow
HEALTH_COLOR = "#2ECC71"  # Green
BUTTON_BG = "#34495E"  # Lighter blue-gray
BUTTON_ACTIVE_BG = "#E74C3C"  # Red when active

def extract_json(text: str) -> str:
    """
    Extracts the first JSON object found in the text using a regex.
    """
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        return match.group(0)
    return text  # Fallback in case no JSON object is found

@dataclass
class PlayerState:
    health: int = 100
    gold: int = 0
    inventory: List[str] = None
    step: int = 0

    def __post_init__(self):
        if self.inventory is None:
            self.inventory = []

    def to_dict(self) -> Dict:
        return {
            "health": self.health,
            "gold": self.gold,
            "inventory": self.inventory,
            "step": self.step
        }

class CustomButton(tk.Button):
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self.config(
            background="#2F3136",  # Discord-like dark gray
            foreground="#FFFFFF",  # White text
            activebackground="#7289DA",  # Discord-like blue when active
            activeforeground="#FFFFFF",
            relief=tk.FLAT,  # Flat modern look
            borderwidth=0,
            padx=20,
            pady=12,
            font=('Helvetica', 11),
            cursor="hand2"  # Hand cursor on hover
        )
        self.bind('<Enter>', self.on_enter)
        self.bind('<Leave>', self.on_leave)

    def on_enter(self, e):
        if self['state'] != 'disabled':
            self['background'] = "#7289DA"  # Discord-like blue

    def on_leave(self, e):
        if self['state'] != 'disabled':
            self['background'] = "#2F3136"  # Back to dark gray

class AdventureGameGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("⚔️ Fantasy Adventure Quest ⚔️")
        self.root.geometry("900x700")
        self.root.configure(bg=BACKGROUND_COLOR)
        
        # Configure custom fonts
        self.title_font = font.Font(family='Helvetica', size=16, weight='bold')
        self.text_font = font.Font(family='Helvetica', size=12)
        self.stats_font = font.Font(family='Helvetica', size=10, weight='bold')
        
        # Initialize game logic
        self.game = AdventureGame(self)
        self.current_scene = None
        self.loading = False
        
        # Add loading messages
        self.loading_messages = [
            "🤔 The dungeon master is rolling dice...",
            "🐉 Consulting with the local dragons...",
            "🗡️ Sharpening virtual swords...",
            "🧙‍♂️ Brewing potions of creativity...",
            "📜 Consulting ancient scrolls...",
            "🎲 Rolling for initiative...",
            "🌟 Gathering magical energies...",
            "🏰 Exploring distant castles...",
            "⚔️ Preparing epic encounters...",
            "🎭 Writing the next chapter..."
        ]
        self.loading_frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self.loading_frame_idx = 0
        self.loading_label = None
        
        # Create GUI elements
        self.setup_gui()
        
        # Start the game
        self.start_game()
    
    def setup_gui(self):
        # Update colors for a more modern look
        BACKGROUND_COLOR = "#1A1A1A"  # Darker background
        TEXT_COLOR = "#E0E0E0"  # Softer white
        ACCENT_COLOR = "#7289DA"  # Discord-like blue
        GOLD_COLOR = "#FFD700"  # Brighter gold
        HEALTH_COLOR = "#43B581"  # Softer green
        BUTTON_BG = "#2F3136"  # Discord-like dark gray
        BUTTON_ACTIVE_BG = "#7289DA"  # Discord-like blue when active
        
        # Create main frame with padding
        main_frame = tk.Frame(self.root, bg=BACKGROUND_COLOR, padx=20, pady=20)
        main_frame.pack(expand=True, fill='both')
        
        # Title
        title_label = tk.Label(
            main_frame,
            text="Fantasy Adventure Quest",
            font=self.title_font,
            bg=BACKGROUND_COLOR,
            fg=TEXT_COLOR,
            pady=10
        )
        title_label.pack(fill='x')
        
        # Story display with custom styling
        self.story_text = scrolledtext.ScrolledText(
            main_frame,
            wrap=tk.WORD,
            width=70,
            height=20,
            font=self.text_font,
            bg='#2F3136',  # Darker background for text
            fg=TEXT_COLOR,
            insertbackground=TEXT_COLOR,
            relief=tk.FLAT,
            padx=15,
            pady=15
        )
        self.story_text.pack(expand=True, fill='both', pady=(0, 15))
        self.story_text.config(state='disabled')  # Make text read-only
        
        # Stats container frame
        stats_container = tk.Frame(main_frame, bg=BACKGROUND_COLOR)
        stats_container.pack(fill='x', pady=(0, 15))
        
        # Left side stats (Health and Gold)
        left_stats = tk.Frame(stats_container, bg=BACKGROUND_COLOR)
        left_stats.pack(side=tk.LEFT, fill='x', expand=True)
        
        # Health and Gold in a single row
        stats_row = tk.Frame(left_stats, bg=BACKGROUND_COLOR)
        stats_row.pack(fill='x')
        
        self.health_label = tk.Label(
            stats_row,
            text="❤️ Health: 100",
            font=self.stats_font,
            bg=BACKGROUND_COLOR,
            fg=HEALTH_COLOR,
            padx=10
        )
        self.health_label.pack(side=tk.LEFT)
        
        self.gold_label = tk.Label(
            stats_row,
            text="💰 Gold: 0",
            font=self.stats_font,
            bg=BACKGROUND_COLOR,
            fg=GOLD_COLOR,
            padx=10
        )
        self.gold_label.pack(side=tk.LEFT)
        
        # Right side stats (Inventory and Progress)
        right_stats = tk.Frame(stats_container, bg=BACKGROUND_COLOR)
        right_stats.pack(side=tk.RIGHT, fill='x')
        
        # Progress label
        self.progress_label = tk.Label(
            right_stats,
            text="Step: 0/5",
            font=self.stats_font,
            bg=BACKGROUND_COLOR,
            fg=TEXT_COLOR,
            padx=10
        )
        self.progress_label.pack(side=tk.RIGHT)
        
        # Inventory label and text
        inventory_frame = tk.Frame(right_stats, bg=BACKGROUND_COLOR)
        inventory_frame.pack(side=tk.RIGHT, fill='x', padx=10)
        
        inventory_label = tk.Label(
            inventory_frame,
            text="Inventory:",
            font=self.stats_font,
            bg=BACKGROUND_COLOR,
            fg=TEXT_COLOR
        )
        inventory_label.pack(side=tk.LEFT)
        
        self.inventory_text = tk.Text(
            inventory_frame,
            height=1,
            width=30,
            font=self.stats_font,
            bg=BACKGROUND_COLOR,
            fg=TEXT_COLOR,
            wrap=tk.WORD,
            relief=tk.FLAT,
            padx=5
        )
        self.inventory_text.pack(side=tk.LEFT, fill='x', expand=True)
        self.inventory_text.config(state='disabled')  # inventory read-only
        
        # Loading label
        self.loading_label = tk.Label(
            main_frame,
            text="",
            font=self.stats_font,
            bg=BACKGROUND_COLOR,
            fg=ACCENT_COLOR
        )
        self.loading_label.pack(pady=(0, 15))
        
        # Add restart button (initially hidden)
        self.restart_button = CustomButton(
            main_frame,
            text="Play Again",
            command=self.restart_game,
            state="disabled"
        )
        self.restart_button.pack(fill='x', pady=3)
        self.restart_button.pack_forget()  # Hide initially
        
        # Choices frame
        choices_frame = tk.Frame(main_frame, bg=BACKGROUND_COLOR)
        choices_frame.pack(fill='x', pady=(0, 10))
        
        self.choice_buttons = []
        for i in range(3):
            btn = CustomButton(
                choices_frame,
                text="",
                state="disabled",
                command=lambda x=i+1: self.on_choice_clicked(x)
            )
            btn.pack(fill='x', pady=3)
            self.choice_buttons.append(btn)
    
    def update_stats(self):
        self.health_label.config(text=f"❤️ Health: {self.game.player.health}")
        self.gold_label.config(text=f"💰 Gold: {self.game.player.gold}")
        
        # Update inventory with scrollable text
        self.inventory_text.config(state='normal')
        self.inventory_text.delete(1.0, tk.END)
        inventory_text = ", ".join(self.game.player.inventory) if self.game.player.inventory else "None"
        self.inventory_text.insert(tk.END, inventory_text)
        self.inventory_text.config(state='disabled')
        
        self.progress_label.config(text=f"Step: {self.game.player.step}/{self.game.MAX_STEPS}")
    
    def update_loading_animation(self):
        if self.loading:
            message = self.loading_messages[self.game.player.step % len(self.loading_messages)]
            frame = self.loading_frames[self.loading_frame_idx]
            self.loading_frame_idx = (self.loading_frame_idx + 1) % len(self.loading_frames)
            self.loading_label.config(text=f"{frame} {message}")
            self.root.after(100, self.update_loading_animation)
        else:
            self.loading_label.config(text="")

    def on_choice_clicked(self, choice_num):
        if self.loading:
            return
        self.loading = True
        self.set_choice_buttons_state("disabled")
        self.update_loading_animation()  # Start loading animation
        threading.Thread(target=self.process_choice, args=(choice_num,), daemon=True).start()
    
    def process_choice(self, choice_num):
        # Make a deep copy of the current scene to avoid threading issues
        scene_copy = copy.deepcopy(self.current_scene)
        self.current_scene = self.game.make_choice(choice_num, scene_copy)
        # Check for game over conditions (health or step count)
        if self.game.player.health <= 0:
            self.current_scene = self.game.end_game(game_over_message="You have perished in your quest!")
        # Update the display on the main thread
        self.root.after(0, self.update_game_display)
        self.loading = False

    def set_choice_buttons_state(self, state):
        for btn in self.choice_buttons:
            btn.config(state=state)
    
    def update_game_display(self):
        # Update story text with formatting
        self.story_text.config(state='normal')
        self.story_text.delete(1.0, tk.END)
        story_text = self.current_scene.get("story", "").strip()
        self.story_text.insert(tk.END, story_text)
        self.story_text.config(state='disabled')
        
        # Update stats
        self.update_stats()
        
        # Update choice buttons
        choices = self.current_scene.get("choices", [])
        for i, btn in enumerate(self.choice_buttons):
            if i < len(choices):
                btn.config(
                    text=choices[i],
                    state="normal"
                )
            else:
                btn.config(text="", state="disabled")
        
        # Show/hide buttons based on game state
        if not choices:  # Game is over
            for btn in self.choice_buttons:
                btn.pack_forget()
            self.restart_button.pack(fill='x', pady=3)
            self.restart_button.config(state="normal")

    def start_game(self):
        self.loading = True
        threading.Thread(target=self.initialize_game, daemon=True).start()
    
    def initialize_game(self):
        self.current_scene = self.game.initialize_story()
        self.root.after(0, self.update_game_display)
        self.loading = False

    def restart_game(self):
        # Reset player state
        self.game.player = PlayerState()
        self.game.conversation_history = []
        # Hide restart button and show choice buttons
        self.restart_button.pack_forget()
        for btn in self.choice_buttons:
            btn.pack(fill='x', pady=3)
        # Start new game
        self.start_game()

class AdventureGame:
    def __init__(self, gui):
        # Get API key from environment variable
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY environment variable not set")
        
        self.client = Groq(api_key=api_key)
        self.player = PlayerState()
        self.conversation_history = []
        self.MAX_STEPS = 5
        self.gui = gui
        # Predefine a system prompt (will be reused) and limit conversation history length.
        self.system_prompt = (
            "You are a dungeon master for a text-based adventure game. "
            "Generate an engaging fantasy story with choices that affect the player's stats (health, gold) and inventory. "
            "The game lasts exactly 5 steps. Each choice should be meaningful and interesting. "
            "Return your response strictly in JSON format with the following structure:\n"
            '{\n'
            '    "story": "current situation description",\n'
            '    "choices": ["choice 1", "choice 2", "choice 3"],\n'
            '    "effects": {\n'
            '        "1": {"health": modifier, "gold": modifier, "items": ["item1"]},\n'
            '        "2": {"health": modifier, "gold": modifier, "items": ["item2"]},\n'
            '        "3": {"health": modifier, "gold": modifier, "items": ["item3"]}\n'
            "    }\n"
            "}"
        )
    
    def add_to_history(self, role: str, content: str):
        self.conversation_history.append({"role": role, "content": content})
        # Keep only the last few messages (plus the system prompt) to reduce token usage.
        if len(self.conversation_history) > 10:
            # Assuming the system prompt is always at index 0.
            self.conversation_history = [self.conversation_history[0]] + self.conversation_history[-9:]
    
    def initialize_story(self):
        prompt = (
            f"{self.system_prompt}\n\n"
            f"Current player state: {self.player.to_dict()}"
        )
        self.add_to_history("system", prompt)
        self.add_to_history("user", "Start the adventure!")
        return self.get_next_scene()
    
    def get_next_scene(self) -> dict:
        # End the game if maximum steps have been reached
        if self.player.step >= self.MAX_STEPS:
            return self.end_game()
        
        try:
            response = self.client.chat.completions.create(
                messages=self.conversation_history,
                model="llama-3.1-8b-instant"
            )
            content = response.choices[0].message.content
            # Clean up any markdown formatting that might wrap the JSON
            content = content.replace('```json', '').replace('```', '').strip()
            # Extract only the JSON portion from the content
            content = extract_json(content)
            return self.process_scene(content)
        except Exception as e:
            print(f"Unexpected error: {e}")
            return self.end_game(game_over_message="An unexpected error occurred. The adventure ends here.")
    
    def make_choice(self, choice_num: int, scene: dict):
        # First check if we're already at max steps
        if self.player.step >= self.MAX_STEPS:
            return self.end_game(game_over_message=(
                "Your epic journey has reached its conclusion...\n\n"
                "As you reflect on your adventures, you realize how far you've come."
            ))
        
        try:
            # Add validation for required scene structure
            if not isinstance(scene, dict):
                print(f"Invalid scene format - expected dict, got: {type(scene)}")
                raise KeyError("Invalid scene format")
            
            if "effects" not in scene:
                print(f"Missing 'effects' in scene: {scene}")
                raise KeyError("Missing effects")
            
            if str(choice_num) not in scene["effects"]:
                print(f"Missing choice {choice_num} in effects: {scene['effects']}")
                raise KeyError(f"Missing choice {choice_num}")
            
            effects = scene["effects"][str(choice_num)]
            
        except KeyError as e:
            # Give more context in the error message
            return self.end_game(game_over_message=(
                "A mysterious force disrupts your adventure...\n\n"
                "The ancient scrolls seem to have become illegible, "
                "but your journey was still a memorable one!\n\n"
                f"Technical note: {str(e)}"
            ))
        
        # Update player state
        self.player.health += effects.get("health", 0)
        self.player.gold += effects.get("gold", 0)
        self.player.inventory.extend(effects.get("items", []))
        self.player.step += 1
        
        # Add the current scene and player's choice to the conversation history.
        self.add_to_history("assistant", json.dumps(scene))
        choice_text = scene["choices"][choice_num - 1]
        self.add_to_history("user", f"Choice made: {choice_text}\nNew player state: {self.player.to_dict()}")
        
        return self.get_next_scene()
    
    def end_game(self, game_over_message=None) -> dict:
        if game_over_message:  # For premature endings (death, errors)
            final_inventory = ', '.join(self.player.inventory) if self.player.inventory else "None"
            return {
                "story": (
                    f"{game_over_message}\n\n"
                    f"Final Stats:\n"
                    f"Health: {self.player.health}\n"
                    f"Gold: {self.player.gold}\n"
                    f"Inventory: {final_inventory}"
                ),
                "choices": [],
                "effects": {}
            }
        
        # For normal game completion, get ending from LLM
        try:
            response = self.client.chat.completions.create(
                messages=self.conversation_history,
                model="llama-3.1-8b-instant"
            )
            content = response.choices[0].message.content
            content = extract_json(content)
            return self.process_scene(content)  # Use the same retry logic for endings
        except Exception as e:
            print(f"Error generating ending: {e}")
            return {
                "story": (
                    "Your adventure comes to an end...\n\n"
                    f"Final Stats:\n"
                    f"Health: {self.player.health}\n"
                    f"Gold: {self.player.gold}\n"
                    f"Inventory: {', '.join(self.player.inventory) if self.player.inventory else 'None'}"
                ),
                "choices": [],
                "effects": {}
            }

    def process_scene(self, scene_text, retries=0):
        MAX_RETRIES = 3
        try:
            scene_data = json.loads(scene_text)
            return scene_data
        except json.JSONDecodeError:
            if retries < MAX_RETRIES:
                print("*The ancient scroll seems blurry, trying to decipher it again...*")
                # Retry the LLM call
                response = self.client.chat.completions.create(
                    messages=self.conversation_history,
                    model="llama-3.1-8b-instant"
                )
                new_content = response.choices[0].message.content.strip()
                new_content = extract_json(new_content)
                return self.process_scene(new_content, retries + 1)
            else:
                return {
                    "story": """
🤖 EMERGENCY STORY CONCLUSION PROTOCOL ACTIVATED! 🤖

Suddenly, a wild developer appears!
'Oh no! The story matrix has become corrupted!' they exclaim.
'But fear not, for your adventure was automatically backed up to the cloud!'

Your character went on to become a successful cloud storage salesperson, 
teaching other adventurers about the importance of data backup.

THE END (brought to you by Technical Difficulties™)

Final Stats:
Health: {self.player.health}
Gold: {self.player.gold}
Inventory: {', '.join(self.player.inventory) if self.player.inventory else 'None'}
                    """,
                    "choices": [],
                    "effects": {}
                }

def process_scene(scene_text, retries=0):
    MAX_RETRIES = 3
    try:
        scene_data = json.loads(scene_text)
        return scene_data
    except json.JSONDecodeError:
        if retries < MAX_RETRIES:
            print("*The ancient scroll seems blurry, trying to decipher it again...*")
            # Retry the LLM call
            new_response = get_next_scene()  # Make sure to import/define this function
            return process_scene(new_response, retries + 1)
        else:
            print("\n" + "*" * 50)
            print("EMERGENCY STORY CONCLUSION PROTOCOL ACTIVATED!")
            print("""
Suddenly, a wild developer appears!
'Oh no! The story matrix has become corrupted!' they exclaim.
'But fear not, for your adventure was automatically backed up to the cloud!'

Your character went on to become a successful cloud storage salesperson, 
teaching other adventurers about the importance of data backup.

THE END (brought to you by Technical Difficulties™)
            """)
            return {
                "description": "Emergency ending activated",
                "choices": [],
                "game_over": True
            }

def main():
    try:
        root = tk.Tk()
        app = AdventureGameGUI(root)
        root.mainloop()
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {e}")

if __name__ == "__main__":
    main()
