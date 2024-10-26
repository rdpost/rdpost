from dotenv import load_dotenv
from swarm import Agent, Swarm
import random
from datetime import datetime
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderServiceError, GeocoderTimedOut
import time


# Cargar variables de entorno
load_dotenv()

# Inicializar el cliente Swarm
client = Swarm()

# Mock data
ENVIOS_DB = {
    "ENV123": {
        "estado": "en_transito",
        "fecha_envio": "2024-10-20",
        "direccion_destino": "Calle Principal 123, 29017 Málaga",
        "codigo_postal": "29017",
        "tipo_envio": "certificado",
        "recibir_por": "Juan Pérez",
        "coordenadas_gps": "36.7213, -4.4214",
        "visitas": [
            {"visita": 1, "fecha_hora": "2024-10-21 10:30:00"},
            {"visita": 2, "fecha_hora": "2024-10-22 14:45:00"}
        ],
        "receptores": {
            "nombre_completo": "FECHA",
            "dni": "12345678A",
            "firma": ""
        }
    },
    "ENV456": {
        "estado": "entregado",
        "fecha_envio": "2024-10-18",
        "direccion_destino": "Avenida Central 456, 28001 Madrid",
        "codigo_postal": "28001",
        "tipo_envio": "express",
        "recibir_por": "Ana Gómez",
        "coordenadas_gps": "40.4168, -3.7038",
        "visitas": [
            {"visita": 1, "fecha_hora": "2024-10-19 09:15:00"},
            {"visita": 2, "fecha_hora": "2024-10-20 16:50:00"}
        ],
        "receptores": {
            "nombre_completo": "JOHNSON PAUL ANTHONY",
            "dni": "87654321B",
            "firma": "Firma del empleado"
        }
    },
    "ENV789": {
        "estado": "rechazado",
        "fecha_envio": "2024-10-19",
        "direccion_destino": "Plaza de la Constitución 789, 41001 Sevilla",
        "codigo_postal": "41001",
        "tipo_envio": "standard",
        "recibir_por": "María López",
        "coordenadas_gps": "37.3891, -5.9845",
        "visitas": [
            {"visita": 1, "fecha_hora": "2024-10-20 11:00:00"},
            {"visita": 2, "fecha_hora": "2024-10-21 15:30:00"},
            {"visita": 3, "fecha_hora": "2024-10-22 18:20:00"}
        ],
        "receptores": {
            "nombre_completo": "Carlos Fernández",
            "dni": "11223344C",
            "firma": ""
        }
    },
    "PNT040010272387000000940": {
        "estado": "en_transito",
        "fecha_envio": "20/10/2022",
        "direccion_destino": "Av. de Carlos III, 348",
        "codigo_postal": "46001",
        "tipo_envio": "standard",
        "recibir_por": "JOHNSON PAUL ANTHONY",
        "coordenadas_gps": "36.722480985338006, -4.3790217116476105",
        "visitas": [
            {"visita": 1, "fecha_hora": "2024-10-23 08:20:00"}
        ],
        "receptores": {
            "nombre_completo": "PRUEBAS",
            "dni": "22334455D",
            "firma": ""
        }
    },
    "ENV102": {
        "estado": "entregado",
        "fecha_envio": "2024-10-17",
        "direccion_destino": "Calle Luna 102, 08001 Barcelona",
        "codigo_postal": "08001",
        "tipo_envio": "express",
        "recibir_por": "Sofía Ruiz",
        "coordenadas_gps": "41.3851, 2.1734",
        "visitas": [
            {"visita": 1, "fecha_hora": "2024-10-18 12:00:00"},
            {"visita": 2, "fecha_hora": "2024-10-19 17:30:00"},
            {"visita": 3, "fecha_hora": "2024-10-20 19:45:00"}
        ],
        "receptores": {
            "nombre_completo": "Miguel Ángel",
            "dni": "33445566E",
            "firma": "Firma del empleado"
        }
    }
}

SEGUROS_DB = {
    "ENV123": {"tipo": "básico", "cobertura": 50},
    "ENV456": {"tipo": "premium", "cobertura": 200},
    "ENV789": {"tipo": "sin_seguro", "cobertura": 0},
    "ENV101": {"tipo": "básico", "cobertura": 75},
    "ENV102": {"tipo": "premium", "cobertura": 150},
    "ENV103": {"tipo": "premium", "cobertura": 250},
    "ENV104": {"tipo": "básico", "cobertura": 100}
}

# Inicializar el geocodificador
geolocator = Nominatim(user_agent="rdpost_agent")

def obtener_ubicacion(coordenadas_gps: str) -> dict:
    """
    Obtiene la dirección a partir de las coordenadas GPS.
    
    Args:
        coordenadas_gps (str): Cadena con las coordenadas GPS en formato "latitud, longitud".
    
    Returns:
        dict: Diccionario con la dirección o un mensaje de error.
    """
    try:
        # Separar latitud y longitud
        lat, lon = map(float, coordenadas_gps.split(","))
        location = geolocator.reverse((lat, lon), exactly_one=True, timeout=10)
        
        if location:
            return {"direccion": location.address}
        else:
            return {"error": "Ubicación no encontrada para las coordenadas proporcionadas."}
    
    except ValueError:
        return {"error": "Formato de coordenadas inválido. Debe ser 'latitud, longitud'."}
    except (GeocoderServiceError, GeocoderTimedOut):
        # Manejar errores de servicio y tiempos de espera
        time.sleep(1)  # Esperar un segundo antes de reintentar
        return obtener_ubicacion(coordenadas_gps)
    except Exception as e:
        return {"error": f"Ocurrió un error inesperado: {str(e)}"}

# Funciones de herramientas específicas por agente

# Herramientas para el Agente de Entregas
def verificar_direccion_destino(id_envio: str) -> dict:
    envio = ENVIOS_DB.get(id_envio)
    if envio:
        return {"direccion_destino": envio["direccion_destino"]}
    return {"error": "Dirección de destino no encontrada"}

def obtener_coordenadas_gps(id_envio: str) -> dict:
    envio = ENVIOS_DB.get(id_envio)
    if envio:
        return {"coordenadas_gps": envio["coordenadas_gps"]}
    return {"error": "Coordenadas GPS no encontradas"}

def obtener_ubicacion_actual_envio(id_envio: str) -> dict:
    envio = ENVIOS_DB.get(id_envio)
    if envio and "coordenadas_gps" in envio:
        return obtener_ubicacion(envio["coordenadas_gps"])
    return {"error": "Coordenadas GPS no disponibles para este envío."}

# Herramientas para el Agente de Reclamaciones
def obtener_detalles_receptor(id_envio: str) -> dict:
    envio = ENVIOS_DB.get(id_envio)
    if envio:
        return envio["receptores"]
    return {"error": "Detalles del receptor no encontrados"}

def listar_visitas(id_envio: str) -> dict:
    envio = ENVIOS_DB.get(id_envio)
    if envio:
        return {"visitas": envio["visitas"]}
    return {"error": "Visitas no encontradas"}

# Funciones de herramientas generales
def verificar_datos_envio(id_envio: str) -> dict:
    envio = ENVIOS_DB.get(id_envio)
    if envio:
        return {
            "id_envio": id_envio,
            "estado": envio["estado"],
            "fecha_envio": envio["fecha_envio"],
            "direccion_destino": envio["direccion_destino"],
            "codigo_postal": envio["codigo_postal"],
            "tipo_envio": envio["tipo_envio"],
            "recibir_por": envio["recibir_por"]
        }
    return {"error": "Envío no encontrado"}

def comprobar_estado_trazabilidad(id_envio: str) -> dict:
    envio = ENVIOS_DB.get(id_envio)
    if not envio:
        return {"error": "Envío no encontrado"}
    return {
        "estado_actual": envio["estado"],
        "ultima_actualizacion": datetime.now().isoformat(),
        "visitas_realizadas": len(envio["visitas"]),
        "visitas_detalle": envio["visitas"]
    }

def registrar_reclamacion(id_envio: str, tipo_incidencia: str) -> dict:
    if id_envio not in ENVIOS_DB:
        return {"error": "Envío no encontrado"}
    reclamacion = {
        "id_reclamacion": f"REC-{random.randint(1000,9999)}",
        "estado": "registrada",
        "tipo_incidencia": tipo_incidencia,
        "fecha_registro": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    }
    return reclamacion

def verificar_seguro(id_envio: str) -> dict:
    return SEGUROS_DB.get(id_envio, {"tipo": "sin_seguro", "cobertura": 0})

def calcular_importe_indemnizacion(id_envio: str, tipo_dano: str) -> dict:
    seguro = verificar_seguro(id_envio)
    if seguro["tipo"] == "sin_seguro":
        return {"error": "El envío no tiene seguro."}
    importe = seguro["cobertura"] * 0.8
    return {
        "importe_calculado": importe,
        "tipo_seguro": seguro["tipo"],
        "tipo_dano": tipo_dano,
        "moneda": "EUR"
    }

def transferir_a_agente_entregas():
    print('transfiriendo a agente de entregas...')
    return agente_entregas

def transferir_a_agente_perdidas():
    print('transfiriendo a agente de perdidas...')
    return agente_perdidas

def actualizar_estado_envio(id_envio: str, nuevo_estado: str) -> dict:
    envio = ENVIOS_DB.get(id_envio)
    if envio:
        envio["estado"] = nuevo_estado
        envio["ultima_actualizacion"] = datetime.now().isoformat()
        return {"mensaje": f"Estado de envío {id_envio} actualizado a {nuevo_estado} el {envio['ultima_actualizacion']}"}
    return {"error": "Envío no encontrado"}

def obtener_lista_centros_rdpost_espana():
    lista_centros = [
        {
        "codigoINE": "04",
        "codigoPostal": "04001",
        "nombre": "Almería",
        "direccion": "Calle del Sol, 1",
        "telefono": "950123456"
        },
        {
        "codigoINE": "11",
        "codigoPostal": "11001", 
        "nombre": "Cádiz",
        "direccion": "Avenida de la Bahía, 23",
        "telefono": "956234567"
        },
        {
        "codigoINE": "14",
        "codigoPostal": "14001",
        "nombre": "Córdoba", 
        "direccion": "Plaza de las Tendillas, 15",
        "telefono": "957345678"
        },
        {
        "codigoINE": "18",
        "codigoPostal": "18001",
        "nombre": "Granada",
        "direccion": "Calle Reyes Católicos, 7",
        "telefono": "958456789"
        },
        {
        "codigoINE": "21",
        "codigoPostal": "21001",
        "nombre": "Huelva",
        "direccion": "Avenida de Andalucía, 45",
        "telefono": "959567890"
        },
        {
        "codigoINE": "23",
        "codigoPostal": "23001",
        "nombre": "Jaén",
        "direccion": "Paseo de la Estación, 8",
        "telefono": "953678901"
        },
        {
        "codigoINE": "29",
        "codigoPostal": "29001",
        "nombre": "Málaga",
        "direccion": "Calle Larios, 10",
        "telefono": "952789012"
        },
        {
        "codigoINE": "41",
        "codigoPostal": "41001",
        "nombre": "Sevilla",
        "direccion": "Avenida de la Constitución, 12",
        "telefono": "954890123"
        },
        {
        "codigoINE": "22",
        "codigoPostal": "22001",
        "nombre": "Huesca",
        "direccion": "Calle del Coso Alto, 5",
        "telefono": "974901234"
        },
        {
        "codigoINE": "44",
        "codigoPostal": "44001",
        "nombre": "Teruel",
        "direccion": "Calle Nueva, 14",
        "telefono": "978012345"
        },
        {
        "codigoINE": "50",
        "codigoPostal": "50001",
        "nombre": "Zaragoza",
        "direccion": "Paseo de la Independencia, 9",
        "telefono": "976123456"
        },
        {
        "codigoINE": "33",
        "codigoPostal": "33001",
        "nombre": "Asturias",
        "direccion": "Calle Uría, 17",
        "telefono": "985234567"
        },
        {
        "codigoINE": "39",
        "codigoPostal": "39001",
        "nombre": "Cantabria",
        "direccion": "Calle Isabel II, 6",
        "telefono": "942345678"
        },
        {
        "codigoINE": "05",
        "codigoPostal": "05001",
        "nombre": "Ávila",
        "direccion": "Calle San Segundo, 11",
        "telefono": "920456789"
        },
        {
        "codigoINE": "09",
        "codigoPostal": "09001",
        "nombre": "Burgos",
        "direccion": "Calle Vitoria, 22",
        "telefono": "947567890"
        },
        {
        "codigoINE": "24",
        "codigoPostal": "24001",
        "nombre": "León",
        "direccion": "Avenida Ordoño II, 3",
        "telefono": "987678901"
        },
        {
        "codigoINE": "34",
        "codigoPostal": "34001",
        "nombre": "Palencia",
        "direccion": "Plaza Mayor, 10",
        "telefono": "979789012"
        },
        {
        "codigoINE": "37",
        "codigoPostal": "37001",
        "nombre": "Salamanca",
        "direccion": "Calle Toro, 12",
        "telefono": "923890123"
        },
        {
        "codigoINE": "40",
        "codigoPostal": "40001",
        "nombre": "Segovia",
        "direccion": "Calle Real, 18",
        "telefono": "921901234"
        },
        {
        "codigoINE": "42",
        "codigoPostal": "42001",
        "nombre": "Soria",
        "direccion": "Calle del Collado, 4",
        "telefono": "975012345"
        },
        {
        "codigoINE": "47",
        "codigoPostal": "47001",
        "nombre": "Valladolid",
        "direccion": "Calle Santiago, 7",
        "telefono": "983123456"
        },
        {
        "codigoINE": "49",
        "codigoPostal": "49001",
        "nombre": "Zamora",
        "direccion": "Calle Santa Clara, 15",
        "telefono": "980234567"
        },
        {
        "codigoINE": "02",
        "codigoPostal": "02001",
        "nombre": "Albacete",
        "direccion": "Avenida de España, 2",
        "telefono": "967345678"
        },
        {
        "codigoINE": "13",
        "codigoPostal": "13001",
        "nombre": "Ciudad Real",
        "direccion": "Calle de la Feria, 6",
        "telefono": "926456789"
        },
        {
        "codigoINE": "16",
        "codigoPostal": "16001",
        "nombre": "Cuenca",
        "direccion": "Calle Carretería, 8",
        "telefono": "969567890"
        },
        {
        "codigoINE": "19",
        "codigoPostal": "19001",
        "nombre": "Guadalajara",
        "direccion": "Paseo de las Cruces, 3",
        "telefono": "949678901"
        },
        {
        "codigoINE": "45",
        "codigoPostal": "45001",
        "nombre": "Toledo",
        "direccion": "Calle Comercio, 1",
        "telefono": "925789012"
        },
        {
        "codigoINE": "08",
        "codigoPostal": "08001",
        "nombre": "Barcelona",
        "direccion": "Calle Pelayo, 10",
        "telefono": "934890123"
        },
        {
        "codigoINE": "17",
        "codigoPostal": "17001",
        "nombre": "Girona",
        "direccion": "Calle de la Força, 21",
        "telefono": "972901234"
        },
        {
        "codigoINE": "25",
        "codigoPostal": "25001",
        "nombre": "Lleida",
        "direccion": "Calle Mayor, 13",
        "telefono": "973012345"
        },
        {
        "codigoINE": "43",
        "codigoPostal": "43001",
        "nombre": "Tarragona",
        "direccion": "Rambla Nova, 20",
        "telefono": "977123456"
        },
        {
        "codigoINE": "03",
        "codigoPostal": "03001",
        "nombre": "Alicante",
        "direccion": "Calle San Francisco, 5",
        "telefono": "965234567"
        },
        {
        "codigoINE": "12",
        "codigoPostal": "12001",
        "nombre": "Castellón",
        "direccion": "Calle Mayor, 16",
        "telefono": "964345678"
        },
        {
        "codigoINE": "46",
        "codigoPostal": "46001",
        "nombre": "Valencia",
        "direccion": "Calle Colón, 18",
        "telefono": "963456789"
        },
        {
        "codigoINE": "06",
        "codigoPostal": "06001",
        "nombre": "Badajoz",
        "direccion": "Calle Menacho, 25",
        "telefono": "924567890"
        },
        {
        "codigoINE": "10",
        "codigoPostal": "10001",
        "nombre": "Cáceres",
        "direccion": "Avenida de España, 7",
        "telefono": "927678901"
        },
        {
        "codigoINE": "15",
        "codigoPostal": "15001",
        "nombre": "A Coruña",
        "direccion": "Calle Real, 9",
        "telefono": "981789012"
        },
        {
        "codigoINE": "27",
        "codigoPostal": "27001",
        "nombre": "Lugo",
        "direccion": "Rúa San Marcos, 11",
        "telefono": "982890123"
        },
        {
        "codigoINE": "32",
        "codigoPostal": "32001",
        "nombre": "Ourense",
        "direccion": "Rúa do Paseo, 14",
        "telefono": "988901234"
        },
        {
        "codigoINE": "36",
        "codigoPostal": "36001",
        "nombre": "Pontevedra",
        "direccion": "Calle Michelena, 2",
        "telefono": "986012345"
        },
        {
        "codigoINE": "28",
        "codigoPostal": "28001",
        "nombre": "Madrid",
        "direccion": "Calle de Alcalá, 1",
        "telefono": "917123456"
        },
        {
        "codigoINE": "30",
        "codigoPostal": "30001",
        "nombre": "Murcia",
        "direccion": "Gran Vía Salzillo, 22",
        "telefono": "968234567"
        },
        {
        "codigoINE": "31",
        "codigoPostal": "31001",
        "nombre": "Navarra",
        "direccion": "Paseo de Sarasate, 5",
        "telefono": "948345678"
        },
        {
        "codigoINE": "01",
        "codigoPostal": "01001",
        "nombre": "Álava",
        "direccion": "Calle Dato, 4",
        "telefono": "945456789"
        },
        {
        "codigoINE": "20",
        "codigoPostal": "20001",
        "nombre": "Guipúzcoa",
        "direccion": "Calle Mayor, 7",
        "telefono": "943567890"
        },
        {
        "codigoINE": "48",
        "codigoPostal": "48001",
        "nombre": "Vizcaya",
        "direccion": "Calle Gran Vía, 35",
        "telefono": "944678901"
        },
        {
        "codigoINE": "07",
        "codigoPostal": "07001",
        "nombre": "Baleares",
        "direccion": "Calle Sant Miquel, 3",
        "telefono": "971789012"
        },
        {
        "codigoINE": "35",
        "codigoPostal": "35001",
        "nombre": "Las Palmas",
        "direccion": "Calle Triana, 10",
        "telefono": "928890123"
        },
        {
        "codigoINE": "38",
        "codigoPostal": "38001",
        "nombre": "Santa Cruz de Tenerife",
        "direccion": "Calle Castillo, 12",
        "telefono": "922901234"
        },
        {
        "codigoINE": "51",
        "codigoPostal": "51001",
        "nombre": "Ceuta",
        "direccion": "Avenida de África, 5",
        "telefono": "956012345"
        },
        {
        "codigoINE": "52",
        "codigoPostal": "52001",
        "nombre": "Melilla",
        "direccion": "Avenida Juan Carlos I, 1",
        "telefono": "952123456"
        }
    ]

    return str(lista_centros)



# Definición de agentes con herramientas específicas
agente_triaje = Agent(
    name="Agente Triaje",
    instructions="""Eres un agente que trabaja para la empresa RDPOST. Esta empresa se encarga del envío postal de cartas y mensajería.
    Tu tarea es responder los tickets/incidencias que pongan los clientes confusos o insatisfechos de manera amigable y útil.
    Analiza el contenido del ticket y determina el tipo de incidencia.
    - Si la incidencia es sobre entregas o trazabilidad, transfiere al Agente de Entregas.
    - Si la incidencia es sobre reclamaciones por pérdidas o daños, transfiere al Agente de Reclamaciones.
    - Obtén la lista de centros de RDPOST en España si es necesario comunicárselo al cliente. (Es importante que incluyas todos los datos del centro, incluido el número de teléfono)

    Si lo ves conveniente, dale los datos del centro más cercano al cliente para que se pueda poner en contacto.
    Recuerda que tú eres el encargado de dar la respuesta final a la incidencia presentada por el cliente. 
    No puedes decirle que has contacto con otro agente que se pondrá en contacto con él ni nada parecido.
    """,
    model="gpt-4o-2024-05-13",
    functions=[transferir_a_agente_entregas, transferir_a_agente_perdidas, obtener_lista_centros_rdpost_espana]
)

# Manual de Actuación para el Agente de Entregas
manual_actuacion_agente_entregas = '''
# Manual de Actuación para el Agente de Entregas

## Tipos de Incidencias

- Retrasos en la entrega
- Consulta de ubicación actual
- Actualización de estado del envío
- Información sobre visitas realizadas
- Problemas con la dirección de destino

## Procedimientos de Respuesta

### Retrasos en la Entrega

**Pasos a seguir:**

1. Verificación de Datos
   - Confirmar ID del envío
   - Verificar estado actual

2. Comunicación
   - Informar estado actual
   - Explicar razones del retraso
   - Dar nueva estimación

3. Seguimiento
   - Ofrecer asistencia adicional

**Plantilla de Respuesta:**

Hola {nombre_cliente},

He verificado el estado de tu envío {id_envio}. 
Se encuentra en tránsito y la última actualización fue el {fecha_hora}.
Lamentamos el retraso. La nueva estimación de entrega es el {nueva_fecha}.

Si necesitas más información, contáctanos.

Saludos cordiales,
Servicio al cliente RDPOST

### Consulta de Ubicación Actual

**Pasos a seguir:**

1. Verificación
   - Confirmar ID del envío
   - Extraer coordenadas GPS

2. Geocodificación
   - Obtener dirección actual

3. Comunicación
   - Informar ubicación actual
   - Dar detalles adicionales

**Plantilla de Respuesta:**

Hola {nombre_cliente},

He verificado la ubicación de tu envío {id_envio}.
Coordenadas GPS: {coordenadas_gps}
Dirección actual: {direccion_actual}

Tu paquete está en tránsito hacia esta dirección.

Saludos cordiales,
Servicio al cliente RDPOST

### Actualización de Estado

**Pasos a seguir:**

1. Verificación
   - Confirmar ID y nuevo estado
   - Validar actualización

2. Actualización
   - Modificar estado en base de datos

**Plantilla de Respuesta:**

Hola {nombre_cliente},

He actualizado el estado de tu envío {id_envio} a "{nuevo_estado}" el {fecha_hora}.
La entrega se ha realizado en {direccion_destino}.

Gracias por confiar en nosotros.

Saludos,
Servicio al cliente RDPOST

### Información de Visitas

**Pasos a seguir:**

1. Verificación
   - Confirmar ID del envío
   - Extraer lista de visitas

2. Comunicación
   - Detallar cada visita
   - Explicar pasos siguientes

**Plantilla de Respuesta:**

Hola {nombre_cliente},

Las visitas realizadas para tu envío {id_envio} son:
{visita_1}
{visita_2}
{visita_3}

Estado actual: {estado_actual}

Saludos cordiales,
Servicio al cliente RDPOST

### Problemas con Dirección

**Pasos a seguir:**

1. Verificación
   - Confirmar ID y revisar dirección

2. Corrección
   - Actualizar nueva dirección válida

**Plantilla de Respuesta:**

Hola {nombre_cliente},

He actualizado la dirección de tu envío {id_envio}.
Nueva dirección:
{nueva_direccion}

Te mantendremos informado sobre el estado.

Saludos cordiales,
Servicio al cliente RDPOST

## Buenas Prácticas

- Claridad y Concisión
- Empatía
- Profesionalismo
- Precisión
- Proactividad
'''

agente_entregas = Agent(
    name="Agente Entregas",
    instructions=f"""Gestiona incidencias relacionadas con la entrega y trazabilidad de envíos.
    - Verifica los datos del envío.
    - Proporciona estado actual y detalles de las visitas realizadas.
    - Proporciona información sobre la dirección de destino y coordenadas GPS.
    - Obtiene la ubicación actual del envío.
    - Actualiza el estado del envío si es necesario.
    - Obtén la lista de centros de RDPOST en España si es necesario comunicárselo al cliente. (Es importante que incluyas todos los datos del centro, incluido el número de teléfono)

    
    Aquí tienes un manual de actuación que te ayudará a responder a las incidencias:

    {manual_actuacion_agente_entregas}


    """,
    model="gpt-4o-mini-2024-07-18",
    functions=[
        verificar_datos_envio,
        comprobar_estado_trazabilidad,
        verificar_direccion_destino,
        obtener_coordenadas_gps,
        obtener_ubicacion_actual_envio,
        actualizar_estado_envio,
        obtener_lista_centros_rdpost_espana
    ]
)


manual_actuacion_agente_perdidas = '''
# Manual de Actuación para el Agente de Pérdidas y Daños

## Tipos de Incidencias

- Reclamaciones por pérdida del envío
- Reclamaciones por daños en el envío  
- Discrepancias en la cobertura del seguro
- Solicitudes de información adicional

## Procedimientos de Respuesta

### Reclamaciones por Pérdida

**Pasos a seguir:**

1. Verificación de Datos
   - Confirmar ID del envío
   - Verificar estado en base de datos

2. Registro de Reclamación  
   - Crear registro con ID único
   - Recopilar información adicional

3. Comunicación y Seguimiento
   - Informar recepción y ID de reclamación
   - Mantener informado sobre progreso

**Plantilla de Respuesta:**

Hola {nombre_cliente},

He recibido tu reclamación por la pérdida del envío {id_envio}. 
Tu solicitud ha sido registrada con ID: REC-{numero_aleatorio} ({fecha_hora}).

Nuestro equipo investigará los detalles y te contactará en {tiempo_estimado}.
Si tienes información adicional, házmelo saber.

Lamentamos los inconvenientes.

Atentamente,
Servicio al cliente de RDPOST

### Reclamaciones por Daños

**Pasos a seguir:**

1. Verificación
   - Confirmar ID y tipo de daño
   - Revisar evidencias

2. Registro y Documentación
   - Crear registro con ID único
   - Solicitar documentos necesarios

3. Gestión de Indemnización
   - Verificar cobertura del seguro
   - Calcular importe 
   - Procesar pago

**Plantilla de Respuesta:**

Hola {nombre_cliente},

Lamento que tu envío {id_envio} haya llegado dañado.
Tu reclamación ha sido registrada con ID: REC-{numero_aleatorio}.

Según nuestros registros, tu envío tiene un seguro tipo {tipo_seguro} con cobertura de {cobertura}€.
Basado en el daño reportado, la indemnización calculada es de {importe}€.

Te notificaremos cuando el pago se haya procesado.

Atentamente,
Servicio al cliente de RDPOST

### Discrepancias de Seguro

**Pasos a seguir:**

1. Verificación
   - Revisar detalles del seguro
   - Analizar la discrepancia

2. Investigación
   - Consultar términos y condiciones
   - Validar con departamento de seguros

3. Resolución
   - Informar hallazgos
   - Proponer soluciones

**Plantilla de Respuesta:**

Hola {nombre_cliente},

He revisado tu consulta sobre el seguro del envío {id_envio}.
Según nuestra póliza, el seguro {tipo_seguro} cubre hasta {cobertura}€ por {tipo_incidencia}.
Entiendo que hay una discrepancia en la cobertura aplicada. Después de revisar los detalles, podemos {solucion_propuesta}.
Por favor, comunícanos cómo deseas proceder.

Atentamente,
Servicio al cliente de RDPOST

### Solicitudes de Información Adicional

**Pasos a seguir:**

1. Verificación
   - Confirmar ID de la reclamación
   - Revisar estado actual

2. Provisión de Información
   - Informar sobre progreso
   - Notificar acciones pendientes

**Plantilla de Respuesta:**

Hola {nombre_cliente},

Te informo que tu reclamación REC-{numero_aleatorio} para el envío {id_envio} está en proceso.
Hemos completado las etapas iniciales y estamos esperando {proximos_pasos}.
Esperamos concluir tu reclamación antes de {fecha_estimada}.
Cualquier pregunta adicional, contáctanos.

Gracias por tu paciencia.

Atentamente,
Servicio al cliente de RDPOST

## Buenas Prácticas

- Empatía y Comprensión
- Claridad y Transparencia
- Profesionalismo
- Precisión
- Proactividad
- Confidencialidad
'''

agente_perdidas = Agent(
    name="Agente Pérdidas y Daños",
    instructions=f"""Gestiona reclamaciones por pérdidas y daños en los envíos.
    - Registra reclamaciones.
    - Verifica seguros asociados al envío.
    - Calcula indemnizaciones basadas en el tipo de seguro y daño.
    - Proporciona detalles del receptor y visitas realizadas.
    - Obtén la lista de centros de RDPOST en España si es necesario comunicárselo al cliente. (Es importante que incluyas todos los datos del centro, incluido el número de teléfono)
    
    Aquí tienes un manual de actuación que te ayudará a responder a las incidencias:
    
    {manual_actuacion_agente_perdidas}    

    """,
    model="gpt-4o-mini-2024-07-18",
    functions=[registrar_reclamacion, verificar_seguro, calcular_importe_indemnizacion, obtener_detalles_receptor, listar_visitas, obtener_lista_centros_rdpost_espana]
)


def procesar_ticket(contenido_ticket: str, imagen: str):
    """Procesa un ticket usando el sistema multi-agente"""
    if imagen:
        response = client.run(
            agent=agente_triaje,
            messages=[{"role": "user", "content": contenido_ticket + "\n\nDescripcion de la imagen adjuntada por el usuario:\n" + imagen}],
            debug=False
        )
    else:
        response = client.run(
            agent=agente_triaje,
            messages=[{"role": "user", "content": contenido_ticket}],
            debug=False
        )
    return response.messages[-1]["content"]

