#!/usr/bin/env python3
"""
Icon Generator Module
Generates application icons with initials, customizable colors, and options
"""

from PIL import Image, ImageDraw, ImageFont
import os
import colorsys
import random


class IconGenerator:
    """Generate custom icons with app name initials"""
    
    DEFAULT_SIZE = 256
    DEFAULT_BG_COLOR = (66, 133, 244)  # Blue
    DEFAULT_TEXT_COLOR = (255, 255, 255)  # White
    
    # Preset color palettes for random generation
    COLOR_PALETTES = [
        {'bg': (66, 133, 244), 'text': (255, 255, 255)},      # Blue
        {'bg': (219, 68, 55), 'text': (255, 255, 255)},       # Red
        {'bg': (244, 81, 30), 'text': (255, 255, 255)},       # Orange
        {'bg': (251, 188, 5), 'text': (50, 50, 50)},          # Yellow
        {'bg': (52, 168, 83), 'text': (255, 255, 255)},       # Green
        {'bg': (156, 39, 176), 'text': (255, 255, 255)},      # Purple
        {'bg': (0, 150, 136), 'text': (255, 255, 255)},       # Teal
        {'bg': (63, 81, 181), 'text': (255, 255, 255)},       # Indigo
        {'bg': (233, 30, 99), 'text': (255, 255, 255)},       # Pink
        {'bg': (76, 175, 80), 'text': (255, 255, 255)},       # Light Green
    ]
    
    def __init__(self, size=DEFAULT_SIZE):
        """Initialize the icon generator"""
        self.size = size
    
    @staticmethod
    def get_initials(text):
        """Extract initials from text"""
        words = text.strip().split()
        if not words:
            return "?"
        
        if len(words) == 1:
            # Single word: use first two characters
            return words[0][:2].upper()
        else:
            # Multiple words: use first letter of first two words
            return (words[0][0] + words[1][0]).upper()
    
    @staticmethod
    def hex_to_rgb(hex_color):
        """Convert hex color to RGB tuple"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    @staticmethod
    def rgb_to_hex(rgb):
        """Convert RGB tuple to hex color"""
        return '#{:02x}{:02x}{:02x}'.format(rgb[0], rgb[1], rgb[2])
    
    @staticmethod
    def lighten_color(rgb, factor=0.2):
        """Lighten an RGB color"""
        h, s, v = colorsys.rgb_to_hsv(rgb[0]/255, rgb[1]/255, rgb[2]/255)
        v = min(1.0, v + factor)
        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        return (int(r*255), int(g*255), int(b*255))
    
    @staticmethod
    def darken_color(rgb, factor=0.2):
        """Darken an RGB color"""
        h, s, v = colorsys.rgb_to_hsv(rgb[0]/255, rgb[1]/255, rgb[2]/255)
        v = max(0, v - factor)
        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        return (int(r*255), int(g*255), int(b*255))
    
    def generate_icon(self, app_name, bg_color=None, text_color=None, bold=False, 
                     output_path=None, with_gradient=False):
        """
        Generate an icon with app initials
        
        Args:
            app_name: Application name (used to extract initials)
            bg_color: Background color as tuple (R, G, B) or hex string
            text_color: Text color as tuple (R, G, B) or hex string
            bold: Whether to use bold font
            output_path: Path to save the icon (optional)
            with_gradient: Add gradient effect to background
        
        Returns:
            PIL Image object or path if output_path specified
        """
        # Handle color inputs
        if bg_color is None:
            bg_color = self.DEFAULT_BG_COLOR
        elif isinstance(bg_color, str):
            bg_color = self.hex_to_rgb(bg_color)
        
        if text_color is None:
            text_color = self.DEFAULT_TEXT_COLOR
        elif isinstance(text_color, str):
            text_color = self.hex_to_rgb(text_color)
        
        # Create image with background
        img = Image.new('RGB', (self.size, self.size), bg_color)
        
        # Add gradient if requested
        if with_gradient:
            darker = self.darken_color(bg_color, 0.15)
            for y in range(self.size):
                ratio = y / self.size
                r = int(bg_color[0] * (1 - ratio) + darker[0] * ratio)
                g = int(bg_color[1] * (1 - ratio) + darker[1] * ratio)
                b = int(bg_color[2] * (1 - ratio) + darker[2] * ratio)
                for x in range(self.size):
                    img.putpixel((x, y), (r, g, b))
        
        draw = ImageDraw.Draw(img)
        
        # Get initials
        initials = self.get_initials(app_name)
        
        # Find font size and font
        font_size = int(self.size * 0.5)
        font_path = self._get_font_path(bold)
        
        # Load font with fallback
        try:
            font = ImageFont.truetype(font_path, font_size)
        except:
            font = ImageFont.load_default()
        
        # Calculate text position (center)
        bbox = draw.textbbox((0, 0), initials, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        x = (self.size - text_width) // 2
        y = (self.size - text_height) // 2
        
        # Draw text
        draw.text((x, y), initials, fill=text_color, font=font)
        
        # Add subtle border
        border_color = self.darken_color(bg_color, 0.1)
        draw.rectangle(
            [(0, 0), (self.size-1, self.size-1)],
            outline=border_color,
            width=2
        )
        
        # Save if path provided
        if output_path:
            img.save(output_path, 'PNG')
            return output_path
        
        return img
    
    @staticmethod
    def _get_font_path(bold=False):
        """Get system font path for rendering"""
        # Try common font locations
        font_names = []
        
        if bold:
            font_names = [
                '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
                '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf',
                '/System/Library/Fonts/Helvetica.ttc',
                'C:\\Windows\\Fonts\\arial.ttf',
            ]
        else:
            font_names = [
                '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
                '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
                '/System/Library/Fonts/Helvetica.ttc',
                'C:\\Windows\\Fonts\\arial.ttf',
            ]
        
        for font_path in font_names:
            if os.path.exists(font_path):
                return font_path
        
        # Return first option as fallback (will trigger exception handler in generate_icon)
        return font_names[0]
    
    def generate_icon_with_style(self, app_name, style='auto', output_path=None):
        """
        Generate icon with preset styles
        
        Args:
            app_name: Application name
            style: 'auto' for random, or 'palette_1' to 'palette_10' for specific styles
            output_path: Path to save the icon
        
        Returns:
            PIL Image object or path if output_path specified
        """
        if style == 'auto':
            palette = random.choice(self.COLOR_PALETTES)
        else:
            idx = int(style.split('_')[1]) - 1
            palette = self.COLOR_PALETTES[idx % len(self.COLOR_PALETTES)]
        
        return self.generate_icon(
            app_name,
            bg_color=palette['bg'],
            text_color=palette['text'],
            bold=False,
            output_path=output_path,
            with_gradient=True
        )
    
    @staticmethod
    def get_color_palettes():
        """Return available color palettes"""
        return IconGenerator.COLOR_PALETTES
    
    @staticmethod
    def get_icons_dir():
        """Get the directory where generated icons are stored"""
        icons_dir = os.path.join(
            os.path.expanduser("~"),
            ".local",
            "share",
            "icons",
            "python-launcher"
        )
        os.makedirs(icons_dir, exist_ok=True)
        return icons_dir
    
    @staticmethod
    def get_icon_path(app_name):
        """Get the full path for an app's icon"""
        safe_name = app_name.lower().replace(' ', '_').replace('-', '_')
        return os.path.join(
            IconGenerator.get_icons_dir(),
            f"{safe_name}.png"
        )
