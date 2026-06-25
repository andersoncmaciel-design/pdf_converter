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
st.write("Ajustado para detectar automaticamente páginas em Paisagem (Tabelas/Pautas) e Retrato.")

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
                    st.info("🤖 Analisando estrutura nativa...")
                    doc = fitz.open(caminho_entrada)
                    total_paginas = len(doc)
                    barra_progresso = st.progress(0)

                    for i, pagina in enumerate(doc):
                        # 1. DETECÇÃO DE ORIENTAÇÃO
                        # Pega a largura e altura originais da página
                        rect = pagina.rect
                        e_paisagem = rect.width > rect.height
                        
                        if e_paisagem:
                            c.setPageSize(landscape(letter))
                            largura, altura = landscape(letter)
                        else:
                            c.setPageSize(letter)
                            largura, altura = letter
                        
                        # Usa Courier para tabelas (mantém colunas retas) ou Helvetica/Times para textos normais
                        fonte = "Times-Roman" if codigo_idioma == "ell" else "Courier"
                        
                        texto_extraido = pagina.get_text("text")
                        
                        # Desenha uma moldura sutil para simular o formulário gráfico
                        c.setStrokeColorRGB(0.8, 0.8, 0.8) # Cinza claro
                        c.setLineWidth(1)
                        c.rect(30, 30, largura - 60, altura - 60) # Linha de borda externa
                        
                        textobject = c.beginText()
                        textobject.setTextOrigin(40, altura - 50)
                        textobject.setFont(fonte, 9) # Fonte ligeiramente menor para caber pautas largas
                        textobject.setLeading(12)
                        
                        for linha in texto_extraido.split('\n'):
                            if codigo_idioma != "ell":
                                linha = linha.encode('ascii', 'ignore').decode('ascii')
                            textobject.textLine(linha)
                        
                        c.drawText(textobject)
                        if i < total_paginas - 1:
                            c.showPage()
                        
                        barra_progresso.progress((i + 1) / total_paginas)
                    doc.close()

                # --- MODO 2: OCR ---
                else:
                    st.info("📷 Renderizando imagens e aplicando OCR...")
                    paginas_imagens = convert_from_path(caminho_entrada, dpi=200)
                    total_paginas = len(paginas_imagens)
                    barra_progresso = st.progress(0)

                    for i, imagem in enumerate(paginas_imagens):
                        # 1. DETECÇÃO DE ORIENTAÇÃO NA IMAGEM
                        e_paisagem = imagem.width > imagem.height
                        
                        if e_paisagem:
                            c.setPageSize(landscape(letter))
                            largura, altura = landscape(letter)
                        else:
                            c.setPageSize(letter)
                            largura, altura = letter
                        
                        fonte = "Times-Roman" if codigo_idioma == "ell" else "Courier"
                        
                        # Preserva espaços em branco para tabelas no OCR
                        config_tess = '--psm 6' if e_paisagem else ''
                        texto_extraido = pytesseract.image_to_string(imagem, lang=codigo_idioma, config=config_tess)
                        
                        # Linha divisória de margem externa
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
                                    linha = linha.encode('ascii', 'ignore').decode('ascii')
                                textobject.textLine(linha)
                        
                        c.drawText(textobject)
                        if i < total_paginas - 1:
                            c.showPage()
                        
                        barra_progresso.progress((i + 1) / total_paginas)

                c.save()

                with open(caminho_saida, "rb") as f:
                    st.success("🎉 Processamento concluído com layout ajustado!")
                    st.download_button(
                        label="📥 Baixar PDF Corrigido",
                        data=f,
                        file_name="pdf_remodelado_alinhado.pdf",
                        mime="application/pdf"
                    )

            except Exception as e:
                st.error(f"Erro: {e}")
            finally:
                if os.path.exists(caminho_entrada): os.remove(caminho_entrada)
                if os.path.exists(caminho_saida): os.remove(caminho_saida)
