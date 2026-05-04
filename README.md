# Email Filter Script - Filtro de E-mails por Base64

Script Python para processar arquivos de e-mail em formato texto, decodificar blocos base64 e filtrar mensagens com base em padrões específicos.

## 📋 Funcionalidades

- ✅ Processa todos os arquivos em um diretório
- ✅ Detecta blocos `Content-Transfer-Encoding: base64` em e-mails
- ✅ Extrai e decodifica múltiplos blocos base64 por arquivo
- ✅ Exibe o conteúdo decodificado na tela
- ✅ Procura por padrões específicos no conteúdo decodificado
- ✅ Move automaticamente arquivos que contêm os padrões para diretório de destino

## 🎯 Padrões de Busca

O script procura por estes padrões no conteúdo base64 decodificado:

1. `.malware-domain1.example.com`
2. `.malware-domain2.example.com`

## 🚀 Como Usar

### Sintaxe

```bash
python3 email_filter.py <diretorio_origem> <diretorio_destino>
```

### Parâmetros

- **`<diretorio_origem>`**: Diretório contendo os arquivos de e-mail a serem processados
- **`<diretorio_destino>`**: Diretório para onde os arquivos filtrados serão movidos

### Exemplos

```bash
# Exemplo básico
python3 email_filter.py /var/mail/inbox /var/mail/filtered

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
5. **Exibição**: Mostra na tela o conteúdo decodificado (preview de 500 caracteres)
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
- Módulos padrão: `sys`, `os`, `base64`, `shutil`, `pathlib`

## ⚠️ Observações

- O diretório de destino é criado automaticamente se não existir
- Arquivos sem blocos base64 são ignorados
- Arquivos sem padrões encontrados permanecem no diretório original
- O script trata erros de encoding (UTF-8 e Latin-1)

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

Para adicionar novos padrões de busca, edite a lista `search_patterns` na função `process_email_files()`:

```python
search_patterns = [
    '.malware-domain1.example.com',
    '.malware-domain2.example.com',
    '.seu-novo-padrao.com'  # Adicione aqui
]
```
