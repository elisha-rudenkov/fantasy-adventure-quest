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
            background=BUTTON_BG,
            foreground=TEXT_COLOR,
            activebackground=BUTTON_ACTIVE_BG,
            activeforeground=TEXT_COLOR,
            relief=tk.RAISED,
            borderwidth=2,
            padx=20,
            pady=10,
            font=('Helvetica', 10, 'bold')
        )
        self.bind('<Enter>', self.on_enter)
        self.bind('<Leave>', self.on_leave)

    def on_enter(self, e):
        if self['state'] != 'disabled':
            self['background'] = BUTTON_ACTIVE_BG

    def on_leave(self, e):
        if self['state'] != 'disabled':
            self['background'] = BUTTON_BG

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
        
        # Create GUI elements
        self.setup_gui()
        
        # Start the game
        self.start_game()
    
    def setup_gui(self):
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
            bg='#34495E',
            fg=TEXT_COLOR,
            insertbackground=TEXT_COLOR,
            relief=tk.SUNKEN,
            padx=10,
            pady=10
        )
        self.story_text.pack(expand=True, fill='both', pady=(0, 10))
        
        # Player stats frame with custom styling
        stats_frame = tk.Frame(main_frame, bg=BACKGROUND_COLOR, relief=tk.RIDGE, bd=2)
        stats_frame.pack(fill='x', pady=(0, 10))
        
        # Health bar
        health_frame = tk.Frame(stats_frame, bg=BACKGROUND_COLOR)
        health_frame.pack(side=tk.LEFT, expand=True, padx=5, pady=5)
        
        self.health_label = tk.Label(
            health_frame,
            text="❤️ Health: ",
            font=self.stats_font,
            bg=BACKGROUND_COLOR,
            fg=HEALTH_COLOR
        )
        self.health_label.pack(side=tk.LEFT)
        
        # Gold counter
        gold_frame = tk.Frame(stats_frame, bg=BACKGROUND_COLOR)
        gold_frame.pack(side=tk.LEFT, expand=True, padx=5, pady=5)
        
        self.gold_label = tk.Label(
            gold_frame,
            text="💰 Gold: ",
            font=self.stats_font,
            bg=BACKGROUND_COLOR,
            fg=GOLD_COLOR
        )
        self.gold_label.pack(side=tk.LEFT)
        
        # Inventory
        inventory_frame = tk.Frame(stats_frame, bg=BACKGROUND_COLOR)
        inventory_frame.pack(side=tk.LEFT, expand=True, padx=5, pady=5)
        
        self.inventory_label = tk.Label(
            inventory_frame,
            text="🎒 Inventory: ",
            font=self.stats_font,
            bg=BACKGROUND_COLOR,
            fg=TEXT_COLOR
        )
        self.inventory_label.pack(side=tk.LEFT)
        
        # Progress indicator
        self.progress_label = tk.Label(
            stats_frame,
            text="Step: 0/10",
            font=self.stats_font,
            bg=BACKGROUND_COLOR,
            fg=TEXT_COLOR
        )
        self.progress_label.pack(side=tk.RIGHT, padx=5)
        
        # Choices frame
        choices_frame = tk.Frame(main_frame, bg=BACKGROUND_COLOR)
        choices_frame.pack(fill='x', pady=10)
        
        self.choice_buttons = []
        for i in range(3):
            btn = CustomButton(
                choices_frame,
                text="",
                state="disabled",
                command=lambda x=i+1: self.on_choice_clicked(x)
            )
            btn.pack(fill='x', pady=5)
            self.choice_buttons.append(btn)
    
    def update_stats(self):
        self.health_label.config(text=f"❤️ Health: {self.game.player.health}")
        self.gold_label.config(text=f"💰 Gold: {self.game.player.gold}")
        inventory_text = ", ".join(self.game.player.inventory) if self.game.player.inventory else "None"
        self.inventory_label.config(text=f"🎒 Inventory: {inventory_text}")
        self.progress_label.config(text=f"Step: {self.game.player.step}/{self.game.MAX_STEPS}")
    
    def on_choice_clicked(self, choice_num):
        if self.loading:
            return  # Prevent multiple simultaneous LLM calls
        self.loading = True
        # Disable buttons to avoid re-clicking while processing
        self.set_choice_buttons_state("disabled")
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
        self.story_text.delete(1.0, tk.END)
        story_text = self.current_scene.get("story", "").strip()
        self.story_text.insert(tk.END, story_text)
        
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
    
    def start_game(self):
        self.loading = True
        threading.Thread(target=self.initialize_game, daemon=True).start()
    
    def initialize_game(self):
        self.current_scene = self.game.initialize_story()
        self.root.after(0, self.update_game_display)
        self.loading = False

class AdventureGame:
    def __init__(self, gui):
        # Get API key from environment variable
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY environment variable not set")
        
        self.client = Groq(api_key=api_key)
        self.player = PlayerState()
        self.conversation_history = []
        self.MAX_STEPS = 10
        self.gui = gui
        # Predefine a system prompt (will be reused) and limit conversation history length.
        self.system_prompt = (
            "You are a dungeon master for a text-based adventure game. "
            "Generate an engaging fantasy story with choices that affect the player's stats (health, gold) and inventory. "
            "The game lasts exactly 10 steps. Each choice should be meaningful and interesting. "
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
            return self.end_game(game_over_message="Your adventure has ended!")
            
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
            scene = json.loads(content)
            return scene
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
            return self.end_game(game_over_message="Error processing the scene. The adventure ends here.")
        except Exception as e:
            print(f"Unexpected error: {e}")
            return self.end_game(game_over_message="An unexpected error occurred. The adventure ends here.")
    
    def make_choice(self, choice_num: int, scene: dict):
        try:
            effects = scene["effects"][str(choice_num)]
        except KeyError:
            # If the expected key is missing, treat it as a fatal error.
            return self.end_game(game_over_message="Malformed scene response. The adventure ends here.")
        
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
    
    def end_game(self, game_over_message="Your adventure has ended!") -> dict:
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

def main():
    try:
        root = tk.Tk()
        app = AdventureGameGUI(root)
        root.mainloop()
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {e}")

if __name__ == "__main__":
    main()
