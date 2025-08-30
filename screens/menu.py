import pygame
from utils.constants import *
from utils.ui import Button, ConfirmationDialog, DropdownMenu
from utils.i18n import tr, set_ui_language, current_language

class MenuScreen:
    def __init__(self, game):
        self.game = game
        self.screen = game.screen
        # Calculate initial (reference) button positions (will be recalculated on draw for responsiveness)
        center_x = SCREEN_WIDTH // 2 - BUTTON_WIDTH // 2
        start_y = SCREEN_HEIGHT // 2 - (BUTTON_HEIGHT * 2 + BUTTON_SPACING * 1.5)

        # Create buttons
        self.play_button = Button(center_x, start_y, BUTTON_WIDTH, BUTTON_HEIGHT, tr('menu.play'))
        self.settings_button = Button(center_x, start_y + BUTTON_HEIGHT + BUTTON_SPACING,
                                      BUTTON_WIDTH, BUTTON_HEIGHT, tr('menu.settings'))
        self.language_button = Button(center_x, start_y + (BUTTON_HEIGHT + BUTTON_SPACING) * 2,
                                      BUTTON_WIDTH, BUTTON_HEIGHT, tr('menu.language'))
        self.exit_button = Button(center_x, start_y + (BUTTON_HEIGHT + BUTTON_SPACING) * 3,
                                  BUTTON_WIDTH, BUTTON_HEIGHT, tr('menu.exit'))

        # Create language dropdown
        self._lang_label_to_code = {
            'Español (Uruguay)': 'ES',
            'English': 'EN',
            'Português': 'PT',
            'Deutsch': 'DE',
            'Italiano': 'IT'
        }
        self._code_to_lang_label = {v: k for k, v in self._lang_label_to_code.items()}
        self.language_dropdown = DropdownMenu(center_x, start_y + (BUTTON_HEIGHT + BUTTON_SPACING) * 2,
                                              BUTTON_WIDTH, BUTTON_HEIGHT, list(self._lang_label_to_code.keys()))
        cur_code = current_language()
        if cur_code in self._code_to_lang_label:
            self.language_dropdown.selected_option = self._code_to_lang_label[cur_code]
        self.show_language_dropdown = False
        self.confirmation_dialog = None

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.game.quit()
                
            # Ignorar scroll globalmente en el menú
            if event.type == pygame.MOUSEBUTTONDOWN and getattr(event, 'button', 1) in (4, 5):
                continue
                
            # ESC para volver atrás
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                if self.confirmation_dialog:
                    self.confirmation_dialog = None
                elif self.show_language_dropdown:
                    self.show_language_dropdown = False
                else:
                    self.game.change_screen("menu")
                continue
                
            if self.confirmation_dialog:
                result = self.confirmation_dialog.handle_event(event)
                if result == "yes":
                    self.game.quit()
                elif result == "no":
                    self.confirmation_dialog = None
                continue
                
            if self.show_language_dropdown:
                selected = self.language_dropdown.handle_event(event)
                if selected:
                    # Change language
                    lang_code = self._lang_label_to_code.get(selected, 'ES')
                    set_ui_language(lang_code)
                    # Rebuild button texts with new language
                    self.play_button.text = tr('menu.play')
                    self.settings_button.text = tr('menu.settings')
                    self.language_button.text = tr('menu.language')
                    self.exit_button.text = tr('menu.exit')
                    self.show_language_dropdown = False
                    continue
                # Cerrar si se hace click fuera del dropdown
                if event.type == pygame.MOUSEBUTTONDOWN and not self.language_dropdown.rect.collidepoint(event.pos):
                    self.show_language_dropdown = False
                    continue

            if self.play_button.handle_event(event):
                self.game.change_screen("game")
            elif self.settings_button.handle_event(event):
                self.game.change_screen("settings")
            elif self.language_button.handle_event(event):
                self.show_language_dropdown = True
                # Simular el clic sobre el dropdown para que se abra de inmediato
                fake_event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'pos': self.language_dropdown.rect.center, 'button': 1})
                self.language_dropdown.handle_event(fake_event)
            elif self.exit_button.handle_event(event):
                self.confirmation_dialog = ConfirmationDialog(self.screen, tr('confirm.exit'))

    def update(self):
        pass

    def draw(self):
        width = self.screen.get_width()
        height = self.screen.get_height()
        self.screen.fill(WHITE)

        # Calcular posiciones relativas
        button_width = int(width * 0.25)
        button_height = int(height * 0.08)
        spacing = int(height * 0.04)
        center_x = (width - button_width) // 2
        start_y = height // 2 - (button_height * 2 + spacing * 1.5)

        # Actualizar posiciones de los botones
        self.play_button.rect = pygame.Rect(center_x, start_y, button_width, button_height)
        self.settings_button.rect = pygame.Rect(center_x, start_y + button_height + spacing, button_width, button_height)
        self.language_button.rect = pygame.Rect(center_x, start_y + (button_height + spacing) * 2, button_width, button_height)
        self.exit_button.rect = pygame.Rect(center_x, start_y + (button_height + spacing) * 3, button_width, button_height)
        self.language_dropdown.rect = pygame.Rect(center_x, start_y + (button_height + spacing) * 2, button_width, button_height)
        self.language_dropdown.update_option_rects()

        # Draw buttons
        self.play_button.draw(self.screen)
        self.settings_button.draw(self.screen)
        if not self.show_language_dropdown:
            self.language_button.draw(self.screen)
        self.exit_button.draw(self.screen)

        # Draw language dropdown if active
        if self.show_language_dropdown:
            self.language_dropdown.draw(self.screen)

        # Draw confirmation dialog if active
        if self.confirmation_dialog:
            self.confirmation_dialog.draw()
