# translation_app.py
import streamlit as st
from transformers import MarianMTModel, MarianTokenizer
from gtts import gTTS
import base64
from datetime import datetime
import os

# Custom CSS for modern UI with dark mode
st.markdown("""
<style>
:root {
    --primary: #3B82F6;
    --secondary: #6366F1;
    --background: #F8FAFC;
    --card-bg: #FFFFFF;
    --text-color: #1E293B;
}

[data-testid="stAppViewContainer"] {
    background: var(--background);
    color: var(--text-color);
}

.dark-mode {
    --background: #1E293B;
    --card-bg: #334155;
    --text-color: #F8FAFC;
}

.header {
    text-align: center;
    padding: 2rem 0;
    background: linear-gradient(135deg, var(--primary), var(--secondary));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.card {
    background: var(--card-bg);
    border-radius: 20px;
    padding: 2rem;
    margin: 1.5rem 0;
    box-shadow: 0 8px 32px rgba(0,0,0,0.05);
    transition: all 0.3s ease;
}

audio {
    margin-top: 1rem;
    width: 100%;
}
</style>
""", unsafe_allow_html=True)

# Supported languages with model codes
LANGUAGES = {
    "🇺🇸 English": "en",
    "🇪🇸 Spanish": "es",
    "🇫🇷 French": "fr",
    "🇩🇪 German": "de",
    "🇮🇹 Italian": "it",
    "🇵🇹 Portuguese": "pt",
    "🇳🇱 Dutch": "nl",
    "🇷🇺 Russian": "ru",
    "🇯🇵 Japanese": "ja",
    "🇰🇷 Korean": "ko",
    "🇨🇳 Chinese": "zh",
    "🇦🇪 Arabic": "ar",
    "🇮🇳 Hindi": "hi",
    "🇹🇷 Turkish": "tr",
    "🇸🇪 Swedish": "sv",
    "🇵🇱 Polish": "pl",
    "🇬🇷 Greek": "el",
    "🇻🇳 Vietnamese": "vi",
    "🇹🇭 Thai": "th",
    "🇮🇩 Indonesian": "id"
}

# Session state initialization
if 'history' not in st.session_state:
    st.session_state.history = []

if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = False

if 'source_lang' not in st.session_state:
    st.session_state.source_lang = "🇺🇸 English"

if 'target_lang' not in st.session_state:
    st.session_state.target_lang = "🇪🇸 Spanish"

@st.cache_resource
def load_models(source_code, target_code):
    # Try direct translation first
    try:
        direct_model_name = f'Helsinki-NLP/opus-mt-{source_code}-{target_code}'
        return {
            'direct': (
                MarianTokenizer.from_pretrained(direct_model_name),
                MarianMTModel.from_pretrained(direct_model_name)
            )
        }
    except:
        pass
    
    # Try two-step translation via English
    if source_code != "en" and target_code != "en":
        try:
            src_to_en = f'Helsinki-NLP/opus-mt-{source_code}-en'
            en_to_tgt = f'Helsinki-NLP/opus-mt-en-{target_code}'
            return {
                'two_step': (
                    MarianTokenizer.from_pretrained(src_to_en),
                    MarianMTModel.from_pretrained(src_to_en),
                    MarianTokenizer.from_pretrained(en_to_tgt),
                    MarianMTModel.from_pretrained(en_to_tgt)
                )
            }
        except:
            pass
    
    return None

def translate_text(text, tokenizer, model):
    inputs = tokenizer.encode(text, return_tensors="pt", truncation=True)
    translated = model.generate(inputs)
    return tokenizer.decode(translated[0], skip_special_tokens=True)

def text_to_speech(text, lang):
    try:
        tts = gTTS(text=text, lang=lang, slow=False)
        filename = f"temp_{lang}_{datetime.now().timestamp()}.mp3"
        tts.save(filename)
        return filename
    except Exception as e:
        st.error(f"Audio generation failed: {str(e)}")
        return None

def main():
    st.markdown("<h1 class='header'>AI Translation Pro</h1>", unsafe_allow_html=True)
    
    # Dark mode toggle
    st.session_state.dark_mode = st.sidebar.checkbox("Dark Mode 🌙", value=st.session_state.dark_mode)
    if st.session_state.dark_mode:
        st.markdown('<style>[data-testid="stAppViewContainer"] { background: #1E293B; color: white; }</style>', unsafe_allow_html=True)

    # Language selection with swap
    col1, col2, col3 = st.columns([10, 1, 10])
    with col1:
        source_lang = st.selectbox(
            "Source Language",
            options=LANGUAGES.keys(),
            index=list(LANGUAGES.keys()).index(st.session_state.source_lang)
        )
    with col2:
        if st.button("⇄", use_container_width=True, help="Swap languages"):
            st.session_state.source_lang, st.session_state.target_lang = st.session_state.target_lang, st.session_state.source_lang
            st.rerun()
    with col3:
        target_lang = st.selectbox(
            "Target Language",
            options=LANGUAGES.keys(),
            index=list(LANGUAGES.keys()).index(st.session_state.target_lang)
        )
    # Translation interface
    source_text = st.text_area(
        f"📝 Source Text ({LANGUAGES[source_lang].upper()})",
        height=150,
        placeholder="Enter text to translate..."
    )

    if st.button("🚀 Translate Now", use_container_width=True):
        if source_text:
            with st.spinner("Translating..."):
                source_code = LANGUAGES[source_lang]
                target_code = LANGUAGES[target_lang]
                
                models = load_models(source_code, target_code)
                
                if models:
                    try:
                        translated_text = ""
                        translation_path = []
                        
                        if 'direct' in models:
                            tokenizer, model = models['direct']
                            translated_text = translate_text(source_text, tokenizer, model)
                            translation_path = [f"{source_lang} → {target_lang}"]
                            
                        elif 'two_step' in models:
                            src_tokenizer, src_model, tgt_tokenizer, tgt_model = models['two_step']
                            st.info("Using two-step translation via English")
                            
                            # First translation to English
                            english_text = translate_text(source_text, src_tokenizer, src_model)
                            # Second translation to target language
                            translated_text = translate_text(english_text, tgt_tokenizer, tgt_model)
                            translation_path = [
                                f"{source_lang} → 🇺🇸 English",
                                f"🇺🇸 English → {target_lang}"
                            ]
                        
                        # Save to history
                        st.session_state.history.append({
                            'timestamp': datetime.now().strftime("%H:%M:%S"),
                            'source': source_lang,
                            'target': target_lang,
                            'text': translated_text,
                            'path': translation_path
                        })
                        
                        # Generate and display audio
                        audio_file = text_to_speech(translated_text, target_code)
                        if audio_file:
                            with open(audio_file, "rb") as f:
                                audio_bytes = f.read()
                            os.remove(audio_file)  # Clean up temp file
                            
                            st.markdown(f"""
                            <div class='card'>
                                <h3>🔖 Translation Result</h3>
                                {" ➔ ".join(translation_path)}
                                <p style='font-size: 1.2rem; margin: 1rem 0;'>{translated_text}</p>
                                <audio controls>
                                    <source src="data:audio/mp3;base64,{base64.b64encode(audio_bytes).decode()}" type="audio/mp3">
                                </audio>
                            </div>
                            """, unsafe_allow_html=True)
                        
                    except Exception as e:
                        st.error(f"Translation error: {str(e)}")
                else:
                    st.error(f"Translation from {source_lang} to {target_lang} not supported")
        else:
            st.warning("Please enter text to translate")

    # History sidebar
    with st.sidebar:
        st.markdown("### 📚 Translation History")
        for entry in reversed(st.session_state.history[-5:]):
            with st.expander(f"{entry['timestamp']}"):
                st.caption(" ➔ ".join(entry['path']))
                st.write(entry['text'])

if __name__ == "__main__":
    main()
