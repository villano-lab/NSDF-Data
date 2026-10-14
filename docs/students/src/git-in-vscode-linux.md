---
title: "Git in VS Code"
subtitle: "NSDF-Data student guide 9 — Linux edition, optional"
date: "Version 2 · 14 October 2026"
---

::: tip
**This is guide 9, and it is optional.** It does the same Git steps as the terminal guides, with buttons in VS Code instead of typed commands. If you are happy with the terminal, you do not need this guide. If a screen here does not match what you see, trust the terminal version, and tell your lead which step differed.
:::

## Before you start

- You finished the setup guide (guide 1) for Linux, including Step 8, which made your branch `student-yourname`.
- You have read *Git in five minutes* (guide 8). It explains the words used here: commit, branch, push, pull request.
- **Time:** about 15 minutes, plus the install in Step 1 if you do not have VS Code yet.

VS Code uses the Git that guide 1 installed, so nothing else has to be set up.

## Step 1. Install VS Code

If you wrote a note in Markdown (guide 3), you already have it: skip to Step 2.

This guide uses Ubuntu or Debian commands. If you use another distribution, follow [Microsoft's instructions for Linux](https://code.visualstudio.com/docs/setup/linux) instead. Go to [code.visualstudio.com](https://code.visualstudio.com/) and download the `.deb` file. In a terminal, go to the folder with the file (usually `cd ~/Downloads`) and run:

```
sudo apt install ./code_*.deb
```

It asks for your password. Nothing appears while you type it; that is normal. If you have downloaded more than one such file, use the exact file name instead of the `*`. When it finishes, start **Visual Studio Code** from your applications menu.

::: checkpoint
VS Code starts and shows a **Welcome** page.
:::

## Step 2. Open the project folder

1. Start VS Code.
2. Choose **File**, then **Open Folder**, and pick the `NSDF-Data` folder (the one in `~/Research`).
3. VS Code may ask whether you trust the authors of the files in this folder. This is your own copy of the project: choose **Yes, I trust the authors**.

::: careful
Until you trust the folder, the **Source Control** tab (Step 4) stays empty and says that Git does not work in Restricted Mode. Nothing is broken: trust the folder and it fills in.
:::

## Step 3. Check your branch

Look at the bottom-left corner of the VS Code window. It shows the name of your branch.

::: checkpoint
The corner shows `student-yourname` (your own branch). This is the same check as `git branch --show-current` in the terminal guides.
:::

::: careful
If it shows `develop` or `master`, **stop and ask your lead**. Do not commit, and do not press any button in the Source Control tab. Your own work belongs on your own branch.
:::

To change branch, click the name in the corner and pick yours from the list.

## Step 4. Save your work as a commit

1. Open **Source Control**: click the branch-shaped icon in the bar on the left, or press `Ctrl+Shift+G`.
2. Under **Changes**, every file you changed is listed with a letter: **M** for changed, **U** for new. Read the list before you do anything else.

::: checkpoint
The list contains only your own files (your notebook, your note, its pictures). If it shows data files (a folder named `idx`, or `.bin` files) or other people's files, do not stage them: ask your lead.
:::

3. Move the mouse over one of your files and click the **+** (Stage Changes). The file moves to **Staged Changes**. Do this for each of your files. This is `git add`.
4. Click the box that says **Message** and write what you changed, in a few words. This is the `-m "..."` of `git commit`.
5. Click **Commit**.

::: careful
If VS Code says that there are no staged changes and asks whether to stage everything and commit, choose **Cancel**, and stage your files yourself with the **+** button. "Commit all" is how data files and other people's files get in by mistake.
:::

## Step 5. Send your commits to GitHub

After a commit, the big blue button under the message box shows what is left to send.

- The first time on your branch, it reads **Publish Branch**. Click it. If VS Code asks which remote, choose `origin`.
- After that, it reads **Sync Changes** with a number and an arrow. The up-arrow number is how many of your commits are waiting to go to GitHub. Click it to send them.

::: careful
Read the branch name in the bottom-left corner before you click either button. They send your commits to GitHub, so they must say your own branch. If the corner shows anything other than `student-yourname`, stop and ask your lead.
:::

::: checkpoint
The big blue button no longer shows an up-arrow number, and your branch appears on <https://github.com/villano-lab/NSDF-Data/branches>.
:::

This step is `git push` (the first time, `git push -u origin student-yourname`).

## Step 6. Bring in the newest project changes

The project keeps changing. When *Updating your setup* (guide 7) tells you to bring in the newest changes (its Step 2), you can do that step here instead of typing the two lines. Do all the other steps of guide 7 as written, because they update your environment.

1. Press `Ctrl+Shift+P`. A box opens at the top of the window.
2. Type `Git: Fetch`{.cmd} and press Enter. This downloads the newest changes without touching your files (`git fetch origin`).
3. Press `Ctrl+Shift+P` again, type `Git: Merge...`{.cmd}, and press Enter.
4. A list of branches opens. Choose **origin/develop**, under *remote branches*. This combines it with your branch (`git merge --no-edit origin/develop`).

::: checkpoint
VS Code finishes without an error message, and the Source Control tab shows no conflict.
:::

::: careful
If VS Code reports a **conflict**, or opens a window with two versions of a file side by side, **stop. Do not click anything in that window and do not edit anything.** Send your lead a screenshot or the message. This is the same rule as the terminal guides.
:::

## Step 7. Open a pull request

When a note or a piece of work is ready for review, open the pull request the way guide 4 (Step 3) shows, on github.com. That route has been tested step by step, and it is the one to use.

### Optional: from inside VS Code

VS Code can also open pull requests for you, with an extension made by GitHub.

::: careful
This part was written from the extension's own documentation and has **not yet been tried on a student's computer**. If a screen differs, stop, and use guide 4 instead.
:::

1. Press `Ctrl+Shift+X` to open **Extensions**.
2. Search for `GitHub Pull Requests`{.cmd}. Install the one whose publisher is **GitHub**, with the blue check mark next to the name.
3. A GitHub icon appears in the bar on the left. Click it and choose **Sign in**. A web page opens in your browser: sign in to GitHub there. **Never type your GitHub password into VS Code or into the terminal.**
4. Your branch is listed in the extension's view, with a button to create a pull request. Follow the prompts, and write the pull request description as guide 4 says.

## The same steps in the terminal

| In VS Code | In the terminal |
|---|---|
| The corner of the window | `git branch --show-current` |
| The list of changes in Source Control | `git status` |
| The **+** button | `git add your-file` |
| Message box and **Commit** | `git commit -m "..."` |
| **Publish Branch** (first time), then **Sync Changes** | `git push -u origin student-yourname`, then `git push` |
| `Git: Fetch`{.cmd} and `Git: Merge...`{.cmd} with `origin/develop` | `git fetch origin` and `git merge --no-edit origin/develop` |

## When something looks wrong

| You see | What it means | What to do |
|---|---|---|
| The Source Control tab is empty and mentions Restricted Mode | VS Code has not been told to trust this folder. | Step 2, point 3. |
| The corner shows `develop` or `master` | You are not on your own branch. | Stop. Do not commit or push. Ask your lead. |
| No **Source Control** icon, or "no repository found" | The folder you opened is not the `NSDF-Data` folder. | **File**, **Open Folder**, and pick the `NSDF-Data` folder itself. |
| A question about staging everything and committing | Nothing is staged yet. | **Cancel**, then stage your files with **+** (Step 4). |
| **Sync Changes** shows a down-arrow number as well as an up-arrow number | There are newer commits on GitHub too. | Ask your lead, or see guide 7, Step 2. |
| A window with two versions of a file side by side | A conflict. | Stop. Click nothing. Send it to your lead. |
| "Make sure you configure your user.name and user.email", or a permission error | Git does not know your name, or you are not signed in to GitHub. | Setup guide, Step 8. Never type your GitHub password into VS Code. |

## Session Info

Guide version 2, 14 October 2026, Linux edition. The Git steps were checked in a browser version of VS Code on a test copy of the project, on Windows (commit, the branch list, the merge list, and installing the extension). The install step for your system, the sign-in, and the pull-request part have not been tried on a student's computer yet. Please tell the project lead where a step was unclear.

## Where to get help

**Anthony Villano**, project lead: <anthony.villano@ucdenver.edu>

When you write, include a screenshot of the VS Code window and the message that worried you.

## Key links

- Repository: <https://github.com/villano-lab/NSDF-Data>
- Student guides: <https://villano-lab.github.io/NSDF-Data/>
- VS Code: <https://code.visualstudio.com/>
