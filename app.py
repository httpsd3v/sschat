# app.py
import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template_string, request
from flask_socketio import SocketIO, emit
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret'
socketio = SocketIO(app, cors_allowed_origins="*")

HTML = """
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ssChat Live</title>
<script src="https://cdn.socket.io/4.7.2/socket.io.min.js"></script>
<style>
body {
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
    background: #121212;
}
#messages{
    flex:1;
    overflow-y:auto;
    padding:15px;
    display:flex;
    flex-direction:column;
    gap:8px;
}
.bubble {
    padding:10px 16px;
    border-radius:25px;
    max-width:75%;
    word-wrap: break-word;
    line-height:1.4;
    font-size:14px;
    position: relative;
    animation: bubble-pop 0.2s ease-out;
}
.bubble .username {
    font-weight:bold;
    font-size:12px;
    margin-bottom:4px;
}
@keyframes bubble-pop {
    0% { transform: scale(0.9); opacity:0.7; }
    50% { transform: scale(1.05); opacity:1; }
    100% { transform: scale(1); opacity:1; }
}
.mine {
    align-self:flex-end;
    background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
    color:white;
    border-bottom-right-radius:4px;
    box-shadow:0 1px 4px rgba(0,0,0,0.3);
}
.mine::after {
    content:"";
    position:absolute;
    bottom:0;
    right:-8px;
    width:0;
    height:0;
    border-top:10px solid #4facfe;
    border-left:8px solid transparent;
    transform-origin: bottom right;
    animation: tail-pop 0.2s ease-out;
}
.other {
    align-self:flex-start;
    background: #262626;
    color:white;
    border-bottom-left-radius:4px;
    box-shadow:0 1px 4px rgba(0,0,0,0.3);
}
.other::after {
    content:"";
    position:absolute;
    bottom:0;
    left:-8px;
    width:0;
    height:0;
    border-top:10px solid #262626;
    border-right:8px solid transparent;
    transform-origin: bottom left;
    animation: tail-pop 0.2s ease-out;
}
@keyframes tail-pop {
    0% { transform: scale(0.5); opacity:0; }
    50% { transform: scale(1.2); opacity:1; }
    100% { transform: scale(1); opacity:1; }
}
.meta{
    font-size:10px;
    opacity:0.6;
    margin-top:4px;
    text-align:right;
}
#typing{
    padding:0 15px;
    height:24px;
    display:flex;
    align-items:center;
    font-size:12px;
    color:#ccc;
}
#input-area{
    display:flex;
    padding:10px;
    border-top:1px solid #222;
    background:#121212;
}
input{
    flex:1;
    background:#262626;
    border:none;
    color:white;
    padding:10px 16px;
    border-radius:25px;
    outline:none;
    font-size:14px;
}
button{
    margin-left:10px;
    background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
    border:none;
    color:white;
    font-weight:bold;
    padding:10px 16px;
    border-radius:25px;
    cursor:pointer;
    transition:0.2s;
}
button:hover{ opacity:0.85; }
</style>
</head>
<body>
<div id="header">🌍 Teens Hangout </div>
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

// Enforce username
while(!username){
    username = prompt("Enter your username:");
    if(username) localStorage.setItem("username", username);
}

// Notification permission
if(Notification.permission !== "granted") Notification.requestPermission();
var ding = new Audio("https://www.soundjay.com/buttons/sounds/button-3.mp3");

// Load stored messages
function loadMessages(){
    var saved = localStorage.getItem("chat_history");
    if(saved) JSON.parse(saved).forEach(displayMessage);
}

// Save messages
function saveMessage(data){
    var msgs = localStorage.getItem("chat_history");
    msgs = msgs ? JSON.parse(msgs) : [];
    msgs.push(data);
    localStorage.setItem("chat_history", JSON.stringify(msgs));
}

// Display messages
function displayMessage(data){
    var div = document.createElement("div");
    div.className = data.user === username ? "bubble mine" : "bubble other";

    var nameDiv = document.createElement("div");
    nameDiv.className = "username";
    nameDiv.textContent = data.user;

    var text = document.createElement("div");
    text.textContent = data.msg;

    var meta = document.createElement("div");
    meta.className = "meta";
    meta.textContent = data.time;

    div.appendChild(nameDiv);
    div.appendChild(text);
    div.appendChild(meta);
    messagesDiv.appendChild(div);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;

    if(data.user !== username && Notification.permission === "granted"){
        new Notification(data.user, { body:data.msg });
        ding.play();
    }
}

// Typing indicator with username
var typingTimeout;
document.getElementById("msg").addEventListener("input", function(){
    socket.emit("typing", { user: username });
    clearTimeout(typingTimeout);
    typingTimeout = setTimeout(()=>{ socket.emit("stop_typing", { user: username }); }, 1000);
});

// Send message
function send(){
    var input = document.getElementById("msg");
    if(!input.value.trim()) return;
    socket.emit("chat_tx", { user: username, msg: input.value });
    input.value = "";
    socket.emit("stop_typing", { user: username });
}
document.getElementById("msg").addEventListener("keypress", e=>{ if(e.key==="Enter") send(); });

// Receive messages
socket.on("chat_rx", function(data){ displayMessage(data); saveMessage(data); });

// Typing indicator
var typingUsers = new Set();
socket.on("typing", function(data){
    typingUsers.add(data.user);
    typingDiv.textContent = Array.from(typingUsers).join(", ") + " is typing...";
});
socket.on("stop_typing", function(data){
    typingUsers.delete(data.user);
    if(typingUsers.size) typingDiv.textContent = Array.from(typingUsers).join(", ") + " is typing...";
    else typingDiv.textContent = "";
});

// Join/leave notifications
socket.emit("join", { user: username });
socket.on("user_joined", function(data){ displayMessage({ user:"System", msg:data.user+" joined the chat", time:data.time }); });
socket.on("user_left", function(data){ displayMessage({ user:"System", msg:data.user+" left the chat", time:data.time }); });

// Load previous messages
loadMessages();
</script>
</body>
</html>
"""

connected_users = {}

@app.route("/")
def index():
    return render_template_string(HTML)

@socketio.on("chat_tx")
def chat_tx(data):
    emit("chat_rx", {
        "user": data["user"],
        "msg": data["msg"],
        "time": datetime.now().strftime("%H:%M")
    }, broadcast=True)

@socketio.on("typing")
def typing(data):
    emit("typing", data, broadcast=True, include_self=False)

@socketio.on("stop_typing")
def stop_typing(data):
    emit("stop_typing", data, broadcast=True, include_self=False)

@socketio.on("join")
def join(data):
    username = data["user"]
    connected_users[request.sid] = username
    emit("user_joined", {
        "user": username,
        "time": datetime.now().strftime("%H:%M")
    }, broadcast=True)

@socketio.on("disconnect")
def disconnect():
    username = connected_users.get(request.sid)
    if username:
        emit("user_left", {
            "user": username,
            "time": datetime.now().strftime("%H:%M")
        }, broadcast=True)
        del connected_users[request.sid]

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5001)
