"""Trigger manual POS category update."""

from pos_category_management.manage_pos_categories import update_pos_categories


def main() -> None:
    """Run the category update process."""
    update_pos_categories()


if __name__ == "__main__":
    main()
