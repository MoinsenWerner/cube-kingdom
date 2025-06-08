<?php
// chatbot.php
require_once 'config.php';

function sendMessageToChatbot($message) {
    // Vorbereitung der Anfrage an die DeepSeek API
    $data = [
        'model' => MODEL,
        'messages' => [
            ['role' => 'system', 'content' => 'You are a helpful assistant.'],
            ['role' => 'user', 'content' => $message]
        ],
        'stream' => true
    ];

    // cURL-Anfrage an die DeepSeek API
    $ch = curl_init(DEEPSEEK_API_URL);
    curl_setopt($ch, CURLOPT_HTTPHEADER, [
        'Content-Type: application/json',
        'Authorization: Bearer ' . DEEPSEEK_API_KEY
    ]);
    curl_setopt($ch, CURLOPT_POST, true);
    curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($data));
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);

    $response = curl_exec($ch);
    curl_close($ch);

    // Verarbeitung der API-Antwort
    if ($response === false) {
        return 'Fehler bei der Kommunikation mit der API.';
    }

    $responseData = json_decode($response, true);
    if (isset($responseData['choices'][0]['message']['content'])) {
        return $responseData['choices'][0]['message']['content'];
    } else {
        return 'Fehler: Keine Antwort vom Chatbot erhalten.';
    }
}

// Beispiel: Verarbeitung einer Benutzereingabe
if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['message'])) {
    $userMessage = htmlspecialchars($_POST['message']);
    $botResponse = sendMessageToChatbot($userMessage);
    echo $botResponse;
}
?>