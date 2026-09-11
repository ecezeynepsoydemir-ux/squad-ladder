from flask import Flask, render_template_string, send_from_directory
from flask_socketio import SocketIO, emit, join_room, leave_room
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'squad-ladder-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*")

rooms = {}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Squad Ladder</title>
    
    <!-- Sekme İkonu (Favicon) -->
    <link rel="icon" type="image/png" href="/static/8.png">
    <link rel="shortcut icon" type="image/png" href="/static/8.png">
    
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #0b131e;
            color: #e3f2fd;
            margin: 0;
            padding: 20px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
        }
        .container {
            width: 100%;
            max-width: 520px;
            background: #121f2d;
            padding: 24px;
            border-radius: 20px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.7);
            border: 1px solid #1e3246;
            text-align: center;
        }
        h1 {
            color: #42a5f5;
            margin-bottom: 8px;
            font-size: 30px;
            letter-spacing: 1px;
        }
        p.subtitle {
            color: #90caf9;
            font-size: 14px;
            margin-top: 0;
            margin-bottom: 20px;
        }
        input, button {
            width: 100%;
            padding: 12px 16px;
            margin: 8px 0;
            border-radius: 10px;
            border: 1px solid #233a52;
            box-sizing: border-box;
            font-size: 16px;
        }
        input {
            background: #182838;
            color: #ffffff;
            outline: none;
        }
        input:focus {
            border-color: #42a5f5;
            box-shadow: 0 0 8px rgba(66, 165, 245, 0.4);
        }
        button {
            background: #1e88e5;
            color: white;
            font-weight: bold;
            cursor: pointer;
            border: none;
            transition: all 0.2s ease;
        }
        button:hover {
            background: #1565c0;
        }
        button:active {
            transform: scale(0.98);
        }
        .btn-tv {
            background: #1976d2;
            font-size: 17px;
        }
        .btn-tv:hover {
            background: #1565c0;
        }
        .character-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 10px;
            margin: 15px 0;
        }
        .avatar-option {
            width: 60px;
            height: 60px;
            border-radius: 50%;
            border: 3px solid transparent;
            cursor: pointer;
            object-fit: cover;
            background: #182838;
            padding: 2px;
            transition: 0.2s;
        }
        .avatar-option:hover {
            transform: scale(1.08);
        }
        .avatar-option.selected {
            border-color: #42a5f5;
            box-shadow: 0 0 12px #42a5f5;
        }
        .color-picker-container {
            margin: 15px 0;
        }
        .color-picker {
            width: 60px;
            height: 35px;
            padding: 0;
            border: none;
            cursor: pointer;
            background: transparent;
        }
        .hidden {
            display: none;
        }
        .player-list {
            list-style: none;
            padding: 0;
            text-align: left;
        }
        .player-list li {
            padding: 12px 16px;
            background: #182838;
            margin-bottom: 8px;
            border-radius: 8px;
            border-left: 5px solid #42a5f5;
            display: flex;
            align-items: center;
            gap: 12px;
        }
        .player-list img {
            width: 36px;
            height: 36px;
            border-radius: 50%;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🏆 Squad Ladder 🏆</h1>
        <p class="subtitle">Televizyon için oda kur veya oyuncu olarak katıl!</p>

        <!-- Giriş Ekranı -->
        <div id="join-screen">
            <button onclick="createRoom()" class="btn-tv">📺 Oda Oluştur (Televizyon Ekranı)</button>

            <div style="margin: 20px 0; border-bottom: 1px solid #1e3246;"></div>
            <h3>Oyuncu Girişi</h3>

            <input type="text" id="username" placeholder="Adını Gir...">

            <p style="margin-bottom: 5px; font-weight: bold;">Karakterini Seç:</p>
            <div class="character-grid">
                <img src="/static/1.png" class="avatar-option selected" onclick="selectAvatar(this, '1.png')">
                <img src="/static/2.png" class="avatar-option" onclick="selectAvatar(this, '2.png')">
                <img src="/static/3.png" class="avatar-option" onclick="selectAvatar(this, '3.png')">
                <img src="/static/4.png" class="avatar-option" onclick="selectAvatar(this, '4.png')">
                <img src="/static/5.png" class="avatar-option" onclick="selectAvatar(this, '5.png')">
                <img src="/static/6.png" class="avatar-option" onclick="selectAvatar(this, '6.png')">
                <img src="/static/7.png" class="avatar-option" onclick="selectAvatar(this, '7.png')">
                <img src="/static/8.png" class="avatar-option" onclick="selectAvatar(this, '8.png')">
                <img src="/static/9.png" class="avatar-option" onclick="selectAvatar(this, '9.png')">
            </div>

            <div class="color-picker-container">
                <label for="color">İsim Rengi:</label><br>
                <input type="color" id="color" class="color-picker" value="#42a5f5">
            </div>

            <input type="text" id="room-code" placeholder="Oda Kodu (Örn: A1B2)">
            <button onclick="joinRoom()">Odaya Katıl</button>
        </div>

        <!-- Lobi Ekranı -->
        <div id="lobby-screen" class="hidden">
            <h2>Oda Kodu: <span id="display-room-code" style="color:#42a5f5;"></span></h2>
            <h3>Oyuncular:</h3>
            <ul id="player-list" class="player-list"></ul>
            <button id="start-btn" onclick="startGame()" style="background:#0288d1; margin-top:15px;">Oyunu Başlat</button>
        </div>

        <!-- Oyun Ekranı -->
        <div id="game-screen" class="hidden">
            <h2>Oyun Başladı!</h2>
            <p>Sıralamanı yap ve liderliğe oyna!</p>
        </div>
    </div>

    <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
    <script>
        const socket = io();
        let currentRoom = "";
        let username = "";
        let selectedAvatar = "1.png";

        function selectAvatar(element, avatar) {
            document.querySelectorAll('.avatar-option').forEach(img => img.classList.remove('selected'));
            element.classList.add('selected');
            selectedAvatar = avatar;
        }

        function createRoom() {
            socket.emit('create_room', { host: true });
        }

        function joinRoom() {
            username = document.getElementById('username').value.trim();
            const room = document.getElementById('room-code').value.trim().toUpperCase();
            const userColor = document.getElementById('color').value;

            if (!username || !room) return alert("Ad ve Oda Kodu girmelisin!");

            currentRoom = room;
            socket.emit('join_room', {
                username: username,
                room: room,
                avatar: selectedAvatar,
                color: userColor
            });
        }

        function startGame() {
            socket.emit('start_game', { room: currentRoom });
        }

        socket.on('room_created', (data) => {
            currentRoom = data.room;
            showLobby(data.room, data.players);
        });

        socket.on('update_players', (data) => {
            showLobby(currentRoom, data.players);
        });

        socket.on('game_started', () => {
            document.getElementById('lobby-screen').classList.add('hidden');
            document.getElementById('game-screen').classList.remove('hidden');
        });

        socket.on('error', (data) => {
            alert(data.message);
        });

        function showLobby(room, players) {
            document.getElementById('join-screen').classList.add('hidden');
            document.getElementById('lobby-screen').classList.remove('hidden');
            document.getElementById('display-room-code').innerText = room;

            const list = document.getElementById('player-list');
            list.innerHTML = '';
            players.forEach(p => {
                const li = document.createElement('li');
                
                const img = document.createElement('img');
                img.src = '/static/' + (p.avatar || '1.png');
                
                const span = document.createElement('span');
                span.innerText = p.username || p;
                if (p.color) span.style.color = p.color;
                span.style.fontWeight = 'bold';

                li.appendChild(img);
                li.appendChild(span);
                list.appendChild(li);
            });
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               '8.png', mimetype='image/png')

@socketio.on('create_room')
def handle_create_room(data):
    import random, string
    room_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    
    rooms[room_code] = {
        'players': []
    }
    
    join_room(room_code)
    emit('room_created', {'room': room_code, 'players': rooms[room_code]['players']})

@socketio.on('join_room')
def handle_join_room(data):
    room = data.get('room')
    username = data.get('username')
    avatar = data.get('avatar', '1.png')
    color = data.get('color', '#42a5f5')
    
    if room in rooms:
        rooms[room]['players'].append({
            'username': username,
            'avatar': avatar,
            'color': color
        })
        join_room(room)
        emit('update_players', {'players': rooms[room]['players']}, to=room)
    else:
        emit('error', {'message': 'Oda bulunamadı!'})

@socketio.on('start_game')
def handle_start_game(data):
    room = data.get('room')
    if room in rooms:
        emit('game_started', to=room)

if __name__ == '__main__':
    socketio.run(app, debug=True)