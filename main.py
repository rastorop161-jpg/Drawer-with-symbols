import json
import os
import random
from typing import Dict, List, Optional, Tuple

class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_MAGENTA = '\033[95m'
    BRIGHT_CYAN = '\033[96m'
    BRIGHT_WHITE = '\033[97m'
    
    ORANGE = '\033[38;5;208m'
    PINK = '\033[38;5;205m'
    LIME = '\033[38;5;154m'
    GOLD = '\033[38;5;220m'
    PURPLE = '\033[38;5;141m'
    TEAL = '\033[38;5;51m'
    
    @classmethod
    def get_color(cls, name: str):
        colors = {
            'bright_red': cls.BRIGHT_RED,
            'bright_green': cls.BRIGHT_GREEN,
            'bright_yellow': cls.BRIGHT_YELLOW,
            'bright_blue': cls.BRIGHT_BLUE,
            'bright_magenta': cls.BRIGHT_MAGENTA,
            'bright_cyan': cls.BRIGHT_CYAN,
            'bright_white': cls.BRIGHT_WHITE,
            'orange': cls.ORANGE,
            'pink': cls.PINK,
            'lime': cls.LIME,
            'gold': cls.GOLD,
            'purple': cls.PURPLE,
            'teal': cls.TEAL,
        }
        return colors.get(name.lower(), cls.BRIGHT_WHITE)
    
    @classmethod
    def get_random_color(cls, include_256=True):
        colors = [
            'bright_red', 'bright_green', 'bright_yellow', 
            'bright_blue', 'bright_magenta', 'bright_cyan',
            'bright_white', 
            'orange', 'pink', 'lime', 'gold', 'purple', 'teal'
        ]
        return random.choice(colors)


class AsciiTextRenderer:
    "Отрисовка из JSON-символов"
    
    def __init__(self, bg=' ', fg='#', width=20, height=40):
        self.bg = bg
        self.fg = fg
        self.width = width
        self.height = height
        self.symbols: Dict[str, List[str]] = {}
        self.loaded_files: List[str] = []
    
    def load_symbol_from_json(self, json_file: str) -> Optional[str]:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            symbol = data['symbol']
            cells = data['cells']
            
            actual_height = len(cells)
            actual_width = len(cells[0]) if cells else 0
            
            if actual_height != self.height or actual_width != self.width:
                height = actual_height
                width = actual_width
            else:
                height = self.height
                width = self.width
            
            pattern = []
            for row in cells:
                row_str = ''.join(self.fg if cell == 1 else self.bg for cell in row)
                if len(row_str) < width:
                    row_str = row_str + self.bg * (width - len(row_str))
                elif len(row_str) > width:
                    row_str = row_str[:width]
                pattern.append(row_str)
            
            if len(pattern) < height:
                pattern.extend([self.bg * width] * (height - len(pattern)))
            elif len(pattern) > height:
                pattern = pattern[:height]
            
            self.symbols[symbol] = pattern
            self.loaded_files.append(json_file)
            return symbol
            
        except Exception as e:
            print(f"Ошибка загрузки {json_file}: {e}")
            return None
    
    def load_symbols_from_folder(self, folder_path: str) -> List[str]:
        loaded = []       
        json_files = [f for f in os.listdir(folder_path) if f.endswith('.json')]
        
        for file in json_files:
            symbol = self.load_symbol_from_json(os.path.join(folder_path, file))
            if symbol:
                loaded.append(symbol)
        
        return loaded
    
    def draw_text(self, text: str, spacing: int = 1, 
                  show_missing: bool = False) -> List[str]:
        if not text:
            return []
        
        patterns = []
        missing_chars = []
        
        for char in text:
            if char == ' ':
                patterns.append([self.bg * self.width] * self.height)
            elif char.upper() in self.symbols:
                patterns.append(self.symbols[char.upper()])
            elif char.lower() in self.symbols:
                patterns.append(self.symbols[char.lower()])
            else:
                if show_missing and char not in [' ', '\n', '\t']:
                    missing_chars.append(char)
                patterns.append([self.bg * self.width] * self.height)
        
        if missing_chars:
            print(f"Символы не найдены: {', '.join(missing_chars)}")
        
        if not patterns:
            return []
        
        result = []
        for y in range(self.height):
            row = []
            for i, pattern in enumerate(patterns):
                row.append(pattern[y] if y < len(pattern) else self.bg * self.width)
                if i < len(patterns) - 1:
                    row.append(' ' * spacing)
            result.append(''.join(row))
        
        return result

class RandomAsciiRenderer(AsciiTextRenderer):
    
    SYMBOLS = '!@#$%^&*+№?='
    
    def __init__(self, bg=' ', fg='#', width=20, height=40,
                 symbols: str = None, random_colors: bool = True,
                 random_symbols: bool = True, use_256_colors: bool = True,
                 always_bold: bool = True):
        """
        :param symbols: набор символов для случайной замены
        :param random_colors: использовать ли случайные цвета
        :param random_symbols: использовать ли случайные символы
        :param use_256_colors: использовать ли 256-цветные (оранжевый, розовый и т.д.)
        :param always_bold: всегда ли использовать жирный шрифт
        """
        super().__init__(bg, fg, width, height)
        self.symbols_set = symbols or self.SYMBOLS
        self.random_colors = random_colors
        self.random_symbols = random_symbols
        self.use_256_colors = use_256_colors
        self.always_bold = always_bold
        
        # Кэш для хранения сгенерированных символов и цветов
        self.char_cache: Dict[Tuple[int, int], Tuple[str, str]] = {}
    
    def _get_random_char(self) -> str:
        return random.choice(self.symbols_set)
    
    def _get_random_color(self) -> str:
        return Colors.get_random_color(include_256=self.use_256_colors)
    
    def _process_cell(self, char: str, x: int, y: int) -> Tuple[str, str]:

        # Обрабатывает одну ячейку: определяет символ и цвет

        if char == self.bg:
            return (char, None)
        
        cache_key = (x, y)
        if cache_key in self.char_cache:
            cached_char, cached_color = self.char_cache[cache_key]
            return (cached_char, cached_color)
        
        new_char = self._get_random_char() if self.random_symbols else char
        color = self._get_random_color() if self.random_colors else None
        
        self.char_cache[cache_key] = (new_char, color)
        
        return (new_char, color)
    
    def _process_line(self, line: str, y: int) -> List[Tuple[str, str]]:
        result = []
        for x, char in enumerate(line):
            new_char, color = self._process_cell(char, x, y)
            result.append((new_char, color))
        return result
    
    def _colorize_line(self, processed_line: List[Tuple[str, str]]) -> str:
        result = []
        for char, color in processed_line:
            if char == self.bg or color is None:
                result.append(char)
            else:
                color_code = Colors.get_color(color)
                if self.always_bold:
                    result.append(f"{Colors.BOLD}{color_code}{char}{Colors.RESET}")
                else:
                    result.append(f"{color_code}{char}{Colors.RESET}")
        return ''.join(result)
    
    def print_text(self, text: str, spacing: int = 1, 
                   show_missing: bool = True, colored: bool = True) -> None:
        self.clear_cache()
        
        result = self.draw_text(text, spacing, show_missing)
        if not result:
            return
        
        for y, line in enumerate(result):
            processed = self._process_line(line, y)
            if colored:
                print(self._colorize_line(processed))
            else:
                print(''.join(char for char, _ in processed))
    
    def save_text_to_file(self, text: str, filename: str, spacing: int = 1,
                         colored: bool = False) -> None:
        self.clear_cache()
        result = self.draw_text(text, spacing)
        if not result:
            return
        
        with open(filename, 'w', encoding='utf-8') as f:
            if colored:
                for y, line in enumerate(result):
                    processed = self._process_line(line, y)
                    f.write(self._colorize_line(processed) + '\n')
            else:
                for y, line in enumerate(result):
                    processed = self._process_line(line, y)
                    f.write(''.join(char for char, _ in processed) + '\n')
        
        print(f"Результат сохранён в {filename}")

def main():
    
    while True:

        renderer = RandomAsciiRenderer(
                bg=' ',
                fg='#',
                width=20,
                height=40,
                symbols='!@#$%^&*+№?=',
                random_colors=True,
                random_symbols=True,
                use_256_colors=True,
                always_bold=True
            )
        renderer.load_symbols_from_folder('.')
        text = 'mail'
        if text:
            renderer.print_text(text.upper(), spacing=1, colored=True)
            break
        
        else:
            print("Ошибка ввода")


if __name__ == "__main__":
    if os.name == 'nt':
        os.system('color')
    
    main()