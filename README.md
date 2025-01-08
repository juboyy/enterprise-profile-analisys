# Análise de Perfil Comportamental e Inteligência Emocional

Este é um aplicativo Streamlit que utiliza o Google Gemini como LLM para realizar análises comportamentais e de inteligência emocional de perfis de clientes, baseado em metodologias e frameworks específicos.

## Propósito

O aplicativo foi desenvolvido para auxiliar analistas a:
- Analisar perfis de clientes de forma rápida e consistente
- Utilizar metodologias específicas de comportamento empresarial
- Gerar insights baseados em inteligência emocional
- Produzir recomendações práticas e acionáveis

## Requisitos

- Python 3.8 ou superior
- pip (gerenciador de pacotes Python)

## Instalação

1. Clone este repositório
2. Instale as dependências:
```bash
pip install -r requirements.txt
```

## Uso

1. Execute o aplicativo:
```bash
streamlit run app.py
```

2. No navegador:
   - Carregue os documentos de metodologia na barra lateral (PDF, DOCX, TXT)
   - Faça upload do perfil do cliente a ser analisado
   - Faça solicitações de análise específicas no chat

## Funcionalidades

- Upload de documentos de metodologia (PDF, DOCX, TXT)
- Processamento de perfis de clientes
- Interface de chat interativa
- Análise estruturada considerando:
  - Características comportamentais
  - Pontos fortes em inteligência emocional
  - Áreas para desenvolvimento
  - Recomendações práticas

## Observações

- A chave API do Google Gemini já está configurada no código
- O aplicativo suporta arquivos PDF, DOCX e TXT
- Os documentos de metodologia persistem durante a sessão
- As análises são baseadas no contexto fornecido pelos documentos de metodologia 