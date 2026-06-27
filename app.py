import streamlit as st
from pdf2image import convert_from_path
import pytesseract
import fitz  # PyMuPDF
from reportlab.lib.pagesizes import letter, landscape
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import tempfile
import os
import urllib.request

st.set_page_config(page_title="Processador Inteligente de PDFs", page_icon="📚", layout="centered")

st.title("📚 Processador e Reformatador Inteligente de PDFs")
st.write("Versão Híbrida Profissional com Suporte Automatizado a Fontes Gregas e Internacionais.")

# --- FUNÇÃO PARA INSTALAR A FONTE GREGA AUTOMATICAMENTE ---
@st.cache_resource
def baixar_e_registrar_fonte_unicode():
    """Baixa a fonte DejaVuSans (suporta Grego, Acentos e Símbolos) e registra no sistema"""
    nome_fonte = "DejaVuSans.ttf"
    # URL confiável da fonte open-source DejaVu Sans
    url_fonte = "https://github.com/matthieam/reportlab/raw/master/src/reportlab/fonts/DejaVuSans.ttf"
    
    if not os.path.exists(nome_fonte):
        try:
            with st.spinner("📥 Instalando suporte a caracteres internacionais/grego no servidor..."):
                urllib.request.urlretrieve(url_fonte, nome_fonte)
        except Exception as e:
            st.error(f"Erro ao baixar fonte internacional: {e}")
            return "Helvetica" # Fallback se falhar a internet
            
    try:
        pdfmetrics.registerFont(TTFont('DejaVuSans', nome_fonte))
        return 'DejaVuSans'
    except Exception as e:
        return "Helvetica"

# Garante que a fonte está pronta para o ReportLab usar
FONTE_UNICODE = baixar_e_registrar_fonte_unicode()

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
                
                # Definir a fonte base com base no idioma (Tabelas latinas usam Courier, Grego usa DejaVu)
                fonte_aplicada = FONTE_UNICODE if codigo_idioma == "ell" else "Courier"
                
                # --- MODO 1: DIGITAL NATIVO ---
                if modo == "PDF Digital Nativo (Limpar Layout Feio)":
                    st.info("🤖 Organizando blocos de parágrafos nativos...")
                    doc = fitz.open(caminho_entrada)
                    total_paginas = len(doc)
                    barra_progresso = st.progress(0)

                    for i, pagina in enumerate(doc):
                        rect = pagina.rect
                        e_paisagem = rect.width > rect.height
                        
                        if e_paisagem:
                            c.setPageSize(landscape(letter))
                            largura, altura = landscape(letter)
                        else:
                            c.setPageSize(letter)
                            largura, altura = letter
                        
                        c.setStrokeColorRGB(0.8, 0.8, 0.8)
                        c.rect(30, 30, largura - 60, altura - 60)
                        
                        textobject = c.beginText()
                        textobject.setTextOrigin(40, altura - 50)
                        textobject.setFont(fonte_aplicada, 9)
                        textobject.setLeading(14)
                        
                        # Extração inteligente por blocos de texto (corrige as quebras do OCR antigo)
                        blocos = pagina.get_text("blocks")
                        blocos.sort(key=lambda b: (b[1], b[0])) 
                        
                        for bloco in blocos:
                            texto_bloco = bloco[4]
                            for linha in texto_bloco.split('\n'):
                                if linha.strip():
                                    textobject.textLine(linha.strip())
                        
                        c.drawText(textobject)
                        if i < total_paginas - 1:
                            c.showPage()
                        
                        barra_progresso.progress((i + 1) / total_paginas)
                    doc.close()

                # --- MODO 2: OCR ---
                else:
                    st.info("📷 Executando reconhecimento óptico avançado...")
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
                        
                        config_tess = '--psm 6' if e_paisagem else ''
                        texto_extraido = pytesseract.image_to_string(imagem, lang=codigo_idioma, config=config_tess)
                        
                        c.setStrokeColorRGB(0.8, 0.8, 0.8)
                        c.rect(30, 30, largura - 60, altura - 60)
                        
                        textobject = c.beginText()
                        textobject.setTextOrigin(40, altura - 50)
                        textobject.setFont(fonte_aplicada, 9)
                        textobject.setLeading(13)
                        
                        if not texto_extraido.strip():
                            textobject.textLine(f"[Nenhum texto detectado na página {i+1}]")
                        else:
                            for linha in texto_extraido.split('\n'):
                                if linha.strip():
                                    textobject.textLine(linha.strip())
                        
                        c.drawText(textobject)
                        if i < total_paginas - 1:
                            c.showPage()
                        
                        barra_progresso.progress((i + 1) / total_paginas)

                c.save()

                with open(caminho_saida, "rb") as f:
                    st.success("🎉 Processamento concluído com tipografia Unicode ajustada!")
                    st.download_button(
                        label="📥 Baixar PDF Corrigido",
                        data=f,
                        file_name="pdf_remodelado_final.pdf",
                        mime="application/pdf"
                    )

            except Exception as e:
                st.error(f"Erro: {e}")
            finally:
                if os.path.exists(caminho_entrada): os.remove(caminho_entrada)
                if os.path.exists(caminho_saida): os.remove(caminho_saida)
