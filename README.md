# minesweeper
Project Title: Minesweeper
Project Members: Michael J. | Sharad L. | Sara C.

HOW TO RUN:
*add this once main.java is built*

Project Purpose:
To build a themed version of a Minesweeper game. The game will be playable through a graphical interface (GUI). The game provides players with a grid of tiles (a “minefield”), and the goal is to safely clear the minefield without setting off a mine. This is done by clicking on a tile. If that tile contains a mine (randomly placed throughout the tile space on game initialization), they lose. If that space does not contain a mine, all adjacent spaces without a mine are cleared.
Numerical clues are then provided to the player to indicate where a mine is located. A number indicates to the player how many mines are touching that tile (including diagonals). The player can flag potential mines without detonating them. 
The theme will be decided by the group. Depending on the difficulty and time required, we may add additional game mechanics such as difficulty adjustment (field size, number of mines, etc.) or other things that we will discuss later.

Project problems it solves:
This game is a logic puzzle that requires spatial reasoning and deduction. From a technical standpoint, it will require managing dynamic grid states, recursively uncovering empty areas, and tracking real-time user actions (flagging, revealing, timing) in a structured game loop.

OOP Concepts/Data Structures:
The data structure we’ll likely use is a 2D array grid to represent the game board. This will allow for intuitive coordinate-based access (Cell[][]). When revealing empty areas, we can use queues/ stacks to recursively search through adjacent empty tiles and reveal them automatically. We can also use an ArrayList to maintain a log of moves, high scores, and to shuffle mine placement. For OOP concepts, we’ll likely use Inheritance and Polymorphism if we get to the different difficulties and game modes to override board settings based on different inputs (easy, medium, hard, etc.) Inheritance could also be used to help with this. Abstraction will be used to hide the game loop, win/loss conditions, and other complexities not required for the game experience. Encapsulation can be used to hide internal states of the board condition by controlling certain user input methods like revealing or flagging and all the conditions that go into that.
