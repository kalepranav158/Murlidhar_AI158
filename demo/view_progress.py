from analytics.progress import compute_progress


def main():
    stats = compute_progress()

    if not stats:
        print("No sessions yet.")
        return

    print("\n📊 Practice Progress Summary")
    print("-----------------------------")
    for k, v in stats.items():
        print(f"{k}: {v}")


if __name__ == "__main__":
    main()
