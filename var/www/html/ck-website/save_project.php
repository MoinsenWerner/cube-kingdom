<?php
session_start();
if (!isset($_SESSION['user_id'])) {
    header('Location: login.php');
    exit;
}

$user_id = $_SESSION['user_id'];
$project_name = $_POST['projectName'] ?? '';
$server_type = $_POST['serverType'] ?? '';
$ram = intval($_POST['ram'] ?? 1);
$price = floatval($_POST['price'] ?? 0.00);

// API Call vorbereiten
$api_url = "https://www.cube-kingdom.de/api/projects";  // FastAPI läuft meist auf :8000
$data = [
    "user_id" => $user_id,
    "project_name" => $project_name,
    "server_type" => $server_type,
    "ram" => $ram,
    "price" => $price
];

$options = [
    'http' => [
        'header'  => "Content-Type: application/json\r\n",
        'method'  => 'POST',
        'content' => json_encode($data),
    ],
];

$context  = stream_context_create($options);
$result = file_get_contents($api_url, false, $context);

if ($result === FALSE) {
    die('API Fehler beim Anlegen des Projekts!');
}

$response = json_decode($result, true);

// Nach erfolgreichem Speichern den Server automatisch erstellen
$serverpanel_url = "http://localhost:8001/create";
$server_data = [
    "name" => $project_name,
    "ram_mb" => $ram * 1024,
    "jar_path" => "/var/www/html/ck-website/server.jar"
];
$sp_options = [
    'http' => [
        'header'  => "Content-Type: application/json\r\nx-api-key: h2r-admin0709-reload9383\r\n",
        'method'  => 'POST',
        'content' => json_encode($server_data),
    ],
];
$sp_context = stream_context_create($sp_options);
@file_get_contents($serverpanel_url, false, $sp_context);
?>

<h1>Projekt gespeichert!</h1>
<p><?php echo htmlspecialchars($response['message'] ?? ''); ?></p>
<p><a href="my_projects.php">Meine Projekte ansehen</a></p>
<p><a href="project_configurator.php">Weiteres Projekt anlegen</a></p>
