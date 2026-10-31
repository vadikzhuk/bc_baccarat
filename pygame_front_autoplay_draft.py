import pygame
from class_player import Player
from game_backend import Game  # Import the game logic
from constants import SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, BLACK, RED, GREEN, FPS, DELAY

# Initialize Pygame
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Card Game")
clock = pygame.time.Clock()

# Load assets (Placeholder, replace with your actual image paths)
player_A_image = pygame.image.load("assets/player_A.png")  # Replace with actual path
player_B_image = pygame.image.load("assets/player_B.png")  # Replace with actual path
card_back_image = pygame.image.load("assets/cards/gray_back.png")  # For card backs


# Placeholder function for loading card images
def load_card_image(card):
    # Assume card is a string with the name of the card
    return pygame.image.load(f"assets/cards/{card}.png")  # Replace with your card image paths


# Function to draw the main game interface
def draw_interface(screen, player_A, player_B, attacker_card, defender_card, message):
    screen.fill(WHITE)

    # Draw players
    screen.blit(player_A_image, (50, 200))  # Position for player A's image
    screen.blit(player_B_image, (600, 200))  # Position for player B's image

    # Display player names
    font = pygame.font.Font(None, 36)
    player_A_name = font.render(f"{player_A['name']} (HP: {player_A['hp']})", True, BLACK)
    player_B_name = font.render(f"{player_B['name']} (HP: {player_B['hp']})", True, BLACK)
    screen.blit(player_A_name, (50, 150))
    screen.blit(player_B_name, (600, 150))

    # Draw cards if they exist
    if attacker_card:
        attacker_card_image = load_card_image(f"{attacker_card[0]}{attacker_card[1]}")
        screen.blit(attacker_card_image, (300, 400))  # Position for attacker's card

    if defender_card:
        defender_card_image = load_card_image(f"{defender_card[0]}{defender_card[1]}")
        screen.blit(defender_card_image, (400, 400))  # Position for defender's card

    # Display messages (like damage dealt)
    message_text = font.render(message, True, RED)
    screen.blit(message_text, (SCREEN_WIDTH // 2 - message_text.get_width() // 2, 50))

    pygame.display.flip()


def main():
    # Initialize the backend game
    game = Game(Player("Gandalf"), Player("Balrog"))
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Update game logic
        if not game.is_game_over():
            attacker, defender = game.get_current_turn()
            attacker_card, defender_card = game.draw_cards()

            # Perform attack
            damage = game.perform_attack(attacker, defender, attacker_card, defender_card)
            message = f"Damage = {damage}! {defender.name} has {defender.hp} HP left"

            draw_interface(
                screen,
                {"name": game.player_A.name, "hp": game.player_A.hp},
                {"name": game.player_B.name, "hp": game.player_B.hp},
                attacker_card,
                defender_card,
                message,
            )

            pygame.time.delay(DELAY * 1000)  # Convert seconds to milliseconds
            game.advance_turn()
        else:
            if game.get_winner():
                winner_message = f"{game.get_winner()} wins!"
            else:
                winner_message = "Game ended in a draw - ran out of cards!"

            draw_interface(
                screen,
                {"name": game.player_A.name, "hp": game.player_A.hp},
                {"name": game.player_B.name, "hp": game.player_B.hp},
                None,
                None,
                winner_message,
            )
            pygame.time.delay(3000)

            # Game is over; now wait for user to close the window
            wait_for_quit()
            break

        clock.tick(FPS)

    pygame.quit()

def wait_for_quit():
    """ Wait until the user closes the game window. """
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                waiting = False


if __name__ == "__main__":
    main()
