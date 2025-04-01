import os
import json
import requests
from datetime import datetime
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

# ======== CONFIGURA TU CLAVE API AQUÍ ========
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
# =============================================

# Verifica que la API key esté configurada correctamente
if not OPENROUTER_API_KEY:
    raise ValueError("❌ ERROR: La variable de entorno 'OPENROUTER_API_KEY' no está definida.")

# Iniciar FastAPI
app = FastAPI()

# Prompt base
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

# Estructura de datos para solicitudes
class UserMessage(BaseModel):
    message: str

# Clase del Chatbot
class ChatbotPublicidadSV:
    def __init__(self):
        self.conversation_history = []
        self.user_context = {
            "business_stage": "nuevo",
            "topics": "publicidad digital, normativas"
        }
        self.session_start_time = datetime.now()

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

        payload = {
            "model": "deepseek/deepseek-r1-zero:free",
            "messages": [
                {"role": "system", "content": PROMPT.format(
                    business_stage=self.user_context["business_stage"],
                    topics=self.user_context["topics"]
                )},
                {"role": "user", "content": user_message}
            ],
            "temperature": 0.7
        }

        try:
            response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
            response_json = response.json()
            assistant_message = response_json.get("choices", [{}])[0].get("message", {}).get("content", "Lo siento, no pude procesar la respuesta.")
            self.conversation_history.append({"role": "assistant", "content": assistant_message})
            return assistant_message
        except Exception as e:
            return f"Error al procesar la respuesta: {str(e)}"

chatbot = ChatbotPublicidadSV()

@app.post("/chat")
def chat_endpoint(user_message: UserMessage):
    try:
        response = chatbot.get_response(user_message.message)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Para ejecutar el servidor en Render
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
