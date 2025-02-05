# Fantasy Adventure Quest 🗡️

A dynamic text-based adventure game powered by the Groq LLM API with a modern graphical interface. Each playthrough generates a unique story where your choices matter, affecting your health, wealth, and inventory.


## 🎮 Features

- **Dynamic Storytelling**: Each game session creates a unique adventure using the Groq LLM API
- **Interactive Choices**: Make meaningful decisions that affect your character's journey
- **Real-time Stats Tracking**: Monitor your health, gold, and inventory
- **Modern GUI**: Clean, fantasy-themed interface with custom styling
- **Progress System**: 10-step adventure with varying outcomes

## 🚀 Getting Started

### Prerequisites

- Python 3.7+
- Groq API key
- Required packages:
  ```bash
  pip install groq python-dotenv
  ```

### Installation

1. Clone the repository:
```bash
git clone https://github.com/elisha-rudenkov/fantasy-adventure-quest.git
cd fantasy-adventure-quest
```

2. Create a `.env` file in the project root and add your Groq API key:
```
GROQ_API_KEY=your_api_key_here
```

3. Run the game:
```bash
python game.py
```

## 🎯 How to Play

1. Launch the game using the instructions above
2. Read the story text in the main window
3. Choose from up to three options for each decision
4. Monitor your stats:
   - ❤️ Health: Your character's current health points
   - 💰 Gold: Accumulated wealth
   - 🎒 Inventory: Items collected during your journey

Each choice affects your character's stats and inventory, potentially leading to different story outcomes.

## 🛠️ Technical Details

- Built with Python and Tkinter for the GUI
- Utilizes the Groq API for dynamic story generation
- Custom theming and styling for an immersive experience
- Object-oriented design with separate game logic and UI components


## 🙏 Acknowledgments

- Powered by [Groq](https://groq.com/) for story generation
- Built with [Python](https://python.org/) and Tkinter
- Inspired by classic text adventure games

