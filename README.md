<a id="readme-top"></a>

[![Contributors][contributors-shield]][contributors-url]
[![Stargazers][stars-shield]][stars-url]


<div align="center">

# Air Hockey

  <p align="center">
    A real-time multiplayer game built using Python and Pygame.
    <br />
    <a href="https://youtu.be/eO7842qc25w">View Demo</a>
  </p>
</div>

<!-- ABOUT THE PROJECT -->
## About The Project
We built a real-time, multiplayer version of the tabletop classic - Air Hockey - from the ground-up in Python using Pygame. It utilizes a client-server model where one machine hosts the game server, while multiple clients connect to join and interact in the same game. The game features realistic physics, collision detection, and interactive mechanics that allow players to control paddles, hit a puck, and score goals.


## Game Features:

- Any player can grab any paddle.
  - When a player joins, a new paddle is created and added to the game.
- While a paddle is grabbed by a player, no other player can grab it until it’s released.
- When two paddles collide, both are released.
- Each new paddle added (when a new client joins) cycles between blue, red, pink, and yellow colors.


<!-- GETTING STARTED -->
## Getting Started

To get a local copy up and running follow these simple steps:

### Installation

1. Clone the repo
   ```sh
   git clone https://github.com/saaranganand/project-371.git
   ```
2. Navigate to the repo
   ```sh
   cd project-371
   ```
3. Install prerequisite packages
   ```sh
   pip install -r requirements.txt
   ```

### Usage

1. Run the client
   ```sh
   python client/client.py
   ```
2. Enter your name

3. Select _'Start Match'_

4. Other clients (on the same LAN) run the client & select _'Join A Server'_

5. Enter the first player's IP + Port to join their match

6. <p>Hit <kbd> Esc </kbd> at any point during the game to open the pause menu, which allows you to return to the main menu. </p>

---

### The Team:

<a href="https://github.com/saaranganand/project-371/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=saaranganand/project-371" alt="contrib.rocks image" />
</a>

* [James Chuong](https://github.com/JamesChuong)
* [Johnny Deng](https://github.com/JohnnyDeng6/)
* [Saarang Anand](https://github.com/saaranganand/)
* [Simon Purdon](https://github.com/SimonGCP/)
  
---

_CMPT 371 - Group 04_\
_Simon Fraser University - Spring 2025_



<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
[contributors-shield]: https://img.shields.io/github/contributors/saaranganand/project-371.svg?style=for-the-badge
[contributors-url]: https://github.com/saaranganand/project-371/graphs/contributors
[stars-shield]: https://img.shields.io/github/stars/saaranganand/project-371.svg?style=for-the-badge
[stars-url]: https://github.com/saaranganand/project-371/stargazers
