#!/usr/bin/env python3
"""
Script de prueba para las notificaciones personalizadas
"""

import tkinter as tk
from tkinter import messagebox
import sys
import os

def test_basic_notification():
    """Prueba básica de notificación"""
    try:
        # Crear ventana de prueba overlay
        root = tk.Tk()
        root.withdraw()  # Ocultar ventana principal
        
        notification = tk.Toplevel()
        notification.title("Prueba Overlay")
        notification.geometry("400x120")
        
        # Configurar overlay
        notification.wm_attributes('-topmost', True)
        notification.wm_attributes('-alpha', 0.95)
        notification.overrideredirect(True)
        
        # Posicionar en esquina superior derecha
        notification.update_idletasks()
        x = notification.winfo_screenwidth() - 420
        y = 20
        notification.geometry(f"+{x}+{y}")
        
        # Contenido
        frame = tk.Frame(notification, bg='#27AE60', padx=20, pady=15)
        frame.pack(fill='both', expand=True)
        
        tk.Label(frame, text="🚀 Prueba de Overlay", 
                font=('Arial', 12, 'bold'), 
                fg='white', bg='#27AE60').pack()
        
        tk.Label(frame, text="Esta notificación debería aparecer\nsobre juegos en pantalla completa", 
                font=('Arial', 9), 
                fg='white', bg='#27AE60',
                justify='center').pack(pady=(5, 0))
        
        # Auto-cerrar después de 3 segundos
        notification.after(3000, lambda: [notification.destroy(), root.quit()])
        
        root.mainloop()
        
    except Exception as e:
        print(f"Error en prueba: {e}")

def test_overlay_visibility():
    """Prueba si el overlay es visible sobre otras ventanas"""
    print("🔍 Probando visibilidad de overlay...")
    print("1. Ejecuta este test")
    print("2. Abre un juego o aplicación en pantalla completa")
    print("3. Verifica si aparece la notificación")
    print("4. Presiona Enter para continuar...")
    input()
    
    test_basic_notification()
    
    print("✅ ¿Pudiste ver la notificación sobre la aplicación en pantalla completa?")
    response = input("Responde S/N: ").upper()
    
    if response == 'S':
        print("🎉 ¡Perfecto! Las notificaciones funcionan correctamente.")
    else:
        print("⚠️  Es posible que necesites ejecutar como administrador.")
        print("💡 También verifica que el juego no esté en modo 'Exclusivo'.")

def main():
    print("🎮 Test de Notificaciones para Gaming")
    print("=" * 40)
    print("Este script prueba si las notificaciones aparecen")
    print("correctamente sobre juegos en pantalla completa.\n")
    
    choice = input("¿Ejecutar prueba de visibilidad? (S/N): ").upper()
    
    if choice == 'S':
        test_overlay_visibility()
    else:
        print("Ejecutando prueba básica...")
        test_basic_notification()

if __name__ == "__main__":
    main()
