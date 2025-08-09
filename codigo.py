import streamlit as st
import openai

# --- A CHAVE DA OPENAI SERÁ CONFIGURADA NA NUVEM ---
# openai_api_key = st.secrets["OPENAI_API_KEY"]

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
    system_prompt = (
        "Você é um professor de matemática especialista em ENEM/Brasil. "
        "Gere uma questão original sobre o assunto fornecido. "
        "Utilize habilidades/competências da BNCC e ENEM. "
        "Apresente alternativas (A-E), destaque a correta, e explique a resposta."
    )
    user_input = f"Assunto de matemática: {topic}\nGere uma nova questão de múltipla escolha."
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        temperature=0.6,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ]
    )
    return response.choices[0].message["content"]


def generate_similar_question(topic, previous_question):
    system_prompt = (
        "Você é um professor de matemática especialista em ENEM/Brasil. "
        "Gere uma questão original e semelhante à anterior, sobre o mesmo assunto, mas mudando contexto/valores. "
        "Utilize habilidades/competências da BNCC e ENEM. "
        "Apresente alternativas (A-E), destaque a correta, e explique a resposta."
    )
    user_input = (
        f"Assunto: {topic}\n"
        f"Questão fornecida anteriormente:\n{previous_question}\n"
        "Gere uma questão nova, semelhante, de múltipla escolha."
    )
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        temperature=0.65,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ]
    )
    return response.choices[0].message["content"]


def extract_answer(question_text):
    lines = question_text.split('\n')
    answer = None
    for line in lines:
        if 'gabarito' in line.lower() or 'resposta:' in line.lower():
            answer = line.split(':')[-1].strip().upper()
            break
        if line.strip().lower().startswith("alternativa correta"):
            answer = line.split(":")[-1].strip().upper()
            break
    return answer


def extract_options(question_text):
    options = {}
    for line in question_text.split('\n'):
        if line.strip().startswith(('A)', 'B)', 'C)', 'D)', 'E)')):
            key = line.strip()[0]
            options[key] = line.strip()[2:].strip()
    return options


def show_question(question_data):
    st.subheader("Questão")
    question_lines = question_data.split('\n')
    question_text_parts = []
    options_started = False
    for l in question_lines:
        if l.strip().startswith(('A)', 'B)', 'C)', 'D)', 'E)')):
            options_started = True
        if not options_started:
            question_text_parts.append(l)

    # Remove explanation triggers from the main question text
    question_text_to_display = [l for l in question_text_parts if 'explicação' not in l.lower() and 'gabarito' not in l.lower()]

    st.markdown('\n'.join(question_text_to_display))
    options = extract_options(question_data)
    return options


def show_explanation(question_data):
    explanation = ""
    explanation_started = False
    for line in question_data.split('\n'):
        if any(word in line.lower() for word in ["explicação", "justificativa", "por quê", "resolução"]):
            explanation_started = True
        if explanation_started:
            explanation += line + '\n'
    if not explanation.strip():
        # fallback: try to extract last paragraph as explanation
        explanation = question_data.split('\n\n')[-1]
    st.info(f"Resolução: {explanation.strip()}")


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

    # Adiciona a chave da OpenAI a partir dos secrets do Streamlit
    openai.api_key = st.secrets["OPENAI_API_KEY"]

    if "questions" not in st.session_state:
        st.session_state.questions = []
        st.session_state.current = 0
        st.session_state.errors = []

    if st.sidebar.button("Preparar questões"):
        with st.spinner("Gerando novas questões... Aguarde!"):
            st.session_state.questions = [
                generate_question(topic) for _ in range(5)
            ]
        st.session_state.current = 0
        st.session_state.errors = []
        st.experimental_rerun()

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
                        if q_idx < len(st.session_state.questions) -1:
                            st.session_state.current += 1
                        else:
                            st.write("Fim das questões! Parabéns.")
                            st.session_state.questions = [] # Limpa para poder gerar novas
                        st.experimental_rerun()
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
                            st.experimental_rerun()
            else:
                st.warning("Não foi possível carregar as alternativas desta questão. Tente gerar novas questões.")

    st.sidebar.info(
        "Este sistema utiliza IA para gerar questões inéditas."
    )


if __name__ == "__main__":
    main()
