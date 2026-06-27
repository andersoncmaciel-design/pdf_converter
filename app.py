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
                
                # --- MODO 1: DIGITAL NATIVO (COM SUPORTE A FONTES UNICODE/GREGO) ---
                if modo == "PDF Digital Nativo (Limpar Layout Feio)":
                    st.info("🤖 Analisando estrutura nativa (Processamento Unicode Avançado)...")
                    
                    # 1. REGISTRAR FONTE UNICODE EXTERNA (Crucial para Grego)
                    # Tentamos carregar uma fonte que suporte caracteres não-latinos.
                    # Se você rodar localmente no Windows, pode usar 'arial.ttf'. 
                    # Na nuvem (Linux), usaremos uma fonte padrão do sistema ou uma baixada na mesma pasta.
                    from reportlab.pdfbase import pdfmetrics
                    from reportlab.pdfbase.ttfonts import TTFont
                    
                    try:
                        # Se você colocar o arquivo 'DejaVuSans.ttf' ou 'Arial.ttf' na mesma pasta do script, ele usa aqui.
                        # Caso contrário, tentará buscar no sistema operacional.
                        pdfmetrics.registerFont(TTFont('UnicodeFont', 'DejaVuSans.ttf'))
                        fonte_final = 'UnicodeFont'
                    except:
                        # Fallback seguro caso não ache a fonte externa (avisa na interface)
                        st.warning("⚠️ Nota: Para renderizar o Grego perfeitamente na nuvem, adicione o arquivo 'DejaVuSans.ttf' na pasta do projeto.")
                        fonte_final = "Times-Roman" if codigo_idioma == "ell" else "Courier"

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
                        
                        # Moldura sutil
                        c.setStrokeColorRGB(0.8, 0.8, 0.8)
                        c.rect(30, 30, largura - 60, altura - 60)
                        
                        textobject = c.beginText()
                        textobject.setTextOrigin(40, altura - 50)
                        textobject.setFont(fonte_final, 9)
                        textobject.setLeading(14) # Aumentado o espaçamento para melhor leitura de parágrafos
                        
                        # MUDANÇA CHAVE: Extração por blocos estruturados (limpa o OCR quebrado de fundo)
                        blocos = pagina.get_text("blocks")
                        # Ordena os blocos de cima para baixo, da esquerda para a direita
                        blocos.sort(key=lambda b: (b[1], b[0])) 
                        
                        for bloco in blocos:
                            texto_bloco = bloco[4] # O texto bruto do parágrafo fica na posição 4
                            
                            for linha in texto_bloco.split('\n'):
                                if linha.strip():
                                    # Para o Grego rodar perfeitamente, NUNCA mude para ascii
                                    textobject.textLine(linha.strip())
                        
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
