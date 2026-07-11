"""
UI Interface Module

Defines the abstract interface for user interfaces.
This allows different UI implementations (terminal, GUI, etc.) to work
with the same player backend.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from player.player_interface import PlayerInterface
from player.player_state import PlayerState


class UIInterface(ABC):
    """
    Abstract base class for user interfaces.
    
    This interface defines the contract between the UI and the application logic.
    Any UI implementation (terminal, GUI, web, etc.) must implement these methods.
    """
    
    @abstractmethod
    def run(self, player: PlayerInterface, start_file: Optional[Path] = None) -> None:
        """
        Run the main UI loop.
        
        Args:
            player: The player instance to control.
            start_file: Optional file to play immediately on start.
        """
        pass
    
    @abstractmethod
    def select_file(self, start_dir: Optional[str] = None) -> Optional[Path]:
        """
        Show a file selection dialog and return the selected file.
        
        Args:
            start_dir: Starting directory for file selection.
            
        Returns:
            Path to the selected audio file, or None if cancelled.
        """
        pass
    
    @abstractmethod
    def display_state(self, state: PlayerState) -> None:
        """
        Display the current player state.
        
        Args:
            state: The current player state to display.
        """
        pass
    
    @abstractmethod
    def show_error(self, message: str) -> None:
        """
        Display an error message to the user.
        
        Args:
            message: The error message to display.
        """
        pass
    
    @abstractmethod
    def show_message(self, message: str) -> None:
        """
        Display a general message to the user.
        
        Args:
            message: The message to display.
        """
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """
        Clean up any resources used by the UI.
        """
        pass
