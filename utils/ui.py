import pygame
from typing import List, Optional
from utils.constants import *
from utils import fonts

class Button:
    """Botón simple con texto cacheado y detección hover/click."""

    def __init__(self, x: int, y: int, width: int, height: int, text: str, font_size: int = FONT_SIZE):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = fonts.registry.get(font_size)
        self.is_hovered = False
        # Cache de superficie de texto (se vuelve a generar sólo si el texto cambia)
        self._text_surface = self.font.render(self.text, True, BLACK)

    def set_text(self, new_text: str) -> None:
        """Actualiza el texto del botón sólo si cambia para evitar re-render por frame."""
        if new_text != self.text:
            self.text = new_text
            self._text_surface = self.font.render(self.text, True, BLACK)

    def draw(self, screen: pygame.Surface) -> None:
        color = GRAY if self.is_hovered else BLACK
        pygame.draw.rect(screen, color, self.rect, 2)
        # Usar superficie cacheada
        if self._text_surface is None:
            self._text_surface = self.font.render(self.text, True, BLACK)
        text_rect = self._text_surface.get_rect(center=self.rect.center)
        screen.blit(self._text_surface, text_rect)

    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.is_hovered:
                return True
        return False

class ConfirmationDialog:
    """Diálogo modal simple Sí/No."""

    def __init__(self, screen: pygame.Surface, message: str):
        self.screen = screen
        self.message = message
        dialog_width = 400
        dialog_height = 200
        x = (SCREEN_WIDTH - dialog_width) // 2
        y = (SCREEN_HEIGHT - dialog_height) // 2
        self.rect = pygame.Rect(x, y, dialog_width, dialog_height)
        
        # Create Yes/No buttons
        btn_y = y + dialog_height - BUTTON_HEIGHT - 20
        self.yes_button = Button(x + 50, btn_y, 100, BUTTON_HEIGHT, "Sí", SMALL_FONT_SIZE)
        self.no_button = Button(x + dialog_width - 150, btn_y, 100, BUTTON_HEIGHT, "No", SMALL_FONT_SIZE)
        self.font = fonts.main_font()

    def draw(self) -> None:
        # Draw semi-transparent background
        s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        s.set_alpha(128)
        s.fill(BLACK)
        self.screen.blit(s, (0,0))
        
        # Draw dialog box
        pygame.draw.rect(self.screen, WHITE, self.rect)
        pygame.draw.rect(self.screen, BLACK, self.rect, 2)
        
        # Draw message
        text_surface = self.font.render(self.message, True, BLACK)
        text_rect = text_surface.get_rect(center=(self.rect.centerx, self.rect.y + 50))
        self.screen.blit(text_surface, text_rect)
        
        # Draw buttons
        self.yes_button.draw(self.screen)
        self.no_button.draw(self.screen)

    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        if self.yes_button.handle_event(event):
            return "yes"
        if self.no_button.handle_event(event):
            return "no"
        return None

class DropdownMenu:
    """Menú desplegable básico para selección entre varias opciones cortas."""

    def __init__(self, x: int, y: int, width: int, height: int, options: List[str], font_size: int = SMALL_FONT_SIZE):
        self.rect = pygame.Rect(x, y, width, height)
        self.options = options
        self.font = fonts.registry.get(font_size)
        self.is_open = False
        self.selected_option = options[0]
        self.option_rects = []
        self.update_option_rects()

    def update_option_rects(self) -> None:
        self.option_rects = []
        for i, _ in enumerate(self.options):
            if self.is_open:
                self.option_rects.append(
                    pygame.Rect(
                        self.rect.x,
                        self.rect.y + (i + 1) * self.rect.height,
                        self.rect.width,
                        self.rect.height
                    )
                )

    def draw(self, screen: pygame.Surface) -> None:
        # Draw main button
        pygame.draw.rect(screen, WHITE, self.rect)
        pygame.draw.rect(screen, BLACK, self.rect, 2)
        text_surface = self.font.render(self.selected_option, True, BLACK)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

        # Draw dropdown options if open
        if self.is_open:
            for i, (option, option_rect) in enumerate(zip(self.options, self.option_rects)):
                pygame.draw.rect(screen, WHITE, option_rect)
                pygame.draw.rect(screen, BLACK, option_rect, 2)
                text_surface = self.font.render(option, True, BLACK)
                text_rect = text_surface.get_rect(center=option_rect.center)
                screen.blit(text_surface, text_rect)

    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        # Ignorar completamente scroll (ruedita) en cualquier parte
        if event.type == pygame.MOUSEBUTTONDOWN and getattr(event, 'button', 1) in (4, 5):
            return None
        if event.type == pygame.MOUSEBUTTONDOWN:
            if getattr(event, 'button', 1) not in (1, 2, 3):
                return None
            if self.rect.collidepoint(event.pos):
                if not self.is_open:
                    self.is_open = True
                    self.update_option_rects()
            if self.is_open:
                for i, option_rect in enumerate(self.option_rects):
                    if option_rect.collidepoint(event.pos):
                        self.selected_option = self.options[i]
                        self.is_open = False
                        self.update_option_rects()
                        return self.selected_option
        return None
