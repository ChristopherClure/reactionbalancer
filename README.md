# Reaction Balancer

A terminal UI for balancing chemical equations, built with [Textual](https://github.com/Textualize/textual) and [ChemPy](https://github.com/bjodah/chempy).

## Features

- Balances chemical equations using stoichiometry
- Shows molar masses for all species
- Clickable examples panel
- Session history of past balancings
- Supports unicode subscripts (₂, ₃, …), parentheses, and hydrate dot notation (·)

## Installation

Requires Python 3.12+ and [uv](https://github.com/astral-sh/uv).

```sh
uv sync
```

## Usage

```sh
uv run reactionbalancer
```

Enter an equation using `+` to separate species and `->` to separate reactants from products:

```
H2 + O2 -> H2O
Fe + O2 -> Fe2O3
Ca3(PO4)2 + SiO2 + C -> CaSiO3 + P4 + CO
```

| Key      | Action          |
|----------|-----------------|
| Enter    | Balance equation |
| Escape   | Clear input     |
| Ctrl+Q   | Quit            |

## Building a standalone binary

Requires `patchelf` on your PATH.

```sh
uv run pyinstaller reactionbalancer.spec
```

The binary will be output to `dist/reactionbalancer`.
