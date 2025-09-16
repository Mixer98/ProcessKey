#!/usr/bin/env python3
"""
Prueba rápida del sistema de iconos
"""

import os
import sys

# Agregar src al path
sys.path.insert(0, 'src')

try:
    from src.icon_utils import icon_manager
    print("✅ IconManager importado correctamente")
    
    # Probar carga de iconos
    print(f"🔍 Ruta de iconos: {icon_manager.icons_path}")
    print(f"📁 Directorio existe: {os.path.exists(icon_manager.icons_path)}")
    
    # Probar obtener rutas de iconos
    test_emojis = ["🚀", "💚", "❌", "✅", "🎯"]
    print("\n🧪 Probando mapeo de emojis a iconos:")
    
    for emoji in test_emojis:
        icon_path = icon_manager.get_icon_path(emoji)
        if icon_path:
            exists = os.path.exists(icon_path)
            status = "✅" if exists else "❌"
            filename = os.path.basename(icon_path)
            print(f"  {emoji} → {filename} {status}")
        else:
            print(f"  {emoji} → No mapeado ❌")
    
    print("\n🏁 Prueba completada")
    
except ImportError as e:
    print(f"❌ Error de importación: {e}")
except Exception as e:
    print(f"❌ Error inesperado: {e}")
