import streamlit as st
import google.generativeai as genai
import time

# --- A CHAVE DA API SERÁ CONFIGURADA NA NUVEM ---
# genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

STEM_SUBJECTS = {
    "Matemática": [
        "Funções",
        "Geometria",
        "Estatística",
        "Probabilidade",
        "Álgebra"
    ]
}

def generate_question(topic):
    model = genai.GenerativeModel('gemini-1.5-flash')
    prompt = (
        "Você é um professor de matemática especialista em ENEM/Brasil. "
        f"Gere uma questão original e desafiadora sobre o seguinte assunto de matemática: **{topic}**. "
        "A questão deve seguir o estilo do ENEM, com um contexto prático. "
        "Apresente 5 alternativas de múltipla escolha (A, B, C, D, E). "
        "No final, inclua uma linha com 'Gabarito: [Letra Correta]' e, em outra seção, uma linha com 'Resolução:' seguida da explicação detalhada de como chegar à resposta."
    )
    response = model.generate_content(prompt)
    return response.text

def generate_similar_question(topic, previous_question):
    model = genai.GenerativeModel('gemini-1.5-flash')
    prompt = (
        "Você é um professor de matemática especialista em ENEM/Brasil. "
        "Gere uma questão original e semelhante à questão fornecida abaixo, sobre o mesmo assunto, mas mudando o contexto e os valores numéricos. "
        "A nova questão deve ser diferente, mas manter o mesmo nível de dificuldade. "
        "Apresente 5 alternativas (A-E), uma linha com 'Gabarito: [Letra Correta]', e uma linha com 'Resolução:' e a explicação. "
        f"\n\n**Assunto:** {topic}\n"
        f"**Questão Anterior para referência:**\n{previous_question}"
    )
    response = model.generate_content(prompt)
    return response.text

def extract_answer(question_text):
    lines = question_text.split('\n')
    for line in lines:
        if 'gabarito:' in line.lower():
            return line.split(':')[-1].strip().upper()
    return None

def extract_options(question_text):
    options = {}
    lines = question_text.split('\n')
    for line in lines:
        if line.strip().startswith(('A)', 'B)', 'C)', 'D)', 'E)')):
            key = line.strip()[0]
            options[key] = line.strip()[2:].strip()
    return options

def show_question(question_data):
    st.subheader("Questão")
    # Mostra o texto até a parte das alternativas
    question_part = question_data.split("A)")[0]
    st.markdown(question_part)
    options = extract_options(question_data)
    return options

def show_explanation(question_data):
    if 'resolução:' in question_data.lower():
        explanation = question_data.lower().split('resolução:')[1].strip()
        st.info(f"**Resolução:**\n\n{explanation.capitalize()}")

def main():
    st.set_page_config(page_title="Questões de Matemática", layout="wide")

    st.sidebar.image("mascote.png", use_column_width=True)
    st.sidebar.title("Plataforma de Questões")

    st.title("Plataforma de Questões Matemáticas ENEM/BNCC")
    st.write(
        "Selecione o assunto de matemática e resolva questões autorais com "
        "feedback imediato, resolução comentada e adaptação ao seu desempenho!"
    )
    st.sidebar.header("Escolha o assunto")
    subject = st.sidebar.selectbox("Disciplina", ["Matemática"])
    topic = st.sidebar.selectbox("Assunto", STEM_SUBJECTS[subject])

    if "GOOGLE_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    else:
        st.error("Chave da API do Google não configurada. Por favor, adicione a chave nas configurações do aplicativo.")
        return

    if "questions" not in st.session_state:
        st.session_state.questions = []
        st.session_state.current = 0
        st.session_state.errors = []

    if st.sidebar.button("Preparar questões"):
        with st.spinner("Gerando novas questões com a IA do Google... Aguarde!"):
            st.session_state.questions = [
                generate_question(topic) for _ in range(5)
            ]
        st.session_state.current = 0
        st.session_state.errors = []
        st.rerun() # CORREÇÃO AQUI

    if st.session_state.get("questions"):
        q_idx = st.session_state.current
        if q_idx < len(st.session_state.questions):
            q_data = st.session_state.questions[q_idx]
            options = show_question(q_data)

            if options:
                user_answer = st.radio("Escolha uma alternativa:", list(options.keys()), key=f"q_{q_idx}")
                if st.button("Responder"):
                    gabarito = extract_answer(q_data)
                    if user_answer == gabarito:
                        st.success("Você acertou!")
                        st.balloons()
                        time.sleep(2)
                        if q_idx < len(st.session_state.questions) - 1:
                            st.session_state.current += 1
                        else:
                            st.write("Fim das questões! Parabéns.")
                            st.session_state.questions = [] 
                        st.rerun() # CORREÇÃO AQUI
                    else:
                        st.error(f"Você errou! A resposta correta era {gabarito}.")
                        st.session_state.errors.append(q_idx)
                        show_explanation(q_data)
                        if st.button(
                            "Quero uma outra questão semelhante para treinar!"
                        ):
                            with st.spinner("Preparando uma questão semelhante..."):
                                new_q = generate_similar_question(
                                    topic, q_data
                                )
                            st.session_state.questions.insert(
                                q_idx + 1, new_q
                            )
                            st.session_state.current += 1
                            st.rerun() # CORREÇÃO AQUI
            else:
                st.warning("Não foi possível carregar as alternativas. Tente gerar novas questões.")

    st.sidebar.info(
        "Este sistema utiliza a IA do Google para gerar questões inéditas."
    )


if __name__ == "__main__":
    main()