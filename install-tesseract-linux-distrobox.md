# Install Tesseract with Distrobox

Use this when the host should not (or cannot) install Tesseract with its own package manager — for example an immutable OS — but Distrobox is available. The result is a `tesseract` command on the host `PATH` that your desktop app can call with subprocess.

You need Distrobox and a container engine (`podman` or `docker`). Create a dedicated container named `tesseract` so it does not mix with other boxes.

Use `sudo` inside the container, not `run0`. Distrobox containers normally do not run systemd as PID 1, so `run0` fails with “System has not been booted with systemd as init system”.

Tesseract needs the engine plus language packs. The examples include English, German, and OSD (orientation / script detection).

---

## 1. Create the container

Pick **one** image. The same Distrobox commands work on any host; only the *guest* package manager changes.

**Ubuntu (same commands on every host):**

```bash
distrobox create --name tesseract --image docker.io/library/ubuntu:24.04
distrobox enter tesseract
```

**Arch:**

```bash
distrobox create --name tesseract --image quay.io/toolbx/arch-toolbox:latest
distrobox enter tesseract
```

**Fedora:**

```bash
distrobox create --name tesseract --image registry.fedoraproject.org/fedora-toolbox:40
distrobox enter tesseract
```

If a box named `tesseract` already exists, skip `create` and run `distrobox enter tesseract`.

---

## 2. Install Tesseract (inside the container)

**Ubuntu / Debian guest:**

```bash
sudo apt update
sudo apt install -y tesseract-ocr tesseract-ocr-eng tesseract-ocr-deu tesseract-ocr-osd
```

Other languages: `tesseract-ocr-fra`, `tesseract-ocr-spa`, …

**Arch guest:**

```bash
sudo pacman -Syu --needed tesseract tesseract-data-eng tesseract-data-deu tesseract-data-osd
```

Other languages: `tesseract-data-fra`, `tesseract-data-spa`, …  
List packs: `pacman -Ss tesseract-data`

**Fedora guest:**

```bash
sudo dnf install -y tesseract tesseract-langpack-eng tesseract-langpack-deu tesseract-langpack-osd
```

Other languages: `tesseract-langpack-fra`, `tesseract-langpack-spa`, …

Check:

```bash
tesseract --version
tesseract --list-langs
```

You should see `eng` and `deu` (needed for `-l deu+eng`).

---

## 3. Export `tesseract` to the host

Still inside the container:

```bash
mkdir -p ~/.local/bin
distrobox-export --bin /usr/bin/tesseract --export-path ~/.local/bin
```

That writes a wrapper at `~/.local/bin/tesseract`. Host programs (including this app) can then run `tesseract` as if it were installed locally. The home directory is shared, so receipt files under `$HOME` work.

Leave the container:

```bash
exit
```

On the host, `~/.local/bin` must be on `PATH`:

```bash
export PATH="$HOME/.local/bin:$PATH"
which tesseract
tesseract --list-langs
```

To make that permanent, add the `export PATH=…` line to your shell rc (`~/.bashrc`, `~/.zshrc`, …). GUI apps started from the application menu only see that PATH if the desktop session includes `~/.local/bin` (KDE/GNOME usually do; if `which tesseract` works in a terminal but the app still reports Tesseract missing, log out and back in, or start the app from that same terminal).

---

## 4. Use it

From the host, after export:

```bash
tesseract receipt.png stdout
tesseract receipt.png stdout -l deu+eng
tesseract receipt.png stdout -l eng
tesseract receipt.png output          # writes output.txt
tesseract receipt.png output pdf      # writes output.pdf
```

Without export, from the host:

```bash
distrobox enter tesseract -- tesseract receipt.png stdout -l deu+eng
```

Inside the container the `tesseract` binary works directly.

Page-segmentation modes:

```bash
tesseract --help-psm
```

---

## 5. Cleanup

```bash
distrobox stop tesseract
distrobox rm tesseract
rm -f ~/.local/bin/tesseract
```

---

## Notes

- First call after a reboot can be slow while Distrobox starts the container.
- Files outside `$HOME` may not be visible inside the box; copy receipts into your home directory if OCR cannot open them.
- Do not use `run0` in Distrobox. Use `sudo`.
