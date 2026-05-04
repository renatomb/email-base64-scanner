#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import base64
import shutil
from pathlib import Path
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def extract_base64_blocks(file_path):
    """
    Extrai todos os blocos base64 de um arquivo de e-mail.
    Retorna uma lista de strings base64.
    """
    base64_blocks = []
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Procura por Content-Transfer-Encoding: base64
            if 'Content-Transfer-Encoding:' in line and 'base64' in line.lower():
                # Pula linhas até encontrar o início do conteúdo base64
                i += 1
                
                # Pula linhas vazias e headers adicionais
                while i < len(lines) and (lines[i].strip() == '' or ':' in lines[i]):
                    i += 1
                
                # Coleta o bloco base64
                base64_content = []
                while i < len(lines):
                    current_line = lines[i].rstrip('\n\r')
                    
                    # Linha vazia indica fim do bloco
                    if current_line.strip() == '':
                        break
                    
                    base64_content.append(current_line)
                    
                    # Se a linha termina com =, pode ser o fim do base64
                    if current_line.endswith('='):
                        # Verifica se a próxima linha está vazia
                        if i + 1 < len(lines) and lines[i + 1].strip() == '':
                            i += 1
                            break
                    
                    i += 1
                
                if base64_content:
                    base64_blocks.append(''.join(base64_content))
            
            i += 1
    
    except Exception as e:
        print(f"Erro ao ler arquivo {file_path}: {e}")
    
    return base64_blocks


def decode_base64(base64_string):
    """
    Decodifica uma string base64.
    Retorna o conteúdo decodificado como string, ou None se houver erro.
    """
    try:
        decoded_bytes = base64.b64decode(base64_string)
        # Tenta decodificar como UTF-8, se falhar usa latin-1
        try:
            return decoded_bytes.decode('utf-8')
        except UnicodeDecodeError:
            return decoded_bytes.decode('latin-1', errors='ignore')
    except Exception as e:
        print(f"Erro ao decodificar base64: {e}")
        return None


def search_patterns_in_content(content, patterns):
    """
    Procura por padrões no conteúdo.
    Retorna True se encontrar qualquer um dos padrões.
    """
    for pattern in patterns:
        if pattern in content:
            return True, pattern
    return False, None


def process_email_files(source_dir, dest_dir):
    """
    Processa todos os arquivos de e-mail no diretório fonte.
    Move arquivos que contêm os padrões especificados para o diretório destino.
    """
    # Array de trechos a procurar
    search_patterns = [
        '.malware-domain1.example.com',
        '.malware-domain2.example.com'
    ]
    
    # Valida diretórios
    if not os.path.isdir(source_dir):
        print(f"Erro: Diretorio fonte '{source_dir}' nao existe.")
        return
    
    # Cria diretório destino se não existir
    os.makedirs(dest_dir, exist_ok=True)
    
    # Lista todos os arquivos no diretório fonte
    files = [f for f in os.listdir(source_dir) if os.path.isfile(os.path.join(source_dir, f))]
    
    print(f"Processando {len(files)} arquivo(s) em '{source_dir}'...\n")
    
    moved_count = 0
    
    for filename in files:
        file_path = os.path.join(source_dir, filename)
        print(f"=== Processando: {filename} ===")
        
        # Extrai blocos base64
        base64_blocks = extract_base64_blocks(file_path)
        
        if not base64_blocks:
            print(f"Nenhum bloco base64 encontrado.\n")
            continue
        
        print(f"Encontrado(s) {len(base64_blocks)} bloco(s) base64.")
        
        # Processa cada bloco
        found_pattern = False
        for idx, block in enumerate(base64_blocks, 1):
            print(f"\n  --- Bloco {idx} ---")
            
            # Decodifica
            decoded = decode_base64(block)
            
            if decoded:
                print(f"Conteudo decodificado ({len(decoded)} caracteres):")
                # Exibe preview (primeiros 500 caracteres)
                #preview = decoded[:500]
                #print(f"{preview}")
                #if len(decoded) > 500:
                #    print(f"... (truncado)")
                
                # Procura padrões
                match_found, matched_pattern = search_patterns_in_content(decoded, search_patterns)
                
                if match_found:
                    print(f"\n✅ PADRAO ENCONTRADO: '{matched_pattern}'")
                    found_pattern = True
        
        # Move arquivo se encontrou padrão
        if found_pattern:
            dest_path = os.path.join(dest_dir, filename)
            try:
                shutil.move(file_path, dest_path)
                print(f"\n➡️ Arquivo movido para: {dest_path}")
                moved_count += 1
            except Exception as e:
                print(f"\n⚠️ Erro ao mover arquivo: {e}")
        else:
            print(f"\nNenhum padrao encontrado. Arquivo nao movido.")
        
        print()
    
    print(f"\n{'='*60}")
    print(f"Processamento concluido!")
    print(f"Total de arquivos movidos: {moved_count}/{len(files)}")
    print(f"{'='*60}")


def main():
    if len(sys.argv) != 3:
        print("Uso: python3 email_filter.py <diretorio_origem> <diretorio_destino>")
        print("\nExemplo:")
        print("  python3 email_filter.py /path/emails /path/filtered")
        sys.exit(1)
    
    source_directory = sys.argv[1]
    destination_directory = sys.argv[2]
    
    process_email_files(source_directory, destination_directory)


if __name__ == "__main__":
    main()