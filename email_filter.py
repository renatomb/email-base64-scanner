#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import base64
import shutil
import argparse
from pathlib import Path
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Tenta importar a biblioteca email do Python
try:
    from email import message_from_file
    from email.policy import default
    EMAIL_LIBRARY_AVAILABLE = True
except ImportError:
    EMAIL_LIBRARY_AVAILABLE = False
    print("⚠️ Biblioteca 'email' não disponível. Usando parser manual.")


def extract_base64_blocks_with_email_lib(file_obj):
    """
    Extrai e decodifica blocos base64 usando a biblioteca email padrão do Python.
    Mais robusto para emails complexos (multipart aninhados, charsets variados, etc).
    Recebe um file object aberto.
    Retorna uma lista de conteúdos decodificados (strings).
    """
    decoded_blocks = []
    
    try:
        # Parse do email diretamente do file object
        msg = message_from_file(file_obj, policy=default)
        
        # Itera por todas as partes do email (incluindo multipart aninhados)
        for part in msg.walk():
            # Pula containers multipart (sem conteúdo real)
            if part.is_multipart():
                continue
            
            # Verifica se é base64
            transfer_encoding = part.get('Content-Transfer-Encoding', '').lower()
            if 'base64' in transfer_encoding:
                # Pega o payload já decodificado (bytes)
                payload = part.get_payload(decode=True)
                if payload:
                    # Tenta decodificar como string com charset apropriado
                    charset = part.get_content_charset() or 'utf-8'
                    try:
                        decoded = payload.decode(charset, errors='ignore')
                    except (UnicodeDecodeError, LookupError):
                        # Fallback para latin-1 se charset falhar
                        decoded = payload.decode('latin-1', errors='ignore')
                    
                    if decoded:
                        decoded_blocks.append(decoded)
    
    except Exception as e:
        print(f"⚠️ Erro ao usar biblioteca email: {e}")
        print("   Tentando com parser manual...")
        return None
    
    return decoded_blocks


def extract_base64_blocks_manual(lines):
    """
    Extrai todos os blocos base64 das linhas de um arquivo de e-mail (método manual).
    Retorna uma lista de strings base64 (ainda codificadas).
    """
    base64_blocks = []
    
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
    
    return base64_blocks


def extract_base64_blocks(file_path=None, file_content=None):
    """
    Extrai e decodifica blocos base64 de um arquivo de e-mail.
    Usa heurísticas para decidir entre biblioteca email (emails complexos) 
    ou parser manual (emails simples, ~3x mais rápido).
    
    Pode receber file_path OU file_content (string com conteúdo do arquivo).
    Retorna uma lista de conteúdos decodificados (strings).
    """
    # Garante que temos o conteúdo
    if file_content is None:
        if file_path is None:
            return []
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                file_content = f.read()
        except Exception as e:
            print(f"⚠️ Erro ao ler arquivo: {e}")
            return []
    
    # Usa heurística para decidir qual parser usar
    use_email_lib = EMAIL_LIBRARY_AVAILABLE and should_use_email_lib(file_content)
    
    # Se biblioteca email está disponível E email é complexo
    if use_email_lib:
        from io import StringIO
        file_obj = StringIO(file_content)
        blocks = extract_base64_blocks_with_email_lib(file_obj)
        # Se funcionou, retorna o resultado (já decodificado)
        if blocks is not None:
            return blocks
        # Se falhou, continua para parser manual
    
    # Parser manual (padrão para emails simples ou fallback)
    lines = file_content.split('\n')
    
    # Extrai blocos base64 (ainda codificados)
    base64_blocks = extract_base64_blocks_manual(lines)
    
    # Decodifica cada bloco
    decoded_blocks = []
    for block in base64_blocks:
        decoded = decode_base64(block)
        if decoded:
            decoded_blocks.append(decoded)
    
    return decoded_blocks


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
        
        if show_patterns:
            print(f"Carregados {len(patterns)} padroes do arquivo '{filename}'")
            for i, pattern in enumerate(patterns, 1):
                print(f"  {i}. {pattern}")
            print()
        
    except Exception as e:
        print(f"Erro ao ler arquivo de padroes: {e}")
        patterns = ['.malware-domain1.example.com', '.malware-domain2.example.com']
    
    return patterns


def process_email_files(source_dir, dest_dir, show_patterns=False, show_preview=False, dry_run=False, show_matched=False):
    """
    Processa todos os arquivos de e-mail no diretorio fonte.
    Move arquivos que contem os padroes especificados para o diretorio destino.
    Se dry_run=True, simula o processamento sem modificar arquivos.
    Se show_matched=True, exibe os padrões encontrados durante o processamento.
    """
    # Carrega padroes do arquivo
    search_patterns = load_patterns_from_file('filtrar-emails.txt', show_patterns=show_patterns)
    
    # Valida diretorios
    if not os.path.isdir(source_dir):
        print(f"Erro: Diretorio fonte '{source_dir}' nao existe.")
        return
    
    # Cria diretorio destino se nao existir (exceto em dry-run)
    if not dry_run:
        os.makedirs(dest_dir, exist_ok=True)
    else:
        print(f"[DRY-RUN] Diretorio destino seria: '{dest_dir}'")
        print(f"[DRY-RUN] Nenhuma alteracao sera feita no disco.\n")
    
    # Lista todos os arquivos no diretorio fonte
    files = [f for f in os.listdir(source_dir) if os.path.isfile(os.path.join(source_dir, f))]
    
    print(f"Processando {len(files)} arquivo(s) em '{source_dir}'...\n")
    
    moved_count = 0
    
    for filename in files:
        file_path = os.path.join(source_dir, filename)
        print(f"=== Processando: {filename} ===")
        
        # Busca em plaintext e extração de base64
        found_in_plaintext = False
        matched_plain_pattern = None
        decoded_blocks = []
        
        try:
            # Ler arquivo UMA ÚNICA VEZ
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                full_content = f.read()
            
            # Procurar padroes no conteudo plaintext
            found_in_plaintext, matched_plain_pattern = search_patterns_in_content(full_content, search_patterns)
            if found_in_plaintext and show_matched:
                print(f"[{filename}] ✅ PADRAO ENCONTRADO EM PLAINTEXT: '{matched_plain_pattern}'")
            
            # Extrai e decodifica blocos base64 usando o mesmo conteúdo
            decoded_blocks = extract_base64_blocks(file_content=full_content)
            
        except Exception as e:
            print(f"⚠️ Erro ao ler arquivo: {e}")
        
        if not decoded_blocks:
            print(f"Nenhum bloco base64 encontrado.")
            # Se não há base64 mas encontrou em plaintext, move o arquivo
            if found_in_plaintext:
                dest_path = os.path.join(dest_dir, filename)
                if dry_run:
                    print(f"[DRY-RUN] Arquivo seria movido para: {dest_path}")
                    moved_count += 1
                else:
                    try:
                        shutil.move(file_path, dest_path)
                        print(f"➡️ Arquivo movido para: {dest_path}")
                        moved_count += 1
                    except Exception as e:
                        print(f"⚠️ Erro ao mover arquivo: {e}")
            print()
            continue
        
        print(f"Encontrado(s) {len(decoded_blocks)} bloco(s) base64.")
        
        # Processa cada bloco (já decodificado)
        found_pattern = False
        for idx, decoded in enumerate(decoded_blocks, 1):
            print(f"\n  --- Bloco {idx} ---")
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
                if show_matched:
                    print(f"[{filename}] ✅ PADRAO ENCONTRADO: '{matched_pattern}'")
                found_pattern = True
        
        # Move arquivo se encontrou padrao (em base64 OU plaintext)
        if found_pattern or found_in_plaintext:
            dest_path = os.path.join(dest_dir, filename)
            if dry_run:
                print(f"\n[DRY-RUN] Arquivo seria movido para: {dest_path}")
                moved_count += 1
            else:
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

def should_use_email_lib(content: str) -> bool:
    """
    Analisa o conteúdo do email e decide se deve usar a biblioteca email.
    Retorna True se o email parecer complexo.
    """
    content_lower = content.lower()
    lines = content.splitlines()
    
    score = 0
    
    # 1. Múltiplos boundaries (forte indicador de multipart aninhado)
    boundary_count = content_lower.count('boundary=')
    if boundary_count >= 2:
        score += 3
    
    # 2. Muitos blocos base64
    base64_headers = sum(1 for line in lines if 'content-transfer-encoding:' in line.lower() and 'base64' in line.lower())
    if base64_headers >= 2:
        score += 2
    
    # 3. Headers folded (continuação)
    folded_headers = sum(1 for line in lines if line.startswith((' ', '\t')) and ':' not in line[:10])
    if folded_headers >= 3:
        score += 1
    
    # 4. Anexos explícitos
    if 'content-disposition: attachment' in content_lower:
        score += 2
    
    # 5. Multipart aninhado ou mixed/alternative
    if 'multipart/mixed' in content_lower or 'multipart/alternative' in content_lower:
        score += 1
    
    # 6. Sinais de e-mail problemático (Gmail, Outlook, etc.)
    if any(x in content_lower for x in ['name="=?utf-8?', '=?utf-8?b?']):
        score += 1
    
    # Threshold: se score >= 3 → considera complexo
    return score >= 3


def main():
    parser = argparse.ArgumentParser(
        description='Filtra emails base64 e plaintext procurando por padrões maliciosos.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Exemplos:
  %(prog)s /path/emails /path/filtered
  %(prog)s --show-patterns /path/emails /path/filtered
  %(prog)s --show-patterns --show-preview /path/emails /path/filtered

O arquivo 'filtrar-emails.txt' deve conter os padrões a serem procurados (um por linha).
        '''
    )
    
    parser.add_argument(
        'source_dir',
        help='Diretório contendo os arquivos de email a serem processados'
    )
    
    parser.add_argument(
        'dest_dir',
        help='Diretório destino para mover emails que contenham padrões maliciosos'
    )
    
    parser.add_argument(
        '--show-patterns',
        action='store_true',
        help='Exibe a lista de padrões carregados do arquivo de configuração'
    )
    
    parser.add_argument(
        '--show-preview',
        action='store_true',
        help='Exibe preview (primeiros 500 caracteres) do conteúdo decodificado'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Simula o processamento sem fazer alterações no disco (não move arquivos)'
    )
    
    parser.add_argument(
        '--show-matched',
        action='store_true',
        help='Exibe os padrões encontrados durante o processamento'
    )
    
    args = parser.parse_args()
    
    process_email_files(
        args.source_dir,
        args.dest_dir,
        show_patterns=args.show_patterns,
        show_preview=args.show_preview,
        dry_run=args.dry_run,
        show_matched=args.show_matched,
    )


if __name__ == "__main__":
    main()
