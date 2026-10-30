# Windows version of theme.sh: push a theme folder (config.json, and optionally a wallpaper.jpg or a
# wallpapers/ collection) to the launcher on the TV and restart Home. See themes/README.md for the keys.
#
# Usage: tools\theme.ps1 -TvHost 192.168.1.50 themes\aurora
#        tools\theme.ps1 -TvHost 192.168.1.50 -As japan themes\japan    # store a bundle, not active
#        tools\theme.ps1 -TvHost 192.168.1.50 -List                     # the bundles on the TV
#        tools\theme.ps1 -TvHost 192.168.1.50 -Remove japan             # drop one bundle
#        tools\theme.ps1 -TvHost 192.168.1.50 -Reset                    # remove the root overlay
#
# A folder replaces the theme Home shows. -As stores the same files one folder deeper, under files/themes/<name>/,
# where Home's long-press Settings menu lists it (Themes) beside the root theme, called Default. A bundle stays
# until -Remove, and -Reset leaves the bundles alone. Exit status as in theme.sh: 0 the theme is on the TV, the
# bundle was stored or removed, or the list/reset ran; 1 the theme could not be pushed; 2 the command line is not
# one of the shapes above, so nothing was sent.
param(
    [Parameter(Position = 0)][string]$Theme,
    [string]$As,
    [switch]$List,
    [string]$Remove,
    [switch]$Reset,
    [string]$TvHost = $env:TV_HOST
)
$usage = 'usage: theme.ps1 <theme folder> | -As <name> <theme folder> | -List | -Remove <name> | -Reset'
# theme.sh judges its own command line here, and this is the same judgement: one shape per run, and -Reset,
# -List and -Remove never share a line with a folder. `-Reset themes\aurora` used to take the reset branch and
# throw the folder away, so nothing is sent for a line this script cannot read.
if ($Reset) {
    if ($List -or $Remove -or $As -or $Theme) { [Console]::Error.WriteLine("theme.ps1 -Reset takes no other argument. Nothing was sent to the TV."); exit 2 }
} elseif ($List) {
    if ($Remove -or $As -or $Theme) { [Console]::Error.WriteLine("theme.ps1 -List takes no other argument. Nothing was sent to the TV."); exit 2 }
} elseif ($Remove) {
    if ($As -or $Theme) { [Console]::Error.WriteLine("theme.ps1 -Remove takes one bundle name. Nothing was sent to the TV."); exit 2 }
} elseif ($As) {
    if (-not $Theme) { [Console]::Error.WriteLine($usage); exit 2 }
} elseif (-not $Theme) {
    [Console]::Error.WriteLine($usage)
    exit 2
}
# A bundle name becomes a folder under files/themes/ and a path inside the provider's URI, so it keeps to the
# characters a theme folder can use here: no dots (no "..", no hidden names) and no spaces.
$bundle = if ($As) { $As } else { $Remove }
if ($bundle -and $bundle -notmatch '^[A-Za-z0-9_-]{1,40}$') {
    [Console]::Error.WriteLine("unsupported bundle name: $bundle (letters, digits, _ and -, up to 40). Nothing was sent to the TV.")
    exit 2
}
$ErrorActionPreference = 'Stop'
$OutputEncoding = New-Object System.Text.UTF8Encoding $false
if (-not $TvHost) { throw 'pass -TvHost <tv ip> or set $env:TV_HOST' }
$env:TV_HOST = $TvHost
# Resolve the theme folder against the caller's directory before moving into tools\.
if ($Theme) { $Theme = (Resolve-Path $Theme).Path }
Set-Location $PSScriptRoot
$py = 'venv\Scripts\python.exe'
if (-not (Test-Path $py)) { throw 'run: python -m venv tools\venv; tools\venv\Scripts\python.exe -m pip install -r tools\requirements.txt' }
$pkg = 'com.gathin.tvhome'
# Runs tools\tv.py or b64push.py and stops on a non-zero exit: 'Stop' only covers cmdlets, so a failed
# native call would otherwise fall through to "Theme ... is on the TV".
function Invoke-Tv {
    $out = & $py -I @args
    if ($LASTEXITCODE -ne 0) { throw "$($args[0]) $($args[1]) failed (exit code $LASTEXITCODE); the theme was not fully applied" }
    $out
}
$dir = "/sdcard/Android/data/$pkg/files"
$revision = [guid]::NewGuid().ToString('N')
# One shared recovery path verifies the helpers after Home restarts.

# Some firmware (TCL G07, Android 11) locks the shell out of Android/data. Files are staged in
# /data/local/tmp and copied in, or written through the launcher's ThemeProvider when that is refused.
# The provider has to be tried first: on Android 14 the shell can write into Android/data, so cp "succeeds",
# but the file it creates belongs to the shell (uid 2000) and the launcher then gets EACCES opening it, which
# silently ignores the theme whenever the file did not exist yet - a fresh install, or after a reinstall.
# A provider write creates the file as the launcher, and it cannot truncate a file the shell owns either, so
# remove our copy first. cp stays as the fallback for firmware without the provider.
$uri = "content://$pkg.theme"
$tmp = '/data/local/tmp/cyt-theme'
# A file's staging path; wallpapers/a.jpg is staged as $tmp-wallpapers-a.jpg.
function Stage($name) { "$tmp-$($name -replace '/', '-')" }
# Android 8 and 9 have no `content write`: they print "[ERROR] Unsupported operation: write" but exit 0, so
# that message counts as a failure and cp runs.
function Put($name) { $t = Stage $name; "rm -f $dir/$name 2>/dev/null; { o=`$(content write --uri $uri/$name < $t 2>&1) && case `"`$o`" in *'Unsupported operation'*) false ;; esac; } || cp $t $dir/$name 2>/dev/null; rm -f $t" }
function Drop($name) { "rm -f $dir/$name 2>/dev/null; content delete --uri $uri/$name 2>/dev/null" }

# The collection a theme can push. A push empties it before writing the theme's own pictures, and -Reset has to
# empty it too: the launcher's wallpaper picker lists that folder itself, and an on-TV pick of one of its
# pictures is read back from it, so a reset that left the pictures behind still shows the theme it just removed.
# $prefix is "" for the root theme and "themes/<name>/" for a bundle (the same string theme.sh builds).
function Clear-Wallpapers($prefix) { "mkdir -p $dir/${prefix}wallpapers 2>/dev/null; rm -f $dir/${prefix}wallpapers/*.[jJ][pP][gG] $dir/${prefix}wallpapers/*.[jJ][pP][eE][gG] $dir/${prefix}wallpapers/*.[pP][nN][gG] $dir/${prefix}wallpapers/*.[wW][eE][bB][pP] 2>/dev/null; content delete --uri $uri/${prefix}wallpapers 2>/dev/null" }

if ($List) {
    # Only a folder with a config.json is a bundle the picker can show, which is also what ThemeDir.bundles reads.
    $out = Invoke-Tv tv.py "for d in $dir/themes/*/; do [ -f `"`$d/config.json`" ] && basename `"`$d`"; done 2>/dev/null"
    $names = @($out | Where-Object { $_ -and $_.Trim() })
    if ($names.Count -eq 0) {
        Write-Host 'no theme bundles on the TV (store one with: theme.ps1 -As <name> <theme folder>)'
    } else {
        Write-Host 'theme bundles on the TV:'
        $names | ForEach-Object { Write-Host "  $_" }
    }
    exit 0
}
if ($Remove) {
    Invoke-Tv tv.py "rm -rf $dir/themes/$Remove 2>/dev/null; content delete --uri $uri/themes/$Remove 2>/dev/null" | Out-Null
    & $py -I theme_restart.py
    if ($LASTEXITCODE) { throw 'Home restart recovery failed' }
    Write-Host 'removed'
    Write-Host "Bundle $Remove is off the TV. If it was the theme Home showed, Home falls back to the root theme (Default)."
    exit 0
}
if ($Reset) {
    Invoke-Tv tv.py "mkdir -p $dir 2>/dev/null; $(Drop 'config.json'); $(Drop 'wallpaper.jpg'); $(Drop 'wallpapers/captions.txt'); $(Clear-Wallpapers ''); printf '%s' '$revision' > $tmp-theme_revision; $(Put 'theme_revision')" | Out-Null
    & $py -I theme_restart.py
    if ($LASTEXITCODE) { throw 'Home restart recovery failed' }
    Write-Host 'reset'
    Write-Host 'The root theme is off the TV. Bundles stored with -As are still there, and a bundle Home is showing'
    Write-Host 'stays until you pick Default in the Themes menu.'
    exit 0
}
$config = Join-Path $Theme 'config.json'
if (-not (Test-Path $config)) { throw "no config.json in $Theme" }
try { $themeJson = Get-Content $config -Raw | ConvertFrom-Json } catch { throw "$config is not valid JSON" }
# Config.read() answers "no overlay" for anything that is not a JSON object, so an array, a number or a
# string is a theme the launcher drops - and it replaces the theme the set had with the built-in config.
# Judged here, before anything is pushed, so "is on the TV" cannot mean the opposite.
if ($themeJson -isnot [System.Management.Automation.PSCustomObject]) {
    throw "$config is not a JSON object of theme keys, so the launcher would ignore it and the TV would go back to its built-in config (themes/README.md). Nothing was sent to the TV."
}
# Every collection name is checked before anything changes on the TV, as in theme.sh: a name refused halfway
# through the push left the new config.json and part of the collection behind. b64push.py refuses '..' in a path.
$wallpapers = Join-Path $Theme 'wallpapers'
$images = @()
if (Test-Path $wallpapers -PathType Container) {
    $images = @(Get-ChildItem $wallpapers -File | Where-Object { $_.Extension -match '^\.(jpg|jpeg|png|webp)$' })
    foreach ($image in $images) {
        if ($image.Name -notmatch '^[A-Za-z0-9_.-]+$' -or $image.Name.Contains('..')) { throw "unsupported wallpaper filename: $($image.Name)" }
    }
}
# A bundle is the same files one folder deeper. A store writes the pictures first and config.json last, so a
# half-finished -As leaves a folder ThemeDir.bundles does not list.
$prefix = if ($As) { "themes/$As/" } else { '' }
function Push-Config {
    Invoke-Tv tv.py --push $config (Stage "${prefix}config.json") | Out-Null
    Invoke-Tv tv.py (Put "${prefix}config.json") | Out-Null
}
function Push-Pictures {
    $wall = Join-Path $Theme 'wallpaper.jpg'
    if (Test-Path $wall) { Invoke-Tv b64push.py $wall (Stage "${prefix}wallpaper.jpg"); Invoke-Tv tv.py (Put "${prefix}wallpaper.jpg") | Out-Null } else { Invoke-Tv tv.py (Drop "${prefix}wallpaper.jpg") | Out-Null }
    Invoke-Tv tv.py (Clear-Wallpapers $prefix) | Out-Null
    foreach ($image in $images) {
        Invoke-Tv b64push.py $image.FullName (Stage "${prefix}wallpapers/$($image.Name)")
        Invoke-Tv tv.py (Put "${prefix}wallpapers/$($image.Name)") | Out-Null
    }
    # The collection's names (wallpaper_captions); a theme without them leaves no stale names behind.
    $captions = Join-Path $Theme 'wallpapers/captions.txt'
    if (Test-Path $captions -PathType Leaf) {
        Invoke-Tv b64push.py $captions (Stage "${prefix}wallpapers/captions.txt")
        Invoke-Tv tv.py (Put "${prefix}wallpapers/captions.txt") | Out-Null
    } else {
        Invoke-Tv tv.py (Drop "${prefix}wallpapers/captions.txt") | Out-Null
    }
}
function Push-Revision {
    Invoke-Tv tv.py "printf '%s' '$revision' > $(Stage "${prefix}theme_revision"); $(Put "${prefix}theme_revision")" | Out-Null
}

# Tolerated, as in theme.sh: a TV that locks Android/data still takes the files through ThemeProvider.
Invoke-Tv tv.py "mkdir -p $dir/$prefix 2>/dev/null; true" | Out-Null
if ($As) {
    Push-Pictures
    Push-Config
    Push-Revision
    Write-Host 'stored'
    Write-Host "Theme $(Split-Path $Theme -Leaf) is on the TV as bundle $As. Pick it on Home: hold Settings, then Themes."
    exit 0
}
Push-Config
Push-Pictures
Push-Revision
& $py -I theme_restart.py
if ($LASTEXITCODE) { throw 'Home restart recovery failed' }
Write-Host 'applied'
Write-Host "Theme $(Split-Path $Theme -Leaf) is on the TV. Undo with: tools\theme.ps1 -TvHost $TvHost -Reset"
