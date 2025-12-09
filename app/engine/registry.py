from typing import Any, Callable, Dict, Optional


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: Dict[str, Callable[[Dict[str, Any]], Any]] = {}

    def register(self, name: str):
        def decorator(func: Callable[[Dict[str, Any]], Any]) -> Callable:
            self._tools[name] = func
            return func
        return decorator

    def add(self, name: str, func: Callable[[Dict[str, Any]], Any]) -> None:
        self._tools[name] = func

    def get(self, name: str) -> Optional[Callable[[Dict[str, Any]], Any]]:
        return self._tools.get(name)

    def list_tools(self) -> Dict[str, str]:
        return {name: (func.__doc__ or "") for name, func in self._tools.items()}
