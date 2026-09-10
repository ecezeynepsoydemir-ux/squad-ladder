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
    <link rel="icon" type="image/png" href="{{ url_for('static', filename='8.png') }}">
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #0a1118;
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
            max-width: 500px;
            background: #101c28;
            padding: 24px;
            border-radius: 16px;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.6);
            border: 1px solid #1a2a3a;
            text-align: center;
        }
        h1 {
            color: #64b5f6;
            margin-bottom: 20px;
            font-size: 28px;
            letter-spacing: 1px;
        }
        h2 {
            color: #90caf9;
        }
        input, button {
            width: 100%;
            padding: 12px 16px;
            margin: 8px 0;
            border-radius: 8px;
            border: 1px solid #23384e;
            box-sizing: border-box;
            font-size: 16px;
        }
        input {
            background: #162434;
            color: #ffffff;
            outline: none;
        }
        input:focus {
            border-color: #42a5f5;
        }
        button {
            background: #1e88e5;
            color: white;
            font-weight: bold;
            cursor: pointer;
            border: none;
            transition: background 0.2s, transform 0.1s;
        }
        button:hover {
            background: #1565c0;
        }
        button:active {
            transform: scale(0.98);
        }
        .btn-secondary {
            background: #0d47a1;
        }
        .btn-secondary:hover {
            background: #1565c0;
        }
        .btn-start {
            background: #0288d1;
        }
        .btn-start:hover {
            background: #0277bd;
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
            padding: 10px 14px;
            background: #182a3c;
            margin-bottom: 6px;
            border-radius: 6px;
            border-left: 4px solid #42a5f5;
            font-size: 15px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🏆 Squad Ladder 🏆</h1>

        <!-- Giriş Ekranı -->
        <div id="join-screen">
            <input type="text" id="username" placeholder="Oyuncu Adı">
            <input type="text" id="room-code" placeholder="Oda Kodu">
            <button onclick="joinRoom()">Odaya Katıl</button>
            <button onclick="createRoom()" class="btn-secondary">Yeni Oda Oluştur</button>
        </div>

        <!-- Lobi Ekranı -->
        <div id="lobby-screen" class="hidden">
            <h2>Oda Kodu: <span id="display-room-code" style="color:#64b5f6;"></span></h2>
            <h3>Oyuncular:</h3>
            <ul id="player-list" class="player-list"></ul>
            <button id="start-btn" onclick="startGame()" class="btn-start">Oyunu Başlat</button>
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

        function createRoom() {
            username = document.getElementById('username').value.trim();
            if (!username) return alert("Lütfen adınızı girin!");
            
            socket.emit('create_room', { username: username });
        }

        function joinRoom() {
            username = document.getElementById('username').value.trim();
            const room = document.getElementById('room-code').value.trim().toUpperCase();
            
            if (!username || !room) return alert("Ad ve Oda Kodu gerekli!");
            
            currentRoom = room;
            socket.emit('join_room', { username: username, room: room });
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
                li.innerText = p;
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
                               '8.png', mimetype='image/vnd.microsoft.icon')

@socketio.on('create_room')
def handle_create_room(data):
    import random, string
    room_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    username = data.get('username')
    
    rooms[room_code] = {
        'host': username,
        'players': [username]
    }
    
    join_room(room_code)
    emit('room_created', {'room': room_code, 'players': rooms[room_code]['players']})

@socketio.on('join_room')
def handle_join_room(data):
    room = data.get('room')
    username = data.get('username')
    
    if room in rooms:
        rooms[room]['players'].append(username)
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