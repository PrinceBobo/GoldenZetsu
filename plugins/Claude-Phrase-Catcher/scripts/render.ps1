
Add-Type -AssemblyName System.Windows.Forms;
Add-Type -AssemblyName System.Drawing;
Add-Type -AssemblyName System.Media;

$imagePath = "D:\Usman\Coding\Projects\MyPluginTestProject\Claude-Phrase-Catcher\hooks\Resources\ClearPicture\ClearPicture2.png";
$soundPath = "D:\Usman\Coding\Projects\MyPluginTestProject\Claude-Phrase-Catcher\hooks\Resources\ClearPicture\Now_I_have_a_clear_picture_clean.wav";

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
