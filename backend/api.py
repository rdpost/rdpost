import json
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
from agents import procesar_ticket
import uvicorn
from typing import Dict
from mistralai import Mistral

def calculate_confidence(ticket, image, resolution):
    
    if image is not None:
        p = f'''
        A continuación, vas a recibir una incidencia de una empresa de envío postal y la resolución de la misma. Esta incidencia ha sido resuelta por Agente LLM de Customer Service.
        Tu tarea es asignar una puntuación de confianza a cómo el agente ha resuelto esta incidencia. Esta puntuación se usará para determinar si la incidencia debería ser revisada por
        un humano o no. La puntuación de confianza debe estar entre 0.0 y 1.0. Un valor cercano a 1.0 significa que la respuesta del agente es muy confiable y no necesita revisión. 
        Un valor cercano a 0.0 significa que la respuesta del agente es muy poco confiable y debería ser revisada por un humano. 
        La puntuación de confianza debe ser una respuesta en formato JSON con la clave "confidence_score". 
        
        El contenido original del ticket es el siguiente: 
        
        ```
        {ticket}
        ```

        El cliente también ha adjuntado una imagen, aquí tienes la descripción de la misma:
        
        ```
        {image}
        ```

        La resolución del ticket por parte del agente ha sido siguiente:

        ```
        {resolution}
        ```
        '''
    else:
        p = f'''
        A continuación, vas a recibir una incidencia de una empresa de envío postal y la resolución de la misma. Esta incidencia ha sido resuelta por Agente LLM de Customer Service.
        Tu tarea es asignar una puntuación de confianza a cómo el agente ha resuelto esta incidencia. Esta puntuación se usará para determinar si la incidencia debería ser revisada por
        un humano o no. La puntuación de confianza debe estar entre 0.0 y 1.0. Un valor cercano a 1.0 significa que la respuesta del agente es muy confiable y no necesita revisión. 
        Un valor cercano a 0.0 significa que la respuesta del agente es muy poco confiable y debería ser revisada por un humano. 
        La puntuación de confianza debe ser una respuesta en formato JSON con la clave "confidence_score". 
        
        El contenido original del ticket es el siguiente: 
        
        ```
        {ticket}
        ```

        La resolución del ticket por parte del agente ha sido siguiente:

        ```
        {resolution}
        ```
        '''
                    
    payload = {
        "model": "gpt-4o-2024-05-13",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": p}
                ]
            }
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.2,
        "top_p": 1
    }

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {os.getenv("OPENAI_API_KEY")}'
    } 

    response_dict = requests.post('https://api.openai.com/v1/chat/completions', headers=headers, json=payload)
    response_json = response_dict.json()
    # print(response_json)
    return json.loads(response_json['choices'][0]['message']['content'])["confidence_score"]

app = FastAPI(
    title="RDPOST Customer Service API",
    description="API para procesar tickets de clientes utilizando agentes LLM.",
    version="1.0.0"
)

class TicketRequest(BaseModel):
    content: str
    image: str = None  # Campo opcional para la imagen en base64

class TicketResponse(BaseModel):
    response: str
    confidence: float


def analizar_imagen(base64_image: str) -> Dict:
    print('Analizando imagen...')
    client = Mistral(
        api_key=os.environ["MISTRAL_API_KEY"]
    )

    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text", 
                    "text": "Analiza esta imagen y devuelve un JSON con una descripcion detallada. Si hay un documento, realiza el OCR. Ten en cuenta que esta imagen debería estar relacionada con un envío postal, así que incluye en tu descripción toda la información relevante respecto al envío."
                },
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                }
            ]
        }
    ]

    # Llamada a la API usando el modelo Pixtral
    response = client.chat.complete(
        model="pixtral-12b-2409",
        messages=messages,
        temperature=0.1,
        max_tokens=1000
    )
    # Procesar respuesta
    try:
        res = response.choices[0].message.content
        # print(res)
        # resultado = json.loads(res)
        return res
    except json.JSONDecodeError:
        return {
            "descripcion": "",
            "objetos": [],
            "texto": ""
        }


@app.post("/process_ticket", response_model=TicketResponse)
def process_ticket_endpoint(ticket: TicketRequest):
    """
    Procesa un ticket de cliente y devuelve la respuesta generada por los agentes.
    Opcionalmente puede incluir una imagen en base64.
    """
    try:
        if ticket.image is not None:
            desc_imagen = analizar_imagen(ticket.image)
        respuesta = procesar_ticket(ticket.content, desc_imagen)
        confidence = calculate_confidence(ticket.content, desc_imagen, respuesta)
        return TicketResponse(response=respuesta, confidence=confidence)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000)