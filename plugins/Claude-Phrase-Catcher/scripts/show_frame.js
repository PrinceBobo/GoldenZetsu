const fs = require("fs");
const path = require("path");
const { exec } = require("child_process");

const BASE_DIR = process.env.CLAUDE_PLUGIN_ROOT || path.resolve(__dirname, "..");
const LOGS_DIR = path.join(BASE_DIR, "scripts","Logs");
const STATE_FILE = path.join(BASE_DIR, "buffer.json");
const TRIGGER_FILE = path.join(BASE_DIR, "trigger.txt");



let buffer = {};

// load state
try {
    buffer = JSON.parse(fs.readFileSync(STATE_FILE, "utf8"));
} catch {
    buffer = {};
}

function normalize(text) {
    return (text || "").toLowerCase();
}

// Define all your phrase groups here
const PHRASE_GROUPS = [
    {
        name: "ClearPicture",
        phrases: ["clear picture", "full picture", "complete picture"]
    },
    {
        name: "SmokingGun",
        phrases: ["smoking gun"]
    },
    {
        name: "Caveat",
        phrases: ["caveat"]
    },
    {
        name: "Nuance",
        phrases: ["it's nuanced", "it's more nuanced", "nuance here"]
    }
    // add as many groups as you want
];

function checkMatch(text) {
    for (const group of PHRASE_GROUPS) {
        if (group.phrases.some(phrase => text.includes(phrase))) {
            return group.name; // returns the group name, or null if no match
        }
    }
    return null;
}


// stdin read
let input = "";

process.stdin.on("data", chunk => {
    input += chunk;
});

process.stdin.on("end", () => {
    try {
        const payload = input ? JSON.parse(input) : {};

        const msgId = payload.message_id;
        const delta = payload.delta || "";

        if (!msgId) return;

        if (!buffer[msgId]) {
            buffer[msgId] = {
                text: "",
                fired: false
            };
        }

        buffer[msgId].text += delta;

        const fullText = normalize(buffer[msgId].text);

        // -------------------------------
        // ONLY FIRE BLOCK (THIS IS WHERE AUDIO + IMAGE GO)
        // -------------------------------
        const matchedGroup = checkMatch(fullText);

        if (!buffer[msgId].fired && matchedGroup) {
            buffer[msgId].fired = true;

            // dynamically pick the media folder based on matched group
            const mediaDir = path.join(BASE_DIR, "hooks", "Resources", matchedGroup);
            
            // rest of your image/sound logic stays exactly the same
            // just replace imagesDir with mediaDir


            // 1. write trigger file (always first)
            fs.writeFileSync(
                TRIGGER_FILE,
                JSON.stringify({
                    trigger: matchedGroup,
                    message_id: msgId,
                    text: fullText,
                    time: new Date().toISOString()
                }, null, 2)
            );

            // -------------------------------
            // IMAGE + SOUND LOGIC (SAFE)
            // -------------------------------

            let imagePath = "";
            let soundPath = "";

            try {
                const images = fs.readdirSync(mediaDir)
                    .filter(f => /\.(png|jpg|jpeg|webp)$/i.test(f));

                if (images.length > 0) {
                    const img = images[Math.floor(Math.random() * images.length)];
                    imagePath = path.join(mediaDir, img).replace(/\\/g, '\\');
                }
            } catch (e) {
                fs.writeFileSync(path.join(LOGS_DIR, "image_error.txt"), String(e));
            }

            try {
                const sounds = fs.readdirSync(mediaDir)
                    .filter(f => /\.wav$/i.test(f));

                if (sounds.length > 0) {
                    const s = sounds[Math.floor(Math.random() * sounds.length)];
                    soundPath = path.join(mediaDir, s).replace(/\\/g, '\\');
                }
            } catch (e) {
                fs.writeFileSync(path.join(LOGS_DIR, "sound_error.txt"), String(e));
            }

            fs.writeFileSync(
                path.join(LOGS_DIR, "debug_render.json"),
                JSON.stringify({
                    mediaDir,
                    imagePath,
                    soundPath,
                    imagesExist: fs.existsSync(mediaDir)
                }, null, 2)
            );

            // -------------------------------
            // POWERSHELL VISUAL
            // -------------------------------
const psScript = `
Add-Type -AssemblyName System.Windows.Forms;
Add-Type -AssemblyName System.Drawing;
Add-Type -AssemblyName System.Media;

$imagePath = "${imagePath}";
$soundPath = "${soundPath}";

if (!(Test-Path $imagePath)) {
    [System.Windows.Forms.MessageBox]::Show("Image not found: $imagePath");
    exit
}

# --- load image ---
$img = [System.Drawing.Image]::FromFile($imagePath);

# --- play sound (non-blocking) ---
if ($soundPath -and (Test-Path $soundPath)) {
    try {
        $wmplayer = New-Object -ComObject WMPlayer.OCX
        $wmplayer.URL = $soundPath
        $wmplayer.controls.play()
    } catch {
        [System.Windows.Forms.MessageBox]::Show("Audio failed to play: " + $_.Exception.Message)
    }
}

# --- form ---
$form = New-Object System.Windows.Forms.Form;
$form.FormBorderStyle = 'None';
$form.StartPosition = 'CenterScreen';
$form.TopMost = $true;
$form.ShowInTaskbar = $false;

$form.BackColor = [System.Drawing.Color]::yellow;
$form.TransparencyKey = [System.Drawing.Color]::yellow;

$form.Width = $img.Width;
$form.Height = $img.Height;

$form.add_Paint({
    param($sender, $e)
    $e.Graphics.DrawImage($img, 0, 0, $sender.Width, $sender.Height);
});

$form.Add_Shown({ $form.Invalidate(); });

$timer = New-Object System.Windows.Forms.Timer;
$timer.Interval = 3000;
$timer.add_Tick({
    $img.Dispose();
    $form.Close();
});
$timer.Start();

[System.Windows.Forms.Application]::Run($form);
`;


            // const encoded = Buffer.from(psScript, 'utf16le').toString('base64');

            const psFile = path.join(BASE_DIR, "scripts","render.ps1");

            fs.writeFileSync(psFile, psScript);

            exec(
                `powershell.exe -NoProfile -ExecutionPolicy Bypass -File "${psFile}"`,
                (err) => {
                    if (err) {
                        fs.writeFileSync(
                            path.join(LOGS_DIR, "ps_error.txt"),
                            String(err)
                        );
                    }
                }
            );
        }

        // persist buffer ALWAYS
        fs.writeFileSync(STATE_FILE, JSON.stringify(buffer, null, 2));

    } catch (err) {
        fs.writeFileSync(
            path.join(LOGS_DIR, "error.txt"),
            String(err)
        );
    }
});