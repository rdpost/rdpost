#app.py
import os
from flask import Flask, render_template, url_for, redirect, session, request
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from functools import wraps
import json
import requests
from flask import jsonify
import re 

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Used for session

# OAuth2 configuration
GOOGLE_CLIENT_CONFIG = {
    "web": {
        "client_id": "22538919107-k1hrsidarmbooh0iphqidgq9705f13fs.apps.googleusercontent.com",
        "client_secret": "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",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "redirect_uris": ["http://localhost:5000/oauth2callback"]
    }
}

SCOPES = [
    'openid',
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/gmail.send'
]

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'credentials' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    if 'credentials' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/login')
def login():
    flow = Flow.from_client_config(
        GOOGLE_CLIENT_CONFIG,
        scopes=SCOPES,
        redirect_uri=url_for('oauth2callback', _external=True)
    )
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true'
    )
    session['state'] = state
    return redirect(authorization_url)

@app.route('/oauth2callback')
def oauth2callback():
    state = session['state']
    flow = Flow.from_client_config(
        GOOGLE_CLIENT_CONFIG,
        scopes=SCOPES,
        state=state,
        redirect_uri=url_for('oauth2callback', _external=True)
    )
    
    authorization_response = request.url
    flow.fetch_token(authorization_response=authorization_response)
    credentials = flow.credentials
    session['credentials'] = {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
@login_required
def dashboard():
    credentials = Credentials(**session['credentials'])
    service = build('gmail', 'v1', credentials=credentials)
    
    # Fetch emails and categorize them
    tickets = fetch_tickets(service)
    return render_template('dashboard.html', tickets=tickets)

def fetch_tickets(service):
    results = service.users().messages().list(userId='me', maxResults=50).execute()
    messages = results.get('messages', [])
    
    tickets = {
        'needs_supervision': [],
        'auto_answered': [],
        'closed': []
    }
    
    for message in messages:
        msg = service.users().messages().get(userId='me', id=message['id']).execute()
        ticket = process_message(msg)
        
        if 'UNREAD' in msg['labelIds']:
            tickets['needs_supervision'].append(ticket)
        elif len(msg.get('labelIds', [])) > 2:  # Simple way to detect auto-answered
            tickets['auto_answered'].append(ticket)
        else:
            tickets['closed'].append(ticket)
            
    return tickets

# Imports adicionales necesarios
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage

def process_message(msg):
    headers = msg['payload']['headers']
    from_header = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
    
    # Split email into name and address
    if '<' in from_header:
        from_name = from_header.split('<')[0].strip(' "')
        from_email = from_header.split('<')[1].strip('>')
    else:
        from_name = 'Unknown'
        from_email = from_header

    # Process body and images
    body, images = extract_message_content(msg)
    
    return {
        'id': msg['id'],
        'subject': next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject'),
        'from': from_name[0].upper(),
        'from_name': from_name,
        'from_email': from_email,
        'date': next((h['value'] for h in headers if h['name'] == 'Date'), 'No Date'),
        'body': body,
        'images': images
    }

def extract_message_content(message):
    body = ''
    images = []
    
    def decode_body(data):
        if not data:
            return ''
        decoded = base64.urlsafe_b64decode(data.replace("-", "+").replace("_", "/")).decode('utf-8', errors='ignore')
        # Eliminar cualquier referencia a [image:nombre.jpg]
        return re.sub(r'\[image:.*?\]', '', decoded)

    def process_parts(parts):
        nonlocal body, images
        
        for part in parts:
            mime_type = part.get('mimeType', '')
            
            if mime_type == 'text/plain':
                if 'data' in part.get('body', {}):
                    body += decode_body(part['body']['data'])
                    
            elif mime_type.startswith('image/'):
                attachment_id = part['body'].get('attachmentId')
                if attachment_id:
                    images.append({
                        'attachment_id': attachment_id,
                        'mime_type': mime_type,
                        'filename': part.get('filename', 'image')
                    })
                    
            elif mime_type == 'multipart/alternative' or mime_type == 'multipart/mixed':
                if 'parts' in part:
                    process_parts(part['parts'])

    if 'payload' in message:
        if 'parts' in message['payload']:
            process_parts(message['payload']['parts'])
        elif 'body' in message['payload']:
            body = decode_body(message['payload']['body'].get('data', ''))

    return body, images

@app.route('/message/<message_id>')
@login_required
def message_detail(message_id):
    credentials = Credentials(**session['credentials'])
    service = build('gmail', 'v1', credentials=credentials)
    
    try:
        # Obtener el mensaje completo
        message = service.users().messages().get(
            userId='me', 
            id=message_id, 
            format='full'
        ).execute()
        
        # Procesar el mensaje para obtener cuerpo e imágenes
        body, image_attachments = extract_message_content(message)
        
        # Obtener los datos de las imágenes adjuntas
        images = []
        for attachment in image_attachments:
            try:
                attachment_data = service.users().messages().attachments().get(
                    userId='me',
                    messageId=message_id,
                    id=attachment['attachment_id']
                ).execute()
                
                if 'data' in attachment_data:
                    # Obtener los datos en base64 y asegurarse de que son válidos
                    image_data = attachment_data['data']
                    # Reemplazar caracteres especiales si es necesario
                    image_data = image_data.replace('-', '+').replace('_', '/')
                    
                    images.append({
                        'mime_type': attachment['mime_type'],
                        'filename': attachment['filename'],
                        'src': f"data:{attachment['mime_type']};base64,{image_data}"
                    })
                    
                    print(f"Successfully processed image: {attachment['filename']}")
            except Exception as e:
                print(f"Error processing attachment {attachment['attachment_id']}: {str(e)}")
        
        # Crear el objeto de mensaje procesado
        processed_message = {
            'id': message_id,
            'body': body,
            'images': images,
            # Otros campos del mensaje...
            'subject': next((h['value'] for h in message['payload']['headers'] if h['name'].lower() == 'subject'), 'No Subject'),
            'from': next((h['value'] for h in message['payload']['headers'] if h['name'].lower() == 'from'), 'Unknown'),
            'date': next((h['value'] for h in message['payload']['headers'] if h['name'].lower() == 'date'), 'No Date')
        }
        
        # Debug logging
        print(f"Processed message:")
        print(f"- Body length: {len(processed_message['body'])}")
        print(f"- Number of images: {len(processed_message['images'])}")
        print(f"- First 100 chars of body: {processed_message['body'][:100]}")
        
        template_base = """Hi {{sender_name}}, Thank you for reaching out to the support team..."""
        
        return render_template(
            'message_detail.html',
            message=processed_message,
            template_base=template_base
        )
        
    except Exception as e:
        print(f"Error in message_detail: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/generate_draft', methods=['POST'])
@login_required
def generate_draft():
    try:
        data = request.json
        
        payload = {
            "content": data.get('content', '').strip()
        }
        
        # Si hay imagen, incluirla directamente (ya viene en base64)
        if 'image' in data:
            payload['image'] = data['image']
        
        response = requests.post(
            'http://127.0.0.1:8000/process_ticket',
            json=payload
        )
        
        if response.status_code == 200:
            return jsonify({
                'success': True,
                'response': response.json()["response"] if response.content else payload['content']
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Error processing ticket: {response.text}'
            }), 500
            
    except Exception as e:
        print(f"Error in generate_draft: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
    
    
@app.route('/send_email', methods=['POST'])
@login_required
def send_email():
    data = request.json
    credentials = Credentials(**session['credentials'])
    service = build('gmail', 'v1', credentials=credentials)
    
    try:
        # Obtener el mensaje original para extraer los datos del remitente
        message = service.users().messages().get(userId='me', id=data['message_id']).execute()
        headers = message['payload']['headers']
        
        # Obtener el correo del remitente original
        from_header = next((h['value'] for h in headers if h['name'].lower() == 'from'), None)
        if '<' in from_header:
            to_address = from_header.split('<')[1].strip('>')
        else:
            to_address = from_header
            
        # Obtener el asunto original
        subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), 'No Subject')
        
        # Crear el mensaje
        email_message = MIMEMultipart()
        email_message['to'] = to_address
        email_message['subject'] = f"Re: {subject}"
        
        # Añadir el contenido del texto
        text_part = MIMEText(data['content'], 'plain', 'utf-8')
        email_message.attach(text_part)
        
        # Si hay una imagen adjunta, añadirla
        if 'image' in data and data['image']:
            # Extraer el base64 puro si viene con el prefijo
            if ',' in data['image']:
                image_data = data['image'].split(',', 1)[1]
            else:
                image_data = data['image']
                
            try:
                img_binary = base64.b64decode(image_data)
                image_part = MIMEImage(img_binary)
                image_part.add_header('Content-Disposition', 'attachment', filename='image.jpg')
                email_message.attach(image_part)
            except Exception as img_error:
                print(f"Error processing image attachment: {str(img_error)}")
        
        # Codificar y enviar el mensaje
        raw_message = base64.urlsafe_b64encode(email_message.as_bytes()).decode('utf-8')
        try:
            sent_message = service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()
            
            print(f"Message sent successfully. Message Id: {sent_message['id']}")
            return jsonify({
                'success': True,
                'messageId': sent_message['id']
            })
            
        except Exception as send_error:
            print(f"Error sending email: {str(send_error)}")
            return jsonify({
                'success': False,
                'error': 'Failed to send email',
                'details': str(send_error)
            }), 500
            
    except Exception as e:
        print(f"General error in send_email: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to process email request',
            'details': str(e)
        }), 500

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'  # Only for development
    app.run(debug=True, host="0.0.0.0", port=5000)