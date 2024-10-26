# RDPost Support 🚀

Gestiona tus tickets de RDPost. Automatiza los procesos de atención al cliente integrando tus datos con IA, clasificando el contenido y generando respuestas como si las hubiera hecho un miembro de tu equipo.

## Tabla de Contenidos 📑
- [Demostración](#demostración)
- [Requisitos Previos](#requisitos-previos)
- [Instalación](#instalación)
- [Configuración](#configuración)
- [Uso](#uso)
- [API Documentation](#api-documentation)
- [Contribución](#contribución)
- [Licencia](#licencia)

## Demostración 🎥
<!-- Aquí puedes insertar un GIF o enlace a un video demostrando el funcionamiento de tu aplicación -->
[![Video Demo](https://img.shields.io/badge/Video-Demo-red)](LINK_AL_VIDEO)



## Requisitos Previos 📋
- Python 3.8+
- pip
- virtualenv (opcional)
- Otras dependencias específicas...

## Instalación 🔧

### Clonar el repositorio
```bash
git clone https://github.com/usuario/proyecto.git

# Ir al directorio del proyecto
cd rdpost

# Crear y activar entorno virtual (opcional)
python -m venv rdpost_env
source rdpost_env/bin/activate  # En Windows: rdpost_env\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```


### Backend
```bash
# Iniciar el servidor
python backend/api.py
```

### Frontend
```bash
# Iniciar la aplicación
python frontend/app.py
```

## Configuración ⚙️
1. Crea un archivo `.env` en el directorio raíz del backend basado en `.env.example`
2. Configura las variables de entorno necesarias:
   ```env
   OPENAI_API_KEY='your_api_key'
   MISTRAL_API_KEY='your_api_key'
   ```

## Uso 💡
1. Asegúrate de que el backend esté corriendo en `http://localhost:8000`
2. Inicia el frontend que estará disponible en `http://localhost:5000`
3. Accede a la documentación de la API en `http://localhost:8000/docs`

## API Documentation 📚
La documentación detallada de la API está disponible en `/docs/api/README.md`

Endpoints principales:
- `POST /process_ticket` - Procesar ticket

## Contribución 🤝
1. Fork el proyecto
2. Crea una nueva rama (`git checkout -b feature/amazing-feature`)
3. Realiza tus cambios
4. Commit tus cambios (`git commit -m 'Add some amazing feature'`)
5. Push a la rama (`git push origin feature/amazing-feature`)
6. Abre un Pull Request

## Licencia 📄
Este proyecto está bajo la Licencia MIT - mira el archivo [LICENSE.md](LICENSE.md) para detalles