import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template_string, request
from flask_socketio import SocketIO, emit, join_room, leave_room
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret'
socketio = SocketIO(app, cors_allowed_origins="*")

HTML = """
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>InstaChat Live</title>
<script src="https://cdn.socket.io/4.7.2/socket.io.min.js"></script>

<style>
body{
    margin:0;
    background:#000;
    color:white;
    font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto;
    display:flex;
    flex-direction:column;
    height:100vh;
}

#header{
    padding:15px;
    border-bottom:1px solid #222;
    text-align:center;
    font-weight:bold;
}

#messages{
    flex:1;
    overflow-y:auto;
    padding:15px;
    display:flex;
    flex-direction:column;
    gap:8px;
}

.bubble{
    background:#262626;
    padding:8px 12px;
    border-radius:18px;
    max-width:70%;
}

.mine{
    background:#3797f0;
    align-self:flex-end;
}

.meta{
    font-size:10px;
    opacity:0.6;
    margin-top:4px;
}

#typing{
    padding:0 15px;
    font-size:12px;
    opacity:0.7;
    height:18px;
}

#input-area{
    display:flex;
    padding:10px;
    border-top:1px solid #222;
}

input{
    flex:1;
    background:#000;
    border:1px solid #333;
    color:white;
    padding:8px;
    border-radius:20px;
}

button{
    margin-left:10px;
    background:none;
    border:none;
    color:#0095f6;
    font-weight:bold;
    cursor:pointer;
}
</style>
</head>
<body>

<div id="header">🌍 Public Chat</div>
<div id="messages"></div>
<div id="typing"></div>

<div id="input-area">
    <input id="msg" placeholder="Message..." autocomplete="off">
    <button onclick="send()">Send</button>
</div>

<script>
var socket = io();
var messagesDiv = document.getElementById("messages");
var typingDiv = document.getElementById("typing");
var username = localStorage.getItem("username");

// Prompt for username until provided
while(!username){
    username = prompt("Enter your username:");
    if(username) localStorage.setItem("username", username);
}

// Notification permission
if(Notification.permission !== "granted") Notification.requestPermission();

// Notification sound
var ding = new Audio("https://www.soundjay.com/buttons/sounds/button-3.mp3");

// ---------- Load Stored Messages ----------
function loadMessages(){
    var saved = localStorage.getItem("chat_history");
    if(saved){
        var msgs = JSON.parse(saved);
        msgs.forEach(displayMessage);
    }
}

// ---------- Save Messages ----------
function saveMessage(data){
    var msgs = localStorage.getItem("chat_history");
    msgs = msgs ? JSON.parse(msgs) : [];
    msgs.push(data);
    localStorage.setItem("chat_history", JSON.stringify(msgs));
}

// ---------- Display ----------
function displayMessage(data){
    var div = document.createElement("div");
    div.className = "bubble" + (data.user === username ? " mine" : "");

    var text = document.createElement("div");
    text.textContent = data.user + ": " + data.msg;

    var meta = document.createElement("div");
    meta.className = "meta";
    meta.textContent = data.time;

    div.appendChild(text);
    div.appendChild(meta);

    messagesDiv.appendChild(div);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;

    // Browser notification if from someone else
    if(data.user !== username && Notification.permission === "granted"){
        new Notification(data.user, { body: data.msg });
        ding.play();
    }
}

// ---------- Typing ----------
var typingTimeout;
document.getElementById("msg").addEventListener("input", function(){
    socket.emit("typing", { user: username });
    clearTimeout(typingTimeout);
    typingTimeout = setTimeout(() => { socket.emit("stop_typing", { user: username }); }, 1000);
});

// ---------- Send ----------
function send(){
    var input = document.getElementById("msg");
    if(!input.value.trim()) return;

    socket.emit("chat_tx", {
        user: username,
        msg: input.value
    });
    input.value = "";
    socket.emit("stop_typing", { user: username });
}

document.getElementById("msg").addEventListener("keypress", function(e){
    if(e.key === "Enter") send();
});

// ---------- Receive ----------
socket.on("chat_rx", function(data){
    displayMessage(data);
    saveMessage(data);
});

// ---------- Typing Indicator ----------
socket.on("typing", function(data){
    typingDiv.textContent = data.user + " is typing...";
});
socket.on("stop_typing", function(data){
    typingDiv.textContent = "";
});

// ---------- Join/Leave ----------
socket.emit("join", { user: username });

socket.on("user_joined", function(data){
    displayMessage({ user: "System", msg: data.user + " joined the chat", time: data.time });
});

socket.on("user_left", function(data){
    displayMessage({ user: "System", msg: data.user + " left the chat", time: data.time });
});

// Load previous messages
loadMessages();

</script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML)

@socketio.on("chat_tx")
def chat(data):
    emit("chat_rx", {
        "user": data["user"],
        "msg": data["msg"],
        "time": datetime.now().strftime("%H:%M")
    }, broadcast=True)

@socketio.on("typing")
def typing(data):
    emit("typing", { "user": data["user"] }, broadcast=True, include_self=False)

@socketio.on("stop_typing")
def stop_typing(data):
    emit("stop_typing", { "user": data["user"] }, broadcast=True, include_self=False)

@socketio.on("join")
def join(data):
    username = data["user"]
    join_room("main")
    emit("user_joined", { "user": username, "time": datetime.now().strftime("%H:%M") }, broadcast=True)

@socketio.on("disconnect")
def handle_disconnect():
    # Since we can't get the username directly on disconnect, this could be improved with a session mapping
    pass  # Optionally track users in a dict to broadcast "user left"

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5001)
