#!/usr/bin/env python3
"""
Script de ejecución principal - Punto de entrada alternativo
"""

import sys
import os

# Agregar el directorio raíz al path de Python
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import main

if __name__ == "__main__":
    main()