# ai_sync.py - auto-generates AI_CONTEXT.md
import os, sys, subprocess, re, datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
CTX = os.path.join(ROOT, "AI_CONTEXT.md")
NOTES = os.path.join(ROOT, "AI_NOTES.md")


def git(*args):
    try:
        return subprocess.check_output(
            ["git"] + list(args), cwd=ROOT, text=True,
            stderr=subprocess.DEVNULL
        ).rstrip()
    except Exception:
        return ""


def tree():
    files = git("ls-files").splitlines()
    if not files:
        return "(no tracked files)"
    out, seen = [], set()
    for f in files:
        parts = f.split("/")
        for i in range(len(parts) - 1):
            d = "/".join(parts[:i+1]) + "/"
            if d not in seen:
                seen.add(d)
                out.append("  " * i + parts[i] + "/")
        out.append("  " * (len(parts) - 1) + parts[-1])
    return "\n".join(out)


def loc_table():
    files = git("ls-files").splitlines()
    rows = []
    for f in files:
        p = os.path.join(ROOT, f)
        if not os.path.isfile(p):
            continue
        if not f.endswith((".py", ".md", ".toml", ".txt", ".bat", ".json")):
            continue
        try:
            with open(p, encoding="utf-8", errors="ignore") as fh:
                n = sum(1 for _ in fh)
            m = datetime.datetime.fromtimestamp(
                os.path.getmtime(p)
            ).strftime("%Y-%m-%d %H:%M")
            rows.append((n, f, m))
        except Exception:
            pass
    rows.sort(reverse=True)
    out = ["| LOC | File | Modified |", "|---:|---|---|"]
    for n, f, m in rows[:30]:
        out.append("| " + str(n) + " | `" + f + "` | " + m + " |")
    return "\n".join(out) if len(out) > 2 else "(no files)"


def recent_commits():
    raw = git("log", "-12", "--pretty=format:%h|%ad|%an|%s",
              "--date=format:%Y-%m-%d %H:%M")
    if not raw:
        return "(no commits)"
    lines = ["| Hash | Date | Author | Subject |", "|---|---|---|---|"]
    for line in raw.splitlines():
        parts = line.split("|", 3)
        if len(parts) == 4:
            lines.append("| `" + parts[0] + "` | " + parts[1] +
                         " | " + parts[2] + " | " + parts[3] + " |")
    lines.append("")
    lines.append("**Files changed in latest commits:**")
    for line in raw.splitlines()[:5]:
        h = line.split("|", 1)[0]
        stat = git("show", "--stat", "--oneline", "--no-color", h)
        sl = stat.splitlines()
        if len(sl) > 1:
            lines.append("- `" + h + "`")
            for s in sl[1:]:
                lines.append("    " + s.strip())
    return "\n".join(lines)


def status_summary():
    s = git("status", "--short")
    b = git("rev-parse", "--abbrev-ref", "HEAD") or "(no branch)"
    head = git("log", "-1", "--pretty=%h %s") or "(no commit)"
    when = git("log", "-1", "--pretty=%cr")
    dirty = len(s.splitlines()) if s else 0
    return b, head, when, dirty, s


def todo_scan():
    hits = []
    skip = {"AI_CONTEXT.md", "ai_sync.py"}
    for f in git("ls-files").splitlines():
        if f in skip:
            continue
        if not f.endswith((".py", ".md", ".bat", ".toml")):
            continue
        p = os.path.join(ROOT, f)
        if not os.path.isfile(p):
            continue
        try:
            with open(p, encoding="utf-8", errors="ignore") as fh:
                for i, line in enumerate(fh, 1):
                    m = re.search(r"\b(TODO|FIXME|XXX|HACK)\b[:\s]*(.*)", line)
                    if m:
                        hits.append("- `" + f + ":" + str(i) +
                                    "` - " + m.group(1) + ": " +
                                    m.group(2).strip()[:120])
        except Exception:
            pass
        if len(hits) >= 40:
            break
    return "\n".join(hits) if hits else "(none)"


def notes():
    if not os.path.exists(NOTES):
        return "(no session notes yet)"
    with open(NOTES, encoding="utf-8") as f:
        text = f.read()
    text = text.replace("# Session notes", "")
    blocks = re.split(r"(?m)^##\s+", text)
    blocks = [b.strip() for b in blocks if b.strip()]
    blocks = blocks[-8:]
    return "\n\n".join("## " + b for b in blocks) if blocks else "(no notes)"


def read_if_exists(name):
    p = os.path.join(ROOT, name)
    if os.path.exists(p):
        with open(p, encoding="utf-8") as f:
            return f.read()
    return ""


def build_context():
    b, head, when, dirty, dirty_lines = status_summary()
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    remote = git("config", "--get", "remote.origin.url") or "(no remote)"
    parts = []
    parts.append("# AI Context (auto-generated - do not edit)")
    parts.append("")
    parts.append("Generated: **" + now + "**")
    parts.append("Repo: `" + remote + "`")
    parts.append("Branch: `" + b + "`")
    parts.append("HEAD: `" + head + "` (" + when + ")")
    parts.append("Working tree: **" + str(dirty) + " uncommitted file(s)**")
    parts.append("")
    parts.append("> Regenerated by ai_sync.py. Do not hand-edit.")
    parts.append("")

    for extra in ["PROJECT.md", "AI_BRIEF.md", "AI_BACKLOG.md"]:
        txt = read_if_exists(extra)
        if txt:
            parts.append("---")
            parts.append("")
            parts.append("## " + extra + " (hand-written)")
            parts.append("")
            parts.append(txt)
            parts.append("")

    sess_txt = read_if_exists("AI_SESSIONS.md")
    if sess_txt:
        blocks = re.split(r"(?m)^###\s+", sess_txt)
        blocks = [b.strip() for b in blocks if b.strip()]
        blocks = blocks[-5:]
        parts.append("---")
        parts.append("")
        parts.append("## Last 5 AI sessions")
        parts.append("")
        for b2 in blocks:
            parts.append("### " + b2)
            parts.append("")

    parts.append("---")
    parts.append("")
    parts.append("## Working tree (uncommitted)")
    parts.append("")
    parts.append("```")
    parts.append(dirty_lines if dirty_lines else "(clean)")
    parts.append("```")
    parts.append("")
    parts.append("---")
    parts.append("")
    parts.append("## Recent commits")
    parts.append("")
    parts.append(recent_commits())
    parts.append("")
    parts.append("---")
    parts.append("")
    parts.append("## Sizes and recently modified files")
    parts.append("")
    parts.append(loc_table())
    parts.append("")
    parts.append("---")
    parts.append("")
    parts.append("## TODO / FIXME / XXX in code")
    parts.append("")
    parts.append(todo_scan())
    parts.append("")
    parts.append("---")
    parts.append("")
    parts.append("## File tree")
    parts.append("")
    parts.append("```")
    parts.append(tree())
    parts.append("```")
    parts.append("")
    parts.append("---")
    parts.append("")
    parts.append("## Session notes (most recent last)")
    parts.append("")
    parts.append(notes())
    parts.append("")
    body = "\n".join(parts)
    with open(CTX, "w", encoding="utf-8") as f:
        f.write(body)
    return CTX


def add_note(text):
    if not text.strip():
        return
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    block = "## " + ts + "\n" + text.strip() + "\n\n"
    if not os.path.exists(NOTES):
        with open(NOTES, "w", encoding="utf-8") as f:
            f.write("# Session notes\n\n")
    with open(NOTES, "a", encoding="utf-8") as f:
        f.write(block)
    print("Note added: " + ts)


HOOK = "#!/bin/sh\n"
HOOK += 'cd "$(git rev-parse --show-toplevel)" || exit 0\n'
HOOK += "if command -v python >/dev/null 2>&1; then\n"
HOOK += "    python ai_sync.py >/dev/null 2>&1\n"
HOOK += "elif command -v py >/dev/null 2>&1; then\n"
HOOK += "    py -3 ai_sync.py >/dev/null 2>&1\n"
HOOK += "fi\n"
HOOK += "git add AI_CONTEXT.md AI_NOTES.md 2>/dev/null\n"
HOOK += "exit 0\n"


def install_hooks():
    if not os.path.isdir(os.path.join(ROOT, ".git")):
        print("Not a git repository.")
        return
    hooks_dir = os.path.join(ROOT, ".git", "hooks")
    os.makedirs(hooks_dir, exist_ok=True)
    for name in ("pre-commit", "post-commit", "pre-push"):
        path = os.path.join(hooks_dir, name)
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(HOOK)
        try:
            os.chmod(path, 0o755)
        except Exception:
            pass
    print("Installed hooks in " + hooks_dir)


def main():
    args = sys.argv[1:]
    if not args:
        install_hooks()
        build_context()
        print("Wrote " + CTX)
        return
    cmd = args[0]
    if cmd == "install":
        install_hooks()
    elif cmd == "note":
        add_note(" ".join(args[1:]))
        build_context()
    else:
        print("Usage: python ai_sync.py [install|note TEXT]")


if __name__ == "__main__":
    main()
