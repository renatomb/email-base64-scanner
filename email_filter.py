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
            
            # Procura por Content-Transfer-Encoding: base64 (não quoted-printable)
            if 'Content-Transfer-Encoding:' in line:
                # Verifica se é base64 e NÃO é quoted-printable
                if 'base64' in line.lower() and 'quoted-printable' not in line.lower():
                    # Pula linhas até encontrar o início do conteúdo base64
                    i += 1
                    
                    # Pula todos os headers adicionais (linhas que começam com letra maiúscula seguida de - ou :, ou são continuações com tab/espaço)
                    while i < len(lines):
                        current = lines[i]
                        stripped = current.strip()
                        # Linha vazia = fim dos headers
                        if stripped == '':
                            i += 1
                            break
                        # Header ou continuação de header
                        if (':' in current and current[0].isupper()) or current[0] in '\t ':
                            i += 1
                            continue
                        # Se chegou aqui, encontrou início do conteúdo
                        break
                    
                    # Coleta o bloco base64
                    base64_content = []
                    while i < len(lines):
                        current_line = lines[i].rstrip('\n\r')
                        
                        # Linha vazia ou início de novo boundary indica fim do bloco
                        if current_line.strip() == '' or current_line.startswith('--'):
                            break
                        
                        base64_content.append(current_line)
                        
                        # Se a linha termina com =, pode ser o fim do base64
                        if current_line.endswith('='):
                            # Verifica se a próxima linha está vazia ou é boundary
                            if i + 1 < len(lines):
                                next_line = lines[i + 1].strip()
                                if next_line == '' or next_line.startswith('--'):
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
    Retorna o conteudo decodificado como string, ou None se houver erro.
    """
    try:
        # Remove espaços e quebras de linha
        base64_string = base64_string.strip().replace('\n', '').replace('\r', '').replace(' ', '')
        
        # Corrige padding se necessário
        missing_padding = len(base64_string) % 4
        if missing_padding:
            base64_string += '=' * (4 - missing_padding)
        
        decoded_bytes = base64.b64decode(base64_string, validate=False)
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
    Procura por padroes no conteúdo.
    Retorna True se encontrar qualquer um dos padroes.
    """
    for pattern in patterns:
        if pattern in content:
            return True, pattern
    return False, None


def load_patterns_from_file(filename='filtrar-emails.txt', show_patterns=False):
    """
    Carrega padroes de dominios do arquivo de texto.
    Cada linha do arquivo deve conter um dominio.
    """
    patterns = []
    
    if not os.path.isfile(filename):
        print(f"Arquivo de padroes '{filename}' nao encontrado.")
        print(f"Criando arquivo de exemplo...")
        # Cria arquivo de exemplo se não existir
        with open(filename, 'w', encoding='utf-8') as f:
            f.write('.malware-domain1.example.com\n')
            f.write('.malware-domain2.example.com\n')
        print(f"Arquivo '{filename}' criado com padroes de exemplo.")
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # Ignora linhas vazias e comentários
                if line and not line.startswith('#'):
                    patterns.append(line)
        
        print(f"Carregados {len(patterns)} padroes do arquivo '{filename}'")
        if show_patterns:
            for i, pattern in enumerate(patterns, 1):
                print(f"  {i}. {pattern}")
            print()
        
    except Exception as e:
        print(f"Erro ao ler arquivo de padroes: {e}")
        patterns = ['.malware-domain1.example.com', '.malware-domain2.example.com']
    
    return patterns


def process_email_files(source_dir, dest_dir, show_patterns=False, show_preview=False):
    """
    Processa todos os arquivos de e-mail no diretorio fonte.
    Move arquivos que contem os padroes especificados para o diretorio destino.
    """
    # Carrega padroes do arquivo
    search_patterns = load_patterns_from_file('filtrar-emails.txt', show_patterns=show_patterns)
    
    # Valida diretorios
    if not os.path.isdir(source_dir):
        print(f"Erro: Diretorio fonte '{source_dir}' nao existe.")
        return
    
    # Cria diretorio destino se nao existir
    os.makedirs(dest_dir, exist_ok=True)
    
    # Lista todos os arquivos no diretorio fonte
    files = [f for f in os.listdir(source_dir) if os.path.isfile(os.path.join(source_dir, f))]
    
    print(f"Processando {len(files)} arquivo(s) em '{source_dir}'...\n")
    
    moved_count = 0
    
    for filename in files:
        file_path = os.path.join(source_dir, filename)
        print(f"=== Processando: {filename} ===")
        
        # Ler conteudo completo do arquivo para busca em plaintext
        found_in_plaintext = False
        matched_plain_pattern = None
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                full_content = f.read()
            
            # Procurar padroes no conteudo plaintext
            found_in_plaintext, matched_plain_pattern = search_patterns_in_content(full_content, search_patterns)
            if found_in_plaintext:
                print(f"✅ PADRAO ENCONTRADO EM PLAINTEXT: '{matched_plain_pattern}'")
        except Exception as e:
            print(f"⚠️ Erro ao ler arquivo em plaintext: {e}")
        
        # Extrai blocos base64
        base64_blocks = extract_base64_blocks(file_path)
        
        if not base64_blocks:
            print(f"Nenhum bloco base64 encontrado.")
            # Se não há base64 mas encontrou em plaintext, move o arquivo
            if found_in_plaintext:
                dest_path = os.path.join(dest_dir, filename)
                try:
                    shutil.move(file_path, dest_path)
                    print(f"➡️ Arquivo movido para: {dest_path}")
                    moved_count += 1
                except Exception as e:
                    print(f"⚠️ Erro ao mover arquivo: {e}")
            print()
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
                # Exibe preview (primeiros 500 caracteres) somente com flag
                if show_preview:
                    preview = decoded[:500]
                    print(f"{preview}")
                    if len(decoded) > 500:
                        print(f"... (truncado)")
                
                # Procura padroes
                match_found, matched_pattern = search_patterns_in_content(decoded, search_patterns)
                
                if match_found:
                    print(f"\n✅ PADRAO ENCONTRADO: '{matched_pattern}'")
                    found_pattern = True
        
        # Move arquivo se encontrou padrao (em base64 OU plaintext)
        if found_pattern or found_in_plaintext:
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
    args = [arg for arg in sys.argv[1:] if arg not in ('--show-patterns', '--show-preview')]
    show_patterns = '--show-patterns' in sys.argv[1:]
    show_preview = '--show-preview' in sys.argv[1:]

    if len(args) != 2:
        print("Uso: python3 email_filter.py [--show-patterns] [--show-preview] <diretorio_origem> <diretorio_destino>")
        print("\nExemplo:")
        print("  python3 email_filter.py --show-patterns --show-preview /path/emails /path/filtered")
        sys.exit(1)

    source_directory = args[0]
    destination_directory = args[1]

    process_email_files(
        source_directory,
        destination_directory,
        show_patterns=show_patterns,
        show_preview=show_preview,
    )


if __name__ == "__main__":
    main()
