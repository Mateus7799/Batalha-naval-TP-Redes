#!/bin/bash

# Script para compilar e executar Batalha Naval

echo "╔════════════════════════════════════════╗"
echo "║   Batalha Naval - Jogo em Java Swing   ║"
echo "╚════════════════════════════════════════╝"
echo ""

# Verificar se Java está instalado
if ! command -v javac &> /dev/null; then
    echo "❌ Erro: Java Development Kit (JDK) não está instalado!"
    echo ""
    echo "Instale o JDK seguindo as instruções em INSTRUCOES_EXECUCAO.md"
    exit 1
fi

echo "✓ Java encontrado: $(java -version 2>&1 | head -n 1)"
echo ""

# Compilar
echo "🔨 Compilando..."
javac BatalhaNavalLogic.java BatalhaNavalGUI.java

if [ $? -ne 0 ]; then
    echo "❌ Erro na compilação!"
    exit 1
fi

echo "✓ Compilação bem-sucedida!"
echo ""

# Executar
echo "🎮 Iniciando o jogo..."
echo ""
java BatalhaNavalGUI
