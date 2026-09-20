"""End-of-session helper.
Prompts for a few details, updates AI_SESSIONS.md, regenerates context,
commits and pushes to GitHub. Run via session.bat.
"""
import os, sys, datetime, subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))


def ask(prompt):
    try:
        return input(prompt).strip()
    except EOFError:
        return ""


def main():
    os.chdir(ROOT)
    print("=" * 50)
    print("  End-of-session: save notes and push")
    print("=" * 50)
    print()

    who = ask("Which AI just worked? (e.g. Claude) : ")
    goal = ask("What was the goal?                 : ")
    did = ask("What did it do?                    : ")
    next_step = ask("Next step?                         : ")

    if not who:
        who = "Unknown"
    if not goal:
        goal = "-"
    if not did:
        did = "-"
    if not next_step:
        next_step = "-"

    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    block = "### " + ts + " - " + who + "\n"
    block += "**Goal:** " + goal + "\n"
    block += "**Did:** " + did + "\n"
    block += "**Next:** " + next_step + "\n\n"

    path = os.path.join(ROOT, "AI_SESSIONS.md")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            content = f.read()
    else:
        content = "# AI Sessions Log\n\n---\n\n"

    marker = "\n---\n\n"
    idx = content.find(marker)
    if idx >= 0:
        new_content = content[:idx + len(marker)] + block + content[idx + len(marker):]
    else:
        new_content = content + "\n" + block

    with open(path, "w", encoding="utf-8") as f:
        f.write(new_content)
    print("\n[session added to AI_SESSIONS.md]")

    print("\n[regenerating AI_CONTEXT.md]")
    subprocess.call([sys.executable, "ai_sync.py"], cwd=ROOT)

    print("\n[staging changes]")
    subprocess.call(["git", "add", "."], cwd=ROOT)

    print("\n[committing]")
    short_goal = (goal[:50] + "...") if len(goal) > 50 else goal
    subprocess.call(["git", "commit", "-m",
                     "Session: " + who + " - " + short_goal], cwd=ROOT)

    print("\n[pushing to GitHub]")
    subprocess.call(["git", "push"], cwd=ROOT)

    print("\n" + "=" * 50)
    print("  DONE")
    print("=" * 50)
    input("\nPress Enter to close...")


if __name__ == "__main__":
    main()