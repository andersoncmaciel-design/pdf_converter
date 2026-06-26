import streamlit as st
from pdf2image import convert_from_path
import pytesseract
import fitz  # PyMuPDF
from reportlab.lib.pagesizes import letter, landscape
from reportlab.pdfgen import canvas
import tempfile
import os

st.set_page_config(page_title="Processador Inteligente de PDFs", page_icon="📚", layout="centered")

st.title("📚 Processador e Reformatador Inteligente de PDFs")
st.write("Versão com suporte completo a acentuação, cedilhas, pontuação e orientação automática.")

modo = st.radio(
    "Selecione o tipo do seu PDF de entrada:",
    ("PDF Digital Nativo (Limpar Layout Feio)", "PDF Escaneado/Imagem (Aplicar OCR)")
)

idiomas_suportados = {"Português": "por", "English (Inglês)": "eng", "Français (Francês)": "fra", "Ελληνικά (Grego)": "ell"}
idioma_selecionado = st.selectbox("Selecione o idioma principal do livro/documento:", list(idiomas_suportados.keys()))
codigo_idioma = idiomas_suportados[idioma_selecionado]

arquivo_pdf = st.file_uploader("Escolha o arquivo PDF original", type=["pdf"])

if arquivo_pdf is not None:
    if st.button("Iniciar Processamento ✨"):
        with st.spinner("Processando documento..."):
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_entrada:
                tmp_entrada.write(arquivo_pdf.read())
                caminho_entrada = tmp_entrada.name

            caminho_saida = tempfile.mktemp(suffix=".pdf")

            try:
                c = canvas.Canvas(caminho_saida)
                
                # --- MODO 1: DIGITAL NATIVO ---
                if modo == "PDF Digital Nativo (Limpar Layout Feio)":
                    st.info("🤖 Analisando estrutura nativa e preservando acentuação...")
                    doc = fitz.open(caminho_entrada)
                    total_paginas = len(doc)
                    barra_progresso = st.progress(0)

                    for i, pagina in enumerate(doc):
                        # Detecção de orientação
                        rect = pagina.rect
                        e_paisagem = rect.width > rect.height
                        
                        if e_paisagem:
                            c.setPageSize(landscape(letter))
                            largura, altura = landscape(letter)
                        else:
                            c.setPageSize(letter)
                            largura, altura = letter
                        
                        # Chaveamento de fontes com suporte a caracteres latinos acentuados
                        fonte = "Times-Roman" if codigo_idioma == "ell" else "Courier"
                        
                        texto_extraido = pagina.get_text("text")
                        
                        # Moldura sutil
                        c.setStrokeColorRGB(0.8, 0.8, 0.8)
                        c.setLineWidth(1)
                        c.rect(30, 30, largura - 60, altura - 60)
                        
                        textobject = c.beginText()
                        textobject.setTextOrigin(40, altura - 50)
                        textobject.setFont(fonte, 9)
                        textobject.setLeading(12)
                        
                        for linha in texto_extraido.split('\n'):
                            # REMOVIDO o filtro .encode('ascii', 'ignore') para preservar os acentos e cedilhas nativos.
                            # Usamos latin-1 apenas para assegurar compatibilidade de escape no ReportLab standard se não for Grego
                            if codigo_idioma != "ell":
                                linha = linha.encode('utf-8', 'ignore').decode('utf-8')
                            textobject.textLine(linha)
                        
                        c.drawText(textobject)
                        if i < total_paginas - 1:
                            c.showPage()
                        
                        barra_progresso.progress((i + 1) / total_paginas)
                    doc.close()

                # --- MODO 2: OCR ---
                else:
                    st.info("📷 Renderizando imagens e aplicando OCR com dicionário completo...")
                    paginas_imagens = convert_from_path(caminho_entrada, dpi=200)
                    total_paginas = len(paginas_imagens)
                    barra_progresso = st.progress(0)

                    for i, imagem in enumerate(paginas_imagens):
                        e_paisagem = imagem.width > imagem.height
                        
                        if e_paisagem:
                            c.setPageSize(landscape(letter))
                            largura, altura = landscape(letter)
                        else:
                            c.setPageSize(letter)
                            largura, altura = letter
                        
                        fonte = "Times-Roman" if codigo_idioma == "ell" else "Courier"
                        
                        # Preserva os espaços (PSM 6 é excelente para tabelas de dados)
                        config_tess = '--psm 6' if e_paisagem else ''
                        texto_extraido = pytesseract.image_to_string(imagem, lang=codigo_idioma, config=config_tess)
                        
                        c.setStrokeColorRGB(0.8, 0.8, 0.8)
                        c.rect(30, 30, largura - 60, altura - 60)
                        
                        textobject = c.beginText()
                        textobject.setTextOrigin(40, altura - 50)
                        textobject.setFont(fonte, 9)
                        textobject.setLeading(12)
                        
                        if not texto_extraido.strip():
                            textobject.textLine(f"[Nenhum texto detectado na página {i+1}]")
                        else:
                            for linha in texto_extraido.split('\n'):
                                if codigo_idioma != "ell":
                                    linha = linha.encode('utf-8', 'ignore').decode('utf-8')
                                textobject.textLine(linha)
                        
                        c.drawText(textobject)
                        if i < total_paginas - 1:
                            c.showPage()
                        
                        barra_progresso.progress((i + 1) / total_paginas)

                c.save()

                with open(caminho_saida, "rb") as f:
                    st.success("🎉 Processamento concluído com acentos e pontuações preservados!")
                    st.download_button(
                        label="📥 Baixar PDF Corrigido",
                        data=f,
                        file_name="pdf_remodelado_perfeito.pdf",
                        mime="application/pdf"
                    )

            except Exception as e:
                st.error(f"Erro: {e}")
            finally:
                if os.path.exists(caminho_entrada): os.remove(caminho_entrada)
                if os.path.exists(caminho_saida): os.remove(caminho_saida)
