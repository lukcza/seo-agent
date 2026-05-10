import sys
import subprocess
import os

def main():
    print("\033[96m\033[1m" + "=" * 65)
    print("         🌟 INTERAKTYWNY ASYSTENT SEO & AUDYTOR STRON (v2.0) 🌟")
    print("=" * 65 + "\033[0m")
    print("  \033[92m[1]\033[0m Uruchom Interaktywny Terminal CLI (Konsola)")
    print("  \033[92m[2]\033[0m Uruchom Serwer Web i Panel Przeglądarki (FastAPI & Dashboard)")
    print("\033[96m" + "=" * 65 + "\033[0m")
    
    try:
        choice = input("\nWybierz tryb uruchomienia (1 lub 2): ").strip()
    except (KeyboardInterrupt, EOFError):
        print("\nAnulowano.")
        return
    
    if choice == "1":
        # Launch CLI mode directly
        import asyncio
        from cli import run_app_async
        try:
            asyncio.run(run_app_async())
        except KeyboardInterrupt:
            print("\n👋 Do zobaczenia!")
    elif choice == "2":
        # Launch FastAPI server using local virtual environment python
        print("\n🚀 Uruchamiam serwer FastAPI pod adresem \033[94m\033[4mhttp://127.0.0.1:8000\033[0m...")
        print("Naciśnij \033[1mCtrl+C\033[0m aby zatrzymać serwer.\n")
        
        python_exe = os.path.join(".venv", "Scripts", "python.exe")
        if not os.path.exists(python_exe):
            python_exe = "python"
            
        try:
            subprocess.run([python_exe, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"])
        except KeyboardInterrupt:
            print("\n🛑 Serwer FastAPI został zatrzymany. Do zobaczenia!")
    else:
        print("\033[91mBłąd: Wybór poza zakresem (wybierz 1 lub 2).\033[0m")

if __name__ == "__main__":
    main()
