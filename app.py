import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template_string
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

<div id="input-area">
    <input id="msg" placeholder="Message..." autocomplete="off">
    <button onclick="send()">Send</button>
</div>

<script>
var socket = io();
var messagesDiv = document.getElementById("messages");
var username = localStorage.getItem("username");

if(!username){
    username = prompt("Enter your username:");
    if(!username) username = "Guest_" + Math.floor(Math.random()*1000);
    localStorage.setItem("username", username);
}

// Notification sound only
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
}

// ---------- Send ----------
function send(){
    var input = document.getElementById("msg");
    if(!input.value.trim()) return;

    socket.emit("chat_tx", {
        user: username,
        msg: input.value
    });

    input.value = "";
}

document.getElementById("msg")
.addEventListener("keypress", function(e){
    if(e.key === "Enter") send();
});

// ---------- Receive ----------
socket.on("chat_rx", function(data){

    displayMessage(data);
    saveMessage(data);

    if(data.user !== username){
        ding.play();
    }
});

// Load previous messages when page loads
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

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5001)
