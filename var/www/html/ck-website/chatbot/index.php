<?php
// index.php
?>
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cube Kingdom Chatbot</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #f4f4f4;
            margin: 0;
            padding: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
        }
        .chat-container {
            width: 400px;
            background-color: #fff;
            border-radius: 10px;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
            overflow: hidden;
        }
        .chat-header {
            background-color: #007bff;
            color: #fff;
            padding: 15px;
            text-align: center;
            font-size: 18px;
        }
        .chat-body {
            padding: 15px;
            height: 300px;
            overflow-y: auto;
            border-bottom: 1px solid #ddd;
        }
        .chat-footer {
            display: flex;
            padding: 10px;
        }
        .chat-footer input {
            flex: 1;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 5px;
            outline: none;
        }
        .chat-footer button {
            padding: 10px 15px;
            background-color: #007bff;
            color: #fff;
            border: none;
            border-radius: 5px;
            margin-left: 10px;
            cursor: pointer;
        }
        .chat-footer button:hover {
            background-color: #0056b3;
        }
        .message {
            margin-bottom: 10px;
        }
        .user-message {
            text-align: right;
            color: #007bff;
        }
        .bot-message {
            text-align: left;
            color: #333;
        }
    </style>
</head>
<body>
    <div class="chat-container">
        <div class="chat-header">
            Cube Kingdom Chatbot
        </div>
        <div class="chat-body" id="chat-body">
            <!-- Hier werden die Nachrichten angezeigt -->
        </div>
        <div class="chat-footer">
            <input type="text" id="user-input" placeholder="Schreibe eine Nachricht...">
            <button onclick="sendMessage()">Senden</button>
        </div>
    </div>

    <script>
        // Funktion zum Senden einer Nachricht an den Chatbot
        function sendMessage() {
            const userInput = document.getElementById('user-input');
            const chatBody = document.getElementById('chat-body');

            if (userInput.value.trim() === '') return;

            // Benutzernachricht anzeigen
            chatBody.innerHTML += `<div class="message user-message">${userInput.value}</div>`;

            // Nachricht an den Server senden
            fetch('chatbot.php', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: `message=${encodeURIComponent(userInput.value)}`
            })
            .then(response => response.text())
            .then(data => {
                // Bot-Antwort anzeigen
                chatBody.innerHTML += `<div class="message bot-message">${data}</div>`;
                chatBody.scrollTop = chatBody.scrollHeight; // Automatisch nach unten scrollen
            })
            .catch(error => {
                console.error('Fehler:', error);
            });

            // Eingabefeld leeren
            userInput.value = '';
        }
    </script>
</body>
</html>