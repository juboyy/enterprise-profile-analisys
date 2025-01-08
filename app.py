import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
from docx import Document
import os
import tempfile
import re
import io

# Configuração da página Streamlit
st.set_page_config(page_title="Análise de Perfil Comportamental", layout="wide")

# Configuração do tema e estilos
st.markdown("""
<style>
    /* Estilo dos headers */
    h1, h2, h3 {
        margin-bottom: 1rem;
    }
    
    /* Estilo dos tooltips */
    .tooltip {
        position: relative;
        display: inline-block;
        cursor: pointer;
        background-color: #E8F1F5;
        border: 1px solid #1E3D59;
        color: #1E3D59;
        border-radius: 50%;
        width: 20px;
        height: 20px;
        text-align: center;
        line-height: 18px;
        margin: 0 3px;
        font-size: 12px;
    }

    .tooltip .tooltiptext {
        visibility: hidden;
        width: auto;
        min-width: 120px;
        background-color: #1E3D59;
        color: #fff;
        text-align: center;
        border-radius: 6px;
        padding: 8px;
        position: absolute;
        z-index: 1;
        bottom: 125%;
        left: 50%;
        transform: translateX(-50%);
        opacity: 0;
        transition: opacity 0.2s;
    }

    .tooltip:hover .tooltiptext {
        visibility: visible;
        opacity: 1;
    }
    
    /* Estilo das mensagens */
    .chat-message {
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 8px;
        line-height: 1.5;
    }
    
    /* Estilo dos uploads */
    .upload-section {
        padding: 1.5rem;
        background-color: #F7F9FB;
        border-radius: 8px;
        margin: 1rem 0;
    }
    
    /* Estilo da barra lateral */
    .sidebar .stButton>button {
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)

# Configuração da chave API do Gemini
GOOGLE_API_KEY = "AIzaSyDJXaH8-ujeF8mCLqGZHG7tGSXdwkXkofA"
genai.configure(api_key=GOOGLE_API_KEY)

# Configuração do modelo
model = genai.GenerativeModel('gemini-2.0-flash-exp')

def extract_text_with_pages(file_content, file_type):
    """Extrai texto mantendo referência das páginas"""
    text_sections = []
    
    try:
        if file_type == "application/pdf":
            # Processar PDF
            pdf_file = io.BytesIO(file_content)
            pdf_reader = PdfReader(pdf_file)
            for page_num, page in enumerate(pdf_reader.pages, 1):
                text = page.extract_text()
                if text.strip():
                    text_sections.append({
                        'page': f'Página {page_num}',
                        'text': text
                    })
        else:
            # Processar DOCX e TXT
            if file_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                doc = Document(io.BytesIO(file_content))
                paragraphs = [p.text for p in doc.paragraphs]
            else:  # text/plain
                text_content = file_content.decode('utf-8')
                paragraphs = text_content.split('\n')
            
            # Dividir em seções
            current_section = ""
            section_count = 0
            
            for paragraph in paragraphs:
                current_section += paragraph + "\n"
                if len(current_section) >= 500:
                    section_count += 1
                    text_sections.append({
                        'page': f'Seção {section_count}',
                        'text': current_section
                    })
                    current_section = ""
            
            if current_section.strip():
                section_count += 1
                text_sections.append({
                    'page': f'Seção {section_count}',
                    'text': current_section
                })
    
    except Exception as e:
        st.error(f"Erro ao extrair texto: {str(e)}")
        return []
    
    return text_sections

def process_file_with_api(uploaded_file):
    """Processa arquivo usando a API do Gemini"""
    try:
        # Ler o conteúdo do arquivo
        file_content = uploaded_file.getvalue()
        
        # Extrair texto com referências de páginas
        text_sections = extract_text_with_pages(file_content, uploaded_file.type)
        
        # Criar objeto para o Gemini
        file_obj = {
            'mime_type': uploaded_file.type,
            'data': file_content,
            'sections': text_sections,
            'name': uploaded_file.name
        }
        
        return file_obj
            
    except Exception as e:
        st.error(f"Erro ao processar arquivo: {str(e)}")
        return None

def process_response_with_tooltips(response_text, reference_map):
    pattern = r'\[(.*?), (Página/Seção \d+|Página \d+|Seção \d+)\]'
    ref_count = 0
    
    def replace_reference(match):
        nonlocal ref_count
        ref_count += 1
        file_name = match.group(1)
        page_ref = match.group(2)
        
        tooltip = f"""<span class="tooltip">{ref_count}
            <span class="tooltiptext">
            {file_name}<br>
            {page_ref}
            </span>
        </span>"""
        
        return tooltip
    
    processed_text = re.sub(pattern, replace_reference, response_text)
    return processed_text

# Template para análise de perfil
ANALYSIS_TEMPLATE = """
Você é um analista especializado em comportamento empresarial e inteligência emocional.
Use o conhecimento da metodologia fornecida para analisar o perfil do cliente.

IMPORTANTE: Para cada informação ou conclusão relevante, cite a fonte usando o formato [Nome do Arquivo, Página/Seção X].

====================
METODOLOGIA E CONTEXTO:
====================
{methodology_context}

====================
PERFIL DO CLIENTE:
====================
{user_context}

====================
SOLICITAÇÃO DE ANÁLISE:
====================
{prompt}

Por favor, forneça uma análise estruturada considerando:
1. Principais características comportamentais (cite as páginas/seções que fundamentam cada característica)
2. Pontos fortes em inteligência emocional (cite as páginas/seções que fundamentam cada ponto)
3. Áreas para desenvolvimento (cite as páginas/seções que fundamentam cada área)
4. Recomendações práticas (baseadas nas metodologias citadas)

IMPORTANTE: 
- Cite SEMPRE a fonte específica (arquivo e página/seção) que fundamenta cada ponto da sua análise
- Use o formato [Nome do Arquivo, Página/Seção X] para todas as citações
- Baseie suas conclusões apenas nos documentos fornecidos
- Mantenha a análise objetiva e fundamentada
"""

# Interface principal
st.title("Análise de Perfil Comportamental")
st.markdown("### Sistema de Análise Comportamental e Inteligência Emocional")

# Inicialização do histórico de chat e referências na sessão
if "messages" not in st.session_state:
    st.session_state.messages = []
if "reference_map" not in st.session_state:
    st.session_state.reference_map = {}
if "methodology_files" not in st.session_state:
    st.session_state.methodology_files = []

# Barra lateral para upload dos documentos de metodologia
with st.sidebar:
    st.header("Metodologia de Análise")
    st.markdown("""
    #### Documentos Necessários:
    - 📊 Diretrizes de comportamento empresarial
    - 🧠 Metodologia de análise comportamental
    - 💡 Frameworks de inteligência emocional
    """)
    
    methodology_files = st.file_uploader(
        "Carregar Documentos de Metodologia", 
        type=["pdf", "docx", "txt"], 
        accept_multiple_files=True
    )
    
    if methodology_files:
        with st.spinner("Processando documentos de metodologia..."):
            processed_files = []
            for file in methodology_files:
                file_obj = process_file_with_api(file)
                if file_obj:
                    processed_files.append(file_obj)
            
            if processed_files:
                st.session_state.methodology_files = processed_files
                st.success("✅ Metodologia atualizada com sucesso!")

# Upload do perfil do cliente
st.header("📄 Perfil do Cliente")
st.markdown("Faça upload do documento contendo o perfil do cliente a ser analisado.")

user_file = st.file_uploader("Carregar Perfil do Cliente", type=["pdf", "docx", "txt"])
if user_file:
    with st.spinner("Processando perfil do cliente..."):
        user_file_obj = process_file_with_api(user_file)
        if user_file_obj:
            st.session_state.user_file = user_file_obj
            st.success(f"✅ Perfil '{user_file.name}' processado com sucesso!")

# Interface de chat
st.header("💬 Análise e Insights")
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message["role"] == "assistant":
            st.markdown(process_response_with_tooltips(message["content"], st.session_state.reference_map), unsafe_allow_html=True)
        else:
            st.markdown(message["content"])

if prompt := st.chat_input("Digite sua solicitação de análise..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Verificar se temos os arquivos necessários
    if st.session_state.methodology_files and hasattr(st.session_state, 'user_file'):
        try:
            # Preparar contexto estruturado
            methodology_context = ""
            for file_obj in st.session_state.methodology_files:
                methodology_context += f"\n### {file_obj['name']}\n"
                for section in file_obj['sections']:
                    methodology_context += f"[{file_obj['name']}, {section['page']}]\n{section['text']}\n\n"
            
            user_context = f"\n### {st.session_state.user_file['name']}\n"
            for section in st.session_state.user_file['sections']:
                user_context += f"[{st.session_state.user_file['name']}, {section['page']}]\n{section['text']}\n\n"
            
            # Preparar prompt completo
            full_prompt = ANALYSIS_TEMPLATE.format(
                methodology_context=methodology_context,
                user_context=user_context,
                prompt=prompt
            )
            
            # Gerar resposta com streaming
            with st.chat_message("assistant"):
                response_placeholder = st.empty()
                full_response = ""
                
                # Incluir arquivos e prompt estruturado
                message = [
                    *[{'mime_type': f['mime_type'], 'data': f['data']} for f in st.session_state.methodology_files],
                    {'mime_type': st.session_state.user_file['mime_type'], 'data': st.session_state.user_file['data']},
                    full_prompt
                ]
                
                # Gerar resposta
                for chunk in model.generate_content(
                    message,
                    stream=True,
                    generation_config={
                        "max_output_tokens": 2000,
                        "temperature": 0.5,
                        "top_p": 0.8,
                        "top_k": 40
                    }
                ):
                    if chunk.text:
                        full_response += chunk.text
                        processed_response = process_response_with_tooltips(full_response, st.session_state.reference_map)
                        response_placeholder.markdown(processed_response, unsafe_allow_html=True)
                
                st.session_state.messages.append({"role": "assistant", "content": full_response})
                
        except Exception as e:
            st.error(f"Erro ao gerar resposta: {str(e)}")
    else:
        st.warning("Por favor, carregue os documentos de metodologia e o perfil do cliente antes de fazer perguntas.") 