import random
import webbrowser
from flask import Flask, render_template_string, request
from flask_socketio import SocketIO, emit, join_room

app = Flask(__name__)
app.config['SECRET_KEY'] = 'gizli_anahtar_bff'
socketio = SocketIO(app, cors_allowed_origins="*")

rooms = {}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <title>BFF Ranker</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.5.4/socket.io.min.js"></script>
    <style>
        /* Açık Renk Tema Tasarımı */
        body { font-family: 'Segoe UI', Tahoma, sans-serif; background: #f0f2f5; color: #333; text-align: center; margin: 0; padding: 20px; }
        .container { max-width: 650px; margin: auto; background: #ffffff; padding: 30px; border-radius: 20px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); border: 2px solid #e1e4e8; }
        input, button { padding: 12px; margin: 10px 0; width: 80%; font-size: 16px; border-radius: 10px; border: 2px solid #ccc; outline: none; }
        input:focus { border-color: #3498db; }
        button { background: #ff4757; color: white; cursor: pointer; font-weight: bold; border: none; transition: 0.2s; }
        button:hover { background: #ff6b81; }
        .hidden { display: none !important; }
        
        /* Büyük Ana Önizleme */
        .preview-container { display: flex; flex-direction: column; align-items: center; margin: 15px 0; }
        .main-avatar-circle { width: 120px; height: 120px; border-radius: 50%; border: 5px solid #f1c40f; overflow: hidden; background: #fff; box-shadow: 0 4px 10px rgba(0,0,0,0.15); }
        .main-preview-img { width: 100%; height: 100%; object-fit: cover; transform: scale(1.5); }

        /* Görsel Karakter Seçim Izgarası */
        .avatar-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 10px; justify-content: center; margin: 15px auto; width: 90%; }
        .grid-item { width: 55px; height: 55px; border-radius: 50%; border: 3px solid #ddd; overflow: hidden; background: #fff; cursor: pointer; transition: 0.2s; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        .grid-item img { width: 100%; height: 100%; object-fit: cover; transform: scale(1.5); }
        .grid-item.selected { border-color: #2ed573; transform: scale(1.1); box-shadow: 0 0 12px rgba(46,213,115,0.5); }

        .stairs-container { display: flex; flex-direction: column-reverse; align-items: center; gap: 10px; margin-top: 20px; padding: 20px; background: #e8ecf1; border-radius: 15px; }
        .stair-step { width: 80%; background: #ffffff; border: 3px solid #ff4757; border-radius: 10px; padding: 12px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 4px 6px rgba(0,0,0,0.05); color: #333; }
        .crown-step { background: #fff3cd; border-color: #ffa502; box-shadow: 0 0 15px rgba(255,165,2,0.4); }
        
        .vote-btn-group { display: flex; justify-content: center; gap: 20px; margin-top: 20px; }
        .circle-btn { width: 70px; height: 70px; border-radius: 50%; font-size: 28px; cursor: pointer; border: none; display: flex; align-items: center; justify-content: center; color: white; box-shadow: 0 4px 8px rgba(0,0,0,0.2); }
        .btn-yes { background: #2ed573; }
        .btn-mid { background: #ffa502; }
        .btn-no { background: #ff4757; }
    </style>
</head>
<body>
    <div class="container" id="menu-screen">
        <h1 style="color: #2f3542;">🏆 BFF RANKER 🏆</h1>
        <p style="color: #57606f;">Televizyon için oda kur veya oyuncu olarak katıl!</p>
        
        <button onclick="createRoom()" style="background: #2ed573; font-size: 18px; padding: 15px;">📺 Oda Oluştur (Televizyon Ekranı)</button><br>
        <hr style="border: 0; border-top: 1px solid #dfe4ea; margin: 20px 0;">
        
        <h3 style="color: #2f3542;">Oyuncu Girişi</h3>
        <input type="text" id="username" placeholder="Adını Gir..." maxlength="15"><br>
        
        <p style="margin: 5px 0; font-size: 14px; color: #57606f;">Karakterini Seç:</p>
        <div class="avatar-grid" id="avatar-grid"></div>

        <div class="preview-container">
            <div class="main-avatar-circle" id="preview-circle">
                <img id="avatar-preview" class="main-preview-img" src="/static/1.png" alt="Seçilen Karakter">
            </div>
            <label style="font-size: 14px; margin-top: 10px; color: #57606f;">İsim Rengi:</label>
            <input type="color" id="color-select" value="#ff4757" onchange="updateColor()" style="width: 80px; height: 35px; padding: 0; cursor: pointer; border-radius: 6px; border: 2px solid #ccc;">
        </div>

        <button onclick="showJoinScreen()" style="background: #3742fa;">Odaya Katıl</button>
    </div>

    <div class="container hidden" id="join-screen">
        <h2 style="color: #2f3542;">Odaya Katıl</h2>
        <input type="text" id="room-code-input" placeholder="Oda Kodunu Gir (Örn: AB12CD)" maxlength="6"><br>
        <button onclick="joinRoom()" style="background: #3742fa;">Giriş Yap</button>
        <button onclick="backToMenu()" style="background: #a4b0be;">Geri</button>
    </div>

    <div class="container hidden" id="lobby-screen">
        <h2 style="color: #2f3542;">Oda Bekleme Ekranı</h2>
        <p style="color: #57606f;">Oda Kodun:</p>
        <h1 id="display-room-code" style="color: #ff4757; letter-spacing: 3px; font-size: 36px;"></h1>
        <p style="color: #57606f;">Bağlanan Oyuncular:</p>
        <ul id="player-list" style="list-style: none; padding: 0; font-size: 18px;"></ul>
        <button id="start-game-btn" class="hidden" onclick="startGame()" style="background: #2ed573;">Oyunu Başlat 🚀</button>
    </div>

    <div class="container hidden" id="game-screen">
        <h3 id="role-title" style="color: #2f3542;">Rol yükleniyor...</h3>
        <p id="question-box" style="font-size: 20px; color: #ff4757; font-weight: bold;"></p>
        
        <div id="answer-section">
            <textarea id="player-answer" rows="3" placeholder="Cevabını buraya yaz..." style="width: 80%; border-radius: 8px; padding: 10px; border: 2px solid #ccc;"></textarea><br>
            <button onclick="submitAnswer()">Cevabı Gönder</button>
        </div>

        <div id="leader-voting-section" class="hidden">
            <p style="color: #57606f;">Gelen Cevap (Kimden geldiği gizli):</p>
            <h2 id="current-eval-answer" style="background: #f1f2f6; color: #2f3542; padding: 15px; border-radius: 10px; border: 2px solid #dfe4ea;"></h2>
            <div class="vote-btn-group">
                <button class="circle-btn btn-no" onclick="voteAnswer('bad')">❌</button>
                <button class="circle-btn btn-mid" onclick="voteAnswer('medium')">🤝</button>
                <button class="circle-btn btn-yes" onclick="voteAnswer('good')">✔</button>
            </div>
        </div>
        
        <div id="waiting-msg" class="hidden">
            <h3 style="color: #57606f;">Diğer oyuncular veya lider bekleniyor...</h3>
        </div>
    </div>

    <div class="container hidden" id="scoreboard-screen">
        <h2 style="color: #2f3542;">📊 MERDİVEN SKOR TABLOSU 📊</h2>
        <div class="stairs-container" id="stairs-list"></div>
        <button id="next-q-btn" class="hidden" onclick="nextQuestion()" style="background: #3742fa; margin-top: 20px;">Sonraki Soruya Geç ➡</button>
    </div>

    <script>
        const socket = io();
        let currentRoomCode = "";
        let isHost = false;
        let selectedAvatar = "1.png";
        let activeAnswerForLeader = "";

        window.onload = function() {
            const grid = document.getElementById('avatar-grid');
            for (let i = 1; i <= 10; i++) {
                let filename = i + ".png";
                let div = document.createElement('div');
                div.className = "grid-item" + (i === 1 ? " selected" : "");
                div.innerHTML = `<img src="/static/${filename}" alt="Karakter ${i}">`;
                div.onclick = function() {
                    document.querySelectorAll('.grid-item').forEach(el => el.classList.remove('selected'));
                    div.classList.add('selected');
                    selectedAvatar = filename;
                    document.getElementById('avatar-preview').src = "/static/" + filename;
                };
                grid.appendChild(div);
            }
        };

        function updateColor() {
            const selectedColor = document.getElementById('color-select').value;
            document.getElementById('preview-circle').style.borderColor = selectedColor;
        }

        function createRoom() {
            isHost = true;
            socket.emit('create_room');
        }

        socket.on('room_created', (data) => {
            currentRoomCode = data.room_code;
            document.getElementById('display-room-code').innerText = currentRoomCode;
            document.getElementById('menu-screen').classList.add('hidden');
            document.getElementById('lobby-screen').classList.remove('hidden');
            document.getElementById('start-game-btn').classList.remove('hidden');
        });

        function showJoinScreen() {
            const username = document.getElementById('username').value.trim();
            if(!username) { alert("Lütfen önce adını yaz!"); return; }
            document.getElementById('menu-screen').classList.add('hidden');
            document.getElementById('join-screen').classList.remove('hidden');
        }

        function backToMenu() {
            document.getElementById('join-screen').classList.add('hidden');
            document.getElementById('menu-screen').classList.remove('hidden');
        }

        function joinRoom() {
            const username = document.getElementById('username').value.trim();
            const color = document.getElementById('color-select').value;
            const room_code = document.getElementById('room-code-input').value.trim();
            
            if(!room_code) { alert("Oda kodunu gir!"); return; }
            socket.emit('join_room', { room_code, username, avatar: selectedAvatar, color });
        }

        socket.on('join_success', (data) => {
            currentRoomCode = data.room_code;
            document.getElementById('display-room-code').innerText = currentRoomCode;
            document.getElementById('join-screen').classList.add('hidden');
            document.getElementById('lobby-screen').classList.remove('hidden');
        });

        socket.on('update_lobby', (data) => {
            const list = document.getElementById('player-list');
            list.innerHTML = "";
            data.players.forEach(p => {
                let li = document.createElement('li');
                li.style.margin = "10px 0";
                li.innerHTML = `<div style="width:45px; height:45px; border-radius:50%; border:2px solid ${p.color}; overflow:hidden; background:white; display:inline-block; vertical-align:middle; margin-right:10px;"><img src="/static/${p.avatar}" style="width:100%; height:100%; object-fit:cover; transform:scale(1.5);"></div> <span style="color: ${p.color}; font-weight: bold; font-size: 20px;">${p.name}</span>`;
                list.appendChild(li);
            });
        });

        function startGame() {
            socket.emit('start_game', { room_code: currentRoomCode });
        }

        socket.on('game_started', (data) => {
            document.getElementById('lobby-screen').classList.add('hidden');
            document.getElementById('scoreboard-screen').classList.add('hidden');
            document.getElementById('game-screen').classList.remove('hidden');
            document.getElementById('question-box').innerText = data.question;

            if (data.is_host) {
                document.getElementById('role-title').innerText = "📺 TELEVİZYON EKRANI (Sunucu)";
                document.getElementById('answer-section').classList.add('hidden');
                document.getElementById('waiting-msg').classList.remove('hidden');
                document.getElementById('leader-voting-section').classList.add('hidden');
            } else if (data.is_leader) {
                document.getElementById('role-title').innerText = "👑 BU TURUN LİDERSİN! Gelen cevapları oyluyorsun.";
                document.getElementById('answer-section').classList.add('hidden');
                document.getElementById('waiting-msg').classList.add('hidden');
                document.getElementById('leader-voting-section').classList.remove('hidden');
            } else {
                document.getElementById('role-title').innerText = `Liderimiz: ${data.leader_name}`;
                document.getElementById('answer-section').classList.remove('hidden');
                document.getElementById('waiting-msg').classList.add('hidden');
                document.getElementById('leader-voting-section').classList.add('hidden');
            }
        });

        function submitAnswer() {
            const answer = document.getElementById('player-answer').value.trim();
            if(!answer) { alert("Boş cevap gönderemezsin!"); return; }
            socket.emit('submit_answer', { room_code: currentRoomCode, answer });
            document.getElementById('answer-section').classList.add('hidden');
            document.getElementById('waiting-msg').classList.remove('hidden');
        }

        socket.on('start_voting', (data) => {
            document.getElementById('waiting-msg').classList.add('hidden');
            document.getElementById('leader-voting-section').classList.remove('hidden');
            window.currentAnswersToVote = data.answers;
            loadNextAnswerForVote();
        });

        function loadNextAnswerForVote() {
            if (window.currentAnswersToVote.length > 0) {
                activeAnswerForLeader = window.currentAnswersToVote[0];
                document.getElementById('current-eval-answer').innerText = activeAnswerForLeader;
            }
        }

        function voteAnswer(voteType) {
            socket.emit('leader_vote', { room_code: currentRoomCode, answer_text: activeAnswerForLeader, vote_type: voteType });
            window.currentAnswersToVote.shift();
            if (window.currentAnswersToVote.length > 0) {
                loadNextAnswerForVote();
            } else {
                document.getElementById('leader-voting-section').classList.add('hidden');
                document.getElementById('waiting-msg').classList.remove('hidden');
            }
        }

        socket.on('waiting_for_leader', () => {
            document.getElementById('answer-section').classList.add('hidden');
            document.getElementById('waiting-msg').classList.remove('hidden');
        });

        socket.on('show_scoreboard', (data) => {
            document.getElementById('game-screen').classList.add('hidden');
            document.getElementById('scoreboard-screen').classList.remove('hidden');
            const stairsList = document.getElementById('stairs-list');
            stairsList.innerHTML = "";

            data.scores.forEach((p, index) => {
                let stepDiv = document.createElement('div');
                stepDiv.className = "stair-step";
                let avatarImg = `<div style="width:40px; height:40px; border-radius:50%; border:2px solid ${p.color}; overflow:hidden; background:white; display:inline-block; vertical-align:middle; margin-right:8px;"><img src="/static/${p.avatar}" style="width:100%; height:100%; object-fit:cover; transform:scale(1.5);"></div>`;
                
                if (index === 0) {
                    stepDiv.classList.add('crown-step');
                    stepDiv.innerHTML = `<span>👑 <b>KRAL KOLTUĞU</b> - ${avatarImg}<span style="color:${p.color}; font-weight:bold; font-size:18px;">${p.name}</span></span> <span>${p.score} Puan</span>`;
                } else {
                    stepDiv.innerHTML = `<span>Basamak ${data.scores.length - index} - ${avatarImg}<span style="color:${p.color}; font-weight:bold; font-size:18px;">${p.name}</span></span> <span>${p.score} Puan</span>`;
                }
                stairsList.appendChild(stepDiv);
            });

            if (isHost) {
                document.getElementById('next-q-btn').classList.remove('hidden');
            }
        });

        function nextQuestion() {
            socket.emit('next_question', { room_code: currentRoomCode });
        }

        socket.on('game_over', () => {
            alert("Oyun bitti! Tüm sorular tamamlandı.");
            location.reload();
        });

        socket.on('error', (data) => { alert(data.message); });
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@socketio.on('create_room')
def handle_create_room():
    room_code = ''.join(random.choices('ABCDEFGHJKLMNPQRSTUVWXYZ23456789', k=6))
    
    rooms[room_code] = {
        'host': request.sid,
        'players': {},
        'state': 'waiting',
        'current_question_index': 0,
        'questions': [
            "Liderinizin bu ana kadar yaptığı en komik davranış neydi?",
            "Lideriniz sizin gizli gizli ne yaptığınızı düşünüyor?",
            "Liderinizin en belirgin takıntısı veya tuhaf huyu nedir?"
        ],
        'current_leader': None,
        'answers': {},
        'shuffled_answers': []
    }
    join_room(room_code)
    emit('room_created', {'room_code': room_code})

@socketio.on('join_room')
def handle_join_room(data):
    room_code = data.get('room_code', '').upper()
    username = data.get('username')
    avatar = data.get('avatar', '1.png')
    color = data.get('color', '#ff4757')
    
    if room_code in rooms and rooms[room_code]['state'] == 'waiting':
        join_room(room_code)
        rooms[room_code]['players'][request.sid] = {'name': username, 'avatar': avatar, 'color': color, 'score': 0}
        
        player_list = [{'name': p['name'], 'avatar': p['avatar'], 'color': p['color']} for p in rooms[room_code]['players'].values()]
        socketio.emit('update_lobby', {'players': player_list}, room=room_code)
        emit('join_success', {'room_code': room_code})
    else:
        emit('error', {'message': 'Oda bulunamadı veya oyun başladı!'})

@socketio.on('start_game')
def handle_start_game(data):
    room_code = data.get('room_code')
    if room_code in rooms and rooms[room_code]['host'] == request.sid:
        p_sids = list(rooms[room_code]['players'].keys())
        if len(p_sids) < 2:
            emit('error', {'message': 'Oyunu başlatmak için en az 2 oyuncu gerekiyor!'})
            return
            
        leader_sid = random.choice(p_sids)
        rooms[room_code]['current_leader'] = leader_sid
        rooms[room_code]['state'] = 'playing'
        rooms[room_code]['answers'] = {}
        
        leader_name = rooms[room_code]['players'][leader_sid]['name']
        question = rooms[room_code]['questions'][rooms[room_code]['current_question_index']]
        
        socketio.emit('game_started', {'is_host': True, 'is_leader': False, 'leader_name': leader_name, 'question': question}, room=rooms[room_code]['host'])
        
        for sid in p_sids:
            is_leader = (sid == leader_sid)
            socketio.emit('game_started', {'is_host': False, 'is_leader': is_leader, 'leader_name': leader_name, 'question': question}, room=sid)

@socketio.on('submit_answer')
def handle_submit_answer(data):
    room_code = data.get('room_code')
    answer = data.get('answer')
    
    if room_code in rooms:
        room = rooms[room_code]
        if request.sid == room['current_leader'] or request.sid == room['host']:
            return
        room['answers'][request.sid] = answer
        
        total_answering_players = len(room['players']) - 1
        if len(room['answers']) >= total_answering_players:
            room['state'] = 'voting'
            ans_list = list(room['answers'].values())
            random.shuffle(ans_list)
            room['shuffled_answers'] = ans_list
            socketio.emit('start_voting', {'answers': ans_list}, room=room['current_leader'])

@socketio.on('leader_vote')
def handle_leader_vote(data):
    room_code = data.get('room_code')
    answer_text = data.get('answer_text')
    vote_type = data.get('vote_type')
    
    if room_code in rooms:
        room = rooms[room_code]
        if request.sid != room['current_leader']:
            return
            
        points = 20 if vote_type == 'good' else (10 if vote_type == 'medium' else -5)
        
        for sid, ans in room['answers'].items():
            if ans == answer_text:
                room['players'][sid]['score'] += points
                break
                
        if answer_text in room['shuffled_answers']:
            room['shuffled_answers'].remove(answer_text)
            
        if len(room['shuffled_answers']) == 0:
            room['state'] = 'scoreboard'
            score_board = [{'name': p['name'], 'avatar': p['avatar'], 'color': p['color'], 'score': p['score']} for p in room['players'].values()]
            score_board = sorted(score_board, key=lambda x: x['score'], reverse=True)
            socketio.emit('show_scoreboard', {'scores': score_board}, room=room_code)

@socketio.on('next_question')
def handle_next_question(data):
    room_code = data.get('room_code')
    if room_code in rooms and rooms[room_code]['host'] == request.sid:
        room = rooms[room_code]
        room['current_question_index'] += 1
        if room['current_question_index'] < len(room['questions']):
            p_sids = list(room['players'].keys())
            leader_sid = random.choice(p_sids)
            room['current_leader'] = leader_sid
            room['state'] = 'playing'
            room['answers'] = {}
            leader_name = room['players'][leader_sid]['name']
            question = room['questions'][room['current_question_index']]
            
            socketio.emit('game_started', {'is_host': True, 'is_leader': False, 'leader_name': leader_name, 'question': question}, room=room['host'])
            for sid in p_sids:
                socketio.emit('game_started', {'is_host': False, 'is_leader': (sid == leader_sid), 'leader_name': leader_name, 'question': question}, room=sid)
        else:
            socketio.emit('game_over', {}, room=room_code)

if __name__ == '__main__':
    webbrowser.open('http://127.0.0.1:5001')
    socketio.run(app, host='0.0.0.0', port=5001, debug=False)