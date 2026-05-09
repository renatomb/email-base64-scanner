# Email Filter Script - Filtro de E-mails por Base64

Script Python para processar arquivos de e-mail em formato texto, decodificar blocos base64 e filtrar mensagens com base em padrões específicos.

## 📋 Funcionalidades

- ✅ Processa todos os arquivos em um diretório
- ✅ Detecta blocos `Content-Transfer-Encoding: base64` em e-mails
- ✅ Extrai e decodifica múltiplos blocos base64 por arquivo
- ✅ Exibe o conteúdo decodificado na tela (opcional)
- ✅ Procura por padrões específicos no conteúdo plaintext
- ✅ Procura por padrões específicos no conteúdo decodificado
- ✅ Move automaticamente arquivos que contêm os padrões para diretório de destino

## 🎯 Padrões de Busca

O script procura por padrões no conteúdo plaintext e base64 baseado no que for especificado no arquivo `filtrar-emails.txt`

## 🚀 Como Usar

### Sintaxe

```bash
python3 email_filter.py [-h] [--show-patterns] [--show-preview] [--dry-run] [--show-matched] source_dir dest_dir
```

### Ajuda

Para ver todas as opções disponíveis:

```bash
python3 email_filter.py --help
```

### Parâmetros

**Posicionais:**
- **`source_dir`**: Diretório contendo os arquivos de e-mail a serem processados
- **`dest_dir`**: Diretório para onde os arquivos filtrados serão movidos

**Opcionais:**
- **`-h, --help`**: Exibe mensagem de ajuda e sai
- **`--show-patterns`**: Exibe na tela todos os padrões carregados do arquivo `filtrar-emails.txt`
- **`--show-preview`**: Exibe preview (até 500 caracteres) do conteúdo decodificado de cada bloco base64
- **`--dry-run`**: Simula o processamento sem fazer alterações no disco (não move arquivos nem cria diretórios)
- **`--show-matched`**: Exibe os padrões encontrados durante o processamento (plaintext e base64)

### Exemplos

```bash
# Ver ajuda
python3 email_filter.py --help

# Exemplo básico
python3 email_filter.py /var/mail/inbox /var/mail/filtered

# Simular processamento sem mover arquivos (dry-run)
python3 email_filter.py --dry-run /var/mail/inbox /var/mail/filtered

# Exibir padrões encontrados durante processamento
python3 email_filter.py --show-matched /var/mail/inbox /var/mail/filtered

# Exibir apenas lista de padrões carregados
python3 email_filter.py --show-patterns /var/mail/inbox /var/mail/filtered

# Exibir preview do conteúdo decodificado
python3 email_filter.py --show-preview /var/mail/inbox /var/mail/filtered

# Combinando múltiplas opções
python3 email_filter.py --show-matched --dry-run /var/mail/inbox /var/mail/filtered

# Usando caminhos relativos
python3 email_filter.py ./emails ./emails_filtrados

# Caminhos completos
python3 email_filter.py /home/usuario/emails /home/usuario/suspeitos
```

## 📝 Comportamento

1. **Processamento**: O script lê cada arquivo no diretório de origem
2. **Detecção**: Identifica blocos com `Content-Transfer-Encoding: base64`
3. **Extração**: Captura o conteúdo base64 até encontrar `=` seguido de linha vazia
4. **Decodificação**: Converte o base64 para texto legível
5. **Exibição (opcional)**: Se `--show-preview` for usado, mostra na tela preview de até 500 caracteres do conteúdo decodificado
6. **Busca**: Procura pelos padrões definidos
7. **Ação**: Se encontrar qualquer padrão, move o arquivo para o diretório destino

### Tratamento de Múltiplos Blocos

O script foi desenvolvido para lidar com e-mails que contêm múltiplos blocos base64 (comum em mensagens com vários anexos ou partes HTML).

## 📤 Saída do Script

```
Processando 5 arquivo(s) em '/path/emails'...

=== Processando: email1.txt ===
  Encontrado(s) 2 bloco(s) base64.

  --- Bloco 1 ---
  Conteúdo decodificado (150 caracteres):
  <html><body><p>Visite nosso site: <a href="http://example.malware-domain2.example.com">...
  
  ✓ PADRÃO ENCONTRADO: '.malware-domain2.example.com'

  → Arquivo movido para: /path/filtered/email1.txt

============================================================
Processamento concluído!
Total de arquivos movidos: 1/5
============================================================
```

## 🔧 Requisitos

- Python 3.x
- Módulos padrão: `sys`, `os`, `base64`, `shutil`, `pathlib`, `argparse`

## ⚠️ Observações

- O diretório de destino é criado automaticamente se não existir
- Arquivos sem blocos base64 não são decodificados, mas ainda podem ser movidos se houver padrão no plaintext
- Arquivos sem padrões encontrados permanecem no diretório original
- O script trata erros de encoding (UTF-8 e Latin-1)
- A lista de padrões é lida do arquivo `filtrar-emails.txt` (linhas vazias e comentários iniciados com `#` são ignorados)

## 📂 Estrutura de E-mail Suportada

O script reconhece e-mails no formato MIME padrão:

```
From: sender@example.com
Subject: Test
Content-Type: multipart/mixed; boundary="xxx"

--xxx
Content-Type: text/html
Content-Transfer-Encoding: base64

[conteúdo base64 aqui]
=

--xxx--
```

## 🧪 Teste

Um arquivo de exemplo foi criado: `exemplo_email.txt`

Para testar:

```bash
# Criar diretórios de teste
mkdir -p test_emails test_filtered

# Copiar exemplo para teste
cp exemplo_email.txt test_emails/

# Executar o script
python3 email_filter.py test_emails test_filtered
```

## 📋 Customização

Para adicionar novos padrões de busca, edite o arquivo `filtrar-emails.txt` (um padrão por linha):

```txt
# Comentários começam com #
.malware-domain1.example.com
.malware-domain2.example.com
.seu-novo-padrao.com
```

## Autor

Renato Monteiro Batista
[https://github.com/renatomb/email-base64-scanner](https://github.com/renatomb/email-base64-scanner)