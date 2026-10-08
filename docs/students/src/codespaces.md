---
title: "Working in your browser with GitHub Codespaces"
subtitle: "NSDF-Data student guide 6 — no install, for every computer"
date: "Version 3 · 7 October 2026"
---

::: tip
**What this is.** GitHub Codespaces gives you a complete Linux computer in your web browser, already set up for this project. You do not install Python, Git or anything else on your own machine. This works on Windows, macOS, Linux and Chromebooks, as long as you have a web browser and a GitHub account.
:::

::: careful
**Status: partly tested.** The setup has been tested once by the project lead, with the same Python and package versions as the lab. The automatic setup step, which runs by itself when you open a codespace, is still being checked. If the environment is missing when you open it, use the fallback in *If the environment is missing* below, and tell your lead.
:::

## Before you start

- A **GitHub account**. Ask your lead to add you to the project first, so that you can save your work on a branch.
- A **web browser** (Chrome, Edge, Firefox or Safari). A Chromebook works well.
- Your lead has confirmed your **usage budget** for Codespaces. A free account gets a small monthly allowance of computing hours. Once it is used up, you may be billed, so stop your codespace when you finish.

## Words you will meet

| Word | What it means here |
|---|---|
| **Codespace** | Your own Linux computer in the browser, for this project. |
| **Terminal** | A window in the codespace where you type commands. |
| **Notebook** | A document that mixes text, code and plots (a `.ipynb` file). |
| **Stop** | Turns the codespace off, so it stops using your hours. Your files are kept. |
| **Delete** | Removes the codespace and everything in it that is not saved to GitHub. |

## Step 1. Start a codespace

1. Go to [github.com/villano-lab/NSDF-Data](https://github.com/villano-lab/NSDF-Data).
2. Click the green **Code** button, then the **Codespaces** tab.
3. Click **Create codespace on develop**. (The button names the project's main working branch.)

A new browser tab opens with a code editor and a terminal at the bottom. The first start takes several minutes while the environment is prepared. Wait until the page stops changing.

::: checkpoint
You see the project's files on the left, and a terminal at the bottom. Type `python3 --version` in the terminal and press Enter. You should see `Python 3.10`.
:::

## Step 2. Check the environment

Type these lines into the terminal, one at a time, pressing Enter after each:

```
nsdf-cli version
python -c "import nsdf_dark_matter; print('ok')"
cd python && python -m pytest -q && cd ..
```

::: checkpoint
You see `NSDF Dark Matter CLI: 0.5.0`, then `ok`, then a line ending `52 passed` (a larger number is fine).
:::

## Step 3. Download the data

::: careful
Download from your **home folder**, not from inside the project. The project folder is tracked by Git, and the data would be picked up by mistake.
:::

```
cd ~
nsdf-cli download 07221203_2025_F0001
```

The data (about 34 MB) goes into an `idx` folder in your home folder. Wait until the prompt comes back.

## Step 4. Open the first-analysis notebook

Follow the steps of the first analysis guide (guide 2 for your computer). The only changes are these:

- **Open a notebook** from the file list on the left: `data_analysis/R76/student/`, then click **New File**, or copy the code from the guide into a new notebook.
- **Choose the kernel** when asked. Pick **darkmatter_cli_env** or the Python 3.10 kernel shown in the list.
- **Data path.** In the codespace your home folder is `/home/vscode`, and the code in the guide uses `Path.home() / "idx"`, so it finds the data without changes.
- **Start the notebook from the right folder.** The code expects to run inside `data_analysis/R76/student`, so open the notebook from there.

::: checkpoint
The first cell prints `(1517, 4096)` and the quiet-trace cell prints `179`.
:::

## Step 5. Save your work

Your work is kept in the codespace, but **it is not part of the project until it is saved to GitHub**. To save a notebook:

1. Click the **Source Control** icon in the left toolbar (it looks like a branch).
2. Under **Changes**, check that only your notebook (and your note, if you have one) is listed. If `idx` or any `.bin` file appears, do not add it.
3. Type a short message, such as `First analysis: 179 quiet traces`, and click **Commit**.
4. Follow your lead's instructions for branches and pull requests. Notes are published through a pull request, as guides 3 and 4 explain.

## Step 6. Stop the codespace

When you finish, **stop** the codespace so it stops using your hours. Click the name of the codespace at the bottom left of the window, then **Stop Current Codespace**. Or go to [github.com/codespaces](https://github.com/codespaces) and use the menu next to it.

::: careful
Do not leave a codespace running overnight. It keeps using your hours while it is on.
:::

## If the environment is missing

If `python -c "import nsdf_dark_matter"` fails, the setup step did not run. Install the packages by hand, in the terminal:

```
python -m pip install nsdf-dark-matter==0.3.0 nsdf-dark-matter-cli==0.5.0 numpy==2.2.6 matplotlib==3.10.7 h5py pytest ipykernel
```

Then run the checks in Step 2 again. If that does not work, copy the last lines of the message and send them to your lead.

## You are done when

- [ ] A codespace starts from the project's `develop` branch.
- [ ] The Step 2 checks pass.
- [ ] The data is in your home folder, and `(1517, 4096)` and `179` are printed.
- [ ] Your notebook is committed through Source Control.
- [ ] You have stopped the codespace.

## Session Info

Guide version 3, 7 October 2026. Written for every computer. Please tell the project lead where a step was unclear.

## Where to get help

**Anthony Villano**, project lead: <anthony.villano@ucdenver.edu>

When you write, include the codespace name (shown at the bottom left), the command you ran, and the last lines of its output.

## Key links

- Repository: <https://github.com/villano-lab/NSDF-Data>
- Your codespaces: <https://github.com/codespaces>
- Guide 2, first analysis (choose your computer): <https://villano-lab.github.io/NSDF-Data/>
