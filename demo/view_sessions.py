import json
from database.db import get_all_sessions


def main():
    sessions = get_all_sessions()

    if not sessions:
        print("No sessions found.")
        return

    for s in sessions:
        print("\n==============================")
        print("Session ID:", s[0])
        print("Timestamp:", s[1])
        print("Note Accuracy:", s[4])
        print("Avg Pitch Error:", s[5])
        print("Avg Timing Error:", s[6])

        print("Mistakes:")
        mistakes = json.loads(s[7])
        if not mistakes:
            print("  None")
        else:
            for m in mistakes:
                print("  ", m)


if __name__ == "__main__":
    main()
