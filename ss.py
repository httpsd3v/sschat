from flask import Flask, render_template_string, request
from flask_socketio import SocketIO, emit
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'insta-secret'
socketio = SocketIO(app, cors_allowed_origins="*")

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>InstaChat Pro</title>
    <script src="https://cdn.socket.io/4.7.2/socket.io.min.js"></script>
    <style>
        body { 
            background-color: #000; 
            color: white; 
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto;
            display: flex; 
            flex-direction: column; 
            height: 100vh; 
            margin: 0;
        }

        #header { 
            padding: 15px; 
            border-bottom: 1px solid #262626; 
            font-weight: bold; 
            text-align: center; 
            font-size: 18px;
        }

        #messages { 
            flex: 1; 
            overflow-y: auto; 
            padding: 20px; 
            display: flex; 
            flex-direction: column; 
            gap: 10px; 
        }

        .bubble { 
            background: #262626; 
            padding: 10px 15px; 
            border-radius: 18px; 
            max-width: 70%; 
            align-self: flex-start; 
            font-size: 14px; 
            line-height: 1.4;
        }

        .mine { 
            background: #3797f0; 
            align-self: flex-end; 
        }

        .meta {
            font-size: 11px;
            opacity: 0.6;
            margin-top: 4px;
        }

        .system {
            align-self: center;
            background: none;
            font-size: 12px;
            opacity: 0.6;
        }

        #input-area { 
            padding: 15px; 
            display: flex; 
            gap: 10px; 
            border-top: 1px solid #262626; 
        }

        input { 
            flex: 1; 
            background: #000; 
            border: 1px solid #363636; 
            border-radius: 20px; 
            padding: 10px 15px; 
            color: white; 
            outline: none;
        }

        button { 
            background: none; 
            border: none; 
            color: #0095f6; 
            font-weight: bold; 
            cursor: pointer; 
        }

        button:hover {
            opacity: 0.8;
        }
    </style>
</head>
<body>

    <div id="header">InstaChat Pro</div>
    <div id="messages"></div>

    <div id="input-area">
        <input id="msg" placeholder="Message..." autocomplete="off">
        <button onclick="send()">Send</button>
    </div>

<script>
    var socket = io();
    var msgsDiv = document.getElementById('messages');
    var username = prompt("Enter your username:");

    if (!username) username = "Guest_" + Math.floor(Math.random() * 1000);

    function scrollDown() {
        msgsDiv.scrollTop = msgsDiv.scrollHeight;
    }

    socket.on('connect', function() {
        socket.emit('user_join', {user: username});
    });

    socket.on('chat_rx', function(data) {
        var div = document.createElement('div');

        if (data.system) {
            div.className = 'bubble system';
            div.textContent = data.msg;
        } else {
            div.className = 'bubble' + (data.user === username ? ' mine' : '');

            var msgText = document.createElement('div');
            msgText.textContent = data.user + ": " + data.msg;

            var meta = document.createElement('div');
            meta.className = 'meta';
            meta.textContent = data.time;

            div.appendChild(msgText);
            div.appendChild(meta);
        }

        msgsDiv.appendChild(div);
        scrollDown();
    });

    function send() {
        var input = document.getElementById('msg');
        if (input.value.trim() !== "") {
            socket.emit('chat_tx', {
                msg: input.value,
                user: username
            });
            input.value = '';
        }
    }

    document.getElementById('msg')
        .addEventListener("keypress", (e) => {
            if(e.key === 'Enter') send();
        });
</script>

</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@socketio.on('user_join')
def user_join(data):
    emit('chat_rx', {
        'msg': f"{data['user']} joined the chat",
        'system': True
    }, broadcast=True)

@socketio.on('chat_tx')
def handle_message(data):
    emit('chat_rx', {
        'msg': data['msg'],
        'user': data['user'],
        'time': datetime.now().strftime("%H:%M"),
        'system': False
    }, broadcast=True)

if __name__ == '__main__':
    socketio.run(app)
