from flask import Flask, render_template_string, send_from_directory
from flask_socketio import SocketIO, emit, join_room, leave_room
import os, random, string

app = Flask(__name__)
app.config['SECRET_KEY'] = 'squad-ladder-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*")

rooms = {}

QUESTIONS = [
    "Liderinizin bu ana kadar yaptığı en komik/sakarlık dolu davranış neydi?",
    "Liderinizi en çok ne çileden çıkarır veya gıcık eder?",
    "Lideriniz bir adaya düşse yanına alacağı 3 şey ne olurdu?",
    "Liderinizin en gizli yeteneği veya kimsenin bilmediği huyu nedir?",
    "Lideriniz bir çizgi film veya film karakteri olsaydı kim olurdu?",
    "Liderinizin en çok kullandığı kelime veya en ünlü lafı nedir?",
    "Liderinizin yaptığı en lezzetli yemek veya sürekli yediği şey nedir?",
    "Liderinizin bir günlüğüne dünyadaki tek kuralı koyma hakkı olsa neyi yasaklardı?",
    "Liderinizin piyangoyu kazansa ilk satın alacağı şey ne olurdu?",
    "Liderinizi tek bir kelimeyle tanımlayacak olsanız bu hangi kelime olurdu?",
    "Liderinizle ilgili unutamadığınız en komik anınız nedir?",
    "Lideriniz bir süper kahraman olsaydı süper gücü ne olurdu?",
    "Liderinizin sabah uyandığında ilk yaptığı şey nedir?",
    "Liderinizin en çok dinlediği veya söylemeyi sevdiği şarkı nedir?",
    "Lideriniz bir zaman makinesi bulsa hangi yıla ve nereye giderdi?"
]

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Squad Ladder</title>

    <!-- Sekme İkonu -->
    <link rel="icon" type="image/png" href="/static/stranger/mutlu-1.png">
    <link rel="shortcut icon" type="image/png" href="/static/stranger/mutlu-1.png">

    <style>
        body {
            font-family: 'Helvetica World', 'Helvetica Neue', Helvetica, Arial, sans-serif;
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
            max-width: 650px;
            background: #121f2d;
            padding: 24px;
            border-radius: 20px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.7);
            border: 1px solid #1e3246;
            text-align: center;
        }
        h1 { color: #42a5f5; margin-bottom: 8px; font-size: 32px; }
        p.subtitle { color: #90caf9; font-size: 14px; margin-top: 0; margin-bottom: 20px; }
        input, button, textarea {
            width: 100%; padding: 12px 16px; margin: 8px 0; border-radius: 10px;
            border: 1px solid #233a52; box-sizing: border-box; font-size: 16px;
            font-family: 'Helvetica World', sans-serif;
        }
        input, textarea { background: #182838; color: #ffffff; outline: none; }
        button { background: #1e88e5; color: white; font-weight: bold; cursor: pointer; border: none; }
        button:hover { background: #1565c0; }

        .character-grid { display: flex; justify-content: center; gap: 15px; margin: 15px 0; }
        .avatar-option { width: 65px; height: 65px; border-radius: 50%; border: 3px solid transparent; cursor: pointer; object-fit: cover; background: #fff; padding: 2px; }
        .avatar-option.selected { border-color: #42a5f5; box-shadow: 0 0 12px #42a5f5; }

        .players-circle-grid { display: flex; flex-wrap: wrap; gap: 20px; justify-content: center; margin: 20px 0; }
        .player-card-circle { display: flex; flex-direction: column; align-items: center; width: 85px; }
        .player-card-circle img { width: 65px; height: 65px; border-radius: 50%; background: #fff; padding: 2px; border: 3px solid #42a5f5; object-fit: cover; }
        .player-card-circle span { margin-top: 6px; font-size: 13px; font-weight: bold; text-align: center; word-break: break-all; }

        .preview-box { margin: 15px 0; padding: 12px; background: #182838; border-radius: 14px; display: flex; flex-direction: column; align-items: center; }
        .preview-avatar { width: 85px; height: 85px; border-radius: 50%; border: 3px solid #42a5f5; background: #fff; padding: 2px; object-fit: cover; }

        /* Merdiven Stilleri */
        .ladder-container { display: flex; flex-direction: column-reverse; gap: 12px; margin-top: 20px; }
        .ladder-step { background: #182838; border: 1px solid #233a52; border-radius: 12px; padding: 10px 16px; display: flex; align-items: center; justify-content: space-between; min-height: 65px; transition: all 0.5s ease; }
        .ladder-step.throne { background: #2c2205; border-color: #ffd700; box-shadow: 0 0 15px rgba(255, 215, 0, 0.4); }

        .leader-banner {
            background: #1e3246;
            border: 2px solid #ffd700;
            color: #ffd700;
            padding: 10px;
            border-radius: 12px;
            font-size: 20px;
            font-weight: bold;
            margin-bottom: 15px;
        }

        .hidden { display: none; }
        .score-btn { width: auto; padding: 10px 18px; margin: 0 4px; font-size: 18px; display: inline-block; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🏆 Squad Ladder 🏆</h1>
        <p class="subtitle">Arkadaşlarını ne kadar iyi tanıyorsun?</p>

        <!-- Giriş Ekranı -->
        <div id="join-screen">
            <button onclick="createRoom()" style="background:#1976d2; font-size:17px;">📺 Oda Oluştur (Televizyon Ekranı)</button>
            <div style="margin: 20px 0; border-bottom: 1px solid #1e3246;"></div>
            <h3>Oyuncu Girişi</h3>
            <input type="text" id="username" placeholder="Adını Gir..." oninput="updatePreview()">
            
            <p style="margin-bottom: 5px; font-weight: bold;">Karakterini Seç:</p>
            <div class="character-grid">
                <img src="/static/stranger/mutlu-1.png" class="avatar-option selected" onclick="selectAvatar(this, '1')">
                <img src="/static/stranger/mutlu-2.png" class="avatar-option" onclick="selectAvatar(this, '2')">
                <img src="/static/stranger/mutlu-3.png" class="avatar-option" onclick="selectAvatar(this, '3')">
                <img src="/static/stranger/mutlu-4.png" class="avatar-option" onclick="selectAvatar(this, '4')">
                <img src="/static/stranger/mutlu-5.png" class="avatar-option" onclick="selectAvatar(this, '5')">
            </div>

            <div style="margin: 10px 0;">
                <label>İsim Rengi: </label>
                <input type="color" id="color" value="#42a5f5" style="width:50px; height:30px; padding:0; border:none; background:none; cursor:pointer;" oninput="updatePreview()">
            </div>

            <div class="preview-box">
                <img id="preview-img" src="/static/stranger/mutlu-1.png" class="preview-avatar">
                <div id="preview-name" style="margin-top:8px; font-weight:bold; color:#42a5f5;">Oyuncu Adı</div>
            </div>

            <input type="text" id="room-code" placeholder="Oda Kodu (Örn: A1B2)">
            <button onclick="joinRoom()">Odaya Katıl</button>
        </div>

        <!-- Lobi Ekranı -->
        <div id="lobby-screen" class="hidden">
            <h2>Oda Kodu: <span id="display-room-code" style="color:#42a5f5;"></span></h2>
            <h3>Oyuncular</h3>
            <div id="player-list-circle" class="players-circle-grid"></div>

            <div id="host-controls" class="hidden">
                <button onclick="startGame()" style="background:#0288d1; margin-top:15px; font-size:18px;">🚀 Oyunu Başlat</button>
            </div>
            <div id="player-wait-msg" class="hidden" style="margin-top:20px; color:#90caf9;">
                <p>⏳ Oyunu başlatan kişinin oyunu başlatması bekleniyor...</p>
            </div>
        </div>

        <!-- TV Ekranı (Merdiven) -->
        <div id="tv-screen" class="hidden">
            <div id="leader-banner-tv" class="leader-banner">👑 Seçilen Lider: -</div>
            <h2 id="tv-question" style="color:#ffd700;"></h2>
            <h3>🏆 Squad Ladder 🏆</h3>
            <div id="ladder-board" class="ladder-container"></div>
        </div>

        <!-- Oyuncu Soru / Cevap Ekranı -->
        <div id="player-game-screen" class="hidden">
            <h3 id="player-question"></h3>
            <div id="answer-area">
                <textarea id="player-answer" rows="3" placeholder="Cevabını buraya yaz..."></textarea>
                <button onclick="submitAnswer()">Cevabı Gönder</button>
            </div>
            <div id="answer-submitted-msg" class="hidden">
                <p style="color:#4caf50;">✅ Cevabın Lidere iletildi! Değerlendirme bekleniyor...</p>
            </div>
        </div>

        <!-- Lider Değerlendirme Ekranı -->
        <div id="leader-screen" class="hidden">
            <h3 style="color:#ffd700;">👑 Sen Lidersin! Cevapları Değerlendir:</h3>
            <div id="answers-to-grade"></div>
        </div>
    </div>

    <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
    <script>
        const socket = io();
        let currentRoom = "";
        let isHost = false;
        let selectedCharId = "1";
        let idleTimeouts = {};

        function selectAvatar(element, charId) {
            document.querySelectorAll('.avatar-option').forEach(img => img.classList.remove('selected'));
            element.classList.add('selected');
            selectedCharId = charId;
            updatePreview();
        }

        function updatePreview() {
            const name = document.getElementById('username').value.trim();
            const color = document.getElementById('color').value;
            document.getElementById('preview-img').src = `/static/stranger/mutlu-${selectedCharId}.png`;
            const nameDisp = document.getElementById('preview-name');
            nameDisp.innerText = name ? name : "Oyuncu Adı";
            nameDisp.style.color = color;
        }

        function createRoom() {
            isHost = true;
            socket.emit('create_room');
        }

        function joinRoom() {
            const name = document.getElementById('username').value.trim();
            const room = document.getElementById('room-code').value.trim().toUpperCase();
            const color = document.getElementById('color').value;

            if (!name || !room) return alert("Lütfen adını ve oda kodunu gir!");

            currentRoom = room;
            socket.emit('join_room', { username: name, room: room, char_id: selectedCharId, color: color });
        }

        function startGame() {
            socket.emit('start_game', { room: currentRoom });
        }

        function submitAnswer() {
            const ans = document.getElementById('player-answer').value.trim();
            if (!ans) return alert("Lütfen bir cevap yaz!");
            socket.emit('submit_answer', { room: currentRoom, answer: ans });
            document.getElementById('answer-area').classList.add('hidden');
            document.getElementById('answer-submitted-msg').classList.remove('hidden');
        }

        function gradeAnswer(targetSid, points) {
            socket.emit('grade_answer', { room: currentRoom, target_sid: targetSid, points: points });
        }

        socket.on('room_created', (data) => {
            currentRoom = data.room;
            document.getElementById('join-screen').classList.add('hidden');
            document.getElementById('lobby-screen').classList.remove('hidden');
            document.getElementById('host-controls').classList.remove('hidden');
            document.getElementById('display-room-code').innerText = data.room;
        });

        socket.on('update_players', (data) => {
            if (!isHost) {
                document.getElementById('join-screen').classList.add('hidden');
                document.getElementById('lobby-screen').classList.remove('hidden');
                document.getElementById('player-wait-msg').classList.remove('hidden');
                document.getElementById('display-room-code').innerText = currentRoom;
            }

            const grid = document.getElementById('player-list-circle');
            grid.innerHTML = '';
            data.players.forEach(p => {
                const card = document.createElement('div');
                card.className = 'player-card-circle';
                card.innerHTML = `<img src="/static/stranger/mutlu-${p.char_id}.png">
                                  <span style="color:${p.color};">${p.username}</span>`;
                grid.appendChild(card);
            });
        });

        socket.on('game_started', (data) => {
            document.getElementById('lobby-screen').classList.add('hidden');

            if (isHost) {
                document.getElementById('tv-screen').classList.remove('hidden');
                document.getElementById('leader-banner-tv').innerText = "👑 Seçilen Lider: " + data.leader_name;
                document.getElementById('tv-question').innerText = "Soru: " + data.question;
                renderLadder(data.players, null);
            } else if (socket.id === data.leader_sid) {
                document.getElementById('leader-screen').classList.remove('hidden');
            } else {
                document.getElementById('player-game-screen').classList.remove('hidden');
                document.getElementById('player-question').innerText = data.question;
            }
        });

        socket.on('new_answers', (answers) => {
            const container = document.getElementById('answers-to-grade');
            container.innerHTML = '';
            answers.forEach(a => {
                const div = document.createElement('div');
                div.style.background = '#182838';
                div.style.padding = '12px';
                div.style.margin = '10px 0';
                div.style.borderRadius = '10px';
                div.innerHTML = `<p style="font-size:18px;">"${a.answer}"</p>
                    <button class="score-btn" style="background:#4caf50;" onclick="gradeAnswer('${a.sid}', 10)">✅ (+10)</button>
                    <button class="score-btn" style="background:#ff9800;" onclick="gradeAnswer('${a.sid}', 5)">⭕ (+5)</button>
                    <button class="score-btn" style="background:#f44336;" onclick="gradeAnswer('${a.sid}', -5)">❌ (-5)</button>`;
                container.appendChild(div);
            });
        });

        socket.on('update_ladder', (data) => {
            if (isHost) {
                renderLadder(data.players, data.changed_sid);
            }
        });

        socket.on('error', (data) => {
            alert(data.message);
        });

        function renderLadder(players, changedSid) {
            const board = document.getElementById('ladder-board');
            board.innerHTML = '';

            const sorted = [...players].sort((a, b) => b.score - a.score);
            const totalPlayers = sorted.length;

            sorted.forEach((p, idx) => {
                const isTop = idx === 0;
                
                // İlk 2 için mutlu, son 3 için aglayan durumu
                let statusPrefix = "mutlu";
                if (totalPlayers >= 5 && idx >= totalPlayers - 3) {
                    statusPrefix = "aglayan";
                } else if (idx < 2) {
                    statusPrefix = "mutlu";
                } else {
                    statusPrefix = "duz";
                }

                // Hareket eden oyuncu için "cikan" durumu
                if (changedSid && p.sid === changedSid) {
                    statusPrefix = "cikan";
                    if (idleTimeouts[p.sid]) clearTimeout(idleTimeouts[p.sid]);
                    
                    // 2.5 saniye sonra "yan" durumuna geçiş
                    idleTimeouts[p.sid] = setTimeout(() => {
                        const imgElem = document.getElementById(`avatar-img-${p.sid}`);
                        if (imgElem) imgElem.src = `/static/stranger/yan-${p.char_id}.png`;
                    }, 2500);
                }

                const step = document.createElement('div');
                step.className = 'ladder-step ' + (isTop ? 'throne' : '');
                step.innerHTML = `
                    <div style="display:flex; align-items:center; gap:12px;">
                        <span style="font-size:20px; font-weight:bold;">${isTop ? '👑 1.' : (idx + 1) + '.'}</span>
                        <img id="avatar-img-${p.sid}" src="/static/stranger/${statusPrefix}-${p.char_id}.png" style="width:50px; height:50px; border-radius:50%; background:#fff; object-fit:cover;">
                        <span style="color:${p.color}; font-weight:bold; font-size:18px;">${p.username}</span>
                    </div>
                    <div style="font-size:22px; font-weight:bold; color:#42a5f5;">${p.score} Puan</div>
                `;
                board.appendChild(step);
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
    return send_from_directory(os.path.join(app.root_path, 'static', 'stranger'), 'mutlu-1.png', mimetype='image/png')

@socketio.on('create_room')
def handle_create_room():
    from flask import request
    room_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    rooms[room_code] = {
        'host_sid': request.sid,
        'players': {},
        'answers': [],
        'question': random.choice(QUESTIONS)
    }
    join_room(room_code)
    emit('room_created', {'room': room_code})

@socketio.on('join_room')
def handle_join_room(data):
    from flask import request
    room = data.get('room')
    if room in rooms:
        rooms[room]['players'][request.sid] = {
            'sid': request.sid,
            'username': data.get('username'),
            'char_id': data.get('char_id', '1'),
            'color': data.get('color', '#42a5f5'),
            'score': 0
        }
        join_room(room)
        emit('update_players', {'players': list(rooms[room]['players'].values())}, to=room)

@socketio.on('start_game')
def handle_start_game(data):
    room = data.get('room')
    if room in rooms:
        players_list = list(rooms[room]['players'].values())
        if len(players_list) < 3:
            emit('error', {'message': 'Oyunu başlatmak için en az 3 oyuncu gereklidir!'})
            return
        
        leader = random.choice(players_list)
        question = rooms[room]['question']
        
        emit('game_started', {
            'question': question,
            'leader_sid': leader['sid'],
            'leader_name': leader['username'],
            'players': players_list
        }, to=room)

@socketio.on('submit_answer')
def handle_submit_answer(data):
    from flask import request
    room = data.get('room')
    if room in rooms:
        rooms[room]['answers'].append({
            'sid': request.sid,
            'answer': data.get('answer')
        })
        emit('new_answers', rooms[room]['answers'], to=room)

@socketio.on('grade_answer')
def handle_grade_answer(data):
    room = data.get('room')
    target_sid = data.get('target_sid')
    points = data.get('points')
    
    if room in rooms and target_sid in rooms[room]['players']:
        rooms[room]['players'][target_sid]['score'] += points
        emit('update_ladder', {
            'players': list(rooms[room]['players'].values()),
            'changed_sid': target_sid
        }, to=room)

if __name__ == '__main__':
    socketio.run(app, debug=True)