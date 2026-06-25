import streamlit as st
from pdf2image import convert_from_path
import pytesseract
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import tempfile
import os

# Configuração da página Web
st.set_page_config(page_title="Conversor OCR de PDF", page_icon="📖", layout="centered")

st.title("📖 Conversor de PDF Escaneado para Texto Limpo")
st.write("Faça o upload de um PDF que contém páginas escaneadas (imagens) para extrair o texto e gerar um novo PDF limpo.")

# --- MAPEAMENTO DE IDIOMAS ---
# O Tesseract usa códigos de 3 letras: por (português), eng (inglês), fra (francês), ell (grego)
idiomas_suportados = {
    "Português": "por",
    "English (Inglês)": "eng",
    "Français (Francês)": "fra",
    "Ελληνικά (Grego)": "ell"
}

# Interface de seleção no site
idioma_selecionado = st.selectbox("Selecione o idioma principal do livro:", list(idiomas_suportados.keys()))
codigo_idioma = idiomas_suportados[idioma_selecionado]

# Upload do arquivo
arquivo_pdf = st.file_uploader("Escolha o arquivo PDF original", type=["pdf"])

if arquivo_pdf is not None:
    if st.button("Iniciar Processamento ✨"):
        with st.spinner("Processando... Isso pode levar alguns minutos dependendo do tamanho do livro."):
            
            # Criar arquivos temporários para não encher o servidor de lixo
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_entrada:
                tmp_entrada.write(arquivo_pdf.read())
                caminho_entrada = tmp_entrada.name

            caminho_saida = tempfile.mktemp(suffix=".pdf")

            try:
                # 1. Converter PDF para Imagens
                paginas_imagens = convert_from_path(caminho_entrada, dpi=200) # 200 DPI para economizar memória no servidor
                
                # 2. Configurar o PDF de saída
                c = canvas.Canvas(caminho_saida, pagesize=letter)
                largura, altura = letter
                
                # Mudar a fonte caso seja Grego (Helvetica padrão não suporta caracteres gregos)
                fonte = "Helvetica" if codigo_idioma != "ell" else "Times-Roman"

                total_paginas = len(paginas_imagens)
                barra_progresso = st.progress(0)

                for i, imagem in enumerate(paginas_imagens):
                    # OCR com o idioma escolhido
                    texto_extraido = pytesseract.image_to_string(imagem, lang=codigo_idioma)
                    
                    textobject = c.beginText()
                    textobject.setTextOrigin(50, altura - 50)
                    textobject.setFont(fonte, 11)
                    textobject.setLeading(14)
                    
                    for linha in texto_extraido.split('\n'):
                        # Se não for grego, removemos caracteres estranhos para evitar quebra no PDF básico
                        if codigo_idioma != "ell":
                            linha = linha.encode('ascii', 'ignore').decode('ascii')
                        textobject.textLine(linha)
                    
                    c.drawText(textobject)
                    
                    if i < total_paginas - 1:
                        c.showPage()
                    
                    # Atualiza a barra de progresso na tela
                    barra_progresso.progress((i + 1) / total_paginas)

                c.save()

                # 3. Disponibilizar o download
                with open(caminho_saida, "rb") as f:
                    st.success("🎉 Processamento concluído com sucesso!")
                    st.download_button(
                        label="📥 Baixar PDF Limpo",
                        data=f,
                        file_name="livro_limpo_ocr.pdf",
                        mime="application/pdf"
                    )

            except Exception as e:
                st.error(f"Ocorreu um erro durante o processamento: {e}")
                st.info("Nota: Certifique-se de que o servidor possui os pacotes de idioma do Tesseract instalados.")
            
            finally:
                # Limpeza dos arquivos temporários do servidor
                if os.path.exists(caminho_entrada): os.remove(caminho_entrada)
                if os.path.exists(caminho_saida): os.remove(caminho_saida)
