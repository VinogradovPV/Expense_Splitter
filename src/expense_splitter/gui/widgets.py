from __future__ import annotations

import tkinter as tk
from tkinter import ttk


def clear_tree(tree: ttk.Treeview) -> None:
    for item in tree.get_children():
        tree.delete(item)


def make_tree(parent: tk.Widget, columns: tuple[str, ...]) -> ttk.Treeview:
    tree = ttk.Treeview(parent, columns=columns, show="headings", height=14)
    for column in columns:
        tree.heading(column, text=column)
        tree.column(column, width=130, anchor="w")
    return tree

