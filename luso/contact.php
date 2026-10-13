<?php
/*
 * Réception du formulaire de devis de Luso.
 *
 * Envoie chaque demande par email à RECIPIENT. Rien n'est enregistré sur le serveur :
 * ni base de données, ni fichier, ni cookie.
 *
 * Prérequis : un hébergement avec PHP 7.4+ et la fonction mail() activée
 * (o2switch, OVHcloud, Hostinger, Infomaniak… l'activent par défaut).
 */

// ---- Configuration ---------------------------------------------------------

// Adresse qui reçoit les demandes.
const RECIPIENT = 'youcefmlpro@gmail.com';

// Expéditeur technique : utilisez une adresse de votre nom de domaine (ex. no-reply@luso.fr),
// sinon les emails risquent d'arriver dans les spams. La réponse partira vers le visiteur
// grâce à l'en-tête Reply-To.
const FROM_EMAIL = 'no-reply@luso.fr';
const FROM_NAME = 'Site Luso';

// Valeurs autorisées (identiques à celles du formulaire).
const PROJECTS = ['Site vitrine', 'Boutique en ligne', 'Application mobile', 'Application web', 'Design UI/UX', 'Maintenance'];
const BUDGETS = ['Moins de 2 000 €', '2 000 € à 5 000 €', '5 000 € à 15 000 €', 'Plus de 15 000 €', 'Je ne sais pas encore'];

// ---- Traitement ------------------------------------------------------------

header('X-Content-Type-Options: nosniff');
header('Referrer-Policy: strict-origin-when-cross-origin');

$wantsJson = stripos($_SERVER['HTTP_ACCEPT'] ?? '', 'application/json') !== false;

function respond(bool $ok, string $message, int $status, bool $json): void
{
    if ($json) {
        http_response_code($status);
        header('Content-Type: application/json; charset=utf-8');
        header('Cache-Control: no-store');
        echo json_encode(['ok' => $ok, 'message' => $message], JSON_UNESCAPED_UNICODE);
    } else {
        // Navigateur sans JavaScript : retour sur la page avec le résultat.
        header('Location: index.html#' . ($ok ? 'demande-envoyee' : 'demande-erreur'), true, 303);
    }
    exit;
}

function field(string $name, int $max): string
{
    $value = trim((string) ($_POST[$name] ?? ''));
    $value = str_replace("\0", '', $value);
    return mb_substr($value, 0, $max, 'UTF-8');
}

// Retire les retours à la ligne des valeurs placées dans les en-têtes de l'email.
function oneLine(string $value): string
{
    return trim(preg_replace('/[\r\n\t]+/', ' ', $value));
}

// Nom affiché dans un en-tête : sans caractères spéciaux qui pourraient être interprétés comme une adresse.
function displayName(string $value): string
{
    $clean = trim(preg_replace('/["\\\\<>()\[\]:;,@]+/', ' ', $value));
    return mb_encode_mimeheader($clean !== '' ? $clean : 'Visiteur', 'UTF-8');
}

if (($_SERVER['REQUEST_METHOD'] ?? '') !== 'POST') {
    header('Allow: POST');
    if (!$wantsJson) {
        header('Location: index.html#contact', true, 303);
        exit;
    }
    respond(false, 'Méthode non autorisée.', 405, true);
}

// Anti-spam : champ piège invisible pour les humains, et délai minimal de saisie.
$elapsed = (int) ($_POST['elapsed'] ?? 0);
if (field('website', 200) !== '' || ($elapsed > 0 && $elapsed < 2500)) {
    respond(true, 'Merci, votre demande a bien été envoyée.', 200, $wantsJson);
}

$name = oneLine(field('name', 120));
$company = oneLine(field('company', 120));
$email = oneLine(field('email', 254));
$phone = oneLine(field('phone', 40));
$project = field('project', 60);
$budget = field('budget', 60);
$message = field('message', 5000);

if ($name === '' || $message === '' || !filter_var($email, FILTER_VALIDATE_EMAIL)) {
    respond(false, 'Merci de renseigner votre nom, une adresse email valide et votre message.', 422, $wantsJson);
}
if (!in_array($project, PROJECTS, true)) {
    $project = 'Non précisé';
}
if (!in_array($budget, BUDGETS, true)) {
    $budget = 'Non précisé';
}

$subject = 'Demande de devis : ' . $project . ' (' . $name . ')';
$lines = [
    'Nouvelle demande reçue depuis le site Luso.',
    '',
    'Nom : ' . $name,
    'Entreprise : ' . ($company !== '' ? $company : '-'),
    'Email : ' . $email,
    'Téléphone : ' . ($phone !== '' ? $phone : '-'),
    'Projet : ' . $project,
    'Budget : ' . $budget,
    '',
    'Message :',
    $message,
    '',
    '--',
    'Répondez directement à cet email pour écrire à ' . $name . '.',
    'Rappel RGPD : supprimez cette demande 3 ans après votre dernier échange si elle reste sans suite.',
];
$body = str_replace(["\r\n", "\r"], "\n", implode("\n", $lines));

$headers = [
    'From' => mb_encode_mimeheader(FROM_NAME, 'UTF-8') . ' <' . FROM_EMAIL . '>',
    'Reply-To' => displayName($name) . ' <' . $email . '>',
    'MIME-Version' => '1.0',
    'Content-Type' => 'text/plain; charset=UTF-8',
    'Content-Transfer-Encoding' => '8bit',
    'X-Mailer' => 'Luso',
];

$sent = mail(
    RECIPIENT,
    mb_encode_mimeheader($subject, 'UTF-8'),
    $body,
    $headers,
    '-f' . FROM_EMAIL
);

if (!$sent) {
    respond(false, "L'envoi a échoué côté serveur.", 500, $wantsJson);
}

respond(true, 'Merci, votre demande a bien été envoyée.', 200, $wantsJson);
