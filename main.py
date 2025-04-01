import os
import json
import requests
from datetime import datetime
import ipywidgets as widgets

# ======== CONFIGURA TU CLAVE API AQUÍ ========
OPENROUTER_API_KEY = "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"
# =============================================

# Prompt modificado para asegurar el formato deseado
PROMPT = """
Eres un asistente especializado en normativas y estrategias para PYMEs publicitarias en El Salvador.
Tu objetivo es proporcionar respuestas claras, precisas y personalizadas para ayudar a empresarios y emprendedores
a cumplir regulaciones, optimizar su negocio y aprovechar oportunidades de crecimiento.

CONTEXTO DEL USUARIO:
- Etapa del negocio: {business_stage}
- Temas de interés: {topics}

INSTRUCCIONES ESPECÍFICAS:

1. NORMATIVAS LEGALES Y FISCALES
- Explica de forma sencilla las leyes y regulaciones aplicables a agencias de publicidad en El Salvador
- Menciona fuentes oficiales cuando sea posible (CNR, Ministerio de Hacienda, CONAMYPE)
- Sé específico con los trámites, costos y plazos

2. ESTRATEGIAS DE CRECIMIENTO Y MARKETING
- Ofrece consejos prácticos sobre publicidad digital, branding, redes sociales relevantes para El Salvador
- Sugiere herramientas accesibles para PYMEs salvadoreñas
- Adapta recomendaciones al contexto económico y cultural de El Salvador

3. FORMATO OBLIGATORIO PARA TODAS TUS RESPUESTAS:
Debes estructurar CADA UNA de tus respuestas siguiendo EXACTAMENTE este formato:
- Respuestas en Español
- Usa lenguaje claro y sin tecnicismos
- Formatea respuestas para ser leídas en dispositivos móviles (párrafos cortos, listas)
- Para respuestas con pasos, usa emojis como marcadores (1️⃣, 2️⃣, etc.)
- Limita respuestas a máximo 250 palabras
- Asegurate de que las respuestas vayan en estilo de lista, no en estilo de parrafo para que sea vea ordenado y sea mas facil de entender.
- Si es relevante, ofrece opciones al final con preguntas como "¿Quieres que te explique más sobre X?"

NO PUEDES RESPONDER SIN USAR ESTE FORMATO. Es MANDATORIO que sigas este formato para TODAS tus respuestas.

4. PERSONALIZACIÓN:
- Si el negocio es nuevo: enfoca en trámites iniciales, costos reducidos
- Si está en crecimiento: enfoca en optimización y expansión
- Si está consolidado: enfoca en innovación y eficiencia

NOTA IMPORTANTE: Si no conoces la respuesta exacta sobre alguna normativa específica de El Salvador, indícalo
claramente y sugiere fuentes oficiales donde el usuario pueda consultar información actualizada.

RECUERDA: Toda respuesta DEBE incluir emojis numéricos (1️⃣, 2️⃣, 3️⃣...) para los pasos, y DEBE terminar con una pregunta.
"""

class ChatbotPublicidadSV:
    def __init__(self):
        self.conversation_history = []
        self.user_context = {
            "business_stage": "nuevo",
            "topics": "publicidad digital, normativas"
        }
        self.session_start_time = datetime.now()

    def save_conversation(self):
        timestamp = self.session_start_time.strftime("%Y%m%d_%H%M%S")
        filename = f"conversacion_{timestamp}.json"

        data = {
            "conversation": self.conversation_history,
            "user_context": self.user_context
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        files.download(filename)
        return filename

    def update_user_context(self, message: str):
        if any(word in message.lower() for word in ["nuevo", "iniciar", "comenzar", "empezar", "emprendimiento"]):
            self.user_context["business_stage"] = "nuevo"
        elif any(word in message.lower() for word in ["crecimiento", "expandir", "crecer", "desarrollo"]):
            self.user_context["business_stage"] = "crecimiento"
        elif any(word in message.lower() for word in ["consolidado", "establecido", "maduro"]):
            self.user_context["business_stage"] = "consolidado"

    def get_response(self, user_message: str) -> str:
        self.update_user_context(user_message)
        self.conversation_history.append({"role": "user", "content": user_message})

        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }

        # Mensajes del sistema mejorados para forzar el formato
        system_messages = [
            {"role": "system", "content": PROMPT.format(
                business_stage=self.user_context["business_stage"],
                topics=self.user_context["topics"]
            )},
            {"role": "system", "content": "IMPORTANTE: Tu respuesta DEBE usar los emojis numéricos (1️⃣, 2️⃣, 3️⃣...) y DEBE terminar con una pregunta de seguimiento."}
        ]

        payload = {
            "model": "deepseek/deepseek-r1-zero:free",
            "messages": system_messages + [{"role": "user", "content": user_message}],
            "temperature": 0.7  # Ajusta esto según sea necesario
        }

        try:
            response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, data=json.dumps(payload))
            response_json = response.json()
            assistant_message = response_json.get("choices", [{}])[0].get("message", {}).get("content", "Lo siento, no pude procesar la respuesta.")

            # Verificar formato y corregir si es necesario
            if "1️⃣" not in assistant_message:
                # Intenta obtener una respuesta con formato correcto
                payload["messages"].append({"role": "assistant", "content": assistant_message})
                payload["messages"].append({"role": "user", "content": "Por favor, reformatea tu respuesta usando los emojis numéricos (1️⃣, 2️⃣, 3️⃣...) y termina con una pregunta."})

                correction_response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, data=json.dumps(payload))
                correction_json = correction_response.json()
                assistant_message = correction_json.get("choices", [{}])[0].get("message", {}).get("content", assistant_message)

            self.conversation_history.append({"role": "assistant", "content": assistant_message})
            return assistant_message
        except Exception as e:
            return f"Error al procesar la respuesta: {str(e)}"

def create_dynamic_chatbot_interface():
    # Initialize chatbot
    chatbot = ChatbotPublicidadSV()

    # CSS styling for the chat interface
    css = """
    <style>
        .chat-container {
            width: 100%;
            max-width: 500px;
            height: 600px;
            background-color: white;
            border-radius: 20px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.1);
            display: flex;
            flex-direction: column;
            overflow: hidden;
            margin: 20px auto;
            font-family: 'Inter', sans-serif;
        }
        .chat-header {
            background-color: #0c2742;
            color: white;
            padding: 15px;
            text-align: center;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .chat-header h2 {
            margin: 0;
            font-size: 18px;
            flex-grow: 1;
            text-align: center;
        }
        .chat-messages {
            flex-grow: 1;
            overflow-y: auto;
            padding: 15px;
            background-color: white !important; /* Changed to white with !important */
            display: flex;
            flex-direction: column;
        }
        .message {
            max-width: 80%;
            margin-bottom: 10px;
            clear: both;
            display: flex;
            flex-direction: column;
        }
        .bot-message {
            align-self: flex-start;
        }
        .user-message {
            align-self: flex-end;
        }
        .message-bubble {
            padding: 10px 15px;
            border-radius: 18px;
            font-size: 14px;
            line-height: 1.4;
            max-width: 100%;
            word-wrap: break-word;
        }
        .bot-message .message-bubble {
            background-color: #007bff; /* Changed bot bubble to blue */
            color: white;
            border-bottom-left-radius: 5px;
        }
        .user-message .message-bubble {
            background-color: #e5e5ea; /* Changed user bubble to gray */
            color: black;
            border-bottom-right-radius: 5px;
        }
        .message-time {
            font-size: 10px;
            color: #888;
            margin-top: 5px;
            align-self: flex-end;
        }
        .chat-input-container {
            display: flex;
            padding: 10px;
            background-color: white;
            border-top: 1px solid #e0e0e0;
        }
        .chat-input {
            flex-grow: 1;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 20px;
            margin-right: 10px;
            font-size: 14px;
        }
        .send-button {
            background-color: #0c2742;
            color: white;
            border: none;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
        }
        .send-button:hover {
            background-color: #1a5276;
        }
        .save-button {
            background-color: #7578ff;
            color: white;
            border: none;
            border-radius: 20px;
            padding: 10px 15px;
            margin-left: 10px;
            cursor: pointer;
        }
        .save-button:hover {
            background-color: #5356c4;
        }
    </style>
    """

    # Additional CSS to override any Jupyter/Colab styles
    additional_css = """
    <style>
        /* Force white background for output areas */
        .jupyter-widgets-output-area .output_area {
            background-color: white !important;
        }
        .widget-output {
            background-color: white !important;
        }
        .p-Widget {
            background-color: white !important;
        }
        .output_subarea {
            background-color: white !important;
        }
    </style>
    """

    # Add Google Fonts
    display(HTML("<link href='https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap' rel='stylesheet'>"))
    display(HTML(css))
    display(HTML(additional_css))

    # Create output area for messages
    output = widgets.Output(
        layout={'height': '500px', 'overflow_y': 'auto', 'padding': '10px', 'background': 'white !important'}
    )

    # Create input widgets
    input_text = widgets.Text(
        placeholder='Escribe tu mensaje...',
        layout=widgets.Layout(width='100%'),
        style={'description_width': 'initial'}
    )

    send_button = widgets.Button(
        description='➤',
        layout=widgets.Layout(width='40px', height='40px'),
        style={'button_color': '#0c2742', 'font_weight': 'bold'}
    )

    save_button = widgets.Button(
        description='Guardar',
        layout=widgets.Layout(width='100px', height='40px'),
        style={'button_color': '#7578ff'}
    )

    # Display initial message with the correct format
    with output:
        display(HTML("""
        <div class="message bot-message">
            <div class="message-bubble">
                ¡Hola! Soy tu asistente especializado para PYMEs publicitarias en El Salvador.
                ¿Sobre qué tema específico necesitas información hoy? 😊
            </div>
            <div class="message-time">Ahora</div>
        </div>
        """))

    # Function to add a message to the chat
    def add_message(content, role):
        timestamp = datetime.now().strftime("%H:%M")
        with output:
            if role == "user":
                display(HTML(f"""
                <div class="message user-message">
                    <div class="message-bubble">{content}</div>
                    <div class="message-time">{timestamp}</div>
                </div>
                """))
            else:
                # Asegurar que el HTML en la respuesta del bot se muestre correctamente
                content = content.replace('\n', '<br>')
                display(HTML(f"""
                <div class="message bot-message">
                    <div class="message-bubble">{content}</div>
                    <div class="message-time">{timestamp}</div>
                </div>
                """))

    # Event handlers
    def on_send_click(b):
        user_message = input_text.value
        if user_message.strip():
            # Clear input
            input_text.value = ''

            # Add user message
            add_message(user_message, "user")

            # Get bot response
            bot_response = chatbot.get_response(user_message)

            # Add bot response
            add_message(bot_response, "bot")

    def on_save_click(b):
        filename = chatbot.save_conversation()
        add_message(f"✅ Conversación guardada en {filename}", "bot")

    # Connect button to click events
    send_button.on_click(on_send_click)
    save_button.on_click(on_save_click)

    # Connect enter key to send button
    def on_enter_key(widget):
        user_message = input_text.value
        if user_message.strip():
            # Clear input
            input_text.value = ''

            # Add user message
            add_message(user_message, "user")

            # Get bot response
            bot_response = chatbot.get_response(user_message)

            # Add bot response
            add_message(bot_response, "bot")

    # Register the enter key handler
    input_text.on_submit(on_enter_key)

    # Create input area container
    input_area = widgets.HBox(
        [input_text, send_button, save_button],
        layout=widgets.Layout(width='100%', justify_content='space-between')
    )

    # One more override to make sure f0f2f5 is replaced with white
    display(HTML("""
    <style>
        .chat-messages {
            background-color: white !important;
        }
    </style>
    """))

    # Create main container
    container = widgets.VBox(
        [
            widgets.HTML("""
            <div class="chat-header">
                <h2>🤖 Asistente PYME El Salvador</h2>
            </div>
            """),
            output,
            input_area
        ],
        layout=widgets.Layout(width='100%', max_width='500px', margin='0 auto', background_color='white')
    )

    # Display the interface
    display(container)

# Run the dynamic interface
create_dynamic_chatbot_interface()
