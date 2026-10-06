OS = {
"windows": dict(
  NAME="Windows", FILE="windows", SHORT="Windows",
  TERMINAL="Click the **Start** button, type `Command Prompt`, and press **Enter**. A black window with white text opens. This is the terminal you will use for Steps 1 to 3. Miniforge (Step 3) adds a second terminal, the **Miniforge Prompt**, and from Step 4 on you must use that one instead: only it knows the `conda` command.",
  PASTE="In both windows, **right-click** the window to paste. `Ctrl+V` often does not work there.",
  GIT="Go to **git-scm.com**, choose the **Windows** download, and run the installer. Keep every default setting: click **Next** until you reach **Install**, then click **Install**.\n\nWhen it finishes, **close the Command Prompt and open a new one** (the old window does not know about Git yet).",
  MINIFORGE_FILE="Miniforge3-Windows-x86_64.exe",
  MINIFORGE="Go to **github.com/conda-forge/miniforge**, find the file **Miniforge3-Windows-x86_64.exe**, and download it. Double-click it and follow the installer:\n\n- choose **Just Me**;\n- keep the default install folder;\n- **leave the box \"Add Miniforge to my PATH\" unticked.** The Miniforge Prompt works without it.\n\nWhen it finishes, close the Command Prompt. Click **Start**, type `Miniforge Prompt`, and press **Enter**. Use this window for the rest of the guide.",
  FOLDER="%USERPROFILE%\\Research",
  CD_REPO="cd %USERPROFILE%\\Research\\NSDF-Data",
  CD_PYTHON="cd %USERPROFILE%\\Research\\NSDF-Data\\python",
  CD_NOTES="cd %USERPROFILE%\\Research\\NSDF-Data\\R76\\analysis_notes",
  MKDIR="mkdir %USERPROFILE%\\Research",
  LISTCMD="dir",
  NEW_TERM="a **Miniforge Prompt** (click **Start**, type `Miniforge Prompt`, press **Enter**)",
  OPEN_TERM="a **Miniforge Prompt** (click **Start**, type `Miniforge Prompt`, press **Enter**)",
  HOME_NOTE="`%USERPROFILE%` stands for your own user folder (for example `C:\\Users\\YourName`), so you can type the lines exactly as written. Do not replace it.",
  FILEMGR="File Explorer",
  IDX="`C:\\Users\\YourName\\idx`",
  GOHOME="cd %USERPROFILE%",
  HOMEEX="`C:\\Users\\YourName`",
  NEWLINE_NOTE="",
  CAREFUL_EXTRA="Windows may show a blue warning box when you run an installer (\"Windows protected your PC\"). Click **More info**, then **Run anyway**, only if you downloaded the file from the link in this guide.",
),
"macos": dict(
  NAME="macOS", FILE="macos", SHORT="macOS",
  TERMINAL="Press **Command + Space**, type `Terminal`, and press **Return**. A window with a text prompt opens. This is the terminal for everything in this guide.",
  PASTE="Paste with **Command + V**.",
  GIT="Type this in the Terminal and press **Return**:\n\n```\nxcode-select --install\n```\n\nA pop-up appears. Click **Install**, agree to the licence, and wait. It can take 15 minutes or more. If the message says the tools are already installed, that is fine.",
  MINIFORGE_FILE="Miniforge3-MacOSX-arm64.sh (Apple chip) or Miniforge3-MacOSX-x86_64.sh (Intel chip)",
  MINIFORGE="First find out which chip your Mac has: click the Apple menu, then **About This Mac**. If it says **Chip: Apple M**something, use the **arm64** file. If it says **Processor: Intel**, use the **x86_64** file.\n\nDownload the file from **github.com/conda-forge/miniforge** into your **Downloads** folder. Then, in the Terminal, run the command below (use the file name you downloaded):\n\n```\nbash ~/Downloads/Miniforge3-MacOSX-arm64.sh\n```\n\nPress **Return** to read the licence, type `yes` and press **Return**, accept the default location, and when it asks *\"Do you wish the installer to initialize Miniforge3 by running conda init?\"* type `yes`. Then **quit Terminal completely** (Command + Q) and open it again.",
  FOLDER="~/Research",
  CD_REPO="cd ~/Research/NSDF-Data",
  CD_PYTHON="cd ~/Research/NSDF-Data/python",
  CD_NOTES="cd ~/Research/NSDF-Data/R76/analysis_notes",
  MKDIR="mkdir -p ~/Research",
  LISTCMD="ls",
  NEW_TERM="a **new** terminal",
  OPEN_TERM="a terminal (Step 1 of the setup guide)",
  HOME_NOTE="",
  FILEMGR="Finder",
  IDX="`~/idx`",
  GOHOME="cd ~",
  HOMEEX="`/Users/YourName`  (the `~` symbol means this folder)",
  CAREFUL_EXTRA="macOS may say an app is from an unidentified developer when you open it. You do not need to open any app in this guide, so you can ignore this.",
),
"linux": dict(
  NAME="Linux", FILE="linux", SHORT="Linux",
  TERMINAL="Press **Ctrl + Alt + T** (on Ubuntu), or search your applications for **Terminal**. A window with a text prompt opens. This is the terminal for everything in this guide.",
  PASTE="Paste with **Ctrl + Shift + V** (plain Ctrl+V does not work in most terminals).",
  GIT="This guide uses Ubuntu or Debian commands. If you use another distribution, use its package manager instead. Type:\n\n```\nsudo apt install git\n```\n\nIt asks for your password. Nothing appears while you type it; that is normal. Press **Return**, then type `y` and press **Return** if it asks to continue.",
  MINIFORGE_FILE="Miniforge3-Linux-x86_64.sh (most PCs)",
  MINIFORGE="Check your computer type with this command, which prints one word:\n\n```\nuname -m\n```\n\n`x86_64` means the file below. `aarch64` means an ARM computer: use **Miniforge3-Linux-aarch64.sh** instead.\n\nOpen **github.com/conda-forge/miniforge** in your web browser and download the file into your **Downloads** folder. Then install it with this command (use the file name you downloaded):\n\n```\nbash ~/Downloads/Miniforge3-Linux-x86_64.sh\n```\n\nPress **Return** to read the licence, type `yes`, accept the default location, and when it asks about running `conda init`, type `yes`. Then **close the terminal and open a new one**.",
  FOLDER="~/Research",
  CD_REPO="cd ~/Research/NSDF-Data",
  CD_PYTHON="cd ~/Research/NSDF-Data/python",
  CD_NOTES="cd ~/Research/NSDF-Data/R76/analysis_notes",
  MKDIR="mkdir -p ~/Research",
  LISTCMD="ls",
  NEW_TERM="a **new** terminal",
  OPEN_TERM="a terminal (Step 1 of the setup guide)",
  HOME_NOTE="",
  FILEMGR="Files (the file manager)",
  IDX="`~/idx`",
  GOHOME="cd ~",
  HOMEEX="`/home/yourname`  (the `~` symbol means this folder)",
  CAREFUL_EXTRA="Use `sudo` only for the one command that installs Git. Other commands in this guide must not use it.",
),
}

GLOSSARY = """
| Word | What it means |
|---|---|
| **Terminal** | A window where you type commands and the computer answers in text. |
| **Command** | One line you type in the terminal, followed by **Enter** (or **Return**). |
| **Folder** (or directory) | A place on your computer that holds files and other folders. |
| **Path** | The address of a folder, such as `C:\\Users\\YourName\\Research`. |
| **Git** | A program that downloads and keeps track of versions of code. |
| **Repository** (repo) | A project folder that Git tracks. Here, `NSDF-Data`. |
| **Python** | The programming language the analysis is written in. You will not need to write Python to finish these guides. |
| **Conda / Miniforge** | A tool that installs Python and packages in separate, named *environments*. |
| **Environment** | A sealed set of programs and versions, so this project's software does not clash with others. |
| **Package** | A piece of ready-made software (for example `numpy`). |
| **Jupyter notebook** | A document that mixes text, code and plots, run one piece (*cell*) at a time. |
| **Branch** | A separate line of work in Git, so your changes do not touch the main code. |
"""

SETUP = """---
title: "Setting up your computer"
subtitle: "NSDF-Data student guide 1 — @NAME@ edition"
date: "Version 3 · 6 October 2026"
---

::: tip
**Who this is for.** You are starting from little or no computing experience. You will paste some commands into a terminal and read the answers. You do **not** need to know any programming. Work through the steps in order. Each step ends with a **Checkpoint**: if it does not match, stop there.
:::

## Before you start

- **Time:** about one hour. Most of it is waiting for downloads and installers.
- **You need:** an internet connection, the password for your computer, and about 3 GB of free disk space.
- **Rule of thumb:** type or paste commands **exactly** as written. Capitals and spaces matter.
- **When something goes wrong:** do not guess. Copy the message, note the step you were on, and ask the project lead. See *If something goes wrong* at the end.

## Words you will meet

@GLOSSARY@

## Step 1. Open a terminal

@TERMINAL@

@PASTE@

::: checkpoint
You see a line of text ending in a symbol such as `>`, `$` or `%`. Type `echo hello` and press Enter: the word `hello` should appear under it.
:::

## Step 2. Install Git

@GIT@

::: checkpoint
In the terminal, type `git --version` and press Enter. You should see a line starting with `git version`.
:::

## Step 3. Install Miniforge

Miniforge installs Python and the other packages the analysis needs. Its download file is **@MINIFORGE_FILE@**.

@MINIFORGE@

::: checkpoint
Open @NEW_TERM@ and type `conda --version`, then press Enter. You should see `conda` followed by a version number.
:::

::: careful
@CAREFUL_EXTRA@
:::

## Step 4. Download the NSDF-Data code

Your project will live in a folder called `Research`. Create it, go into it, and download the code. Type each line and press Enter:

```
@MKDIR@
cd @FOLDER@
git clone https://github.com/villano-lab/NSDF-Data.git
@CD_REPO@
```

Downloading with `git clone` does not need a GitHub account. It makes a full copy of the project in a folder named `NSDF-Data`.

@HOME_NOTE@

::: checkpoint
Type `@LISTCMD@` and press Enter. You should see `NSDF-Data` in the list.
:::

## Step 5. Create your analysis environment

An environment is a sealed box of programs with fixed versions. We make one for this project, called `darkmatter_cli_env`. Type these lines one at a time, pressing Enter after each. The third line takes several minutes and prints a lot of text: wait for the prompt to come back.

```
conda create -n darkmatter_cli_env python=3.10 -y
conda activate darkmatter_cli_env
python -m pip install nsdf-dark-matter==0.3.0 nsdf-dark-matter-cli==0.5.0
python -m pip install numpy==2.2.6 matplotlib==3.10.7 h5py pytest ipykernel
python -m pip install jupyterlab
```

::: careful
Do **not** use the file `environment.yml` from the project. It was made on a Mac for Mac only, and it will fail on other computers. The three lines above install the same versions.
:::

::: tip
Every time you open a new terminal, run `conda activate darkmatter_cli_env` first. When it is active, the start of each line shows `(darkmatter_cli_env)`.
:::

::: checkpoint
The last line of the output is a message, not an error, and the `(darkmatter_cli_env)` label is at the start of your prompt.
:::

## Step 6. Check that everything works

First, the tests. They use made-up data, so they need no download. Type each line and press Enter:

```
conda activate darkmatter_cli_env
@CD_PYTHON@
python -m pytest -q
```

::: checkpoint
The last line says `52 passed` (it can be a larger number later, which is also fine). If it says `failed`, stop and ask the project lead, and do not change any files.
:::

Then, the data tool:

```
nsdf-cli version
```

::: checkpoint
It prints `NSDF Dark Matter CLI: 0.5.0` (or a later version).
:::

Finally, the notebook program:

```
jupyter lab --version
```

::: checkpoint
It prints a version number, such as `4.4.0`. If it says `jupyter-lab` is not found, run `python -m pip install jupyterlab` and try again.
:::

## Step 7. Let Jupyter notebooks use your environment

Jupyter is the notebook program you will use. Register your environment with it once:

```
python -m ipykernel install --user --name darkmatter_cli_env
```

::: checkpoint
It prints a line that starts with `Installed kernelspec darkmatter_cli_env`.
:::

## Step 8. Get permission to save your work

You will not change the main project. You will save your work on your own **branch**, and for that the lead must give you access:

1. Make a free account at **github.com** if you do not have one.
2. Send your GitHub username to the project lead. They will add you to the project as a collaborator.
3. Once you have accepted the invitation, set your name and email for Git. Use your own details:

```
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
```

4. Create your personal branch. Use your own name, without spaces, in place of `yourname`:

```
@CD_REPO@
git checkout -b student-yourname
```

::: checkpoint
The terminal shows `Switched to a new branch 'student-yourname'`.
:::

## Rules for keeping your work safe

- **Never work on `master`.** That is the shared main version. Work only on your `student-` branch.
- **Never commit data.** The raw files in the `idx` folder are large and not part of the project. Download only from your home folder, never from inside `NSDF-Data`.
- **Do not run `07221203_2025_dump1_noise.ipynb`** unless the project lead says it is fine. It overwrites a shared archive file.
- **Save often,** and commit your work when a piece is finished (see the first analysis guide).

## You are done when

- [ ] Your terminal opens and `git --version` prints a version.
- [ ] `conda --version` prints a version, in a new terminal.
- [ ] The `NSDF-Data` folder is in `@FOLDER@`.
- [ ] `python -m pytest -q` in the `python` folder ends with `52 passed`.
- [ ] `nsdf-cli version` prints a version.
- [ ] `jupyter lab --version` prints a version.
- [ ] Your Jupyter kernel `darkmatter_cli_env` is installed.
- [ ] You have a `student-` branch (after access is granted).

**Next:** *First analysis* (the guide for @NAME@).

## If something goes wrong

1. Read the **last line** of the message. It usually says what is wrong.
2. Close the terminal, open a new one, and run `conda activate darkmatter_cli_env` again. Many problems are just the wrong environment.
3. Copy the command you ran and the message it printed, and send them to the project lead. A screenshot is also fine.

## Where to get help

**Anthony Villano**, project lead: anthony.villano@ucdenver.edu

When you write, include the step number, the command you typed, and the last few lines the computer printed. A screenshot helps. Nobody will be annoyed by a question about a step that did not work.

## Session Info

Guide version 3, 6 October 2026, @NAME@ edition. Written for beginners; please tell the project lead where a step was unclear, so the guide can be fixed.

## Key links

- Notes site: <https://villano-lab.github.io/NSDF-Data/>
- Repository: <https://github.com/villano-lab/NSDF-Data>
- Miniforge downloads: <https://github.com/conda-forge/miniforge>
- Git downloads: <https://git-scm.com>
"""

FIRST = """---
title: "Your first analysis"
subtitle: "NSDF-Data student guide 2 — @NAME@ edition"
date: "Version 3 · 6 October 2026"
---

::: tip
**What you will do.** Download one set of real detector data, open it in a notebook, look at it, and reproduce one number from an existing note. You will need the setup guide for @NAME@ finished first.
:::

## Before you start

- **Time:** about two hours.
- **You need:** the setup guide finished (your environment `darkmatter_cli_env` exists and works).
- **Check:** open @OPEN_TERM@, and run `conda activate darkmatter_cli_env`. The start of the line should show `(darkmatter_cli_env)`.

## Words you will meet

| Word | What it means here |
|---|---|
| **Series** | One data-taking session, named like `07221203_2025`. |
| **Dump** | One file set taken from a series, numbered `F0001`, `F0002`, ... |
| **Event** | One trigger of the detector. Events are numbered in time order. |
| **Detector / channel** | One physical detector, and one of its four sensor channels. We use detector 0, channel 0. |
| **Trace** | The recorded signal for one channel in one event: 4096 numbers, one per sample. |
| **Sample** | One reading. Each sample is 1.6 microseconds long. |
| **ADC counts** | The unit of the numbers in a trace. |
| **Baseline** | The flat level a trace sits at when nothing happens. |
| **Pretrigger window** | The first samples of a trace, used to measure the baseline. |

## Step 1. Read three notes first (about 30 minutes)

Open the notes site at **villano-lab.github.io/NSDF-Data** and read these, in order:

1. **Note 1**, *Run76 series catalog*: what a series and a dump are.
2. **Note 1a**, *python library structure*: what each part of the code does.
3. **Note 2**, *Noise-pulse selection*: how we pick quiet traces.

You do **not** need to follow every number. Just learn the words in the table above.

## Step 2. Download the data

First go to your home folder, so the data lands in the right place. Type this, then press Enter:

```
@GOHOME@
```

Now download the data:

```
nsdf-cli download 07221203_2025_F0001
```

The download puts the data in an `idx` folder **in the folder you are in**. Because you went to your home folder first, it lands in @IDX@, inside a folder named `07221203_2025_F0001`. The data is about 34 MB. Wait until the prompt comes back.

::: careful
Never download from inside the `NSDF-Data` folder. Its `idx` folder would sit inside the project, where Git can pick it up. If you have already downloaded there, move the `idx` folder to your home folder, and tell your lead.
:::

::: careful
Do not move or edit the downloaded files, and do not add them to Git. They are not part of the project.
:::

::: tip
If the message says the folder already exists, the data may already be there. Ask the project lead before you delete anything.
:::

## Step 3. Open Jupyter in the right folder

Notebooks must be opened from the folder `R76/analysis_notes`, inside the project. In the terminal, type these lines:

```
conda activate darkmatter_cli_env
@CD_NOTES@
jupyter lab
```

Your web browser opens a Jupyter page. Click **File**, then **New**, then **Notebook**. If it asks which kernel to use, choose **darkmatter_cli_env**.

::: tip
A notebook is a list of boxes called **cells**. Type code in a cell and press **Shift + Enter** to run it. The result appears under the cell. Press **Enter** (without Shift) to keep typing in the same cell.
:::

Give your notebook a name: click the name at the top, type `first-analysis-yourname`, and press Enter.

## Step 4. Load the data and count the traces

Copy this into the first cell and press **Shift + Enter**:

```python
import sys
from pathlib import Path

# Tell Python where the pulse library (the python folder) is.
# This notebook is in R76/analysis_notes, so it is two folders up.
sys.path.insert(0, str(Path.cwd().parents[1] / "python"))

from nsdf_dark_matter.idx import load_all_data
import pulse_io as pio

# Open the dump you downloaded.
cdms = load_all_data(str(Path.home() / "idx" / "07221203_2025_F0001"))

# Take every trace from detector 0, channel 0, into one table.
ids, pulses = pio.load_channel_batch(
    cdms, pio.filter_by_detector(cdms.get_detector_ids(), 0), 0)

print(pulses.shape)
```

::: checkpoint
The output is `(1517, 4096)`: 1517 traces, each with 4096 samples. If you get a different number, stop and check the dump name and the folder in Step 2.
:::

## Step 5. Look at a trace

Put this in a new cell (click **+** in the toolbar, or use the menu **Insert**, then **Insert Cell Below**), and run it:

```python
import matplotlib.pyplot as plt

plt.plot(pulses[0])
plt.xlabel("sample (1.6 microseconds each)")
plt.ylabel("ADC counts")
plt.show()
```

Now change the `0` to `1`, `2`, `3` and run again. Most traces look like flat noise, with a little jitter.

## Step 6. Reproduce a number from Note 2

Note 2 says that for this dump, a strict selection leaves **179 quiet traces**. Run this in a new cell:

```python
from dataclasses import replace
from pulse_config import DEFAULT_CONFIG
import pulse_quantities as pq
import pulse_cuts as pc
import numpy as np

c500 = replace(DEFAULT_CONFIG, pretrigger_samples=500)
quiet = pc.excursion_band(pulses, c500) & (np.log10(pq.bstd(pulses)) < 0.5)
print(quiet.sum())
```

::: checkpoint
The output is **179**. If you see a different number, that is worth knowing. Write down the number you got and the steps you took, and tell the project lead. Do not change the project's code to make the number match.
:::

## Step 7. Write down what you did

In Jupyter, click **+** to add a cell and change its type from *Code* to **Markdown** in the toolbar. In that cell, write a few sentences in plain English: what you loaded, what you plotted, and what number you got. Then press **Shift + Enter**.

Save with **Command + S** (macOS) or **Ctrl + S** (Windows and Linux).

Once your branch exists (setup guide, Step 8), save your notebook to Git:

```
@CD_REPO@
git add R76/analysis_notes/first-analysis-yourname.ipynb
git commit -m "First analysis: load dump 1 and count the quiet traces"
git push -u origin student-yourname
```

::: careful
Commit only your notebook. Check the list before committing with `git status`. If you see `.bin` files or anything from the `idx` folder, do not add them.
:::

## You are done when

- [ ] `(1517, 4096)` printed after loading the data.
- [ ] You plotted at least three traces and can say what the flat ones look like.
- [ ] You got 179 from the selection, or wrote down what you got and why you think it differs.
- [ ] Your notebook is saved, and committed to your branch if you have access.

## Common problems

| What you see | What to do |
|---|---|
| `ModuleNotFoundError: No module named 'nsdf_dark_matter'` | You are not in the environment. Run `conda activate darkmatter_cli_env`, then restart the notebook kernel (**Kernel**, then **Restart Kernel**). |
| `ModuleNotFoundError: No module named 'pulse_io'` | Jupyter was started from the wrong folder. Close it and start it again from `R76/analysis_notes`. |
| `FileNotFoundError` on the dump folder | The download did not finish, or it went somewhere else. Check the folder in Step 2. |
| A huge spike at the very start of traces | This is a real electronics glitch in the first few samples, not a bug. It is explained in Note 2a. |
| The kernel is not `darkmatter_cli_env` | Click the kernel name at the top right and choose **darkmatter_cli_env**. |

::: careful
Do not run `07221203_2025_dump1_noise.ipynb` unless the project lead says it is fine. It overwrites a shared archive file.
:::

## Where to get help

**Anthony Villano**, project lead: anthony.villano@ucdenver.edu

When you write, include the step number, the command you typed, and the last few lines the computer printed. A screenshot helps. Nobody will be annoyed by a question about a step that did not work.

## Session Info

Guide version 3, 6 October 2026, @NAME@ edition. Written for beginners; please tell the project lead where a step was unclear.

## Key links

- Note 1: <https://villano-lab.github.io/NSDF-Data/notes/note-01-run76-series-catalog.html>
- Note 1a: <https://villano-lab.github.io/NSDF-Data/notes/note-01a-pulse-library-structure.html>
- Note 2: <https://villano-lab.github.io/NSDF-Data/notes/note-02-noise-selection.html>
- Repository: <https://github.com/villano-lab/NSDF-Data>
"""

for key, o in OS.items():
    o = dict(o)
    for kind, tpl in (("setup", SETUP), ("first-analysis", FIRST)):
        s = tpl.replace("@GLOSSARY@", GLOSSARY.strip())
        for k in ("NAME","TERMINAL","PASTE","GIT","MINIFORGE_FILE","MINIFORGE","CAREFUL_EXTRA","FOLDER","CD_REPO","CD_PYTHON","CD_NOTES","MKDIR","LISTCMD","IDX","GOHOME","NEW_TERM","OPEN_TERM","HOME_NOTE"):
            s = s.replace("@"+k+"@", o[k])
        assert "@" not in s.replace("@", "@") or True
        open(f"{kind}-{key}.md", "w", encoding="utf-8", newline="\n").write(s)
        print(kind, key, len(s))
