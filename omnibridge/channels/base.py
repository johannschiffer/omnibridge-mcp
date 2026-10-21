"""
Base channel interface for OmniBridge notification providers.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseChannel(ABC):
    @property
    @abstractmethod
    def channel_name(self) -> str:
        """Unique identifier for channel."""
        pass

    @abstractmethod
    def is_configured(self) -> bool:
        """Checks if required credentials/endpoints are set."""
        pass

    @abstractmethod
    def send(self, **kwargs) -> Dict[str, Any]:
        """Synchronously or asynchronously dispatches notification."""
        pass
