#!/usr/bin/env python3
"""
Script pour démarrer le serveur MCP facilement
"""
import uvicorn
import sys
import os

if __name__ == "__main__":
    print("🚀 Démarrage du serveur MCP Agent IA...")
    print("📍 Le serveur sera accessible à: http://127.0.0.1:8000")
    print("📚 Documentation API: http://127.0.0.1:8000/docs")
    print("💚 Endpoint de santé: http://127.0.0.1:8000/health")
    print("\n⚠️  Appuyez sur Ctrl+C pour arrêter le serveur\n")
    
    try:
        uvicorn.run(
            "mcp_server:app",
            host="127.0.0.1",
            port=8000,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n\n👋 Serveur arrêté. Au revoir !")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Erreur lors du démarrage: {e}")
        sys.exit(1)

