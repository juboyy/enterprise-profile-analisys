import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
from docx import Document
import os
import tempfile
import re

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
GOOGLE_API_KEY = "AIzaSyAhM39a9f_53uqs9qGXgEWMqDA_hgpetSU"
genai.configure(api_key=GOOGLE_API_KEY)

# Configuração do modelo
model = genai.GenerativeModel('gemini-2.0-flash-exp')

def extract_text_from_pdf(pdf_file):
    pdf_reader = PdfReader(pdf_file)
    text_by_page = []
    for page_num, page in enumerate(pdf_reader.pages, 1):
        text = page.extract_text()
        if text.strip():
            text_by_page.append({
                'page': page_num,
                'text': text
            })
    return text_by_page

def extract_text_from_docx(docx_file):
    doc = Document(docx_file)
    text_by_section = []
    current_section = ""
    section_count = 0
    
    for paragraph in doc.paragraphs:
        current_section += paragraph.text + "\n"
        if len(current_section) >= 500:
            section_count += 1
            text_by_section.append({
                'page': f'Seção {section_count}',
                'text': current_section
            })
            current_section = ""
    
    if current_section.strip():
        section_count += 1
        text_by_section.append({
            'page': f'Seção {section_count}',
            'text': current_section
        })
    
    return text_by_section

def extract_text_from_txt(txt_file):
    content = txt_file.getvalue().decode('utf-8')
    text_by_section = []
    lines = content.split('\n')
    current_section = ""
    section_count = 0
    
    for line in lines:
        current_section += line + "\n"
        if len(current_section) >= 500:
            section_count += 1
            text_by_section.append({
                'page': f'Seção {section_count}',
                'text': current_section
            })
            current_section = ""
    
    if current_section.strip():
        section_count += 1
        text_by_section.append({
            'page': f'Seção {section_count}',
            'text': current_section
        })
    
    return text_by_section

def process_file(uploaded_file):
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        tmp_file_path = tmp_file.name

    try:
        if uploaded_file.type == "application/pdf":
            text_sections = extract_text_from_pdf(tmp_file_path)
        elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            text_sections = extract_text_from_docx(tmp_file_path)
        elif uploaded_file.type == "text/plain":
            text_sections = extract_text_from_txt(uploaded_file)
        else:
            text_sections = [{'page': 'N/A', 'text': "Formato de arquivo não suportado"}]
    finally:
        os.unlink(tmp_file_path)
    
    return text_sections

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

Metodologia e Contexto de Análise:
{system_context}

Perfil do Cliente para Análise:
{user_context}

Solicitação de Análise:
{prompt}


Lembre-se: SEMPRE cite as fontes específicas (arquivo e página/seção) que fundamentam cada ponto da sua análise.
"""

# Interface principal
st.title("Análise de Perfil Comportamental")
st.markdown("### Sistema de Análise Comportamental e Inteligência Emocional")

# Inicialização do histórico de chat e referências na sessão
if "messages" not in st.session_state:
    st.session_state.messages = []
if "reference_map" not in st.session_state:
    st.session_state.reference_map = {}

# Carregamento do contexto base (documentos de metodologia)
if "system_context" not in st.session_state:
    st.session_state.system_context = ""
    st.info("Por favor, carregue os documentos de metodologia na barra lateral.")

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
            system_context = ""
            reference_map = {}
            for file in methodology_files:
                text_sections = process_file(file)
                for section in text_sections:
                    ref_key = f"{file.name}, Página/Seção {section['page']}"
                    reference_map[ref_key] = section['text']
                    system_context += f"\n### Documento: {file.name}\n[{ref_key}]\n{section['text']}\n"
            
            st.session_state.system_context = system_context
            st.session_state.reference_map.update(reference_map)
            st.success("✅ Metodologia atualizada com sucesso!")

# Upload do perfil do cliente
st.header("📄 Perfil do Cliente")
st.markdown("Faça upload do documento contendo o perfil do cliente a ser analisado.")

user_file = st.file_uploader("Carregar Perfil do Cliente", type=["pdf", "docx", "txt"])
if user_file:
    with st.spinner("Processando perfil do cliente..."):
        text_sections = process_file(user_file)
        user_context = f"### Documento: {user_file.name}\n"
        for section in text_sections:
            ref_key = f"{user_file.name}, Página/Seção {section['page']}"
            st.session_state.reference_map[ref_key] = section['text']
            user_context += f"\n[{ref_key}]\n{section['text']}\n"
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

    # Preparar o contexto completo para o Gemini usando o template
    full_context = ANALYSIS_TEMPLATE.format(
        system_context=st.session_state.system_context,
        user_context=user_context if 'user_context' in locals() else 'Nenhum perfil carregado',
        prompt=prompt
    )

    # Gerar resposta com streaming
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        
        # Gerar resposta em streaming
        for chunk in model.generate_content(full_context, stream=True):
            if chunk.text:
                full_response += chunk.text
                # Atualizar a resposta com tooltips em tempo real
                processed_response = process_response_with_tooltips(full_response, st.session_state.reference_map)
                response_placeholder.markdown(processed_response, unsafe_allow_html=True)
        
        # Armazenar a resposta completa no histórico
        st.session_state.messages.append({"role": "assistant", "content": full_response}) 