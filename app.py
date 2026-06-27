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

st.set_page_config(page_title="Processador Inteligente de PDFs", page_icon="📚", layout="centered")

st.title("📚 Processador e Reformatador Inteligente de PDFs")
st.write("Versão Híbrida Estabilizada com Tratamento de Fontes Universais.")

# --- FUNÇÃO CORRIGIDA DE CHECAGEM DE FONTE UNICODE ---
def obter_fonte_apropriada(codigo_idioma):
    """Retorna uma fonte válida registrada ou uma fonte padrão segura do sistema"""
    if codigo_idioma != "ell":
        return "Courier" # Padrão excelente para manter o alinhamento de tabelas latinas
        
    # Se for Grego, tentamos mapear caminhos reais de fontes Unicode do sistema
    caminhos_fontes = [
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "C:\\Windows\\Fonts\\arial.ttf" # Windows Local
    ]
    
    for caminho in caminhos_fontes:
        if os.path.exists(caminho):
            try:
                # Registra dinamicamente com um nome único para evitar conflitos
                pdfmetrics.registerFont(TTFont('SistemaUnicode', caminho))
                return 'SistemaUnicode'
            except:
                continue
                
    # Se o servidor não tiver nenhuma fonte instalada no sistema, usa o fallback padrão do ReportLab
    return "Times-Roman"

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
                
                # Obtém a fonte de forma dinâmica e segura baseada no idioma selecionado
                fonte_aplicada = obter_fonte_apropriada(codigo_idioma)
                
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
                    st.success("🎉 Processamento concluído com estabilização tipográfica!")
                    st.download_button(
                        label="📥 Baixar PDF Corrigido",
                        data=f,
                        file_name="pdf_remodelado_final.pdf",
                        mime="application/pdf"
                    )

            except Exception as e:
                st.error(f"Erro interno no processamento: {e}")
            finally:
                if os.path.exists(caminho_entrada): os.remove(caminho_entrada)
                if os.path.exists(caminho_saida): os.remove(caminho_saida)
