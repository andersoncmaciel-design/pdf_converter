import streamlit as st
from pdf2image import convert_from_path
import pytesseract
import fitz  # PyMuPDF (Para extração direta de texto)
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import tempfile
import os

# Configuração da página Web
st.set_page_config(page_title="Processador Inteligente de PDFs", page_icon="📚", layout="centered")

st.title("📚 Processador e Reformatador Inteligente de PDFs")
st.write("Escolha o modo ideal para o seu arquivo: extrair texto de páginas escaneadas ou limpar o layout de um PDF que já possui texto digital.")

# --- SELEÇÃO DO MODO DE OPERAÇÃO ---
modo = st.radio(
    "Selecione o tipo do seu PDF de entrada:",
    ("PDF Digital Nativo (Limpar Layout Feio)", "PDF Escaneado/Imagem (Aplicar OCR)")
)

# --- MAPEAMENTO DE IDIOMAS ---
idiomas_suportados = {
    "Português": "por",
    "English (Inglês)": "eng",
    "Français (Francês)": "fra",
    "Ελληνικά (Grego)": "ell"
}

idioma_selecionado = st.selectbox("Selecione o idioma principal do livro:", list(idiomas_suportados.keys()))
codigo_idioma = idiomas_suportados[idioma_selecionado]

# Upload do arquivo
arquivo_pdf = st.file_uploader("Escolha o arquivo PDF original", type=["pdf"])

if arquivo_pdf is not None:
    if st.button("Iniciar Processamento ✨"):
        with st.spinner("Processando o documento... Por favor, aguarde."):
            
            # Criar arquivos temporários para manipulação segura no servidor
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_entrada:
                tmp_entrada.write(arquivo_pdf.read())
                caminho_entrada = tmp_entrada.name

            caminho_saida = tempfile.mktemp(suffix=".pdf")

            try:
                # Configurações iniciais do PDF de destino limpo
                c = canvas.Canvas(caminho_saida, pagesize=letter)
                largura, altura = letter
                
                # Chaveamento de fonte: Helvetica nativa não suporta o alfabeto Grego
                fonte = "Helvetica" if codigo_idioma != "ell" else "Times-Roman"
                
                # --- MODO 1: LIMPEZA DE LAYOUT (PDF DIGITAL NATIVO) ---
                if modo == "PDF Digital Nativo (Limpar Layout Feio)":
                    st.info("🤖 Modo Digital Ativo: Extraindo texto limpo nativo eletronicamente...")
                    doc = fitz.open(caminho_entrada)
                    total_paginas = len(doc)
                    barra_progresso = st.progress(0)

                    for i, pagina in enumerate(doc):
                        # Extrai o texto digital mantendo blocos básicos
                        texto_extraido = pagina.get_text("text")
                        
                        textobject = c.beginText()
                        textobject.setTextOrigin(50, altura - 50)
                        textobject.setFont(fonte, 11)
                        textobject.setLeading(14)
                        
                        for linha in texto_extraido.split('\n'):
                            if codigo_idioma != "ell":
                                linha = linha.encode('ascii', 'ignore').decode('ascii')
                            textobject.textLine(linha.strip())
                        
                        c.drawText(textobject)
                        if i < total_paginas - 1:
                            c.showPage()
                        
                        barra_progresso.progress((i + 1) / total_paginas)
                    
                    doc.close()

                # --- MODO 2: PROCESSAMENTO OCR (PDF IMAGEM) ---
                else:
                    st.info("📷 Modo OCR Ativo: Renderizando páginas e aplicando reconhecimento óptico...")
                    # Converte em 200 DPI para balancear qualidade e economia de memória RAM
                    paginas_imagens = convert_from_path(caminho_entrada, dpi=200)
                    total_paginas = len(paginas_imagens)
                    barra_progresso = st.progress(0)

                    for i, imagem in enumerate(paginas_imagens):
                        texto_extraido = pytesseract.image_to_string(imagem, lang=codigo_idioma)
                        
                        textobject = c.beginText()
                        textobject.setTextOrigin(50, altura - 50)
                        textobject.setFont(fonte, 11)
                        textobject.setLeading(14)
                        
                        for linha in texto_extraido.split('\n'):
                            if codigo_idioma != "ell":
                                linha = linha.encode('ascii', 'ignore').decode('ascii')
                            textobject.textLine(linha)
                        
                        c.drawText(textobject)
                        if i < total_paginas - 1:
                            c.showPage()
                        
                        barra_progresso.progress((i + 1) / total_paginas)

                # Salva o PDF remodelado e limpo
                c.save()

                # Disponibiliza o botão para download
                with open(caminho_saida, "rb") as f:
                    st.success("🎉 O seu PDF foi totalmente remodelado com sucesso!")
                    st.download_button(
                        label="📥 Baixar PDF com Layout Limpo",
                        data=f,
                        file_name="pdf_remodelado_limpo.pdf",
                        mime="application/pdf"
                    )

            except Exception as e:
                st.error(f"Ocorreu um erro inesperado: {e}")
                st.info("Lembrete: Garanta que todas as dependências de idioma do Tesseract estão operantes no servidor.")
            
            finally:
                # Remove os arquivos temporários criados para evitar consumo de disco rígido
                if os.path.exists(caminho_entrada): os.remove(caminho_entrada)
                if os.path.exists(caminho_saida): os.remove(caminho_saida)
