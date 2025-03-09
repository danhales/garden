"""
Theme management for Pathfinder with enhanced accessibility options
"""

import re
import json
import base64
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any

# Initialize logging
logger = logging.getLogger('pathfinder.themes')

class ThemeManager:
    """
    Manages visual themes in Pathfinder with enhanced accessibility options
    """
    def __init__(self, themes_dir=None):
        """Initialize the theme manager"""
        self.themes_dir = themes_dir or Path.home() / '.pathfinder' / 'themes'
        
        # Ensure the themes directory exists
        if not isinstance(self.themes_dir, Path):
            self.themes_dir = Path(self.themes_dir)
        self.themes_dir.mkdir(parents=True, exist_ok=True)
        
        self.current_theme = None
        self.themes = {}
        self.default_theme = self._create_default_theme()
        
        # Create additional built-in themes
        self.low_contrast_theme = self._create_low_contrast_theme()
        self.focus_theme = self._create_focus_theme()
        
        # Load any existing themes
        self._load_themes()
        
        # Set default theme as current if none loaded
        if not self.current_theme:
            self.current_theme = "default"
    
    def _create_default_theme(self) -> Dict:
        """Create the default theme with accessibility features"""
        default_css = """
        :root {
            /* Main colors */
            --primary-color: #4a6fa5;
            --secondary-color: #6b96c9;
            --accent-color: #ffa500;
            --background-color: #f5f7fa;
            --text-color: #333333;
            
            /* Node colors - ensuring sufficient contrast */
            --node-default-color: #2b68b8;
            --node-focus-color: #d86000;
            --node-highlight-color: #cc3300;
            
            /* Context colors */
            --context-active-color: #2e8534;
            --context-inactive-color: #6b6b6b;
            
            /* Path colors */
            --path-line-color: #4a6fa5;
            --path-node-color: #d86000;
            
            /* Text sizes */
            --text-size-small: 0.85rem;
            --text-size-normal: 1rem;
            --text-size-large: 1.25rem;
            --text-size-xlarge: 1.5rem;
            
            /* Spacing */
            --spacing-xs: 0.25rem;
            --spacing-sm: 0.5rem;
            --spacing-md: 1rem;
            --spacing-lg: 1.5rem;
            --spacing-xl: 2rem;
            
            /* Animation - reduced for accessibility */
            --transition-speed: 0.2s;
            
            /* Opacity */
            --inactive-opacity: 0.8;
            
            /* Border radius */
            --border-radius-sm: 4px;
            --border-radius-md: 8px;
            --border-radius-lg: 12px;
            
            /* Shadow */
            --shadow-light: 0 2px 4px rgba(0,0,0,0.1);
            --shadow-medium: 0 4px 8px rgba(0,0,0,0.1);
            --shadow-heavy: 0 8px 16px rgba(0,0,0,0.1);
            
            /* Border styles */
            --border-width-thin: 1px;
            --border-width-medium: 2px;
            --border-width-thick: 4px;
            
            /* High contrast mode support */
            --high-contrast-mode: 0;  /* 0 for off, 1 for on */
        }
        
        /* High contrast mode colors */
        @media (prefers-contrast: more) {
            :root {
                --high-contrast-mode: 1;
                --primary-color: #0056b3;
                --secondary-color: #2979cf;
                --accent-color: #d86000;
                --background-color: #ffffff;
                --text-color: #000000;
                --node-default-color: #0056b3;
                --node-focus-color: #d86000;
                --node-highlight-color: #cc0000;
                --context-active-color: #006400;
                --context-inactive-color: #444444;
                --path-line-color: #000000;
                --path-node-color: #d86000;
                --shadow-light: 0 0 0 1px #000000;
                --shadow-medium: 0 0 0 2px #000000;
                --shadow-heavy: 0 0 0 3px #000000;
            }
        }
        
        /* Container styles */
        .pathfinder-container {
            background-color: var(--background-color);
            color: var(--text-color);
            font-size: var(--text-size-normal);
            transition: all var(--transition-speed) ease;
            padding: var(--spacing-md);
        }
        
        /* Focus styles for keyboard navigation */
        *:focus {
            outline: 3px solid var(--accent-color);
            outline-offset: 2px;
        }
        
        /* Node styles */
        .pathfinder-node {
            background-color: var(--node-default-color);
            border-radius: var(--border-radius-md);
            box-shadow: var(--shadow-light);
            transition: all var(--transition-speed) ease;
            padding: var(--spacing-md);
            color: white;
            position: relative;
        }
        
        .pathfinder-node.focus {
            background-color: var(--node-focus-color);
            box-shadow: var(--shadow-medium);
        }
        
        .pathfinder-node.highlight {
            background-color: var(--node-highlight-color);
            box-shadow: var(--shadow-heavy);
        }
        
        /* Ensure text in nodes is readable */
        .pathfinder-node-text {
            font-weight: 600;
            text-shadow: 0 1px 2px rgba(0,0,0,0.2);
            padding: var(--spacing-xs);
        }
        
        /* Edge styles with improved positioning */
        .pathfinder-edge {
            stroke: var(--path-line-color);
            stroke-width: 2;
            transition: all var(--transition-speed) ease;
        }
        
        /* Edge labels with improved positioning and readability */
        .pathfinder-edge-label {
            background-color: rgba(255, 255, 255, 0.9);
            padding: var(--spacing-xs) var(--spacing-sm);
            border-radius: var(--border-radius-sm);
            font-size: var(--text-size-small);
            color: var(--text-color);
            border: 1px solid var(--path-line-color);
            text-anchor: middle;
            dominant-baseline: central;
            pointer-events: none;
            /* Ensure horizontal alignment */
            transform: none !important;
        }
        
        /* Context styles */
        .pathfinder-context {
            border-radius: var(--border-radius-lg);
            box-shadow: var(--shadow-medium);
            transition: all var(--transition-speed) ease;
            margin-bottom: var(--spacing-md);
            padding: var(--spacing-md);
        }
        
        .pathfinder-context.active {
            border-left: var(--border-width-thick) solid var(--context-active-color);
        }
        
        .pathfinder-context.inactive {
            opacity: var(--inactive-opacity);
            border-left: var(--border-width-thin) solid var(--context-inactive-color);
        }
        
        /* Path styles */
        .pathfinder-path {
            stroke: var(--path-line-color);
            transition: all var(--transition-speed) ease;
        }
        
        .pathfinder-path-node {
            fill: var(--path-node-color);
        }
        
        /* Button styles */
        .pathfinder-button {
            background-color: var(--primary-color);
            color: white;
            border: none;
            border-radius: var(--border-radius-sm);
            padding: var(--spacing-sm) var(--spacing-md);
            transition: all var(--transition-speed) ease;
            cursor: pointer;
            font-weight: bold;
        }
        
        .pathfinder-button:hover {
            background-color: var(--secondary-color);
            box-shadow: var(--shadow-light);
        }
        
        .pathfinder-button:focus {
            outline: 3px solid var(--accent-color);
            outline-offset: 2px;
        }
        
        /* Header styles */
        .pathfinder-header {
            color: var(--primary-color);
            font-size: var(--text-size-large);
            margin-bottom: var(--spacing-md);
            font-weight: bold;
        }
        
        /* Accessibility helpers */
        .sr-only {
            position: absolute;
            width: 1px;
            height: 1px;
            padding: 0;
            margin: -1px;
            overflow: hidden;
            clip: rect(0, 0, 0, 0);
            white-space: nowrap;
            border-width: 0;
        }
        
        /* Skip links for keyboard navigation */
        .skip-link {
            position: absolute;
            top: -40px;
            left: 0;
            background: var(--primary-color);
            color: white;
            padding: 8px;
            z-index: 100;
            transition: top 0.2s ease;
        }
        
        .skip-link:focus {
            top: 0;
        }
        
        /* Reduced motion support */
        @media (prefers-reduced-motion: reduce) {
            * {
                transition-duration: 0.001s !important;
                animation-duration: 0.001s !important;
            }
        }
        """
        
        return {
            "name": "default",
            "description": "Default Pathfinder theme with accessibility features",
            "css": default_css
        }
    
    def _create_low_contrast_theme(self) -> Dict:
        """
        Create a low-contrast theme for reduced visual strain
        
        Features:
        - High contrast for text only
        - Minimal borders (only on active elements)
        - Subdued colors for non-text elements
        - Increased spacing
        """
        low_contrast_css = """
        :root {
            /* Main colors - low contrast */
            --primary-color: #6b8cb2;
            --secondary-color: #9cb7d9;
            --accent-color: #f0b963;
            --background-color: #f9fbfd;
            --text-color: #222222;
            
            /* Node colors - reduced saturation */
            --node-default-color: #a8c1e5;
            --node-focus-color: #e3b289;
            --node-highlight-color: #d9a688;
            
            /* Context colors - subtle */
            --context-active-color: #91c396;
            --context-inactive-color: #dadada;
            
            /* Path colors - subtle */
            --path-line-color: #ccd9ea;
            --path-node-color: #e3b289;
            
            /* Text sizes - slightly larger */
            --text-size-small: 0.9rem;
            --text-size-normal: 1.1rem;
            --text-size-large: 1.35rem;
            --text-size-xlarge: 1.6rem;
            
            /* Increased spacing */
            --spacing-xs: 0.4rem;
            --spacing-sm: 0.7rem;
            --spacing-md: 1.4rem;
            --spacing-lg: 1.8rem;
            --spacing-xl: 2.5rem;
            
            /* Slower transitions */
            --transition-speed: 0.4s;
            
            /* Higher opacity for better visibility */
            --inactive-opacity: 0.9;
            
            /* Softer border radius */
            --border-radius-sm: 6px;
            --border-radius-md: 10px;
            --border-radius-lg: 16px;
            
            /* Minimal shadows */
            --shadow-light: 0 1px 2px rgba(0,0,0,0.05);
            --shadow-medium: 0 2px 4px rgba(0,0,0,0.05);
            --shadow-heavy: 0 3px 6px rgba(0,0,0,0.05);
            
            /* Border styles */
            --border-width-thin: 0px;  /* No borders on inactive elements */
            --border-width-medium: 1px;
            --border-width-thick: 2px;
        }
        
        /* Container styles */
        .pathfinder-container {
            background-color: var(--background-color);
            color: var(--text-color);
            font-size: var(--text-size-normal);
            transition: all var(--transition-speed) ease;
            padding: var(--spacing-lg);
            line-height: 1.6;
        }
        
        /* Focus styles - subtle */
        *:focus {
            outline: 2px solid var(--accent-color);
            outline-offset: 3px;
        }
        
        /* Node styles - low contrast fills with high contrast text */
        .pathfinder-node {
            background-color: var(--node-default-color);
            border-radius: var(--border-radius-md);
            box-shadow: none;  /* No shadows */
            transition: all var(--transition-speed) ease;
            padding: var(--spacing-md);
            position: relative;
        }
        
        /* Node text always has high contrast regardless of background */
        .pathfinder-node-text {
            background-color: rgba(255, 255, 255, 0.9);
            color: var(--text-color);
            font-weight: 600;
            padding: var(--spacing-xs) var(--spacing-sm);
            border-radius: var(--border-radius-sm);
            box-shadow: none;
        }
        
        /* Edge styles - thinner, lower contrast */
        .pathfinder-edge {
            stroke: var(--path-line-color);
            stroke-width: 1.5;
            stroke-dasharray: none;
        }
        
        /* Edge labels - higher contrast for text only */
        .pathfinder-edge-label {
            background-color: rgba(255, 255, 255, 0.95);
            padding: var(--spacing-xs) var(--spacing-sm);
            border-radius: var(--border-radius-sm);
            font-size: var(--text-size-small);
            color: var(--text-color);
            border: none;  /* No borders */
            text-anchor: middle;
            dominant-baseline: central;
            font-weight: normal;
        }
        
        /* Context styles - only active items have borders */
        .pathfinder-context {
            border-radius: var(--border-radius-lg);
            box-shadow: none;  /* No shadows */
            transition: all var(--transition-speed) ease;
            margin-bottom: var(--spacing-lg);  /* More spacing */
            padding: var(--spacing-md);
            border: none;  /* No border by default */
        }
        
        .pathfinder-context.active {
            border-left: var(--border-width-thick) solid var(--context-active-color);
            background-color: rgba(255, 255, 255, 0.7);  /* Subtle highlight */
        }
        
        .pathfinder-context.inactive {
            border: none;  /* No border for inactive */
            opacity: var(--inactive-opacity);
        }
        
        /* Button styles - clear text, subtle background */
        .pathfinder-button {
            background-color: var(--background-color);
            color: var(--text-color);
            border: var(--border-width-medium) solid var(--primary-color);
            border-radius: var(--border-radius-md);
            padding: var(--spacing-sm) var(--spacing-md);
            font-weight: bold;
            box-shadow: none;  /* No shadow */
        }
        
        .pathfinder-button:hover {
            background-color: rgba(107, 140, 178, 0.1); /* Very subtle highlight */
            box-shadow: none;  /* No shadow */
        }
        
        /* Text elements - always high contrast */
        h1, h2, h3, h4, h5, h6, p, li, td, th, label, input, textarea, select, button {
            color: var(--text-color);
        }
        
        /* Tables without grid lines */
        table {
            border-collapse: collapse;
            width: 100%;
        }
        
        th, td {
            padding: var(--spacing-sm);
            text-align: left;
            border: none;  /* No borders */
        }
        
        tr {
            border-bottom: var(--border-width-thin) solid var(--context-inactive-color);
        }
        
        /* More spacing for list items */
        li {
            margin-bottom: var(--spacing-sm);
        }
        
        /* Increased paragraph spacing */
        p {
            margin-bottom: var(--spacing-md);
            line-height: 1.7;
        }
        """
        
        return {
            "name": "low_contrast",
            "description": "Low contrast theme with minimal visual elements and high text readability",
            "css": low_contrast_css
        }
    
    def _create_focus_theme(self) -> Dict:
        """
        Create a focus theme for government users and data-focused users
        
        Features:
        - Maximum readability for data
        - No decorative elements
        - Strong text contrast
        - Minimal borders and backgrounds
        - Extra spacing between elements
        """
        focus_css = """
        :root {
            /* Main colors - pure minimalism */
            --primary-color: #000000;
            --secondary-color: #666666;
            --accent-color: #000000;
            --background-color: #ffffff;
            --text-color: #000000;
            
            /* Node colors - subtle backgrounds, clear text */
            --node-default-color: #f0f0f0;
            --node-focus-color: #e6e6e6;
            --node-highlight-color: #d9d9d9;
            
            /* Context colors */
            --context-active-color: #000000;
            --context-inactive-color: #cccccc;
            
            /* Path colors */
            --path-line-color: #999999;
            --path-node-color: #cccccc;
            
            /* Text sizes - optimized for reading */
            --text-size-small: 0.95rem;
            --text-size-normal: 1.1rem;
            --text-size-large: 1.4rem;
            --text-size-xlarge: 1.7rem;
            
            /* Maximum spacing */
            --spacing-xs: 0.5rem;
            --spacing-sm: 0.8rem;
            --spacing-md: 1.5rem;
            --spacing-lg: 2rem;
            --spacing-xl: 3rem;
            
            /* Minimal animations */
            --transition-speed: 0.1s;
            
            /* Full opacity */
            --inactive-opacity: 1;
            
            /* Minimal border radius */
            --border-radius-sm: 0px;
            --border-radius-md: 0px;
            --border-radius-lg: 0px;
            
            /* No shadows */
            --shadow-light: none;
            --shadow-medium: none;
            --shadow-heavy: none;
            
            /* Border styles - minimal */
            --border-width-thin: 0px;
            --border-width-medium: 1px;
            --border-width-thick: 2px;
        }
        
        /* Container styles - maximum white space */
        .pathfinder-container {
            background-color: var(--background-color);
            color: var(--text-color);
            font-size: var(--text-size-normal);
            line-height: 1.8;
            padding: var(--spacing-xl);
            max-width: 1400px;
            margin: 0 auto;
        }
        
        /* Focus styles - clear but not distracting */
        *:focus {
            outline: 1px solid #000000;
            outline-offset: 3px;
        }
        
        /* Node styles - minimal visual elements */
        .pathfinder-node {
            background-color: var(--node-default-color);
            border: none;
            padding: var(--spacing-md);
            margin-bottom: var(--spacing-md);
        }
        
        /* Always show node text on white background */
        .pathfinder-node-text {
            background-color: #ffffff;
            padding: var(--spacing-xs) var(--spacing-sm);
            color: #000000;
            font-weight: normal;
            border: 1px solid #cccccc;
        }
        
        /* Edge styles - thin, subtle lines */
        .pathfinder-edge {
            stroke: var(--path-line-color);
            stroke-width: 1;
        }
        
        /* Edge labels - maximally readable */
        .pathfinder-edge-label {
            background-color: #ffffff;
            padding: var(--spacing-xs) var(--spacing-sm);
            font-size: var(--text-size-small);
            color: var(--text-color);
            border: none;
        }
        
        /* Context styles - only active items have indicators */
        .pathfinder-context {
            padding: var(--spacing-lg);
            margin-bottom: var(--spacing-lg);
            background-color: #ffffff;
            border: none;
        }
        
        .pathfinder-context.active {
            border-left: var(--border-width-thick) solid #000000;
        }
        
        .pathfinder-context.inactive {
            background-color: #fafafa;
            border: none;
        }
        
        /* Button styles - minimal, clear buttons */
        .pathfinder-button {
            background-color: #f0f0f0;
            color: #000000;
            border: 1px solid #000000;
            padding: var(--spacing-sm) var(--spacing-lg);
            font-weight: normal;
            text-transform: uppercase;
            letter-spacing: 1px;
            font-size: 90%;
        }
        
        .pathfinder-button:hover {
            background-color: #e0e0e0;
        }
        
        /* Header styles - clean and simple */
        .pathfinder-header {
            color: #000000;
            font-size: var(--text-size-large);
            margin: var(--spacing-xl) 0;
            font-weight: normal;
            border-bottom: 1px solid #000000;
            padding-bottom: var(--spacing-sm);
        }
        
        /* Tables without ANY grid lines */
        table {
            border-collapse: collapse;
            width: 100%;
            margin: var(--spacing-lg) 0;
        }
        
        th {
            padding: var(--spacing-md);
            text-align: left;
            border: none;
            border-bottom: 1px solid #000000;
            font-weight: normal;
            text-transform: uppercase;
            letter-spacing: 1px;
            font-size: 90%;
        }
        
        td {
            padding: var(--spacing-md);
            text-align: left;
            border: none;
        }
        
        tr {
            border: none;
        }
        
        /* Alternate row colors instead of gridlines */
        tr:nth-child(even) {
            background-color: #fafafa;
        }
        
        /* Clean list styling */
        ul, ol {
            padding-left: var(--spacing-lg);
        }
        
        li {
            margin-bottom: var(--spacing-md);
            line-height: 1.7;
        }
        
        /* Generous paragraph spacing */
        p {
            margin-bottom: var(--spacing-lg);
            max-width: 70ch; /* Optimal reading width */
        }
        
        /* Remove all decorative elements */
        [role="decoration"],
        .decoration,
        .decorative {
            display: none;
        }
        
        /* Maximize data visibility */
        [role="data"],
        .data-element {
            font-weight: 600;
            font-size: 105%;
        }
        """
        
        return {
            "name": "focus",
            "description": "Data-focused theme for government employees with minimal visual elements",
            "css": focus_css
        }
    
    def _load_themes(self):
        """Load themes from the themes directory"""
        # First add the built-in themes
        self.themes["default"] = self.default_theme
        self.themes["low_contrast"] = self.low_contrast_theme
        self.themes["focus"] = self.focus_theme
        
        # Then load any other themes from the directory
        for theme_file in self.themes_dir.glob("*.css"):
            theme_name = theme_file.stem
            
            with open(theme_file, 'r', encoding='utf-8') as f:
                css = f.read()
                
                # Parse the CSS to extract any metadata from comments
                description = "Custom theme"
                metadata_match = re.search(r'/\*\s*Theme:\s*(.*?)\s*\*/', css)
                if metadata_match:
                    description = metadata_match.group(1)
                
                self.themes[theme_name] = {
                    "name": theme_name,
                    "description": description,
                    "css": css
                }
        
        # Load current theme setting if it exists
        theme_settings_file = self.themes_dir / 'theme_settings.json'
        if theme_settings_file.exists():
            with open(theme_settings_file, 'r', encoding='utf-8') as f:
                settings = json.load(f)
                self.current_theme = settings.get('current_theme', 'default')
                
                # Ensure the theme exists
                if self.current_theme not in self.themes:
                    self.current_theme = 'default'
    
    def get_current_theme(self) -> Dict:
        """Get the current theme"""
        return self.themes.get(self.current_theme, self.default_theme)
    
    def set_theme(self, theme_name: str) -> bool:
        """Set the current theme"""
        if theme_name not in self.themes:
            return False
        
        self.current_theme = theme_name
        
        # Save the setting
        theme_settings_file = self.themes_dir / 'theme_settings.json'
        with open(theme_settings_file, 'w', encoding='utf-8') as f:
            json.dump({'current_theme': theme_name}, f)
        
        return True
    
    def create_theme(self, name: str, css: str, description: str = None) -> bool:
        """Create a new theme"""
        if name in self.themes and name not in ['default', 'low_contrast', 'focus']:
            return False
        
        # Extract description from CSS comment if not provided
        if not description:
            metadata_match = re.search(r'/\*\s*Theme:\s*(.*?)\s*\*/', css)
            if metadata_match:
                description = metadata_match.group(1)
            else:
                description = f"{name} theme"
        
        # Save the theme
        theme_file = self.themes_dir / f"{name}.css"
        with open(theme_file, 'w', encoding='utf-8') as f:
            f.write(css)
        
        # Add to our themes dictionary
        self.themes[name] = {
            "name": name,
            "description": description,
            "css": css
        }
        
        return True
    
    def create_relaxed_theme(self) -> str:
        """
        Create a relaxed version of the current theme
        
        Slows transitions, increases spacing, and softens colors
        """
        current_theme = self.get_current_theme()
        css = current_theme["css"]
        
        # Modify parameters for a more relaxed theme
        relaxed_css = css.replace("--transition-speed: 0.2s", "--transition-speed: 0.6s")
        relaxed_css = relaxed_css.replace("--spacing-md: 1rem", "--spacing-md: 1.5rem")
        relaxed_css = relaxed_css.replace("--spacing-lg: 1.5rem", "--spacing-lg: 2rem")
        
        # Soften colors if it's the default theme
        if current_theme["name"] == "default":
            relaxed_css = relaxed_css.replace("--primary-color: #4a6fa5", "--primary-color: #5d7eaf")
            relaxed_css = relaxed_css.replace("--secondary-color: #6b96c9", "--secondary-color: #8bacd5")
            relaxed_css = relaxed_css.replace("--accent-color: #ffa500", "--accent-color: #ffb84d")
            relaxed_css = relaxed_css.replace("--node-default-color: #2b68b8", "--node-default-color: #4979bd")
            relaxed_css = relaxed_css.replace("--node-focus-color: #d86000", "--node-focus-color: #e07d33")
        
        # Add relaxed theme tag
        relaxed_css = f"/* Theme: Relaxed {current_theme['name']} - Slower transitions and softer colors */\n" + relaxed_css
        
        # Add a class for the relaxed theme
        relaxed_css += "\n\n.pathfinder-relaxed {\n    transition-duration: 0.8s;\n}\n"
        
        # Create the theme
        theme_name = f"relaxed_{current_theme['name']}"
        self.create_theme(
            name=theme_name, 
            css=relaxed_css, 
            description=f"Relaxed version of {current_theme['name']} with slower transitions and softer colors"
        )
        
        return theme_name
    
    def create_high_contrast_theme(self) -> str:
        """
        Create a high contrast version of the current theme
        
        Increases contrast for better accessibility
        """
        current_theme = self.get_current_theme()
        css = current_theme["css"]
        
        # Define high contrast colors
        high_contrast_css = css.replace("--primary-color: #4a6fa5", "--primary-color: #0046a6")
        high_contrast_css = high_contrast_css.replace("--secondary-color: #6b96c9", "--secondary-color: #1f6bbc")
        high_contrast_css = high_contrast_css.replace("--accent-color: #ffa500", "--accent-color: #d86000")
        high_contrast_css = high_contrast_css.replace("--text-color: #333333", "--text-color: #000000")
        high_contrast_css = high_contrast_css.replace("--background-color: #f5f7fa", "--background-color: #ffffff")
        high_contrast_css = high_contrast_css.replace("--node-default-color: #2b68b8", "--node-default-color: #003da0")
        high_contrast_css = high_contrast_css.replace("--node-focus-color: #d86000", "--node-focus-color: #c14d00")
        
        # Add high contrast theme tag
        high_contrast_css = f"/* Theme: High Contrast {current_theme['name']} - Increased contrast for accessibility */\n" + high_contrast_css
        
        # Create the theme
        theme_name = f"high_contrast_{current_theme['name']}"
        self.create_theme(
            name=theme_name, 
            css=high_contrast_css, 
            description=f"High contrast version of {current_theme['name']} for better accessibility"
        )
        
        return theme_name
    
    def get_css_inline(self) -> str:
        """Get the current theme CSS for inline use"""
        theme = self.get_current_theme()
        return theme["css"]
    
    def get_css_data_uri(self) -> str:
        """Get the current theme CSS as a data URI for use in HTML"""
        theme = self.get_current_theme()
        css_bytes = theme["css"].encode('utf-8')
        base64_css = base64.b64encode(css_bytes).decode('utf-8')
        return f"data:text/css;base64,{base64_css}"
    
    def list_themes(self) -> List[Dict]:
        """List all available themes"""
        return [
            {"name": name, "description": theme["description"], "is_current": name == self.current_theme}
            for name, theme in self.themes.items()
        ]